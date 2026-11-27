"""Phase 09 – Fahrzeugakte, Historie, Vergleich, Mandant, Demo-Trennung."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
import app.db.session as session_mod
from app.models import SessionDtcResult, SessionEcuResult, User, Workshop
from app.services import vehicle_history as vh


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_vehicle_record_lookup_timeline_and_persistence(client: TestClient, auth_headers: dict[str, str]):
    vehicles = client.get("/api/vehicles", headers=auth_headers)
    assert vehicles.status_code == 200
    v = vehicles.json()[0]
    vid = v["id"]
    vin = v["vin"]
    plate = v["license_plate"]

    # Sitzung starten (v2) mit Idempotenz
    key = "idem-phase09-test-key-001"
    s1 = client.post(
        "/api/sessions/v2",
        headers=auth_headers,
        json={
            "vehicle_id": vid,
            "odometer_km": 100001,
            "idempotency_key": key,
            "notes": "Demo-Sitzung Phase 09",
        },
    )
    assert s1.status_code == 200, s1.text
    body = s1.json()
    assert body["status"] == "open"
    assert body["data_source"] == "simulated"
    assert body["odometer_km"] == 100001
    assert body["adapter_name"]
    assert body["protocol_name"]
    assert body["dtc_count"] >= 1
    assert len(body["ecus"]) >= 1
    assert body["measurement_sample_count"] >= 1
    sid = body["id"]

    # Idempotente Wiederholung → gleiche ID
    s1b = client.post(
        "/api/sessions/v2",
        headers=auth_headers,
        json={"vehicle_id": vid, "idempotency_key": key},
    )
    assert s1b.status_code == 200
    assert s1b.json()["id"] == sid

    closed = client.post(f"/api/sessions/{sid}/close", headers=auth_headers)
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    detail = client.get(f"/api/sessions/{sid}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["auto_saved_at"] is not None
    assert detail.json()["freeze_frame"] is not None

    # Lookup VIN / Kennzeichen
    by_vin = client.get(f"/api/vehicle-records/lookup?vin={vin}", headers=auth_headers)
    assert by_vin.status_code == 200
    assert any(m["vehicle_id"] == vid for m in by_vin.json()["matches"])
    assert "Beispieldaten" in by_vin.json()["disclaimer_de"] or "Simulation" in by_vin.json()["disclaimer_de"]

    by_plate = client.get(
        f"/api/vehicle-records/lookup?license_plate={plate}",
        headers=auth_headers,
    )
    assert by_plate.status_code == 200
    assert len(by_plate.json()["matches"]) >= 1

    record = client.get(f"/api/vehicle-records/{vid}", headers=auth_headers)
    assert record.status_code == 200
    rec = record.json()
    assert rec["vin"] == vin
    assert rec["session_count"] >= 1
    assert any(t["kind"] == "session" for t in rec["timeline"])
    assert any(t["authenticity"] in ("simulated", "example_seed") for t in rec["timeline"])

    # Notiz
    note = client.post(
        f"/api/vehicle-records/{vid}/notes",
        headers=auth_headers,
        json={"body": "Ölwechsel dokumentiert (Demo)", "note_type": "service"},
    )
    assert note.status_code == 201
    assert note.json()["authenticity"] == "recorded"

    timeline = client.get(f"/api/vehicle-records/{vid}/timeline", headers=auth_headers)
    assert timeline.status_code == 200
    assert any(t["kind"] == "note" for t in timeline.json()["timeline"])

    meas = client.get(f"/api/vehicle-records/{vid}/measurements?limit=50", headers=auth_headers)
    assert meas.status_code == 200
    assert meas.json()["count"] >= 1
    assert meas.json()["samples"][0]["data_source"] == "simulated"
    assert "begrenzt" in meas.json()["disclaimer_de"].lower() or "limit" in meas.json()["disclaimer_de"].lower()


def test_abort_session_marked(client: TestClient, auth_headers: dict[str, str]):
    vid = client.get("/api/vehicles", headers=auth_headers).json()[0]["id"]
    started = client.post(
        "/api/sessions/v2",
        headers=auth_headers,
        json={"vehicle_id": vid, "idempotency_key": "idem-abort-session-xyz"},
    )
    assert started.status_code == 200
    sid = started.json()["id"]
    aborted = client.post(
        f"/api/sessions/{sid}/abort",
        headers=auth_headers,
        json={"reason": "Kabel gezogen während Demo"},
    )
    assert aborted.status_code == 200
    assert aborted.json()["status"] == "aborted"
    assert aborted.json()["abort_reason"]


def test_dtc_compare_incomplete_scan_not_resolved(client: TestClient, auth_headers: dict[str, str]):
    """Nicht erneut beobachtet ohne ECU-Check darf nicht als behoben gelten."""
    vid = client.get("/api/vehicles", headers=auth_headers).json()[0]["id"]

    a = client.post(
        "/api/sessions/v2",
        headers=auth_headers,
        json={
            "vehicle_id": vid,
            "idempotency_key": "idem-compare-before-001",
            "ecu_codes": ["ECM", "ABS"],
        },
    )
    assert a.status_code == 200, a.text
    before_id = a.json()["id"]
    client.post(f"/api/sessions/{before_id}/close", headers=auth_headers)

    b = client.post(
        "/api/sessions/v2",
        headers=auth_headers,
        json={
            "vehicle_id": vid,
            "idempotency_key": "idem-compare-after-001",
            "ecu_codes": ["ECM"],  # ABS bewusst nicht geprüft
        },
    )
    assert b.status_code == 200
    after_id = b.json()["id"]
    client.post(f"/api/sessions/{after_id}/close", headers=auth_headers)

    # Manuell ABS-DTC nur in before setzen (unvollständiger Scan-Test)
    # SessionLocal aus session_mod – von conftest auf Test-Engine umgebogen
    db: Session = session_mod.SessionLocal()
    try:
        ecus = (
            db.query(SessionEcuResult)
            .filter(SessionEcuResult.session_id == before_id)
            .all()
        )
        codes = {e.ecu_code for e in ecus}
        assert "ABS" in codes, f"erwartete ABS in {codes}"
        abs_ecu = next(e for e in ecus if e.ecu_code == "ABS")
        db.add(
            SessionDtcResult(
                session_id=before_id,
                ecu_result_id=abs_ecu.id,
                ecu_code="ABS",
                code="C0035",
                dtc_status="stored",
                description_de="Raddrehzahl Demo",
                severity="warning",
            )
        )
        db.commit()
    finally:
        db.close()

    cmp = client.get(
        f"/api/sessions/compare?before={before_id}&after={after_id}",
        headers=auth_headers,
    )
    assert cmp.status_code == 200, cmp.text
    data = cmp.json()
    assert data["incomplete_scan"] is True
    assert "ABS" in data["unchecked_ecus_in_after"]
    abs_items = [i for i in data["items"] if i["ecu_code"] == "ABS" and i["code"] == "C0035"]
    assert abs_items
    assert abs_items[0]["outcome"] == "nicht_erneut_beobachtet"
    assert abs_items[0]["may_interpret_as_resolved"] is False
    assert "NICHT" in abs_items[0]["note_de"] or "nicht" in abs_items[0]["note_de"]


def test_cross_tenant_vehicle_record_404(client: TestClient, auth_headers: dict[str, str]):
    vid = client.get("/api/vehicles", headers=auth_headers).json()[0]["id"]

    db: Session = session_mod.SessionLocal()
    try:
        other = Workshop(
            name="Fremde Werkstatt Phase09",
            is_example_data=True,
        )
        db.add(other)
        db.flush()
        stranger = User(
            email="stranger09@example.com",
            full_name="Fremd User",
            hashed_password=hash_password("StrangerDemo123!"),
            role="admin",
            workshop_id=other.id,
            is_active=True,
        )
        db.add(stranger)
        db.commit()
    finally:
        db.close()

    foreign = _login(client, "stranger09@example.com", "StrangerDemo123!")
    res = client.get(f"/api/vehicle-records/{vid}", headers=foreign)
    assert res.status_code == 404

    lookup = client.get(
        "/api/vehicle-records/lookup?vin=" + client.get("/api/vehicles", headers=auth_headers).json()[0]["vin"],
        headers=foreign,
    )
    assert lookup.status_code == 200
    assert lookup.json()["matches"] == []


def test_measurement_prune_limit():
    """Unit: Overflow wird gekürzt."""
    assert vh.MAX_SAMPLES_PER_SESSION == 500
    assert vh.MAX_SAMPLES_PER_VEHICLE == 5000
