"""Phase 11 – Geführte Diagnose: Überblick, Messwertgruppen, DTC-Hilfe."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.service import DtcHelpOut, GuidedOverviewOut, MeasurementGroupOut
from app.services import guided_diagnosis as guided
from app.services.tenant import require_workshop_id
from app.models import Vehicle

router = APIRouter(prefix="/guided", tags=["guided"])


@router.get("/overview", response_model=GuidedOverviewOut)
def overview(_user: CurrentUser) -> GuidedOverviewOut:
    return guided.guided_overview()


@router.get("/measurement-groups", response_model=list[MeasurementGroupOut])
def list_groups(_user: CurrentUser) -> list[MeasurementGroupOut]:
    return guided.measurement_groups()


@router.get("/measurement-groups/{group_id}")
def group_readings(group_id: str, vehicle_id: str, user: CurrentUser, db: DbSession) -> dict:
    wid = require_workshop_id(user)
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")
    payload = guided.group_live_readings(vehicle.id, vehicle.vin or "DEMO", group_id)
    if payload.get("error") == "unknown_group":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=payload["message_de"])
    return payload


@router.get("/dtc/{code}", response_model=DtcHelpOut)
def dtc_help(code: str, _user: CurrentUser, db: DbSession) -> DtcHelpOut:
    return guided.dtc_help(db, code)
