"""VIN-Hilfen (Phase 02). Keine echte WMI-/Decoder-DB – nur Formatprüfung und Normalisierung."""

from __future__ import annotations

import re

VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


def normalize_vin(raw: str | None) -> str:
    return (raw or "").strip().upper().replace(" ", "")


def validate_vin(raw: str | None) -> tuple[bool, str | None]:
    vin = normalize_vin(raw)
    if not vin:
        return False, "VIN fehlt"
    if len(vin) != 17:
        return False, "VIN muss 17 Zeichen haben"
    if any(c in vin for c in "IOQ"):
        return False, "VIN darf keine Buchstaben I, O oder Q enthalten"
    if not VIN_RE.match(vin):
        return False, "VIN enthält ungültige Zeichen"
    return True, None
