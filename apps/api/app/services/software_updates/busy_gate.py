"""Sperrt Software-Updates während Diagnose, Service oder Flash/Codierung."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.coding import CodingRun
from app.models.entities import DiagnosticSession
from app.models.service import ServiceRun
from app.models.subscriptions import CriticalOperationLock


def check_update_allowed(db: Session, *, workshop_id: str | None = None) -> dict:
    """Keine Updates während offener Diagnose, laufendem Service/Flash oder kritischen Ops."""
    blockers: list[dict] = []

    diag_q = select(DiagnosticSession).where(DiagnosticSession.status == "open")
    if workshop_id:
        diag_q = diag_q.where(DiagnosticSession.workshop_id == workshop_id)
    for s in db.scalars(diag_q.limit(20)).all():
        blockers.append(
            {
                "kind": "diagnosis",
                "ref": s.id,
                "detail_de": f"Offene Diagnosesitzung {s.id[:8]}…",
            }
        )

    svc_q = select(ServiceRun).where(ServiceRun.status == "running")
    if workshop_id:
        svc_q = svc_q.where(ServiceRun.workshop_id == workshop_id)
    for r in db.scalars(svc_q.limit(20)).all():
        blockers.append(
            {
                "kind": "service",
                "ref": r.id,
                "detail_de": f"Laufender Service {r.procedure_code} ({r.id[:8]}…)",
            }
        )

    code_q = select(CodingRun).where(CodingRun.status == "running")
    if workshop_id:
        code_q = code_q.where(CodingRun.workshop_id == workshop_id)
    for r in db.scalars(code_q.limit(20)).all():
        blockers.append(
            {
                "kind": "coding_flash",
                "ref": r.id,
                "detail_de": f"Laufende Codierung/Flash-Vorbereitung {r.operation_code} ({r.id[:8]}…)",
            }
        )

    crit_q = select(CriticalOperationLock).where(CriticalOperationLock.status == "running")
    if workshop_id:
        crit_q = crit_q.where(CriticalOperationLock.workshop_id == workshop_id)
    for o in db.scalars(crit_q.limit(20)).all():
        blockers.append(
            {
                "kind": "critical_op",
                "ref": o.id,
                "detail_de": f"Kritische Operation {o.operation_kind} läuft ({o.id[:8]}…)",
            }
        )

    allowed = len(blockers) == 0
    reason = None
    if not allowed:
        kinds = sorted({b["kind"] for b in blockers})
        reason = (
            "Update gesperrt: aktive Vorgänge ("
            + ", ".join(kinds)
            + "). Keine Installation während Diagnose, Service oder Flash."
        )
    return {
        "allowed": allowed,
        "reason_de": reason,
        "blockers": blockers,
    }
