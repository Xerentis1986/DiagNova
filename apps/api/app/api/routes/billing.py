"""Phase 13 – Payment-Stub Webhooks (signiert, idempotent). KEINE echten Abbuchungen."""

from __future__ import annotations

import json

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import CurrentUser, DbSession
from app.models.subscriptions import Subscription
from app.schemas.subscriptions import MockWebhookOut, MockWebhookRequest, SubscriptionOut
from app.services import email_service, license_management, payment_stub
from app.services import subscriptions as subsvc
from app.services.payments import stripe_provider
from app.services.tenant import require_admin_role

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/stub-info")
def stub_info(_user: CurrentUser) -> dict:
    return {
        "provider": "mock",
        "live_payments": False,
        "message_de": subsvc.PAYMENT_NOTE,
        "signature_header": "X-DiagNova-Stub-Signature",
        "signature_format": "sha256=<hmac_hex> oder roh hex",
        "legal_note_de": (
            "DACH Rechnungs-/Steueranforderungen und AVV: rechtliche Prüfung offen. "
            "Kein echter Payment-Provider ohne Zustimmung."
        ),
    }


@router.post("/webhooks/mock", response_model=MockWebhookOut)
async def mock_webhook(
    request: Request,
    db: DbSession,
    x_diagnova_stub_signature: str | None = Header(default=None),
) -> MockWebhookOut:
    raw = await request.body()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Ungültiges JSON") from exc

    body = MockWebhookRequest(**payload)
    result = payment_stub.process_mock_webhook(
        db,
        raw_body=raw,
        signature=x_diagnova_stub_signature,
        event_id=body.event_id,
        event_type=body.event_type,
        subscription_id=body.subscription_id,
        workshop_id=body.workshop_id,
        meta=body.meta,
    )
    sub_out = None
    if result.get("subscription_id") and result.get("status") in {"processed", "duplicate"}:
        sub = db.get(Subscription, result["subscription_id"])
        if sub:
            sub_out = SubscriptionOut(**subsvc.subscription_to_dict(db, sub))
    return MockWebhookOut(
        id=result["id"],
        event_id=result["event_id"],
        status=result["status"],
        signature_valid=result["signature_valid"],
        message_de=result["message_de"],
        payment_note_de=result["payment_note_de"],
        subscription=sub_out,
    )


@router.post("/demo/sign-payload")
def demo_sign_payload(body: MockWebhookRequest, user: CurrentUser) -> dict:
    """Nur Demo: Signatur + kanonischen Body für Stub-Webhook (kein Prod-PSP)."""
    require_admin_role(user)
    # Kanonisch: sortierte Keys, kompakte Trenner – Client muss body_raw exakt POSTen
    raw = json.dumps(
        body.model_dump(mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    sig = payment_stub.sign_payload(raw)
    return {
        "signature": sig,
        "header": f"sha256={sig}",
        "body_raw": raw.decode("utf-8"),
        "body_canonical_note_de": (
            "Client muss body_raw unverändert als Request-Body POSTen. "
            "SIMULATION – keine echte Zahlung."
        ),
        "payment_note_de": subsvc.PAYMENT_NOTE,
        "raw_preview": raw.decode("utf-8")[:500],
    }


# --- Phase 21 Stripe + Lizenz + Mail ---


@router.get("/stripe/status")
def stripe_status_endpoint(_user: CurrentUser) -> dict:
    stub = stub_info(_user)
    stripe = stripe_provider.stripe_status()
    return {
        **stripe,
        "mock_stub_still_available": True,
        "mock_stub_path": "/api/billing/webhooks/mock",
        "stub_info": stub,
    }


class StripeCheckoutRequest(BaseModel):
    subscription_id: str
    plan_code: str = "pkw_pro"
    customer_email: EmailStr
    amount_cents: int = Field(ge=100, le=500_000)
    interval: str = Field(default="month", pattern="^(month|year)$")
    success_url: str = "http://localhost:5173/commerce?checkout=success"
    cancel_url: str = "http://localhost:5173/commerce?checkout=cancel"


@router.post("/stripe/checkout")
async def stripe_checkout(body: StripeCheckoutRequest, user: CurrentUser, db: DbSession) -> dict:
    require_admin_role(user)
    wid = user.workshop_id
    if not wid:
        raise HTTPException(status_code=400, detail="Kein Mandant")
    sub = db.get(Subscription, body.subscription_id)
    if sub is None or sub.workshop_id != wid:
        raise HTTPException(status_code=404, detail="Subscription nicht gefunden")
    return await stripe_provider.create_checkout_session(
        subscription_id=sub.id,
        workshop_id=wid,
        plan_code=body.plan_code,
        customer_email=str(body.customer_email),
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        amount_cents=body.amount_cents,
        interval=body.interval,
    )


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db: DbSession,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> dict:
    raw = await request.body()
    return stripe_provider.process_stripe_webhook(
        db, raw_body=raw, signature_header=stripe_signature
    )


@router.get("/licenses/overview")
def licenses_overview(user: CurrentUser, db: DbSession) -> dict:
    wid = user.workshop_id
    if not wid:
        raise HTTPException(status_code=400, detail="Kein Mandant")
    return license_management.license_overview(db, wid)


class LicenseActivateRequest(BaseModel):
    subscription_id: str
    device_name: str = Field(min_length=1, max_length=128)
    device_fingerprint: str = Field(min_length=8, max_length=128)
    platform: str = "windows"


@router.post("/licenses/activate-device")
def licenses_activate(body: LicenseActivateRequest, user: CurrentUser, db: DbSession) -> dict:
    require_admin_role(user)
    wid = user.workshop_id
    if not wid:
        raise HTTPException(status_code=400, detail="Kein Mandant")
    return license_management.activate_or_refresh_license(
        db,
        workshop_id=wid,
        subscription_id=body.subscription_id,
        device_name=body.device_name,
        device_fingerprint=body.device_fingerprint,
        platform=body.platform,
    )


class LicenseVerifyRequest(BaseModel):
    device_fingerprint: str = Field(min_length=8, max_length=128)


@router.post("/licenses/verify")
def licenses_verify(body: LicenseVerifyRequest, user: CurrentUser, db: DbSession) -> dict:
    wid = user.workshop_id
    if not wid:
        raise HTTPException(status_code=400, detail="Kein Mandant")
    return license_management.verify_connector_license(
        db, workshop_id=wid, device_fingerprint=body.device_fingerprint
    )


class LicenseTokenRequest(BaseModel):
    device_fingerprint: str = Field(min_length=8, max_length=128)
    valid_hours: int | None = Field(default=None, ge=1, le=72)


@router.post("/licenses/offline-token")
def licenses_offline_token(body: LicenseTokenRequest, user: CurrentUser, db: DbSession) -> dict:
    """Phase 23 – signiertes Offline-Token für Connector-Gate."""
    wid = user.workshop_id
    if not wid:
        raise HTTPException(status_code=400, detail="Kein Mandant")
    return license_management.issue_signed_offline_token(
        db,
        workshop_id=wid,
        device_fingerprint=body.device_fingerprint,
        valid_hours=body.valid_hours,
    )


@router.get("/email/status")
def email_status_endpoint(user: CurrentUser) -> dict:
    require_admin_role(user)
    return email_service.email_status()


class EmailSendRequest(BaseModel):
    template: str
    to_email: EmailStr
    extra_body: str | None = None
    force_dry_run: bool = True


@router.post("/email/send-template")
def email_send(body: EmailSendRequest, user: CurrentUser) -> dict:
    require_admin_role(user)
    # Standard: dry_run – kein Spam ohne Freigabe
    return email_service.send_template_email(
        template=body.template,
        to_email=str(body.to_email),
        extra_body=body.extra_body,
        force_dry_run=body.force_dry_run,
    )
