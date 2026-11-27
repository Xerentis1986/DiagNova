"""Phase 07: Scheduler-Pipeline, SSRF, Signatur, Staging, Freigabe, Rollback."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from app.models.data_updates import UpdateChannel
from app.services.data_updates.ssrf import SsrfBlocked, validate_https_url

FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "app"
    / "data"
    / "fixtures"
)


def _db(client):
    from app.db.session import SessionLocal

    return SessionLocal()


def test_ssrf_blocks_http_and_localhost():
    with pytest.raises(SsrfBlocked):
        validate_https_url("http://example.com/x")
    with pytest.raises(SsrfBlocked):
        validate_https_url("https://localhost/secret")
    with pytest.raises(SsrfBlocked):
        validate_https_url("https://127.0.0.1/x")
    with pytest.raises(SsrfBlocked):
        validate_https_url("https://192.168.1.1/x")
    # öffentliche Hosts ohne Auth-User ok (DNS darf unresolved sein)
    ok = validate_https_url("https://example.com/path", allow_unresolved=True)
    assert ok.startswith("https://")


def test_dashboard_admin_only(client, auth_headers):
    res = client.get("/api/data-updates/dashboard", headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["scheduler_enabled"] is False
    assert body["default_interval_hours"] == 24
    keys = {c["key"] for c in body["channels"]}
    assert "sim-dtc-descriptive" in keys
    assert "https-placeholder-disabled" in keys
    https = next(c for c in body["channels"] if c["key"] == "https-placeholder-disabled")
    assert https["enabled"] is False
    assert https["rights_verified"] is False


def test_tech_forbidden_on_updates(client):
    login = client.post(
        "/api/auth/login",
        json={"email": "tech@example.com", "password": "TechDemo123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    res = client.get("/api/data-updates/dashboard", headers=headers)
    assert res.status_code == 403


def test_new_version_auto_publish_and_rollback(client, auth_headers):
    # Manueller Lauf mit force (Kanal standardmäßig disabled)
    run = client.post(
        "/api/data-updates/channels/sim-dtc-descriptive/run",
        headers=auth_headers,
        json={"force": True},
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["status"] == "published", body
    assert body["signature_ok"] is True
    assert body["version_label"] == "phase07-sim-new-v1"
    run_id = body["id"]

    dtc = client.get("/api/diagnostic-data/dtcs/P0301", headers=auth_headers)
    assert dtc.status_code == 200
    # Nach Auto-Publish: simulierter Demo-Text (klar gekennzeichnet)
    assert "Simuliert" in dtc.json()["description_de"] or dtc.json()["description_status"] == "known"

    rb = client.post(f"/api/data-updates/runs/{run_id}/rollback", headers=auth_headers)
    assert rb.status_code == 200, rb.text
    assert rb.json()["status"] == "rolled_back"


def test_same_version_skipped(client, auth_headers):
    first = client.post(
        "/api/data-updates/channels/sim-dtc-descriptive/run",
        headers=auth_headers,
        json={"force": True},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "published"

    second = client.post(
        "/api/data-updates/channels/sim-dtc-descriptive/run",
        headers=auth_headers,
        json={"force": False},
    )
    # Kanal noch disabled → failed ohne force
    assert second.status_code == 200
    assert second.json()["status"] == "failed"
    assert "deaktiviert" in (second.json()["error_de"] or "").lower()

    # Aktivieren und erneut → same hash skip
    patch = client.patch(
        "/api/data-updates/channels/sim-dtc-descriptive",
        headers=auth_headers,
        json={"enabled": True},
    )
    assert patch.status_code == 200

    third = client.post(
        "/api/data-updates/channels/sim-dtc-descriptive/run",
        headers=auth_headers,
        json={"force": False},
    )
    assert third.status_code == 200, third.text
    assert third.json()["status"] == "skipped"
    assert third.json()["summary"].get("reason") in ("same_hash", "not_modified")


def test_broken_schema_rejected(client, auth_headers):
    db = _db(client)
    ch = db.scalar(select(UpdateChannel).where(UpdateChannel.key == "sim-dtc-descriptive"))
    assert ch is not None
    ch.url = "fixture://phase07_update_broken.json"
    ch.require_signature = False
    ch.last_content_hash = None
    ch.last_etag = None
    db.commit()
    db.close()

    run = client.post(
        "/api/data-updates/channels/sim-dtc-descriptive/run",
        headers=auth_headers,
        json={"force": True},
    )
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "failed"
    assert body["error_de"]


def test_license_change_awaits_approval(client, auth_headers):
    db = _db(client)
    ch = db.scalar(select(UpdateChannel).where(UpdateChannel.key == "sim-dtc-descriptive"))
    assert ch is not None
    ch.url = "fixture://phase07_update_license_changed.json"
    ch.require_signature = False
    ch.last_content_hash = None
    ch.last_etag = None
    db.commit()
    db.close()

    run = client.post(
        "/api/data-updates/channels/sim-dtc-descriptive/run",
        headers=auth_headers,
        json={"force": True},
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["status"] == "awaiting_approval"
    assert body["license_changed"] is True
    run_id = body["id"]

    approved = client.post(f"/api/data-updates/runs/{run_id}/approve", headers=auth_headers)
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "published"


def test_procedures_require_manual_approval(client, auth_headers):
    run = client.post(
        "/api/data-updates/channels/sim-procedures/run",
        headers=auth_headers,
        json={"force": True},
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["status"] == "awaiting_approval"

    rejected = client.post(
        f"/api/data-updates/runs/{body['id']}/reject",
        headers=auth_headers,
        json={"reason_de": "Testablehnung"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "failed"


def test_addresses_require_manual_approval(client, auth_headers):
    run = client.post(
        "/api/data-updates/channels/sim-ecu-addresses/run",
        headers=auth_headers,
        json={"force": True},
    )
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "awaiting_approval"


def test_https_without_rights_blocked(client, auth_headers):
    run = client.post(
        "/api/data-updates/channels/https-placeholder-disabled/run",
        headers=auth_headers,
        json={"force": True},
    )
    assert run.status_code == 200
    assert run.json()["status"] == "failed"
    assert "Rechte" in (run.json()["error_de"] or "")


def test_https_enable_requires_rights(client, auth_headers):
    res = client.patch(
        "/api/data-updates/channels/https-placeholder-disabled",
        headers=auth_headers,
        json={"enabled": True},
    )
    assert res.status_code == 400


def test_network_error_with_mock_transport(client, auth_headers):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated network failure", request=request)

    transport = httpx.MockTransport(handler)
    mock_client = httpx.Client(transport=transport)

    from app.db.session import SessionLocal
    from app.services.data_updates.pipeline import run_channel_update

    db = SessionLocal()
    ch = db.scalar(select(UpdateChannel).where(UpdateChannel.key == "https-placeholder-disabled"))
    assert ch is not None
    ch.rights_verified = True
    ch.enabled = True
    ch.url = "https://example.com/diagnova-update.json"
    db.commit()

    run = run_channel_update(
        db,
        ch,
        trigger="manual",
        force=True,
        http_client=mock_client,
    )
    assert run.status == "failed"
    assert run.error_de and ("Netz" in run.error_de or "Connect" in run.error_de or "HTTP" in run.error_de)
    db.close()
    mock_client.close()


def test_parallel_lock(client, auth_headers):
    from app.db.session import SessionLocal
    from app.services.data_updates.scheduler import acquire_job_lock, release_job_lock

    db = SessionLocal()
    assert acquire_job_lock(db, holder="test-a") is True
    assert acquire_job_lock(db, holder="test-b") is False
    release_job_lock(db, holder="test-a")
    assert acquire_job_lock(db, holder="test-b") is True
    release_job_lock(db, holder="test-b")
    db.close()


def test_ssrf_check_endpoint(client, auth_headers):
    bad = client.post(
        "/api/data-updates/ssrf-check",
        headers=auth_headers,
        json={"url": "http://evil.example/x"},
    )
    assert bad.status_code == 200
    assert bad.json()["ok"] is False

    good = client.post(
        "/api/data-updates/ssrf-check",
        headers=auth_headers,
        json={"url": "https://example.com/data.json"},
    )
    assert good.status_code == 200
    assert good.json()["ok"] is True


def test_coverage_mentions_phase07(client, auth_headers):
    res = client.get("/api/diagnostic-data/coverage", headers=auth_headers)
    assert res.json()["phase_07"] == "implemented_simulated"


def test_fixture_file_exists():
    assert (FIXTURES / "phase07_update_new.json").is_file()
    data = json.loads((FIXTURES / "phase07_update_new.json").read_text(encoding="utf-8"))
    assert data["dataset_version_label"] == "phase07-sim-new-v1"
