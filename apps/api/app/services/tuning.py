"""Phase 18 – Optionales Chiptuning: Architektur, Gates, Simulation.

Keine Kennfeldänderungen. Kein Tuning-Flash. Keine Abgas-/Sicherheitsmanipulation.
Produktive Aktivierung standardmäßig gesperrt.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.tuning_catalog import (
    EXCLUDED_OPERATIONS,
    SEED_BASELINES,
    get_operation,
    list_catalog,
)
from app.models import User, Vehicle
from app.models.tuning import (
    TuningApprovalDocument,
    TuningSoftwareBaseline,
    TuningVersionHistoryEntry,
    TuningWorkflowRun,
)
from app.schemas.tuning import (
    LegalGateCheckOut,
    PrerequisiteState,
    TuningAbortRequest,
    TuningApprovalCreate,
    TuningApprovalOut,
    TuningBaselineCreate,
    TuningBaselineOut,
    TuningCatalogOut,
    TuningGateStateIn,
    TuningHistoryOut,
    TuningModuleStatusOut,
    TuningOperationOut,
    TuningRunOut,
    TuningStartRequest,
)
from app.services.audit import write_audit
from app.services.tenant import require_workshop_id

CONFIRM_PHRASE_WORKFLOW = "TUNING WORKFLOW SIM BESTAETIGEN"
CONFIRM_PHRASE_LEGAL = "LEGAL GATE BESTAETIGEN"
CONFIRM_PHRASE_BASELINE = "BASELINE REGISTRIEREN BESTAETIGEN"
CONFIRM_PHRASE_APPROVAL = "GENEHMIGUNG DOKUMENTIEREN BESTAETIGEN"
CONFIRM_PHRASE_COMPAT = "KOMPATIBILITAET PRUEFEN BESTAETIGEN"


def catalog_payload() -> dict[str, Any]:
    return list_catalog(include_excluded=True)


def module_status() -> TuningModuleStatusOut:
    return TuningModuleStatusOut(
        disclaimer_de=(
            "Chiptuning-Modul: Geplant/deaktiviert. Nur Verwaltungs- und Gate-Simulation. "
            "Keine Kennfeldänderungen, kein Flash, keine Abgasmanipulation. "
            "Produktive Aktivierung gesperrt bis gesonderte technische und rechtliche Freigabe."
        ),
    )


def _baseline_out(row: TuningSoftwareBaseline) -> TuningBaselineOut:
    return TuningBaselineOut(
        id=row.id,
        code=row.code,
        ecu_role=row.ecu_role,
        software_version=row.software_version,
        part_number=row.part_number,
        checksum_ref=row.checksum_ref,
        source_de=row.source_de,
        authorization_status=row.authorization_status,
        compatible_notes_de=row.compatible_notes_de,
        data_source=row.data_source,
        created_at=row.created_at,
    )


def _approval_out(row: TuningApprovalDocument) -> TuningApprovalOut:
    return TuningApprovalOut(
        id=row.id,
        baseline_id=row.baseline_id,
        vehicle_id=row.vehicle_id,
        doc_type=row.doc_type,
        title_de=row.title_de,
        reference_code=row.reference_code,
        issuer_de=row.issuer_de,
        status=row.status,
        notes_de=row.notes_de,
        data_source=row.data_source,
        created_at=row.created_at,
    )


def _history_out(row: TuningVersionHistoryEntry) -> TuningHistoryOut:
    return TuningHistoryOut(
        id=row.id,
        vehicle_id=row.vehicle_id,
        baseline_id=row.baseline_id,
        ecu_role=row.ecu_role,
        software_version=row.software_version,
        event_type=row.event_type,
        message_de=row.message_de,
        data_source=row.data_source,
        created_at=row.created_at,
    )


def _run_out(run: TuningWorkflowRun, prereqs: list[PrerequisiteState] | None = None) -> TuningRunOut:
    result = json.loads(run.result_json or "{}")
    gates = json.loads(run.gates_json or "{}")
    if prereqs is None:
        raw = json.loads(run.prerequisites_json or "[]")
        prereqs = [PrerequisiteState.model_validate(p) for p in raw]
    return TuningRunOut(
        id=run.id,
        operation_code=run.operation_code,
        status=run.status,
        scenario=run.scenario,
        data_source=run.data_source,
        prerequisites=prereqs,
        gates=gates,
        result=result,
        message_de=run.message_de,
        abort_reason_de=run.abort_reason_de,
        map_commands_sent=bool(result.get("map_commands_sent", False)),
        flash_commands_sent=bool(result.get("flash_commands_sent", False)),
        tuning_activated=bool(result.get("tuning_activated", False)),
        auto_retry_attempted=bool(result.get("auto_retry_attempted", False)),
        started_at=run.started_at,
        ended_at=run.ended_at,
    )


def ensure_seed_baselines(db: Session, workshop_id: str) -> None:
    """Stellt Demo-Baseline-Metadaten bereit (keine Maps)."""
    existing = (
        db.query(TuningSoftwareBaseline)
        .filter(TuningSoftwareBaseline.workshop_id == workshop_id)
        .count()
    )
    if existing > 0:
        return
    for item in SEED_BASELINES:
        row = TuningSoftwareBaseline(
            workshop_id=workshop_id,
            code=item["code"],
            ecu_role=item["ecu_role"],
            software_version=item["software_version"],
            part_number=item.get("part_number"),
            checksum_ref=item.get("checksum_ref"),
            source_de=item["source_de"],
            authorization_status=item["authorization_status"],
            compatible_notes_de=item.get("compatible_notes_de"),
            data_source="simulated",
        )
        db.add(row)
        db.add(
            TuningVersionHistoryEntry(
                workshop_id=workshop_id,
                baseline_id=None,
                ecu_role=item["ecu_role"],
                software_version=item["software_version"],
                event_type="recorded",
                message_de=f"Demo-Baseline {item['code']} angelegt (Metadaten).",
                data_source="simulated",
            )
        )
    db.commit()


def list_baselines(db: Session, user: User) -> list[TuningBaselineOut]:
    wid = require_workshop_id(user)
    ensure_seed_baselines(db, wid)
    rows = (
        db.query(TuningSoftwareBaseline)
        .filter(TuningSoftwareBaseline.workshop_id == wid)
        .order_by(TuningSoftwareBaseline.created_at.desc())
        .all()
    )
    return [_baseline_out(r) for r in rows]


def register_baseline(db: Session, user: User, body: TuningBaselineCreate) -> TuningBaselineOut:
    wid = require_workshop_id(user)
    if user.role not in ("admin", "technician"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rolle unzureichend")
    if not body.acknowledge_no_map_binary or not body.acknowledge_demo_only:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bestätigungen erforderlich: keine Map/Binary, nur Demo/Metadaten.",
        )
    dup = (
        db.query(TuningSoftwareBaseline)
        .filter(
            TuningSoftwareBaseline.workshop_id == wid,
            TuningSoftwareBaseline.code == body.code.strip(),
        )
        .first()
    )
    if dup:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Baseline-Code existiert bereits")

    row = TuningSoftwareBaseline(
        workshop_id=wid,
        code=body.code.strip(),
        ecu_role=body.ecu_role.strip() or "engine",
        software_version=body.software_version.strip(),
        part_number=body.part_number,
        checksum_ref=body.checksum_ref,
        source_de=body.source_de.strip(),
        authorization_status="draft",
        compatible_notes_de=body.compatible_notes_de,
        data_source="simulated",
        created_by_user_id=user.id,
    )
    db.add(row)
    db.flush()
    db.add(
        TuningVersionHistoryEntry(
            workshop_id=wid,
            baseline_id=row.id,
            ecu_role=row.ecu_role,
            software_version=row.software_version,
            event_type="baseline_linked",
            message_de=f"Baseline {row.code} als draft registriert (kein Flash).",
            data_source="simulated",
            created_by_user_id=user.id,
        )
    )
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="tuning.baseline_register",
        resource=row.code,
        detail=f"baseline={row.id} status=draft no_map=true",
    )
    return _baseline_out(row)


def list_approvals(db: Session, user: User) -> list[TuningApprovalOut]:
    wid = require_workshop_id(user)
    rows = (
        db.query(TuningApprovalDocument)
        .filter(TuningApprovalDocument.workshop_id == wid)
        .order_by(TuningApprovalDocument.created_at.desc())
        .all()
    )
    return [_approval_out(r) for r in rows]


def register_approval(db: Session, user: User, body: TuningApprovalCreate) -> TuningApprovalOut:
    wid = require_workshop_id(user)
    if user.role not in ("admin", "technician"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rolle unzureichend")
    if not body.acknowledge_not_legal_advice or not body.acknowledge_no_activation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bestätigungen erforderlich: keine Rechtsberatung, keine Aktivierung.",
        )
    if body.baseline_id:
        bl = db.get(TuningSoftwareBaseline, body.baseline_id)
        if bl is None or bl.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baseline nicht gefunden")
    if body.vehicle_id:
        veh = db.get(Vehicle, body.vehicle_id)
        if veh is None or veh.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")

    row = TuningApprovalDocument(
        workshop_id=wid,
        baseline_id=body.baseline_id,
        vehicle_id=body.vehicle_id,
        doc_type=body.doc_type,
        title_de=body.title_de.strip(),
        reference_code=body.reference_code,
        issuer_de=body.issuer_de,
        status="recorded",
        notes_de=body.notes_de,
        data_source="simulated",
        created_by_user_id=user.id,
    )
    db.add(row)
    db.flush()
    if body.baseline_id:
        bl = db.get(TuningSoftwareBaseline, body.baseline_id)
        if bl:
            db.add(
                TuningVersionHistoryEntry(
                    workshop_id=wid,
                    vehicle_id=body.vehicle_id,
                    baseline_id=body.baseline_id,
                    ecu_role=bl.ecu_role,
                    software_version=bl.software_version,
                    event_type="approval_linked",
                    message_de=f"Genehmigungsnachweis „{row.title_de}“ verknüpft (kein Tuning aktiv).",
                    data_source="simulated",
                    created_by_user_id=user.id,
                )
            )
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="tuning.approval_register",
        resource=row.id,
        detail=f"type={row.doc_type} baseline={row.baseline_id} activation=locked",
    )
    return _approval_out(row)


def list_history(
    db: Session,
    user: User,
    *,
    vehicle_id: str | None = None,
    limit: int = 50,
) -> list[TuningHistoryOut]:
    wid = require_workshop_id(user)
    ensure_seed_baselines(db, wid)
    q = db.query(TuningVersionHistoryEntry).filter(TuningVersionHistoryEntry.workshop_id == wid)
    if vehicle_id:
        veh = db.get(Vehicle, vehicle_id)
        if veh is None or veh.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")
        q = q.filter(TuningVersionHistoryEntry.vehicle_id == vehicle_id)
    rows = q.order_by(TuningVersionHistoryEntry.created_at.desc()).limit(limit).all()
    return [_history_out(r) for r in rows]


def run_legal_gates(gs: TuningGateStateIn) -> LegalGateCheckOut:
    blockers: list[str] = []

    legal_ok = gs.legal_approval_present and gs.legal_gate_ack
    if not legal_ok:
        blockers.append("legal_approval_missing")

    tech_ok = gs.technical_review_present
    if not tech_ok:
        blockers.append("technical_review_missing")

    recovery_ok = gs.recovery_plan
    if not recovery_ok:
        blockers.append("recovery_plan_missing")

    emission_ok = gs.no_emission_defeat_ack
    if not emission_ok:
        blockers.append("emission_policy_ack_missing")

    if not gs.no_map_change_ack:
        blockers.append("map_change_ack_missing")

    if not gs.oem_baseline_documented:
        blockers.append("oem_baseline_undocumented")

    if not gs.hardware_suitable:
        blockers.append("hardware_unsuitable")

    vin_match: bool | None = None
    if gs.expected_vin and gs.actual_vin:
        vin_match = gs.expected_vin.strip().upper() == gs.actual_vin.strip().upper()
        if not vin_match:
            blockers.append("vin_mismatch")

    software_compatible: bool | None = None
    if gs.expected_ecu_sw and gs.actual_ecu_sw:
        software_compatible = gs.expected_ecu_sw.strip() == gs.actual_ecu_sw.strip()
        if not software_compatible:
            blockers.append("software_incompatible")

    # overall_ok nur für Gate-Framework – aktiviert niemals Tuning
    overall = (
        legal_ok
        and tech_ok
        and recovery_ok
        and emission_ok
        and gs.no_map_change_ack
        and gs.oem_baseline_documented
        and gs.hardware_suitable
        and (vin_match is not False)
        and (software_compatible is not False)
    )

    return LegalGateCheckOut(
        legal_approval_ok=legal_ok,
        technical_review_ok=tech_ok,
        recovery_plan_ok=recovery_ok,
        emission_policy_ok=emission_ok,
        map_change_blocked=True,
        flash_blocked=True,
        tuning_activation_blocked=True,
        vin_match=vin_match,
        software_compatible=software_compatible,
        overall_ok=overall,
        blockers=blockers,
        message_de=(
            "Rechtliche/technische Gates bewertet (Simulation). "
            "Kennfeldänderung, Flash und produktive Tuning-Aktivierung bleiben gesperrt."
            if overall
            else "Gates unvollständig – Tuning weiterhin gesperrt."
        ),
        productive_activation_locked=True,
    )


def evaluate_prerequisites(
    operation: dict[str, Any],
    gate_state: TuningGateStateIn,
    *,
    force_missing: bool = False,
) -> list[PrerequisiteState]:
    sm = {
        "operator_confirm": gate_state.operator_confirm,
        "legal_gate_ack": gate_state.legal_gate_ack,
        "no_emission_defeat_ack": gate_state.no_emission_defeat_ack,
        "no_map_change_ack": gate_state.no_map_change_ack,
        "legal_approval_present": gate_state.legal_approval_present,
        "technical_review_present": gate_state.technical_review_present,
        "recovery_plan": gate_state.recovery_plan,
        "oem_baseline_documented": gate_state.oem_baseline_documented,
        "hardware_suitable": gate_state.hardware_suitable,
    }
    out: list[PrerequisiteState] = []
    for pr in operation.get("prerequisites") or []:
        pid = pr["id"]
        met = bool(sm.get(pid, False))
        if force_missing and pid in (
            "legal_gate_ack",
            "no_emission_defeat_ack",
            "no_map_change_ack",
            "operator_confirm",
        ):
            met = False
        detail = None if met else "Voraussetzung nicht erfüllt (simuliert geprüft)."
        out.append(
            PrerequisiteState(
                id=pid,
                label_de=pr.get("label_de", pid),
                met=met,
                detail_de=detail,
            )
        )
    return out


def _expected_phrase(operation: dict[str, Any]) -> str | None:
    return operation.get("confirmation_phrase")


def start_run(db: Session, user: User, operation_code: str, body: TuningStartRequest) -> TuningRunOut:
    wid = require_workshop_id(user)
    op = get_operation(operation_code)
    if op is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation nicht gefunden")
    if op.get("safety_class") == "excluded":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=op.get("reason_de", "Ausgeschlossen"),
        )

    if not body.acknowledge_disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="acknowledge_disabled erforderlich: Modul ist geplant/deaktiviert.",
        )
    if not body.acknowledge_no_map_change or not body.acknowledge_no_emission_defeat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bestätigungen erforderlich: keine Kennfeldänderung, keine Abgasmanipulation.",
        )
    if not body.acknowledge_activation_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="acknowledge_activation_locked erforderlich: produktive Aktivierung gesperrt.",
        )

    phrase = _expected_phrase(op)
    if phrase and (body.confirmation_phrase or "").strip() != phrase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bestätigungsphrase erforderlich: „{phrase}“",
        )

    if body.vehicle_id:
        veh = db.get(Vehicle, body.vehicle_id)
        if veh is None or veh.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")

    force_missing = body.scenario == "missing_prereq"
    prereqs = evaluate_prerequisites(op, body.gate_state, force_missing=force_missing)
    gates = run_legal_gates(body.gate_state)

    if body.scenario == "missing_legal":
        gates = run_legal_gates(
            TuningGateStateIn(
                **{
                    **body.gate_state.model_dump(),
                    "legal_approval_present": False,
                    "legal_gate_ack": False,
                }
            )
        )

    if body.scenario == "wrong_vehicle":
        gates = run_legal_gates(
            TuningGateStateIn(
                **{
                    **body.gate_state.model_dump(),
                    "expected_vin": body.gate_state.expected_vin or "WVWZZZ1JZYW000001",
                    "actual_vin": "WRONGVIN000000001",
                }
            )
        )

    now = datetime.now(timezone.utc)
    base_result = {
        "map_commands_sent": False,
        "flash_commands_sent": False,
        "tuning_activated": False,
        "auto_retry_attempted": False,
        "productive_activation_locked": True,
        "module_status": "planned_disabled",
    }

    run = TuningWorkflowRun(
        workshop_id=wid,
        vehicle_id=body.vehicle_id,
        user_id=user.id,
        operation_code=operation_code,
        status="pending",
        scenario=body.scenario,
        data_source="simulated",
        prerequisites_json=json.dumps([p.model_dump() for p in prereqs], ensure_ascii=False),
        gates_json=json.dumps(gates.model_dump(), ensure_ascii=False),
        result_json=json.dumps(base_result, ensure_ascii=False),
        started_at=now,
    )

    all_met = all(p.met for p in prereqs)

    if body.scenario == "missing_legal" or (
        body.scenario == "normal" and op.get("requires_legal_approval") and not gates.legal_approval_ok
    ):
        run.status = "blocked"
        run.ended_at = now
        run.message_de = (
            "Rechtliche Genehmigung fehlt – Tuning-Workflow gesperrt. "
            "Keine Kennfeld-/Flashbefehle."
        )
        run.result_json = json.dumps(
            {**base_result, "gate": "legal", "blockers": gates.blockers},
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="tuning.run_blocked_legal",
            resource=operation_code,
            detail=f"run={run.id} blockers={gates.blockers}",
        )
        return _run_out(run, prereqs)

    if body.scenario == "wrong_vehicle" or (gates.vin_match is False):
        run.status = "blocked"
        run.ended_at = now
        run.message_de = "Fahrzeug/VIN stimmt nicht überein – Workflow gesperrt."
        run.result_json = json.dumps(
            {**base_result, "gate": "vin_mismatch", "blockers": gates.blockers},
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="tuning.run_blocked_vin",
            resource=operation_code,
            detail=f"run={run.id}",
        )
        return _run_out(run, prereqs)

    if not all_met:
        run.status = "blocked"
        run.ended_at = now
        run.message_de = "Voraussetzungen nicht erfüllt – Tuning-Modul bleibt deaktiviert."
        run.result_json = json.dumps(
            {
                **base_result,
                "gate": "prerequisites",
                "missing": [p.id for p in prereqs if not p.met],
            },
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="tuning.run_blocked",
            resource=operation_code,
            detail=f"run={run.id} missing={[p.id for p in prereqs if not p.met]}",
        )
        return _run_out(run, prereqs)

    if body.scenario == "comm_loss":
        run.status = "failed"
        run.ended_at = now
        run.message_de = (
            "Kommunikationsverlust simuliert – keine Kennfeld-/Flashbefehle, kein Auto-Retry."
        )
        run.result_json = json.dumps(
            {**base_result, "gate": "comm_loss", "error": "communication_lost"},
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="tuning.run_comm_loss",
            resource=operation_code,
            detail=f"run={run.id}",
        )
        return _run_out(run, prereqs)

    if body.scenario == "abort":
        run.status = "running"
        run.message_de = "Simulation läuft – Abbruch erwartet. Kein Tuning aktiviert."
        run.result_json = json.dumps({**base_result, "gate": "awaiting_abort"}, ensure_ascii=False)
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="tuning.run_started",
            resource=operation_code,
            detail=f"run={run.id} scenario=abort",
        )
        return _run_out(run, prereqs)

    # normal: complete simulation without vehicle writes / map changes
    run.status = "completed"
    run.ended_at = now
    op_type = op.get("operation_type", "workflow")
    if op_type in ("baseline", "history", "approval"):
        run.message_de = (
            "Verwaltungs-Simulation abgeschlossen. Keine Kennfeldänderung, kein Flash, "
            "Aktivierung gesperrt."
        )
    elif op_type == "legal":
        run.message_de = (
            "Legal-Gate-Simulation abgeschlossen. Produktive Aktivierung bleibt gesperrt."
        )
    else:
        run.message_de = (
            "Gate-/Workflow-Simulation abgeschlossen. Keine Fahrzeug-Schreibbefehle, "
            "kein Auto-Retry, nicht hardwaregetestet, Aktivierung gesperrt."
        )
    run.result_json = json.dumps(
        {
            **base_result,
            "gate": "ok",
            "legal_overall": gates.overall_ok,
            "activation_locked": True,
        },
        ensure_ascii=False,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="tuning.run_completed",
        resource=operation_code,
        detail=f"run={run.id} map=false flash=false activated=false",
    )
    return _run_out(run, prereqs)


def abort_run(db: Session, user: User, run_id: str, body: TuningAbortRequest) -> TuningRunOut:
    wid = require_workshop_id(user)
    run = db.get(TuningWorkflowRun, run_id)
    if run is None or run.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lauf nicht gefunden")
    if run.status not in ("running", "pending"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lauf kann nicht abgebrochen werden (Status: {run.status})",
        )
    now = datetime.now(timezone.utc)
    run.status = "aborted"
    run.ended_at = now
    run.abort_reason_de = body.reason_de or "Bedienerabbruch"
    run.message_de = "Abgebrochen – keine Kennfeld-/Flashbefehle, kein Auto-Retry, nicht aktiviert."
    result = json.loads(run.result_json or "{}")
    result["map_commands_sent"] = False
    result["flash_commands_sent"] = False
    result["tuning_activated"] = False
    result["auto_retry_attempted"] = False
    result["gate"] = "aborted"
    run.result_json = json.dumps(result, ensure_ascii=False)
    db.add(run)
    db.commit()
    db.refresh(run)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="tuning.run_aborted",
        resource=run.operation_code,
        detail=f"run={run.id} reason={run.abort_reason_de}",
    )
    return _run_out(run)


def get_run(db: Session, user: User, run_id: str) -> TuningRunOut:
    wid = require_workshop_id(user)
    run = db.get(TuningWorkflowRun, run_id)
    if run is None or run.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lauf nicht gefunden")
    return _run_out(run)


def list_runs(db: Session, user: User, *, limit: int = 50) -> list[TuningRunOut]:
    wid = require_workshop_id(user)
    rows = (
        db.query(TuningWorkflowRun)
        .filter(TuningWorkflowRun.workshop_id == wid)
        .order_by(TuningWorkflowRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [_run_out(r) for r in rows]


def activate_blocked(operation_code: str) -> None:
    """Produktive Tuning-Aktivierung – immer 403."""
    op = get_operation(operation_code)
    if op and op.get("safety_class") == "excluded":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=op.get("reason_de", "Ausgeschlossen."),
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Produktive Tuning-Aktivierung ist standardmäßig gesperrt "
            "(rechtliche/technische Prüfung, Hardware und Wiederherstellung ausstehend)."
        ),
    )


def map_change_blocked(operation_code: str) -> None:
    op = get_operation(operation_code)
    if op and op.get("safety_class") == "excluded":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=op.get("reason_de", "Ausgeschlossen."),
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Aktive Kennfeldänderungen sind in Phase 18 ausgeschlossen. "
            "Keine erfundenen Maps, keine Abgasmanipulation."
        ),
    )


def flash_blocked(operation_code: str) -> None:
    op = get_operation(operation_code)
    if op and op.get("safety_class") == "excluded":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=op.get("reason_de", "Ausgeschlossen."),
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Tuning-Flash ist nicht freigegeben (fehlende Spec, Hardware und Freigabe).",
    )


def catalog_out() -> TuningCatalogOut:
    payload = catalog_payload()
    return TuningCatalogOut(
        data_source=payload["data_source"],
        module_status=payload["module_status"],
        disclaimer_de=payload["disclaimer_de"],
        operations=[TuningOperationOut.model_validate(o) for o in payload["operations"]],
        excluded=payload["excluded"],
        live_execution_available=payload["live_execution_available"],
        map_change_available=payload["map_change_available"],
        flash_available=payload["flash_available"],
        tuning_activation_available=payload["tuning_activation_available"],
        hardware_live=payload["hardware_live"],
        auto_retry_forbidden=payload["auto_retry_forbidden"],
        productive_activation_locked=payload["productive_activation_locked"],
        legal_gates_required=payload["legal_gates_required"],
    )


# Re-export for tests / clarity
__all__ = [
    "EXCLUDED_OPERATIONS",
    "abort_run",
    "activate_blocked",
    "catalog_out",
    "flash_blocked",
    "get_run",
    "list_approvals",
    "list_baselines",
    "list_history",
    "list_runs",
    "map_change_blocked",
    "module_status",
    "register_approval",
    "register_baseline",
    "run_legal_gates",
    "start_run",
]
