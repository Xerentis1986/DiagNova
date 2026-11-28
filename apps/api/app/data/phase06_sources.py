"""Dokumentierte freie/strukturelle Quellen – Prüfdatum 2026-11-27. Nichts erfinden."""

from __future__ import annotations

from typing import Any

# commercial_use: allowed | restricted | prohibited | unknown | not_applicable
DOCUMENTED_SOURCES: list[dict[str, Any]] = [
    {
        "key": "diagnova-structural",
        "name": "DiagNova struktureller Katalog (Phase 02/06)",
        "url": None,
        "version": "phase-06-v1",
        "license_name": "DiagNova project data (internal structural)",
        "commercial_use": "not_applicable",
        "attribution": "DiagNova – Marken-/Modellstruktur ohne OEM-Diagnosedaten",
        "scope": "structural",
        "notes_de": (
            "Nur strukturelle Hersteller-/Modell-Slugs und ISO-15765-4-Adressen. "
            "Keine Bosch/Gutmann/Delphi-Inhalte."
        ),
        "checked_at": "2026-11-27",
        "redistributable": True,
    },
    {
        "key": "sae-j1979-pid-subset",
        "name": "SAE J1979 Mode-01 PID-Teilmenge (bereits im Repo)",
        "url": "https://www.sae.org/standards/content/j1979/",
        "version": "subset-mvp",
        "license_name": "SAE Standard (Kauf/Lizenz; Volltext nicht redistribuierbar)",
        "commercial_use": "restricted",
        "attribution": "PID-Namen/Einheiten als DiagNova-Implementierungs-Subset; kein SAE-Volltext",
        "scope": "generic",
        "notes_de": (
            "Die Norm selbst ist kommerziell. Im Repo liegen nur die bereits "
            "implementierten Skalierungsformeln (packages/diagnostic-protocols). "
            "Kein Abschreiben der SAE-Publikation."
        ),
        "checked_at": "2026-11-27",
        "redistributable": True,  # nur unser schmales Implementierungs-Subset
    },
    {
        "key": "iso-15765-4-obd-addresses",
        "name": "ISO 15765-4 OBD-Standardadressen (öffentlich referenziert)",
        "url": "https://www.iso.org/standard/66322.html",
        "version": "11-bit functional 7DF / 7E8-7EF",
        "license_name": "ISO Standard (Volltext lizenziert; Adressen weithin dokumentiert)",
        "commercial_use": "restricted",
        "attribution": "Nur Standard-Request/Response-Adressen 7E0/7E8, 7E1/7E9 – keine OEM-Maps",
        "scope": "generic",
        "notes_de": "Verifiziert in Phase 05. OEM ABS/Airbag/Komfort fehlen (BLK-OEM).",
        "checked_at": "2026-11-27",
        "redistributable": True,
    },
    {
        "key": "dtc-descriptions-unavailable",
        "name": "DTC-Volltextbeschreibungen – keine freie Redistribution",
        "url": None,
        "version": None,
        "license_name": "none – not redistributed",
        "commercial_use": "prohibited",
        "attribution": None,
        "scope": "documentation_only",
        "notes_de": (
            "Recherche 2026-11-27: Vollständige DTC-Textkataloge (SAE J2012, OEM, "
            "Bosch/Gutmann/Delphi) sind nicht frei kommerziell redistribuierbar. "
            "DiagNova speichert Codes ohne erfundene Beschreibung; UI zeigt „unbekannt“."
        ),
        "checked_at": "2026-11-27",
        "redistributable": False,
    },
    {
        "key": "odx-pdx-placeholder",
        "name": "ODX/PDX – Platzhalter bis Lizenz",
        "url": None,
        "version": None,
        "license_name": "pending license",
        "commercial_use": "prohibited",
        "attribution": None,
        "scope": "documentation_only",
        "notes_de": "Importpfad bewusst abgelehnt (REQ-06-ODX). Keine Spezifikation/Rechte im Projekt.",
        "checked_at": "2026-11-27",
        "redistributable": False,
    },
]

# Baseline-PIDs: nur das, was bereits in diagnova_protocols.pids liegt – Herkunft dokumentiert
BASELINE_PIDS: list[dict[str, Any]] = [
    {"pid_hex": "04", "name": "engine_load", "description_de": "Berechnete Motorlast", "unit": "%", "bytes_needed": 1, "conversion_formula": "A*100/255"},
    {"pid_hex": "05", "name": "coolant_temp", "description_de": "Kühlmitteltemperatur", "unit": "°C", "bytes_needed": 1, "conversion_formula": "A-40"},
    {"pid_hex": "0C", "name": "rpm", "description_de": "Motordrehzahl", "unit": "1/min", "bytes_needed": 2, "conversion_formula": "((A*256)+B)/4"},
    {"pid_hex": "0D", "name": "speed", "description_de": "Fahrzeuggeschwindigkeit", "unit": "km/h", "bytes_needed": 1, "conversion_formula": "A"},
    {"pid_hex": "0F", "name": "intake_temp", "description_de": "Ansauglufttemperatur", "unit": "°C", "bytes_needed": 1, "conversion_formula": "A-40"},
    {"pid_hex": "10", "name": "maf", "description_de": "Luftmassenstrom", "unit": "g/s", "bytes_needed": 2, "conversion_formula": "((A*256)+B)/100"},
    {"pid_hex": "11", "name": "throttle", "description_de": "Drosselklappenstellung", "unit": "%", "bytes_needed": 1, "conversion_formula": "A*100/255"},
    {"pid_hex": "2F", "name": "fuel_level", "description_de": "Kraftstofffüllstand", "unit": "%", "bytes_needed": 1, "conversion_formula": "A*100/255"},
    {"pid_hex": "42", "name": "control_module_voltage", "description_de": "Steuergerätespannung", "unit": "V", "bytes_needed": 2, "conversion_formula": "((A*256)+B)/1000"},
]

BASELINE_ECUS: list[dict[str, Any]] = [
    {
        "code": "obd_ecu_0",
        "name_de": "OBD Powertrain ECU #1",
        "category": "powertrain",
        "protocol_id": "iso_15765_4",
        "request_address": "7E0",
        "response_address": "7E8",
        "verified": True,
        "notes_de": "ISO 15765-4 Standardadresse – Phase 05 verifiziert.",
    },
    {
        "code": "obd_ecu_1",
        "name_de": "OBD Powertrain ECU #2",
        "category": "powertrain",
        "protocol_id": "iso_15765_4",
        "request_address": "7E1",
        "response_address": "7E9",
        "verified": True,
        "notes_de": "ISO 15765-4 Standardadresse – Phase 05 verifiziert.",
    },
]

BASELINE_UNITS: list[dict[str, Any]] = [
    {"code": "percent", "label_de": "Prozent", "symbol": "%"},
    {"code": "celsius", "label_de": "Grad Celsius", "symbol": "°C"},
    {"code": "rpm", "label_de": "Umdrehungen pro Minute", "symbol": "1/min"},
    {"code": "kmh", "label_de": "Kilometer pro Stunde", "symbol": "km/h"},
    {"code": "gps", "label_de": "Gramm pro Sekunde", "symbol": "g/s"},
    {"code": "volt", "label_de": "Volt", "symbol": "V"},
]

# DTC-Codes ohne Beschreibung (keine erfundenen Texte) – nur Format/System
BASELINE_DTC_CODES_UNKNOWN: list[str] = [
    "P0301",
    "P0171",
    "P0420",
    "P0128",
    "U0100",
    "C0035",
]

# Nachgetragen Phase Automotive-Katalog (2026-11-28)
DOCUMENTED_SOURCES.append(
    {
        "key": "obdex-cc0",
        "name": "OBDex generic DTC JSON (CC0-1.0)",
        "url": "https://foerbsnavi.github.io/OBDex/generic.min.json",
        "version": "generic.min",
        "license_name": "CC0-1.0",
        "commercial_use": "allowed",
        "attribution": "OBDex / foerbsnavi – Public Domain (CC0)",
        "scope": "generic",
        "notes_de": (
            "Vollbestand ~9533 DTCs. Im Repo: Sample-200 Fixture. "
            "Vollimport nur lokal via scripts/automotive_catalog_probe_and_import.py --full-obdex."
        ),
        "checked_at": "2026-11-28",
        "redistributable": True,
    }
)
DOCUMENTED_SOURCES.append(
    {
        "key": "obdb-cc-by-sa",
        "name": "OBDb Signalsets (CC BY-SA 4.0)",
        "url": "https://github.com/OBDb",
        "version": "signalsets/v3",
        "license_name": "CC BY-SA 4.0",
        "commercial_use": "restricted",
        "attribution": "OBDb – Attribution + ShareAlike; Contact notice vor Produktlaunch",
        "scope": "oem",
        "notes_de": (
            "Prius/Focus Signalsets erreichbar. v1: nur Metadaten-Fixture; "
            "kein Bulk-Redistrib ohne Attribution-Pipeline."
        ),
        "checked_at": "2026-11-28",
        "redistributable": False,
    }
)
