"""Automotive-Quellenkatalog – Summary, Suche, Fixture-Paket."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_catalog_summary(client: TestClient, auth_headers: dict):
    r = client.get("/api/automotive-catalog/summary", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source_count"] == 447
    assert body["write_diag_flash"] == "gesperrt"
    assert body["secrets_in_repo"] is False
    assert body["obdex_sample_dtcs"] == 200


def test_catalog_sources_search(client: TestClient, auth_headers: dict):
    r = client.get("/api/automotive-catalog/sources?q=OBDex&limit=10", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert any("OBDex" in str(i.get("name")) for i in body["items"])


def test_fixture_package_shape(client: TestClient, auth_headers: dict):
    r = client.get("/api/automotive-catalog/fixtures/import-package", headers=auth_headers)
    assert r.status_code == 200
    pkg = r.json()
    assert pkg["schema_version"] == "diagnova.diagnostic-import.v1"
    assert pkg["source_key"] == "obdex-cc0"
    assert len(pkg["dtcs"]) == 200
    assert len(pkg["pids"]) >= 10
    assert all(d.get("data_scope") == "generic" for d in pkg["dtcs"][:5])


def test_import_preview_obdex_sample(client: TestClient, auth_headers: dict):
    r = client.post("/api/automotive-catalog/fixtures/import-preview", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "batch_id" in body
    assert body["status"] in {"preview", "ready", "quarantined", "rejected"} or "can_apply" in body


def test_probe_requires_platform_admin(client: TestClient):
    tech = client.post(
        "/api/auth/login",
        json={"email": "tech@example.com", "password": "TechDemo123!"},
    )
    assert tech.status_code == 200
    th = {"Authorization": f"Bearer {tech.json()['access_token']}"}
    r = client.post("/api/automotive-catalog/probe?live=false", headers=th)
    assert r.status_code == 403
