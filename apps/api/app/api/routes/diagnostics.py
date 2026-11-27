from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import DiagnosticReport, DiagnosticSession, User, Vehicle
from app.schemas.api import (
    ClearDtcRequest,
    ConnectionStatusOut,
    DiagnosticSessionOut,
    DtcOut,
    LiveDataOut,
    ReportCreate,
    ReportOut,
)
from app.services import simulator
from app.services.audit import write_audit
from app.services.reports import create_report, report_to_csv, report_to_pdf
from app.services.tenant import require_workshop_id

router = APIRouter(tags=["diagnostics"])

Technician = Annotated[User, Depends(require_roles("admin", "technician"))]


def _tenant_vehicle(db: DbSession, user: User, vehicle_id: str) -> Vehicle:
    wid = require_workshop_id(user)
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")
    return vehicle


def _session_out(session: DiagnosticSession, vehicle: Vehicle) -> DiagnosticSessionOut:
    dtcs = json.loads(session.dtc_snapshot_json or "[]")
    return DiagnosticSessionOut(
        id=session.id,
        vehicle_id=session.vehicle_id,
        vehicle_label=f"{vehicle.make} {vehicle.model}",
        started_at=session.started_at,
        ended_at=session.ended_at,
        data_source=session.data_source,  # type: ignore[arg-type]
        dtc_count=len(dtcs),
        status=session.status,  # type: ignore[arg-type]
    )


@router.get("/connection", response_model=ConnectionStatusOut)
def get_connection(_user: CurrentUser) -> ConnectionStatusOut:
    return simulator.connection_status()


@router.get("/diagnostics/pids")
def list_pids(_user: CurrentUser) -> dict:
    return {"data_source": "simulated", "pids": simulator.supported_pids()}


@router.get("/diagnostics/{vehicle_id}/dtcs", response_model=list[DtcOut])
def get_dtcs(vehicle_id: str, user: CurrentUser, db: DbSession) -> list[DtcOut]:
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    return simulator.list_dtcs(vehicle.id)


@router.get("/diagnostics/{vehicle_id}/live", response_model=LiveDataOut)
def get_live(vehicle_id: str, user: CurrentUser, db: DbSession) -> LiveDataOut:
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    return simulator.live_data(vehicle.id, vehicle.vin)


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
) -> DiagnosticSessionOut:
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    dtcs = simulator.list_dtcs(vehicle.id)
    session = DiagnosticSession(
        vehicle_id=vehicle.id,
        user_id=user.id,
        status="open",
        data_source="simulated",
        dtc_snapshot_json=json.dumps([d.model_dump() for d in dtcs], ensure_ascii=False),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=vehicle.workshop_id,
        action="session.start",
        resource=f"session:{session.id}",
        detail=f"vehicle={vehicle.id}",
    )
    return _session_out(session, vehicle)


@router.get("/sessions", response_model=list[DiagnosticSessionOut])
def list_sessions(
    user: CurrentUser,
    db: DbSession,
    limit: int = Query(20, ge=1, le=100),
) -> list[DiagnosticSessionOut]:
    wid = require_workshop_id(user)
    rows = (
        db.query(DiagnosticSession)
        .join(Vehicle, Vehicle.id == DiagnosticSession.vehicle_id)
        .filter(Vehicle.workshop_id == wid)
        .order_by(DiagnosticSession.started_at.desc())
        .limit(limit)
        .all()
    )
    result: list[DiagnosticSessionOut] = []
    for session in rows:
        vehicle = db.get(Vehicle, session.vehicle_id)
        if vehicle is None:
            continue
        result.append(_session_out(session, vehicle))
    return result


@router.post("/sessions/{session_id}/close", response_model=DiagnosticSessionOut)
def close_session(session_id: str, user: Technician, db: DbSession) -> DiagnosticSessionOut:
    wid = require_workshop_id(user)
    session = db.get(DiagnosticSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    vehicle = db.get(Vehicle, session.vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    session.status = "closed"
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="session.close",
        resource=f"session:{session.id}",
    )
    return _session_out(session, vehicle)


def _tenant_report(db: DbSession, user: User, report_id: str) -> DiagnosticReport:
    wid = require_workshop_id(user)
    report = db.get(DiagnosticReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bericht nicht gefunden")
    session = db.get(DiagnosticSession, report.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bericht nicht gefunden")
    vehicle = db.get(Vehicle, session.vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bericht nicht gefunden")
    return report


@router.post("/reports", response_model=ReportOut)
def create_diagnostic_report(body: ReportCreate, user: Technician, db: DbSession) -> ReportOut:
    wid = require_workshop_id(user)
    session = db.get(DiagnosticSession, body.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    vehicle = db.get(Vehicle, session.vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    report = create_report(db, session, body.title)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="report.create",
        resource=f"report:{report.id}",
    )
    return ReportOut(
        id=report.id,
        session_id=report.session_id,
        title=report.title,
        created_at=report.created_at,
        content=json.loads(report.content_json),
    )


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: str, user: CurrentUser, db: DbSession) -> ReportOut:
    report = _tenant_report(db, user, report_id)
    return ReportOut(
        id=report.id,
        session_id=report.session_id,
        title=report.title,
        created_at=report.created_at,
        content=json.loads(report.content_json),
    )


@router.get("/reports/{report_id}/export.csv")
def export_csv(report_id: str, user: CurrentUser, db: DbSession) -> Response:
    report = _tenant_report(db, user, report_id)
    csv_text = report_to_csv(report)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="diagnova-report-{report_id}.csv"'},
    )


@router.get("/reports/{report_id}/export.pdf")
def export_pdf(report_id: str, user: CurrentUser, db: DbSession) -> Response:
    report = _tenant_report(db, user, report_id)
    pdf = report_to_pdf(report)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="diagnova-report-{report_id}.pdf"'},
    )