"""Phase 12 – Codierung/Programmierung: Identifikation, Gates, kein Flash."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_catalog_disables_write_and_flash(client: TestClient, auth_headers: dict[str, str]):
    res = client.get("/api/coding/catalog", headers=auth_headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["live_execution_available"] is False
    assert body["flash_available"] is False
    assert body["hardware_live"] is False
    assert body["auto_retry_forbidden"] is True
    assert body["j2534_status"] == "documented_prep"
    codes = {o["code"] for o in body["operations"]}
    assert "ECU_IDENTIFY_READ" in codes
    assert "CODING_WRITE_GENERIC" in codes
    assert "FLASH_PROGRAMMING" in codes
    assert "GATE_CODING_PROBE" in codes
    assert "UNAUTH_FLASH" not in codes
    for o in body["operations"]:
        assert o["enabled"] is False
        assert o["write_allowed"] is False
        assert o["flash_allowed"] is False
        assert o["oem_procedure_invented"] is False
        assert o["auto_retry_forbidden"] is True
        if o["code"] in ("CODING_WRITE_GENERIC", "FLASH_PROGRAMMING"):
            assert o["release_status"] == "disabled"
    excluded = {e["code"]: e for e in body["excluded"]}
    assert "UNAUTH_FLASH" in excluded
    assert "EMISSION_DEFEAT_CODING" in excluded


def test_excluded_and_live_flash_blocked(client: TestClient, auth_headers: dict[str, str]):
    blocked = client.post(
        "/api/coding/operations/UNAUTH_FLASH/start",
        headers=auth_headers,
        json={
            "acknowledge_disabled": True,
            "acknowledge_no_oem_write": True,
            "acknowledge_no_flash": True,
        },
    )
    assert blocked.status_code == 403

    live = client.post(
        "/api/coding/operations/FLASH_PROGRAMMING/execute-live",
        headers=auth_headers,
    )
    assert live.status_code == 403

    flash = client.post(
        "/api/coding/operations/FLASH_PROGRAMMING/flash",
        headers=auth_headers,
    )
    assert flash.status_code == 403


def test_flash_requires_acks(client: TestClient, auth_headers: dict[str, str]):
    denied = client.post(
        "/api/coding/operations/FLASH_PROGRAMMING/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "FLASH PROGRAMMIERUNG BESTAETIGEN",
            "vehicle_state": {
                "adapter_connected": True,
                "operator_confirm": True,
                "oem_spec_present": True,
                "authorization_present": True,
                "recovery_plan": True,
                "battery_voltage_ok": True,
                "vin_ecu_match": True,
                "stable_connection": True,
                "ignition_on": True,
            },
        },
    )
    assert denied.status_code == 403

    ok = client.post(
        "/api/coding/operations/FLASH_PROGRAMMING/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "FLASH PROGRAMMIERUNG BESTAETIGEN",
            "acknowledge_disabled": True,
            "acknowledge_no_oem_write": True,
            "acknowledge_no_flash": True,
            "vehicle_state": {
                "adapter_connected": True,
                "operator_confirm": True,
                "oem_spec_present": True,
                "authorization_present": True,
                "recovery_plan": True,
                "battery_voltage_ok": True,
                "battery_voltage_v": 12.8,
                "vin_ecu_match": True,
                "stable_connection": True,
                "ignition_on": True,
            },
        },
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert body["status"] == "completed"
    assert body["write_commands_sent"] is False
    assert body["flash_commands_sent"] is False
    assert body["auto_retry_attempted"] is False


def test_voltage_drop_and_wrong_vehicle(client: TestClient, auth_headers: dict[str, str]):
    drop = client.post(
        "/api/coding/operations/GATE_CODING_PROBE/start",
        headers=auth_headers,
        json={
            "scenario": "voltage_drop",
            "vehicle_state": {"adapter_connected": True, "operator_confirm": True},
        },
    )
    assert drop.status_code == 200, drop.text
    body = drop.json()
    assert body["status"] == "failed"
    assert body["result"]["error"] == "voltage_drop"
    assert body["flash_commands_sent"] is False
    assert body["auto_retry_attempted"] is False

    wrong = client.post(
        "/api/coding/operations/GATE_CODING_PROBE/start",
        headers=auth_headers,
        json={
            "scenario": "wrong_vehicle",
            "vehicle_state": {"adapter_connected": True, "operator_confirm": True},
        },
    )
    assert wrong.status_code == 200, wrong.text
    assert wrong.json()["status"] == "blocked"
    assert wrong.json()["result"]["error"] == "vin_ecu_mismatch"
    assert wrong.json()["write_commands_sent"] is False


def test_missing_prereq_comm_loss_abort(client: TestClient, auth_headers: dict[str, str]):
    blocked = client.post(
        "/api/coding/operations/GATE_CODING_PROBE/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "CODING GATE BESTAETIGEN",
            "scenario": "missing_prereq",
            "vehicle_state": {"adapter_connected": False},
        },
    )
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["status"] == "blocked"
    assert any(not p["met"] for p in blocked.json()["prerequisites"])

    lost = client.post(
        "/api/coding/operations/GATE_CODING_PROBE/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "CODING GATE BESTAETIGEN",
            "scenario": "comm_loss",
            "vehicle_state": {
                "adapter_connected": True,
                "operator_confirm": True,
                "oem_spec_present": True,
                "authorization_present": True,
                "recovery_plan": True,
                "battery_voltage_ok": True,
                "vin_ecu_match": True,
                "stable_connection": True,
                "ignition_on": True,
            },
        },
    )
    assert lost.status_code == 200, lost.text
    assert lost.json()["status"] == "failed"
    assert lost.json()["result"]["error"] == "communication_lost"
    assert lost.json()["auto_retry_attempted"] is False

    running = client.post(
        "/api/coding/operations/GATE_CODING_PROBE/start",
        headers=auth_headers,
        json={
            "confirmation_phrase": "CODING GATE BESTAETIGEN",
            "scenario": "abort",
            "vehicle_state": {
                "adapter_connected": True,
                "operator_confirm": True,
                "oem_spec_present": True,
                "authorization_present": True,
                "recovery_plan": True,
                "battery_voltage_ok": True,
                "vin_ecu_match": True,
                "stable_connection": True,
                "ignition_on": True,
            },
        },
    )
    assert running.status_code == 200, running.text
    assert running.json()["status"] == "running"
    run_id = running.json()["id"]

    aborted = client.post(
        f"/api/coding/runs/{run_id}/abort",
        headers=auth_headers,
        json={"reason_de": "Testabbruch"},
    )
    assert aborted.status_code == 200, aborted.text
    assert aborted.json()["status"] == "aborted"
    assert aborted.json()["flash_commands_sent"] is False
    assert aborted.json()["auto_retry_attempted"] is False


def test_identify_and_compatibility_and_interfaces(client: TestClient, auth_headers: dict[str, str]):
    ident = client.get("/api/coding/identify", headers=auth_headers)
    assert ident.status_code == 200, ident.text
    body = ident.json()
    assert body["data_source"] == "simulated"
    assert body["oem_fields_available"] is False
    assert body["coding_profile_status"] == "unavailable"
    assert body["coding_profile"] is None

    compat = client.post(
        "/api/coding/compatibility-check",
        headers=auth_headers,
        json={
            "battery_voltage_v": 11.0,
            "battery_voltage_ok": True,
            "oem_spec_present": False,
            "authorization_present": False,
            "recovery_plan": False,
            "vin_ecu_match": True,
            "stable_connection": True,
        },
    )
    assert compat.status_code == 200, compat.text
    c = compat.json()
    assert c["voltage_ok"] is False
    assert c["flash_blocked"] is True
    assert c["write_blocked"] is True
    assert c["overall_ok"] is False
    assert "voltage" in c["blockers"]

    iface = client.get("/api/coding/interfaces", headers=auth_headers)
    assert iface.status_code == 200, iface.text
    assert iface.json()["vendor_dll_present"] is False
    assert iface.json()["j2534_status"] == "documented_prep"


def test_identify_run_no_writes(client: TestClient, auth_headers: dict[str, str]):
    res = client.post(
        "/api/coding/operations/ECU_IDENTIFY_READ/start",
        headers=auth_headers,
        json={
            "scenario": "normal",
            "vehicle_state": {
                "ignition_on": True,
                "adapter_connected": True,
                "stable_connection": True,
            },
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "completed"
    assert body["write_commands_sent"] is False
    assert body["flash_commands_sent"] is False
