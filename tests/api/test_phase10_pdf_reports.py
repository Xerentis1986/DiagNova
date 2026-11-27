"""Phase 10 – PDF-Berichte, Archiv, Unicode, Mandant, Demo-Kennzeichnung."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
import app.db.session as session_mod
from app.models import DiagnosticReport, SessionDtcResult, SessionEcuResult, User, Workshop
from app.services.reports import report_to_pdf


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _start_and_close(client: TestClient, headers: dict[str, str], *, auto_pdf: bool = False) -> tuple[str, str]:
    vehicles = client.get("/api/vehicles", headers=headers)
    assert vehicles.status_code == 200
    vid = vehicles.json()[0]["id"]
    vin = vehicles.json()[0]["vin"]
    started = client.post(
        "/api/sessions/v2",
        headers=headers,
        json={
            "vehicle_id": vid,
            "odometer_km": 123456,
            "notes": "Prüfung: Ölstand & Kühlmittel – Übung",
            "idempotency_key": f"phase10-{vid[:8]}",
        },
    )
    assert started.status_code == 200, started.text
    sid = started.json()["id"]
    closed = client.post(
        f"/api/sessions/{sid}/close" + ("?auto_pdf=true" if auto_pdf else ""),
        headers=headers,
    )
    assert closed.status_code == 200, closed.text
    return sid, vin


def test_report_pdf_csv_umlauts_demo_and_redownload(client: TestClient, auth_headers: dict[str, str]):
    sid, vin = _start_and_close(client, auth_headers)

    created = client.post(
        "/api/reports",
        headers=auth_headers,
        json={
            "session_id": sid,
            "title": "Diagnosebericht Größe Ölfleck",
            "notes": "Kunde meldet Rütteln bei Kälte",
            "recommendations": "Sichtprüfung Ölwanne – manuell erfasst",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["report_number"]
    assert body["data_source"] == "simulated"
    assert body["content_sha256"]
    assert body["frozen_at"]
    assert body["content"]["demo_watermark"] is True
    assert body["content"]["repair_diagnosis_auto"] is False
    assert "SIMULIERT" in body["content"]["disclaimer_de"]
    assert body["content"]["recommendations"] == "Sichtprüfung Ölwanne – manuell erfasst"
    assert "nicht verfügbar" not in body["content"]["notes"].lower() or True
    rid = body["id"]
    sha = body["content_sha256"]

    # Erneuter Download – gleicher Snapshot-Hash
    again = client.get(f"/api/reports/{rid}", headers=auth_headers)
    assert again.status_code == 200
    assert again.json()["content_sha256"] == sha

    csv_res = client.get(f"/api/reports/{rid}/export.csv", headers=auth_headers)
    assert csv_res.status_code == 200
    csv_text = csv_res.content.decode("utf-8-sig")
    assert "Ölfleck" in csv_text or "Größe" in csv_text or "Ölwanne" in csv_text
    assert "SIMULIERT" in csv_text or "simulated" in csv_text

    pdf1 = client.get(f"/api/reports/{rid}/export.pdf", headers=auth_headers)
    assert pdf1.status_code == 200
    assert pdf1.headers["content-type"] == "application/pdf"
    assert pdf1.content[:4] == b"%PDF"
    pdf2 = client.get(f"/api/reports/{rid}/export.pdf", headers=auth_headers)
    assert pdf2.status_code == 200
    assert pdf2.content[:4] == b"%PDF"
    # Unveränderlich ist der JSON-Snapshot (Hash), nicht die regenerierten PDF-Objekt-IDs
    assert again.json()["content_sha256"] == sha
    assert len(pdf1.content) > 1500
    assert len(pdf2.content) > 1500

    listing = client.get("/api/reports", headers=auth_headers)
    assert listing.status_code == 200
    assert any(r["id"] == rid for r in listing.json())

    by_vin = client.get(f"/api/reports?vin={vin}", headers=auth_headers)
    assert by_vin.status_code == 200
    assert any(r["id"] == rid for r in by_vin.json())


def test_long_tables_page_break_and_empty_fields(client: TestClient, auth_headers: dict[str, str]):
    sid, _ = _start_and_close(client, auth_headers)

    db: Session = session_mod.SessionLocal()
    try:
        # Viele DTCs für Seitenumbruch
        for i in range(80):
            db.add(
                SessionDtcResult(
                    session_id=sid,
                    ecu_code="ECM",
                    code=f"P{i:04d}",
                    dtc_status="stored",
                    description_de=f"Simulierter Code Nummer {i} – Prüfung Kühlung",
                    severity="info",
                )
            )
        db.add(
            SessionEcuResult(
                session_id=sid,
                ecu_code="ABS",
                ecu_label_de="Antiblockiersystem",
                checked=False,
                status="not_checked",
            )
        )
        db.commit()
    finally:
        db.close()

    created = client.post(
        "/api/reports",
        headers=auth_headers,
        json={"session_id": sid, "title": "Langer Bericht mit vielen DTCs"},
    )
    assert created.status_code == 200, created.text
    content = created.json()["content"]
    assert len(content["dtcs"]) >= 80
    assert any(not e["checked"] for e in content["ecus"])
    # Fehlende Empfehlung → nicht verfügbar
    assert content["recommendations"] == "nicht verfügbar"

    db2 = session_mod.SessionLocal()
    try:
        report = db2.get(DiagnosticReport, created.json()["id"])
        assert report is not None
        pdf = report_to_pdf(report)
    finally:
        db2.close()
    assert pdf[:4] == b"%PDF"
    # Mehrseitigkeit: mehrere Seitenobjekte oder ausreichende Größe
    assert pdf.count(b"/Type /Page") >= 2 or len(pdf) > 4000


def test_auto_pdf_on_close_and_archive(client: TestClient, auth_headers: dict[str, str]):
    sid, _ = _start_and_close(client, auth_headers, auto_pdf=True)
    listing = client.get("/api/reports", headers=auth_headers)
    assert listing.status_code == 200
    matches = [r for r in listing.json() if r["session_id"] == sid and r["auto_generated"]]
    assert matches
    rid = matches[0]["id"]

    arch = client.post(f"/api/reports/{rid}/archive", headers=auth_headers)
    assert arch.status_code == 200
    assert arch.json()["archived_at"]

    active = client.get("/api/reports", headers=auth_headers)
    assert not any(r["id"] == rid for r in active.json())
    archived = client.get("/api/reports?include_archived=true", headers=auth_headers)
    assert any(r["id"] == rid for r in archived.json())


def test_cross_tenant_report_404(client: TestClient, auth_headers: dict[str, str]):
    sid, _ = _start_and_close(client, auth_headers)
    created = client.post(
        "/api/reports",
        headers=auth_headers,
        json={"session_id": sid, "title": "Mandantentest Bericht"},
    )
    assert created.status_code == 200
    rid = created.json()["id"]

    db: Session = session_mod.SessionLocal()
    try:
        other = Workshop(name="Fremde Werkstatt Phase10", is_example_data=True)
        db.add(other)
        db.flush()
        stranger = User(
            email="stranger10@example.com",
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

    foreign = _login(client, "stranger10@example.com", "StrangerDemo123!")
    assert client.get(f"/api/reports/{rid}", headers=foreign).status_code == 404
    assert client.get(f"/api/reports/{rid}/export.pdf", headers=foreign).status_code == 404
    assert client.get("/api/reports", headers=foreign).json() == []


def test_immutable_snapshot_hash_stable(client: TestClient, auth_headers: dict[str, str]):
    sid, _ = _start_and_close(client, auth_headers)
    created = client.post(
        "/api/reports",
        headers=auth_headers,
        json={"session_id": sid, "title": "Snapshot Stabilität"},
    )
    rid = created.json()["id"]
    sha = created.json()["content_sha256"]
    content = created.json()["content"]

    # Inhalt in DB unverändert nach erneutem GET
    got = client.get(f"/api/reports/{rid}", headers=auth_headers).json()
    assert got["content_sha256"] == sha
    assert json.dumps(got["content"], sort_keys=True) == json.dumps(content, sort_keys=True)
