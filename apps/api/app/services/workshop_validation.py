"""Validierung VIN, Kennzeichen, Kilometerstand, Motorisierung (Phase 08)."""

from __future__ import annotations

import re

from app.services.vin import normalize_vin, validate_vin

PLATE_RE = re.compile(r"^[A-Z0-9ÄÖÜ\- ]{2,32}$", re.IGNORECASE)
ENGINE_RE = re.compile(r"^[\w\.\-\+\/ ]{1,64}$", re.UNICODE)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[\d\s\+\-\/\(\)]{5,64}$")
LOGO_MAX_CHARS = 120_000  # ~90 KB Base64 – minimale Speicherung


def normalize_plate(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = " ".join(raw.strip().upper().split())
    return cleaned or None


def validate_plate(raw: str | None) -> tuple[bool, str | None]:
    if raw is None or not str(raw).strip():
        return True, None
    plate = normalize_plate(raw)
    assert plate is not None
    if len(plate) > 32:
        return False, "Kennzeichen zu lang"
    if not PLATE_RE.match(plate):
        return False, "Kennzeichen enthält ungültige Zeichen"
    return True, None


def validate_odometer(value: int | None) -> tuple[bool, str | None]:
    if value is None:
        return True, None
    if value < 0:
        return False, "Kilometerstand darf nicht negativ sein"
    if value > 9_999_999:
        return False, "Kilometerstand unrealistisch hoch"
    return True, None


def validate_engine(raw: str | None) -> tuple[bool, str | None]:
    if raw is None or not str(raw).strip():
        return True, None
    eng = raw.strip()
    if len(eng) > 64:
        return False, "Motorisierung zu lang"
    if not ENGINE_RE.match(eng):
        return False, "Motorisierung enthält ungültige Zeichen"
    return True, None


def validate_optional_email(raw: str | None) -> tuple[bool, str | None]:
    if raw is None or not str(raw).strip():
        return True, None
    email = raw.strip().lower()
    if len(email) > 255 or not EMAIL_RE.match(email):
        return False, "E-Mail ungültig"
    return True, None


def validate_optional_phone(raw: str | None) -> tuple[bool, str | None]:
    if raw is None or not str(raw).strip():
        return True, None
    phone = raw.strip()
    if not PHONE_RE.match(phone):
        return False, "Telefonnummer ungültig"
    return True, None


def validate_logo_data_url(raw: str | None) -> tuple[bool, str | None]:
    if raw is None or not str(raw).strip():
        return True, None
    data = raw.strip()
    if len(data) > LOGO_MAX_CHARS:
        return False, "Logo zu groß (max. ~90 KB Data-URL)"
    if not data.startswith("data:image/"):
        return False, "Logo muss Data-URL (image/*) sein"
    if ";base64," not in data:
        return False, "Logo muss Base64-Data-URL sein"
    return True, None


def validate_vehicle_fields(
    *,
    vin: str | None = None,
    license_plate: str | None = None,
    odometer_km: int | None = None,
    engine: str | None = None,
    require_vin: bool = False,
) -> list[str]:
    errors: list[str] = []
    if require_vin or vin is not None:
        ok, err = validate_vin(vin)
        if not ok and err:
            errors.append(err)
    ok, err = validate_plate(license_plate)
    if not ok and err:
        errors.append(err)
    ok, err = validate_odometer(odometer_km)
    if not ok and err:
        errors.append(err)
    ok, err = validate_engine(engine)
    if not ok and err:
        errors.append(err)
    return errors


__all__ = [
    "normalize_plate",
    "normalize_vin",
    "validate_engine",
    "validate_logo_data_url",
    "validate_odometer",
    "validate_optional_email",
    "validate_optional_phone",
    "validate_plate",
    "validate_vehicle_fields",
    "validate_vin",
]
