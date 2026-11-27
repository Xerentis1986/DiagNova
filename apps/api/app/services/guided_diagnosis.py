"""Phase 11 – Geführte Diagnose: Messwertgruppen, DTC-Hilfe, ECU-Kurzüberblick.

Keine erfundenen Reparaturdiagnosen. Unbekannte DTCs bleiben unbekannt.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.diagnostic_data import DiagDtcDefinition, DiagDatasetVersion
from app.schemas.service import DtcHelpOut, GuidedOverviewOut, MeasurementGroupOut
from app.services import simulator
from diagnova_protocols.ecu_definition import ecu_overview_static


MEASUREMENT_GROUPS: list[MeasurementGroupOut] = [
    MeasurementGroupOut(
        id="engine_basic",
        label_de="Motor Basis",
        pid_names=["rpm", "speed", "coolant_temp", "engine_load", "throttle"],
        notes_de="Standard-OBD-PIDs sofern vom Simulator/Adapter belegt.",
        data_source="simulated",
    ),
    MeasurementGroupOut(
        id="fuel_air",
        label_de="Gemisch / Kraftstoff",
        pid_names=["maf", "fuel_level"],
        notes_de="Nur anzeigen, wenn PID-Bitmap unterstützt – sonst auslassen.",
        data_source="simulated",
    ),
    MeasurementGroupOut(
        id="temps",
        label_de="Temperaturen",
        pid_names=["coolant_temp", "intake_temp"],
        notes_de="OBD-Standard; OEM-Sensoren ohne Definition nicht erfinden.",
        data_source="simulated",
    ),
    MeasurementGroupOut(
        id="electrical",
        label_de="Bordnetz",
        pid_names=["control_module_voltage"],
        notes_de="Steuerspannung OBD PID 0x42 – kein OEM-Energiemanagement.",
        data_source="simulated",
    ),
]


def measurement_groups() -> list[MeasurementGroupOut]:
    return list(MEASUREMENT_GROUPS)


def dtc_help(db: Session, code: str) -> DtcHelpOut:
    normalized = code.strip().upper()
    # Prefer published diagnostic DB definition
    published = (
        db.query(DiagDatasetVersion)
        .filter(DiagDatasetVersion.status == "published")
        .order_by(DiagDatasetVersion.created_at.desc())
        .first()
    )
    if published:
        row = (
            db.query(DiagDtcDefinition)
            .filter(
                DiagDtcDefinition.dataset_version_id == published.id,
                DiagDtcDefinition.code == normalized,
            )
            .first()
        )
        if row is not None:
            desc = (row.description_de or "").strip() or None
            status = row.description_status or ("known" if desc else "unknown")
            # Nur mit echter Beschreibung aus der DB antworten – sonst Fallback (kein Erfinden).
            if desc and status == "known":
                return DtcHelpOut(
                    code=normalized,
                    description_de=desc,
                    description_status="known",
                    severity=None,
                    help_de=(
                        "Beschreibung aus Diagnosedatenbank mit Herkunft. "
                        "Keine automatische Reparaturdiagnose."
                    ),
                    source="diag_dtc_definitions",
                    data_source="database",
                    repair_auto_generated=False,
                )

    # Simulator catalog (demo texts, clearly simulated)
    if normalized in simulator.DTC_CATALOG:
        desc, sev = simulator.DTC_CATALOG[normalized]
        return DtcHelpOut(
            code=normalized,
            description_de=desc,
            description_status="known",
            severity=sev,
            help_de=(
                "Simulierte Demo-Beschreibung – nicht als OEM-Werkstattdaten verwenden. "
                "Keine automatische Reparaturempfehlung."
            ),
            source="simulator_catalog",
            data_source="simulated",
            repair_auto_generated=False,
        )

    return DtcHelpOut(
        code=normalized,
        description_de=None,
        description_status="unknown",
        severity=None,
        help_de="Unbekannter DTC – keine Beschreibung erfunden. Herkunft prüfen oder als unbekannt belassen.",
        source="none",
        data_source="unknown",
        repair_auto_generated=False,
    )


def guided_overview() -> GuidedOverviewOut:
    ecu = ecu_overview_static()
    return GuidedOverviewOut(
        data_source="simulated",
        disclaimer_de=(
            "Geführte Diagnose Phase 11: ECU-Überblick, Messwertgruppen und DTC-Hilfe. "
            "Servicefunktionen nur mit Specs/Safety-Gates; Live-Schreiben deaktiviert."
        ),
        ecu_summary={
            "blind_scan_allowed": ecu.get("blind_scan_allowed", False),
            "categories": ecu.get("categories"),
            "standard_obd_slots": ecu.get("standard_obd_slots"),
            "read_policy_de": ecu.get("read_policy_de"),
            "disclaimer_de": ecu.get("disclaimer_de"),
        },
        measurement_groups=measurement_groups(),
        dtc_help_hint_de="GET /api/guided/dtc/{code} – unbekannte Codes bleiben unbekannt.",
    )


def group_live_readings(vehicle_id: str, vin: str, group_id: str) -> dict[str, Any]:
    groups = {g.id: g for g in MEASUREMENT_GROUPS}
    group = groups.get(group_id)
    if group is None:
        return {
            "data_source": "simulated",
            "error": "unknown_group",
            "message_de": "Messwertgruppe nicht gefunden.",
        }
    live = simulator.live_data(vehicle_id, vin)
    wanted = set(group.pid_names)
    filtered = []
    for r in live.readings:
        name = r.name if hasattr(r, "name") else r.get("name")  # type: ignore[union-attr]
        if name in wanted:
            filtered.append(r.model_dump() if hasattr(r, "model_dump") else r)
    return {
        "data_source": "simulated",
        "group": group.model_dump(),
        "readings": filtered,
        "message_de": "Simulierte Messwerte – keine echte Fahrzeugtelemetrie.",
    }
