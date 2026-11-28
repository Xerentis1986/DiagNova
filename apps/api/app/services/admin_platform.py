"""Phase 13 – Plattform-Admin-Dashboard (Nutzer, Abos, Datenversionen, Adapter, Audit)."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AuditLog, User, Workshop
from app.models.coding import CodingRun
from app.models.data_updates import UpdateChannel, UpdateRun
from app.models.diagnostic_data import DiagDatasetVersion
from app.models.commerce import BillingAccount, Invoice
from app.models.subscriptions import (
    DeviceBinding,
    PaymentWebhookEvent,
    Subscription,
    WorkshopInvitation,
)
from app.services.payments.mollie_provider import mollie_status
from app.services.subscriptions import PAYMENT_NOTE, subscription_to_dict

LEGAL_OPEN = [
    "DACH/AT Rechnungs-/Steueranforderungen: rechtliche Prüfung offen (BLK-LEGAL) – Steuerberater/Anwalt.",
    "Auftragsverarbeitung (AVV) / DSGVO: keine Konformität behauptet.",
    "Mollie Live-Charges erst nach Freigabe (mollie_live_charges_allowed) – BLK-PAY.",
    "Steuerregeln draft_needs_review – keine produktive Steuerfreigabe.",
    "Widerruf/AGB: Platzhalter – Betreiber muss Texte freigeben.",
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

    billing_accounts = db.query(BillingAccount).count()
    b2b = db.query(BillingAccount).filter(BillingAccount.customer_type == "b2b").count()
    b2c = db.query(BillingAccount).filter(BillingAccount.customer_type == "b2c").count()
    invoices_open = (
        db.query(Invoice).filter(Invoice.status.in_(["issued", "draft"])).count()
    )
    invoices_paid = db.query(Invoice).filter(Invoice.status == "paid").count()
    invoices_overdue = 0
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    for inv in db.query(Invoice).filter(Invoice.status == "issued").all():
        if inv.due_at and inv.due_at < now:
            invoices_overdue += 1

    # MRR/ARR Näherung aus aktiven Abos (Plan-Preise aus Stub-Katalog, Cent)
    from app.services.subscriptions import plans_public

    plan_price = {p["code"]: int(p.get("price_cents_demo") or 0) for p in plans_public()}
    mrr_cents = 0
    for s in db.query(Subscription).filter(Subscription.status.in_(["active"])).all():
        # Trial zählt nicht als Umsatz; nur active
        mrr_cents += plan_price.get(s.plan_code, 0)
    arr_cents = mrr_cents * 12

    mollie = mollie_status()
    payment_mode = (
        "mollie_test"
        if mollie.get("configured") and mollie.get("test_mode")
        else ("mollie_live_gated" if mollie.get("live_keys_present") else "mock_stub_plus_mollie_ready")
    )

    return {
        "payment_mode": payment_mode,
        "payment_note_de": PAYMENT_NOTE,
        "mollie": mollie,
        "stripe": {"removed": True, "replacement": "mollie"},
        "workshops_count": workshops,
        "users_count": users,
        "customers_count": billing_accounts,
        "customers_b2b": b2b,
        "customers_b2c": b2c,
        "active_subscriptions": active,
        "trial_subscriptions": db.query(Subscription)
        .filter(Subscription.status == "trialing")
        .count(),
        "past_due_subscriptions": past_due,
        "canceled_subscriptions": canceled,
        "mrr_cents": mrr_cents,
        "arr_cents": arr_cents,
        "invoices_open": invoices_open,
        "invoices_paid": invoices_paid,
        "invoices_overdue": invoices_overdue,
        "invitations_pending": inv_pending,
        "devices_bound": devices,
        "active_licenses": devices,
        "data_versions": data_versions,
        "adapter_summary": adapter_summary,
        "recent_audit": recent_audit,
        "recent_webhooks": recent_webhooks,
        "subscriptions": sub_outs,
        "legal_open_items_de": LEGAL_OPEN,
        "metrics_note_de": (
            "Kennzahlen aus DB. MRR/ARR aus Plan-Katalog-Näherung – "
            "keine Demo-Umsätze als Zahlungseingang. is_example_data-Rechnungen getrennt prüfen."
        ),
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


def list_billing_accounts(db: Session) -> list[dict]:
    rows = db.query(BillingAccount).order_by(BillingAccount.created_at.desc()).limit(100).all()
    return [
        {
            "id": a.id,
            "workshop_id": a.workshop_id,
            "customer_type": a.customer_type,
            "status": a.status,
            "company_name": a.company_name,
            "contact_name": a.contact_name,
            "display_name": a.company_name or a.contact_name or a.billing_email,
            "email": a.billing_email,
            "country": a.country,
            "vat_id": a.vat_id,
            "preferred_plan_code": a.preferred_plan_code,
            "is_example_data": bool(a.is_example_data),
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in rows
    ]


def list_invoices_admin(db: Session, *, limit: int = 50) -> list[dict]:
    limit = max(1, min(limit, 200))
    rows = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(limit).all()
    return [
        {
            "id": i.id,
            "workshop_id": i.workshop_id,
            "billing_account_id": getattr(i, "billing_account_id", None),
            "number": getattr(i, "number", None) or getattr(i, "invoice_number", None),
            "status": i.status,
            "gross_cents": getattr(i, "gross_cents", None),
            "net_cents": getattr(i, "net_cents", None),
            "currency": getattr(i, "currency", None) or "EUR",
            "is_example_data": bool(getattr(i, "is_example_data", False)),
            "created_at": i.created_at.isoformat() if i.created_at else None,
            "due_at": i.due_at.isoformat() if getattr(i, "due_at", None) else None,
        }
        for i in rows
    ]


def list_devices_admin(db: Session) -> list[dict]:
    rows = db.query(DeviceBinding).order_by(DeviceBinding.created_at.desc()).limit(100).all()
    return [
        {
            "id": d.id,
            "workshop_id": d.workshop_id,
            "device_name": d.device_name,
            "device_fingerprint": d.device_fingerprint[:16] + "…"
            if d.device_fingerprint and len(d.device_fingerprint) > 16
            else d.device_fingerprint,
            "platform": d.platform,
            "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
            "revoked_at": d.revoked_at.isoformat() if d.revoked_at else None,
            "active": d.revoked_at is None,
        }
        for d in rows
    ]


def build_operator_console(db: Session) -> dict:
    dash = build_admin_dashboard(db)
    return {
        **dash,
        "console": "operator",
        "base_path": "/operator",
        "customers": list_billing_accounts(db)[:50],
        "invoices": list_invoices_admin(db, limit=30),
        "devices": list_devices_admin(db),
        "users": list_admin_users(db),
        "site_settings": {
            "supplier_country": "AT",
            "currency": "EUR",
            "tax_review_status": "draft_needs_review",
            "at_legal_aligned_technical": True,
            "legal_note_de": (
                "Technisch AT-aligned. Rechtsfreigabe durch Betreiber/Steuerberater offen."
            ),
        },
        "adapter_test_paths_de": [
            "Connector GET /hardware/probe – CDP+/OBD-DIAG/Vgate Inventur",
            "POST /adapters/delphi-cdp/identify-sim – CDP+ Simulator Safe-Read",
            "POST /adapters/delphi-cdp/inventory-probe – FTDI/CDP Kandidaten",
            "POST /adapters/obd-diag/inventory-probe – USB/COM Inventur (kein ELM-Fake)",
            "POST /adapters/vgate-icar-pro-2s/connection-test – ELM327 AT (COM/BT)",
            "API-Proxy: GET /api/admin/hardware-probe (Betreiber)",
        ],
        "rbac_de": "Nur Plattform-Admin. Kunden-UI ohne Betreiber-Menü.",
    }
