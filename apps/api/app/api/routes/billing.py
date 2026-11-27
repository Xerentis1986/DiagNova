"""Phase 13 – Payment-Stub Webhooks (signiert, idempotent). KEINE echten Abbuchungen."""

from __future__ import annotations

import json

from fastapi import APIRouter, Header, HTTPException, Request

from app.api.deps import CurrentUser, DbSession
from app.models.subscriptions import Subscription
from app.schemas.subscriptions import MockWebhookOut, MockWebhookRequest, SubscriptionOut
from app.services import payment_stub
from app.services import subscriptions as subsvc
from app.services.tenant import require_admin_role

router = APIRouter(prefix="/billing", tags=["billing-stub"])


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
