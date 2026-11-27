"""Phase-05 API: Protokollkatalog, Capability-Matrix, ECU-Übersicht (simuliert)."""


def test_protocol_catalog_and_architecture(client, auth_headers):
    arch = client.get("/api/protocols/architecture", headers=auth_headers)
    assert arch.status_code == 200
    layers = {x["id"] for x in arch.json()["layers"]}
    assert layers == {"transport", "protocol", "adapter", "vehicle_definition"}

    cat = client.get("/api/protocols/catalog", headers=auth_headers)
    assert cat.status_code == 200
    body = cat.json()
    ids = {p["id"] for p in body["protocols"]}
    assert "iso_14229_uds" in ids
    assert "iso_13400_doip" in ids
    assert "sae_j2534" in ids
    assert "sae_j1939" in ids


def test_capability_matrix_elm_not_universal(client, auth_headers):
    res = client.get("/api/protocols/capability-matrix", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    elm = next(a for a in body["adapters"] if a["adapter_id"] == "elm327-obd")
    assert elm["protocols"]["iso_13400_doip"] == "not_supported"
    assert elm["protocols"]["can_fd"] == "not_supported"
    assert elm["hardware_tested"] is False


def test_ecu_overview_no_blind_scan(client, auth_headers):
    overview = client.get("/api/protocols/ecu/overview", headers=auth_headers)
    assert overview.status_code == 200
    assert overview.json()["blind_scan_allowed"] is False
    abs_cat = next(c for c in overview.json()["categories"] if c["id"] == "abs")
    assert abs_cat["availability"] == "unavailable_no_definition"

    sim = client.get("/api/protocols/ecu/simulated", headers=auth_headers)
    assert sim.status_code == 200
    data = sim.json()
    assert data["blind_scan_used"] is False
    assert data["data_source"] == "simulated"
    assert data["count"] == 2
    ids = {e["ecu_id"] for e in data["discovered_obd_ecus"]}
    assert "7E8" in ids and "7E9" in ids


def test_uds_catalog_write_disabled(client, auth_headers):
    res = client.get("/api/protocols/uds", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["active_write_paths"] is False
    assert body["security_access_enabled"] is False


def test_capabilities_include_phase05(client, auth_headers):
    caps = client.get("/api/catalog/capabilities", headers=auth_headers)
    assert caps.status_code == 200
    available_ids = {c["id"] for c in caps.json()["available"]}
    assert "multi_ecu_obd" in available_ids
    assert "protocol_catalog" in available_ids
