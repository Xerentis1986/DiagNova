from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="technician")
    # Mandanten-ID – serverseitig aus Sitzung, nie vom Client gesetzt
    workshop_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workshops.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    theme_preference: Mapped[str] = mapped_column(String(16), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    brand_favorites: Mapped[list[UserBrandFavorite]] = relationship(back_populates="user")


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("workshop_id", "vin", name="uq_vehicles_workshop_vin"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workshops.id"), nullable=True, index=True
    )
    # Primärer Kunde (optional); weitere Zuordnungen über customer_vehicles
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=True, index=True
    )
    make: Mapped[str] = mapped_column(String(64), index=True)
    model: Mapped[str] = mapped_column(String(64))
    year: Mapped[int] = mapped_column(Integer)
    vin: Mapped[str] = mapped_column(String(17), index=True)
    license_plate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    series: Mapped[str | None] = mapped_column(String(64), nullable=True)
    odometer_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    catalog_brand_slug: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    catalog_model_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    catalog_variant_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sessions: Mapped[list[DiagnosticSession]] = relationship(back_populates="vehicle")


class UserBrandFavorite(Base):
    __tablename__ = "user_brand_favorites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    brand_slug: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="brand_favorites")


class UserRecentSelection(Base):
    __tablename__ = "user_recent_selections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    vehicle_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("vehicles.id"), nullable=True)
    brand_slug: Mapped[str] = mapped_column(String(64))
    brand_name: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(64))
    series: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"
    __table_args__ = (
        UniqueConstraint("workshop_id", "idempotency_key", name="uq_session_workshop_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    # Phase 09: Mandant denormalisiert für Filter; nie vom Client gesetzt
    workshop_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    work_order_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("work_orders.id"), nullable=True, index=True
    )
    # open | closed | aborted – Abbruch nicht als erfolgreiche Historie
    status: Mapped[str] = mapped_column(String(16), default="open")
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dtc_snapshot_json: Mapped[str] = mapped_column(Text, default="[]")
    freeze_frame_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    readiness_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    odometer_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adapter_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    protocol_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    abort_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Clientseitige Wiederholung → gleiche Sitzung zurück
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    vehicle: Mapped[Vehicle] = relationship(back_populates="sessions")
    reports: Mapped[list[DiagnosticReport]] = relationship(back_populates="session")
    ecu_results: Mapped[list] = relationship(
        "SessionEcuResult", back_populates="session", cascade="all, delete-orphan"
    )


class DiagnosticReport(Base):
    """Unveränderlicher Berichtssnapshot (Phase 10). Inhalt nach Create nicht mehr ändern."""

    __tablename__ = "diagnostic_reports"
    __table_args__ = (
        UniqueConstraint("workshop_id", "report_number", name="uq_diagnostic_reports_workshop_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("diagnostic_sessions.id"), index=True)
    workshop_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    vehicle_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    # z. B. DN-2026-000042 – pro Mandant eindeutig
    report_number: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    content_json: Mapped[str] = mapped_column(Text)
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")
    data_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Nur manuell; keine automatisch erfundene Reparaturdiagnose
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    frozen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[DiagnosticSession] = relationship(back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    workshop_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64))
    resource: Mapped[str] = mapped_column(String(128))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
