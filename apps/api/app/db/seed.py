"""Seed demo users and example vehicles. Klar als Beispieldaten gekennzeichnet."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import User, Vehicle
from app.services.simulator import simulated_vin

EXAMPLE_VEHICLES = [
    {"make": "Volkswagen", "model": "Golf VII", "year": 2017, "engine": "1.4 TSI", "fuel_type": "Benzin", "license_plate": "W-DEMO-01"},
    {"make": "Audi", "model": "A4 B9", "year": 2019, "engine": "2.0 TDI", "fuel_type": "Diesel", "license_plate": "W-DEMO-02"},
    {"make": "BMW", "model": "320d G20", "year": 2020, "engine": "2.0 Diesel", "fuel_type": "Diesel", "license_plate": "W-DEMO-03"},
    {"make": "Mercedes-Benz", "model": "C 200 W205", "year": 2018, "engine": "1.5 Turbo", "fuel_type": "Benzin", "license_plate": "W-DEMO-04"},
    {"make": "Škoda", "model": "Octavia III", "year": 2016, "engine": "1.6 TDI", "fuel_type": "Diesel", "license_plate": "W-DEMO-05"},
    {"make": "Seat", "model": "Leon III", "year": 2018, "engine": "1.5 TSI", "fuel_type": "Benzin", "license_plate": "W-DEMO-06"},
    {"make": "Opel", "model": "Astra K", "year": 2017, "engine": "1.4 Turbo", "fuel_type": "Benzin", "license_plate": "W-DEMO-07"},
    {"make": "Ford", "model": "Focus Mk4", "year": 2021, "engine": "1.0 EcoBoost", "fuel_type": "Benzin", "license_plate": "W-DEMO-08"},
    {"make": "Toyota", "model": "Corolla", "year": 2022, "engine": "1.8 Hybrid", "fuel_type": "Hybrid", "license_plate": "W-DEMO-09"},
]


def seed_all(db: Session) -> None:
    settings = get_settings()
    if db.query(User).count() == 0:
        db.add(
            User(
                email=settings.seed_admin_email.lower(),
                full_name="Admin Demo",
                hashed_password=hash_password(settings.seed_admin_password),
                role="admin",
            )
        )
        db.add(
            User(
                email=settings.seed_tech_email.lower(),
                full_name="Techniker Demo",
                hashed_password=hash_password(settings.seed_tech_password),
                role="technician",
            )
        )
        db.commit()

    if db.query(Vehicle).count() == 0:
        for idx, item in enumerate(EXAMPLE_VEHICLES):
            # temporary id for VIN derivation – replaced by ORM uuid after flush
            temp_id = f"seed{idx:04d}xxxx"
            vin = simulated_vin(item["make"], temp_id)
            # ensure uniqueness
            vin = f"{vin[:14]}{idx:03d}"[:17]
            db.add(
                Vehicle(
                    make=item["make"],
                    model=item["model"],
                    year=item["year"],
                    vin=vin,
                    license_plate=item["license_plate"],
                    engine=item["engine"],
                    fuel_type=item["fuel_type"],
                    is_example_data=True,
                    notes="Beispieldaten für Demo – keine echte Markenabdeckung / Fahrzeugdiagnose.",
                )
            )
        db.commit()
