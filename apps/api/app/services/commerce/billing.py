"""B2B/B2C Konten, Rechnungen, Kündigung – Simulation, kein echter PSP."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.data.subscription_plans import PLAN_CATALOG
from app.models.commerce import BillingAccount, ConsentRecord, Invoice
from app.models.subscriptions import DeviceBinding, Subscription
from app.services.audit import write_audit
from app.services.commerce import vies as vies_svc
from app.services.commerce.tax_engine import resolve_tax
from app.services import subscriptions as subsvc

PAYMENT_NOTE = (
    "SIMULATION – keine echte Zahlung. PSP erst nach ausdrücklicher Zustimmung (BLK-PAY). "
    "Steuerregeln draft_needs_review."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _plan(code: str) -> dict[str, Any]:
    for p in PLAN_CATALOG:
        if p["code"] == code:
            return p
    raise HTTPException(status_code=400, detail=f"Unbekannter Tarif: {code}")


def account_to_dict(acc: BillingAccount) -> dict[str, Any]:
    return {
        "id": acc.id,
        "workshop_id": acc.workshop_id,
        "customer_type": acc.customer_type,
        "status": acc.status,
        "contact_name": acc.contact_name,
        "billing_email": acc.billing_email,
        "company_name": acc.company_name,
        "legal_form": acc.legal_form,
        "vat_id": acc.vat_id,
        "vat_status": acc.vat_status,
        "tax_classification": acc.tax_classification,
        "street": acc.street,
        "postal_code": acc.postal_code,
        "city": acc.city,
        "country": acc.country,
        "location_evidence": acc.location_evidence,
        "payment_method": acc.payment_method,
        "preferred_plan_code": acc.preferred_plan_code,
        "license_seats": acc.license_seats,
        "terms_accepted_at": acc.terms_accepted_at.isoformat() if acc.terms_accepted_at else None,
        "privacy_accepted_at": acc.privacy_accepted_at.isoformat() if acc.privacy_accepted_at else None,
        "withdrawal_info_ack_at": (
            acc.withdrawal_info_ack_at.isoformat() if acc.withdrawal_info_ack_at else None
        ),
        "marketing_opt_in": acc.marketing_opt_in,
        "is_example_data": acc.is_example_data,
        "payment_note_de": PAYMENT_NOTE,
        "created_at": acc.created_at.isoformat() if acc.created_at else None,
    }


def create_account(
    db: Session,
    *,
    workshop_id: str,
    user_id: str,
    customer_type: str,
    contact_name: str,
    billing_email: str,
    country: str = "AT",
    company_name: str | None = None,
    legal_form: str | None = None,
    vat_id: str | None = None,
    street: str | None = None,
    postal_code: str | None = None,
    city: str | None = None,
    tax_classification: str | None = None,
    payment_method: str = "mock",
    preferred_plan_code: str | None = None,
    license_seats: int = 1,
    accept_terms: bool = False,
    accept_privacy: bool = False,
    ack_withdrawal: bool = False,
    force_vies_stub: bool = True,
) -> BillingAccount:
    ctype = customer_type.lower()
    if ctype not in {"b2b", "b2c"}:
        raise HTTPException(status_code=400, detail="customer_type muss b2b oder b2c sein")
    if not contact_name.strip() or not billing_email.strip():
        raise HTTPException(status_code=400, detail="contact_name und billing_email Pflicht")
    if ctype == "b2b":
        if not (company_name or "").strip():
            raise HTTPException(status_code=400, detail="B2B: Firmenname Pflicht")
        if not vat_id:
            raise HTTPException(status_code=400, detail="B2B: UID/USt-IdNr. Pflicht")
    else:
        if vat_id:
            raise HTTPException(status_code=400, detail="B2C: keine UID erlaubt")
        company_name = None
        legal_form = None
        tax_classification = tax_classification or "private_consumer"

    if not accept_terms or not accept_privacy:
        raise HTTPException(status_code=400, detail="AGB und Datenschutz müssen akzeptiert werden")
    if ctype == "b2c" and not ack_withdrawal:
        raise HTTPException(status_code=400, detail="B2C: Widerrufsinfo muss bestätigt werden")

    vat_status = "not_applicable"
    if ctype == "b2b" and vat_id:
        check = vies_svc.check_vat(
            db,
            vat_id=vat_id,
            workshop_id=workshop_id,
            force_stub=force_vies_stub,
        )
        vat_status = "valid" if check["valid"] else check["result"]
        vat_id = check.get("vat_id") or vat_id

    now = _now()
    acc = BillingAccount(
        workshop_id=workshop_id,
        customer_type=ctype,
        status="active",
        contact_name=contact_name.strip(),
        billing_email=billing_email.strip().lower(),
        company_name=company_name.strip() if company_name else None,
        legal_form=legal_form,
        vat_id=vat_id,
        vat_status=vat_status,
        tax_classification=tax_classification or ("business" if ctype == "b2b" else "private_consumer"),
        street=street,
        postal_code=postal_code,
        city=city,
        country=country.upper(),
        location_evidence="billing_address" if street else "self_declared",
        payment_method=payment_method,
        preferred_plan_code=preferred_plan_code,
        license_seats=max(1, license_seats),
        terms_accepted_at=now,
        privacy_accepted_at=now,
        withdrawal_info_ack_at=now if ctype == "b2c" else None,
        is_example_data=True,
    )
    db.add(acc)
    db.flush()

    consent_items = [("terms", "phase21-v1"), ("privacy", "phase21-v1")]
    if ctype == "b2c":
        consent_items.append(("withdrawal", "phase21-v1"))
    for consent_type, version in consent_items:
        text = f"{consent_type}:{version}"
        db.add(
            ConsentRecord(
                billing_account_id=acc.id,
                workshop_id=workshop_id,
                consent_type=consent_type,
                version_label=version,
                text_hash=hashlib.sha256(text.encode()).hexdigest(),
                accepted=True,
            )
        )

    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="commerce.account_created",
        resource=f"billing_account:{acc.id}",
        detail=f"customer_type={ctype};country={acc.country}",
    )
    db.refresh(acc)
    return acc


def list_accounts(db: Session, workshop_id: str) -> list[BillingAccount]:
    return (
        db.query(BillingAccount)
        .filter(BillingAccount.workshop_id == workshop_id)
        .order_by(BillingAccount.created_at.desc())
        .all()
    )


def get_account(db: Session, workshop_id: str, account_id: str) -> BillingAccount:
    acc = db.get(BillingAccount, account_id)
    if acc is None or acc.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="Billing-Konto nicht gefunden")
    return acc


def subscribe_and_invoice(
    db: Session,
    *,
    workshop_id: str,
    user_id: str,
    account_id: str,
    plan_code: str,
    force_vies_stub: bool = True,
) -> dict[str, Any]:
    acc = get_account(db, workshop_id, account_id)
    plan = _plan(plan_code)
    if plan.get("release_status") != "available":
        raise HTTPException(status_code=400, detail="Tarif nicht buchbar")

    net = int(plan.get("price_cents_demo") or 0)
    vat_valid = None
    if acc.customer_type == "b2b" and acc.vat_id:
        check = vies_svc.check_vat(
            db,
            vat_id=acc.vat_id,
            billing_account_id=acc.id,
            workshop_id=workshop_id,
            force_stub=force_vies_stub,
        )
        vat_valid = check["valid"]
        acc.vat_status = "valid" if vat_valid else check["result"]

    tax = resolve_tax(
        customer_type=acc.customer_type,
        customer_country=acc.country,
        vat_id=acc.vat_id,
        vat_valid=vat_valid,
        net_cents=net,
    )

    # Stub-Abo anlegen / aktualisieren
    sub = (
        db.query(Subscription)
        .filter(Subscription.workshop_id == workshop_id, Subscription.plan_code == plan_code)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    now = _now()
    if sub is None:
        sub = Subscription(
            workshop_id=workshop_id,
            plan_code=plan_code,
            status="active",
            payment_provider="mock",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            entitlements_json=json.dumps(plan.get("entitlements") or []),
            is_example_data=True,
            notes="Phase 21 Commerce-Stub",
        )
        db.add(sub)
        db.flush()
    else:
        sub.status = "active"
        sub.cancel_at_period_end = False
        sub.canceled_at = None
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=30)
        sub.entitlements_json = json.dumps(plan.get("entitlements") or [])

    acc.preferred_plan_code = plan_code
    seats = min(acc.license_seats, int(plan.get("max_devices") or acc.license_seats))

    number = f"DN-21-{now.strftime('%Y%m')}-{acc.id[:8].upper()}"
    inv = Invoice(
        workshop_id=workshop_id,
        billing_account_id=acc.id,
        subscription_id=sub.id,
        doc_type="invoice",
        number=number,
        status="issued",
        currency="EUR",
        net_cents=tax["net_cents"],
        vat_cents=tax["vat_cents"],
        gross_cents=tax["gross_cents"],
        vat_rate_bp=tax["vat_rate_bp"],
        tax_scenario=tax["scenario"],
        reverse_charge=tax["reverse_charge"],
        oss_applicable=tax["oss_applicable"],
        line_items_json=json.dumps(
            [
                {
                    "sku": plan_code,
                    "name_de": plan["name_de"],
                    "qty": 1,
                    "net_cents": net,
                    "seats": seats,
                }
            ],
            ensure_ascii=False,
        ),
        buyer_snapshot_json=json.dumps(account_to_dict(acc), ensure_ascii=False, default=str),
        tax_snapshot_json=json.dumps(tax, ensure_ascii=False),
        notes_de=PAYMENT_NOTE,
        issued_at=now,
        due_at=now + timedelta(days=14),
        retention_until=now + timedelta(days=365 * 7),
        is_example_data=True,
    )
    db.add(inv)

    # Bestellbestätigung Consent
    db.add(
        ConsentRecord(
            billing_account_id=acc.id,
            workshop_id=workshop_id,
            consent_type="order_confirmation",
            version_label="phase21-v1",
            text_hash=hashlib.sha256(f"order:{number}".encode()).hexdigest(),
            accepted=True,
        )
    )
    if acc.customer_type == "b2c":
        db.add(
            ConsentRecord(
                billing_account_id=acc.id,
                workshop_id=workshop_id,
                consent_type="auto_renewal",
                version_label="phase21-v1",
                text_hash=hashlib.sha256(b"auto_renewal:phase21-v1").hexdigest(),
                accepted=True,
            )
        )

    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="commerce.subscribe_invoiced",
        resource=f"invoice:{inv.id}",
        detail=f"plan={plan_code};scenario={tax['scenario']}",
    )
    db.refresh(inv)
    db.refresh(sub)

    return {
        "account": account_to_dict(acc),
        "subscription": subsvc.subscription_to_dict(db, sub),
        "invoice": invoice_to_dict(inv),
        "tax": tax,
        "payment_note_de": PAYMENT_NOTE,
        "order_confirmation_de": (
            f"Bestellung {number} bestätigt (Simulation). "
            f"{'Brutto' if tax['display_gross'] else 'Netto'}-Betrag "
            f"{tax['gross_cents'] if tax['display_gross'] else tax['net_cents']} Cent EUR."
        ),
    }


def invoice_to_dict(inv: Invoice) -> dict[str, Any]:
    return {
        "id": inv.id,
        "workshop_id": inv.workshop_id,
        "billing_account_id": inv.billing_account_id,
        "subscription_id": inv.subscription_id,
        "doc_type": inv.doc_type,
        "number": inv.number,
        "status": inv.status,
        "currency": inv.currency,
        "net_cents": inv.net_cents,
        "vat_cents": inv.vat_cents,
        "gross_cents": inv.gross_cents,
        "vat_rate_bp": inv.vat_rate_bp,
        "tax_scenario": inv.tax_scenario,
        "reverse_charge": inv.reverse_charge,
        "oss_applicable": inv.oss_applicable,
        "line_items": json.loads(inv.line_items_json or "[]"),
        "notes_de": inv.notes_de,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "due_at": inv.due_at.isoformat() if inv.due_at else None,
        "retention_until": inv.retention_until.isoformat() if inv.retention_until else None,
        "download": {
            "format": "json",
            "path": f"/api/commerce/invoices/{inv.id}/download",
            "note_de": "JSON-Download (Simulation). PDF später.",
        },
        "is_example_data": inv.is_example_data,
    }


def list_invoices(db: Session, workshop_id: str, account_id: str | None = None) -> list[Invoice]:
    q = db.query(Invoice).filter(Invoice.workshop_id == workshop_id)
    if account_id:
        q = q.filter(Invoice.billing_account_id == account_id)
    return q.order_by(Invoice.created_at.desc()).all()


def get_invoice(db: Session, workshop_id: str, invoice_id: str) -> Invoice:
    inv = db.get(Invoice, invoice_id)
    if inv is None or inv.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="Rechnung nicht gefunden")
    return inv


def create_credit_note(
    db: Session, *, workshop_id: str, user_id: str, invoice_id: str, reason_de: str
) -> Invoice:
    src = get_invoice(db, workshop_id, invoice_id)
    if src.doc_type != "invoice":
        raise HTTPException(status_code=400, detail="Nur Rechnungen können gutgeschrieben werden")
    now = _now()
    cn = Invoice(
        workshop_id=workshop_id,
        billing_account_id=src.billing_account_id,
        subscription_id=src.subscription_id,
        doc_type="credit_note",
        number=f"GS-{src.number}",
        status="issued",
        currency=src.currency,
        net_cents=-abs(src.net_cents),
        vat_cents=-abs(src.vat_cents),
        gross_cents=-abs(src.gross_cents),
        vat_rate_bp=src.vat_rate_bp,
        tax_scenario=src.tax_scenario,
        reverse_charge=src.reverse_charge,
        oss_applicable=src.oss_applicable,
        line_items_json=src.line_items_json,
        buyer_snapshot_json=src.buyer_snapshot_json,
        tax_snapshot_json=src.tax_snapshot_json,
        notes_de=reason_de or "Gutschrift (Simulation)",
        issued_at=now,
        retention_until=now + timedelta(days=365 * 7),
        is_example_data=True,
    )
    src.status = "credited"
    db.add(cn)
    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="commerce.credit_note",
        resource=f"invoice:{cn.id}",
        detail=f"source={src.id}",
    )
    db.refresh(cn)
    return cn


def cancel_subscription(
    db: Session,
    *,
    workshop_id: str,
    user_id: str,
    account_id: str,
    at_period_end: bool = True,
) -> dict[str, Any]:
    acc = get_account(db, workshop_id, account_id)
    if not acc.preferred_plan_code:
        raise HTTPException(status_code=400, detail="Kein aktives Tarif auf dem Konto")
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.workshop_id == workshop_id,
            Subscription.plan_code == acc.preferred_plan_code,
        )
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if sub is None:
        raise HTTPException(status_code=404, detail="Abo nicht gefunden")
    now = _now()
    if at_period_end:
        sub.cancel_at_period_end = True
        message = "Kündigung zum Periodenende vorgemerkt (Simulation)."
    else:
        sub.status = "canceled"
        sub.canceled_at = now
        sub.cancel_at_period_end = False
        message = "Abo sofort gekündigt (Simulation)."
    write_audit(
        db,
        user_id=user_id,
        workshop_id=workshop_id,
        action="commerce.cancel",
        resource=f"subscription:{sub.id}",
        detail=f"at_period_end={at_period_end}",
    )
    db.refresh(sub)
    return {
        "message_de": message,
        "subscription": subsvc.subscription_to_dict(db, sub),
        "account": account_to_dict(acc),
        "consumer_note_de": (
            "B2C: Kündigungsinformationen und Widerruf rechtlich vor Launch prüfen."
            if acc.customer_type == "b2c"
            else None
        ),
        "payment_note_de": PAYMENT_NOTE,
    }


def list_licenses(db: Session, workshop_id: str, account_id: str) -> dict[str, Any]:
    acc = get_account(db, workshop_id, account_id)
    devices = (
        db.query(DeviceBinding)
        .filter(DeviceBinding.workshop_id == workshop_id, DeviceBinding.revoked_at.is_(None))
        .all()
    )
    return {
        "account_id": acc.id,
        "license_seats": acc.license_seats,
        "devices_bound": len(devices),
        "devices": [
            {
                "id": d.id,
                "device_name": d.device_name,
                "platform": d.platform,
                "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
            }
            for d in devices
        ],
        "message_de": "Lizenzverwaltung (Simulation) – Gerätebindung aus Phase 13.",
    }
