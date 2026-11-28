"""Phase 18 – Optionales Chiptuning: Katalog (nur Architektur).

Keine Kennfeldänderungen, keine Flashfunktionen, keine Abgas-/Sicherheitsmanipulation.
Nur Verwaltung autorisierter Originalsoftwarestände, Versionshistorie, Kompatibilität,
Genehmigungsnachweise, Audit und simulierte Arbeitsabläufe. Produktive Aktivierung gesperrt.
"""

from __future__ import annotations

from typing import Any


def _op(
    *,
    code: str,
    name_de: str,
    category: str,
    operation_type: str,
    safety_class: str = "admin_sim",
    release_status: str = "disabled",
    prerequisites: list[dict[str, str]] | None = None,
    confirmation_phrase: str | None = None,
    timeout_seconds: int = 60,
    abort_strategy_de: str = "Sofort abbrechen; keine Fahrzeugschreibvorgänge.",
    result_checks_de: list[str] | None = None,
    notes_de: str = "",
    blockers: list[str] | None = None,
    requires_legal_approval: bool = True,
    requires_technical_review: bool = True,
    map_change_allowed: bool = False,
    flash_allowed: bool = False,
) -> dict[str, Any]:
    return {
        "code": code,
        "name_de": name_de,
        "category": category,
        "operation_type": operation_type,  # baseline | history | compatibility | approval | workflow | legal
        "safety_class": safety_class,
        "release_status": release_status,
        "enabled": False,
        "write_allowed": False,
        "map_change_allowed": map_change_allowed,
        "flash_allowed": flash_allowed,
        "tuning_activation_allowed": False,
        "prerequisites": prerequisites
        or [
            {"id": "operator_confirm", "label_de": "Fachkraft bestätigt Simulation"},
            {"id": "legal_gate_ack", "label_de": "Rechtliche Hinweise bestätigt"},
            {"id": "no_emission_defeat_ack", "label_de": "Keine Abgas-Manipulation bestätigt"},
            {"id": "no_map_change_ack", "label_de": "Keine Kennfeldänderung bestätigt"},
        ],
        "confirmation_phrase": confirmation_phrase,
        "timeout_seconds": timeout_seconds,
        "abort_strategy_de": abort_strategy_de,
        "result_checks_de": result_checks_de
        or ["Nur Metadaten/Simulation; kein ECU-Schreiben"],
        "notes_de": notes_de,
        "blockers": blockers or ["BLK-LEGAL", "BLK-OEM", "BLK-HW", "BLK-RELEASE"],
        "requires_legal_approval": requires_legal_approval,
        "requires_technical_review": requires_technical_review,
        "data_source": "catalog",
        "oem_maps_invented": False,
        "auto_retry_forbidden": True,
        "productive_activation_locked": True,
    }


OPERATIONS: list[dict[str, Any]] = [
    _op(
        code="OEM_BASELINE_LIST",
        name_de="Autorisierte Originalsoftwarestände auflisten",
        category="Softwarestände",
        operation_type="baseline",
        safety_class="read_only",
        release_status="sim_gates_only",
        confirmation_phrase=None,
        timeout_seconds=30,
        requires_legal_approval=False,
        requires_technical_review=False,
        prerequisites=[
            {"id": "operator_confirm", "label_de": "Fachkraft bestätigt Lesen"},
        ],
        notes_de=(
            "Liest nur hinterlegte Metadaten autorisierter OEM-Softwarestände. "
            "Keine Kennfelder, keine Binaries, keine erfundenen OEM-Maps."
        ),
        blockers=["BLK-OEM"],
        result_checks_de=["Liste enthält nur dokumentierte Baselines"],
    ),
    _op(
        code="OEM_BASELINE_REGISTER",
        name_de="Autorisierten Originalsoftwarestand registrieren",
        category="Softwarestände",
        operation_type="baseline",
        safety_class="admin_sim",
        release_status="sim_gates_only",
        confirmation_phrase="BASELINE REGISTRIEREN BESTAETIGEN",
        notes_de=(
            "Registriert Metadaten (Version, ECU-Rolle, Quelle, Prüfsummenverweis). "
            "Kein Flash, keine Map-Datei. Ohne Genehmigungsnachweis bleibt Status draft."
        ),
        blockers=["BLK-OEM", "BLK-LEGAL"],
    ),
    _op(
        code="VERSION_HISTORY_VIEW",
        name_de="Versionshistorie anzeigen",
        category="Historie",
        operation_type="history",
        safety_class="read_only",
        release_status="sim_gates_only",
        confirmation_phrase=None,
        timeout_seconds=30,
        requires_legal_approval=False,
        requires_technical_review=False,
        prerequisites=[
            {"id": "operator_confirm", "label_de": "Fachkraft bestätigt Lesen"},
        ],
        notes_de="Simulierte/werkstattseitige Versionshistorie – nicht als Live-ECU-Stand behaupten.",
        blockers=[],
    ),
    _op(
        code="COMPATIBILITY_CHECK",
        name_de="Kompatibilitätsprüfung Baseline ↔ Fahrzeug",
        category="Kompatibilität",
        operation_type="compatibility",
        safety_class="sim_probe",
        release_status="sim_gates_only",
        confirmation_phrase="KOMPATIBILITAET PRUEFEN BESTAETIGEN",
        notes_de=(
            "Framework-Prüfung (VIN/ECU/SW/Dokument). Kein Schreiben. "
            "overall_ok bedeutet nicht Freigabe für Tuning/Flash."
        ),
        blockers=["BLK-OEM"],
    ),
    _op(
        code="APPROVAL_DOC_REGISTER",
        name_de="Genehmigungsnachweis hinterlegen",
        category="Recht / Genehmigung",
        operation_type="approval",
        safety_class="admin_sim",
        release_status="sim_gates_only",
        confirmation_phrase="GENEHMIGUNG DOKUMENTIEREN BESTAETIGEN",
        notes_de=(
            "Speichert Verweis/Metadaten zu Genehmigungsnachweisen (z. B. Typgenehmigung, "
            "Werkstattfreigabe). Keine Rechtsberatung; keine Aktivierung von Tuning."
        ),
        blockers=["BLK-LEGAL"],
        requires_legal_approval=True,
        requires_technical_review=False,
    ),
    _op(
        code="APPROVAL_DOC_LIST",
        name_de="Genehmigungsnachweise auflisten",
        category="Recht / Genehmigung",
        operation_type="approval",
        safety_class="read_only",
        release_status="sim_gates_only",
        confirmation_phrase=None,
        timeout_seconds=30,
        requires_legal_approval=False,
        requires_technical_review=False,
        prerequisites=[
            {"id": "operator_confirm", "label_de": "Fachkraft bestätigt Lesen"},
        ],
        notes_de="Nur Mandanten-eigene Dokumentmetadaten.",
        blockers=["BLK-LEGAL"],
    ),
    _op(
        code="LEGAL_GATE_CHECK",
        name_de="Rechtliche / technische Gates prüfen",
        category="Gates",
        operation_type="legal",
        safety_class="sim_probe",
        release_status="sim_gates_only",
        confirmation_phrase="LEGAL GATE BESTAETIGEN",
        notes_de=(
            "Prüft dokumentierte Gates: Genehmigung, technische Review, Wiederherstellung, "
            "kein Abgas-/Sicherheits-Eingriff. Produktive Aktivierung bleibt gesperrt."
        ),
        blockers=["BLK-LEGAL", "BLK-RELEASE"],
    ),
    _op(
        code="WORKFLOW_SIM_GATE",
        name_de="Simulierter Tuning-Arbeitsablauf (Gates)",
        category="Workflow",
        operation_type="workflow",
        safety_class="sim_probe",
        release_status="sim_gates_only",
        confirmation_phrase="TUNING WORKFLOW SIM BESTAETIGEN",
        notes_de=(
            "Simuliert Ablauf inkl. fehlender Genehmigung, Abbruch, Kommunikationsverlust. "
            "Sendet keine Kennfeld-/Flashbefehle. Standardmäßig deaktiviert."
        ),
        blockers=["BLK-LEGAL", "BLK-OEM", "BLK-HW", "BLK-RELEASE"],
    ),
]

EXCLUDED_OPERATIONS: list[dict[str, Any]] = [
    {
        "code": "MAP_CHANGE_ACTIVE",
        "name_de": "Aktive Kennfeldänderung",
        "reason_de": (
            "Ausgeschlossen in Phase 18: keine aktiven Kennfeldänderungen ohne gesonderte "
            "technische und rechtliche Prüfung, geeignete Hardware und Wiederherstellungsprozess."
        ),
        "safety_class": "excluded",
    },
    {
        "code": "TUNING_FLASH",
        "name_de": "Tuning-Flash / Programmierung",
        "reason_de": (
            "Ausgeschlossen: keine Flashfunktionen für Tuning ohne Freigabe. "
            "Flash-Pfad bleibt 403 (siehe auch Phase 12)."
        ),
        "safety_class": "excluded",
    },
    {
        "code": "EMISSION_DEFEAT_TUNE",
        "name_de": "Abgas-/DPF/SCR-Manipulation",
        "reason_de": (
            "Ausgeschlossen: keine Manipulation vorgeschriebener Abgasreinigung "
            "(DPF-Off, SCR-Off, Katalysator-Deaktivierung u. Ä.)."
        ),
        "safety_class": "excluded",
    },
    {
        "code": "SAFETY_SYSTEM_DISABLE",
        "name_de": "Sicherheitsystem-Deaktivierung",
        "reason_de": "Ausgeschlossen: keine Deaktivierung vorgeschriebener Sicherheitssysteme.",
        "safety_class": "excluded",
    },
    {
        "code": "RAW_REMOTE_TUNE",
        "name_de": "Remote-Rohbefehle / ungeprüfte Maps",
        "reason_de": (
            "Ausgeschlossen: keine beliebigen Remote-Rohbefehle und keine erfundenen OEM-Maps."
        ),
        "safety_class": "excluded",
    },
]

# Demo-Baseline-Metadaten (keine echten OEM-Maps / keine Binaries)
SEED_BASELINES: list[dict[str, Any]] = [
    {
        "code": "DEMO-OEM-ENGINE-1.0.0",
        "ecu_role": "engine",
        "software_version": "1.0.0",
        "part_number": "DEMO-PN-0001",
        "checksum_ref": "sha256:demo-placeholder-not-a-real-map",
        "source_de": "Demo-Metadaten – keine OEM-Lizenz, keine Binärdatei",
        "authorization_status": "unauthorized_demo",
        "compatible_notes_de": "Nur für Simulation/Gates; nicht fahrzeugbezogen freigegeben.",
    },
    {
        "code": "DEMO-OEM-TCU-1.0.0",
        "ecu_role": "transmission",
        "software_version": "1.0.0",
        "part_number": "DEMO-PN-TCU-01",
        "checksum_ref": "sha256:demo-tcu-placeholder",
        "source_de": "Demo-Metadaten – keine OEM-Lizenz",
        "authorization_status": "unauthorized_demo",
        "compatible_notes_de": "Platzhalter Getriebe-SW; keine echte Kompatibilitätsgarantie.",
    },
]


def get_operation(code: str) -> dict[str, Any] | None:
    for op in OPERATIONS:
        if op["code"] == code:
            return op
    for ex in EXCLUDED_OPERATIONS:
        if ex["code"] == code:
            return {
                **ex,
                "enabled": False,
                "write_allowed": False,
                "map_change_allowed": False,
                "flash_allowed": False,
                "tuning_activation_allowed": False,
            }
    return None


def list_catalog(*, include_excluded: bool = True) -> dict[str, Any]:
    return {
        "data_source": "catalog",
        "module_status": "planned_disabled",
        "disclaimer_de": (
            "Phase 18 (optional): Nur Architektur und Verwaltungs-Skelett. "
            "Kennfeldänderungen, Tuning-Flash und Abgas-/Sicherheitsmanipulation sind "
            "ausgeschlossen. Produktive Aktivierung standardmäßig gesperrt. "
            "Demo/simuliert ≠ Live. Keine Bosch/Gutmann/Delphi-Gleichwertigkeit."
        ),
        "operations": list(OPERATIONS),
        "excluded": list(EXCLUDED_OPERATIONS) if include_excluded else [],
        "live_execution_available": False,
        "map_change_available": False,
        "flash_available": False,
        "tuning_activation_available": False,
        "hardware_live": False,
        "auto_retry_forbidden": True,
        "productive_activation_locked": True,
        "legal_gates_required": True,
    }
