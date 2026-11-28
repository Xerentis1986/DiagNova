"""Phase 23 – Live-Bridge E2E: API + echter Connector-Prozess + Fake-Adapter.

Kein physisches Fahrzeug. SSRF: nur Loopback. Auth: CONNECTOR_TOKEN.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


REPO = Path(__file__).resolve().parents[2]
CONNECTOR_PROJ = REPO / "apps" / "windows-connector" / "DiagNova.Connector" / "DiagNova.Connector.csproj"
E2E_TOKEN = "phase23-e2e-connector-token-local-only"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {E2E_TOKEN}", "Accept": "application/json"}


def _wait_http(url: str, timeout: float = 90.0) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            r = httpx.get(url, headers=_headers(), timeout=1.5)
            if r.status_code == 200:
                return
            last = r.status_code
        except Exception as exc:  # noqa: BLE001
            last = exc
        time.sleep(0.4)
    raise RuntimeError(f"Connector nicht bereit: {url} last={last}")


@pytest.fixture(scope="module")
def connector_proc():
    if not CONNECTOR_PROJ.is_file():
        pytest.skip("Connector-Projekt fehlt")
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["DIAGNOVA_CONNECTOR_URL"] = url
    env["DIAGNOVA_DEVICE_ID"] = "dev_phase23_e2e_connector"
    env["CONNECTOR_TOKEN"] = E2E_TOKEN
    env["ASPNETCORE_ENVIRONMENT"] = "Development"
    cmd = [
        "dotnet",
        "run",
        "--project",
        str(CONNECTOR_PROJ),
        "-c",
        "Release",
        "--no-launch-profile",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(CONNECTOR_PROJ.parent.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        _wait_http(f"{url}/health", timeout=90.0)
        yield {"url": url, "proc": proc, "port": port, "token": E2E_TOKEN}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_connector_health_and_fake_adapter(connector_proc):
    base = connector_proc["url"]
    h = httpx.get(f"{base}/health", headers=_headers(), timeout=5.0)
    assert h.status_code == 200
    v = httpx.get(f"{base}/version", headers=_headers(), timeout=5.0)
    assert v.status_code == 200

    fake = httpx.post(f"{base}/adapter/connect/fake", headers=_headers(), timeout=10.0)
    assert fake.status_code == 200
    body = fake.json()
    blob = json.dumps(body).lower()
    assert "fake" in blob or body.get("data_source") == "adapter_fake"

    init = httpx.post(f"{base}/obd/init", headers=_headers(), timeout=15.0)
    assert init.status_code == 200, init.text

    live = httpx.get(f"{base}/obd/live", headers=_headers(), timeout=15.0)
    assert live.status_code == 200, live.text
    live_j = live.json()
    assert live_j.get("data_source") == "adapter_fake"

    dtcs = httpx.get(f"{base}/obd/dtcs", headers=_headers(), timeout=10.0)
    assert dtcs.status_code == 200


def test_bridge_live_via_api(client: TestClient, auth_headers: dict[str, str], connector_proc, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "connector_base_url", connector_proc["url"])
    monkeypatch.setattr(s, "connector_url_allowlist", "127.0.0.1,localhost")
    monkeypatch.setattr(s, "connector_bearer_token", E2E_TOKEN)

    cf = client.post("/api/connector/connect-fake", headers=auth_headers)
    assert cf.status_code == 200, cf.text

    br = client.get("/api/connector/bridge-status", headers=auth_headers)
    assert br.status_code == 200
    assert br.json()["connector"]["reachable"] is True

    vehicles = client.get("/api/vehicles", headers=auth_headers)
    assert vehicles.status_code == 200 and vehicles.json()
    vid = vehicles.json()[0]["id"]

    init = client.post("/api/connector/obd-init?mode=live", headers=auth_headers)
    assert init.status_code == 200, init.text

    live = client.get(f"/api/diagnostics/{vid}/live?mode=live", headers=auth_headers)
    assert live.status_code == 200, live.text
    assert live.json()["data_source"] == "live"

    monkeypatch.setattr(s, "connector_base_url", "http://example.com:8765")
    bad = client.get("/api/connector/bridge-status", headers=auth_headers)
    assert bad.status_code == 200
    assert bad.json()["connector"].get("reachable") is False
