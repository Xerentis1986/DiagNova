from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.models import DiagnosticReport, DiagnosticSession, Vehicle
from app.services import simulator


def build_report_payload(db: Session, session: DiagnosticSession) -> dict:
    vehicle = db.get(Vehicle, session.vehicle_id)
    assert vehicle is not None
    dtcs = simulator.list_dtcs(vehicle.id)
    live = simulator.live_data(vehicle.id, vehicle.vin)
    return {
        "data_source": "simulated",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer_de": "Dieser Bericht basiert auf SIMULIERTEN Daten. Keine echte Fahrzeugdiagnose.",
        "vehicle": {
            "id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "vin": vehicle.vin,
            "license_plate": vehicle.license_plate,
            "is_example_data": vehicle.is_example_data,
        },
        "session": {
            "id": session.id,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "status": session.status,
            "data_source": session.data_source,
        },
        "dtcs": [d.model_dump() for d in dtcs],
        "live_snapshot": {
            "readings": [r.model_dump(mode="json") for r in live.readings],
            "readiness": live.readiness,
            "freeze_frame": live.freeze_frame,
        },
    }


def create_report(db: Session, session: DiagnosticSession, title: str) -> DiagnosticReport:
    payload = build_report_payload(db, session)
    report = DiagnosticReport(
        session_id=session.id,
        title=title,
        content_json=json.dumps(payload, ensure_ascii=False),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def report_to_csv(report: DiagnosticReport) -> str:
    content = json.loads(report.content_json)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Feld", "Wert"])
    writer.writerow(["Hinweis", content.get("disclaimer_de", "")])
    writer.writerow(["Datenquelle", content.get("data_source", "")])
    vehicle = content.get("vehicle", {})
    writer.writerow(["Fahrzeug", f"{vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('year')})"])
    writer.writerow(["VIN", vehicle.get("vin", "")])
    writer.writerow([])
    writer.writerow(["DTC", "Status", "Beschreibung", "Schwere"])
    for dtc in content.get("dtcs", []):
        writer.writerow([dtc["code"], dtc["status"], dtc["description_de"], dtc["severity"]])
    writer.writerow([])
    writer.writerow(["PID", "Name", "Wert", "Einheit"])
    for reading in content.get("live_snapshot", {}).get("readings", []):
        writer.writerow([reading["pid_hex"], reading["name"], reading["value"], reading["unit"]])
    return buf.getvalue()


def report_to_pdf(report: DiagnosticReport) -> bytes:
    content = json.loads(report.content_json)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "DiagNova Diagnosebericht (SIMULIERT)")
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawString(40, y, content.get("disclaimer_de", ""))
    y -= 20
    vehicle = content.get("vehicle", {})
    lines = [
        f"Titel: {report.title}",
        f"Fahrzeug: {vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('year')})",
        f"VIN: {vehicle.get('vin')}",
        f"Kennzeichen: {vehicle.get('license_plate') or '-'}",
        f"Erstellt: {content.get('generated_at')}",
        "",
        "Fehlercodes:",
    ]
    for line in lines:
        c.drawString(40, y, line)
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
    for dtc in content.get("dtcs", []):
        c.drawString(50, y, f"{dtc['code']} [{dtc['status']}] – {dtc['description_de']}")
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
    y -= 10
    c.drawString(40, y, "Live-PIDs (Snapshot):")
    y -= 14
    for reading in content.get("live_snapshot", {}).get("readings", []):
        c.drawString(
            50,
            y,
            f"{reading['pid_hex']} {reading['name']}: {reading['value']} {reading['unit']}",
        )
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
    c.showPage()
    c.save()
    return buffer.getvalue()
