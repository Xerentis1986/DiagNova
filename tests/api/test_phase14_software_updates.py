"""Phase 14: Software-/Connector-Updates – Signatur, Kompatibilität, Busy, Rollback."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.models.entities import DiagnosticSession, Vehicle
from app.models.software_updates import SoftwareComponent


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_dashboard_and_separation_from_data_updates(client: TestClient, auth_headers: dict[str, str]):
    dash = client.get("/api/software-updates/dashboard", headers=auth_headers)
    assert dash.status_code == 200, dash.text
    body = dash.json()
    assert body["auto_install_enabled"] is False
    assert body["productive_auto_updates_blocked"] is True
    assert body["signing_cert_configured"] is False
    keys = {c["key"] for c in body["components"]}
    assert keys == {"api", "web", "connector"}
    assert "data-updates" in body["data_updates_note_de"] or "data-updates" in body["data_updates_note_de"].lower() or "Diagnosedaten" in body["data_updates_note_de"]

    # Daten-Updates bleiben erreichbar und getrennt
    data = client.get("/api/data-updates/dashboard", headers=auth_headers)
    assert data.status_code == 200

    ver = client.get("/version")
    assert ver.status_code == 200
    assert ver.json()["api"] == "0.14.0"


def test_reject_tampered_package(client: TestClient, auth_headers: dict[str, str]):
    res = client.post(
        "/api/software-updates/packages/ingest",
        headers=auth_headers,
        json={
            "channel_key": "stable-fixture",
            "fixture_name": "phase14_web_0.14.1.json",
            "tamper": True,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "rejected"
    assert body["error_de"]
    assert "Checksum" in body["error_de"] or "Signatur" in body["error_de"] or "abgelehnt" in body["error_de"].lower()


def test_reject_incompatible_version(client: TestClient, auth_headers: dict[str, str]):
    check = client.post(
        "/api/software-updates/compatibility/check",
        headers=auth_headers,
        json={"component": "web", "version": "0.15.0"},
    )
    assert check.status_code == 200
    assert check.json()["compatible"] is False
    assert check.json()["violations"]

    res = client.post(
        "/api/software-updates/packages/ingest",
        headers=auth_headers,
        json={
            "channel_key": "stable-fixture",
            "fixture_name": "phase14_web_0.15.0_incompat.json",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "rejected"
    assert "Inkompatibel" in (body["error_de"] or "") or "inkompatibel" in (body["error_de"] or "").lower()


def test_production_channel_blocked_without_cert(client: TestClient, auth_headers: dict[str, str]):
    res = client.post(
        "/api/software-updates/packages/ingest",
        headers=auth_headers,
        json={
            "channel_key": "production-blocked",
            "fixture_name": "phase14_web_0.14.1.json",
        },
    )
    # Kanal disabled → 400, oder enabled aber cert → rejected
    assert res.status_code in (200, 400), res.text
    if res.status_code == 200:
        assert res.json()["status"] == "rejected"
        assert "zertifikat" in (res.json()["error_de"] or "").lower()
    else:
        detail = str(res.json().get("detail", "")).lower()
        assert "deaktiviert" in detail or "zertifikat" in detail


def test_approve_install_and_rollback(client: TestClient, auth_headers: dict[str, str]):
    ingest = client.post(
        "/api/software-updates/packages/ingest",
        headers=auth_headers,
        json={
            "channel_key": "stable-fixture",
            "fixture_name": "phase14_web_0.14.1.json",
        },
    )
    assert ingest.status_code == 200, ingest.text
    pkg = ingest.json()
    assert pkg["status"] == "awaiting_approval"
    pkg_id = pkg["id"]

    run = client.post(
        f"/api/software-updates/packages/{pkg_id}/approve",
        headers=auth_headers,
        json={},
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["status"] == "succeeded"
    assert body["to_version"] == "0.14.1"
    assert body["healthcheck_ok"] is True

    comps = client.get("/api/software-updates/components", headers=auth_headers)
    web = next(c for c in comps.json() if c["key"] == "web")
    assert web["current_version"] == "0.14.1"
    assert web["previous_version"] == "0.14.0"

    rb = client.post(
        "/api/software-updates/components/web/rollback",
        headers=auth_headers,
    )
    assert rb.status_code == 200, rb.text
    assert rb.json()["status"] == "succeeded"
    assert rb.json()["to_version"] == "0.14.0"


def test_healthcheck_fail_triggers_rollback(client: TestClient, auth_headers: dict[str, str]):
    ingest = client.post(
        "/api/software-updates/packages/ingest",
        headers=auth_headers,
        json={
            "channel_key": "stable-fixture",
            "fixture_name": "phase14_connector_0.14.1.json",
        },
    )
    assert ingest.status_code == 200, ingest.text
    pkg_id = ingest.json()["id"]

    run = client.post(
        f"/api/software-updates/packages/{pkg_id}/approve",
        headers=auth_headers,
        json={"force_healthcheck_fail": True},
    )
    assert run.status_code == 200, run.text
    body = run.json()
    assert body["status"] == "rolled_back"
    assert body["healthcheck_ok"] is False

    comps = client.get("/api/software-updates/components", headers=auth_headers)
    conn = next(c for c in comps.json() if c["key"] == "connector")
    assert conn["current_version"] == "0.14.0"


def test_busy_blocks_install_during_diagnosis(client: TestClient, auth_headers: dict[str, str]):
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).first()
        assert vehicle is not None
        # Admin-User id aus Token-Login
        me = client.get("/api/auth/me", headers=auth_headers)
        user_id = me.json()["id"]
        session = DiagnosticSession(
            vehicle_id=vehicle.id,
            user_id=user_id,
            workshop_id=vehicle.workshop_id,
            status="open",
            data_source="simulated",
        )
        db.add(session)
        db.commit()
        session_id = session.id
    finally:
        db.close()

    ingest = client.post(
        "/api/software-updates/packages/ingest",
        headers=auth_headers,
        json={
            "channel_key": "stable-fixture",
            "fixture_name": "phase14_web_0.14.1.json",
        },
    )
    assert ingest.status_code == 200
    # Falls vorheriger Test bereits 0.14.1 installed hat, Version ggf. ok – awaiting oder rejected
    if ingest.json()["status"] != "awaiting_approval":
        # Noch einmal mit connector, der ggf. noch auf 0.14.0 ist
        ingest = client.post(
            "/api/software-updates/packages/ingest",
            headers=auth_headers,
            json={
                "channel_key": "stable-fixture",
                "fixture_name": "phase14_connector_0.14.1.json",
            },
        )
    assert ingest.json()["status"] == "awaiting_approval", ingest.text
    pkg_id = ingest.json()["id"]

    busy = client.get("/api/software-updates/busy", headers=auth_headers)
    assert busy.status_code == 200
    assert busy.json()["allowed"] is False

    run = client.post(
        f"/api/software-updates/packages/{pkg_id}/approve",
        headers=auth_headers,
        json={},
    )
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "blocked_busy"

    # Cleanup Sitzung
    db = SessionLocal()
    try:
        s = db.get(DiagnosticSession, session_id)
        if s:
            s.status = "closed"
            db.add(s)
            db.commit()
    finally:
        db.close()


def test_technician_forbidden(client: TestClient):
    tech = _login(client, "tech@example.com", "TechDemo123!")
    dash = client.get("/api/software-updates/dashboard", headers=tech)
    assert dash.status_code == 403


def test_installer_docs(client: TestClient, auth_headers: dict[str, str]):
    docs = client.get("/api/software-updates/installer-docs", headers=auth_headers)
    assert docs.status_code == 200
    body = docs.json()
    assert body["auto_update_blocked"] is True
    assert body["install_steps_de"]
    assert body["uninstall_steps_de"]
