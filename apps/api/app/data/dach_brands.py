"""DACH-Markenkatalog (Phase 02).

Katalogeinträge sind Navigations-/Auswahlhilfen – KEINE Diagnoseabdeckung.
Keine Markenlogos: Text-Fallback (Initialen), da Nutzungsrechte ungeklärt (BLK-LOGO).
Modell-/Variantenlisten sind Beispieldaten für den Auswahlfluss, keine OEM-Datenbank.
"""

from __future__ import annotations

from typing import Any

# Verfügbare Funktionen – ehrlich getrennt (MVP simuliert vs. geplant)
MVP_SIMULATED_CAPABILITIES = [
    {
        "id": "obd_read_dtc",
        "label_de": "OBD-II Fehlercodes lesen (simuliert)",
        "status": "simulated",
        "phase": 1,
    },
    {
        "id": "obd_live_pids",
        "label_de": "Live-PIDs / Messwerte (simuliert)",
        "status": "simulated",
        "phase": 1,
    },
    {
        "id": "obd_freeze_frame",
        "label_de": "Freeze-Frame (simuliert)",
        "status": "simulated",
        "phase": 1,
    },
    {
        "id": "obd_readiness",
        "label_de": "Readiness-Monitore (simuliert)",
        "status": "simulated",
        "phase": 1,
    },
    {
        "id": "session_report",
        "label_de": "Diagnosesitzung & Bericht CSV/PDF (simuliert)",
        "status": "simulated",
        "phase": 1,
    },
    {
        "id": "obd_clear_dtc_gated",
        "label_de": "Fehlerlöschung freigabegeschützt (simuliert; permanente DTCs bleiben)",
        "status": "simulated",
        "phase": 4,
    },
    {
        "id": "obd_connector_parser",
        "label_de": "Connector OBD-Parser/Allowlist (simuliert getestet, keine HW-Freigabe)",
        "status": "simulated",
        "phase": 4,
    },
    {
        "id": "multi_ecu_obd",
        "label_de": "Mehr-ECU OBD (ISO 15765-4 Standardadressen, simuliert)",
        "status": "simulated",
        "phase": 5,
    },
    {
        "id": "protocol_catalog",
        "label_de": "Protokollkatalog + Adapter-Capability-Matrix",
        "status": "simulated",
        "phase": 5,
    },
    {
        "id": "diagnostic_data_import",
        "label_de": "Diagnosedaten JSON/CSV-Import (Validierung, Quarantäne, Rollback)",
        "status": "simulated",
        "phase": 6,
    },
    {
        "id": "dtc_lookup_provenance",
        "label_de": "DTC-Lookup mit Herkunft; unbekannte Codes → „unbekannt“",
        "status": "simulated",
        "phase": 6,
    },
    {
        "id": "diagnostic_data_auto_updates",
        "label_de": "Automatische Diagnosedaten-Updates (Scheduler, Staging, Freigabe, Rollback)",
        "status": "simulated",
        "phase": 7,
    },
]

PLANNED_CAPABILITIES = [
    {
        "id": "oem_ecu_abs_airbag_comfort",
        "label_de": "OEM-Steuergeräte ABS/Airbag/Komfort (verifizierte Definitionen)",
        "status": "planned",
        "phase": 6,
    },
    {
        "id": "odx_pdx_licensed_import",
        "label_de": "ODX/PDX-Import (nur mit Lizenz/Spezifikation)",
        "status": "unavailable",
        "phase": 6,
    },
    {
        "id": "doip_can_fd_j2534_live",
        "label_de": "DoIP / CAN-FD / J2534 Live-Hardware",
        "status": "unavailable",
        "phase": 5,
    },
    {
        "id": "service_functions",
        "label_de": "Servicefunktionen (Öl, EPB, …)",
        "status": "planned",
        "phase": 11,
    },
    {
        "id": "coding",
        "label_de": "Codierung / Programmierung",
        "status": "planned",
        "phase": 12,
    },
]


def _variant(
    id_: str,
    series: str,
    year_from: int,
    year_to: int,
    engine: str,
    fuel_type: str,
) -> dict[str, Any]:
    return {
        "id": id_,
        "series": series,
        "year_from": year_from,
        "year_to": year_to,
        "engine": engine,
        "fuel_type": fuel_type,
    }


def _model(id_: str, name: str, variants: list[dict[str, Any]]) -> dict[str, Any]:
    return {"id": id_, "name": name, "variants": variants}


def _brand(
    slug: str,
    name: str,
    group: str,
    sort: int,
    models: list[dict[str, Any]],
) -> dict[str, Any]:
    initials = "".join(p[0] for p in name.replace("-", " ").split() if p)[:3].upper()
    if name == "Škoda":
        initials = "SK"
    elif name == "CUPRA":
        initials = "CU"
    elif name == "MINI":
        initials = "MI"
    elif name == "DS":
        initials = "DS"
    elif name == "MG":
        initials = "MG"
    elif name == "BYD":
        initials = "BYD"
    return {
        "slug": slug,
        "name": name,
        "group": group,
        "sort_order": sort,
        "logo_mode": "text_fallback",
        "logo_initials": initials,
        "logo_rights_cleared": False,
        "coverage_disclaimer_de": (
            "Katalogeintrag bedeutet keine Diagnoseabdeckung. "
            "Verfügbare Funktionen werden gesondert angezeigt."
        ),
        "models": models,
    }


# Reihenfolge laut Master-Prompt 02 (+ sinnvolle Gruppen für UI)
DACH_BRANDS: list[dict[str, Any]] = [
    _brand(
        "vw",
        "VW",
        "VAG",
        10,
        [
            _model(
                "vw-golf",
                "Golf",
                [
                    _variant("vw-golf-7-14tsi", "VII", 2013, 2020, "1.4 TSI", "Benzin"),
                    _variant("vw-golf-8-15etsi", "VIII", 2020, 2026, "1.5 eTSI", "Mild-Hybrid"),
                ],
            ),
            _model(
                "vw-passat",
                "Passat",
                [_variant("vw-passat-b8-20tdi", "B8", 2015, 2023, "2.0 TDI", "Diesel")],
            ),
        ],
    ),
    _brand(
        "audi",
        "Audi",
        "VAG",
        20,
        [
            _model(
                "audi-a4",
                "A4",
                [_variant("audi-a4-b9-20tdi", "B9", 2016, 2023, "2.0 TDI", "Diesel")],
            ),
            _model(
                "audi-a3",
                "A3",
                [_variant("audi-a3-8y-35tfsi", "8Y", 2020, 2026, "35 TFSI", "Benzin")],
            ),
        ],
    ),
    _brand(
        "skoda",
        "Škoda",
        "VAG",
        30,
        [
            _model(
                "skoda-octavia",
                "Octavia",
                [_variant("skoda-octavia-3-16tdi", "III", 2013, 2020, "1.6 TDI", "Diesel")],
            ),
        ],
    ),
    _brand(
        "seat",
        "SEAT",
        "VAG",
        40,
        [
            _model(
                "seat-leon",
                "Leon",
                [_variant("seat-leon-3-15tsi", "III", 2017, 2020, "1.5 TSI", "Benzin")],
            ),
        ],
    ),
    _brand(
        "cupra",
        "CUPRA",
        "VAG",
        50,
        [
            _model(
                "cupra-formentor",
                "Formentor",
                [_variant("cupra-formentor-15tsi", "KM7", 2020, 2026, "1.5 TSI", "Benzin")],
            ),
        ],
    ),
    _brand(
        "bmw",
        "BMW",
        "BMW Group",
        60,
        [
            _model(
                "bmw-3er",
                "3er",
                [_variant("bmw-320d-g20", "G20", 2019, 2026, "320d", "Diesel")],
            ),
        ],
    ),
    _brand(
        "mini",
        "MINI",
        "BMW Group",
        70,
        [
            _model(
                "mini-cooper",
                "Cooper",
                [_variant("mini-cooper-f56", "F56", 2014, 2024, "1.5", "Benzin")],
            ),
        ],
    ),
    _brand(
        "mercedes-benz",
        "Mercedes-Benz",
        "Mercedes-Benz Group",
        80,
        [
            _model(
                "mb-c-klasse",
                "C-Klasse",
                [_variant("mb-c200-w205", "W205", 2014, 2021, "C 200", "Benzin")],
            ),
        ],
    ),
    _brand(
        "smart",
        "Smart",
        "Mercedes-Benz Group",
        90,
        [
            _model(
                "smart-fortwo",
                "fortwo",
                [_variant("smart-fortwo-453", "453", 2014, 2024, "Electric", "Elektro")],
            ),
        ],
    ),
    _brand(
        "opel",
        "Opel",
        "Stellantis",
        100,
        [
            _model(
                "opel-astra",
                "Astra",
                [_variant("opel-astra-k-14t", "K", 2015, 2021, "1.4 Turbo", "Benzin")],
            ),
        ],
    ),
    _brand(
        "ford",
        "Ford",
        "Ford",
        110,
        [
            _model(
                "ford-focus",
                "Focus",
                [_variant("ford-focus-mk4-10eb", "Mk4", 2018, 2026, "1.0 EcoBoost", "Benzin")],
            ),
        ],
    ),
    _brand(
        "renault",
        "Renault",
        "Renault",
        120,
        [
            _model(
                "renault-clio",
                "Clio",
                [_variant("renault-clio-5-tce", "V", 2019, 2026, "1.0 TCe", "Benzin")],
            ),
        ],
    ),
    _brand(
        "dacia",
        "Dacia",
        "Renault",
        130,
        [
            _model(
                "dacia-duster",
                "Duster",
                [_variant("dacia-duster-2-tce", "II", 2018, 2026, "1.3 TCe", "Benzin")],
            ),
        ],
    ),
    _brand(
        "peugeot",
        "Peugeot",
        "Stellantis",
        140,
        [
            _model(
                "peugeot-308",
                "308",
                [_variant("peugeot-308-p5-puretech", "P5", 2021, 2026, "1.2 PureTech", "Benzin")],
            ),
        ],
    ),
    _brand(
        "citroen",
        "Citroën",
        "Stellantis",
        150,
        [
            _model(
                "citroen-c3",
                "C3",
                [_variant("citroen-c3-3-puretech", "III", 2016, 2024, "1.2 PureTech", "Benzin")],
            ),
        ],
    ),
    _brand(
        "ds",
        "DS",
        "Stellantis",
        160,
        [
            _model(
                "ds-ds3",
                "DS 3",
                [_variant("ds-ds3-crossback", "Crossback", 2019, 2026, "1.2 PureTech", "Benzin")],
            ),
        ],
    ),
    _brand(
        "fiat",
        "Fiat",
        "Stellantis",
        170,
        [
            _model(
                "fiat-500",
                "500",
                [_variant("fiat-500-312", "312", 2015, 2024, "1.2", "Benzin")],
            ),
        ],
    ),
    _brand(
        "alfa-romeo",
        "Alfa Romeo",
        "Stellantis",
        180,
        [
            _model(
                "alfa-giulia",
                "Giulia",
                [_variant("alfa-giulia-952-20", "952", 2016, 2026, "2.0 Turbo", "Benzin")],
            ),
        ],
    ),
    _brand(
        "jeep",
        "Jeep",
        "Stellantis",
        190,
        [
            _model(
                "jeep-renegade",
                "Renegade",
                [_variant("jeep-renegade-bu", "BU", 2015, 2024, "1.6 Multijet", "Diesel")],
            ),
        ],
    ),
    _brand(
        "volvo",
        "Volvo",
        "Geely",
        200,
        [
            _model(
                "volvo-xc60",
                "XC60",
                [_variant("volvo-xc60-2-b4", "II", 2017, 2026, "B4", "Mild-Hybrid")],
            ),
        ],
    ),
    _brand(
        "polestar",
        "Polestar",
        "Geely",
        210,
        [
            _model(
                "polestar-2",
                "2",
                [_variant("polestar-2-lr", "LCA", 2020, 2026, "Long Range", "Elektro")],
            ),
        ],
    ),
    _brand(
        "porsche",
        "Porsche",
        "VAG",
        220,
        [
            _model(
                "porsche-macan",
                "Macan",
                [_variant("porsche-macan-95b", "95B", 2014, 2024, "2.0 Turbo", "Benzin")],
            ),
        ],
    ),
    _brand(
        "land-rover",
        "Land Rover",
        "JLR",
        230,
        [
            _model(
                "lr-discovery-sport",
                "Discovery Sport",
                [_variant("lr-disco-sport-l550", "L550", 2015, 2026, "2.0 D180", "Diesel")],
            ),
        ],
    ),
    _brand(
        "jaguar",
        "Jaguar",
        "JLR",
        240,
        [
            _model(
                "jaguar-e-pace",
                "E-Pace",
                [_variant("jaguar-e-pace-x540", "X540", 2017, 2024, "2.0 D150", "Diesel")],
            ),
        ],
    ),
    _brand(
        "toyota",
        "Toyota",
        "Toyota",
        250,
        [
            _model(
                "toyota-corolla",
                "Corolla",
                [_variant("toyota-corolla-e210-18h", "E210", 2019, 2026, "1.8 Hybrid", "Hybrid")],
            ),
        ],
    ),
    _brand(
        "lexus",
        "Lexus",
        "Toyota",
        260,
        [
            _model(
                "lexus-ux",
                "UX",
                [_variant("lexus-ux-250h", "ZA10", 2019, 2026, "250h", "Hybrid")],
            ),
        ],
    ),
    _brand(
        "honda",
        "Honda",
        "Honda",
        270,
        [
            _model(
                "honda-civic",
                "Civic",
                [_variant("honda-civic-11-ehev", "XI", 2022, 2026, "e:HEV", "Hybrid")],
            ),
        ],
    ),
    _brand(
        "nissan",
        "Nissan",
        "Renault-Nissan",
        280,
        [
            _model(
                "nissan-qashqai",
                "Qashqai",
                [_variant("nissan-qashqai-j12", "J12", 2021, 2026, "1.3 DIG-T", "Mild-Hybrid")],
            ),
        ],
    ),
    _brand(
        "mazda",
        "Mazda",
        "Mazda",
        290,
        [
            _model(
                "mazda-3",
                "3",
                [_variant("mazda-3-bp-skyactiv", "BP", 2019, 2026, "2.0 Skyactiv-G", "Benzin")],
            ),
        ],
    ),
    _brand(
        "mitsubishi",
        "Mitsubishi",
        "Mitsubishi",
        300,
        [
            _model(
                "mitsubishi-asx",
                "ASX",
                [_variant("mitsubishi-asx-ga", "GA0", 2023, 2026, "1.3 Turbo", "Mild-Hybrid")],
            ),
        ],
    ),
    _brand(
        "suzuki",
        "Suzuki",
        "Suzuki",
        310,
        [
            _model(
                "suzuki-vitara",
                "Vitara",
                [_variant("suzuki-vitara-ly", "LY", 2015, 2026, "1.4 Boosterjet", "Mild-Hybrid")],
            ),
        ],
    ),
    _brand(
        "subaru",
        "Subaru",
        "Subaru",
        320,
        [
            _model(
                "subaru-forester",
                "Forester",
                [_variant("subaru-forester-sk", "SK", 2019, 2026, "2.0 e-Boxer", "Hybrid")],
            ),
        ],
    ),
    _brand(
        "hyundai",
        "Hyundai",
        "Hyundai",
        330,
        [
            _model(
                "hyundai-i30",
                "i30",
                [_variant("hyundai-i30-pd", "PD", 2017, 2026, "1.5 T-GDI", "Benzin")],
            ),
        ],
    ),
    _brand(
        "kia",
        "Kia",
        "Hyundai",
        340,
        [
            _model(
                "kia-ceed",
                "Ceed",
                [_variant("kia-ceed-cd", "CD", 2018, 2026, "1.5 T-GDI", "Benzin")],
            ),
        ],
    ),
    _brand(
        "genesis",
        "Genesis",
        "Hyundai",
        350,
        [
            _model(
                "genesis-gv60",
                "GV60",
                [_variant("genesis-gv60-jw1", "JW1", 2021, 2026, "Electric", "Elektro")],
            ),
        ],
    ),
    _brand(
        "mg",
        "MG",
        "SAIC",
        360,
        [
            _model(
                "mg-zs",
                "ZS",
                [_variant("mg-zs-ev", "EV", 2020, 2026, "Electric", "Elektro")],
            ),
        ],
    ),
    _brand(
        "byd",
        "BYD",
        "BYD",
        370,
        [
            _model(
                "byd-atto3",
                "Atto 3",
                [_variant("byd-atto3-sc2e", "SC2E", 2022, 2026, "Electric", "Elektro")],
            ),
        ],
    ),
    _brand(
        "tesla",
        "Tesla",
        "Tesla",
        380,
        [
            _model(
                "tesla-model-3",
                "Model 3",
                [_variant("tesla-model-3-rwd", "Highland", 2023, 2026, "RWD", "Elektro")],
            ),
        ],
    ),
]


def list_brands(query: str | None = None) -> list[dict[str, Any]]:
    q = (query or "").strip().casefold()
    items = []
    for b in sorted(DACH_BRANDS, key=lambda x: x["sort_order"]):
        if q and q not in b["name"].casefold() and q not in b["slug"].casefold() and q not in b["group"].casefold():
            continue
        items.append(_brand_summary(b))
    return items


def _brand_summary(b: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": b["slug"],
        "name": b["name"],
        "group": b["group"],
        "sort_order": b["sort_order"],
        "logo_mode": b["logo_mode"],
        "logo_initials": b["logo_initials"],
        "logo_rights_cleared": b["logo_rights_cleared"],
        "coverage_disclaimer_de": b["coverage_disclaimer_de"],
        "model_count": len(b["models"]),
    }


def get_brand(slug: str) -> dict[str, Any] | None:
    for b in DACH_BRANDS:
        if b["slug"] == slug:
            return b
    return None


def get_models(slug: str) -> list[dict[str, Any]] | None:
    brand = get_brand(slug)
    if brand is None:
        return None
    return [
        {"id": m["id"], "name": m["name"], "variant_count": len(m["variants"])}
        for m in brand["models"]
    ]


def get_model(slug: str, model_id: str) -> dict[str, Any] | None:
    brand = get_brand(slug)
    if brand is None:
        return None
    for m in brand["models"]:
        if m["id"] == model_id:
            return m
    return None


def get_variant(slug: str, model_id: str, variant_id: str) -> dict[str, Any] | None:
    model = get_model(slug, model_id)
    if model is None:
        return None
    for v in model["variants"]:
        if v["id"] == variant_id:
            return v
    return None


def capabilities_for_selection() -> dict[str, Any]:
    """Katalogauswahl ≠ OEM-Abdeckung. Nur MVP-Simulator-Funktionen sind nutzbar."""
    return {
        "disclaimer_de": (
            "Ein Katalogeintrag bedeutet keine Diagnoseabdeckung. "
            "Simuliert: OBD-II, Mehr-ECU (ISO-15765-4) und Diagnosedaten-Import (JSON/CSV). "
            "Unbekannte DTCs → „unbekannt“. Kein Blindscan. ODX und OEM-Texte fehlen."
        ),
        "available": MVP_SIMULATED_CAPABILITIES,
        "unavailable": PLANNED_CAPABILITIES,
        "adapter_next_step_de": (
            "Adapter: Windows-Connector Fake/Simulator oder ELM-Pfad (nicht hardwarefreigegeben). "
            "Capability-Matrix unter /api/protocols/capability-matrix."
        ),
    }


REQUIRED_DACH_NAMES = [
    "VW",
    "Audi",
    "Škoda",
    "SEAT",
    "CUPRA",
    "BMW",
    "MINI",
    "Mercedes-Benz",
    "Smart",
    "Opel",
    "Ford",
    "Renault",
    "Dacia",
    "Peugeot",
    "Citroën",
    "DS",
    "Fiat",
    "Alfa Romeo",
    "Jeep",
    "Volvo",
    "Polestar",
    "Porsche",
    "Land Rover",
    "Jaguar",
    "Toyota",
    "Lexus",
    "Honda",
    "Nissan",
    "Mazda",
    "Mitsubishi",
    "Suzuki",
    "Subaru",
    "Hyundai",
    "Kia",
    "Genesis",
    "MG",
    "BYD",
    "Tesla",
]
