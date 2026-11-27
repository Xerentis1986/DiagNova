"""Phase 13 – Plattform-Admin-Dashboard (Nutzer, Abos, Datenversionen, Adapter, Audit)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AuditLog, User, Workshop
from app.models.coding import CodingRun
from app.models.data_updates import UpdateChannel, UpdateRun
from app.models.diagnostic_data import DiagDatasetVersion
from app.models.subscriptions import (
    DeviceBinding,
    PaymentWebhookEvent,
    Subscription,
    WorkshopInvitation,
)
from app.services.subscriptions import PAYMENT_NOTE, subscription_to_dict

LEGAL_OPEN = [
    "DACH Rechnungs-/Steueranforderungen: rechtliche Prüfung offen (BLK-LEGAL).",
    "Auftragsverarbeitung (AVV) / DSGVO: keine Konformität behauptet.",
    "Echter Payment-Provider erst nach ausdrücklicher Zustimmung (BLK-PAY).",
]


def require_platform_admin(user: User) -> None:
    if not getattr(user, "is_platform_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nur Plattform-Admin",
        )


def build_admin_dashboard(db: Session) -> dict:
    workshops = db.query(Workshop).count()
    users = db.query(User).count()
    active = db.query(Subscription).filter(Subscription.status.in_(["trialing", "active"])).count()
    past_due = db.query(Subscription).filter(Subscription.status == "past_due").count()
    canceled = db.query(Subscription).filter(Subscription.status.in_(["canceled", "expired"])).count()
    inv_pending = (
        db.query(WorkshopInvitation).filter(WorkshopInvitation.status == "pending").count()
    )
    devices = db.query(DeviceBinding).filter(DeviceBinding.revoked_at.is_(None)).count()

    versions = (
        db.query(DiagDatasetVersion)
        .order_by(DiagDatasetVersion.created_at.desc())
        .limit(10)
        .all()
    )
    data_versions = [
        {
            "id": v.id,
            "label": v.version_label,
            "status": v.status,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]

    channels = db.query(UpdateChannel).all()
    adapter_summary = [
        {
            "kind": "data_update_channel",
            "code": c.key,
            "enabled": bool(c.enabled),
            "last_run_at": c.last_run_at.isoformat() if c.last_run_at else None,
            "name": c.name,
        }
        for c in channels
    ]
    # Coding/J2534 Prep als Adapter-Hinweis (keine echte HW)
    adapter_summary.append(
        {
            "kind": "coding_interface",
            "code": "j2534_dpdu_prep",
            "enabled": False,
            "last_run_at": None,
            "note_de": "Nur dokumentierte Vorbereitung – keine Vendor-DLL (Phase 12).",
        }
    )

    coding_running = (
        db.query(CodingRun).filter(CodingRun.status == "running").count()
        if hasattr(CodingRun, "status")
        else 0
    )
    adapter_summary.append(
        {
            "kind": "coding_runs_running",
            "code": "coding",
            "enabled": coding_running > 0,
            "count": coding_running,
            "last_run_at": None,
        }
    )

    audit_rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(25).all()
    recent_audit = [
        {
            "id": a.id,
            "action": a.action,
            "resource": a.resource,
            "workshop_id": a.workshop_id,
            "user_id": a.user_id,
            "detail": a.detail,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in audit_rows
    ]

    hooks = (
        db.query(PaymentWebhookEvent)
        .order_by(PaymentWebhookEvent.created_at.desc())
        .limit(15)
        .all()
    )
    recent_webhooks = [
        {
            "id": h.id,
            "event_id": h.event_id,
            "event_type": h.event_type,
            "status": h.status,
            "signature_valid": h.signature_valid,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in hooks
    ]

    # Neueste Subscription pro Workshop für Übersicht
    latest_subs = (
        db.query(Subscription).order_by(Subscription.created_at.desc()).limit(30).all()
    )
    sub_outs = [subscription_to_dict(db, s) for s in latest_subs]

    update_runs = db.query(UpdateRun).count() if UpdateRun else 0
    _ = update_runs

    return {
        "payment_mode": "mock_stub",
        "payment_note_de": PAYMENT_NOTE,
        "workshops_count": workshops,
        "users_count": users,
        "active_subscriptions": active,
        "past_due_subscriptions": past_due,
        "canceled_subscriptions": canceled,
        "invitations_pending": inv_pending,
        "devices_bound": devices,
        "data_versions": data_versions,
        "adapter_summary": adapter_summary,
        "recent_audit": recent_audit,
        "recent_webhooks": recent_webhooks,
        "subscriptions": sub_outs,
        "legal_open_items_de": LEGAL_OPEN,
    }


def list_admin_users(db: Session) -> list[dict]:
    rows = db.query(User).order_by(User.email).all()
    out = []
    for u in rows:
        ws = db.get(Workshop, u.workshop_id) if u.workshop_id else None
        out.append(
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "workshop_id": u.workshop_id,
                "workshop_name": ws.name if ws else None,
                "is_active": u.is_active,
                "is_platform_admin": bool(getattr(u, "is_platform_admin", False)),
            }
        )
    return out
