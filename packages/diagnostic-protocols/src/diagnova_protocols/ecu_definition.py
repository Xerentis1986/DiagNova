"""Fahrzeug-/ECU-Definitionen – nur verifizierte Einträge.

Kein Blindscan. OEM-Steuergeräte (ABS, Airbag, Komfort) ohne belegte Adresse
erscheinen als unavailable / blocked, nicht als erfundene Adressen.
"""

from __future__ import annotations

from typing import Any, Literal

from .obd_addresses import STANDARD_OBD_SLOTS, standard_address_catalog

EcuAvailability = Literal["discoverable_obd", "unavailable_no_definition", "planned"]


# Kategorien laut Master-Prompt 05 – Abdeckung ehrlich
ECU_CATEGORIES: list[dict[str, Any]] = [
    {
        "id": "engine",
        "label_de": "Motor / ECM",
        "availability": "discoverable_obd",
        "obd_slot_index": 0,
        "source": "ISO 15765-4 Slot 0 (0x7E0/0x7E8)",
        "read_first": ["identification", "dtc", "live_pids"],
    },
    {
        "id": "transmission",
        "label_de": "Getriebe / TCM",
        "availability": "discoverable_obd",
        "obd_slot_index": 1,
        "source": "ISO 15765-4 Slot 1 (0x7E1/0x7E9) – nur wenn ECU antwortet",
        "read_first": ["identification", "dtc"],
        "notes_de": "Nur sichtbar, wenn OBD-Antwort auf 0x7E9 vorliegt – nicht erzwungen.",
    },
    {
        "id": "abs",
        "label_de": "ABS / ESP",
        "availability": "unavailable_no_definition",
        "source": None,
        "blocker": "BLK-OEM",
        "notes_de": "Keine verifizierte Adresse im Repo – kein Blindscan.",
    },
    {
        "id": "airbag",
        "label_de": "Airbag / SRS",
        "availability": "unavailable_no_definition",
        "source": None,
        "blocker": "BLK-OEM",
        "notes_de": "Keine verifizierte Adresse im Repo – kein Blindscan.",
    },
    {
        "id": "comfort",
        "label_de": "Komfort / Karosserie",
        "availability": "unavailable_no_definition",
        "source": None,
        "blocker": "BLK-OEM",
        "notes_de": "OEM-spezifisch; Phase 06 Datenimport mit Lizenz.",
    },
    {
        "id": "other_obd",
        "label_de": "Weitere OBD-Slots (2–7)",
        "availability": "discoverable_obd",
        "obd_slot_index": None,
        "source": "ISO 15765-4 0x7E2–0x7E7 / 0x7EA–0x7EF",
        "notes_de": "Nur bei tatsächlicher Antwort; keine Annahmen über Funktion.",
    },
]


def vehicle_definition_template() -> dict[str, Any]:
    """Leeres Schema für Phase 06 – bewusst ohne erfundene OEM-Daten."""
    return {
        "schema_version": 1,
        "vehicle_id": None,
        "brand": None,
        "model": None,
        "year": None,
        "protocol_profile": None,
        "ecus": [],
        "import_policy_de": (
            "Nur lizenziert/verifiziert importieren. Öffentlich sichtbar ≠ frei verwendbar. "
            "Keine Bosch/Gutmann/Delphi-Kopien."
        ),
        "blind_scan_allowed": False,
    }


def ecu_overview_static() -> dict[str, Any]:
    slots = [
        {
            "slot_index": s.slot_index,
            "request_hex": s.request_hex,
            "response_hex": s.response_hex,
            "role_hint_de": s.role_hint_de,
        }
        for s in STANDARD_OBD_SLOTS
    ]
    return {
        "data_source": "simulated",
        "blind_scan_allowed": False,
        "disclaimer_de": (
            "Steuergeräteübersicht nur mit ISO-15765-4-OBD-Adressen bzw. späteren "
            "verifizierten Definitionen. ABS/Airbag/Komfort ohne Definition = nicht verfügbar."
        ),
        "categories": ECU_CATEGORIES,
        "standard_obd_slots": slots,
        "address_catalog": standard_address_catalog(),
        "vehicle_definition_template": vehicle_definition_template(),
        "read_policy_de": "Lesende Identifikation, DTCs und Messwerte zuerst. Schreiben gesperrt.",
    }
