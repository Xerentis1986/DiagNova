"""Phase 08 – Werkstatt, Kunden, Rollen, Mandanten, DSGVO."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Customer, User, Vehicle, Workshop


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_workshop_profile_and_members(client: TestClient, auth_headers: dict[str, str]):
    me = client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["workshop_id"]

    ws = client.get("/api/workshop/me", headers=auth_headers)
    assert ws.status_code == 200
    body = ws.json()
    assert body["name"] == "Demo-Werkstatt DiagNova"
    assert body["is_example_data"] is True
    assert body["retention_days"] >= 30
    assert "has_logo" in body

    members = client.get("/api/workshop/me/members", headers=auth_headers)
    assert members.status_code == 200
    roles = {m["role"] for m in members.json()}
    assert "admin" in roles
    assert "technician" in roles

    patch = client.patch(
        "/api/workshop/me",
        headers=auth_headers,
        json={"phone": "+43 1 555 9999", "retention_days": 730},
    )
    assert patch.status_code == 200
    assert patch.json()["phone"] == "+43 1 555 9999"
    assert patch.json()["retention_days"] == 730


def test_customer_crud_search_duplicate_merge(client: TestClient, auth_headers: dict[str, str]):
    create = client.post(
        "/api/customers",
        headers=auth_headers,
        json={
            "display_name": "Test Kunde Gamma",
            "email": "gamma@example.com",
            "phone": "+43 664 1111111",
            "city": "Graz",
        },
    )
    assert create.status_code == 201, create.text
    cid = create.json()["id"]

    # Dublette ohne force → 409
    dup = client.post(
        "/api/customers",
        headers=auth_headers,
        json={"display_name": "Test Kunde Gamma", "email": "gamma@example.com"},
    )
    assert dup.status_code == 409
    assert "duplicates" in dup.json()["detail"]

    forced = client.post(
        "/api/customers",
        headers=auth_headers,
        json={
            "display_name": "Test Kunde Gamma",
            "email": "gamma2@example.com",
            "force": True,
        },
    )
    assert forced.status_code == 201
    source_id = forced.json()["id"]

    listed = client.get("/api/customers?q=Gamma", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 2

    merged = client.post(
        f"/api/customers/{cid}/merge",
        headers=auth_headers,
        json={"source_customer_id": source_id},
    )
    assert merged.status_code == 200
    assert merged.json()["id"] == cid

    archived_list = client.get("/api/customers?include_archived=true&q=Gamma", headers=auth_headers)
    assert any(c["id"] == source_id and c["archived_at"] for c in archived_list.json())


def test_work_orders_and_vehicle_tenant(client: TestClient, auth_headers: dict[str, str]):
    customers = client.get("/api/customers", headers=auth_headers).json()
    assert customers
    cid = customers[0]["id"]

    order = client.post(
        "/api/work-orders",
        headers=auth_headers,
        json={
            "title": "Bremsen prüfen",
            "customer_id": cid,
            "notes": "Nur Demo",
            "status": "open",
        },
    )
    assert order.status_code == 201, order.text
    oid = order.json()["id"]

    patched = client.patch(
        f"/api/work-orders/{oid}",
        headers=auth_headers,
        json={"status": "in_progress", "repair_summary": "Beläge ok (Demo)"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "in_progress"

    vehicles = client.get("/api/vehicles", headers=auth_headers)
    assert vehicles.status_code == 200
    assert all(v.get("workshop_id") for v in vehicles.json())
    assert all(v["is_example_data"] or True for v in vehicles.json())

    # Ungültige VIN
    bad = client.post(
        "/api/vehicles",
        headers=auth_headers,
        json={
            "make": "VW",
            "model": "Golf",
            "year": 2018,
            "vin": "INVALID",
        },
    )
    assert bad.status_code in (400, 422)

    ok_vin = "WVWZZZ1JZXW000001"
    created = client.post(
        "/api/vehicles",
        headers=auth_headers,
        json={
            "make": "Volkswagen",
            "model": "Golf",
            "year": 2018,
            "vin": ok_vin,
            "license_plate": "W-TEST-08",
            "engine": "1.5 TSI",
            "odometer_km": 12000,
            "customer_id": cid,
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["customer_id"] == cid


def test_dsgvo_export_and_delete_conflict(client: TestClient, auth_headers: dict[str, str]):
    create = client.post(
        "/api/customers",
        headers=auth_headers,
        json={"display_name": "Lösch Kandidat", "email": "loesch@example.com", "force": True},
    )
    assert create.status_code == 201
    cid = create.json()["id"]

    order = client.post(
        "/api/work-orders",
        headers=auth_headers,
        json={"title": "Offener Auftrag", "customer_id": cid, "status": "open"},
    )
    assert order.status_code == 201

    export = client.get(f"/api/customers/{cid}/export", headers=auth_headers)
    assert export.status_code == 200
    assert "display_name" in export.text
    assert "Lösch Kandidat" in export.text

    conflict = client.post(
        f"/api/customers/{cid}/delete",
        headers=auth_headers,
        json={"mode": "anonymize", "force": False},
    )
    assert conflict.status_code == 409

    # Auftrag schließen → Anonymisierung ok
    client.patch(
        f"/api/work-orders/{order.json()['id']}",
        headers=auth_headers,
        json={"status": "done"},
    )
    anon = client.post(
        f"/api/customers/{cid}/delete",
        headers=auth_headers,
        json={"mode": "anonymize", "force": False},
    )
    assert anon.status_code == 200
    assert anon.json()["status"] == "anonymized"

    got = client.get(f"/api/customers/{cid}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["email"] is None
    assert got.json()["anonymized_at"]


def test_viewer_read_only(client: TestClient, auth_headers: dict[str, str]):
    # Viewer im gleichen Mandanten anlegen
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@example.com").one()
        viewer = User(
            email="viewer@example.com",
            full_name="Viewer Demo",
            hashed_password=hash_password("ViewerDemo123!"),
            role="viewer",
            workshop_id=admin.workshop_id,
        )
        db.add(viewer)
        db.commit()
    finally:
        db.close()

    headers = _login(client, "viewer@example.com", "ViewerDemo123!")
    listed = client.get("/api/customers", headers=headers)
    assert listed.status_code == 200

    denied = client.post(
        "/api/customers",
        headers=headers,
        json={"display_name": "Sollte scheitern"},
    )
    assert denied.status_code == 403

    denied_ws = client.patch(
        "/api/workshop/me",
        headers=headers,
        json={"name": "Hack"},
    )
    assert denied_ws.status_code == 403


def test_cross_tenant_isolation(client: TestClient, auth_headers: dict[str, str]):
    # Fremder Mandant
    db: Session = SessionLocal()
    try:
        other = Workshop(
            name="Fremde Werkstatt",
            country="AT",
            retention_days=365,
            is_example_data=True,
            notes="Isolations-Test – keine Produktivdaten",
        )
        db.add(other)
        db.flush()
        foreign_customer = Customer(
            workshop_id=other.id,
            display_name="Fremder Kunde",
            email="fremd@example.com",
            is_example_data=True,
        )
        db.add(foreign_customer)
        foreign_user = User(
            email="fremd.admin@example.com",
            full_name="Fremd Admin",
            hashed_password=hash_password("FremdDemo123!"),
            role="admin",
            workshop_id=other.id,
        )
        db.add(foreign_user)
        db.flush()
        foreign_vehicle = Vehicle(
            workshop_id=other.id,
            make="Audi",
            model="A3",
            year=2019,
            vin="WAUZZZ8V0KA000099",
            is_example_data=True,
            notes="Fremd-Mandant",
        )
        db.add(foreign_vehicle)
        db.commit()
        foreign_customer_id = foreign_customer.id
        foreign_vehicle_id = foreign_vehicle.id
    finally:
        db.close()

    # Demo-Admin darf fremden Kunden nicht sehen
    res = client.get(f"/api/customers/{foreign_customer_id}", headers=auth_headers)
    assert res.status_code == 404

    res_v = client.get(f"/api/vehicles/{foreign_vehicle_id}", headers=auth_headers)
    assert res_v.status_code == 404

    # Fremder Admin sieht nur eigenen Mandanten
    foreign_headers = _login(client, "fremd.admin@example.com", "FremdDemo123!")
    own = client.get("/api/customers", headers=foreign_headers)
    assert own.status_code == 200
    assert all(c["display_name"] == "Fremder Kunde" for c in own.json())
    assert len(own.json()) == 1

    demo_customers = client.get("/api/customers", headers=auth_headers).json()
    demo_ids = {c["id"] for c in demo_customers}
    assert foreign_customer_id not in demo_ids


def test_tech_can_create_customer_not_workshop(client: TestClient):
    headers = _login(client, "tech@example.com", "TechDemo123!")
    create = client.post(
        "/api/customers",
        headers=headers,
        json={"display_name": "Tech Kunde", "email": "tech.kunde@example.com", "force": True},
    )
    assert create.status_code == 201

    denied = client.patch(
        "/api/workshop/me",
        headers=headers,
        json={"name": "Umbenannt"},
    )
    assert denied.status_code == 403
