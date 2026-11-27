"""Phase 11 – Servicefunktionen: Katalog, Safety-Gates, Simulator-Zustandsmaschine.

Kein generischer Schreibbefehl. Kein DPF-Off. Live-Ausführung bleibt gesperrt.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.service_catalog import EXCLUDED_PROCEDURES, get_procedure, list_catalog
from app.models import User, Vehicle
from app.models.service import ServiceRun
from app.schemas.service import (
    PrerequisiteState,
    ServiceRunOut,
    ServiceStartRequest,
    VehicleStateIn,
)
from app.services.audit import write_audit
from app.services.tenant import require_workshop_id

CONFIRM_PHRASE_GATE = "GATE SIMULATION BESTAETIGEN"


def catalog_payload() -> dict[str, Any]:
    return list_catalog(include_excluded=True)


def _state_map(vs: VehicleStateIn) -> dict[str, bool]:
    return {
        "ignition_on": vs.ignition_on,
        "adapter_connected": vs.adapter_connected,
        "battery_voltage_ok": vs.battery_voltage_ok,
        "operator_confirm": vs.operator_confirm,
        "oem_spec_present": vs.oem_spec_present,
        "safe_work_area": vs.safe_work_area,
        "exhaust_safe": vs.exhaust_safe,
    }


def evaluate_prerequisites(
    procedure: dict[str, Any],
    vehicle_state: VehicleStateIn,
    *,
    force_missing: bool = False,
) -> list[PrerequisiteState]:
    sm = _state_map(vehicle_state)
    out: list[PrerequisiteState] = []
    for pr in procedure.get("prerequisites") or []:
        pid = pr["id"]
        met = bool(sm.get(pid, False))
        if force_missing and pid in ("oem_spec_present", "operator_confirm", "adapter_connected"):
            met = False
        detail = None
        if not met:
            detail = "Voraussetzung nicht erfüllt (simuliert geprüft)."
        out.append(
            PrerequisiteState(
                id=pid,
                label_de=pr.get("label_de", pid),
                met=met,
                detail_de=detail,
            )
        )
    return out


def _run_out(run: ServiceRun, prerequisites: list[PrerequisiteState] | None = None) -> ServiceRunOut:
    prereqs = prerequisites
    if prereqs is None:
        raw = json.loads(run.prerequisites_json or "[]")
        prereqs = [PrerequisiteState.model_validate(x) for x in raw]
    result = json.loads(run.result_json or "{}")
    return ServiceRunOut(
        id=run.id,
        procedure_code=run.procedure_code,
        status=run.status,
        scenario=run.scenario,
        data_source=run.data_source,
        prerequisites=prereqs,
        result=result,
        message_de=run.message_de,
        abort_reason_de=run.abort_reason_de,
        write_commands_sent=bool(result.get("write_commands_sent", False)),
        started_at=run.started_at,
        ended_at=run.ended_at,
    )


def start_run(
    db: Session,
    user: User,
    procedure_code: str,
    body: ServiceStartRequest,
) -> ServiceRunOut:
    wid = require_workshop_id(user)
    procedure = get_procedure(procedure_code)
    if procedure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prozedur nicht gefunden")

    if procedure.get("safety_class") == "excluded" or procedure_code == "DPF_OFF":
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="service.excluded_blocked",
            resource=procedure_code,
            detail="DPF-Off / ausgeschlossene Funktion abgelehnt",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ausgeschlossen: keine Deaktivierung der Abgasreinigung / DPF-Off.",
        )

    if body.vehicle_id:
        vehicle = db.get(Vehicle, body.vehicle_id)
        if vehicle is None or vehicle.workshop_id != wid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fahrzeug nicht gefunden")

    release = procedure.get("release_status")
    if release == "disabled":
        if not (body.acknowledge_disabled and body.acknowledge_no_oem_write):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Funktion ohne Freigabe deaktiviert. "
                    "Nur Gate-Simulation mit acknowledge_disabled + acknowledge_no_oem_write möglich – "
                    "keine Fahrzeug-Schreibbefehle."
                ),
            )
        # Gate-only dry-run for disabled safety-critical items
        mode = "gates_only_disabled"
    elif release == "sim_gates_only":
        mode = "sim_gates_only"
    else:
        mode = "catalog_only"

    # Live write path always blocked in Phase 11
    if procedure.get("write_allowed") or procedure.get("enabled"):
        # defensive – catalog never sets these true
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live-Ausführung ist in Phase 11 nicht freigegeben.",
        )

    phrase = procedure.get("confirmation_phrase")
    if phrase and body.scenario != "missing_prereq":
        if (body.confirmation_phrase or "").strip() != phrase:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bestätigungsphrase fehlt oder falsch. Erwartet: {phrase}",
            )

    force_missing = body.scenario == "missing_prereq"
    prereqs = evaluate_prerequisites(procedure, body.vehicle_state, force_missing=force_missing)
    all_met = all(p.met for p in prereqs)

    now = datetime.now(timezone.utc)
    run = ServiceRun(
        workshop_id=wid,
        vehicle_id=body.vehicle_id,
        user_id=user.id,
        procedure_code=procedure_code,
        status="pending",
        scenario=body.scenario,
        data_source="simulated",
        prerequisites_json=json.dumps([p.model_dump() for p in prereqs], ensure_ascii=False),
        result_json="{}",
        started_at=now,
    )

    if not all_met:
        run.status = "blocked"
        run.ended_at = now
        run.message_de = "Voraussetzungen nicht erfüllt – Ausführung gesperrt."
        run.result_json = json.dumps(
            {
                "write_commands_sent": False,
                "mode": mode,
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
            action="service.run_blocked",
            resource=procedure_code,
            detail=f"run={run.id} missing={[p.id for p in prereqs if not p.met]}",
        )
        return _run_out(run, prereqs)

    if body.scenario == "comm_loss":
        run.status = "failed"
        run.ended_at = now
        run.message_de = "Kommunikationsverlust simuliert – keine Schreibbefehle gesendet."
        run.result_json = json.dumps(
            {
                "write_commands_sent": False,
                "mode": mode,
                "gate": "comm_loss",
                "error": "communication_lost",
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
            action="service.run_comm_loss",
            resource=procedure_code,
            detail=f"run={run.id}",
        )
        return _run_out(run, prereqs)

    if body.scenario == "abort":
        # Start as running then immediately leave as running so client can abort,
        # or auto-mark running for abort endpoint.
        run.status = "running"
        run.message_de = "Simulation läuft – Abbruch erwartet."
        run.result_json = json.dumps(
            {"write_commands_sent": False, "mode": mode, "gate": "awaiting_abort"},
            ensure_ascii=False,
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        write_audit(
            db,
            user_id=user.id,
            workshop_id=wid,
            action="service.run_started",
            resource=procedure_code,
            detail=f"run={run.id} scenario=abort",
        )
        return _run_out(run, prereqs)

    # normal: complete gate simulation without vehicle writes
    run.status = "completed"
    run.ended_at = now
    run.message_de = (
        "Gate-Simulation abgeschlossen. Keine Fahrzeug-Schreibbefehle, "
        "keine OEM-Prozedur ausgeführt, nicht hardwaregetestet."
    )
    run.result_json = json.dumps(
        {
            "write_commands_sent": False,
            "mode": mode,
            "gate": "ok",
            "live_execution": False,
            "hardware_tested": False,
            "release_status": release,
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
        action="service.run_completed_gates",
        resource=procedure_code,
        detail=f"run={run.id} mode={mode}",
    )
    return _run_out(run, prereqs)


def abort_run(db: Session, user: User, run_id: str, reason_de: str | None) -> ServiceRunOut:
    wid = require_workshop_id(user)
    run = db.get(ServiceRun, run_id)
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
    run.abort_reason_de = reason_de or "Bedienerabbruch"
    run.message_de = "Abgebrochen – keine Schreibbefehle gesendet."
    result = json.loads(run.result_json or "{}")
    result["write_commands_sent"] = False
    result["gate"] = "aborted"
    run.result_json = json.dumps(result, ensure_ascii=False)
    db.add(run)
    db.commit()
    db.refresh(run)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="service.run_aborted",
        resource=run.procedure_code,
        detail=f"run={run.id} reason={run.abort_reason_de}",
    )
    return _run_out(run)


def get_run(db: Session, user: User, run_id: str) -> ServiceRunOut:
    wid = require_workshop_id(user)
    run = db.get(ServiceRun, run_id)
    if run is None or run.workshop_id != wid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lauf nicht gefunden")
    return _run_out(run)


def list_runs(db: Session, user: User, *, limit: int = 50) -> list[ServiceRunOut]:
    wid = require_workshop_id(user)
    rows = (
        db.query(ServiceRun)
        .filter(ServiceRun.workshop_id == wid)
        .order_by(ServiceRun.started_at.desc())
        .limit(limit)
        .all()
    )
    return [_run_out(r) for r in rows]


def execute_live_blocked(procedure_code: str) -> None:
    """Expliziter Live-Pfad – immer 403."""
    procedure = get_procedure(procedure_code)
    if procedure and procedure.get("safety_class") == "excluded":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ausgeschlossen: DPF-Off / Abgas-Deaktivierung.",
        )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Live-Serviceausführung ist nicht freigegeben "
            "(fehlende OEM-Spezifikation, Hardwaretest und fachliche Freigabe)."
        ),
    )
