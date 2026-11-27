from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import DiagnosticSession, User, Vehicle, WorkOrder
from app.schemas.api import (
    ClearDtcRequest,
    ConnectionStatusOut,
    DiagnosticSessionOut,
    DtcOut,
    LiveDataOut,
)
from app.schemas.vehicle_history import (
    SessionAbortRequest,
    SessionCompareOut,
    SessionDetailOut,
    SessionStartRequest,
)
from app.services import connector_bridge
from app.services import simulator
from app.services import vehicle_history as vh
from app.services.audit import write_audit
from app.services.connector_bridge import ConnectorBridgeError
from app.services.reports import create_report
from app.services.tenant import require_workshop_id

router = APIRouter(tags=["diagnostics"])

Technician = Annotated[User, Depends(require_roles("admin", "technician"))]


def _mode_from_query(mode: str | None) -> connector_bridge.DiagMode:
    return connector_bridge.resolve_mode(mode)


def _tenant_vehicle(db: DbSession, user: User, vehicle_id: str) -> Vehicle:
    wid = require_workshop_id(user)
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")
    return vehicle


def _tenant_session(db: DbSession, user: User, session_id: str) -> tuple[DiagnosticSession, Vehicle]:
    wid = require_workshop_id(user)
    session = db.get(DiagnosticSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    vehicle = db.get(Vehicle, session.vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    if session.workshop_id and session.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    return session, vehicle


def _session_out(session: DiagnosticSession, vehicle: Vehicle) -> DiagnosticSessionOut:
    dtcs = json.loads(session.dtc_snapshot_json or "[]")
    status_val = session.status if session.status in ("open", "closed", "aborted") else "closed"
    return DiagnosticSessionOut(
        id=session.id,
        vehicle_id=session.vehicle_id,
        vehicle_label=f"{vehicle.make} {vehicle.model}",
        started_at=session.started_at,
        ended_at=session.ended_at,
        data_source=session.data_source,  # type: ignore[arg-type]
        dtc_count=len(dtcs),
        status=status_val,  # type: ignore[arg-type]
    )


class SessionStartBody(BaseModel):
    """Optionaler Body; Query vehicle_id bleibt für Abwärtskompatibilität."""

    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    work_order_id: str | None = None
    notes: str | None = None
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=64)
    ecu_codes: list[str] | None = None


@router.get("/connection", response_model=ConnectionStatusOut)
async def get_connection(
    _user: CurrentUser,
    mode: str | None = Query(default=None, description="demo|live"),
) -> ConnectionStatusOut:
    return await connector_bridge.connection_status(_mode_from_query(mode))


@router.get("/connector/bridge-status")
async def bridge_status(_user: CurrentUser) -> dict:
    probe = await connector_bridge.probe_connector()
    return {
        "default_mode": connector_bridge.resolve_mode(None),
        "connector": probe,
        "message_de": (
            "LIVE nur mit erreichbarem Windows-Connector; DEMO nutzt Simulator. "
            "Kein Simulator-Fallback im LIVE-Modus."
        ),
    }


@router.post("/connector/obd-init")
async def bridge_obd_init(
    _user: Technician,
    mode: str | None = Query(default=None),
) -> dict:
    m = _mode_from_query(mode)
    try:
        return await connector_bridge.ensure_obd_init(m)
    except ConnectorBridgeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/diagnostics/pids")
def list_pids(_user: CurrentUser) -> dict:
    return {"data_source": "simulated", "pids": simulator.supported_pids()}


@router.get("/diagnostics/{vehicle_id}/dtcs", response_model=list[DtcOut])
async def get_dtcs(
    vehicle_id: str,
    user: CurrentUser,
    db: DbSession,
    mode: str | None = Query(default=None),
) -> list[DtcOut]:
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    m = _mode_from_query(mode)
    try:
        return await connector_bridge.list_dtcs(m, vehicle.id)
    except ConnectorBridgeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/diagnostics/{vehicle_id}/live", response_model=LiveDataOut)
async def get_live(
    vehicle_id: str,
    user: CurrentUser,
    db: DbSession,
    mode: str | None = Query(default=None),
) -> LiveDataOut:
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    m = _mode_from_query(mode)
    try:
        return await connector_bridge.live_data(m, vehicle.id, vehicle.vin)
    except ConnectorBridgeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/diagnostics/clear/warnings")
def clear_warnings(_user: CurrentUser) -> dict:
    """Warnhinweise für Fehlerlöschung – immer mit data_source-Kennzeichnung."""
    return simulator.clear_dtc_warnings()


@router.post("/diagnostics/{vehicle_id}/dtcs/clear")
def clear_dtcs(
    vehicle_id: str,
    body: ClearDtcRequest,
    user: Technician,
    db: DbSession,
) -> dict:
    """
    Freigabegeschützte DTC-Löschung im Simulator.
    Permanente DTCs bleiben. Kein Hardwarezugriff – data_source=simulated.
    """
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    result = simulator.clear_dtcs_simulated(
        vehicle.id,
        confirmation_phrase=body.confirmation_phrase,
        acknowledge_freeze_frame_loss=body.acknowledge_freeze_frame_loss,
        acknowledge_readiness_reset=body.acknowledge_readiness_reset,
        acknowledge_permanent_remain=body.acknowledge_permanent_remain,
        pre_report_saved=body.pre_report_saved,
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("message_de"))
    write_audit(
        db,
        user_id=user.id,
        workshop_id=vehicle.workshop_id,
        action="dtc.clear.simulated",
        resource=f"vehicle:{vehicle.id}",
        detail=body.operator_note or "simulated clear",
    )
    return result


@router.post("/sessions", response_model=DiagnosticSessionOut)
def start_session(
    user: Technician,
    db: DbSession,
    vehicle_id: str = Query(...),
    body: SessionStartBody | None = None,
) -> DiagnosticSessionOut:
    """Startet Sitzung; idempotency_key liefert bei Wiederholung dieselbe Sitzung."""
    wid = require_workshop_id(user)
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    payload = body or SessionStartBody()

    if payload.idempotency_key:
        existing = vh.find_by_idempotency(db, wid, payload.idempotency_key)
        if existing is not None:
            return _session_out(existing, vehicle)

    if payload.work_order_id:
        wo = db.get(WorkOrder, payload.work_order_id)
        if wo is None or wo.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auftrag nicht gefunden")

    conn = simulator.connection_status()
    dtcs = simulator.list_dtcs(vehicle.id)
    session = DiagnosticSession(
        vehicle_id=vehicle.id,
        user_id=user.id,
        workshop_id=wid,
        work_order_id=payload.work_order_id,
        status="open",
        data_source="simulated",
        dtc_snapshot_json=json.dumps([d.model_dump() for d in dtcs], ensure_ascii=False),
        odometer_km=payload.odometer_km if payload.odometer_km is not None else vehicle.odometer_km,
        adapter_name=conn.adapter_name,
        protocol_name=vh.DEFAULT_PROTOCOL,
        notes=payload.notes,
        idempotency_key=payload.idempotency_key,
    )
    db.add(session)
    db.flush()
    vh.capture_session_snapshot(db, session, vehicle, ecu_codes=payload.ecu_codes)
    db.commit()
    db.refresh(session)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="session.start",
        resource=f"session:{session.id}",
        detail=f"vehicle={vehicle.id};data_source=simulated",
    )
    return _session_out(session, vehicle)


@router.post("/sessions/v2", response_model=SessionDetailOut)
def start_session_v2(body: SessionStartRequest, user: Technician, db: DbSession) -> SessionDetailOut:
    """JSON-Body-Variante mit vollem Detail-Response (Phase 09)."""
    wid = require_workshop_id(user)
    vehicle = _tenant_vehicle(db, user, body.vehicle_id)
    if body.idempotency_key:
        existing = vh.find_by_idempotency(db, wid, body.idempotency_key)
        if existing is not None:
            return SessionDetailOut(**vh.session_detail(db, existing, vehicle))
    if body.work_order_id:
        wo = db.get(WorkOrder, body.work_order_id)
        if wo is None or wo.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auftrag nicht gefunden")
    conn = simulator.connection_status()
    session = DiagnosticSession(
        vehicle_id=vehicle.id,
        user_id=user.id,
        workshop_id=wid,
        work_order_id=body.work_order_id,
        status="open",
        data_source="simulated",
        dtc_snapshot_json="[]",
        odometer_km=body.odometer_km if body.odometer_km is not None else vehicle.odometer_km,
        adapter_name=conn.adapter_name,
        protocol_name=vh.DEFAULT_PROTOCOL,
        notes=body.notes,
        idempotency_key=body.idempotency_key,
    )
    db.add(session)
    db.flush()
    vh.capture_session_snapshot(db, session, vehicle, ecu_codes=body.ecu_codes)
    db.commit()
    db.refresh(session)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="session.start",
        resource=f"session:{session.id}",
        detail="v2;data_source=simulated",
    )
    return SessionDetailOut(**vh.session_detail(db, session, vehicle))


@router.get("/sessions", response_model=list[DiagnosticSessionOut])
def list_sessions(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(20, ge=1, le=100),
    vehicle_id: str | None = Query(default=None),
) -> list[DiagnosticSessionOut]:
    wid = require_workshop_id(user)
    q = (
        db.query(DiagnosticSession)
        .join(Vehicle, Vehicle.id == DiagnosticSession.vehicle_id)
        .filter(Vehicle.workshop_id == wid)
    )
    if vehicle_id:
        q = q.filter(DiagnosticSession.vehicle_id == vehicle_id)
    rows = q.order_by(DiagnosticSession.started_at.desc()).limit(limit).all()
    result: list[DiagnosticSessionOut] = []
    for session in rows:
        vehicle = db.get(Vehicle, session.vehicle_id)
        if vehicle is None:
            continue
        result.append(_session_out(session, vehicle))
    return result


@router.get("/sessions/compare", response_model=SessionCompareOut)
def compare_sessions(
    user: CurrentUser,
    db: DbSession,
    before: str = Query(..., description="Frühere Sitzungs-ID"),
    after: str = Query(..., description="Spätere Sitzungs-ID"),
) -> SessionCompareOut:
    wid = require_workshop_id(user)
    before_s, before_v = _tenant_session(db, user, before)
    after_s, after_v = _tenant_session(db, user, after)
    if before_v.id != after_v.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vergleich nur für dasselbe Fahrzeug",
        )
    if before_s.workshop_id != wid or after_s.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    if before_s.started_at and after_s.started_at and before_s.started_at > after_s.started_at:
        before_s, after_s = after_s, before_s
    return SessionCompareOut(**vh.compare_sessions(db, before_s, after_s))


@router.get("/sessions/{session_id}", response_model=SessionDetailOut)
def get_session_detail(session_id: str, user: CurrentUser, db: DbSession) -> SessionDetailOut:
    session, vehicle = _tenant_session(db, user, session_id)
    return SessionDetailOut(**vh.session_detail(db, session, vehicle))


@router.post("/sessions/{session_id}/snapshot", response_model=SessionDetailOut)
def refresh_snapshot(session_id: str, user: Technician, db: DbSession) -> SessionDetailOut:
    session, vehicle = _tenant_session(db, user, session_id)
    if session.status != "open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nur offene Sitzungen")
    vh.capture_session_snapshot(db, session, vehicle)
    db.commit()
    db.refresh(session)
    return SessionDetailOut(**vh.session_detail(db, session, vehicle))


@router.post("/sessions/{session_id}/close", response_model=DiagnosticSessionOut)
def close_session(
    session_id: str,
    user: Technician,
    db: DbSession,
    auto_pdf: bool = Query(
        default=False,
        description="Optional: unveränderlichen PDF-Berichtssnapshot automatisch erzeugen",
    ),
) -> DiagnosticSessionOut:
    wid = require_workshop_id(user)
    session, vehicle = _tenant_session(db, user, session_id)
    if session.status != "open":
        return _session_out(session, vehicle)
    vh.close_session(db, session, vehicle)
    db.commit()
    db.refresh(session)
    if auto_pdf:
        create_report(
            db,
            session,
            title=f"Auto-Bericht {vehicle.make} {vehicle.model}",
            notes=session.notes,
            recommendations=None,
            auto_generated=True,
        )
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="session.close",
        resource=f"session:{session.id}",
        detail="auto_saved" + (";auto_pdf" if auto_pdf else ""),
    )
    return _session_out(session, vehicle)


@router.post("/sessions/{session_id}/abort", response_model=SessionDetailOut)
def abort_session(
    session_id: str,
    body: SessionAbortRequest,
    user: Technician,
    db: DbSession,
) -> SessionDetailOut:
    wid = require_workshop_id(user)
    session, vehicle = _tenant_session(db, user, session_id)
    if session.status != "open":
        return SessionDetailOut(**vh.session_detail(db, session, vehicle))
    vh.abort_session(db, session, vehicle, body.reason)
    db.commit()
    db.refresh(session)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="session.abort",
        resource=f"session:{session.id}",
        detail=body.reason,
    )
    return SessionDetailOut(**vh.session_detail(db, session, vehicle))
