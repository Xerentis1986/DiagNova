"""Phase 13 – Pydantic-Schemas für Abos, Einladungen, Admin, Payment-Stub."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class PlanOut(BaseModel):
    code: str
    name_de: str
    vehicle_scope: Literal["pkw", "lkw", "kombi"]
    billing_period: str
    price_cents_demo: int | None
    currency: str
    trial_days: int
    max_devices: int
    release_status: Literal["available", "planned"]
    description_de: str
    entitlements: list[str]
    payment_note_de: str = (
        "SIMULATION / STUB – keine echte Zahlung. Kein Payment-Provider ohne Zustimmung."
    )


class SubscriptionOut(BaseModel):
    id: str
    workshop_id: str
    plan_code: str
    plan_name_de: str | None = None
    status: str
    payment_provider: str
    external_ref: str | None = None
    trial_ends_at: datetime | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    canceled_at: datetime | None = None
    grace_until: datetime | None = None
    entitlements: list[str] = []
    is_example_data: bool = True
    license_active: bool
    allows_new_operations: bool
    has_running_critical_ops: bool = False
    message_de: str
    payment_note_de: str = (
        "SIMULATION / STUB – keine echte Abbuchung. Statusabgleich nur über Mock-Webhooks."
    )


class EntitlementCheckOut(BaseModel):
    feature: str
    allowed: bool
    subscription_status: str | None
    reason_de: str
    running_critical_ops: int = 0
    interrupt_forbidden: bool = False


class StartTrialRequest(BaseModel):
    plan_code: str = "pkw_trial"


class ActivatePlanRequest(BaseModel):
    """Stub-Aktivierung – keine echte Zahlung."""

    plan_code: str = Field(..., description="Nur verfügbare Tarife (nicht planned)")
    acknowledge_stub_payment: bool = False


class CancelSubscriptionRequest(BaseModel):
    at_period_end: bool = True
    reason_de: str | None = None


class DeviceBindRequest(BaseModel):
    device_name: str = Field(min_length=1, max_length=128)
    device_fingerprint: str = Field(min_length=8, max_length=128)
    platform: str = "windows"


class DeviceOut(BaseModel):
    id: str
    workshop_id: str
    device_name: str
    device_fingerprint: str
    platform: str
    last_seen_at: datetime | None
    revoked_at: datetime | None
    is_example_data: bool


class InvitationCreate(BaseModel):
    email: EmailStr
    role: Literal["admin", "technician", "viewer"] = "technician"


class InvitationOut(BaseModel):
    id: str
    workshop_id: str
    email: EmailStr
    role: str
    status: str
    expires_at: datetime
    accepted_at: datetime | None = None
    # Token nur für Admin-Ersteller sichtbar (Demo)
    token: str | None = None


class InvitationAccept(BaseModel):
    token: str = Field(min_length=16, max_length=64)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TenantRegisterRequest(BaseModel):
    workshop_name: str = Field(min_length=2, max_length=255)
    admin_email: EmailStr
    admin_full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    country: str = Field(default="AT", min_length=2, max_length=2)
    plan_code: str = "pkw_trial"
    acknowledge_demo: bool = False


class TenantRegisterOut(BaseModel):
    workshop_id: str
    user_id: str
    subscription_id: str
    message_de: str
    is_example_data: bool = True


class MockWebhookRequest(BaseModel):
    """Stub-Webhook-Payload. Signatur separat im Header."""

    event_id: str = Field(min_length=4, max_length=128)
    event_type: Literal[
        "invoice.paid",
        "invoice.payment_failed",
        "subscription.canceled",
        "subscription.renewed",
        "subscription.expired",
    ]
    subscription_id: str
    workshop_id: str | None = None
    occurred_at: datetime | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class MockWebhookOut(BaseModel):
    id: str
    event_id: str
    status: str
    signature_valid: bool
    message_de: str
    payment_note_de: str = "SIMULATION – keine echte Zahlung verarbeitet."
    subscription: SubscriptionOut | None = None


class CriticalOpStartRequest(BaseModel):
    operation_kind: str = Field(min_length=2, max_length=64)
    resource_ref: str = Field(min_length=1, max_length=128)
    message_de: str | None = None


class CriticalOpOut(BaseModel):
    id: str
    workshop_id: str
    operation_kind: str
    resource_ref: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    message_de: str | None


class AdminDashboardOut(BaseModel):
    payment_mode: str
    payment_note_de: str
    workshops_count: int
    users_count: int
    active_subscriptions: int
    past_due_subscriptions: int
    canceled_subscriptions: int
    invitations_pending: int
    devices_bound: int
    data_versions: list[dict[str, Any]]
    adapter_summary: list[dict[str, Any]]
    recent_audit: list[dict[str, Any]]
    recent_webhooks: list[dict[str, Any]]
    subscriptions: list[SubscriptionOut]
    legal_open_items_de: list[str]
    # Phase 21 – Betreiberkennzahlen (DB, keine Fake-Zahlungen)
    stripe: dict[str, Any] | None = None  # Phase 25: removed shim
    mollie: dict[str, Any] | None = None
    customers_count: int = 0
    customers_b2b: int = 0
    customers_b2c: int = 0
    trial_subscriptions: int = 0
    mrr_cents: int = 0
    arr_cents: int = 0
    invoices_open: int = 0
    invoices_paid: int = 0
    invoices_overdue: int = 0
    active_licenses: int = 0
    metrics_note_de: str | None = None


class AdminUserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    workshop_id: str | None
    workshop_name: str | None
    is_active: bool
    is_platform_admin: bool
