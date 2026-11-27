from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models import DiagnosticSession, Vehicle
from app.schemas.api import DashboardOut, DiagnosticSessionOut, VehicleOut
from app.services import simulator
from app.services.tenant import require_workshop_id
import json

router = APIRouter(tags=["dashboard"])

PLANNED = [
    {"id": "ecu", "label": "Steuergeräte (OBD simuliert)", "status": "simulated"},
    {"id": "service", "label": "Servicefunktionen (Gates, deaktiviert)", "status": "simulated"},
    {"id": "guided", "label": "Geführte Diagnose", "status": "simulated"},
    {"id": "coding", "label": "Codierung / Programmierung (Gates)", "status": "simulated"},
    {"id": "subscriptions", "label": "Abos & Lizenzen (Stub)", "status": "simulated"},
    {"id": "admin", "label": "Administration", "status": "simulated"},
    {"id": "lkw", "label": "LKW / Nutzfahrzeug (J1939/RP1210)", "status": "planned"},
    {"id": "actuator", "label": "Stellglieddiagnose (Gerüst)", "status": "planned"},
    {"id": "flash", "label": "Flash Live", "status": "planned"},
]


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    user: CurrentUser,
    db: DbSession,
    active_vehicle_id: str | None = Query(None),
) -> DashboardOut:
    settings = get_settings()
    wid = require_workshop_id(user)
    active: Vehicle | None = None
    if active_vehicle_id:
        candidate = db.get(Vehicle, active_vehicle_id)
        if candidate is not None and candidate.workshop_id == wid:
            active = candidate
    if active is None:
        active = (
            db.query(Vehicle)
            .filter(Vehicle.workshop_id == wid, Vehicle.archived_at.is_(None))
            .order_by(Vehicle.make)
            .first()
        )

    sessions = (
        db.query(DiagnosticSession)
        .join(Vehicle, Vehicle.id == DiagnosticSession.vehicle_id)
        .filter(Vehicle.workshop_id == wid)
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
