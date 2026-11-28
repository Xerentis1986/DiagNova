"""Phase 22 – Live-Bridge (demo), MFA TOTP, Invoice PDF, E-Mail Auth."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.mfa_totp import totp_at, verify_totp, _b32_secret


def test_bridge_status_and_demo_live(client: TestClient, auth_headers: dict[str, str]):
    br = client.get("/api/connector/bridge-status", headers=auth_headers)
    assert br.status_code == 200
    body = br.json()
    assert "connector" in body
    assert body["connector"]["reachable"] in (True, False)

    conn_demo = client.get("/api/connection?mode=demo", headers=auth_headers)
    assert conn_demo.status_code == 200
    assert conn_demo.json()["data_source"] == "simulated"
    assert conn_demo.json()["mode"] == "simulator"

    vehicles = client.get("/api/vehicles", headers=auth_headers)
    assert vehicles.status_code == 200
    vids = vehicles.json()
    assert vids
    vid = vids[0]["id"]

    live = client.get(f"/api/diagnostics/{vid}/live?mode=demo", headers=auth_headers)
    assert live.status_code == 200
    assert live.json()["data_source"] == "simulated"

    # LIVE ohne Connector → Fehler, kein Simulator-Fallback
    live_fail = client.get(f"/api/diagnostics/{vid}/live?mode=live", headers=auth_headers)
    assert live_fail.status_code in {409, 503, 400}


def test_mfa_totp_roundtrip(client: TestClient, auth_headers: dict[str, str]):
    st = client.get("/api/admin/mfa/status", headers=auth_headers)
    assert st.status_code == 200
    setup = client.post("/api/admin/mfa/setup", headers=auth_headers)
    assert setup.status_code == 200
    secret = setup.json()["secret"]
    code = totp_at(secret)
    assert verify_totp(secret, code)
    conf = client.post("/api/admin/mfa/confirm", headers=auth_headers, json={"code": code})
    assert conf.status_code == 200
    assert conf.json()["mfa_enabled"] is True

    # Login ohne MFA-Code schlägt fehl
    bad = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "AdminDemo123!"},
    )
    assert bad.status_code == 401

    ok = client.post(
        "/api/auth/login",
        json={
            "email": "admin@example.com",
            "password": "AdminDemo123!",
            "mfa_code": totp_at(secret),
        },
    )
    assert ok.status_code == 200


def test_invoice_pdf_and_password_reset(client: TestClient, auth_headers: dict[str, str]):
    # Commerce B2C account + subscribe für Invoice
    acc = client.post(
        "/api/commerce/accounts",
        headers=auth_headers,
        json={
            "customer_type": "b2c",
            "contact_name": "Phase22 Test",
            "billing_email": "p22@example.com",
            "country": "AT",
            "accept_terms": True,
            "accept_privacy": True,
            "ack_withdrawal": True,
        },
    )
    assert acc.status_code == 200, acc.text
    aid = acc.json()["id"] if "id" in acc.json() else acc.json().get("account", {}).get("id")
    if not aid:
        # structure may nest
        aid = acc.json().get("billing_account", {}).get("id") or acc.json().get("account_id")
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
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert pdf.content[:4] == b"%PDF"

    reset = client.post("/api/auth/password-reset/request", json={"email": "admin@example.com"})
    assert reset.status_code == 200
    assert reset.json()["ok"] is True


def test_totp_helper_unit():
    secret = _b32_secret()
    code = totp_at(secret)
    assert len(code) == 6
    assert verify_totp(secret, code)
    assert not verify_totp(secret, "000000")
