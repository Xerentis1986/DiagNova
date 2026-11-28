"""Connector setup-guide + LIVE-Assistent (Kunden-Frontend API)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_setup_guide_requires_auth(client: TestClient):
    assert client.get("/api/connector/setup-guide").status_code == 401


def test_setup_guide_legal_and_unsigned(client: TestClient, auth_headers: dict[str, str]):
    r = client.get("/api/connector/setup-guide", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["signing"] == "UNSIGNED"
    assert "Darknet" in body["legal_notice_de"] or "Raubkopien" in body["legal_notice_de"]
    assert body["installer"]["filename"].endswith("-unsigned.exe")
    assert len(body["installer"]["sha256"]) == 64
    assert body["install_steps_de"]
    assert body["pairing_steps_de"]
    assert body["live_checklist"]
    assert "/operator" in body["ui_separation_de"]
    assert "Vgate" in " ".join(a["label_de"] for a in body["adapters"])


def test_live_assistant_no_demo_fallback_message(client: TestClient, auth_headers: dict[str, str]):
    r = client.get("/api/connector/live-assistant?mode=live", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "live"
    assert body["steps"]
    ids = {s["id"] for s in body["steps"]}
    assert "connector_running" in ids
    assert "live_mode" in ids
    assert "obd_basics" in ids
    live_step = next(s for s in body["steps"] if s["id"] == "live_mode")
    assert live_step["auto_ok"] is True
    # Ohne Connector: reachable false, kein stiller DEMO-Fallback
    conn_step = next(s for s in body["steps"] if s["id"] == "connector_running")
    assert conn_step["auto_ok"] is False
    assert "DEMO-Fallback" in (conn_step["status_de"] + body["message_de"]) or "nicht erreichbar" in conn_step[
        "status_de"
    ].lower() or "nicht erreichbar" in str(body.get("connector", {})).lower()


def test_live_assistant_demo_mode_flag(client: TestClient):
    tech = _login(client, "tech@example.com", "TechDemo123!")
    r = client.get("/api/connector/live-assistant?mode=demo", headers=tech)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo"
    live_step = next(s for s in body["steps"] if s["id"] == "live_mode")
    assert live_step["auto_ok"] is False
