"""Phase 13 – Plattform-Admin-Dashboard (+ Phase 22 MFA)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.schemas.subscriptions import AdminDashboardOut, AdminUserOut, SubscriptionOut
from app.services import admin_platform, subscriptions as subsvc
from app.services.admin_platform import require_platform_admin
from app.services import mfa_totp
from app.models.subscriptions import Subscription

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardOut)
def admin_dashboard(user: CurrentUser, db: DbSession) -> AdminDashboardOut:
    require_platform_admin(user)
    data = admin_platform.build_admin_dashboard(db)
    return AdminDashboardOut(**data)


@router.get("/users", response_model=list[AdminUserOut])
def admin_users(user: CurrentUser, db: DbSession) -> list[AdminUserOut]:
    require_platform_admin(user)
    return [AdminUserOut(**u) for u in admin_platform.list_admin_users(db)]


@router.get("/subscriptions", response_model=list[SubscriptionOut])
def admin_subscriptions(user: CurrentUser, db: DbSession) -> list[SubscriptionOut]:
    require_platform_admin(user)
    rows = db.query(Subscription).order_by(Subscription.created_at.desc()).limit(100).all()
    return [SubscriptionOut(**subsvc.subscription_to_dict(db, s)) for s in rows]


@router.get("/audit")
def admin_audit(user: CurrentUser, db: DbSession, limit: int = 50) -> list[dict]:
    require_platform_admin(user)
    from app.models import AuditLog

    limit = max(1, min(limit, 200))
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": a.id,
            "action": a.action,
            "resource": a.resource,
            "workshop_id": a.workshop_id,
            "user_id": a.user_id,
            "detail": a.detail,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in rows
    ]


@router.get("/support")
def admin_support(user: CurrentUser, db: DbSession) -> dict:
    """Support-Übersicht: offene Einladungen, past_due, laufende kritische Ops."""
    require_platform_admin(user)
    from app.models.subscriptions import CriticalOperationLock, WorkshopInvitation

    return {
        "past_due": [
            subsvc.subscription_to_dict(db, s)
            for s in db.query(Subscription).filter(Subscription.status == "past_due").all()
        ],
        "pending_invitations": db.query(WorkshopInvitation)
        .filter(WorkshopInvitation.status == "pending")
        .count(),
        "running_critical_ops": [
            {
                "id": o.id,
                "workshop_id": o.workshop_id,
                "operation_kind": o.operation_kind,
                "resource_ref": o.resource_ref,
                "started_at": o.started_at.isoformat() if o.started_at else None,
            }
            for o in db.query(CriticalOperationLock)
            .filter(CriticalOperationLock.status == "running")
            .all()
        ],
        "payment_note_de": subsvc.PAYMENT_NOTE,
        "legal_open_items_de": admin_platform.LEGAL_OPEN,
    }


@router.get("/mfa/status")
def mfa_status(user: CurrentUser) -> dict:
    require_platform_admin(user)
    return mfa_totp.mfa_status(user)


@router.post("/mfa/setup")
def mfa_setup(user: CurrentUser, db: DbSession) -> dict:
    require_platform_admin(user)
    return mfa_totp.start_mfa_setup(db, user)


class MfaConfirmIn(BaseModel):
    code: str = Field(min_length=6, max_length=8)


@router.post("/mfa/confirm")
def mfa_confirm(body: MfaConfirmIn, user: CurrentUser, db: DbSession) -> dict:
    require_platform_admin(user)
    return mfa_totp.confirm_mfa(db, user, body.code)


@router.get("/console")
def admin_console(user: CurrentUser, db: DbSession) -> dict:
    """Aggregierte Betreiberkonsole: Kunden, Abos, Rechnungen, Geräte, Updates, Adapter-Hinweise."""
    require_platform_admin(user)
    return admin_platform.build_operator_console(db)


@router.get("/billing-accounts")
def admin_billing_accounts(user: CurrentUser, db: DbSession) -> list[dict]:
    require_platform_admin(user)
    return admin_platform.list_billing_accounts(db)


@router.get("/invoices")
def admin_invoices(user: CurrentUser, db: DbSession, limit: int = 50) -> list[dict]:
    require_platform_admin(user)
    return admin_platform.list_invoices_admin(db, limit=limit)


@router.get("/devices")
def admin_devices(user: CurrentUser, db: DbSession) -> list[dict]:
    require_platform_admin(user)
    return admin_platform.list_devices_admin(db)


@router.get("/hardware-probe")
async def admin_hardware_probe(user: CurrentUser) -> dict:
    """Nichtinvasive Adapter-Inventur über Connector-Bridge (Betreiber)."""
    require_platform_admin(user)
    from app.services import connector_bridge

    return await connector_bridge.hardware_probe()


@router.get("/operator-nav")
def operator_nav(user: CurrentUser) -> dict:
    """Welche Menüs/URLs der Betreiber nutzt (Frontend-Hilfsinfo)."""
    require_platform_admin(user)
    return {
        "base_path": "/operator",
        "alias": ["/admin"],
        "sections": [
            {"id": "overview", "path": "/operator", "label_de": "Übersicht"},
            {"id": "customers", "path": "/operator?tab=customers", "label_de": "Kunden B2B/B2C"},
            {"id": "subscriptions", "path": "/operator?tab=subscriptions", "label_de": "Abos"},
            {"id": "mollie", "path": "/operator?tab=mollie", "label_de": "Zahlung Mollie"},
            {"id": "invoices", "path": "/operator?tab=invoices", "label_de": "Rechnungen"},
            {"id": "licenses", "path": "/operator?tab=licenses", "label_de": "Lizenzen/Geräte"},
            {"id": "updates", "path": "/operator?tab=updates", "label_de": "Updates/Connector"},
            {"id": "adapters", "path": "/operator?tab=adapters", "label_de": "Adapter-Status"},
            {"id": "audit", "path": "/operator?tab=audit", "label_de": "Audit"},
            {"id": "mfa", "path": "/operator?tab=mfa", "label_de": "MFA / Sicherheit"},
            {"id": "settings", "path": "/operator?tab=settings", "label_de": "Seiteneinstellungen"},
        ],
        "rbac_de": "Nur is_platform_admin. Kundenportal zeigt keinen Betreiber-Link.",
        "mfa_de": "MFA für Plattform-Admin empfohlen (Setup unter MFA-Tab).",
        "no_live_charges": True,
    }

