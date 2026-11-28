"""Phase 14 – Software-/Connector-Updates (getrennt von Diagnosedaten-Updates)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class SoftwareComponent(Base):
    """Installierte Komponentenversion (api | web | connector)."""

    __tablename__ = "software_components"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # api|web|connector
    label_de: Mapped[str] = mapped_column(String(128))
    current_version: Mapped[str] = mapped_column(String(32))
    previous_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    channel_key: Mapped[str] = mapped_column(String(64), default="stable-fixture")
    health_status: Mapped[str] = mapped_column(String(32), default="ok")  # ok|degraded|failed
    last_healthcheck_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SoftwareUpdateChannel(Base):
    """Updatekanal – Auto-Install standardmäßig aus."""

    __tablename__ = "software_update_channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    channel_type: Mapped[str] = mapped_column(String(32), default="stable")  # stable|beta|production
    fetch_mode: Mapped[str] = mapped_column(String(16), default="fixture")  # fixture|https
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_install_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    require_signature: Mapped[bool] = mapped_column(Boolean, default=True)
    require_signing_cert: Mapped[bool] = mapped_column(Boolean, default=False)
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    packages: Mapped[list[SoftwareUpdatePackage]] = relationship(back_populates="channel")


class SoftwareUpdatePackage(Base):
    """Staging-Paket mit Checksum/Signatur und Release Notes."""

    __tablename__ = "software_update_packages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    channel_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("software_update_channels.id"), index=True
    )
    component: Mapped[str] = mapped_column(String(32), index=True)  # api|web|connector
    version: Mapped[str] = mapped_column(String(32), index=True)
    package_filename: Mapped[str] = mapped_column(String(255))
    content_sha256: Mapped[str] = mapped_column(String(64))
    signature_hex: Mapped[str | None] = mapped_column(String(128), nullable=True)
    signature_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    release_notes_de: Mapped[str] = mapped_column(Text, default="")
    migration_plan_json: Mapped[str] = mapped_column(Text, default="[]")
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(32), default="staged", index=True)
    # staged | rejected | awaiting_approval | approved | installed | rolled_back | failed
    error_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    channel: Mapped[SoftwareUpdateChannel] = relationship(back_populates="packages")
    runs: Mapped[list[SoftwareUpdateRun]] = relationship(back_populates="package")


class SoftwareUpdateRun(Base):
    """Installations-/Rollback-Lauf mit Healthcheck."""

    __tablename__ = "software_update_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    package_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("software_update_packages.id"), index=True
    )
    component: Mapped[str] = mapped_column(String(32), index=True)
    action: Mapped[str] = mapped_column(String(16), default="install")  # install|rollback|abort
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    # pending | blocked_busy | installing | healthcheck | succeeded | failed | rolled_back | aborted
    from_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    healthcheck_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    busy_reason_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    triggered_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    package: Mapped[SoftwareUpdatePackage] = relationship(back_populates="runs")


class SoftwareCompatibilityRule(Base):
    """Persistierte Kompatibilitätsregeln (Seed aus Matrix)."""

    __tablename__ = "software_compatibility_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    component: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[str] = mapped_column(String(32), index=True)
    requires_json: Mapped[str] = mapped_column(Text, default="{}")
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)


class SoftwareUpdateEvent(Base):
    """Ereignisprotokoll für Admin-Anzeige."""

    __tablename__ = "software_update_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    package_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    component: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    event: Mapped[str] = mapped_column(String(64), index=True)
    detail_de: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
