"""Seed demo users and example vehicles. Klar als Beispieldaten gekennzeichnet."""

from __future__ import annotations

from sqlalchemy.orm import Session

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.data.phase06_sources import (
    BASELINE_DTC_CODES_UNKNOWN,
    BASELINE_ECUS,
    BASELINE_PIDS,
    BASELINE_UNITS,
    DOCUMENTED_SOURCES,
)
from app.models import User, Vehicle
from app.models.diagnostic_data import (
    DataLicenseSource,
    DiagDatasetVersion,
    DiagDtcDefinition,
    DiagEcuDefinition,
    DiagPidDefinition,
    DiagUnitDefinition,
)
from app.services.simulator import simulated_vin

EXAMPLE_VEHICLES = [
    {
        "make": "Volkswagen",
        "model": "Golf VII",
        "year": 2017,
        "engine": "1.4 TSI",
        "fuel_type": "Benzin",
        "license_plate": "W-DEMO-01",
        "series": "VII",
        "catalog_brand_slug": "vw",
        "odometer_km": 98420,
    },
    {
        "make": "Audi",
        "model": "A4 B9",
        "year": 2019,
        "engine": "2.0 TDI",
        "fuel_type": "Diesel",
        "license_plate": "W-DEMO-02",
        "series": "B9",
        "catalog_brand_slug": "audi",
        "odometer_km": 67210,
    },
    {
        "make": "BMW",
        "model": "320d G20",
        "year": 2020,
        "engine": "2.0 Diesel",
        "fuel_type": "Diesel",
        "license_plate": "W-DEMO-03",
        "series": "G20",
        "catalog_brand_slug": "bmw",
        "odometer_km": 45100,
    },
    {
        "make": "Mercedes-Benz",
        "model": "C 200 W205",
        "year": 2018,
        "engine": "1.5 Turbo",
        "fuel_type": "Benzin",
        "license_plate": "W-DEMO-04",
        "series": "W205",
        "catalog_brand_slug": "mercedes-benz",
        "odometer_km": 110340,
    },
    {
        "make": "Škoda",
        "model": "Octavia III",
        "year": 2016,
        "engine": "1.6 TDI",
        "fuel_type": "Diesel",
        "license_plate": "W-DEMO-05",
        "series": "III",
        "catalog_brand_slug": "skoda",
        "odometer_km": 152000,
    },
    {
        "make": "Seat",
        "model": "Leon III",
        "year": 2018,
        "engine": "1.5 TSI",
        "fuel_type": "Benzin",
        "license_plate": "W-DEMO-06",
        "series": "III",
        "catalog_brand_slug": "seat",
        "odometer_km": 88900,
    },
    {
        "make": "Opel",
        "model": "Astra K",
        "year": 2017,
        "engine": "1.4 Turbo",
        "fuel_type": "Benzin",
        "license_plate": "W-DEMO-07",
        "series": "K",
        "catalog_brand_slug": "opel",
        "odometer_km": 121500,
    },
    {
        "make": "Ford",
        "model": "Focus Mk4",
        "year": 2021,
        "engine": "1.0 EcoBoost",
        "fuel_type": "Benzin",
        "license_plate": "W-DEMO-08",
        "series": "Mk4",
        "catalog_brand_slug": "ford",
        "odometer_km": 33400,
    },
    {
        "make": "Toyota",
        "model": "Corolla",
        "year": 2022,
        "engine": "1.8 Hybrid",
        "fuel_type": "Hybrid",
        "license_plate": "W-DEMO-09",
        "series": "E210",
        "catalog_brand_slug": "toyota",
        "odometer_km": 21800,
    },
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
                    series=item.get("series"),
                    odometer_km=item.get("odometer_km"),
                    catalog_brand_slug=item.get("catalog_brand_slug"),
                    is_example_data=True,
                    notes="Beispieldaten für Demo – keine echte Markenabdeckung / Fahrzeugdiagnose.",
                )
            )
        db.commit()

    seed_phase06_baseline(db)


def seed_phase06_baseline(db: Session) -> None:
    """Lizenzquellen + generische Baseline (PIDs/ECUs/Units/DTC-Codes ohne erfundene Texte)."""
    if db.scalar(select(DataLicenseSource).limit(1)) is None:
        for src in DOCUMENTED_SOURCES:
            db.add(DataLicenseSource(**src))
        db.commit()

    if db.scalar(select(DiagDatasetVersion).where(DiagDatasetVersion.version_label == "baseline-06")):
        return

    structural = db.scalar(select(DataLicenseSource).where(DataLicenseSource.key == "diagnova-structural"))
    pid_src = db.scalar(select(DataLicenseSource).where(DataLicenseSource.key == "sae-j1979-pid-subset"))
    ecu_src = db.scalar(select(DataLicenseSource).where(DataLicenseSource.key == "iso-15765-4-obd-addresses"))
    dtc_src = db.scalar(
        select(DataLicenseSource).where(DataLicenseSource.key == "dtc-descriptions-unavailable")
    )
    if not all([structural, pid_src, ecu_src, dtc_src]):
        return

    version = DiagDatasetVersion(
        version_label="baseline-06",
        status="published",
        source_id=structural.id,  # type: ignore[union-attr]
        notes_de="Phase-06 Baseline: generische PIDs/ECUs/Units; DTC-Codes ohne Beschreibungstext.",
    )
    db.add(version)
    db.flush()

    for u in BASELINE_UNITS:
        db.add(
            DiagUnitDefinition(
                dataset_version_id=version.id,
                source_id=structural.id,  # type: ignore[union-attr]
                **u,
            )
        )
    for p in BASELINE_PIDS:
        db.add(
            DiagPidDefinition(
                dataset_version_id=version.id,
                source_id=pid_src.id,  # type: ignore[union-attr]
                data_scope="generic",
                kind="pid",
                **p,
            )
        )
    for e in BASELINE_ECUS:
        db.add(
            DiagEcuDefinition(
                dataset_version_id=version.id,
                source_id=ecu_src.id,  # type: ignore[union-attr]
                data_scope="generic",
                software_variant=None,
                **e,
            )
        )
    for code in BASELINE_DTC_CODES_UNKNOWN:
        db.add(
            DiagDtcDefinition(
                dataset_version_id=version.id,
                source_id=dtc_src.id,  # type: ignore[union-attr]
                code=code,
                description_de=None,
                description_status="unknown",
                data_scope="generic",
                system=code[0],
                notes_de="Nur Code; keine kommerzielle Beschreibungstexte übernommen.",
            )
        )
    db.commit()
