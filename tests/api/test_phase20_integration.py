"""Phase 20: Integrations-Smoke nach Merge Phase 18+19 – ohne Flash/HW-Schreiben."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_reports_versions(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["data_source_default"] == "simulated"
    assert body["demo_mode"] is True
    assert "version" in body
    assert body["components"]["api"] == body["version"]
    assert set(body["components"]) >= {"api", "web", "connector"}


def test_dashboard_planned_modules_unique_and_include_tuning_lkw(
    client: TestClient, auth_headers: dict[str, str]
):
    res = client.get("/api/dashboard", headers=auth_headers)
    assert res.status_code == 200
    modules = res.json()["planned_modules"]
    ids = [m["id"] for m in modules]
    assert len(ids) == len(set(ids)), f"doppelte planned_modules: {ids}"
    assert "chiptuning" in ids
    assert "lkw" in ids
    assert "flash" in ids


def test_tuning_and_lkw_architecture_coexist(client: TestClient, auth_headers: dict[str, str]):
    tuning = client.get("/api/tuning/status", headers=auth_headers)
    assert tuning.status_code == 200, tuning.text
    t = tuning.json()
    assert t["productive_activation_locked"] is True
    assert t["map_change_available"] is False
    assert t["flash_available"] is False

    lkw = client.get("/api/lkw/architecture", headers=auth_headers)
    assert lkw.status_code == 200, lkw.text
    arch = lkw.json()
    assert arch["phase"] == 19
    assert arch.get("status") in {
        "planned",
        "architecture",
        "documented_prep",
        "geplant",
        "planned_disabled",
    }

    caps = client.get("/api/lkw/capabilities", headers=auth_headers)
    assert caps.status_code == 200
    assert caps.json()["diagnosis_enabled"] is False


def test_lkw_diagnosis_posts_forbidden(client: TestClient, auth_headers: dict[str, str]):
    for path in (
        "/api/lkw/diagnose",
        "/api/lkw/j1939/read",
        "/api/lkw/rp1210/connect",
    ):
        res = client.post(path, headers=auth_headers, json={})
        assert res.status_code == 403, (path, res.status_code, res.text)


def test_tuning_activation_and_flash_forbidden(client: TestClient, auth_headers: dict[str, str]):
    code = "demo_baseline_review"
    for suffix in ("activate", "map-change", "flash"):
        res = client.post(f"/api/tuning/operations/{code}/{suffix}", headers=auth_headers, json={})
        assert res.status_code == 403, (suffix, res.status_code, res.text)


def test_coding_flash_still_disabled(client: TestClient, auth_headers: dict[str, str]):
    catalog = client.get("/api/coding/catalog", headers=auth_headers)
    assert catalog.status_code == 200
    body = catalog.json()
    assert body.get("flash_available") in (False, None)
    if "live_execution_available" in body:
        assert body["live_execution_available"] is False
