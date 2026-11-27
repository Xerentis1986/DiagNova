"""Phase 21 – Stripe-Integration (Testmodus).

Produktive Live-Charges nur mit expliziten Live-Keys und Freigabe.
Ohne Keys: ehrlicher Status, keine erfundenen Zahlungen.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.subscriptions import PaymentWebhookEvent, Subscription
from app.services.audit import write_audit
from app.services.subscriptions import refresh_subscription_status


STRIPE_API = "https://api.stripe.com/v1"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def stripe_status() -> dict[str, Any]:
    s = get_settings()
    secret = (s.stripe_secret_key or "").strip()
    wh = (s.stripe_webhook_secret or "").strip()
    configured = bool(secret and wh)
    test_mode = secret.startswith("sk_test_") if secret else True
    live_keys = secret.startswith("sk_live_") if secret else False
    return {
        "provider": "stripe",
        "configured": configured,
        "test_mode": test_mode and not live_keys,
        "live_keys_present": live_keys,
        "live_charges_allowed": bool(s.stripe_live_charges_allowed) and live_keys,
        "publishable_key_configured": bool((s.stripe_publishable_key or "").strip()),
        "webhook_path": "/api/billing/webhooks/stripe",
        "message_de": (
            "Stripe-Testmodus bereit, sobald STRIPE_SECRET_KEY (sk_test_…) und "
            "STRIPE_WEBHOOK_SECRET gesetzt sind. Live-Charges standardmäßig gesperrt."
            if not configured
            else (
                "Stripe konfiguriert – Testmodus."
                if test_mode and not live_keys
                else "Stripe Live-Keys erkannt – Charges nur mit stripe_live_charges_allowed=true."
            )
        ),
        "no_fake_success": True,
    }


def verify_stripe_signature(payload: bytes, header: str | None, secret: str, tolerance_sec: int = 300) -> bool:
    """Stripe-Signature: t=…,v1=… (HMAC-SHA256 über f'{t}.{payload}')."""
    if not header or not secret:
        return False
    parts: dict[str, list[str]] = {}
    for item in header.split(","):
        item = item.strip()
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        parts.setdefault(k.strip(), []).append(v.strip())
    if "t" not in parts or "v1" not in parts:
        return False
    try:
        ts = int(parts["t"][0])
    except ValueError:
        return False
    if abs(int(time.time()) - ts) > tolerance_sec:
        return False
    signed = f"{ts}.".encode("utf-8") + payload
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, sig) for sig in parts["v1"])


async def create_checkout_session(
    *,
    subscription_id: str,
    workshop_id: str,
    plan_code: str,
    customer_email: str,
    success_url: str,
    cancel_url: str,
    amount_cents: int,
    currency: str = "eur",
    interval: str = "month",
) -> dict[str, Any]:
    """Erstellt Checkout Session über Stripe REST (httpx). Kein Fake-Success."""
    s = get_settings()
    secret = (s.stripe_secret_key or "").strip()
    if not secret:
        return {
            "ok": False,
            "status": "not_configured",
            "message_de": "STRIPE_SECRET_KEY fehlt. Checkout nicht gestartet – keine simulierte Zahlung.",
            "live_payments": False,
        }
    if secret.startswith("sk_live_") and not s.stripe_live_charges_allowed:
        return {
            "ok": False,
            "status": "live_blocked",
            "message_de": "Live-Keys vorhanden, aber stripe_live_charges_allowed=false. Keine Prod-Charge.",
            "live_payments": False,
        }

    data = {
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "customer_email": customer_email,
        "client_reference_id": subscription_id,
        "metadata[subscription_id]": subscription_id,
        "metadata[workshop_id]": workshop_id,
        "metadata[plan_code]": plan_code,
        "line_items[0][price_data][currency]": currency,
        "line_items[0][price_data][unit_amount]": str(amount_cents),
        "line_items[0][price_data][recurring][interval]": interval,
        "line_items[0][price_data][product_data][name]": f"DiagNova {plan_code}",
        "line_items[0][quantity]": "1",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{STRIPE_API}/checkout/sessions",
            content=urlencode(data),
            headers={
                "Authorization": f"Bearer {secret}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    if resp.status_code >= 400:
        return {
            "ok": False,
            "status": "stripe_error",
            "http_status": resp.status_code,
            "message_de": "Stripe-API-Fehler – siehe detail (keine erfundene Zahlung).",
            "detail": resp.text[:500],
            "live_payments": False,
        }
    body = resp.json()
    return {
        "ok": True,
        "status": "checkout_created",
        "session_id": body.get("id"),
        "url": body.get("url"),
        "mode": body.get("mode"),
        "test_mode": secret.startswith("sk_test_"),
        "message_de": "Checkout-Session erstellt. Zahlung erst nach Stripe-Abschluss + Webhook.",
    }


def process_stripe_webhook(
    db: Session,
    *,
    raw_body: bytes,
    signature_header: str | None,
) -> dict[str, Any]:
    s = get_settings()
    secret = (s.stripe_webhook_secret or "").strip()
    if not secret:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET nicht konfiguriert")

    sig_ok = verify_stripe_signature(raw_body, signature_header, secret)
    try:
        event = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Ungültiges JSON") from exc

    event_id = str(event.get("id") or "")
    event_type = str(event.get("type") or "unknown")
    if not event_id:
        raise HTTPException(status_code=400, detail="event.id fehlt")

    existing = (
        db.query(PaymentWebhookEvent)
        .filter(
            PaymentWebhookEvent.provider == "stripe",
            PaymentWebhookEvent.event_id == event_id,
        )
        .first()
    )
    if existing is not None and existing.status in {"processed", "duplicate", "received"}:
        return {
            "id": existing.id,
            "event_id": existing.event_id,
            "status": "duplicate",
            "signature_valid": existing.signature_valid,
            "message_de": "Idempotent: Stripe-Event bereits verarbeitet.",
            "duplicate": True,
        }

    if not sig_ok:
        if existing is None:
            evt = PaymentWebhookEvent(
                provider="stripe",
                event_id=event_id,
                event_type=event_type,
                status="rejected",
                signature_valid=False,
                payload_json=raw_body.decode("utf-8", errors="replace")[:8000],
            )
            db.add(evt)
            db.commit()
            db.refresh(evt)
            return {
                "id": evt.id,
                "event_id": event_id,
                "status": "rejected",
                "signature_valid": False,
                "message_de": "Signatur ungültig – Event abgelehnt.",
            }
        return {
            "id": existing.id,
            "event_id": event_id,
            "status": "rejected",
            "signature_valid": False,
            "message_de": "Signatur ungültig.",
        }

    data_obj = (event.get("data") or {}).get("object") or {}
    meta = data_obj.get("metadata") or {}
    subscription_id = meta.get("subscription_id") or data_obj.get("client_reference_id")
    workshop_id = meta.get("workshop_id")

    evt = existing or PaymentWebhookEvent(
        provider="stripe",
        event_id=event_id,
        event_type=event_type,
        status="received",
        signature_valid=True,
        payload_json=raw_body.decode("utf-8", errors="replace")[:8000],
        subscription_id=subscription_id,
    )
    if existing is None:
        db.add(evt)
    else:
        evt.signature_valid = True
        evt.status = "received"
        evt.subscription_id = subscription_id or evt.subscription_id

    message = "Event empfangen."
    if event_type in {
        "checkout.session.completed",
        "invoice.paid",
        "customer.subscription.updated",
    }:
        if subscription_id:
            sub = db.get(Subscription, subscription_id)
            if sub:
                sub.payment_provider = "stripe"
                sub.external_ref = str(data_obj.get("id") or sub.external_ref or "")
                if event_type in {"checkout.session.completed", "invoice.paid"}:
                    sub.status = "active"
                    sub.is_example_data = False
                refresh_subscription_status(sub)
                message = f"Abo {subscription_id} aktualisiert ({event_type})."
                write_audit(
                    db,
                    user_id=None,
                    action="stripe_webhook",
                    resource="subscription",
                    detail=f"{event_type}:{event_id}",
                    workshop_id=workshop_id or sub.workshop_id,
                )
            else:
                message = f"Subscription {subscription_id} nicht gefunden – Event gespeichert."
        else:
            message = "Kein subscription_id in Metadata – Event nur protokolliert."
    elif event_type in {"invoice.payment_failed", "customer.subscription.deleted"}:
        if subscription_id:
            sub = db.get(Subscription, subscription_id)
            if sub:
                sub.status = "past_due" if "failed" in event_type else "canceled"
                refresh_subscription_status(sub)
                message = f"Abo-Status → {sub.status}"

    evt.status = "processed"
    db.commit()
    db.refresh(evt)
    return {
        "id": evt.id,
        "event_id": event_id,
        "status": "processed",
        "signature_valid": True,
        "message_de": message,
        "subscription_id": subscription_id,
        "duplicate": False,
    }
