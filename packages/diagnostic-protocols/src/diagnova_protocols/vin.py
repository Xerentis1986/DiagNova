"""Mode 09 PID 02 – VIN-Dekodierung aus Multiframe-/Einzelantworten."""

from __future__ import annotations

import re


_VIN_CHAR = re.compile(r"^[A-HJ-NPR-Z0-9]$")


def decode_vin_bytes(data: list[int] | bytes | tuple[int, ...]) -> str | None:
    """
    Extrahiert VIN aus Mode-09-Payload (ohne Service/PID-Header).
    Gibt None zurück wenn keine gültige 17-Zeichen-VIN erkennbar –
    Aufrufer muss das als 'unavailable' kennzeichnen, nicht als leeren String vortäuschen.
    """
    chars: list[str] = []
    for b in data:
        if b == 0x00:
            continue
        if 32 <= b <= 126:
            ch = chr(b)
            if _VIN_CHAR.match(ch):
                chars.append(ch)
    vin = "".join(chars)
    if len(vin) >= 17:
        candidate = vin[:17]
        if all(_VIN_CHAR.match(c) for c in candidate):
            return candidate
    if len(vin) == 17:
        return vin
    return None


def decode_vin_from_mode09_frames(payloads: list[list[int] | bytes | tuple[int, ...]]) -> dict:
    """
    Kombiniert mehrere Frame-Payloads (nach 49 02 …) zu einer VIN-Struktur.
    Ergebnis immer mit explizitem Status – nie null-Wert ohne Kennzeichnung.
    """
    merged: list[int] = []
    for p in payloads:
        merged.extend(list(p))
    # Manche ECUs liefern Message-Count als erstes Byte
    if merged and merged[0] <= 5 and len(merged) > 17:
        merged = merged[1:]
    vin = decode_vin_bytes(merged)
    if vin:
        return {
            "status": "ok",
            "vin": vin,
            "supported": True,
            "message_de": "VIN gelesen.",
        }
    return {
        "status": "unavailable",
        "vin": None,  # explizit unavailable – nicht als leerer String
        "supported": False,
        "message_de": "VIN nicht lesbar oder von ECU nicht unterstützt.",
        "raw_len": len(merged),
    }
