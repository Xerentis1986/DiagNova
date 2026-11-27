from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.api.routes.preferences import record_recent_selection
from app.data.dach_brands import get_brand, get_model, get_variant
from app.models import Customer, Vehicle
from app.schemas.api import VehicleConfirmRequest, VehicleOut, VehicleUpdateRequest
from app.schemas.workshop import VehicleWorkshopCreate, VehicleWorkshopUpdate
from app.services.audit import write_audit
from app.services.tenant import require_workshop_id, require_write_role
from app.services.vin import normalize_vin, validate_vin
from app.services.workshop_validation import (
    normalize_plate,
    validate_engine,
    validate_odometer,
    validate_plate,
    validate_vehicle_fields,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _tenant_vehicle(db: DbSession, user: CurrentUser, vehicle_id: str) -> Vehicle:
    wid = require_workshop_id(user)
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or vehicle.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")
    return vehicle


@router.get("", response_model=list[VehicleOut])
def list_vehicles(
    user: CurrentUser,
    db: DbSession,
    q: str | None = Query(default=None, max_length=128),
    customer_id: str | None = None,
    include_archived: bool = False,
) -> list[Vehicle]:
    wid = require_workshop_id(user)
    query = db.query(Vehicle).filter(Vehicle.workshop_id == wid)
    if not include_archived:
        query = query.filter(Vehicle.archived_at.is_(None))
    if customer_id:
        query = query.filter(Vehicle.customer_id == customer_id)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            (Vehicle.vin.ilike(term))
            | (Vehicle.license_plate.ilike(term))
            | (Vehicle.make.ilike(term))
            | (Vehicle.model.ilike(term))
        )
    return query.order_by(Vehicle.make, Vehicle.model).all()


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: str, user: CurrentUser, db: DbSession) -> Vehicle:
    return _tenant_vehicle(db, user, vehicle_id)


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(body: VehicleWorkshopCreate, user: CurrentUser, db: DbSession) -> Vehicle:
    require_write_role(user)
    wid = require_workshop_id(user)

    errors = validate_vehicle_fields(
        vin=body.vin,
        license_plate=body.license_plate,
        odometer_km=body.odometer_km,
        engine=body.engine,
        require_vin=True,
    )
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    vin = normalize_vin(body.vin)
    plate = normalize_plate(body.license_plate)

    if body.customer_id:
        customer = db.get(Customer, body.customer_id)
        if customer is None or customer.workshop_id != wid:
            raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    existing = (
        db.query(Vehicle)
        .filter(Vehicle.workshop_id == wid, Vehicle.vin == vin)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="VIN bereits in dieser Werkstatt vorhanden")

    if plate and not body.force_duplicate_plate:
        plate_hit = (
            db.query(Vehicle)
            .filter(
                Vehicle.workshop_id == wid,
                Vehicle.license_plate == plate,
                Vehicle.archived_at.is_(None),
            )
            .first()
        )
        if plate_hit is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "message_de": "Kennzeichen-Dublette – force_duplicate_plate=true zum Fortfahren",
                    "vehicle_id": plate_hit.id,
                },
            )

    vehicle = Vehicle(
        workshop_id=wid,
        customer_id=body.customer_id,
        make=body.make.strip(),
        model=body.model.strip(),
        year=body.year,
        vin=vin,
        license_plate=plate,
        engine=(body.engine or "").strip() or None,
        fuel_type=(body.fuel_type or "").strip() or None,
        series=(body.series or "").strip() or None,
        odometer_km=body.odometer_km,
        is_example_data=False,
        notes=(body.notes or "").strip() or None,
    )
    db.add(vehicle)
    db.flush()
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="vehicle_create",
        resource=f"vehicle:{vehicle.id}",
        detail=vin,
    )
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.patch("/workshop/{vehicle_id}", response_model=VehicleOut)
def update_workshop_vehicle(
    vehicle_id: str, body: VehicleWorkshopUpdate, user: CurrentUser, db: DbSession
) -> Vehicle:
    """Erweiterte Fahrzeugpflege (Kunde, Archiv, Motorisierung)."""
    require_write_role(user)
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    wid = vehicle.workshop_id

    if body.vin is not None:
        vin = normalize_vin(body.vin)
        ok, err = validate_vin(vin)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        clash = (
            db.query(Vehicle)
            .filter(Vehicle.workshop_id == wid, Vehicle.vin == vin, Vehicle.id != vehicle_id)
            .first()
        )
        if clash is not None:
            raise HTTPException(status_code=409, detail="VIN bereits vergeben")
        vehicle.vin = vin

    if body.license_plate is not None:
        ok, err = validate_plate(body.license_plate)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        vehicle.license_plate = normalize_plate(body.license_plate)
    if body.odometer_km is not None:
        ok, err = validate_odometer(body.odometer_km)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        vehicle.odometer_km = body.odometer_km
    if body.engine is not None:
        ok, err = validate_engine(body.engine)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        vehicle.engine = body.engine.strip() or None
    if body.make is not None:
        vehicle.make = body.make.strip()
    if body.model is not None:
        vehicle.model = body.model.strip()
    if body.year is not None:
        vehicle.year = body.year
    if body.fuel_type is not None:
        vehicle.fuel_type = body.fuel_type.strip() or None
    if body.series is not None:
        vehicle.series = body.series.strip() or None
    if body.notes is not None:
        vehicle.notes = body.notes.strip() or None
    if body.customer_id is not None:
        if body.customer_id == "":
            vehicle.customer_id = None
        else:
            customer = db.get(Customer, body.customer_id)
            if customer is None or customer.workshop_id != wid:
                raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
            vehicle.customer_id = customer.id
    if body.archive is True:
        vehicle.archived_at = datetime.now(timezone.utc)
    elif body.archive is False:
        vehicle.archived_at = None

    db.add(vehicle)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="vehicle_workshop_update",
        resource=f"vehicle:{vehicle.id}",
    )
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.post("/confirm", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def confirm_vehicle_selection(
    body: VehicleConfirmRequest,
    user: CurrentUser,
    db: DbSession,
) -> Vehicle:
    wid = require_workshop_id(user)
    brand = get_brand(body.brand_slug)
    if brand is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Marke unbekannt")
    model = get_model(body.brand_slug, body.model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Modell unbekannt")
    variant = get_variant(body.brand_slug, body.model_id, body.variant_id)
    if variant is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Variante unbekannt")
    if not (variant["year_from"] <= body.year <= variant["year_to"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Baujahr muss zwischen {variant['year_from']} und {variant['year_to']} liegen",
        )

    vin = normalize_vin(body.vin)
    ok, err = validate_vin(vin)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    ok, err = validate_plate(body.license_plate)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    ok, err = validate_odometer(body.odometer_km)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)

    plate = normalize_plate(body.license_plate)
    existing = db.query(Vehicle).filter(Vehicle.workshop_id == wid, Vehicle.vin == vin).first()
    if existing is not None:
        existing.make = brand["name"]
        existing.model = model["name"]
        existing.year = body.year
        existing.series = variant["series"]
        existing.engine = variant["engine"]
        existing.fuel_type = variant["fuel_type"]
        existing.license_plate = plate
        existing.odometer_km = body.odometer_km
        existing.catalog_brand_slug = brand["slug"]
        existing.catalog_model_id = model["id"]
        existing.catalog_variant_id = variant["id"]
        if body.notes is not None:
            existing.notes = body.notes
        db.add(existing)
        record_recent_selection(db, user_id=user.id, vehicle=existing)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="vehicle_confirm_existing",
            resource=f"vehicle:{existing.id}",
            detail=vin,
        )
        db.commit()
        db.refresh(existing)
        return existing

    vehicle = Vehicle(
        workshop_id=wid,
        make=brand["name"],
        model=model["name"],
        year=body.year,
        vin=vin,
        license_plate=plate,
        engine=variant["engine"],
        fuel_type=variant["fuel_type"],
        series=variant["series"],
        odometer_km=body.odometer_km,
        catalog_brand_slug=brand["slug"],
        catalog_model_id=model["id"],
        catalog_variant_id=variant["id"],
        is_example_data=False,
        notes=body.notes
        or (
            "Über Markenauswahl bestätigt. Katalogeintrag ≠ Diagnoseabdeckung. "
            "Diagnose im MVP nur simuliert."
        ),
    )
    db.add(vehicle)
    db.flush()
    record_recent_selection(db, user_id=user.id, vehicle=vehicle)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="vehicle_confirm",
        resource=f"vehicle:{vehicle.id}",
        detail=vin,
    )
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: str,
    body: VehicleUpdateRequest,
    user: CurrentUser,
    db: DbSession,
) -> Vehicle:
    vehicle = _tenant_vehicle(db, user, vehicle_id)
    wid = vehicle.workshop_id

    if body.vin is not None:
        vin = normalize_vin(body.vin)
        ok, err = validate_vin(vin)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
        clash = (
            db.query(Vehicle)
            .filter(Vehicle.workshop_id == wid, Vehicle.vin == vin, Vehicle.id != vehicle_id)
            .first()
        )
        if clash is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIN bereits vergeben")
        vehicle.vin = vin

    if body.license_plate is not None:
        ok, err = validate_plate(body.license_plate)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        vehicle.license_plate = normalize_plate(body.license_plate)
    if body.odometer_km is not None:
        ok, err = validate_odometer(body.odometer_km)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        vehicle.odometer_km = body.odometer_km
    if body.notes is not None:
        vehicle.notes = body.notes

    db.add(vehicle)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="vehicle_update",
        resource=f"vehicle:{vehicle.id}",
        detail="vin/plate/odometer",
    )
    db.commit()
    db.refresh(vehicle)
    return vehicle
