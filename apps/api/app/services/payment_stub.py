"""Phase 13 – Payment-Provider-STUB.

Kein Stripe/PayPal/Adyen o. Ä. ohne ausdrückliche Zustimmung.
Webhooks: HMAC-Signatur + Idempotenz über event_id.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.subscriptions import PaymentWebhookEvent, Subscription
from app.services.audit import write_audit
from app.services.subscriptions import PAYMENT_NOTE, get_workshop_subscription, refresh_subscription_status


def mock_webhook_secret() -> str:
    return get_settings().payment_webhook_demo_secret


def sign_payload(body: bytes, secret: str | None = None) -> str:
    key = (secret or mock_webhook_secret()).encode("utf-8")
    return hmac.new(key, body, hashlib.sha256).hexdigest()


def verify_signature(body: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = sign_payload(body)
    # Header kann "sha256=<hex>" oder roh sein
    provided = signature.removeprefix("sha256=").strip()
    return hmac.compare_digest(expected, provided)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def process_mock_webhook(
    db: Session,
    *,
    raw_body: bytes,
    signature: str | None,
    event_id: str,
    event_type: str,
    subscription_id: str,
    workshop_id: str | None,
    meta: dict | None = None,
) -> dict:
    sig_ok = verify_signature(raw_body, signature)
    existing = (
        db.query(PaymentWebhookEvent)
        .filter(
            PaymentWebhookEvent.provider == "mock",
            PaymentWebhookEvent.event_id == event_id,
        )
        .first()
    )
    # Idempotenz nur für bereits akzeptierte Events; rejected darf mit gültiger Signatur wiederholt werden
    if existing is not None and existing.status in {"processed", "duplicate", "received"}:
        return {
            "id": existing.id,
            "event_id": existing.event_id,
            "status": "duplicate",
            "signature_valid": existing.signature_valid,
            "message_de": "Idempotent: Event bereits verarbeitet (Replay erkannt).",
            "payment_note_de": PAYMENT_NOTE,
            "subscription_id": existing.subscription_id,
            "duplicate": True,
        }

    if not sig_ok:
        if existing is None:
            evt = PaymentWebhookEvent(
                provider="mock",
                event_id=event_id,
                event_type=event_type,
                signature_valid=False,
                status="rejected",
                payload_json=raw_body.decode("utf-8", errors="replace")[:8000],
                subscription_id=subscription_id,
                workshop_id=workshop_id,
                error_detail="Ungültige Stub-Signatur",
            )
            db.add(evt)
            db.commit()
        raise HTTPException(status_code=401, detail="Webhook-Signatur ungültig (Stub)")

    # Vorher rejected → Zeile für Neuversuch entfernen (Unique provider+event_id)
    if existing is not None and existing.status == "rejected":
        db.delete(existing)
        db.flush()

    sub = db.get(Subscription, subscription_id)
    if sub is None:
        evt = PaymentWebhookEvent(
            provider="mock",
            event_id=event_id,
            event_type=event_type,
            signature_valid=True,
            status="rejected",
            payload_json=raw_body.decode("utf-8", errors="replace")[:8000],
            subscription_id=subscription_id,
            workshop_id=workshop_id,
            error_detail="Subscription nicht gefunden",
        )
        db.add(evt)
        db.commit()
        raise HTTPException(status_code=404, detail="Subscription nicht gefunden")

    refresh_subscription_status(sub)
    now = _now()
    msg = f"Stub-Event {event_type} verarbeitet."

    if event_type == "invoice.paid":
        sub.status = "active"
        sub.grace_until = None
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=30)
        sub.cancel_at_period_end = False
        msg = "Stub: Rechnung bezahlt → active. Keine echte Abbuchung."
    elif event_type == "invoice.payment_failed":
        sub.status = "past_due"
        sub.grace_until = now + timedelta(days=3)
        msg = (
            "Stub: Zahlungsausfall → past_due (Grace 3 Tage). "
            "Laufende kritische Ops werden nicht abgebrochen."
        )
    elif event_type == "subscription.canceled":
        sub.status = "canceled"
        sub.canceled_at = now
        sub.cancel_at_period_end = False
        msg = "Stub: Abo gekündigt. Laufende kritische Ops nicht abrupt beendet."
    elif event_type == "subscription.renewed":
        sub.status = "active"
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=30)
        msg = "Stub: Verlängerung simuliert."
    elif event_type == "subscription.expired":
        sub.status = "expired"
        msg = "Stub: Abo abgelaufen. Neue Ops gesperrt; laufende kritische Ops dürfen enden."
    else:
        raise HTTPException(status_code=400, detail=f"Unbekannter Event-Typ: {event_type}")

    if meta:
        sub.notes = (sub.notes or "") + f" | webhook meta: {json.dumps(meta)[:200]}"

    db.add(sub)
    evt = PaymentWebhookEvent(
        provider="mock",
        event_id=event_id,
        event_type=event_type,
        signature_valid=True,
        status="processed",
        payload_json=raw_body.decode("utf-8", errors="replace")[:8000],
        subscription_id=sub.id,
        workshop_id=sub.workshop_id,
        processed_at=now,
    )
    db.add(evt)
    write_audit(
        db,
        user_id=None,
        workshop_id=sub.workshop_id,
        action="payment_webhook_stub",
        resource=f"event:{event_id}",
        detail=event_type,
    )
    db.commit()
    db.refresh(evt)
    return {
        "id": evt.id,
        "event_id": evt.event_id,
        "status": evt.status,
        "signature_valid": True,
        "message_de": msg,
        "payment_note_de": PAYMENT_NOTE,
        "subscription_id": sub.id,
        "duplicate": False,
    }


def apply_payment_failed_for_tests(db: Session, workshop_id: str) -> Subscription:
    """Hilfsfunktion Tests: past_due ohne HTTP."""
    sub = get_workshop_subscription(db, workshop_id)
    if sub is None:
        raise HTTPException(status_code=404, detail="Kein Abo")
    sub.status = "past_due"
    sub.grace_until = _now() + timedelta(days=3)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
