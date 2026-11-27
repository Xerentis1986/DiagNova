"""Phase 13 – Abos, Entitlements, Mandanten, Webhook-Stub, Admin."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.services import payment_stub


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _sign_and_post(client: TestClient, headers: dict[str, str], payload: dict) -> dict:
    """Signiert kanonischen Body und POSTet denselben Rohkörper."""
    signed = client.post("/api/billing/demo/sign-payload", headers=headers, json=payload)
    assert signed.status_code == 200, signed.text
    body_raw = signed.json()["body_raw"]
    sig_header = signed.json()["header"]
    # Verifikation: lokale Signatur muss matchen
    local = payment_stub.sign_payload(body_raw.encode("utf-8"))
    assert local == signed.json()["signature"]
    res = client.post(
        "/api/billing/webhooks/mock",
        content=body_raw,
        headers={**headers, "X-DiagNova-Stub-Signature": sig_header, "Content-Type": "application/json"},
    )
    return {"response": res, "body_raw": body_raw, "sig": sig_header}


def test_plans_and_demo_subscription(client: TestClient, auth_headers: dict[str, str]):
    plans = client.get("/api/subscriptions/plans", headers=auth_headers)
    assert plans.status_code == 200
    codes = {p["code"] for p in plans.json()}
    assert "pkw_basic" in codes
    assert "pkw_pro" in codes
    assert "lkw_planned" in codes
    assert all("STUB" in p["payment_note_de"].upper() or "SIMULATION" in p["payment_note_de"].upper() for p in plans.json())

    me = client.get("/api/subscriptions/me", headers=auth_headers)
    assert me.status_code == 200
    body = me.json()
    assert body["plan_code"] == "pkw_pro"
    assert body["status"] == "active"
    assert body["license_active"] is True
    assert body["allows_new_operations"] is True
    assert "diagnostics.read" in body["entitlements"]
    assert "mock" in body["payment_provider"]


def test_entitlements_and_roles(client: TestClient, auth_headers: dict[str, str]):
    ok = client.get(
        "/api/subscriptions/me/entitlements/diagnostics.read",
        headers=auth_headers,
    )
    assert ok.status_code == 200
    assert ok.json()["allowed"] is True

    missing = client.get(
        "/api/subscriptions/me/entitlements/vehicle.lkw",
        headers=auth_headers,
    )
    assert missing.status_code == 200
    assert missing.json()["allowed"] is False

    tech = _login(client, "tech@example.com", "TechDemo123!")
    # Techniker darf Abo nicht kündigen
    cancel = client.post(
        "/api/subscriptions/me/cancel",
        headers=tech,
        json={"at_period_end": True},
    )
    assert cancel.status_code == 403


def test_tenant_isolation_invitations_devices(client: TestClient, auth_headers: dict[str, str]):
    inv = client.post(
        "/api/workshop/me/invitations",
        headers=auth_headers,
        json={"email": "neu.kollege@example.com", "role": "viewer"},
    )
    assert inv.status_code == 200, inv.text
    token = inv.json()["token"]
    assert token

    accept = client.post(
        "/api/invitations/accept",
        json={
            "token": token,
            "full_name": "Neuer Kollege",
            "password": "NeuKollege123!",
        },
    )
    assert accept.status_code == 200
    assert accept.json()["status"] == "accepted"

    # Zweiter Mandant registrieren
    reg = client.post(
        "/api/tenants/register",
        json={
            "workshop_name": "Andere Werkstatt Demo",
            "admin_email": "andere.admin@example.com",
            "admin_full_name": "Andere Admin",
            "password": "AndereAdmin123!",
            "country": "AT",
            "plan_code": "pkw_trial",
            "acknowledge_demo": True,
        },
    )
    assert reg.status_code == 200, reg.text
    other_headers = _login(client, "andere.admin@example.com", "AndereAdmin123!")

    # Fremde Einladungen nicht sichtbar
    other_inv = client.get("/api/workshop/me/invitations", headers=other_headers)
    assert other_inv.status_code == 200
    assert all(i["email"] != "neu.kollege@example.com" for i in other_inv.json())

    # Gerätebindung
    bind = client.post(
        "/api/subscriptions/me/devices",
        headers=auth_headers,
        json={
            "device_name": "Diag-PC-1",
            "device_fingerprint": "fp-test-phase13-aaaa",
            "platform": "windows",
        },
    )
    assert bind.status_code == 200, bind.text
    listed = client.get("/api/subscriptions/me/devices", headers=auth_headers)
    assert any(d["device_fingerprint"] == "fp-test-phase13-aaaa" for d in listed.json())

    # Anderer Mandant sieht Gerät nicht
    other_dev = client.get("/api/subscriptions/me/devices", headers=other_headers)
    assert all(d["device_fingerprint"] != "fp-test-phase13-aaaa" for d in other_dev.json())


def test_webhook_signature_idempotency_and_payment_failed(
    client: TestClient, auth_headers: dict[str, str]
):
    sub = client.get("/api/subscriptions/me", headers=auth_headers).json()
    payload = {
        "event_id": "evt_phase13_pay_fail_1",
        "event_type": "invoice.payment_failed",
        "subscription_id": sub["id"],
        "workshop_id": sub["workshop_id"],
        "meta": {"demo": True},
    }

    # Ungültige Signatur
    bad = client.post(
        "/api/billing/webhooks/mock",
        content=json.dumps(payload, separators=(",", ":"), sort_keys=True),
        headers={"Content-Type": "application/json", "X-DiagNova-Stub-Signature": "deadbeef"},
    )
    assert bad.status_code == 401

    first = _sign_and_post(client, auth_headers, payload)
    assert first["response"].status_code == 200, first["response"].text
    assert first["response"].json()["status"] == "processed"
    assert first["response"].json()["subscription"]["status"] == "past_due"

    # Replay / Idempotenz
    replay = client.post(
        "/api/billing/webhooks/mock",
        content=first["body_raw"],
        headers={
            "Content-Type": "application/json",
            "X-DiagNova-Stub-Signature": first["sig"],
        },
    )
    assert replay.status_code == 200
    assert replay.json()["status"] == "duplicate"

    # Neue kritische Ops bei past_due gesperrt
    start = client.post(
        "/api/subscriptions/me/critical-ops",
        headers=auth_headers,
        json={"operation_kind": "coding_sim", "resource_ref": "blocked-after-past-due"},
    )
    assert start.status_code == 402


def test_cancel_does_not_abort_critical_op(client: TestClient, auth_headers: dict[str, str]):
    # Frisches Stub-Abo aktivieren (nach past_due aus anderem Test – Reihenfolge: eigene Fixture)
    # Sicher aktivieren
    act = client.post(
        "/api/subscriptions/me/activate-stub",
        headers=auth_headers,
        json={"plan_code": "pkw_basic", "acknowledge_stub_payment": True},
    )
    assert act.status_code == 200, act.text
    assert act.json()["status"] == "active"

    start = client.post(
        "/api/subscriptions/me/critical-ops",
        headers=auth_headers,
        json={
            "operation_kind": "service_sim",
            "resource_ref": "keep-running",
            "message_de": "Darf nicht abrupt enden",
        },
    )
    assert start.status_code == 200, start.text
    op_id = start.json()["id"]
    assert start.json()["status"] == "running"

    # Sofortkündigung
    cancel = client.post(
        "/api/subscriptions/me/cancel",
        headers=auth_headers,
        json={"at_period_end": False, "reason_de": "Test Sofortkündigung"},
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "canceled"
    assert cancel.json()["has_running_critical_ops"] is True

    # Finish trotzdem erlaubt
    finish = client.post(
        f"/api/subscriptions/me/critical-ops/{op_id}/finish",
        headers=auth_headers,
    )
    assert finish.status_code == 200
    assert finish.json()["status"] == "completed"

    # Neue Ops gesperrt
    again = client.post(
        "/api/subscriptions/me/critical-ops",
        headers=auth_headers,
        json={"operation_kind": "service_sim", "resource_ref": "should-block"},
    )
    assert again.status_code == 402


def test_admin_dashboard_platform_only(client: TestClient, auth_headers: dict[str, str]):
    dash = client.get("/api/admin/dashboard", headers=auth_headers)
    assert dash.status_code == 200, dash.text
    body = dash.json()
    assert body["payment_mode"] in {
        "mock_stub",
        "mock_stub_plus_stripe_ready",
        "stripe_test",
        "stripe_live_gated",
    }
    assert body["workshops_count"] >= 1
    assert body["users_count"] >= 2
    assert "BLK-PAY" in " ".join(body["legal_open_items_de"]) or any(
        "Payment" in x or "Zahlung" in x for x in body["legal_open_items_de"]
    )

    tech = _login(client, "tech@example.com", "TechDemo123!")
    denied = client.get("/api/admin/dashboard", headers=tech)
    assert denied.status_code == 403

    users = client.get("/api/admin/users", headers=auth_headers)
    assert users.status_code == 200
    assert any(u["is_platform_admin"] for u in users.json())

    support = client.get("/api/admin/support", headers=auth_headers)
    assert support.status_code == 200
    assert "payment_note_de" in support.json()


def test_planned_plans_not_activatable(client: TestClient, auth_headers: dict[str, str]):
    bad = client.post(
        "/api/subscriptions/me/activate-stub",
        headers=auth_headers,
        json={"plan_code": "lkw_planned", "acknowledge_stub_payment": True},
    )
    assert bad.status_code == 400

    no_ack = client.post(
        "/api/subscriptions/me/activate-stub",
        headers=auth_headers,
        json={"plan_code": "pkw_basic", "acknowledge_stub_payment": False},
    )
    assert no_ack.status_code == 400
