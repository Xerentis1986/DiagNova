from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.api.routes.preferences import record_recent_selection
from app.data.dach_brands import get_brand, get_model, get_variant
from app.models import Vehicle
from app.schemas.api import VehicleConfirmRequest, VehicleOut, VehicleUpdateRequest
from app.services.audit import write_audit
from app.services.vin import normalize_vin, validate_vin

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
def list_vehicles(_user: CurrentUser, db: DbSession) -> list[Vehicle]:
    return db.query(Vehicle).order_by(Vehicle.make, Vehicle.model).all()


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: str, _user: CurrentUser, db: DbSession) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")
    return vehicle


@router.post("/confirm", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def confirm_vehicle_selection(
    body: VehicleConfirmRequest,
    user: CurrentUser,
    db: DbSession,
) -> Vehicle:
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

    existing = db.query(Vehicle).filter(Vehicle.vin == vin).first()
    if existing is not None:
        # Bestehendes Fahrzeug aktualisieren (manuelle Korrektur / Wiederwahl)
        existing.make = brand["name"]
        existing.model = model["name"]
        existing.year = body.year
        existing.series = variant["series"]
        existing.engine = variant["engine"]
        existing.fuel_type = variant["fuel_type"]
        existing.license_plate = (body.license_plate or "").strip() or None
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
            action="vehicle_confirm_existing",
            resource=f"vehicle:{existing.id}",
            detail=vin,
        )
        db.commit()
        db.refresh(existing)
        return existing

    vehicle = Vehicle(
        make=brand["name"],
        model=model["name"],
        year=body.year,
        vin=vin,
        license_plate=(body.license_plate or "").strip() or None,
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
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")

    if body.vin is not None:
        vin = normalize_vin(body.vin)
        ok, err = validate_vin(vin)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
        clash = db.query(Vehicle).filter(Vehicle.vin == vin, Vehicle.id != vehicle_id).first()
        if clash is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="VIN bereits vergeben")
        vehicle.vin = vin

    if body.license_plate is not None:
        vehicle.license_plate = body.license_plate.strip() or None
    if body.odometer_km is not None:
        vehicle.odometer_km = body.odometer_km
    if body.notes is not None:
        vehicle.notes = body.notes

    db.add(vehicle)
    write_audit(
        db,
        user_id=user.id,
        action="vehicle_update",
        resource=f"vehicle:{vehicle.id}",
        detail="vin/plate/odometer",
    )
    db.commit()
    db.refresh(vehicle)
    return vehicle
