"""Phase 24 – Portable Connector Install/Start/API/Stop E2E (Linux).

Windows Inno Install/Uninstall: CI-Artefakt vorhanden; Uninstall-Pfad NOT TESTED hier.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parents[2]
CONNECTOR_PROJ = REPO / "apps" / "windows-connector" / "DiagNova.Connector" / "DiagNova.Connector.csproj"
TOKEN = "phase24-portable-install-token"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_portable_install_start_probe_stop(tmp_path: Path):
    if not CONNECTOR_PROJ.is_file():
        pytest.skip("Connector fehlt")

    install_dir = tmp_path / "DiagNovaConnector"
    install_dir.mkdir()
    # „Install“: publish into target dir (portable)
    pub = subprocess.run(
        [
            "dotnet",
            "publish",
            str(CONNECTOR_PROJ),
            "-c",
            "Release",
            "-o",
            str(install_dir),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert pub.returncode == 0, pub.stdout + pub.stderr
    dll = install_dir / "DiagNova.Connector.dll"
    assert dll.is_file()

    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["DIAGNOVA_CONNECTOR_URL"] = url
    env["CONNECTOR_TOKEN"] = TOKEN
    env["DIAGNOVA_DEVICE_ID"] = "dev_phase24_portable"
    proc = subprocess.Popen(
        ["dotnet", str(dll)],
        cwd=str(install_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        deadline = time.time() + 60
        last = None
        while time.time() < deadline:
            try:
                r = httpx.get(f"{url}/health", headers=headers, timeout=1.5)
                if r.status_code == 200:
                    break
                last = r.status_code
            except Exception as exc:  # noqa: BLE001
                last = exc
            time.sleep(0.4)
        else:
            raise RuntimeError(f"Connector start failed: {last}")

        probe = httpx.get(f"{url}/hardware/probe", headers=headers, timeout=10)
        assert probe.status_code == 200
        body = probe.json()
        assert body.get("schema") == "diagnova.hardware_probe.v1"
        assert body.get("flash_attempted") is False
        assert "delphi_cdp" in body and "obd_diag" in body

        fake = httpx.post(f"{url}/adapter/connect/fake", headers=headers, timeout=10)
        assert fake.status_code == 200
        init = httpx.post(f"{url}/obd/init", headers=headers, timeout=15)
        assert init.status_code == 200
        live = httpx.get(f"{url}/obd/live", headers=headers, timeout=15)
        assert live.status_code == 200
        assert live.json().get("data_source") == "adapter_fake"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
        # „Uninstall“ portable: remove install dir
        shutil.rmtree(install_dir, ignore_errors=True)
        assert not install_dir.exists()
