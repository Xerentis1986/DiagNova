"""Phase 12 – Codier-/Flash-Gate-Läufe (kein Live-Schreiben/Flash)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class CodingRun(Base):
    """Dokumentierter Gate-/Identifikationslauf – nie als echte Flash-/Codierausführung freigegeben."""

    __tablename__ = "coding_runs"

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
    checks_json: Mapped[str] = mapped_column(Text, default="{}")
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    message_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    abort_reason_de: Mapped[str | None] = mapped_column(Text, nullable=True)
