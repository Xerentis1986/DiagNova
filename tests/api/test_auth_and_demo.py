def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True
    assert body["data_source_default"] == "simulated"


def test_login_success(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "AdminDemo123!"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["user"]["role"] == "admin"


def test_login_failure(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "wrong-password"},
    )
    assert res.status_code == 401


def test_demo_vehicles_seeded(client, auth_headers):
    res = client.get("/api/vehicles", headers=auth_headers)
    assert res.status_code == 200
    vehicles = res.json()
    makes = {v["make"] for v in vehicles}
    expected = {
        "Volkswagen",
        "Audi",
        "BMW",
        "Mercedes-Benz",
        "Škoda",
        "Seat",
        "Opel",
        "Ford",
        "Toyota",
    }
    assert expected.issubset(makes)
    assert all(v["is_example_data"] for v in vehicles)


def test_simulator_dtcs_and_live(client, auth_headers):
    vehicles = client.get("/api/vehicles", headers=auth_headers).json()
    vid = vehicles[0]["id"]
    dtcs = client.get(f"/api/diagnostics/{vid}/dtcs", headers=auth_headers)
    assert dtcs.status_code == 200
    assert len(dtcs.json()) >= 1

    live = client.get(f"/api/diagnostics/{vid}/live", headers=auth_headers)
    assert live.status_code == 200
    body = live.json()
    assert body["data_source"] == "simulated"
    assert len(body["readings"]) >= 5
    assert "readiness" in body
    assert body["freeze_frame"] is not None


def test_session_and_report_export(client, auth_headers):
    vehicles = client.get("/api/vehicles", headers=auth_headers).json()
    vid = vehicles[0]["id"]
    session = client.post(f"/api/sessions?vehicle_id={vid}", headers=auth_headers)
    assert session.status_code == 200
    sid = session.json()["id"]
    assert session.json()["data_source"] == "simulated"

    report = client.post(
        "/api/reports",
        headers=auth_headers,
        json={"session_id": sid, "title": "Testbericht Simulator"},
    )
    assert report.status_code == 200
    rid = report.json()["id"]
    assert report.json()["content"]["data_source"] == "simulated"

    csv_res = client.get(f"/api/reports/{rid}/export.csv", headers=auth_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Simulierte" in csv_res.text or "SIMULIERTEN" in csv_res.text or "simulated" in csv_res.text

    pdf_res = client.get(f"/api/reports/{rid}/export.pdf", headers=auth_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content[:4] == b"%PDF"


def test_connection_is_simulator(client, auth_headers):
    res = client.get("/api/connection", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "simulator"
    assert body["data_source"] == "simulated"
