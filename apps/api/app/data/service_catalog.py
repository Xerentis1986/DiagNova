"""Phase 11 – Servicekatalog ohne erfundene OEM-Prozeduren.

Jede Prozedur ist spezifiziert (Voraussetzungen, Safety-Gates, Timeout, Abbruch).
Schreibende/sicherheitskritische Abläufe bleiben deaktiviert bis fachliche Freigabe
und realer kontrollierter Test. DPF-Off / Abgas-Deaktivierung sind ausgeschlossen.
"""

from __future__ import annotations

from typing import Any, Literal

ReleaseStatus = Literal["disabled", "sim_gates_only", "read_catalog"]
SafetyClass = Literal["read_only", "service_reset", "safety_critical", "excluded"]
Category = Literal[
    "inspection",
    "battery",
    "brakes",
    "dpf",
    "injection",
    "intake",
    "steering",
    "actuator",
    "basic_settings",
    "guided",
]


def _proc(
    *,
    code: str,
    name_de: str,
    category: Category,
    safety_class: SafetyClass,
    release_status: ReleaseStatus,
    prerequisites: list[dict[str, str]],
    confirmation_phrase: str | None,
    timeout_seconds: int,
    abort_strategy_de: str,
    result_checks_de: list[str],
    ecu_roles: list[str],
    compatibility_de: str,
    source_license_de: str,
    notes_de: str,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "name_de": name_de,
        "category": category,
        "safety_class": safety_class,
        "release_status": release_status,
        "enabled": False,  # keine Live-Freigabe in Phase 11
        "write_allowed": False,
        "prerequisites": prerequisites,
        "confirmation_phrase": confirmation_phrase,
        "timeout_seconds": timeout_seconds,
        "abort_strategy_de": abort_strategy_de,
        "result_checks_de": result_checks_de,
        "ecu_roles": ecu_roles,
        "compatibility_de": compatibility_de,
        "source_license_de": source_license_de,
        "notes_de": notes_de,
        "blockers": blockers or ["BLK-OEM", "BLK-HW", "BLK-RELEASE"],
        "data_source": "catalog",
        "oem_procedure_invented": False,
    }


# Generische, belegte Voraussetzungen (keine OEM-UDS-Schritte)
_PREREQ_IGNITION = {
    "id": "ignition_on",
    "label_de": "Zündung ein (Motor aus, sofern nicht anders gefordert)",
}
_PREREQ_ADAPTER = {
    "id": "adapter_connected",
    "label_de": "Diagnoseadapter verbunden und kommunikationsfähig",
}
_PREREQ_BATTERY = {
    "id": "battery_voltage_ok",
    "label_de": "Bordnetzspannung im sicheren Bereich (typ. ≥ 12,0 V stehend)",
}
_PREREQ_OPERATOR = {
    "id": "operator_confirm",
    "label_de": "Fachkraft bestätigt Fahrzeug/ECU-Kompatibilität und Arbeitsumfeld",
}
_PREREQ_OEM_SPEC = {
    "id": "oem_spec_present",
    "label_de": "Lizenzierte OEM-/Herstellerprozedur und ECU-Adressen vorhanden",
}
_PREREQ_SAFE_AREA = {
    "id": "safe_work_area",
    "label_de": "Fahrzeug standfest, sicherer Arbeitsbereich, keine Personen im Gefahrenbereich",
}
_PREREQ_EXHAUST = {
    "id": "exhaust_safe",
    "label_de": "Abgasführung sicher (Halle/Absaugung), keine Brandgefahr",
}


SERVICE_CATALOG: list[dict[str, Any]] = [
    _proc(
        code="OIL_INSPECTION_RESET",
        name_de="Öl- / Inspektionsintervall-Reset",
        category="inspection",
        safety_class="service_reset",
        release_status="disabled",
        prerequisites=[_PREREQ_IGNITION, _PREREQ_ADAPTER, _PREREQ_OEM_SPEC, _PREREQ_OPERATOR],
        confirmation_phrase="SERVICE RESET BESTAETIGEN",
        timeout_seconds=120,
        abort_strategy_de="Sofort abbrechen; kein Retry ohne erneute Freigabe; Zustand unverändert belassen.",
        result_checks_de=[
            "Service-Anzeige / Kilometerstand erneut auslesen (nur mit OEM-DID)",
            "Keine automatische Bestätigung ohne Rücklesung",
        ],
        ecu_roles=["instrument_cluster", "gateway"],
        compatibility_de="Nur mit belegter Marke/Modell/ECU-Definition und lizenzierter Prozedur.",
        source_license_de="Keine OEM-Reset-Schritte im Repo – Platzhalter bis Lizenz/Freigabe.",
        notes_de="Deaktiviert. Keine generischen Schreibbefehle.",
    ),
    _proc(
        code="BATTERY_REGISTRATION",
        name_de="Batterieanlernen / IBS-Registrierung",
        category="battery",
        safety_class="service_reset",
        release_status="disabled",
        prerequisites=[_PREREQ_IGNITION, _PREREQ_ADAPTER, _PREREQ_BATTERY, _PREREQ_OEM_SPEC, _PREREQ_OPERATOR],
        confirmation_phrase="BATTERIE ANLERNEN BESTAETIGEN",
        timeout_seconds=180,
        abort_strategy_de="Abbruch → Sitzung beenden; Batterietyp nicht spekulativ schreiben.",
        result_checks_de=["IBS-/Energiemanagement-Status rücklesen (OEM)", "Audit speichern"],
        ecu_roles=["body", "gateway", "energy"],
        compatibility_de="Hersteller-/Baujahr-spezifisch; ohne Definition gesperrt.",
        source_license_de="Keine IBS-Codierdaten im Repo.",
        notes_de="Deaktiviert bis OEM-Spezifikation und Freigabe.",
    ),
    _proc(
        code="EPB_SERVICE_MODE",
        name_de="Elektrische Feststellbremse (EPB) – Servicemodus",
        category="brakes",
        safety_class="safety_critical",
        release_status="disabled",
        prerequisites=[
            _PREREQ_SAFE_AREA,
            _PREREQ_IGNITION,
            _PREREQ_ADAPTER,
            _PREREQ_BATTERY,
            _PREREQ_OEM_SPEC,
            _PREREQ_OPERATOR,
        ],
        confirmation_phrase="EPB SERVICE BESTAETIGEN",
        timeout_seconds=300,
        abort_strategy_de="Sofort stoppen; Fahrzeug nicht bewegen; manuelle Sicherung prüfen.",
        result_checks_de=["EPB-Status rücklesen", "Warnleuchten prüfen", "Audit"],
        ecu_roles=["abs_esp", "epb"],
        compatibility_de="Nur mit verifizierter EPB-ECU-Adresse und Herstellervorgabe.",
        source_license_de="Keine EPB-Routinen im Repo.",
        notes_de="Sicherheitskritisch – ohne Freigabe und realen Test deaktiviert.",
        blockers=["BLK-OEM", "BLK-HW", "BLK-RELEASE", "BLK-SAFETY"],
    ),
    _proc(
        code="DPF_STATUS_READ",
        name_de="DPF-Diagnose (Status lesen)",
        category="dpf",
        safety_class="read_only",
        release_status="sim_gates_only",
        prerequisites=[_PREREQ_IGNITION, _PREREQ_ADAPTER, _PREREQ_OEM_SPEC],
        confirmation_phrase=None,
        timeout_seconds=60,
        abort_strategy_de="Lesung abbrechen; keine Schreibbefehle.",
        result_checks_de=["Nur anzeigen, wenn OEM-DID belegt; sonst „nicht verfügbar“"],
        ecu_roles=["ecm"],
        compatibility_de="Lesend, sofern lizenzierte DIDs vorliegen – sonst nur Katalogeintrag.",
        source_license_de="Keine erfundenen DPF-DIDs; Simulator zeigt Gate-Verhalten.",
        notes_de="Gate-Simulation erlaubt. Keine Live-Werte als echt ausgeben.",
        blockers=["BLK-OEM", "BLK-HW"],
    ),
    _proc(
        code="DPF_REGENERATION",
        name_de="DPF-Regeneration (erzwungen)",
        category="dpf",
        safety_class="safety_critical",
        release_status="disabled",
        prerequisites=[
            _PREREQ_EXHAUST,
            _PREREQ_SAFE_AREA,
            _PREREQ_IGNITION,
            _PREREQ_ADAPTER,
            _PREREQ_BATTERY,
            _PREREQ_OEM_SPEC,
            _PREREQ_OPERATOR,
        ],
        confirmation_phrase="DPF REGENERATION BESTAETIGEN",
        timeout_seconds=2400,
        abort_strategy_de="Abbruch laut OEM; Abgastemperaturen beobachten; kein Blind-Retry.",
        result_checks_de=["Ruß-/Aschewerte rücklesen", "DTCs nach Lauf", "Audit"],
        ecu_roles=["ecm"],
        compatibility_de="Nur nach OEM-Spezifikation und kontrolliertem Test.",
        source_license_de="Keine Regenerationsroutine im Repo.",
        notes_de="Ohne Freigabe deaktiviert. Kein DPF-Off.",
        blockers=["BLK-OEM", "BLK-HW", "BLK-RELEASE", "BLK-SAFETY"],
    ),
    _proc(
        code="DPF_FILTER_REPLACE",
        name_de="DPF-Filtertausch / Aschezähler-Reset",
        category="dpf",
        safety_class="safety_critical",
        release_status="disabled",
        prerequisites=[_PREREQ_OEM_SPEC, _PREREQ_OPERATOR, _PREREQ_ADAPTER, _PREREQ_EXHAUST],
        confirmation_phrase="DPF FILTERTAUSCH BESTAETIGEN",
        timeout_seconds=600,
        abort_strategy_de="Kein Reset ohne physischen Tausch-Nachweis; Abbruch ohne Schreiben.",
        result_checks_de=["Aschezähler nur nach OEM rücksetzen", "Audit mit Nachweis"],
        ecu_roles=["ecm"],
        compatibility_de="OEM-pflichtig.",
        source_license_de="Keine Reset-Schritte im Repo.",
        notes_de="Deaktiviert. Kein DPF-Off / Abgas-Deaktivierung.",
        blockers=["BLK-OEM", "BLK-HW", "BLK-RELEASE", "BLK-SAFETY"],
    ),
    _proc(
        code="INJECTOR_CODING",
        name_de="Injektorcodierung",
        category="injection",
        safety_class="safety_critical",
        release_status="disabled",
        prerequisites=[_PREREQ_OEM_SPEC, _PREREQ_OPERATOR, _PREREQ_ADAPTER, _PREREQ_IGNITION],
        confirmation_phrase="INJEKTORCODIERUNG BESTAETIGEN",
        timeout_seconds=300,
        abort_strategy_de="Keine Teilcodierung speichern; Rollback nur wenn OEM es vorsieht.",
        result_checks_de=["Codierwerte rücklesen", "Leerlauf/DTCs prüfen"],
        ecu_roles=["ecm"],
        compatibility_de="Nur mit belegten IMA/Codierdaten – nicht erfinden.",
        source_license_de="Keine Injektor-Tabellen im Repo.",
        notes_de="Deaktiviert.",
        blockers=["BLK-OEM", "BLK-HW", "BLK-RELEASE"],
    ),
    _proc(
        code="THROTTLE_ADAPTATION",
        name_de="Drosselklappen-Anpassung",
        category="intake",
        safety_class="service_reset",
        release_status="disabled",
        prerequisites=[_PREREQ_OEM_SPEC, _PREREQ_OPERATOR, _PREREQ_ADAPTER, _PREREQ_IGNITION],
        confirmation_phrase="DROSSELKLAPPE ANPASSEN BESTAETIGEN",
        timeout_seconds=180,
        abort_strategy_de="Abbruch → Grundeinstellung nicht als erfolgreich markieren.",
        result_checks_de=["Lernwerte rücklesen (OEM)", "Leerlauf beobachten"],
        ecu_roles=["ecm"],
        compatibility_de="OEM-Prozedur erforderlich.",
        source_license_de="Keine Stellglied-Routinen im Repo.",
        notes_de="Deaktiviert.",
    ),
    _proc(
        code="STEERING_ANGLE_CAL",
        name_de="Lenkwinkelsensor-Kalibrierung",
        category="steering",
        safety_class="safety_critical",
        release_status="disabled",
        prerequisites=[
            _PREREQ_SAFE_AREA,
            _PREREQ_OEM_SPEC,
            _PREREQ_OPERATOR,
            _PREREQ_ADAPTER,
            _PREREQ_IGNITION,
        ],
        confirmation_phrase="LENKWINKEL KALIBRIEREN BESTAETIGEN",
        timeout_seconds=240,
        abort_strategy_de="Abbruch; Fahrzeug nicht bewegen bis Status klar.",
        result_checks_de=["Sensor-Nullpunkt rücklesen", "ESP-Warnungen prüfen"],
        ecu_roles=["abs_esp", "steering"],
        compatibility_de="Sicherheitskritisch – nur mit OEM und Freigabe.",
        source_license_de="Keine Kalibrierroutine im Repo.",
        notes_de="Deaktiviert.",
        blockers=["BLK-OEM", "BLK-HW", "BLK-RELEASE", "BLK-SAFETY"],
    ),
    _proc(
        code="ACTUATOR_TEST_GENERIC",
        name_de="Stellgliedtest (generisches Gerüst)",
        category="actuator",
        safety_class="safety_critical",
        release_status="disabled",
        prerequisites=[_PREREQ_OEM_SPEC, _PREREQ_OPERATOR, _PREREQ_SAFE_AREA, _PREREQ_ADAPTER],
        confirmation_phrase="STELLGLIEDTEST BESTAETIGEN",
        timeout_seconds=120,
        abort_strategy_de="Sofort stoppen; keine Daueransteuerung.",
        result_checks_de=["Nur dokumentierte Routine-IDs; Ergebnis prüfen"],
        ecu_roles=["ecm", "abs_esp", "body"],
        compatibility_de="Kein Blind-IO-Control. Nur mit Spezifikation.",
        source_license_de="Keine UDS-Routine-IDs erfunden.",
        notes_de="Gerüst für spätere Freigabe – Ausführung gesperrt.",
        blockers=["BLK-OEM", "BLK-HW", "BLK-RELEASE", "BLK-SAFETY"],
    ),
    _proc(
        code="BASIC_SETTINGS",
        name_de="Grundeinstellungen",
        category="basic_settings",
        safety_class="service_reset",
        release_status="disabled",
        prerequisites=[_PREREQ_OEM_SPEC, _PREREQ_OPERATOR, _PREREQ_ADAPTER, _PREREQ_IGNITION],
        confirmation_phrase="GRUNDEINSTELLUNG BESTAETIGEN",
        timeout_seconds=300,
        abort_strategy_de="Abbruch ohne Speichern unvollständiger Schritte.",
        result_checks_de=["OEM-Ergebnisprüfung", "Audit"],
        ecu_roles=["ecm", "transmission", "abs_esp"],
        compatibility_de="Nur mit belegter Prozedur pro ECU.",
        source_license_de="Keine OEM-Schritte im Repo.",
        notes_de="Deaktiviert.",
    ),
    _proc(
        code="GATE_SIMULATION_PROBE",
        name_de="Safety-Gate-Simulation (kein Fahrzeugbefehl)",
        category="guided",
        safety_class="read_only",
        release_status="sim_gates_only",
        prerequisites=[_PREREQ_ADAPTER, _PREREQ_OPERATOR],
        confirmation_phrase="GATE SIMULATION BESTAETIGEN",
        timeout_seconds=30,
        abort_strategy_de="Simulation jederzeit abbrechbar; keine Nebenwirkungen am Fahrzeug.",
        result_checks_de=["Statusanzeige: completed / aborted / failed / blocked"],
        ecu_roles=[],
        compatibility_de="Nur Simulator – prüft Voraussetzungen, Abbruch und Kommunikationsverlust.",
        source_license_de="Internes Testartefakt, keine OEM-Daten.",
        notes_de="Erlaubt Gate-Tests ohne Schreibzugriff.",
        blockers=[],
    ),
]

# Explizit ausgeschlossen – nie im ausführbaren Katalog
EXCLUDED_PROCEDURES: list[dict[str, Any]] = [
    {
        "code": "DPF_OFF",
        "name_de": "DPF-Off / Abgasreinigung deaktivieren",
        "safety_class": "excluded",
        "release_status": "disabled",
        "enabled": False,
        "write_allowed": False,
        "reason_de": "Ausgeschlossen: keine Umgehung vorgeschriebener Abgasreinigung.",
        "oem_procedure_invented": False,
    },
]


def get_procedure(code: str) -> dict[str, Any] | None:
    for p in SERVICE_CATALOG:
        if p["code"] == code:
            return dict(p)
    for p in EXCLUDED_PROCEDURES:
        if p["code"] == code:
            return dict(p)
    return None


def list_catalog(*, include_excluded: bool = True) -> dict[str, Any]:
    return {
        "data_source": "catalog",
        "disclaimer_de": (
            "Servicekatalog Phase 11: Spezifikationen und Safety-Gates. "
            "Keine erfundenen OEM-Schreibprozeduren. Sicherheitskritische Funktionen "
            "sind ohne Freigabe deaktiviert. DPF-Off ist ausgeschlossen."
        ),
        "procedures": [dict(p) for p in SERVICE_CATALOG],
        "excluded": [dict(p) for p in EXCLUDED_PROCEDURES] if include_excluded else [],
        "live_execution_available": False,
        "hardware_live": False,
    }
