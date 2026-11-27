"""Phase 21 – B2B/B2C Commerce, VIES-Stub, Steuerpreview, Rechnungen."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.commerce.tax_engine import resolve_tax
from app.services.commerce.vies import normalize_vat


def _login(client: TestClient, email: str = "admin@example.com", password: str = "AdminDemo123!") -> dict:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_commerce_overview(client: TestClient, auth_headers: dict[str, str]):
    res = client.get("/api/commerce/overview", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["live_payments"] is False
    assert "b2b" in body["supports"]
    assert body["tax_review_status"] == "draft_needs_review"


def test_tax_preview_scenarios():
    at_b2c = resolve_tax(customer_type="b2c", customer_country="AT", net_cents=10000)
    assert at_b2c["scenario"] == "b2c_at"
    assert at_b2c["vat_rate_bp"] == 2000
    assert at_b2c["gross_cents"] == 12000
    assert at_b2c["display_gross"] is True

    eu_b2b = resolve_tax(
        customer_type="b2b",
        customer_country="DE",
        vat_id="DE123456789",
        vat_valid=True,
        net_cents=10000,
    )
    assert eu_b2b["scenario"] == "b2b_reverse_charge"
    assert eu_b2b["reverse_charge"] is True
    assert eu_b2b["vat_cents"] == 0

    oss = resolve_tax(customer_type="b2c", customer_country="DE", net_cents=10000)
    assert oss["scenario"] == "b2c_eu_oss"
    assert oss["oss_applicable"] is True
    assert oss["vat_rate_bp"] == 1900


def test_vies_normalize_and_stub(client: TestClient, auth_headers: dict[str, str]):
    country, number = normalize_vat("AT U12345678")
    assert country == "AT"
    assert number == "U12345678"

    ok = client.post(
        "/api/commerce/vat/check",
        headers=auth_headers,
        json={"vat_id": "ATU12345678", "force_stub": True},
    )
    assert ok.status_code == 200
    assert ok.json()["valid"] is True
    assert ok.json()["request_mode"] == "stub"

    bad = client.post(
        "/api/commerce/vat/check",
        headers=auth_headers,
        json={"vat_id": "ATU00000000", "force_stub": True},
    )
    assert bad.status_code == 200
    assert bad.json()["valid"] is False


def test_b2c_account_subscribe_invoice_cancel(client: TestClient):
    headers = _login(client)
    create = client.post(
        "/api/commerce/accounts",
        headers=headers,
        json={
            "customer_type": "b2c",
            "contact_name": "Max Privat",
            "billing_email": "max.privat@example.com",
            "country": "AT",
            "street": "Testgasse 1",
            "postal_code": "1010",
            "city": "Wien",
            "accept_terms": True,
            "accept_privacy": True,
            "ack_withdrawal": True,
            "license_seats": 1,
        },
    )
    assert create.status_code == 200, create.text
    acc = create.json()
    assert acc["customer_type"] == "b2c"
    assert acc["vat_id"] is None

    # B2C darf keine UID setzen
    reject_vat = client.post(
        "/api/commerce/accounts",
        headers=headers,
        json={
            "customer_type": "b2c",
            "contact_name": "X",
            "billing_email": "x@example.com",
            "vat_id": "ATU12345678",
            "accept_terms": True,
            "accept_privacy": True,
            "ack_withdrawal": True,
        },
    )
    assert reject_vat.status_code == 400

    sub = client.post(
        f"/api/commerce/accounts/{acc['id']}/subscribe",
        headers=headers,
        json={"plan_code": "pkw_basic", "force_vies_stub": True},
    )
    assert sub.status_code == 200, sub.text
    body = sub.json()
    assert body["invoice"]["tax_scenario"] == "b2c_at"
    assert body["invoice"]["gross_cents"] == body["invoice"]["net_cents"] + body["invoice"]["vat_cents"]
    inv_id = body["invoice"]["id"]

    dl = client.get(f"/api/commerce/invoices/{inv_id}/download", headers=headers)
    assert dl.status_code == 200
    assert dl.headers.get("content-disposition", "").endswith('.json"') or "json" in dl.headers.get(
        "content-disposition", ""
    )

    cancel = client.post(
        f"/api/commerce/accounts/{acc['id']}/cancel",
        headers=headers,
        json={"at_period_end": True},
    )
    assert cancel.status_code == 200
    assert cancel.json()["subscription"]["cancel_at_period_end"] is True


def test_b2b_account_with_vies_and_reverse_charge_preview(client: TestClient):
    headers = _login(client)
    create = client.post(
        "/api/commerce/accounts",
        headers=headers,
        json={
            "customer_type": "b2b",
            "contact_name": "Anna Admin",
            "billing_email": "billing@firma-de.example",
            "company_name": "Demo Firma DE GmbH",
            "legal_form": "GmbH",
            "vat_id": "DE123456789",
            "country": "DE",
            "accept_terms": True,
            "accept_privacy": True,
            "license_seats": 3,
        },
    )
    assert create.status_code == 200, create.text
    acc = create.json()
    assert acc["vat_status"] == "valid"

    sub = client.post(
        f"/api/commerce/accounts/{acc['id']}/subscribe",
        headers=headers,
        json={"plan_code": "pkw_basic", "force_vies_stub": True},
    )
    assert sub.status_code == 200, sub.text
    inv = sub.json()["invoice"]
    assert inv["tax_scenario"] == "b2b_reverse_charge"
    assert inv["reverse_charge"] is True
    assert inv["vat_cents"] == 0

    cn = client.post(
        f"/api/commerce/invoices/{inv['id']}/credit-note",
        headers=headers,
        json={"reason_de": "Testgutschrift"},
    )
    assert cn.status_code == 200
    assert cn.json()["doc_type"] == "credit_note"
    assert cn.json()["gross_cents"] < 0


def test_b2b_requires_company_and_vat(client: TestClient):
    headers = _login(client)
    res = client.post(
        "/api/commerce/accounts",
        headers=headers,
        json={
            "customer_type": "b2b",
            "contact_name": "X",
            "billing_email": "x@example.com",
            "accept_terms": True,
            "accept_privacy": True,
        },
    )
    assert res.status_code == 400
