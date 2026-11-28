"""Phase 21 – Stripe-Status, Signatur, E-Mail dry_run, Lizenzen (ohne echte Charges)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest


def test_stripe_removed_shim(client, auth_headers):
    """Phase 25: Stripe entfernt – Alt-Pfad zeigt Replacement Mollie."""
    r = client.get("/api/billing/stripe/status", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body.get("removed") is True
    assert body.get("replacement") == "mollie"


def test_stripe_checkout_removed(client, auth_headers):
    r = client.post(
        "/api/billing/stripe/checkout",
        headers=auth_headers,
        json={
            "subscription_id": "x" * 8,
            "plan_code": "pkw_pro",
            "customer_email": "test@example.com",
            "amount_cents": 9900,
        },
    )
    # Admin required – may 403/404/200 with removed
    assert r.status_code in {200, 403, 404}
    if r.status_code == 200:
        assert r.json().get("status") == "stripe_removed"


def test_stripe_signature_helper_disabled():
    from app.services.payments.stripe_provider import verify_stripe_signature

    assert verify_stripe_signature(b"{}", "t=1,v1=x", "secret") is False

def test_email_dry_run(client, auth_headers):
    r = client.post(
        "/api/billing/email/send-template",
        headers=auth_headers,
        json={
            "template": "invoice",
            "to_email": "customer@example.com",
            "force_dry_run": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["status"] == "dry_run"


def test_admin_dashboard_has_commerce_metrics(client, auth_headers):
    # Seed-Admin ist Plattform-Admin in Demo
    r = client.get("/api/admin/dashboard", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert "mrr_cents" in body
    assert "customers_b2b" in body
    assert "invoices_open" in body
    assert "stripe" in body
