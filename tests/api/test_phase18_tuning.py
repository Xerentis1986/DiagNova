"""Phase 18 – Optionales Chiptuning: Architektur, Gates, keine Maps/Flash."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _acks(**extra):
    base = {
        "acknowledge_disabled": True,
        "acknowledge_no_map_change": True,
        "acknowledge_no_emission_defeat": True,
        "acknowledge_activation_locked": True,
    }
    base.update(extra)
    return base


def test_module_status_planned_disabled(client: TestClient, auth_headers: dict[str, str]):
    res = client.get("/api/tuning/status", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "planned_disabled"
    assert body["productive_activation_locked"] is True
    assert body["map_change_available"] is False
    assert body["flash_available"] is False
    assert body["emission_defeat_excluded"] is True


def test_catalog_disables_maps_and_flash(client: TestClient, auth_headers: dict[str, str]):
    res = client.get("/api/tuning/catalog", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["module_status"] == "planned_disabled"
    assert body["map_change_available"] is False
    assert body["flash_available"] is False
    assert body["tuning_activation_available"] is False
    assert body["productive_activation_locked"] is True
    assert body["live_execution_available"] is False

    codes = {o["code"] for o in body["operations"]}
    assert "OEM_BASELINE_LIST" in codes
    assert "APPROVAL_DOC_REGISTER" in codes
    assert "WORKFLOW_SIM_GATE" in codes
    assert "LEGAL_GATE_CHECK" in codes
    assert "MAP_CHANGE_ACTIVE" not in codes

    excluded = {e["code"] for e in body["excluded"]}
    assert "MAP_CHANGE_ACTIVE" in excluded
    assert "TUNING_FLASH" in excluded
    assert "EMISSION_DEFEAT_TUNE" in excluded
    assert "SAFETY_SYSTEM_DISABLE" in excluded
    assert "RAW_REMOTE_TUNE" in excluded

    for o in body["operations"]:
        assert o["enabled"] is False
        assert o["map_change_allowed"] is False
        assert o["flash_allowed"] is False
        assert o["tuning_activation_allowed"] is False
        assert o["productive_activation_locked"] is True


def test_excluded_and_activation_paths_blocked(client: TestClient, auth_headers: dict[str, str]):
    blocked = client.post(
        "/api/tuning/operations/MAP_CHANGE_ACTIVE/start",
        headers=auth_headers,
        json=_acks(
            confirmation_phrase="x",
            gate_state={"operator_confirm": True},
        ),
    )
    assert blocked.status_code == 403

    for path in ("activate", "map-change", "flash"):
        res = client.post(
            f"/api/tuning/operations/WORKFLOW_SIM_GATE/{path}",
            headers=auth_headers,
        )
        assert res.status_code == 403, path


def test_baselines_seed_and_register(client: TestClient, auth_headers: dict[str, str]):
    listed = client.get("/api/tuning/baselines", headers=auth_headers)
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) >= 2
    assert all(r["authorization_status"] in ("unauthorized_demo", "draft") for r in rows)
    assert all("demo" in (r["checksum_ref"] or "").lower() or r["data_source"] == "simulated" for r in rows)

    created = client.post(
        "/api/tuning/baselines",
        headers=auth_headers,
        json={
            "code": "TEST-BASELINE-2.0.0",
            "ecu_role": "engine",
            "software_version": "2.0.0",
            "part_number": "PN-TEST",
            "checksum_ref": "sha256:test-meta-only",
            "source_de": "Testdokumentation ohne Binary",
            "acknowledge_no_map_binary": True,
            "acknowledge_demo_only": True,
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["code"] == "TEST-BASELINE-2.0.0"
    assert body["authorization_status"] == "draft"
    assert body["data_source"] == "simulated"

    missing_ack = client.post(
        "/api/tuning/baselines",
        headers=auth_headers,
        json={
            "code": "NO-ACK",
            "software_version": "1.0",
            "source_de": "ohne ack",
            "acknowledge_no_map_binary": False,
            "acknowledge_demo_only": True,
        },
    )
    assert missing_ack.status_code == 400


def test_approvals_and_history(client: TestClient, auth_headers: dict[str, str]):
    baselines = client.get("/api/tuning/baselines", headers=auth_headers).json()
    baseline_id = baselines[0]["id"]

    bad = client.post(
        "/api/tuning/approvals",
        headers=auth_headers,
        json={
            "baseline_id": baseline_id,
            "title_de": "Demo-Genehmigung",
            "doc_type": "workshop_ack",
            "acknowledge_not_legal_advice": False,
            "acknowledge_no_activation": True,
        },
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/tuning/approvals",
        headers=auth_headers,
        json={
            "baseline_id": baseline_id,
            "title_de": "Demo-Werkstattfreigabe",
            "doc_type": "workshop_ack",
            "reference_code": "REF-DEMO-1",
            "issuer_de": "Demo-Werkstatt",
            "acknowledge_not_legal_advice": True,
            "acknowledge_no_activation": True,
        },
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "recorded"

    listed = client.get("/api/tuning/approvals", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    hist = client.get("/api/tuning/history", headers=auth_headers)
    assert hist.status_code == 200
    assert len(hist.json()) >= 1


def test_legal_gates_always_block_activation(client: TestClient, auth_headers: dict[str, str]):
    incomplete = client.post(
        "/api/tuning/legal-gates",
        headers=auth_headers,
        json={},
    )
    assert incomplete.status_code == 200
    body = incomplete.json()
    assert body["overall_ok"] is False
    assert body["map_change_blocked"] is True
    assert body["flash_blocked"] is True
    assert body["tuning_activation_blocked"] is True
    assert body["productive_activation_locked"] is True

    complete = client.post(
        "/api/tuning/legal-gates",
        headers=auth_headers,
        json={
            "operator_confirm": True,
            "legal_gate_ack": True,
            "no_emission_defeat_ack": True,
            "no_map_change_ack": True,
            "legal_approval_present": True,
            "technical_review_present": True,
            "recovery_plan": True,
            "oem_baseline_documented": True,
            "hardware_suitable": True,
            "expected_vin": "WVWZZZ1JZYW000001",
            "actual_vin": "WVWZZZ1JZYW000001",
            "expected_ecu_sw": "1.0.0",
            "actual_ecu_sw": "1.0.0",
        },
    )
    assert complete.status_code == 200
    ok = complete.json()
    assert ok["overall_ok"] is True
    assert ok["map_change_blocked"] is True
    assert ok["flash_blocked"] is True
    assert ok["tuning_activation_blocked"] is True


def test_workflow_scenarios(client: TestClient, auth_headers: dict[str, str]):
    gate_ok = {
        "operator_confirm": True,
        "legal_gate_ack": True,
        "no_emission_defeat_ack": True,
        "no_map_change_ack": True,
        "legal_approval_present": True,
        "technical_review_present": True,
        "recovery_plan": True,
        "oem_baseline_documented": True,
        "hardware_suitable": True,
    }

    legal_block = client.post(
        "/api/tuning/operations/WORKFLOW_SIM_GATE/start",
        headers=auth_headers,
        json=_acks(
            confirmation_phrase="TUNING WORKFLOW SIM BESTAETIGEN",
            scenario="missing_legal",
            gate_state=gate_ok,
        ),
    )
    assert legal_block.status_code == 200
    assert legal_block.json()["status"] == "blocked"
    assert legal_block.json()["map_commands_sent"] is False
    assert legal_block.json()["tuning_activated"] is False

    missing = client.post(
        "/api/tuning/operations/WORKFLOW_SIM_GATE/start",
        headers=auth_headers,
        json=_acks(
            confirmation_phrase="TUNING WORKFLOW SIM BESTAETIGEN",
            scenario="missing_prereq",
            gate_state={**gate_ok, "operator_confirm": False},
        ),
    )
    assert missing.status_code == 200
    assert missing.json()["status"] == "blocked"

    wrong = client.post(
        "/api/tuning/operations/WORKFLOW_SIM_GATE/start",
        headers=auth_headers,
        json=_acks(
            confirmation_phrase="TUNING WORKFLOW SIM BESTAETIGEN",
            scenario="wrong_vehicle",
            gate_state=gate_ok,
        ),
    )
    assert wrong.status_code == 200
    assert wrong.json()["status"] == "blocked"

    normal = client.post(
        "/api/tuning/operations/WORKFLOW_SIM_GATE/start",
        headers=auth_headers,
        json=_acks(
            confirmation_phrase="TUNING WORKFLOW SIM BESTAETIGEN",
            scenario="normal",
            gate_state=gate_ok,
        ),
    )
    assert normal.status_code == 200
    body = normal.json()
    assert body["status"] == "completed"
    assert body["map_commands_sent"] is False
    assert body["flash_commands_sent"] is False
    assert body["tuning_activated"] is False
    assert body["auto_retry_attempted"] is False

    abort_start = client.post(
        "/api/tuning/operations/WORKFLOW_SIM_GATE/start",
        headers=auth_headers,
        json=_acks(
            confirmation_phrase="TUNING WORKFLOW SIM BESTAETIGEN",
            scenario="abort",
            gate_state=gate_ok,
        ),
    )
    assert abort_start.status_code == 200
    assert abort_start.json()["status"] == "running"
    run_id = abort_start.json()["id"]
    aborted = client.post(
        f"/api/tuning/runs/{run_id}/abort",
        headers=auth_headers,
        json={"reason_de": "Testabbruch"},
    )
    assert aborted.status_code == 200
    assert aborted.json()["status"] == "aborted"
    assert aborted.json()["map_commands_sent"] is False
    assert aborted.json()["tuning_activated"] is False

    runs = client.get("/api/tuning/runs", headers=auth_headers)
    assert runs.status_code == 200
    assert len(runs.json()) >= 1


def test_dashboard_lists_chiptuning_planned(client: TestClient, auth_headers: dict[str, str]):
    res = client.get("/api/dashboard", headers=auth_headers)
    assert res.status_code == 200
    modules = {m["id"]: m for m in res.json()["planned_modules"]}
    assert modules["chiptuning"]["status"] == "planned"
    assert modules["lkw"]["status"] == "planned"
