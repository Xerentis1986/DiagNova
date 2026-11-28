"""Phase 19 – LKW/Nutzfahrzeug-Markenkatalog (Architektur only).

Katalogeinträge sind Navigationshilfen – KEINE Diagnoseabdeckung.
Keine J1939-Parser, keine SPN/FMI-Auswertung, keine RP1210-Bindung.
Alle Capabilities: planned / unavailable. Schreib-/OEM-Service: deaktiviert.
"""

from __future__ import annotations

from typing import Any

# Lesende Architektur-Flags – bewusst nicht freigegeben
LKW_CAPABILITY_FLAGS: list[dict[str, Any]] = [
    {
        "id": "j1939_read_dtc_spn_fmi",
        "label_de": "J1939 DTCs lesen (SPN/FMI)",
        "status": "planned",
        "enabled": False,
        "phase": 19,
        "blocker": "BLK-HW",
        "notes_de": "Benötigt rechtmäßig nutzbare Spec + 24-V/RP1210-Hardware.",
    },
    {
        "id": "j1939_live_pg_spn",
        "label_de": "J1939 Live-Messwerte (PG/SPN)",
        "status": "planned",
        "enabled": False,
        "phase": 19,
        "blocker": "BLK-HW",
        "notes_de": "Kein Simulator mit vorgetäuschten LKW-Werten.",
    },
    {
        "id": "j1939_transport_bam_rts",
        "label_de": "J1939 Transport (BAM/RTS-CTS)",
        "status": "planned",
        "enabled": False,
        "phase": 19,
        "blocker": "BLK-HW",
    },
    {
        "id": "rp1210_adapter",
        "label_de": "RP1210 Adapter-API",
        "status": "planned",
        "enabled": False,
        "phase": 19,
        "blocker": "BLK-HW",
        "notes_de": "PKW-ELM/OBD-Adapter ist kein RP1210-Interface.",
    },
    {
        "id": "j1708_j1587",
        "label_de": "J1708/J1587 (ältere US-Nutzfahrzeuge)",
        "status": "planned",
        "enabled": False,
        "phase": 19,
        "blocker": "BLK-HW",
    },
    {
        "id": "truck_uds_doip",
        "label_de": "UDS/DoIP am Nutzfahrzeug (wo belegt)",
        "status": "planned",
        "enabled": False,
        "phase": 19,
        "blocker": "BLK-HW",
    },
    {
        "id": "lkw_simulator",
        "label_de": "LKW-Simulator",
        "status": "planned",
        "enabled": False,
        "phase": 19,
        "blocker": "BLK-HW",
        "notes_de": "Erst nach Spezifikationsbeleg – keine Fake-Diagnose.",
    },
    {
        "id": "lkw_history_pdf",
        "label_de": "LKW-Historie / PDF-Berichte",
        "status": "planned",
        "enabled": False,
        "phase": 19,
    },
    {
        "id": "lkw_tariff",
        "label_de": "Eigene LKW-Tarife",
        "status": "planned",
        "enabled": False,
        "phase": 19,
        "notes_de": "Tarifcodes lkw_planned / kombi_planned existieren, nicht buchbar.",
    },
    {
        "id": "oem_truck_service_write",
        "label_de": "Hersteller-Service / Schreibfunktionen",
        "status": "unavailable",
        "enabled": False,
        "phase": 19,
        "blocker": "BLK-OEM",
        "notes_de": "Bis Daten, Hardware und Freigabe deaktiviert.",
    },
]


def _truck_brand(
    slug: str,
    name: str,
    group: str,
    sort: int,
    *,
    example_models: list[str] | None = None,
) -> dict[str, Any]:
    initials = "".join(p[0] for p in name.replace("-", " ").split() if p)[:3].upper()
    return {
        "slug": slug,
        "name": name,
        "vehicle_class": "commercial",
        "group": group,
        "sort_order": sort,
        "logo_mode": "text_fallback",
        "logo_initials": initials,
        "logo_rights_cleared": False,
        "release_status": "planned",
        "diagnosis_available": False,
        "protocols_planned": ["sae_j1939", "rp1210"],
        "voltage_note_de": "Typisch 24 V – PKW-12-V-Adapter nicht unterstellen.",
        "coverage_disclaimer_de": (
            "Katalogeintrag bedeutet keine Diagnoseabdeckung. "
            "LKW-Diagnose ist Architektur-Vorbereitung (Phase 19) – nicht freigegeben."
        ),
        "example_models_nav_only": example_models or [],
        "example_models_note_de": (
            "Beispiele nur zur Navigation – keine ECU-Adressen, keine SPN-Tabellen."
        ),
    }


# Belegte Markennamen laut Master-Prompt 19 – keine erfundenen Diagnose-IDs
LKW_BRANDS: list[dict[str, Any]] = [
    _truck_brand(
        "man-trucks",
        "MAN",
        "Traton",
        10,
        example_models=["TGX", "TGS"],
    ),
    _truck_brand(
        "mercedes-benz-trucks",
        "Mercedes-Benz Trucks",
        "Daimler Truck",
        20,
        example_models=["Actros", "Atego"],
    ),
    _truck_brand(
        "scania",
        "Scania",
        "Traton",
        30,
        example_models=["R-Series", "S-Series"],
    ),
    _truck_brand(
        "volvo-trucks",
        "Volvo Trucks",
        "Volvo Group",
        40,
        example_models=["FH", "FM"],
    ),
    _truck_brand(
        "daf",
        "DAF",
        "PACCAR",
        50,
        example_models=["XF", "XD"],
    ),
    _truck_brand(
        "iveco",
        "Iveco",
        "Iveco Group",
        60,
        example_models=["S-Way", "Eurocargo"],
    ),
    _truck_brand(
        "renault-trucks",
        "Renault Trucks",
        "Volvo Group",
        70,
        example_models=["T", "C"],
    ),
]


ARCHITECTURE: dict[str, Any] = {
    "phase": 19,
    "scope": "architecture_only",
    "status": "documented_prep",
    "title_de": "LKW / Nutzfahrzeug – Architekturvorbereitung",
    "summary_de": (
        "Fahrzeugmodell, Capability-Flags und J1939/RP1210-Schnittstellenvorbereitung. "
        "Keine laufende LKW-Diagnose, kein Parser, kein Simulator mit Fake-Werten."
    ),
    "layers": [
        {
            "id": "transport",
            "planned": ["rp1210", "j2534_where_applicable", "doip_where_applicable"],
            "notes_de": "24-V-taugliche Hardware und passende Steckverbinder erforderlich.",
        },
        {
            "id": "protocol",
            "planned": ["sae_j1939", "j1708_j1587", "iso_14229_uds_where_documented"],
            "notes_de": "SPN/FMI, Quellenadresse, Transport erst mit Spec-Beleg.",
        },
        {
            "id": "adapter",
            "planned": ["rp1210"],
            "not_assumed": ["elm327-obd", "pkw_12v_dongle"],
            "notes_de": "Keine PKW-Adapterkompatibilität unterstellen.",
        },
        {
            "id": "vehicle_definition",
            "planned_brands": [b["slug"] for b in LKW_BRANDS],
            "notes_de": "Nur Markennamen/Navigation – keine OEM-ECU-Definitionen.",
        },
    ],
    "explicitly_disabled": [
        "j1939_live_read",
        "j1939_dtc_clear",
        "rp1210_dll_bind",
        "oem_truck_service_write",
        "fake_truck_simulator_values",
    ],
    "blockers": ["BLK-HW", "BLK-OEM", "BLK-ADAPTER"],
    "docs": [
        "docs/lkw-j1939-architecture.md",
        "docs/j2534-doip-j1939-prep.md",
        "docs/adapter-capability-matrix.md",
    ],
}


def list_lkw_brands(q: str | None = None) -> list[dict[str, Any]]:
    items = list(LKW_BRANDS)
    if q:
        ql = q.casefold()
        items = [b for b in items if ql in b["name"].casefold() or ql in b["slug"]]
    return items


def get_lkw_brand(slug: str) -> dict[str, Any] | None:
    for b in LKW_BRANDS:
        if b["slug"] == slug:
            return b
    return None


def lkw_capabilities() -> dict[str, Any]:
    return {
        "disclaimer_de": (
            "Alle LKW-Capabilities sind geplant oder unavailable. "
            "Keine Diagnose freigegeben. PKW-OBD ersetzt J1939/RP1210 nicht."
        ),
        "release_status": "planned",
        "diagnosis_enabled": False,
        "flags": LKW_CAPABILITY_FLAGS,
        "available": [],
        "unavailable": LKW_CAPABILITY_FLAGS,
    }


def lkw_architecture() -> dict[str, Any]:
    return {
        **ARCHITECTURE,
        "brand_count": len(LKW_BRANDS),
        "capability_flag_count": len(LKW_CAPABILITY_FLAGS),
        "entitlement_key": "vehicle.lkw",
        "entitlement_granted": False,
        "tariff_codes_planned": ["lkw_planned", "kombi_planned"],
    }
