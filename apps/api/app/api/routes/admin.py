"""Phase 13 – Plattform-Admin-Dashboard."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.subscriptions import AdminDashboardOut, AdminUserOut, SubscriptionOut
from app.services import admin_platform, subscriptions as subsvc
from app.services.admin_platform import require_platform_admin
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
