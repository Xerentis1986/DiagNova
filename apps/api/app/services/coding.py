"""Phase 12 – Codierung/Programmierung: Identifikation, Gates, Framework.

Kein Flash ohne Spec. Kein Schreiben ohne Berechtigung. Kein Auto-Retry.
J2534/D-PDU nur als dokumentierte Vorbereitung.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.coding_catalog import EXCLUDED_OPERATIONS, get_operation, list_catalog
from app.models import User, Vehicle
from app.models.coding import CodingRun
from app.schemas.coding import (
    CodingAbortRequest,
    CodingRunOut,
    CodingStartRequest,
    CodingVehicleStateIn,
    CompatibilityCheckOut,
    EcuIdentificationOut,
    InterfacePrepOut,
    PrerequisiteState,
)
from app.services.audit import write_audit
from app.services.tenant import require_workshop_id
from app.services import simulator

CONFIRM_PHRASE_GATE = "CODING GATE BESTAETIGEN"
MIN_VOLTAGE_V = 12.0


def catalog_payload() -> dict[str, Any]:
    return list_catalog(include_excluded=True)


def _state_map(vs: CodingVehicleStateIn) -> dict[str, bool]:
    voltage_ok = vs.battery_voltage_ok
    if vs.battery_voltage_v is not None and vs.battery_voltage_v < MIN_VOLTAGE_V:
        voltage_ok = False
    return {
        "ignition_on": vs.ignition_on,
        "adapter_connected": vs.adapter_connected,
        "battery_voltage_ok": voltage_ok,
        "stable_connection": vs.stable_connection,
        "vin_ecu_match": vs.vin_ecu_match,
        "oem_spec_present": vs.oem_spec_present,
        "authorization_present": vs.authorization_present,
        "recovery_plan": vs.recovery_plan,
        "operator_confirm": vs.operator_confirm,
    }


def evaluate_prerequisites(
    operation: dict[str, Any],
    vehicle_state: CodingVehicleStateIn,
    *,
    force_missing: bool = False,
) -> list[PrerequisiteState]:
    sm = _state_map(vehicle_state)
    out: list[PrerequisiteState] = []
    for pr in operation.get("prerequisites") or []:
        pid = pr["id"]
        met = bool(sm.get(pid, False))
        if force_missing and pid in (
            "oem_spec_present",
            "authorization_present",
            "adapter_connected",
            "vin_ecu_match",
            "battery_voltage_ok",
        ):
            met = False
        detail = None
        if not met:
            detail = "Voraussetzung nicht erfüllt (simuliert geprüft)."
        out.append(
            PrerequisiteState(
                id=pid,
                label_de=pr.get("label_de", pid),
                met=met,
                detail_de=detail,
            )
        )
    return out


def run_compatibility_checks(vs: CodingVehicleStateIn) -> CompatibilityCheckOut:
    """Spannungs-/Kompatibilitäts-Framework – keine Live-Messung."""
    blockers: list[str] = []
    voltage_v = vs.battery_voltage_v
    voltage_ok = vs.battery_voltage_ok and (voltage_v is None or voltage_v >= MIN_VOLTAGE_V)
    if not voltage_ok:
        blockers.append("voltage")

    vin_match = vs.vin_ecu_match
    if vs.expected_vin and vs.actual_vin and vs.expected_vin.strip().upper() != vs.actual_vin.strip().upper():
        vin_match = False
    if not vin_match:
        blockers.append("vin_mismatch")

    ecu_match = True
    software_compatible: bool | None = None
    if vs.expected_ecu_sw and vs.actual_ecu_sw:
        software_compatible = vs.expected_ecu_sw.strip() == vs.actual_ecu_sw.strip()
        if not software_compatible:
            ecu_match = False
            blockers.append("software_incompatible")
    else:
        software_compatible = None  # unbekannt ohne Spec
        if not vs.oem_spec_present:
            blockers.append("oem_spec_missing")

    if not vs.stable_connection:
        blockers.append("unstable_connection")
    if not vs.authorization_present:
        blockers.append("authorization_missing")
    if not vs.oem_spec_present:
        if "oem_spec_missing" not in blockers:
            blockers.append("oem_spec_missing")
    if not vs.recovery_plan:
        blockers.append("recovery_plan_missing")

    # Signatur ohne OEM-Daten nicht verifizierbar
    signature_verified: bool | None = False if vs.oem_spec_present else None
    if signature_verified is False:
        blockers.append("signature_unverified")

    overall = (
        voltage_ok
        and vin_match
        and ecu_match
        and vs.stable_connection
        and vs.authorization_present
        and vs.oem_spec_present
        and vs.recovery_plan
        and signature_verified is True
    )

    return CompatibilityCheckOut(
        data_source="simulated",
        vin_match=vin_match,
        ecu_match=ecu_match,
        software_compatible=software_compatible,
        signature_verified=signature_verified,
        voltage_ok=voltage_ok,
        voltage_v=voltage_v,
        stable_connection=vs.stable_connection,
        authorization_ok=vs.authorization_present,
        oem_spec_ok=vs.oem_spec_present,
        recovery_plan_ok=vs.recovery_plan,
        overall_ok=overall,
        blockers=blockers,
        message_de=(
            "Kompatibilitäts-/Spannungsprüfung (Framework). "
            "Flash und Schreiben bleiben gesperrt, bis Spec, Signatur und Freigabe vorliegen."
            if not overall
            else "Framework-Prüfung ok – Live-Flash dennoch nicht freigegeben (Phase 12)."
        ),
        flash_blocked=True,
        write_blocked=True,
    )


def identify_ecu(db: Session, user: User, vehicle_id: str | None = None) -> EcuIdentificationOut:
    """Lesende Identifikation – simuliert; OEM-Felder ohne Spec nicht erfinden."""
    wid = require_workshop_id(user)
    vin = None
    if vehicle_id:
        vehicle = db.get(Vehicle, vehicle_id)
        if vehicle is None or vehicle.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")
        vin = vehicle.vin

    # Simulator liefert höchstens generische Demo-Identifikation
    demo = simulator.connection_status()
    adapter_label = getattr(demo, "adapter_name", None) or getattr(demo, "mode", "simulator")
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="coding.identify_read",
        resource=vehicle_id or "none",
        detail="read_only_simulated",
    )
    return EcuIdentificationOut(
        data_source="simulated",
        disclaimer_de=(
            "Nur lesende, simulierte Identifikation. Keine OEM-Codierdaten. "
            "Softwarestand/Codierprofil ohne Spezifikation nicht als echt ausgeben."
        ),
        vin=vin,
        ecu_id="ECM-OBD-7E0",
        part_number=None,  # nicht erfinden
        software_version="SIM-SW-UNVERIFIED",
        hardware_version=None,
        coding_profile=None,
        coding_profile_status="unavailable",
        oem_fields_available=False,
        message_de=(
            f"Adapter: {adapter_label}. "
            "Codierprofil: nicht verfügbar (BLK-OEM). Keine Schreib-/Flashaktion."
        ),
    )


def interface_prep() -> InterfacePrepOut:
    return InterfacePrepOut(
        j2534_status="documented_prep",
        dpdu_status="documented_prep",
        vendor_dll_present=False,
        notes_de=(
            "J2534/D-PDU nur als Framework dokumentiert. Keine Vendor-DLL, kein PassThruOpen, "
            "keine Flash-Routine. Siehe docs/j2534-doip-j1939-prep.md."
        ),
        docs=["docs/j2534-doip-j1939-prep.md", "docs/adapter-capability-matrix.md"],
    )


def _run_out(run: CodingRun, prerequisites: list[PrerequisiteState] | None = None) -> CodingRunOut:
    prereqs = prerequisites
    if prereqs is None:
        raw = json.loads(run.prerequisites_json or "[]")
        prereqs = [PrerequisiteState.model_validate(x) for x in raw]
    result = json.loads(run.result_json or "{}")
    checks = json.loads(run.checks_json or "{}")
    return CodingRunOut(
        id=run.id,
        operation_code=run.operation_code,
        status=run.status,
        scenario=run.scenario,
        data_source=run.data_source,
        prerequisites=prereqs,
        checks=checks,
        result=result,
        message_de=run.message_de,
        abort_reason_de=run.abort_reason_de,
        write_commands_sent=bool(result.get("write_commands_sent", False)),
        flash_commands_sent=bool(result.get("flash_commands_sent", False)),
        auto_retry_attempted=bool(result.get("auto_retry_attempted", False)),
        started_at=run.started_at,
        ended_at=run.ended_at,
    )


def start_run(
    db: Session,
    user: User,
    operation_code: str,
    body: CodingStartRequest,
) -> CodingRunOut:
    wid = require_workshop_id(user)
    operation = get_operation(operation_code)
    if operation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation nicht gefunden")

    if operation.get("safety_class") == "excluded" or operation_code in {
        e["code"] for e in EXCLUDED_OPERATIONS
    }:
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="coding.excluded_blocked",
            resource=operation_code,
            detail="Ausgeschlossene Codier-/Flashfunktion abgelehnt",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=operation.get(
                "reason_de",
                "Ausgeschlossen: unautorisierte Programmierung / Abgas-Deaktivierung.",
            ),
        )

    if body.vehicle_id:
        vehicle = db.get(Vehicle, body.vehicle_id)
        if vehicle is None or vehicle.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")

    release = operation.get("release_status")
    op_type = operation.get("operation_type")

    # Write/Flash operations always need ack that they stay disabled
    if op_type in ("coding", "flash") and release == "disabled":
        if not (
            body.acknowledge_disabled
            and body.acknowledge_no_oem_write
            and body.acknowledge_no_flash
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Codierung/Flash ohne Spezifikation und Berechtigung DEAKTIVIERT. "
                    "Nur Gate-Simulation mit acknowledge_disabled + acknowledge_no_oem_write "
                    "+ acknowledge_no_flash – keine Fahrzeug-Schreib-/Flashbefehle."
                ),
            )
        mode = "gates_only_disabled"
    elif release in ("sim_gates_only", "documented_prep"):
        mode = release
    else:
        mode = "catalog_only"

    # Defensive: never allow live write/flash flags
    if operation.get("write_allowed") or operation.get("flash_allowed") or operation.get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live-Codierung/Flash ist in Phase 12 nicht freigegeben.",
        )

    phrase = operation.get("confirmation_phrase")
    if phrase and body.scenario not in ("missing_prereq", "wrong_vehicle", "voltage_drop"):
        if (body.confirmation_phrase or "").strip() != phrase:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bestätigungsphrase fehlt oder falsch. Erwartet: {phrase}",
            )

    force_missing = body.scenario == "missing_prereq"
    vs = body.vehicle_state
    if body.scenario == "voltage_drop":
        vs = vs.model_copy(update={"battery_voltage_ok": False, "battery_voltage_v": 9.5})
    if body.scenario == "wrong_vehicle":
        vs = vs.model_copy(
            update={
                "vin_ecu_match": False,
                "expected_vin": vs.expected_vin or "WVWZZZ1JZAW000001",
                "actual_vin": vs.actual_vin or "WBAWRONGVIN000000",
            }
        )

    prereqs = evaluate_prerequisites(operation, vs, force_missing=force_missing)
    checks = run_compatibility_checks(vs)
    all_met = all(p.met for p in prereqs)

    now = datetime.now(timezone.utc)
    run = CodingRun(
        workshop_id=wid,
        vehicle_id=body.vehicle_id,
        user_id=user.id,
        operation_code=operation_code,
        status="pending",
        scenario=body.scenario,
        data_source="simulated",
        prerequisites_json=json.dumps([p.model_dump() for p in prereqs], ensure_ascii=False),
        checks_json=json.dumps(checks.model_dump(), ensure_ascii=False),
        result_json="{}",
        started_at=now,
    )

    base_result = {
        "write_commands_sent": False,
        "flash_commands_sent": False,
        "auto_retry_attempted": False,
        "auto_retry_forbidden": True,
        "mode": mode,
        "operation_type": op_type,
        "live_execution": False,
        "hardware_tested": False,
        "release_status": release,
    }

    if body.scenario == "wrong_vehicle" or not checks.vin_match:
        run.status = "blocked"
        run.ended_at = now
        run.message_de = "Falsches Fahrzeug / VIN-ECU-Mismatch – Codierung/Flash gesperrt."
        run.result_json = json.dumps(
            {**base_result, "gate": "wrong_vehicle", "error": "vin_ecu_mismatch"},
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="coding.run_blocked_vehicle",
            resource=operation_code,
            detail=f"run={run.id}",
        )
        return _run_out(run, prereqs)

    if body.scenario == "voltage_drop" or not checks.voltage_ok:
        run.status = "failed"
        run.ended_at = now
        run.message_de = (
            "Spannungsabfall / Unterspannung simuliert – Abbruch, kein Flash, kein Auto-Retry."
        )
        run.result_json = json.dumps(
            {
                **base_result,
                "gate": "voltage_drop",
                "error": "voltage_drop",
                "voltage_v": checks.voltage_v,
            },
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="coding.run_voltage_drop",
            resource=operation_code,
            detail=f"run={run.id} v={checks.voltage_v}",
        )
        return _run_out(run, prereqs)

    if not all_met:
        run.status = "blocked"
        run.ended_at = now
        run.message_de = "Voraussetzungen nicht erfüllt – Codierung/Flash gesperrt."
        run.result_json = json.dumps(
            {
                **base_result,
                "gate": "prerequisites",
                "missing": [p.id for p in prereqs if not p.met],
            },
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="coding.run_blocked",
            resource=operation_code,
            detail=f"run={run.id} missing={[p.id for p in prereqs if not p.met]}",
        )
        return _run_out(run, prereqs)

    if body.scenario == "comm_loss":
        run.status = "failed"
        run.ended_at = now
        run.message_de = "Kommunikationsverlust simuliert – keine Schreib-/Flashbefehle, kein Auto-Retry."
        run.result_json = json.dumps(
            {**base_result, "gate": "comm_loss", "error": "communication_lost"},
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="coding.run_comm_loss",
            resource=operation_code,
            detail=f"run={run.id}",
        )
        return _run_out(run, prereqs)

    if body.scenario == "abort":
        run.status = "running"
        run.message_de = "Simulation läuft – Abbruch erwartet. Kein Flash gestartet."
        run.result_json = json.dumps(
            {**base_result, "gate": "awaiting_abort"},
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="coding.run_started",
            resource=operation_code,
            detail=f"run={run.id} scenario=abort",
        )
        return _run_out(run, prereqs)

    # normal: complete gate / identify simulation without vehicle writes
    run.status = "completed"
    run.ended_at = now
    if op_type == "identify":
        run.message_de = (
            "Identifikation (simuliert) abgeschlossen. Keine OEM-Codierdaten, kein Schreiben."
        )
    elif op_type == "interface":
        run.message_de = (
            "Schnittstellen-Prep dokumentiert. Keine Vendor-DLL geladen, kein Flash."
        )
    else:
        run.message_de = (
            "Gate-Simulation abgeschlossen. Keine Fahrzeug-Schreib-/Flashbefehle, "
            "kein Auto-Retry, nicht hardwaregetestet."
        )
    run.result_json = json.dumps(
        {**base_result, "gate": "ok", "compatibility_overall": checks.overall_ok},
        ensure_ascii=False,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="coding.run_completed_gates",
        resource=operation_code,
        detail=f"run={run.id} mode={mode}",
    )
    return _run_out(run, prereqs)


def abort_run(db: Session, user: User, run_id: str, body: CodingAbortRequest) -> CodingRunOut:
    wid = require_workshop_id(user)
    run = db.get(CodingRun, run_id)
    if run is None or run.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lauf nicht gefunden")
    if run.status not in ("running", "pending"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lauf kann nicht abgebrochen werden (Status: {run.status})",
        )
    now = datetime.now(timezone.utc)
    run.status = "aborted"
    run.ended_at = now
    run.abort_reason_de = body.reason_de or "Bedienerabbruch"
    run.message_de = "Abgebrochen – keine Schreib-/Flashbefehle, kein Auto-Retry."
    result = json.loads(run.result_json or "{}")
    result["write_commands_sent"] = False
    result["flash_commands_sent"] = False
    result["auto_retry_attempted"] = False
    result["gate"] = "aborted"
    run.result_json = json.dumps(result, ensure_ascii=False)
    db.add(run)
    db.commit()
    db.refresh(run)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="coding.run_aborted",
        resource=run.operation_code,
        detail=f"run={run.id} reason={run.abort_reason_de}",
    )
    return _run_out(run)


def get_run(db: Session, user: User, run_id: str) -> CodingRunOut:
    wid = require_workshop_id(user)
    run = db.get(CodingRun, run_id)
    if run is None or run.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lauf nicht gefunden")
    return _run_out(run)


def list_runs(db: Session, user: User, *, limit: int = 50) -> list[CodingRunOut]:
    wid = require_workshop_id(user)
    rows = (
        db.query(CodingRun)
        .filter(CodingRun.workshop_id == wid)
        .order_by(CodingRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [_run_out(r) for r in rows]


def execute_live_blocked(operation_code: str) -> None:
    operation = get_operation(operation_code)
    if operation and operation.get("safety_class") == "excluded":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=operation.get("reason_de", "Ausgeschlossen."),
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Live-Codierung/Flash ist nicht freigegeben "
            "(fehlende OEM-Spezifikation, Berechtigung, Hardwaretest und fachliche Freigabe)."
        ),
    )


def flash_blocked(operation_code: str) -> None:
    """Expliziter Flash-Pfad – immer 403, kein Auto-Retry."""
    execute_live_blocked(operation_code)
