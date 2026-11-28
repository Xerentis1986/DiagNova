"""DEPRECATED – Stripe entfernt (Phase 25). Nur noch Ablehnungshinweise für Alt-Clients."""

from __future__ import annotations

from typing import Any


def stripe_status() -> dict[str, Any]:
    return {
        "provider": "stripe",
        "configured": False,
        "removed": True,
        "replacement": "mollie",
        "message_de": (
            "Stripe wurde entfernt. Bitte Mollie nutzen: "
            "/api/billing/mollie/status und MOLLIE_API_KEY."
        ),
        "no_fake_success": True,
        "live_charges_allowed": False,
    }


async def create_checkout_session(**kwargs: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "stripe_removed",
        "message_de": "Stripe entfernt – Mollie verwenden (/api/billing/mollie/checkout).",
    }


def verify_stripe_signature(*_a: Any, **_k: Any) -> bool:
    return False


def process_stripe_webhook(*_a: Any, **_k: Any) -> dict[str, Any]:
    return {
        "status": "stripe_removed",
        "message_de": "Stripe-Webhooks deaktiviert. Mollie: /api/billing/webhooks/mollie",
    }
