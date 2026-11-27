"""ISO 15765-4 OBD-on-CAN Standardadressen – keine OEM-Erweiterungen.

Nur emissionsbezogene Adressen laut ISO 15765-4 / SAE J1979:
- Funktional Request: 0x7DF
- Physikalisch Request: 0x7E0–0x7E7
- Antwort: 0x7E8–0x7EF (Request + 8)

OEM-Adressen für ABS/Airbag/Komfort usw. werden hier bewusst NICHT erfunden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


FUNCTIONAL_REQUEST_11BIT = 0x7DF
PHYSICAL_REQUEST_MIN = 0x7E0
PHYSICAL_REQUEST_MAX = 0x7E7
PHYSICAL_RESPONSE_MIN = 0x7E8
PHYSICAL_RESPONSE_MAX = 0x7EF


@dataclass(frozen=True)
class ObdEcuSlot:
    """Ein Standard-OBD-Steuergeräteplatz (ISO 15765-4)."""

    request_id: int
    response_id: int
    slot_index: int
    role_hint_de: str
    verified_source: str = "ISO 15765-4"

    @property
    def request_hex(self) -> str:
        return f"{self.request_id:03X}"

    @property
    def response_hex(self) -> str:
        return f"{self.response_id:03X}"


# Index 0 = typisch Motor/ECM; weitere Slots = weitere emissionsbezogene ECUs.
# Die Rollen-Hinweise sind Konvention, keine OEM-Garantie.
STANDARD_OBD_SLOTS: tuple[ObdEcuSlot, ...] = tuple(
    ObdEcuSlot(
        request_id=0x7E0 + i,
        response_id=0x7E8 + i,
        slot_index=i,
        role_hint_de=(
            "Motor/ECM (OBD-Konvention)"
            if i == 0
            else ("Getriebe/TCM (OBD-Konvention, falls vorhanden)" if i == 1 else f"OBD-ECU-Slot {i}")
        ),
    )
    for i in range(8)
)


def normalize_ecu_id(ecu_id: str | int | None) -> str | None:
    if ecu_id is None:
        return None
    if isinstance(ecu_id, int):
        return f"{ecu_id:03X}"
    s = str(ecu_id).strip().upper().replace("0X", "")
    if not s:
        return None
    try:
        return f"{int(s, 16):03X}"
    except ValueError:
        return s


def is_standard_obd_response(ecu_id: str | int | None) -> bool:
    norm = normalize_ecu_id(ecu_id)
    if norm is None:
        return False
    try:
        value = int(norm, 16)
    except ValueError:
        return False
    return PHYSICAL_RESPONSE_MIN <= value <= PHYSICAL_RESPONSE_MAX


def is_standard_obd_request(ecu_id: str | int | None) -> bool:
    norm = normalize_ecu_id(ecu_id)
    if norm is None:
        return False
    try:
        value = int(norm, 16)
    except ValueError:
        return False
    return (
        value == FUNCTIONAL_REQUEST_11BIT
        or PHYSICAL_REQUEST_MIN <= value <= PHYSICAL_REQUEST_MAX
    )


def slot_for_response(ecu_id: str | int | None) -> ObdEcuSlot | None:
    norm = normalize_ecu_id(ecu_id)
    if norm is None:
        return None
    try:
        value = int(norm, 16)
    except ValueError:
        return None
    if not (PHYSICAL_RESPONSE_MIN <= value <= PHYSICAL_RESPONSE_MAX):
        return None
    return STANDARD_OBD_SLOTS[value - PHYSICAL_RESPONSE_MIN]


def standard_address_catalog() -> dict[str, Any]:
    return {
        "source": "ISO 15765-4",
        "functional_request_hex": f"{FUNCTIONAL_REQUEST_11BIT:03X}",
        "slots": [
            {
                "slot_index": s.slot_index,
                "request_hex": s.request_hex,
                "response_hex": s.response_hex,
                "role_hint_de": s.role_hint_de,
                "verified_source": s.verified_source,
            }
            for s in STANDARD_OBD_SLOTS
        ],
        "oem_note_de": (
            "ABS, Airbag, Komfort und andere Nicht-OBD-Steuergeräte erfordern "
            "verifizierte Fahrzeugdefinitionen (Phase 06+) – hier nicht enthalten, "
            "kein Blindscan."
        ),
        "blind_scan_allowed": False,
    }
