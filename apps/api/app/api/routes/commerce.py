"""Phase 21 – B2B/B2C Commerce API (Simulation, kein echter PSP)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, DbSession
from app.data.tax_rules_at import CONSUMER_DISCLAIMERS_DE, TAX_RULE_SEED
from app.services.commerce import billing as billing_svc
from app.services.commerce import vies as vies_svc
from app.services.commerce.tax_engine import resolve_tax
from app.services.tenant import require_admin_role, require_workshop_id

router = APIRouter(prefix="/commerce", tags=["commerce-phase21"])


class AccountCreateIn(BaseModel):
    customer_type: str = Field(pattern="^(b2b|b2c)$")
    contact_name: str
    billing_email: str
    country: str = "AT"
    company_name: str | None = None
    legal_form: str | None = None
    vat_id: str | None = None
    street: str | None = None
    postal_code: str | None = None
    city: str | None = None
    tax_classification: str | None = None
    payment_method: str = "mock"
    preferred_plan_code: str | None = None
    license_seats: int = 1
    accept_terms: bool = False
    accept_privacy: bool = False
    ack_withdrawal: bool = False


class VatCheckIn(BaseModel):
    vat_id: str
    billing_account_id: str | None = None
    force_stub: bool = True


class TaxPreviewIn(BaseModel):
    customer_type: str
    customer_country: str
    net_cents: int
    vat_id: str | None = None
    vat_valid: bool | None = None


class SubscribeIn(BaseModel):
    plan_code: str
    force_vies_stub: bool = True


class CancelIn(BaseModel):
    at_period_end: bool = True


class CreditNoteIn(BaseModel):
    reason_de: str = "Gutschrift (Simulation)"


@router.get("/overview")
def overview(_user: CurrentUser) -> dict[str, Any]:
    from app.services.payments.stripe_provider import stripe_status

    stripe = stripe_status()
    return {
        "phase": 21,
        "live_payments": False,
        "stripe": {
            "configured": stripe.get("configured"),
            "test_mode": stripe.get("test_mode"),
            "live_charges_allowed": stripe.get("live_charges_allowed"),
            "status_path": "/api/billing/stripe/status",
            "note_de": stripe.get("message_de"),
        },
        "payment_note_de": billing_svc.PAYMENT_NOTE,
        "supports": ["b2b", "b2c"],
        "features": [
            "billing_accounts",
            "vies_check",
            "tax_preview",
            "subscribe_invoice",
            "invoice_download_json",
            "credit_notes",
            "cancel",
            "license_list",
            "stripe_checkout_when_keys_set",
        ],
        "missing_de": [
            "Rechnung PDF (nur JSON-Download)",
            "E-Mail-Versand Rechnungen (nur dry_run ohne SMTP)",
            "Produktive Steuerfreigabe (draft_needs_review)",
            "Stripe Live-Charges (gesperrt ohne Freigabe)",
        ],
        "consumer_disclaimers_de": CONSUMER_DISCLAIMERS_DE,
        "tax_review_status": "draft_needs_review",
        "message_de": (
            "Kaufmännisches Backend B2B/B2C. Commerce-Abo erzeugt Stub-Rechnung. "
            "Stripe-Testmodus-Code vorhanden – ohne Keys kein Checkout-Erfolg. "
            "Steuerkonfiguration vor Prod fachlich prüfen."
        ),
    }


@router.get("/tax/rules")
def tax_rules(_user: CurrentUser) -> dict[str, Any]:
    return {
        "review_status": "draft_needs_review",
        "rules": TAX_RULE_SEED,
        "message_de": "Seed-Regeln – keine produktive Steuerfreigabe.",
    }


@router.post("/tax/preview")
def tax_preview(body: TaxPreviewIn, _user: CurrentUser) -> dict[str, Any]:
    return resolve_tax(
        customer_type=body.customer_type,
        customer_country=body.customer_country,
        vat_id=body.vat_id,
        vat_valid=body.vat_valid,
        net_cents=body.net_cents,
    )


@router.post("/vat/check")
def vat_check(body: VatCheckIn, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    wid = require_workshop_id(user)
    return vies_svc.check_vat(
        db,
        vat_id=body.vat_id,
        billing_account_id=body.billing_account_id,
        workshop_id=wid,
        force_stub=body.force_stub,
    )


@router.post("/accounts")
def create_account(body: AccountCreateIn, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    require_admin_role(user)
    wid = require_workshop_id(user)
    acc = billing_svc.create_account(
        db,
        workshop_id=wid,
        user_id=user.id,
        **body.model_dump(),
    )
    return billing_svc.account_to_dict(acc)


@router.get("/accounts")
def list_accounts(user: CurrentUser, db: DbSession) -> dict[str, Any]:
    wid = require_workshop_id(user)
    items = [billing_svc.account_to_dict(a) for a in billing_svc.list_accounts(db, wid)]
    return {"count": len(items), "accounts": items}


@router.get("/accounts/{account_id}")
def get_account(account_id: str, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    wid = require_workshop_id(user)
    return billing_svc.account_to_dict(billing_svc.get_account(db, wid, account_id))


@router.get("/accounts/{account_id}/contract")
def contract_info(account_id: str, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    wid = require_workshop_id(user)
    acc = billing_svc.get_account(db, wid, account_id)
    return {
        "account": billing_svc.account_to_dict(acc),
        "contract_de": {
            "customer_type": acc.customer_type,
            "plan": acc.preferred_plan_code,
            "seats": acc.license_seats,
            "auto_renewal": True,
            "payment_method": acc.payment_method,
            "notes_de": (
                "Vertragsinformationen (Simulation). Rechtliche Texte vor Veröffentlichung prüfen."
            ),
        },
        "disclaimers_de": CONSUMER_DISCLAIMERS_DE if acc.customer_type == "b2c" else {},
    }


@router.get("/accounts/{account_id}/licenses")
def licenses(account_id: str, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    wid = require_workshop_id(user)
    return billing_svc.list_licenses(db, wid, account_id)


@router.post("/accounts/{account_id}/subscribe")
def subscribe(account_id: str, body: SubscribeIn, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    require_admin_role(user)
    wid = require_workshop_id(user)
    return billing_svc.subscribe_and_invoice(
        db,
        workshop_id=wid,
        user_id=user.id,
        account_id=account_id,
        plan_code=body.plan_code,
        force_vies_stub=body.force_vies_stub,
    )


@router.post("/accounts/{account_id}/cancel")
def cancel(account_id: str, body: CancelIn, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    require_admin_role(user)
    wid = require_workshop_id(user)
    return billing_svc.cancel_subscription(
        db,
        workshop_id=wid,
        user_id=user.id,
        account_id=account_id,
        at_period_end=body.at_period_end,
    )


@router.get("/invoices")
def invoices(
    user: CurrentUser,
    db: DbSession,
    account_id: str | None = Query(default=None),
) -> dict[str, Any]:
    wid = require_workshop_id(user)
    items = [billing_svc.invoice_to_dict(i) for i in billing_svc.list_invoices(db, wid, account_id)]
    return {"count": len(items), "invoices": items}


@router.get("/invoices/{invoice_id}")
def invoice_detail(invoice_id: str, user: CurrentUser, db: DbSession) -> dict[str, Any]:
    wid = require_workshop_id(user)
    return billing_svc.invoice_to_dict(billing_svc.get_invoice(db, wid, invoice_id))


@router.get("/invoices/{invoice_id}/download")
def invoice_download(invoice_id: str, user: CurrentUser, db: DbSession) -> JSONResponse:
    wid = require_workshop_id(user)
    inv = billing_svc.get_invoice(db, wid, invoice_id)
    payload = billing_svc.invoice_to_dict(inv)
    payload["buyer"] = json.loads(inv.buyer_snapshot_json or "{}")
    payload["tax"] = json.loads(inv.tax_snapshot_json or "{}")
    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="{inv.number}.json"',
            "X-DiagNova-Doc-Type": inv.doc_type,
        },
    )


@router.post("/invoices/{invoice_id}/credit-note")
def credit_note(
    invoice_id: str, body: CreditNoteIn, user: CurrentUser, db: DbSession
) -> dict[str, Any]:
    require_admin_role(user)
    wid = require_workshop_id(user)
    cn = billing_svc.create_credit_note(
        db,
        workshop_id=wid,
        user_id=user.id,
        invoice_id=invoice_id,
        reason_de=body.reason_de,
    )
    return billing_svc.invoice_to_dict(cn)
