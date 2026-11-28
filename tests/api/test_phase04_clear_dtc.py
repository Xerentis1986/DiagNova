def test_clear_warnings_simulated(client, auth_headers):
    res = client.get("/api/diagnostics/clear/warnings", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["data_source"] == "simulated"
    assert body["permanent_dtcs_clearable"] is False
    assert body["hardware_live"] is False
    assert body["requires_confirmation_phrase"] == "FEHLERCODES LOESCHEN"
    assert len(body["warnings_de"]) >= 3


def test_clear_dtc_requires_acks(client, auth_headers):
    vehicles = client.get("/api/vehicles", headers=auth_headers).json()
    vid = vehicles[0]["id"]
    res = client.post(
        f"/api/diagnostics/{vid}/dtcs/clear",
        headers=auth_headers,
        json={
            "confirmation_phrase": "wrong",
            "acknowledge_freeze_frame_loss": True,
            "acknowledge_readiness_reset": True,
            "acknowledge_permanent_remain": True,
            "pre_report_saved": True,
        },
    )
    assert res.status_code == 400


def test_clear_dtc_simulated_keeps_permanent(client, auth_headers):
    vehicles = client.get("/api/vehicles", headers=auth_headers).json()
    vid = vehicles[0]["id"]
    before = client.get(f"/api/diagnostics/{vid}/dtcs", headers=auth_headers).json()
    assert any(d["status"] == "permanent" for d in before)

    res = client.post(
        f"/api/diagnostics/{vid}/dtcs/clear",
        headers=auth_headers,
        json={
            "confirmation_phrase": "FEHLERCODES LOESCHEN",
            "acknowledge_freeze_frame_loss": True,
            "acknowledge_readiness_reset": True,
            "acknowledge_permanent_remain": True,
            "pre_report_saved": True,
            "operator_note": "pytest",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data_source"] == "simulated"
    assert all(d["status"] == "permanent" for d in body["after"])
    assert len(body["permanent_remain"]) >= 1

    after = client.get(f"/api/diagnostics/{vid}/dtcs", headers=auth_headers).json()
    assert all(d["status"] == "permanent" for d in after)
