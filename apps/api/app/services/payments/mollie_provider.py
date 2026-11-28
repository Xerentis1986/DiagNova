"""Phase 25 – Mollie-Zahlungsanbieter (Test/Live gated).

Kein Stripe. Keys nur über Env/Settings – nie committen.
Verbindungstest: GET /v2/profiles/me (ohne Charge).
Live-Charges nur mit live_-Key UND mollie_live_charges_allowed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.subscriptions import PaymentWebhookEvent, Subscription
from app.services.audit import write_audit
from app.services.payments import mollie_secrets
from app.services.subscriptions import refresh_subscription_status

MOLLIE_API = "https://api.mollie.com/v2"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _api_key() -> str:
    key, _src = mollie_secrets.resolve_api_key()
    return key


def mollie_status() -> dict[str, Any]:
    key, key_src = mollie_secrets.resolve_api_key()
    configured = bool(key)
    test_mode = key.startswith("test_") if key else True
    live_keys = key.startswith("live_") if key else False
    live_flag = mollie_secrets.resolve_live_charges_allowed()
    pub = mollie_secrets.public_config()
    return {
        "provider": "mollie",
        "configured": configured,
        "test_mode": test_mode and not live_keys,
        "live_keys_present": live_keys,
        "live_charges_allowed": bool(live_flag) and live_keys,
        "api_key_source": key_src,
        "api_key_masked": pub.get("api_key_masked"),
        "editable_via_admin": True,
        "webhook_path": "/api/billing/webhooks/mollie",
        "connection_test_path": "/api/billing/mollie/connection-test",
        "config_path": "/api/billing/mollie/config",
        "message_de": pub.get("message_de")
        or (
            "Mollie: Key im Betreiber-UI oder Env setzen. Live-Charges standardmäßig gesperrt."
            if not configured
            else (
                "Mollie konfiguriert – Testmodus (test_-Key)."
                if test_mode and not live_keys
                else "Mollie Live-Key erkannt – Charges nur mit live_charges_allowed."
            )
        ),
        "security_de": pub.get("security_de"),
        "no_fake_success": True,
        "stripe_removed": True,
    }


async def connection_test() -> dict[str, Any]:
    """Ruft Mollie profiles/me auf – keine Zahlung, kein Fake-OK."""
    key = _api_key()
    if not key:
        return {
            "ok": False,
            "status": "not_configured",
            "http_status": None,
            "message_de": (
                "API-Key fehlt. Im Betreiber-UI unter Mollie eintragen oder MOLLIE_API_KEY setzen. "
                "Keine simulierte OK-Antwort."
            ),
        }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{MOLLIE_API}/profiles/me",
                headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            )
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "status": "network_error",
            "message_de": f"Mollie nicht erreichbar: {exc}",
        }
    if resp.status_code == 401:
        return {
            "ok": False,
            "status": "unauthorized",
            "http_status": 401,
            "message_de": "API-Key ungültig (401). Key prüfen – kein Fake-Erfolg.",
        }
    if resp.status_code >= 400:
        return {
            "ok": False,
            "status": "error",
            "http_status": resp.status_code,
            "detail": resp.text[:300],
            "message_de": f"Mollie antwortete HTTP {resp.status_code}.",
        }
    data = resp.json() if resp.content else {}
    return {
        "ok": True,
        "status": "connected",
        "http_status": 200,
        "profile_id": data.get("id"),
        "profile_name": data.get("name"),
        "mode": data.get("mode"),
        "message_de": "Mollie-Verbindungstest OK (profiles/me). Keine Charge ausgeführt.",
        "no_charge": True,
    }


async def create_checkout_payment(
    *,
    subscription_id: str,
    workshop_id: str,
    plan_code: str,
    customer_email: str,
    amount_cents: int,
    currency: str = "eur",
    redirect_url: str,
    description: str | None = None,
) -> dict[str, Any]:
    key = _api_key()
    if not key:
        return {
            "ok": False,
            "status": "not_configured",
            "message_de": "API-Key fehlt. Checkout nicht gestartet – keine simulierte Zahlung.",
            "live_payments": False,
        }
    if key.startswith("live_") and not mollie_secrets.resolve_live_charges_allowed():
        return {
            "ok": False,
            "status": "live_blocked",
            "message_de": "Live-Key vorhanden, aber live_charges_allowed=false. Keine Prod-Charge.",
            "live_payments": False,
        }

    value = f"{amount_cents / 100:.2f}"
    payload = {
        "amount": {"currency": currency.upper(), "value": value},
        "description": description or f"DiagNova {plan_code}",
        "redirectUrl": redirect_url,
        "metadata": {
            "subscription_id": subscription_id,
            "workshop_id": workshop_id,
            "plan_code": plan_code,
            "customer_email": customer_email,
        },
    }
    wh, _ = mollie_secrets.resolve_webhook_url()
    if wh:
        payload["webhookUrl"] = wh

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{MOLLIE_API}/payments",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        return {"ok": False, "status": "network_error", "message_de": str(exc)[:300]}

    if resp.status_code >= 400:
        return {
            "ok": False,
            "status": "mollie_error",
            "http_status": resp.status_code,
            "detail": resp.text[:400],
            "message_de": "Mollie Payment-Erstellung fehlgeschlagen.",
        }
    data = resp.json()
    checkout = (data.get("_links") or {}).get("checkout") or {}
    return {
        "ok": True,
        "status": "created",
        "payment_id": data.get("id"),
        "checkout_url": checkout.get("href"),
        "mode": data.get("mode"),
        "live_payments": key.startswith("live_") and mollie_secrets.resolve_live_charges_allowed(),
        "message_de": "Mollie-Payment angelegt (Checkout-URL).",
    }


def verify_mollie_webhook_optional(raw: bytes, signature: str | None) -> bool:
    """Optional HMAC wenn Webhook-Secret gesetzt – sonst true nur mit Secret-less Test."""
    secret, _ = mollie_secrets.resolve_webhook_secret()
    if not secret:
        return True  # Mollie sendet oft nur payment id; Signatur optional konfigurierbar
    if not signature:
        return False
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip().removeprefix("sha256="))


def process_mollie_webhook(
    db: Session,
    *,
    raw_body: bytes,
    signature_header: str | None,
    payment_id: str | None = None,
) -> dict[str, Any]:
    if not verify_mollie_webhook_optional(raw_body, signature_header):
        raise HTTPException(status_code=400, detail="Ungültige Webhook-Signatur")

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = {}
    pid = payment_id or payload.get("id")
    if not pid:
        raise HTTPException(status_code=400, detail="payment id fehlt")

    event_id = f"mollie:{pid}"
    existing = db.query(PaymentWebhookEvent).filter(PaymentWebhookEvent.event_id == event_id).first()
    if existing:
        return {
            "id": existing.id,
            "event_id": event_id,
            "status": "duplicate",
            "signature_valid": True,
            "message_de": "Webhook bereits verarbeitet (idempotent).",
            "payment_note_de": "Mollie – keine Doppelbuchung.",
            "subscription_id": None,
        }

    # Ohne Live-API-Fetch hier: nur Event speichern; Status-Refresh bei nächstem Poll/Admin
    ev = PaymentWebhookEvent(
        event_id=event_id,
        event_type="mollie.payment",
        payload_json=json.dumps({"id": pid, "raw_preview": raw_body.decode("utf-8", errors="replace")[:2000]}),
        signature_valid=True,
        processed_at=_now(),
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    write_audit(
        db,
        user_id=None,
        action="mollie_webhook",
        resource="payment_webhook",
        detail=event_id,
        workshop_id=None,
    )
    return {
        "id": ev.id,
        "event_id": event_id,
        "status": "processed",
        "signature_valid": True,
        "message_de": "Mollie-Webhook gespeichert. Payment-Status bitte serverseitig nachziehen.",
        "payment_note_de": "Kein Fake-paid ohne Mollie-Statusabfrage.",
        "subscription_id": None,
        "payment_id": pid,
    }
