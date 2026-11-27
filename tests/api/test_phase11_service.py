"""Phase 11 – Servicekatalog, Safety-Gates, Guided Diagnosis."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_catalog_lists_disabled_and_excludes_dpf_off(client: TestClient, auth_headers: dict[str, str]):
    res = client.get("/api/service/catalog", headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["live_execution_available"] is False
    assert body["hardware_live"] is False
    codes = {p["code"] for p in body["procedures"]}
    assert "DPF_REGENERATION" in codes
    assert "EPB_SERVICE_MODE" in codes
    assert "GATE_SIMULATION_PROBE" in codes
    assert "DPF_OFF" not in codes
    for p in body["procedures"]:
        assert p["enabled"] is False
        assert p["write_allowed"] is False
        assert p["oem_procedure_invented"] is False
        if p["code"] in ("DPF_REGENERATION", "EPB_SERVICE_MODE", "STEERING_ANGLE_CAL"):
            assert p["release_status"] == "disabled"
            assert p["safety_class"] == "safety_critical"
    excluded = {e["code"]: e for e in body["excluded"]}
    assert "DPF_OFF" in excluded
    assert "Abgas" in excluded["DPF_OFF"]["reason_de"] or "DPF" in excluded["DPF_OFF"]["reason_de"]


def test_dpf_off_and_live_execute_blocked(client: TestClient, auth_headers: dict[str, str]):
    blocked = client.post(
        "/api/service/procedures/DPF_OFF/start",
        headers=auth_headers,
        json={"acknowledge_disabled": True, "acknowledge_no_oem_write": True},
    )
    assert blocked.status_code == 403

    live = client.post(
        "/api/service/procedures/DPF_REGENERATION/execute-live",
        headers=auth_headers,
    )
    assert live.status_code == 403


def test_missing_prerequisites_blocks(client: TestClient, auth_headers: dict[str, str]):
    res = client.post(
        "/api/service/procedures/GATE_SIMULATION_PROBE/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "GATE SIMULATION BESTAETIGEN",
            "scenario": "missing_prereq",
            "vehicle_state": {
                "adapter_connected": False,
                "operator_confirm": False,
            },
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "blocked"
    assert body["write_commands_sent"] is False
    assert any(not p["met"] for p in body["prerequisites"])


def test_comm_loss_and_abort(client: TestClient, auth_headers: dict[str, str]):
    lost = client.post(
        "/api/service/procedures/GATE_SIMULATION_PROBE/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "GATE SIMULATION BESTAETIGEN",
            "scenario": "comm_loss",
            "vehicle_state": {"adapter_connected": True, "operator_confirm": True},
        },
    )
    assert lost.status_code == 200, lost.text
    assert lost.json()["status"] == "failed"
    assert lost.json()["result"]["error"] == "communication_lost"
    assert lost.json()["write_commands_sent"] is False

    running = client.post(
        "/api/service/procedures/GATE_SIMULATION_PROBE/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "GATE SIMULATION BESTAETIGEN",
            "scenario": "abort",
            "vehicle_state": {"adapter_connected": True, "operator_confirm": True},
        },
    )
    assert running.status_code == 200, running.text
    assert running.json()["status"] == "running"
    run_id = running.json()["id"]

    aborted = client.post(
        f"/api/service/runs/{run_id}/abort",
        headers=auth_headers,
        json={"reason_de": "Testabbruch"},
    )
    assert aborted.status_code == 200, aborted.text
    assert aborted.json()["status"] == "aborted"
    assert aborted.json()["write_commands_sent"] is False
    assert aborted.json()["abort_reason_de"] == "Testabbruch"


def test_disabled_dpf_regen_requires_ack_then_gates_only(client: TestClient, auth_headers: dict[str, str]):
    denied = client.post(
        "/api/service/procedures/DPF_REGENERATION/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "DPF REGENERATION BESTAETIGEN",
            "vehicle_state": {
                "adapter_connected": True,
                "operator_confirm": True,
                "oem_spec_present": True,
                "exhaust_safe": True,
                "safe_work_area": True,
                "battery_voltage_ok": True,
                "ignition_on": True,
            },
        },
    )
    assert denied.status_code == 403

    ok = client.post(
        "/api/service/procedures/DPF_REGENERATION/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "DPF REGENERATION BESTAETIGEN",
            "acknowledge_disabled": True,
            "acknowledge_no_oem_write": True,
            "scenario": "normal",
            "vehicle_state": {
                "adapter_connected": True,
                "operator_confirm": True,
                "oem_spec_present": True,
                "exhaust_safe": True,
                "safe_work_area": True,
                "battery_voltage_ok": True,
                "ignition_on": True,
            },
        },
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["status"] == "completed"
    assert body["write_commands_sent"] is False
    assert body["result"]["live_execution"] is False


def test_guided_overview_groups_and_dtc_help(client: TestClient, auth_headers: dict[str, str]):
    ov = client.get("/api/guided/overview", headers=auth_headers)
    assert ov.status_code == 200, ov.text
    assert ov.json()["data_source"] == "simulated"
    assert len(ov.json()["measurement_groups"]) >= 3

    known = client.get("/api/guided/dtc/P0420", headers=auth_headers)
    assert known.status_code == 200
    assert known.json()["description_status"] == "known"
    assert known.json()["repair_auto_generated"] is False

    unknown = client.get("/api/guided/dtc/P9999", headers=auth_headers)
    assert unknown.status_code == 200
    assert unknown.json()["description_status"] == "unknown"
    assert unknown.json()["description_de"] is None

    vehicles = client.get("/api/vehicles", headers=auth_headers)
    assert vehicles.status_code == 200
    vid = vehicles.json()[0]["id"]
    group = client.get(
        f"/api/guided/measurement-groups/engine_basic?vehicle_id={vid}",
        headers=auth_headers,
    )
    assert group.status_code == 200, group.text
    assert group.json()["data_source"] == "simulated"
    assert isinstance(group.json()["readings"], list)


def test_tenant_isolation_service_run(client: TestClient, auth_headers: dict[str, str]):
    started = client.post(
        "/api/service/procedures/GATE_SIMULATION_PROBE/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "GATE SIMULATION BESTAETIGEN",
            "scenario": "normal",
            "vehicle_state": {"adapter_connected": True, "operator_confirm": True},
        },
    )
    assert started.status_code == 200
    run_id = started.json()["id"]

    # viewer from same workshop can list; foreign id → 404 via get
    listing = client.get("/api/service/runs", headers=auth_headers)
    assert listing.status_code == 200
    assert any(r["id"] == run_id for r in listing.json())

    missing = client.get("/api/service/runs/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert missing.status_code == 404
