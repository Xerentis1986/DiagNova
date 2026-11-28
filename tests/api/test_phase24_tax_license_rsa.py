"""Phase 24 – Steuer-Szenarien + asymmetrische Offline-Lizenz (RSA)."""

from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from app.services.commerce.tax_engine import resolve_tax
from app.services import license_crypto
from app.core.config import get_settings


def test_tax_scenarios_at_eu_third_rc_oss_uid():
    # AT B2C
    at_c = resolve_tax(customer_type="b2c", customer_country="AT", net_cents=10000)
    assert at_c["scenario"] == "b2c_at"
    assert at_c["vat_rate_bp"] > 0
    assert at_c["review_status"] == "draft_needs_review"

    # AT B2B
    at_b = resolve_tax(customer_type="b2b", customer_country="AT", net_cents=10000)
    assert at_b["scenario"] == "b2b_at"

    # EU B2B reverse charge with valid UID
    rc = resolve_tax(
        customer_type="b2b",
        customer_country="DE",
        vat_id="DE123",
        vat_valid=True,
        net_cents=10000,
    )
    assert rc["scenario"] == "b2b_reverse_charge"
    assert rc["reverse_charge"] is True
    assert rc["vat_cents"] == 0

    # EU B2B without UID
    uid = resolve_tax(customer_type="b2b", customer_country="DE", vat_valid=False, net_cents=10000)
    assert uid["scenario"] == "b2b_eu_uid_required"

    # B2C EU OSS
    oss = resolve_tax(customer_type="b2c", customer_country="DE", net_cents=10000)
    assert oss["scenario"] == "b2c_eu_oss"
    assert oss["oss_applicable"] is True

    # Drittland
    third = resolve_tax(customer_type="b2c", customer_country="US", net_cents=10000)
    assert third["scenario"] == "third_country"
    assert third["vat_cents"] == 0

    for row in (at_c, at_b, rc, uid, oss, third):
        assert row["legal_review_required"] is True or row["review_status"] == "draft_needs_review"


def test_tax_preview_api(client: TestClient, auth_headers: dict[str, str]):
    r = client.post(
        "/api/commerce/tax/preview",
        headers=auth_headers,
        json={
            "customer_type": "b2b",
            "customer_country": "DE",
            "vat_id": "DE123",
            "vat_valid": True,
            "net_cents": 5000,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["scenario"] == "b2b_reverse_charge"
    assert body["review_status"] == "draft_needs_review"


def test_rsa_offline_token_roundtrip(client: TestClient, auth_headers: dict[str, str]):
    assert license_crypto.public_key_pem()
    r = client.post(
        "/api/billing/licenses/offline-token",
        headers=auth_headers,
        json={"device_fingerprint": "dev_phase24_rsa_device", "valid_hours": 2},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("algorithm") == "RSA-SHA256-PKCS1v15"
    assert body.get("signature_encoding") == "base64"
    payload = body["payload"]
    sig = body["signature"]
    assert license_crypto.verify_payload(payload, sig) is True
    # Fälschung
    assert license_crypto.verify_payload(payload, base64.b64encode(b"x" * 256).decode()) is False


def test_commerce_overview_still_draft(client: TestClient, auth_headers: dict[str, str]):
    st = client.get("/api/commerce/overview", headers=auth_headers)
    assert st.status_code == 200
    assert st.json().get("tax_review_status") == "draft_needs_review"
