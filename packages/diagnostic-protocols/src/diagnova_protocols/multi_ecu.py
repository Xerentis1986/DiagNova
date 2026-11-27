"""Mehrsteuergerätediagnose auf Basis beobachteter OBD-Antworten.

Discovery = Auswertung vorhandener Antworten (z. B. Multi-ECU auf 0100),
kein Blindscan unbekannter Bus-IDs.
"""

from __future__ import annotations

from typing import Any, Iterable

from .elm_response import EcuFrame, group_frames_by_ecu
from .obd_addresses import is_standard_obd_response, normalize_ecu_id, slot_for_response


def discover_ecus_from_frames(frames: Iterable[EcuFrame]) -> list[dict[str, Any]]:
    """Extrahiert antwortende Standard-OBD-ECUs aus bereits empfangenen Frames."""
    by_ecu = group_frames_by_ecu(list(frames))
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    for ecu_key, ecu_frames in by_ecu.items():
        norm = normalize_ecu_id(ecu_key if ecu_key != "unknown" else None)
        if norm is None or not is_standard_obd_response(norm):
            # Unbekannte / Nicht-Standard-IDs nicht als „entdeckt“ ausgeben
            continue
        if norm in seen:
            continue
        seen.add(norm)
        slot = slot_for_response(norm)
        found.append(
            {
                "ecu_id": norm,
                "response_hex": norm,
                "request_hex": slot.request_hex if slot else None,
                "slot_index": slot.slot_index if slot else None,
                "role_hint_de": slot.role_hint_de if slot else "OBD-ECU",
                "verified_source": "ISO 15765-4",
                "discovery_method": "observed_response",
                "frame_count": len(ecu_frames),
                "identification": None,
                "status": "responding",
                "data_source_hint": "from_bus_or_simulator",
            }
        )

    found.sort(key=lambda e: e.get("slot_index") if e.get("slot_index") is not None else 99)
    return found


def build_ecu_inventory(
    frames: Iterable[EcuFrame],
    *,
    data_source: str = "simulated",
    protocol_name: str | None = None,
) -> dict[str, Any]:
    discovered = discover_ecus_from_frames(frames)
    return {
        "data_source": data_source,
        "protocol_name": protocol_name,
        "blind_scan_used": False,
        "blind_scan_allowed": False,
        "discovered_obd_ecus": discovered,
        "count": len(discovered),
        "unavailable_categories": [
            {
                "id": "abs",
                "label_de": "ABS / ESP",
                "reason_de": "Keine verifizierte Adresse – nicht gescannt.",
            },
            {
                "id": "airbag",
                "label_de": "Airbag / SRS",
                "reason_de": "Keine verifizierte Adresse – nicht gescannt.",
            },
            {
                "id": "comfort",
                "label_de": "Komfort",
                "reason_de": "Keine verifizierte Adresse – nicht gescannt.",
            },
        ],
        "message_de": (
            f"{len(discovered)} OBD-Steuergerät(e) aus beobachteten Antworten. "
            "Kein Netzwerk-Blindscan."
        ),
    }
