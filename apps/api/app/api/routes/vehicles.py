from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.models import Vehicle
from app.schemas.api import VehicleOut

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
