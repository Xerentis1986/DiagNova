from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models import DiagnosticSession, Vehicle
from app.schemas.api import DashboardOut, DiagnosticSessionOut, VehicleOut
from app.services import simulator
import json

router = APIRouter(tags=["dashboard"])

PLANNED = [
    {"id": "ecu", "label": "Steuergeräte", "status": "planned"},
    {"id": "service", "label": "Servicefunktionen", "status": "planned"},
    {"id": "coding", "label": "Codierung", "status": "planned"},
    {"id": "actuator", "label": "Stellglieddiagnose", "status": "planned"},
    {"id": "flash", "label": "Programmierung", "status": "planned"},
]


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    _user: CurrentUser,
    db: DbSession,
    active_vehicle_id: str | None = Query(None),
) -> DashboardOut:
    settings = get_settings()
    active: Vehicle | None = None
    if active_vehicle_id:
        active = db.get(Vehicle, active_vehicle_id)
    if active is None:
        active = db.query(Vehicle).order_by(Vehicle.make).first()

    sessions = (
        db.query(DiagnosticSession)
        .order_by(DiagnosticSession.started_at.desc())
        .limit(5)
        .all()
    )
    recent: list[DiagnosticSessionOut] = []
    for session in sessions:
        vehicle = db.get(Vehicle, session.vehicle_id)
        if vehicle is None:
            continue
        dtcs = json.loads(session.dtc_snapshot_json or "[]")
        recent.append(
            DiagnosticSessionOut(
                id=session.id,
                vehicle_id=session.vehicle_id,
                vehicle_label=f"{vehicle.make} {vehicle.model}",
                started_at=session.started_at,
                ended_at=session.ended_at,
                data_source=session.data_source,  # type: ignore[arg-type]
                dtc_count=len(dtcs),
                status=session.status,  # type: ignore[arg-type]
            )
        )

    return DashboardOut(
        active_vehicle=VehicleOut.model_validate(active) if active else None,
        connection=simulator.connection_status(),
        recent_sessions=recent,
        demo_mode=settings.demo_mode,
        planned_modules=PLANNED,
    )
