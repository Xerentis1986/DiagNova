"""Phase 23 – SSRF Bridge, License-Token, Stripe-Webhook-Fixture, SMTP lokal."""

from __future__ import annotations

import hashlib
import hmac
import json
import smtplib
import threading
import time
from email.parser import BytesParser
from email.policy import default

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.services import connector_bridge, email_service
from app.services.connector_bridge import ConnectorBridgeError, validate_connector_base_url
from app.services.payments.stripe_provider import verify_stripe_signature
from app.services.mfa_totp import totp_at


def test_ssrf_blocks_external_connector_host(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "connector_base_url", "http://169.254.169.254/latest")
    monkeypatch.setattr(s, "connector_url_allowlist", "127.0.0.1,localhost")
    with pytest.raises(ConnectorBridgeError) as ei:
        validate_connector_base_url()
    assert ei.value.status_code == 400

    monkeypatch.setattr(s, "connector_base_url", "http://evil.example.com:8765")
    with pytest.raises(ConnectorBridgeError):
        validate_connector_base_url()

    monkeypatch.setattr(s, "connector_base_url", "http://127.0.0.1:8765")
    assert validate_connector_base_url().startswith("http://127.0.0.1")


def test_stripe_webhook_signature_fixture():
    secret = "whsec_test_phase23"
    payload = b'{"id":"evt_test","type":"checkout.session.completed"}'
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={ts},v1={sig}"
    assert verify_stripe_signature(payload, header, secret) is True
    assert verify_stripe_signature(payload, f"t={ts},v1=deadbeef", secret) is False
    assert verify_stripe_signature(payload, None, secret) is False


def test_smtp_send_path_with_local_stub(monkeypatch):
    """Interne SMTP-E2E: smtplib wird mit lokalem Stub verdrahtet (kein Prod-SMTP)."""
    sent: dict = {}

    class _FakeSMTP:
        def __init__(self, host, port, timeout=20):
            sent["host"] = host
            sent["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            sent["tls"] = True

        def login(self, user, password):
            sent["login"] = user

        def send_message(self, msg):
            sent["to"] = msg["To"]
            sent["subject"] = msg["Subject"]

    monkeypatch.setattr(email_service.smtplib, "SMTP", _FakeSMTP)
    s = get_settings()
    monkeypatch.setattr(s, "smtp_host", "127.0.0.1")
    monkeypatch.setattr(s, "smtp_port", 2525)
    monkeypatch.setattr(s, "smtp_from_email", "noreply@diagnova.test")
    monkeypatch.setattr(s, "smtp_use_tls", False)
    monkeypatch.setattr(s, "smtp_user", "")
    result = email_service.send_template_email(
        template="security_alert",
        to_email="ops@diagnova.test",
        force_dry_run=False,
    )
    assert result["ok"] is True
    assert result["status"] == "sent"
    assert sent.get("to") == "ops@diagnova.test"
    assert sent.get("host") == "127.0.0.1"


def test_offline_license_token_endpoint(client: TestClient, auth_headers: dict[str, str]):
    from app.services import license_crypto

    r = client.post(
        "/api/billing/licenses/offline-token",
        headers=auth_headers,
        json={"device_fingerprint": "dev_phase23_test_device", "valid_hours": 2},
    )
    assert r.status_code == 200
    body = r.json()
    assert "payload" in body and "signature" in body
    payload = body["payload"]
    sig = body["signature"]
    # Phase 24: bevorzugt RSA; HMAC nur Fallback
    if body.get("algorithm", "").startswith("RSA"):
        assert license_crypto.verify_payload(payload, sig) is True
    else:
        secret = get_settings().license_hmac_secret.encode()
        expected = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
        assert hmac.compare_digest(expected, sig)


def test_invoice_pdf_and_mfa_still_ok(client: TestClient, auth_headers: dict[str, str]):
    acc = client.post(
        "/api/commerce/accounts",
        headers=auth_headers,
        json={
            "customer_type": "b2c",
            "contact_name": "Phase23",
            "billing_email": "p23@example.com",
            "country": "AT",
            "accept_terms": True,
            "accept_privacy": True,
            "ack_withdrawal": True,
        },
    )
    assert acc.status_code == 200, acc.text
    aid = acc.json().get("id") or acc.json().get("account", {}).get("id")
    assert aid
    sub = client.post(
        f"/api/commerce/accounts/{aid}/subscribe",
        headers=auth_headers,
        json={"plan_code": "pkw_basic", "force_vies_stub": True},
    )
    assert sub.status_code == 200, sub.text
    inv_id = sub.json().get("invoice", {}).get("id")
    assert inv_id
    pdf = client.get(f"/api/commerce/invoices/{inv_id}/download?format=pdf", headers=auth_headers)
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
    st = client.get("/api/admin/mfa/status", headers=auth_headers)
    assert st.status_code == 200
