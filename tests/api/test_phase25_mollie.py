"""Phase 25 – Mollie Status, Connection-Test (gemockt), Stripe entfernt."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient


def test_mollie_status_not_configured(client: TestClient, auth_headers: dict):
    r = client.get("/api/billing/mollie/status", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "mollie"
    assert body["configured"] is False
    assert body["no_fake_success"] is True
    assert body["stripe_removed"] is True


def test_mollie_checkout_without_keys(client: TestClient, auth_headers: dict):
    me = client.get("/api/subscriptions/me", headers=auth_headers)
    assert me.status_code == 200
    sub_id = me.json().get("id") or ""
    if not sub_id:
        trial = client.post(
            "/api/subscriptions/me/trial",
            headers=auth_headers,
            json={"plan_code": "pkw_trial"},
        )
        assert trial.status_code == 200
        sub_id = trial.json()["id"]
    r = client.post(
        "/api/billing/mollie/checkout",
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


def test_mollie_connection_test_without_key(client: TestClient, auth_headers: dict):
    r = client.post("/api/billing/mollie/connection-test", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["status"] == "not_configured"


def test_mollie_connection_test_mocked_ok(client: TestClient, auth_headers: dict, monkeypatch):
    from app.core.config import get_settings
    from app.services.payments import mollie_provider

    s = get_settings()
    monkeypatch.setattr(s, "mollie_api_key", "test_mock_key_phase25")

    class _Resp:
        status_code = 200
        content = b'{"id":"pfl_test","name":"DiagNova","mode":"test"}'

        def json(self):
            return {"id": "pfl_test", "name": "DiagNova", "mode": "test"}

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None):
            assert "profiles/me" in url
            return _Resp()

    monkeypatch.setattr(mollie_provider.httpx, "AsyncClient", _Client)
    r = client.post("/api/billing/mollie/connection-test", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["status"] == "connected"
    assert body["no_charge"] is True


def test_stripe_status_removed(client: TestClient, auth_headers: dict):
    r = client.get("/api/billing/stripe/status", headers=auth_headers)
    assert r.status_code == 200
    assert r.json().get("removed") is True
    assert r.json().get("replacement") == "mollie"


def test_commerce_overview_mollie(client: TestClient, auth_headers: dict):
    r = client.get("/api/commerce/overview", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["payment_provider"] == "mollie"
    assert body["stripe"]["removed"] is True
    assert "at_legal_note_de" in body
