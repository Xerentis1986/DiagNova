"""Phase 21 – Stripe-Status, Signatur, E-Mail dry_run, Lizenzen (ohne echte Charges)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest


def test_stripe_status_not_configured(client, auth_headers):
    r = client.get("/api/billing/stripe/status", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "stripe"
    assert body["configured"] is False
    assert body["no_fake_success"] is True
    assert body["live_charges_allowed"] is False


def test_stripe_checkout_without_keys_no_fake_success(client, auth_headers):
    me = client.get("/api/subscriptions/me", headers=auth_headers)
    assert me.status_code == 200
    sub_id = me.json().get("id") or ""
    if not sub_id:
        # Trial anlegen (Stub)
        trial = client.post(
            "/api/subscriptions/me/trial",
            headers=auth_headers,
            json={"plan_code": "pkw_trial"},
        )
        assert trial.status_code == 200, trial.text
        sub_id = trial.json()["id"]
    r = client.post(
        "/api/billing/stripe/checkout",
        headers=auth_headers,
        json={
            "subscription_id": sub_id,
            "plan_code": "pkw_pro",
            "customer_email": "test@example.com",
            "amount_cents": 9900,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["status"] == "not_configured"
    assert not body.get("url")


def test_stripe_signature_helper():
    from app.services.payments.stripe_provider import verify_stripe_signature

    secret = "whsec_test_secret"
    payload = b'{"id":"evt_1","type":"ping"}'
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"
    assert verify_stripe_signature(payload, header, secret) is True
    assert verify_stripe_signature(payload, "t=1,v1=dead", secret) is False


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
