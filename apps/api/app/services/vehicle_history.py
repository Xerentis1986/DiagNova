"""Phase 09 – Fahrzeugakte, Sitzungs-Snapshots, DTC-Vergleich, Messwertlimit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import (
    DiagnosticReport,
    DiagnosticSession,
    SessionDtcResult,
    SessionEcuResult,
    SessionMeasurementSample,
    User,
    Vehicle,
    VehicleRecordNote,
    WorkOrder,
)
from app.services import simulator

# Begrenzte Speicherung großer Streams
MAX_SAMPLES_PER_SESSION = 500
MAX_SAMPLES_PER_VEHICLE = 5_000

# Simulator-Standard-ECU für OBD-Snapshot (keine erfundenen OEM-Adressen)
DEFAULT_ECU_CODE = "ECM"
DEFAULT_ECU_LABEL = "Motorsteuergerät (OBD)"
DEFAULT_PROTOCOL = "ISO 15765-4 CAN"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def lookup_vehicles(
    db: Session,
    workshop_id: str,
    *,
    vin: str | None = None,
    license_plate: str | None = None,
) -> list[Vehicle]:
    q = db.query(Vehicle).filter(Vehicle.workshop_id == workshop_id, Vehicle.archived_at.is_(None))
    clauses = []
    if vin:
        clauses.append(Vehicle.vin.ilike(vin.strip().upper()))
    if license_plate:
        plate = license_plate.strip().upper().replace(" ", "")
        clauses.append(func.replace(func.upper(Vehicle.license_plate), " ", "") == plate)
    if not clauses:
        return []
    return q.filter(or_(*clauses)).order_by(Vehicle.make, Vehicle.model).all()


def get_tenant_vehicle(db: Session, workshop_id: str, vehicle_id: str) -> Vehicle | None:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.workshop_id != workshop_id:
        return None
    return vehicle


def find_by_idempotency(
    db: Session, workshop_id: str, idempotency_key: str
) -> DiagnosticSession | None:
    return (
        db.query(DiagnosticSession)
        .filter(
            DiagnosticSession.workshop_id == workshop_id,
            DiagnosticSession.idempotency_key == idempotency_key,
        )
        .first()
    )


def capture_session_snapshot(
    db: Session,
    session: DiagnosticSession,
    vehicle: Vehicle,
    *,
    ecu_codes: list[str] | None = None,
    include_measurements: bool = True,
) -> None:
    """Speichert ECU-/DTC-/Freeze-/Messwert-Snapshot. Demo bleibt data_source=simulated."""
    checked_codes = ecu_codes or [DEFAULT_ECU_CODE]
    # Bestehende Snapshot-Zeilen ersetzen (idempotente Wiederholung innerhalb Session)
    db.query(SessionDtcResult).filter(SessionDtcResult.session_id == session.id).delete()
    db.query(SessionEcuResult).filter(SessionEcuResult.session_id == session.id).delete()

    dtcs = simulator.list_dtcs(vehicle.id)
    live = simulator.live_data(vehicle.id, vehicle.vin)
    conn = simulator.connection_status()

    session.adapter_name = session.adapter_name or conn.adapter_name
    session.protocol_name = session.protocol_name or DEFAULT_PROTOCOL
    session.dtc_snapshot_json = json.dumps([d.model_dump() for d in dtcs], ensure_ascii=False)
    session.freeze_frame_json = json.dumps(live.freeze_frame, ensure_ascii=False) if live.freeze_frame else None
    session.readiness_json = json.dumps(live.readiness, ensure_ascii=False)
    session.data_source = "simulated"

    ecu_map: dict[str, SessionEcuResult] = {}
    for code in checked_codes:
        label = DEFAULT_ECU_LABEL if code == DEFAULT_ECU_CODE else code
        row = SessionEcuResult(
            session_id=session.id,
            ecu_code=code,
            ecu_label_de=label,
            checked=True,
            protocol_name=session.protocol_name,
            address_hex="7E8" if code == DEFAULT_ECU_CODE else None,
            status="ok",
        )
        db.add(row)
        db.flush()
        ecu_map[code] = row

    # DTCs dem geprüften ECM zuordnen (Simulator liefert keine ECU-Zuordnung)
    primary = ecu_map.get(DEFAULT_ECU_CODE) or next(iter(ecu_map.values()), None)
    primary_code = primary.ecu_code if primary else DEFAULT_ECU_CODE
    for d in dtcs:
        db.add(
            SessionDtcResult(
                session_id=session.id,
                ecu_result_id=primary.id if primary else None,
                ecu_code=primary_code,
                code=d.code,
                dtc_status=d.status,
                description_de=d.description_de,
                severity=d.severity,
            )
        )

    if include_measurements:
        _store_measurement_batch(db, session, vehicle, live.readings)

    session.auto_saved_at = _now()
    db.flush()


def _store_measurement_batch(
    db: Session,
    session: DiagnosticSession,
    vehicle: Vehicle,
    readings: list[Any],
) -> None:
    wid = session.workshop_id or vehicle.workshop_id or ""
    existing = (
        db.query(func.count(SessionMeasurementSample.id))
        .filter(SessionMeasurementSample.session_id == session.id)
        .scalar()
        or 0
    )
    room = max(0, MAX_SAMPLES_PER_SESSION - int(existing))
    for r in readings[:room]:
        recorded = r.timestamp if hasattr(r, "timestamp") else _now()
        db.add(
            SessionMeasurementSample(
                session_id=session.id,
                vehicle_id=vehicle.id,
                workshop_id=wid,
                pid=r.pid,
                pid_hex=r.pid_hex,
                name=r.name,
                value=float(r.value),
                unit=r.unit or "",
                recorded_at=recorded,
                data_source=getattr(session, "data_source", None) or "simulated",
            )
        )
    db.flush()
    prune_vehicle_measurements(db, vehicle.id)


def prune_vehicle_measurements(db: Session, vehicle_id: str) -> int:
    """Älteste Samples löschen, wenn Fahrzeuglimit überschritten."""
    total = (
        db.query(func.count(SessionMeasurementSample.id))
        .filter(SessionMeasurementSample.vehicle_id == vehicle_id)
        .scalar()
        or 0
    )
    overflow = int(total) - MAX_SAMPLES_PER_VEHICLE
    if overflow <= 0:
        return 0
    oldest = (
        db.query(SessionMeasurementSample.id)
        .filter(SessionMeasurementSample.vehicle_id == vehicle_id)
        .order_by(SessionMeasurementSample.recorded_at.asc())
        .limit(overflow)
        .all()
    )
    ids = [row[0] for row in oldest]
    if ids:
        db.query(SessionMeasurementSample).filter(SessionMeasurementSample.id.in_(ids)).delete(
            synchronize_session=False
        )
    return len(ids)


def _existing_ecu_codes(db: Session, session_id: str) -> list[str] | None:
    rows = (
        db.query(SessionEcuResult.ecu_code)
        .filter(SessionEcuResult.session_id == session_id, SessionEcuResult.checked.is_(True))
        .all()
    )
    codes = [r[0] for r in rows]
    return codes or None


def close_session(db: Session, session: DiagnosticSession, vehicle: Vehicle) -> DiagnosticSession:
    if session.status == "open":
        # Geprüfte ECUs beibehalten (unvollständige Scans nicht überschreiben)
        capture_session_snapshot(
            db, session, vehicle, ecu_codes=_existing_ecu_codes(db, session.id)
        )
        session.status = "closed"
        session.ended_at = _now()
        if vehicle.odometer_km is None and session.odometer_km is not None:
            vehicle.odometer_km = session.odometer_km
        elif session.odometer_km is not None and (
            vehicle.odometer_km is None or session.odometer_km >= vehicle.odometer_km
        ):
            vehicle.odometer_km = session.odometer_km
    return session


def abort_session(
    db: Session, session: DiagnosticSession, vehicle: Vehicle, reason: str
) -> DiagnosticSession:
    if session.status == "open":
        # Teil-Snapshot behalten, aber als abgebrochen markieren
        capture_session_snapshot(
            db, session, vehicle, ecu_codes=_existing_ecu_codes(db, session.id)
        )
        session.status = "aborted"
        session.abort_reason = reason
        session.ended_at = _now()
    return session


def compare_sessions(
    db: Session, before: DiagnosticSession, after: DiagnosticSession
) -> dict[str, Any]:
    """Vorher/Nachher pro ECU/DTC. Nicht erneut beobachtet ≠ behoben ohne ECU-Check."""
    before_ecus = {
        e.ecu_code: e
        for e in db.query(SessionEcuResult).filter(SessionEcuResult.session_id == before.id).all()
        if e.checked
    }
    after_ecus = {
        e.ecu_code: e
        for e in db.query(SessionEcuResult).filter(SessionEcuResult.session_id == after.id).all()
        if e.checked
    }
    before_dtcs = (
        db.query(SessionDtcResult).filter(SessionDtcResult.session_id == before.id).all()
    )
    after_dtcs = db.query(SessionDtcResult).filter(SessionDtcResult.session_id == after.id).all()

    after_keys = {(d.ecu_code, d.code, d.dtc_status) for d in after_dtcs}
    before_keys = {(d.ecu_code, d.code, d.dtc_status) for d in before_dtcs}

    items: list[dict[str, Any]] = []
    unchecked = sorted(set(before_ecus) - set(after_ecus))

    for d in after_dtcs:
        key = (d.ecu_code, d.code, d.dtc_status)
        if key in before_keys:
            items.append(
                {
                    "ecu_code": d.ecu_code,
                    "code": d.code,
                    "dtc_status": d.dtc_status,
                    "description_de": d.description_de,
                    "outcome": "weiterhin_vorhanden",
                    "ecu_checked_in_after": d.ecu_code in after_ecus,
                    "may_interpret_as_resolved": False,
                    "note_de": "DTC in beiden Sitzungen beobachtet.",
                }
            )
        else:
            items.append(
                {
                    "ecu_code": d.ecu_code,
                    "code": d.code,
                    "dtc_status": d.dtc_status,
                    "description_de": d.description_de,
                    "outcome": "neu",
                    "ecu_checked_in_after": d.ecu_code in after_ecus,
                    "may_interpret_as_resolved": False,
                    "note_de": "In der späteren Sitzung neu beobachtet.",
                }
            )

    for d in before_dtcs:
        key = (d.ecu_code, d.code, d.dtc_status)
        if key in after_keys:
            continue
        checked = d.ecu_code in after_ecus
        items.append(
            {
                "ecu_code": d.ecu_code,
                "code": d.code,
                "dtc_status": d.dtc_status,
                "description_de": d.description_de,
                "outcome": "nicht_erneut_beobachtet",
                "ecu_checked_in_after": checked,
                "may_interpret_as_resolved": checked,
                "note_de": (
                    "ECU erneut geprüft – DTC nicht erneut beobachtet (kann behoben sein)."
                    if checked
                    else "ECU in der späteren Sitzung NICHT geprüft – nicht als behoben darstellen."
                ),
            }
        )

    incomplete = bool(unchecked)
    return {
        "before_session_id": before.id,
        "after_session_id": after.id,
        "vehicle_id": before.vehicle_id,
        "incomplete_scan": incomplete,
        "unchecked_ecus_in_after": unchecked,
        "items": items,
        "disclaimer_de": (
            "Vergleich nur für geprüfte Steuergeräte. "
            "„Nicht erneut beobachtet“ ohne ECU-Prüfung ist kein Behebungsnachweis. "
            "Demo-/Simulationsdaten sind als solche gekennzeichnet."
        ),
    }


def build_timeline(db: Session, vehicle: Vehicle, workshop_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    sessions = (
        db.query(DiagnosticSession)
        .filter(DiagnosticSession.vehicle_id == vehicle.id)
        .order_by(DiagnosticSession.started_at.desc())
        .all()
    )
    users = {u.id: u for u in db.query(User).filter(User.workshop_id == workshop_id).all()}
    for s in sessions:
        user = users.get(s.user_id)
        dtc_n = len(json.loads(s.dtc_snapshot_json or "[]"))
        auth = "example_seed" if vehicle.is_example_data else (
            "simulated" if s.data_source == "simulated" else "recorded"
        )
        status_label = {"open": "offen", "closed": "abgeschlossen", "aborted": "abgebrochen"}.get(
            s.status, s.status
        )
        items.append(
            {
                "id": f"session:{s.id}",
                "kind": "session",
                "at": s.started_at,
                "title_de": f"Diagnosesitzung ({status_label})",
                "summary_de": (
                    f"{user.full_name if user else 'Benutzer'} · "
                    f"{s.adapter_name or 'Adapter n/v'} · {s.protocol_name or 'Protokoll n/v'} · "
                    f"{dtc_n} DTC(s)"
                    + (f" · Abbruch: {s.abort_reason}" if s.abort_reason else "")
                ),
                "data_source": s.data_source,
                "status": s.status,
                "odometer_km": s.odometer_km,
                "session_id": s.id,
                "work_order_id": s.work_order_id,
                "report_id": None,
                "is_example_data": vehicle.is_example_data,
                "authenticity": auth,
            }
        )
        reports = (
            db.query(DiagnosticReport)
            .filter(DiagnosticReport.session_id == s.id)
            .order_by(DiagnosticReport.created_at.desc())
            .all()
        )
        for r in reports:
            items.append(
                {
                    "id": f"report:{r.id}",
                    "kind": "report",
                    "at": r.created_at,
                    "title_de": f"Bericht: {r.title}",
                    "summary_de": f"Verknüpft mit Sitzung {s.id[:8]}…",
                    "data_source": s.data_source,
                    "status": None,
                    "odometer_km": s.odometer_km,
                    "session_id": s.id,
                    "work_order_id": s.work_order_id,
                    "report_id": r.id,
                    "is_example_data": vehicle.is_example_data,
                    "authenticity": auth,
                }
            )

    orders = (
        db.query(WorkOrder)
        .filter(WorkOrder.vehicle_id == vehicle.id, WorkOrder.workshop_id == workshop_id)
        .order_by(WorkOrder.created_at.desc())
        .all()
    )
    for o in orders:
        items.append(
            {
                "id": f"work_order:{o.id}",
                "kind": "work_order",
                "at": o.created_at,
                "title_de": f"Auftrag: {o.title}",
                "summary_de": (
                    f"Status {o.status}"
                    + (f" · {o.repair_summary}" if o.repair_summary else "")
                    + (f" · {o.notes}" if o.notes and not o.repair_summary else "")
                )[:400],
                "data_source": None,
                "status": o.status,
                "odometer_km": o.odometer_km,
                "session_id": None,
                "work_order_id": o.id,
                "report_id": None,
                "is_example_data": o.is_example_data,
                "authenticity": "example_seed" if o.is_example_data else "recorded",
            }
        )

    notes = (
        db.query(VehicleRecordNote)
        .filter(
            VehicleRecordNote.vehicle_id == vehicle.id,
            VehicleRecordNote.workshop_id == workshop_id,
        )
        .order_by(VehicleRecordNote.created_at.desc())
        .all()
    )
    for n in notes:
        type_de = {"note": "Notiz", "service": "Service", "repair": "Reparatur"}.get(
            n.note_type, "Notiz"
        )
        items.append(
            {
                "id": f"note:{n.id}",
                "kind": "note",
                "at": n.created_at,
                "title_de": type_de,
                "summary_de": n.body[:400],
                "data_source": None,
                "status": n.note_type,
                "odometer_km": n.odometer_km,
                "session_id": n.session_id,
                "work_order_id": n.work_order_id,
                "report_id": None,
                "is_example_data": n.is_example_data,
                "authenticity": "example_seed" if n.is_example_data else "recorded",
            }
        )

    items.sort(key=lambda x: x["at"] or _now(), reverse=True)
    return items


def build_vehicle_record(db: Session, vehicle: Vehicle, workshop_id: str) -> dict[str, Any]:
    sessions = (
        db.query(DiagnosticSession).filter(DiagnosticSession.vehicle_id == vehicle.id).all()
    )
    open_n = sum(1 for s in sessions if s.status == "open")
    return {
        "vehicle_id": vehicle.id,
        "make": vehicle.make,
        "model": vehicle.model,
        "year": vehicle.year,
        "vin": vehicle.vin,
        "license_plate": vehicle.license_plate,
        "odometer_km": vehicle.odometer_km,
        "is_example_data": vehicle.is_example_data,
        "customer_id": vehicle.customer_id,
        "workshop_id": vehicle.workshop_id,
        "session_count": len(sessions),
        "open_session_count": open_n,
        "timeline": build_timeline(db, vehicle, workshop_id),
        "disclaimer_de": (
            "Digitale Fahrzeugakte – nur mandanteneigene, persistierte Einträge. "
            "Beispieldaten und Simulationssitzungen sind gekennzeichnet und keine echte Historie."
        ),
    }


def session_detail(db: Session, session: DiagnosticSession, vehicle: Vehicle) -> dict[str, Any]:
    user = db.get(User, session.user_id)
    ecus = (
        db.query(SessionEcuResult)
        .filter(SessionEcuResult.session_id == session.id)
        .order_by(SessionEcuResult.ecu_code)
        .all()
    )
    dtcs = (
        db.query(SessionDtcResult)
        .filter(SessionDtcResult.session_id == session.id)
        .order_by(SessionDtcResult.code)
        .all()
    )
    reports = (
        db.query(DiagnosticReport.id).filter(DiagnosticReport.session_id == session.id).all()
    )
    m_count = (
        db.query(func.count(SessionMeasurementSample.id))
        .filter(SessionMeasurementSample.session_id == session.id)
        .scalar()
        or 0
    )
    freeze = json.loads(session.freeze_frame_json) if session.freeze_frame_json else None
    readiness = json.loads(session.readiness_json) if session.readiness_json else None
    return {
        "id": session.id,
        "vehicle_id": session.vehicle_id,
        "vehicle_label": f"{vehicle.make} {vehicle.model}",
        "workshop_id": session.workshop_id,
        "user_id": session.user_id,
        "user_name": user.full_name if user else None,
        "work_order_id": session.work_order_id,
        "status": session.status,
        "data_source": session.data_source,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "auto_saved_at": session.auto_saved_at,
        "odometer_km": session.odometer_km,
        "adapter_name": session.adapter_name,
        "protocol_name": session.protocol_name,
        "abort_reason": session.abort_reason,
        "notes": session.notes,
        "dtc_count": len(dtcs) or len(json.loads(session.dtc_snapshot_json or "[]")),
        "ecus": [
            {
                "ecu_code": e.ecu_code,
                "ecu_label_de": e.ecu_label_de,
                "checked": e.checked,
                "protocol_name": e.protocol_name,
                "address_hex": e.address_hex,
                "status": e.status,
            }
            for e in ecus
        ],
        "dtcs": [
            {
                "ecu_code": d.ecu_code,
                "code": d.code,
                "dtc_status": d.dtc_status,
                "description_de": d.description_de,
                "severity": d.severity,
            }
            for d in dtcs
        ],
        "freeze_frame": freeze,
        "readiness": readiness,
        "report_ids": [r[0] for r in reports],
        "measurement_sample_count": int(m_count),
    }


def list_measurements(
    db: Session,
    vehicle_id: str,
    workshop_id: str,
    *,
    pid: int | None = None,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    limit = min(max(1, limit), MAX_SAMPLES_PER_SESSION)
    q = db.query(SessionMeasurementSample).filter(
        SessionMeasurementSample.vehicle_id == vehicle_id,
        SessionMeasurementSample.workshop_id == workshop_id,
    )
    if pid is not None:
        q = q.filter(SessionMeasurementSample.pid == pid)
    if from_at is not None:
        q = q.filter(SessionMeasurementSample.recorded_at >= from_at)
    if to_at is not None:
        q = q.filter(SessionMeasurementSample.recorded_at <= to_at)
    total = q.count()
    rows = q.order_by(SessionMeasurementSample.recorded_at.desc()).limit(limit).all()
    samples = list(reversed(rows))
    unit = samples[0].unit if samples else None
    name = samples[0].name if samples else None
    return {
        "vehicle_id": vehicle_id,
        "pid": pid,
        "name": name,
        "unit": unit,
        "from_at": from_at or (samples[0].recorded_at if samples else None),
        "to_at": to_at or (samples[-1].recorded_at if samples else None),
        "count": len(samples),
        "truncated": total > len(samples),
        "max_samples": MAX_SAMPLES_PER_SESSION,
        "samples": [
            {
                "id": s.id,
                "session_id": s.session_id,
                "pid": s.pid,
                "pid_hex": s.pid_hex,
                "name": s.name,
                "value": s.value,
                "unit": s.unit,
                "recorded_at": s.recorded_at,
                "data_source": s.data_source,
            }
            for s in samples
        ],
        "disclaimer_de": (
            f"Messwertverlauf begrenzt (max. {MAX_SAMPLES_PER_SESSION}/Sitzung, "
            f"{MAX_SAMPLES_PER_VEHICLE}/Fahrzeug). Simulierte Werte sind gekennzeichnet."
        ),
    }
