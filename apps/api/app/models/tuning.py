"""Phase 18 – Tuning-Architektur: Baselines, Genehmigungen, Workflow-Läufe.

Kein Live-Flash, keine Kennfelder. Nur Metadaten und simulierte Gates.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class TuningSoftwareBaseline(Base):
    """Autorisierter Originalsoftwarestand – nur Metadaten, keine Map/Binary."""

    __tablename__ = "tuning_software_baselines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    code: Mapped[str] = mapped_column(String(128), index=True)
    ecu_role: Mapped[str] = mapped_column(String(64), default="engine")
    software_version: Mapped[str] = mapped_column(String(64))
    part_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum_ref: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_de: Mapped[str] = mapped_column(Text, default="")
    authorization_status: Mapped[str] = mapped_column(
        String(32), default="draft"
    )  # draft|documented|unauthorized_demo|revoked
    compatible_notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TuningApprovalDocument(Base):
    """Genehmigungsnachweis – Metadaten/Verweis, keine Rechtsberatung."""

    __tablename__ = "tuning_approval_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    baseline_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tuning_software_baselines.id"), nullable=True, index=True
    )
    vehicle_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=True, index=True)
    doc_type: Mapped[str] = mapped_column(
        String(64), default="workshop_ack"
    )  # type_approval|workshop_ack|technical_review|other
    title_de: Mapped[str] = mapped_column(String(256))
    reference_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issuer_de: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="recorded"
    )  # recorded|verified_sim|rejected|expired
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TuningVersionHistoryEntry(Base):
    """Versionshistorie-Eintrag (werkstattseitig / simuliert)."""

    __tablename__ = "tuning_version_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    vehicle_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=True, index=True)
    baseline_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tuning_software_baselines.id"), nullable=True, index=True
    )
    ecu_role: Mapped[str] = mapped_column(String(64), default="engine")
    software_version: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(
        String(32), default="recorded"
    )  # recorded|baseline_linked|compat_checked|approval_linked
    message_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TuningWorkflowRun(Base):
    """Simulierter Gate-/Workflow-Lauf – nie als echte Tuning-Ausführung freigegeben."""

    __tablename__ = "tuning_workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    vehicle_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    operation_code: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending|blocked|running|completed|aborted|failed
    scenario: Mapped[str | None] = mapped_column(String(32), nullable=True)
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")
    prerequisites_json: Mapped[str] = mapped_column(Text, default="[]")
    gates_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    message_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    abort_reason_de: Mapped[str | None] = mapped_column(Text, nullable=True)
