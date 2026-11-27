"""Phase 07 – automatische Diagnosedaten-Updates (Kanäle, Läufe, Changelog)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UpdateChannel(Base):
    """Freigegebene Update-Quelle. Keine unbekannten Auto-Downloads."""

    __tablename__ = "update_channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    # https | fixture (nur Demo/Tests – keine erfundenen kommerziellen Feeds)
    fetch_mode: Mapped[str] = mapped_column(String(16), default="https")
    url: Mapped[str] = mapped_column(String(1024))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # Rechteprüfung durch Admin erforderlich vor enabled=True
    rights_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    interval_hours: Mapped[int] = mapped_column(Integer, default=24)
    expected_license: Mapped[str] = mapped_column(String(128))
    source_key: Mapped[str] = mapped_column(String(64))
    # dtc_descriptive | structural | procedures | addresses | mixed
    content_kind: Mapped[str] = mapped_column(String(32), default="structural")
    auto_activate_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    max_bytes: Mapped[int] = mapped_column(Integer, default=2_000_000)
    require_signature: Mapped[bool] = mapped_column(Boolean, default=False)
    # HMAC-SHA256 Shared Secret Key-ID (kein Secret in DB – nur Referenz); oder "none"
    signature_key_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    runs: Mapped[list[UpdateRun]] = relationship(back_populates="channel")


class UpdateJobLock(Base):
    """Globale Sperre gegen parallele Update-Jobs (eine Zeile)."""

    __tablename__ = "update_job_locks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default="global")
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    locked_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UpdateRun(Base):
    """Ein Update-Lauf (Scheduler oder manuell)."""

    __tablename__ = "update_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    channel_id: Mapped[str] = mapped_column(String(36), ForeignKey("update_channels.id"), index=True)
    trigger: Mapped[str] = mapped_column(String(16), default="manual")  # scheduler | manual
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    # pending | fetching | staging | awaiting_approval | published | skipped | failed | rolled_back
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    license_changed: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_license: Mapped[str | None] = mapped_column(String(128), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    staging_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    import_batch_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dataset_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("diag_dataset_versions.id"), nullable=True
    )
    previous_dataset_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    channel: Mapped[UpdateChannel] = relationship(back_populates="runs")
    changelog_entries: Mapped[list[UpdateChangelog]] = relationship(back_populates="run")


class UpdateChangelog(Base):
    """Änderungsprotokoll für Admin-Dashboard."""

    __tablename__ = "update_changelogs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("update_runs.id"), index=True)
    channel_key: Mapped[str] = mapped_column(String(64), index=True)
    event: Mapped[str] = mapped_column(String(64))
    # fetched | skipped_same | staged | auto_published | awaiting_approval |
    # approved | rejected | rolled_back | failed | license_changed
    detail_de: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped[UpdateRun] = relationship(back_populates="changelog_entries")
