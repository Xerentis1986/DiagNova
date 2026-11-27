"""Phase 09 – Digitale Fahrzeugakte, Lookup, Vergleich, Messwerte."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession, require_roles
from app.models import DiagnosticSession, User, Vehicle, VehicleRecordNote, WorkOrder
from app.schemas.vehicle_history import (
    MeasurementSeriesOut,
    VehicleLookupOut,
    VehicleRecordNoteCreate,
    VehicleRecordOut,
)
from app.services.audit import write_audit
from app.services.tenant import require_workshop_id, require_write_role
from app.services import vehicle_history as vh

router = APIRouter(prefix="/vehicle-records", tags=["vehicle-records"])

Technician = Annotated[User, Depends(require_roles("admin", "technician"))]


def _tenant_vehicle(db: DbSession, user: User, vehicle_id: str) -> Vehicle:
    wid = require_workshop_id(user)
    vehicle = vh.get_tenant_vehicle(db, wid, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")
    return vehicle


@router.get("/lookup", response_model=VehicleLookupOut)
def lookup_record(
    user: CurrentUser,
    db: DbSession,
    vin: str | None = Query(default=None, max_length=17),
    license_plate: str | None = Query(default=None, max_length=32),
) -> VehicleLookupOut:
    wid = require_workshop_id(user)
    if not vin and not license_plate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vin oder license_plate erforderlich",
        )
    matches = vh.lookup_vehicles(db, wid, vin=vin, license_plate=license_plate)
    records = [VehicleRecordOut(**vh.build_vehicle_record(db, v, wid)) for v in matches]
    q = vin or license_plate or ""
    return VehicleLookupOut(
        query=q,
        matches=records,
        disclaimer_de=(
            "Nur Fahrzeuge des eigenen Mandanten. Beispieldaten/Simulation sind gekennzeichnet – "
            "keine erfundenen Historien als echt."
        ),
    )


@router.get("/{vehicle_id}", response_model=VehicleRecordOut)
def get_vehicle_record(vehicle_id: str, user: CurrentUser, db: DbSession) -> VehicleRecordOut:
    wid = require_workshop_id(user)
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    return VehicleRecordOut(**vh.build_vehicle_record(db, vehicle, wid))


@router.get("/{vehicle_id}/timeline")
def get_timeline(vehicle_id: str, user: CurrentUser, db: DbSession) -> dict:
    wid = require_workshop_id(user)
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    return {
        "vehicle_id": vehicle.id,
        "timeline": vh.build_timeline(db, vehicle, wid),
        "disclaimer_de": (
            "Chronologischer Zeitstrahl – Demo/Beispieldaten und Simulationssitzungen sind markiert."
        ),
    }


@router.get("/{vehicle_id}/measurements", response_model=MeasurementSeriesOut)
def get_measurements(
    vehicle_id: str,
    user: CurrentUser,
    db: DbSession,
    pid: int | None = Query(default=None, ge=0, le=255),
    from_at: datetime | None = None,
    to_at: datetime | None = None,
    limit: int = Query(default=500, ge=1, le=500),
) -> MeasurementSeriesOut:
    wid = require_workshop_id(user)
    _tenant_vehicle(db, user, vehicle_id)
    data = vh.list_measurements(
        db, vehicle_id, wid, pid=pid, from_at=from_at, to_at=to_at, limit=limit
    )
    return MeasurementSeriesOut(**data)


@router.post("/{vehicle_id}/notes", status_code=status.HTTP_201_CREATED)
def add_note(
    vehicle_id: str,
    body: VehicleRecordNoteCreate,
    user: Technician,
    db: DbSession,
) -> dict:
    wid = require_workshop_id(user)
    require_write_role(user)
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    if body.work_order_id:
        wo = db.get(WorkOrder, body.work_order_id)
        if wo is None or wo.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Auftrag nicht gefunden")
    if body.session_id:
        sess = db.get(DiagnosticSession, body.session_id)
        if sess is None or sess.vehicle_id != vehicle.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
        if sess.workshop_id and sess.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sitzung nicht gefunden")
    note = VehicleRecordNote(
        workshop_id=wid,
        vehicle_id=vehicle.id,
        user_id=user.id,
        work_order_id=body.work_order_id,
        session_id=body.session_id,
        note_type=body.note_type,
        body=body.body,
        odometer_km=body.odometer_km if body.odometer_km is not None else vehicle.odometer_km,
        is_example_data=False,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="vehicle_record.note",
        resource=f"vehicle:{vehicle.id}",
        detail=body.note_type,
    )
    return {
        "id": note.id,
        "vehicle_id": note.vehicle_id,
        "note_type": note.note_type,
        "body": note.body,
        "odometer_km": note.odometer_km,
        "created_at": note.created_at,
        "authenticity": "recorded",
    }

