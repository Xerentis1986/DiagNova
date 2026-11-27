"""Phase 19 – LKW/Nutzfahrzeug Architektur only; keine Diagnose-Freigabe."""


def test_lkw_architecture_is_prep_only(client, auth_headers):
    res = client.get("/api/lkw/architecture", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["phase"] == 19
    assert body["scope"] == "architecture_only"
    assert body["status"] == "documented_prep"
    assert body["entitlement_granted"] is False
    assert "j1939_live_read" in body["explicitly_disabled"]
    assert "fake_truck_simulator_values" in body["explicitly_disabled"]
    assert body["brand_count"] >= 7


def test_lkw_brands_all_planned_no_diagnosis(client, auth_headers):
    res = client.get("/api/lkw/brands", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    names = {b["name"] for b in body["brands"]}
    for expected in (
        "MAN",
        "Mercedes-Benz Trucks",
        "Scania",
        "Volvo Trucks",
        "DAF",
        "Iveco",
        "Renault Trucks",
    ):
        assert expected in names
    for brand in body["brands"]:
        assert brand["release_status"] == "planned"
        assert brand["diagnosis_available"] is False
        assert "sae_j1939" in brand["protocols_planned"]


def test_lkw_capabilities_all_disabled(client, auth_headers):
    res = client.get("/api/lkw/capabilities", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["diagnosis_enabled"] is False
    assert body["release_status"] == "planned"
    assert body["available"] == []
    assert len(body["flags"]) >= 8
    for flag in body["flags"]:
        assert flag["enabled"] is False
        assert flag["status"] in ("planned", "unavailable")


def test_lkw_diagnose_endpoints_forbidden(client, auth_headers):
    for path in ("/api/lkw/diagnose", "/api/lkw/j1939/read", "/api/lkw/rp1210/connect"):
        res = client.post(path, headers=auth_headers)
        assert res.status_code == 403, path


def test_capability_matrix_includes_rp1210_adapter(client, auth_headers):
    res = client.get("/api/protocols/capability-matrix", headers=auth_headers)
    assert res.status_code == 200
    adapters = {a["adapter_id"]: a for a in res.json()["adapters"]}
    assert "rp1210-commercial" in adapters
    rp = adapters["rp1210-commercial"]
    assert rp["hardware_tested"] is False
    assert rp["protocols"]["rp1210"] == "planned"
    assert rp["protocols"]["sae_j1939"] == "planned"
    elm = adapters["elm327-obd"]
    assert elm["protocols"]["sae_j1939"] == "not_supported"
    assert elm["protocols"]["rp1210"] == "not_supported"


def test_protocol_catalog_j1939_documented_prep(client, auth_headers):
    res = client.get("/api/protocols/catalog", headers=auth_headers)
    assert res.status_code == 200
    by_id = {p["id"]: p for p in res.json()["protocols"]}
    assert by_id["sae_j1939"]["status"] == "documented_prep"
    assert by_id["rp1210"]["status"] == "documented_prep"
    assert by_id["sae_j1708_j1587"]["status"] == "documented_prep"


def test_dashboard_lists_lkw_planned(client, auth_headers):
    res = client.get("/api/dashboard", headers=auth_headers)
    assert res.status_code == 200
    modules = {m["id"]: m for m in res.json()["planned_modules"]}
    assert "lkw" in modules
    assert modules["lkw"]["status"] == "planned"


def test_catalog_capabilities_include_lkw_planned(client, auth_headers):
    res = client.get("/api/catalog/capabilities", headers=auth_headers)
    assert res.status_code == 200
    unavailable = {c["id"] for c in res.json()["unavailable"]}
    assert "lkw_j1939_rp1210" in unavailable
