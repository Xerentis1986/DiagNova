"""Phase 13 – Abonnements, Einladungen, Gerätebindung, Payment-Stub-Events."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Subscription(Base):
    """Mandanten-Abo / Lizenzstatus. Zahlung nur Stub/Simulation."""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    plan_code: Mapped[str] = mapped_column(String(64), index=True)
    # trialing | active | past_due | canceled | expired | unpaid | incomplete
    status: Mapped[str] = mapped_column(String(32), default="incomplete", index=True)
    # mock | none – nie ein echter PSP ohne Zustimmung
    payment_provider: Mapped[str] = mapped_column(String(32), default="mock")
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Nach Ablauf: laufende sicherheitskritische Ops dürfen zu Ende laufen
    grace_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    entitlements_json: Mapped[str] = mapped_column(Text, default="[]")
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WorkshopInvitation(Base):
    """Einladung in einen Mandanten (Rollenbindung)."""

    __tablename__ = "workshop_invitations"
    __table_args__ = (
        UniqueConstraint("workshop_id", "email", name="uq_invitation_workshop_email"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    role: Mapped[str] = mapped_column(String(32), default="technician")
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    invited_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    # pending | accepted | revoked | expired
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeviceBinding(Base):
    """Gerätebindung an Mandanten-Lizenz (Connector/Workstation)."""

    __tablename__ = "device_bindings"
    __table_args__ = (
        UniqueConstraint("workshop_id", "device_fingerprint", name="uq_device_workshop_fp"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    subscription_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("subscriptions.id"), nullable=True, index=True
    )
    device_name: Mapped[str] = mapped_column(String(128))
    device_fingerprint: Mapped[str] = mapped_column(String(128))
    platform: Mapped[str] = mapped_column(String(64), default="windows")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PaymentWebhookEvent(Base):
    """Idempotente Stub-Webhooks (signiert). Keine echten Abbuchungen."""

    __tablename__ = "payment_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_payment_webhook_event"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider: Mapped[str] = mapped_column(String(32), default="mock")
    event_id: Mapped[str] = mapped_column(String(128), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    # received | processed | rejected | duplicate
    status: Mapped[str] = mapped_column(String(32), default="received", index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    subscription_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    workshop_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CriticalOperationLock(Base):
    """Laufende sicherheitskritische Operation – Abo-Ablauf darf sie nicht abrupt beenden."""

    __tablename__ = "critical_operation_locks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    operation_kind: Mapped[str] = mapped_column(String(64))  # coding | service | clear_dtc | …
    resource_ref: Mapped[str] = mapped_column(String(128))
    # running | completed | aborted
    status: Mapped[str] = mapped_column(String(32), default="running", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    message_de: Mapped[str | None] = mapped_column(Text, nullable=True)


class TenantRegistration(Base):
    """Selbstregistrierung eines Mandanten (Werkstatt) – Demo/Simulation."""

    __tablename__ = "tenant_registrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    admin_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    plan_code: Mapped[str] = mapped_column(String(64), default="pkw_trial")
    # Demo-Kennzeichnung
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
