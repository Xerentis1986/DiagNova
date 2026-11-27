"""Phase 06: Diagnosedatenbank, Lookup, Import/Quarantäne/Rollback."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURES = (
    Path(__file__).resolve().parents[2]
    / "apps"
    / "api"
    / "app"
    / "data"
    / "fixtures"
)


def test_sources_seeded_with_license_fields(client, auth_headers):
    res = client.get("/api/diagnostic-data/sources", headers=auth_headers)
    assert res.status_code == 200
    keys = {s["key"] for s in res.json()}
    assert "diagnova-structural" in keys
    assert "dtc-descriptions-unavailable" in keys
    assert "odx-pdx-placeholder" in keys
    blocked = next(s for s in res.json() if s["key"] == "dtc-descriptions-unavailable")
    assert blocked["redistributable"] is False
    assert blocked["commercial_use"] == "prohibited"


def test_baseline_pids_and_ecus_with_provenance(client, auth_headers):
    pids = client.get("/api/diagnostic-data/pids", headers=auth_headers)
    assert pids.status_code == 200
    body = pids.json()
    assert len(body) >= 9
    assert all(p["provenance"]["source_key"] for p in body)
    assert any(p["pid_hex"] == "0C" for p in body)

    ecus = client.get("/api/diagnostic-data/ecus", headers=auth_headers)
    assert ecus.status_code == 200
    addrs = {(e["request_address"], e["response_address"]) for e in ecus.json()}
    assert ("7E0", "7E8") in addrs
    assert ("7E1", "7E9") in addrs
    assert all(e["verified"] for e in ecus.json())


def test_unknown_dtc_shows_unbekannt(client, auth_headers):
    # Code in Baseline ohne Beschreibung
    known_code = client.get("/api/diagnostic-data/dtcs/P0301", headers=auth_headers)
    assert known_code.status_code == 200
    data = known_code.json()
    assert data["code"] == "P0301"
    assert data["description_de"] == "unbekannt"
    assert data["description_status"] == "unknown"

    # Komplett unbekannter Code
    missing = client.get("/api/diagnostic-data/dtcs/P9999", headers=auth_headers)
    assert missing.status_code == 200
    assert missing.json()["known"] is False
    assert missing.json()["description_de"] == "unbekannt"


def test_json_import_preview_apply_rollback(client, auth_headers):
    payload = json.loads((FIXTURES / "phase06_sample_valid.json").read_text(encoding="utf-8"))
    preview = client.post("/api/diagnostic-data/import/preview", headers=auth_headers, json=payload)
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["can_apply"] is True
    assert body["status"] == "preview"
    batch_id = body["batch_id"]

    applied = client.post(f"/api/diagnostic-data/import/{batch_id}/apply", headers=auth_headers)
    assert applied.status_code == 200, applied.text
    assert applied.json()["status"] == "applied"
    assert applied.json()["applied_count"] > 0

    # DTC aus Import – weiterhin unbekannt (kein Text)
    dtc = client.get("/api/diagnostic-data/dtcs/P0500", headers=auth_headers)
    assert dtc.json()["description_de"] == "unbekannt"
    assert dtc.json()["known"] is True

    mfrs = client.get("/api/diagnostic-data/manufacturers", headers=auth_headers)
    assert any(m["slug"] == "vw" for m in mfrs.json())
    assert all(m["provenance"]["source_key"] for m in mfrs.json())

    rb = client.post(f"/api/diagnostic-data/import/{batch_id}/rollback", headers=auth_headers)
    assert rb.status_code == 200
    assert rb.json()["status"] == "rolled_back"

    mfrs_after = client.get("/api/diagnostic-data/manufacturers", headers=auth_headers)
    assert not any(m["slug"] == "vw" for m in mfrs_after.json())


def test_blocked_bosch_source_rejected(client, auth_headers):
    payload = json.loads((FIXTURES / "phase06_sample_invalid.json").read_text(encoding="utf-8"))
    res = client.post("/api/diagnostic-data/import/preview", headers=auth_headers, json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "rejected"
    assert body["can_apply"] is False
    assert "Bosch" in body["message_de"] or "bosch" in body["message_de"].lower() or "Gutmann" in body["message_de"]


def test_schema_invalid_goes_to_quarantine(client, auth_headers):
    bad = {
        "schema_version": "wrong",
        "dataset_version_label": "x",
        "source_key": "diagnova-structural",
    }
    res = client.post("/api/diagnostic-data/import/preview", headers=auth_headers, json=bad)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "quarantine"
    assert body["can_apply"] is False
    assert len(body["quarantine"]) >= 1


def test_csv_import_quarantines_bad_rows(client, auth_headers):
    csv_text = (FIXTURES / "phase06_dtcs.csv").read_text(encoding="utf-8")
    res = client.post(
        "/api/diagnostic-data/import/preview-csv",
        headers=auth_headers,
        data={
            "source_key": "diagnova-structural",
            "dataset_version_label": "csv-demo-06",
            "entity_type": "dtc",
        },
        files={"file": ("phase06_dtcs.csv", csv_text, "text/csv")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["format"] == "csv"
    assert body["status"] == "quarantine"
    assert any("BADCODE" in q.get("reason_de", "") or q.get("payload", {}).get("code") == "BADCODE" for q in body["quarantine"])


def test_odx_import_forbidden(client, auth_headers):
    res = client.post("/api/diagnostic-data/import/odx", headers=auth_headers)
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["accepted"] is False
    assert detail["format"] == "odx"


def test_coverage_no_completeness_claim(client, auth_headers):
    res = client.get("/api/diagnostic-data/coverage", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert "unvollständig" in body["disclaimer_de"].lower() or "unbekannt" in body["disclaimer_de"].lower()
    assert body["odx_import"] == "disabled"
    assert body["phase_07"] == "implemented_simulated"
    assert "Bosch" in body["blocked_vendors"]


def test_capabilities_include_phase06(client, auth_headers):
    caps = client.get("/api/catalog/capabilities", headers=auth_headers)
    assert caps.status_code == 200
    available_ids = {c["id"] for c in caps.json()["available"]}
    assert "diagnostic_data_import" in available_ids
    assert "dtc_lookup_provenance" in available_ids
