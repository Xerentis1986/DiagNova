"""Phase 12 – Katalog Codierung / Programmierung.

Nur Architektur und Gates. Keine erfundenen OEM-Flash-/Codierprotokolle.
Schreiben und Flash bleiben ohne Spezifikation und Berechtigung deaktiviert.
"""

from __future__ import annotations

from typing import Any


def _op(
    *,
    code: str,
    name_de: str,
    category: str,
    operation_type: str,
    safety_class: str = "write_critical",
    release_status: str = "disabled",
    prerequisites: list[dict[str, str]] | None = None,
    confirmation_phrase: str | None = None,
    timeout_seconds: int = 120,
    abort_strategy_de: str = "Sofort abbrechen; kein automatisches Wiederholen.",
    result_checks_de: list[str] | None = None,
    ecu_roles: list[str] | None = None,
    compatibility_de: str = "Nur mit belegter OEM-Spezifikation und Freigabe.",
    source_license_de: str = "Keine OEM-Codier-/Flashdaten im Repo.",
    notes_de: str = "",
    blockers: list[str] | None = None,
    requires_j2534: bool = False,
    requires_authorization: bool = True,
    backup_supported: bool = False,
) -> dict[str, Any]:
    return {
        "code": code,
        "name_de": name_de,
        "category": category,
        "operation_type": operation_type,  # identify | coding | flash | interface
        "safety_class": safety_class,
        "release_status": release_status,
        "enabled": False,
        "write_allowed": False,
        "flash_allowed": False,
        "prerequisites": prerequisites
        or [
            {"id": "ignition_on", "label_de": "Zündung ein"},
            {"id": "adapter_connected", "label_de": "Adapter verbunden"},
            {"id": "battery_voltage_ok", "label_de": "Bordnetzspannung ausreichend"},
            {"id": "stable_connection", "label_de": "Stabile Diagnoseverbindung"},
            {"id": "vin_ecu_match", "label_de": "VIN/ECU-Kompatibilität geprüft"},
            {"id": "oem_spec_present", "label_de": "OEM-Spezifikation vorhanden"},
            {"id": "authorization_present", "label_de": "Berechtigung / Freigabe vorhanden"},
            {"id": "recovery_plan", "label_de": "Wiederherstellungsplan bestätigt"},
            {"id": "operator_confirm", "label_de": "Fachkraft bestätigt"},
        ],
        "confirmation_phrase": confirmation_phrase,
        "timeout_seconds": timeout_seconds,
        "abort_strategy_de": abort_strategy_de,
        "result_checks_de": result_checks_de or ["Identifikation rücklesen", "Keine Teilschreibung"],
        "ecu_roles": ecu_roles or ["engine"],
        "compatibility_de": compatibility_de,
        "source_license_de": source_license_de,
        "notes_de": notes_de,
        "blockers": blockers or ["BLK-OEM", "BLK-HW", "BLK-RELEASE"],
        "requires_j2534": requires_j2534,
        "requires_authorization": requires_authorization,
        "backup_supported": backup_supported,
        "data_source": "catalog",
        "oem_procedure_invented": False,
        "auto_retry_forbidden": True,
    }


OPERATIONS: list[dict[str, Any]] = [
    _op(
        code="ECU_IDENTIFY_READ",
        name_de="ECU-Identifikation (lesend)",
        category="Identifikation",
        operation_type="identify",
        safety_class="read_only",
        release_status="sim_gates_only",
        confirmation_phrase=None,
        timeout_seconds=30,
        abort_strategy_de="Lesung abbrechen; kein Schreibzugriff.",
        result_checks_de=["Teilenummer/SW-Stand anzeigen, sofern Simulator liefert"],
        prerequisites=[
            {"id": "ignition_on", "label_de": "Zündung ein"},
            {"id": "adapter_connected", "label_de": "Adapter verbunden"},
            {"id": "stable_connection", "label_de": "Stabile Diagnoseverbindung"},
        ],
        requires_authorization=False,
        notes_de=(
            "Nur lesende Identifikation (simuliert). Keine OEM-DIDs erfinden. "
            "Softwarestand und Codierprofil nur als Platzhalter, wenn keine Spec vorliegt."
        ),
        blockers=["BLK-OEM"],
        compatibility_de="Generische OBD/UDS-Identifikation wo belegt; OEM-Felder ohne Spec leer.",
    ),
    _op(
        code="CODING_PROFILE_READ",
        name_de="Codierprofil lesen (Platzhalter)",
        category="Identifikation",
        operation_type="identify",
        safety_class="read_only",
        release_status="sim_gates_only",
        confirmation_phrase=None,
        timeout_seconds=30,
        requires_authorization=False,
        backup_supported=False,
        notes_de=(
            "Zeigt nur an, dass kein lizenziertes Codierprofil vorliegt. "
            "Kein Auslesen echter OEM-Codierungen ohne Spezifikation."
        ),
        prerequisites=[
            {"id": "adapter_connected", "label_de": "Adapter verbunden"},
            {"id": "oem_spec_present", "label_de": "OEM-Spezifikation vorhanden"},
        ],
        blockers=["BLK-OEM"],
    ),
    _op(
        code="CODING_WRITE_GENERIC",
        name_de="Steuergerätecodierung schreiben",
        category="Codierung",
        operation_type="coding",
        confirmation_phrase="CODIERUNG SCHREIBEN BESTAETIGEN",
        timeout_seconds=180,
        backup_supported=True,
        notes_de=(
            "Ohne OEM-Spezifikation und Berechtigung DEAKTIVIERT. "
            "Originalcodierung nur sichern, wenn offiziell unterstützt – hier nicht belegt."
        ),
        abort_strategy_de=(
            "Sofort abbrechen; keine Teilcodierung speichern; kein Auto-Retry. "
            "Wiederherstellung nur mit belegtem OEM-Backup."
        ),
    ),
    _op(
        code="FLASH_PROGRAMMING",
        name_de="Steuergeräteprogrammierung (Flash)",
        category="Programmierung",
        operation_type="flash",
        safety_class="flash_critical",
        confirmation_phrase="FLASH PROGRAMMIERUNG BESTAETIGEN",
        timeout_seconds=900,
        requires_j2534=True,
        notes_de=(
            "Keine erfundenen Flashprotokolle. Nur autorisierte OEM-Abläufe oder "
            "externe OEM-Anwendung – hier DEAKTIVIERT bis Spec, Hardware und Freigabe."
        ),
        abort_strategy_de=(
            "Abbruch stoppt den Versuch; kein automatisches Wiederholen fehlgeschlagener Flashvorgänge. "
            "Wiederherstellungsplan Pflicht."
        ),
        result_checks_de=["Signatur/SW-Stand", "Spannung vor/nach", "Verbindung stabil"],
        blockers=["BLK-OEM", "BLK-HW", "BLK-RELEASE", "BLK-J2534"],
    ),
    _op(
        code="J2534_PASSTHRU_PREP",
        name_de="J2534 PassThru – Schnittstellenvorbereitung",
        category="Schnittstelle",
        operation_type="interface",
        safety_class="interface",
        release_status="documented_prep",
        confirmation_phrase=None,
        timeout_seconds=60,
        requires_j2534=True,
        requires_authorization=False,
        prerequisites=[
            {"id": "adapter_connected", "label_de": "PassThru-Gerät erkannt (simuliert)"},
        ],
        notes_de=(
            "Framework/Dokumentation für SAE J2534. Keine Vendor-DLL, kein PassThruOpen live. "
            "Siehe docs/j2534-doip-j1939-prep.md."
        ),
        blockers=["BLK-HW", "BLK-J2534"],
        compatibility_de="Nur dokumentierte Treiber/APIs – keine Blindbindung.",
        source_license_de="SAE J2534 Spezifikation (extern); keine DLL im Repo.",
    ),
    _op(
        code="DPDU_MVCI_PREP",
        name_de="ISO 22900 D-PDU / MVCI – Vorbereitung",
        category="Schnittstelle",
        operation_type="interface",
        safety_class="interface",
        release_status="documented_prep",
        confirmation_phrase=None,
        timeout_seconds=60,
        requires_authorization=False,
        prerequisites=[
            {"id": "adapter_connected", "label_de": "MVCI-Runtime verfügbar (simuliert)"},
        ],
        notes_de="Nur Prep. Keine proprietäre Runtime/Lizenz im Repo.",
        blockers=["BLK-HW", "BLK-OEM"],
        source_license_de="ISO 22900 – keine Runtime im Repo.",
    ),
    _op(
        code="GATE_CODING_PROBE",
        name_de="Gate-Simulation Codierung/Flash",
        category="Prüfung",
        operation_type="coding",
        safety_class="sim_probe",
        release_status="sim_gates_only",
        confirmation_phrase="CODING GATE BESTAETIGEN",
        timeout_seconds=60,
        notes_de=(
            "Simuliert Spannungsabfall, falsches Fahrzeug, Abbruch und fehlende Spec/Berechtigung. "
            "Sendet keine Schreib-/Flashbefehle."
        ),
        blockers=[],
        requires_authorization=True,
    ),
]

EXCLUDED_OPERATIONS: list[dict[str, Any]] = [
    {
        "code": "UNAUTH_FLASH",
        "name_de": "Unautorisierte Flash-/Rohprogrammierung",
        "reason_de": (
            "Ausgeschlossen: keine erfundenen Flashprotokolle, keine Umgehung von "
            "Schutzmechanismen, keine Rohbefehle ohne OEM-Autorisierung."
        ),
        "safety_class": "excluded",
    },
    {
        "code": "EMISSION_DEFEAT_CODING",
        "name_de": "Codierung zur Abgas-Deaktivierung",
        "reason_de": "Ausgeschlossen: keine Deaktivierung vorgeschriebener Abgasreinigung.",
        "safety_class": "excluded",
    },
]


def get_operation(code: str) -> dict[str, Any] | None:
    for op in OPERATIONS:
        if op["code"] == code:
            return op
    for ex in EXCLUDED_OPERATIONS:
        if ex["code"] == code:
            return {**ex, "enabled": False, "write_allowed": False, "flash_allowed": False}
    return None


def list_catalog(*, include_excluded: bool = True) -> dict[str, Any]:
    return {
        "data_source": "catalog",
        "disclaimer_de": (
            "Phase 12: Architektur, Identifikation und Safety-Gates. "
            "Codierung und Flash ohne Spezifikation/Berechtigung sind DEAKTIVIERT. "
            "Keine echten Flash-Routinen. Kein Auto-Retry. Demo/simuliert ≠ Live."
        ),
        "operations": list(OPERATIONS),
        "excluded": list(EXCLUDED_OPERATIONS) if include_excluded else [],
        "live_execution_available": False,
        "flash_available": False,
        "hardware_live": False,
        "auto_retry_forbidden": True,
        "j2534_status": "documented_prep",
        "dpdu_status": "documented_prep",
    }
