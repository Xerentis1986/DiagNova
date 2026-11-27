"""Phase 10 – PDF-Diagnoseberichte, unveränderliche Snapshots, Archiv."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import (
    Customer,
    DiagnosticReport,
    DiagnosticSession,
    SessionDtcResult,
    SessionEcuResult,
    SessionMeasurementSample,
    User,
    Vehicle,
    Workshop,
)
from app.services import simulator

NA = "nicht verfügbar"
REPORT_DATA_VERSION = "phase10-v1"
_FONTS_REGISTERED = False
_FONT_REG = "DiagNovaSans"
_FONT_BOLD = "DiagNovaSans-Bold"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _register_fonts() -> tuple[str, str]:
    """Unicode-fähige Schriften (Umlaute). Fallback Helvetica nur ohne äöüß."""
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return _FONT_REG, _FONT_BOLD
    candidates = [
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont(_FONT_REG, str(regular)))
            pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(bold)))
            _FONTS_REGISTERED = True
            return _FONT_REG, _FONT_BOLD
    _FONTS_REGISTERED = True
    return "Helvetica", "Helvetica-Bold"


def _na(value: Any) -> str:
    if value is None:
        return NA
    if isinstance(value, str) and not value.strip():
        return NA
    return str(value)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _next_report_number(db: Session, workshop_id: str) -> str:
    year = _now().year
    prefix = f"DN-{year}-"
    existing = (
        db.query(DiagnosticReport.report_number)
        .filter(
            DiagnosticReport.workshop_id == workshop_id,
            DiagnosticReport.report_number.like(f"{prefix}%"),
        )
        .all()
    )
    max_n = 0
    for (num,) in existing:
        if not num:
            continue
        m = re.search(r"(\d+)$", num)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"{prefix}{max_n + 1:06d}"


def _session_ecus(db: Session, session_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(SessionEcuResult)
        .filter(SessionEcuResult.session_id == session_id)
        .order_by(SessionEcuResult.ecu_code)
        .all()
    )
    return [
        {
            "ecu_code": r.ecu_code,
            "ecu_label_de": r.ecu_label_de,
            "checked": bool(r.checked),
            "protocol_name": r.protocol_name,
            "address_hex": r.address_hex,
            "status": r.status,
            "notes": r.notes,
        }
        for r in rows
    ]


def _session_dtcs(db: Session, session_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(SessionDtcResult)
        .filter(SessionDtcResult.session_id == session_id)
        .order_by(SessionDtcResult.ecu_code, SessionDtcResult.code)
        .all()
    )
    return [
        {
            "ecu_code": r.ecu_code,
            "code": r.code,
            "status": r.dtc_status,
            "description_de": r.description_de or NA,
            "severity": r.severity,
        }
        for r in rows
    ]


def _session_measurements(db: Session, session_id: str, limit: int = 200) -> list[dict[str, Any]]:
    rows = (
        db.query(SessionMeasurementSample)
        .filter(SessionMeasurementSample.session_id == session_id)
        .order_by(SessionMeasurementSample.recorded_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "pid_hex": r.pid_hex,
            "name": r.name,
            "value": r.value,
            "unit": r.unit,
            "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            "data_source": r.data_source,
        }
        for r in rows
    ]


def build_report_payload(
    db: Session,
    session: DiagnosticSession,
    *,
    notes: str | None = None,
    recommendations: str | None = None,
    report_number: str | None = None,
) -> dict[str, Any]:
    """Snapshot aus Sitzung/Fahrzeug/Werkstatt. Keine erfundenen Testergebnisse oder Reparaturdiagnosen."""
    vehicle = db.get(Vehicle, session.vehicle_id)
    assert vehicle is not None
    workshop = db.get(Workshop, session.workshop_id) if session.workshop_id else None
    customer = None
    if vehicle.customer_id:
        customer = db.get(Customer, vehicle.customer_id)
    technician = db.get(User, session.user_id)

    ecus = _session_ecus(db, session.id)
    dtcs = _session_dtcs(db, session.id)
    measurements = _session_measurements(db, session.id)

    # Fallback nur wenn noch kein Sitzungs-Snapshot: Simulator, klar als simulated
    used_simulator_fallback = False
    if not dtcs and not ecus:
        used_simulator_fallback = True
        sim_dtcs = simulator.list_dtcs(vehicle.id)
        live = simulator.live_data(vehicle.id, vehicle.vin)
        dtcs = [
            {
                "ecu_code": "ECM",
                "code": d.code,
                "status": d.status,
                "description_de": d.description_de,
                "severity": d.severity,
            }
            for d in sim_dtcs
        ]
        measurements = [
            {
                "pid_hex": r.pid_hex,
                "name": r.name,
                "value": r.value,
                "unit": r.unit,
                "recorded_at": None,
                "data_source": "simulated",
            }
            for r in live.readings
        ]
        freeze_frame = live.freeze_frame
        readiness = live.readiness
        ecus = [
            {
                "ecu_code": "ECM",
                "ecu_label_de": "Motorsteuergerät (OBD)",
                "checked": True,
                "protocol_name": session.protocol_name,
                "address_hex": "7E8",
                "status": "ok",
                "notes": None,
            }
        ]
    else:
        try:
            freeze_frame = json.loads(session.freeze_frame_json) if session.freeze_frame_json else None
        except json.JSONDecodeError:
            freeze_frame = None
        try:
            readiness = json.loads(session.readiness_json) if session.readiness_json else None
        except json.JSONDecodeError:
            readiness = None

    data_source = session.data_source or "simulated"
    if used_simulator_fallback:
        data_source = "simulated"

    is_demo = data_source != "live" or bool(vehicle.is_example_data) or bool(
        workshop and workshop.is_example_data
    )

    disclaimer = (
        "Dieser Bericht basiert auf SIMULIERTEN / DEMO-Daten. Keine echte Fahrzeugdiagnose. "
        "Keine automatisch erfundene Reparaturdiagnose."
        if is_demo
        else "Bericht aus erfassten Diagnosedaten. Fehlende Felder sind als „nicht verfügbar“ gekennzeichnet. "
        "Keine automatisch erfundene Reparaturdiagnose."
    )

    checked = [e for e in ecus if e.get("checked")]
    unchecked = [e for e in ecus if not e.get("checked")]

    payload: dict[str, Any] = {
        "schema_version": REPORT_DATA_VERSION,
        "data_source": data_source,
        "authenticity": "simulated" if is_demo else "recorded",
        "demo_watermark": is_demo,
        "generated_at": _now().isoformat(),
        "report_number": report_number,
        "disclaimer_de": disclaimer,
        "workshop": {
            "id": workshop.id if workshop else None,
            "name": workshop.name if workshop else NA,
            "legal_name": workshop.legal_name if workshop else None,
            "email": workshop.email if workshop else None,
            "phone": workshop.phone if workshop else None,
            "street": workshop.street if workshop else None,
            "postal_code": workshop.postal_code if workshop else None,
            "city": workshop.city if workshop else None,
            "country": workshop.country if workshop else None,
            "logo_data_url": workshop.logo_data_url if workshop else None,
            "is_example_data": bool(workshop.is_example_data) if workshop else True,
        },
        "customer": {
            "id": customer.id if customer else None,
            "display_name": customer.display_name if customer else NA,
            "email": customer.email if customer else None,
            "phone": customer.phone if customer else None,
            "city": customer.city if customer else None,
        }
        if customer
        else {
            "id": None,
            "display_name": NA,
            "email": None,
            "phone": None,
            "city": None,
        },
        "vehicle": {
            "id": vehicle.id,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "vin": vehicle.vin,
            "license_plate": vehicle.license_plate,
            "engine": vehicle.engine,
            "odometer_km": session.odometer_km
            if session.odometer_km is not None
            else vehicle.odometer_km,
            "is_example_data": vehicle.is_example_data,
        },
        "session": {
            "id": session.id,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "status": session.status,
            "data_source": session.data_source,
            "adapter_name": session.adapter_name,
            "protocol_name": session.protocol_name,
            "odometer_km": session.odometer_km,
            "technician": technician.full_name if technician else NA,
            "abort_reason": session.abort_reason,
        },
        "ecus_checked": checked,
        "ecus_not_checked": unchecked,
        "ecus": ecus,
        "dtcs": dtcs,
        "measurements": measurements,
        "freeze_frame": freeze_frame if freeze_frame else NA,
        "readiness": readiness if readiness else NA,
        "notes": notes if notes else (session.notes or NA),
        # Nur manuelle Empfehlungen – nie automatisch erfunden
        "recommendations": recommendations if recommendations else NA,
        "repair_diagnosis_auto": False,
    }
    return payload


def create_report(
    db: Session,
    session: DiagnosticSession,
    title: str,
    *,
    notes: str | None = None,
    recommendations: str | None = None,
    auto_generated: bool = False,
) -> DiagnosticReport:
    workshop_id = session.workshop_id
    report_number = _next_report_number(db, workshop_id) if workshop_id else None
    payload = build_report_payload(
        db,
        session,
        notes=notes,
        recommendations=recommendations,
        report_number=report_number,
    )
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    now = _now()
    vehicle = db.get(Vehicle, session.vehicle_id)
    report = DiagnosticReport(
        session_id=session.id,
        workshop_id=workshop_id,
        vehicle_id=session.vehicle_id,
        customer_id=vehicle.customer_id if vehicle else None,
        report_number=report_number,
        title=title,
        content_json=content,
        data_source=payload.get("data_source", "simulated"),
        data_version=REPORT_DATA_VERSION,
        content_sha256=_sha256_text(content),
        notes=notes,
        recommendations=recommendations,
        auto_generated=auto_generated,
        frozen_at=now,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(
    db: Session,
    workshop_id: str,
    *,
    q: str | None = None,
    vin: str | None = None,
    include_archived: bool = False,
    include_deleted: bool = False,
    limit: int = 100,
) -> list[DiagnosticReport]:
    query = db.query(DiagnosticReport).filter(DiagnosticReport.workshop_id == workshop_id)
    if not include_deleted:
        query = query.filter(DiagnosticReport.deleted_at.is_(None))
    if not include_archived:
        query = query.filter(DiagnosticReport.archived_at.is_(None))
    if vin:
        v = vin.strip().upper()
        query = query.join(Vehicle, Vehicle.id == DiagnosticReport.vehicle_id).filter(
            Vehicle.vin.ilike(v)
        )
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                DiagnosticReport.title.ilike(like),
                DiagnosticReport.report_number.ilike(like),
                DiagnosticReport.notes.ilike(like),
            )
        )
    return query.order_by(DiagnosticReport.created_at.desc()).limit(limit).all()


def archive_report(db: Session, report: DiagnosticReport) -> DiagnosticReport:
    if report.archived_at is None:
        report.archived_at = _now()
        db.commit()
        db.refresh(report)
    return report


def soft_delete_report(db: Session, report: DiagnosticReport) -> DiagnosticReport:
    if report.deleted_at is None:
        report.deleted_at = _now()
        if report.archived_at is None:
            report.archived_at = report.deleted_at
        db.commit()
        db.refresh(report)
    return report


def purge_expired_reports(db: Session, workshop: Workshop) -> int:
    """Soft-Delete nach Aufbewahrungsfrist (workshop.retention_days)."""
    days = workshop.retention_days or 365
    cutoff = _now() - timedelta(days=days)
    rows = (
        db.query(DiagnosticReport)
        .filter(
            DiagnosticReport.workshop_id == workshop.id,
            DiagnosticReport.deleted_at.is_(None),
            DiagnosticReport.created_at < cutoff,
        )
        .all()
    )
    for r in rows:
        r.deleted_at = _now()
        if r.archived_at is None:
            r.archived_at = r.deleted_at
    if rows:
        db.commit()
    return len(rows)


def report_summary(report: DiagnosticReport) -> dict[str, Any]:
    content = json.loads(report.content_json)
    vehicle = content.get("vehicle") or {}
    return {
        "id": report.id,
        "session_id": report.session_id,
        "workshop_id": report.workshop_id,
        "vehicle_id": report.vehicle_id,
        "customer_id": report.customer_id,
        "report_number": report.report_number,
        "title": report.title,
        "data_source": report.data_source,
        "data_version": report.data_version,
        "content_sha256": report.content_sha256,
        "auto_generated": report.auto_generated,
        "demo_watermark": bool(content.get("demo_watermark")),
        "created_at": report.created_at,
        "frozen_at": report.frozen_at,
        "archived_at": report.archived_at,
        "deleted_at": report.deleted_at,
        "vehicle_label": f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip() or NA,
        "vin": vehicle.get("vin"),
        "dtc_count": len(content.get("dtcs") or []),
    }


def report_to_csv(report: DiagnosticReport) -> str:
    content = json.loads(report.content_json)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Feld", "Wert"])
    writer.writerow(["Berichtsnummer", content.get("report_number") or report.report_number or NA])
    writer.writerow(["Hinweis", content.get("disclaimer_de", "")])
    writer.writerow(["Datenquelle", content.get("data_source", "")])
    writer.writerow(["Datenversion", report.data_version or NA])
    writer.writerow(["Snapshot-Hash", report.content_sha256 or NA])
    workshop = content.get("workshop") or {}
    writer.writerow(["Werkstatt", workshop.get("name") or NA])
    customer = content.get("customer") or {}
    writer.writerow(["Kunde", customer.get("display_name") or NA])
    vehicle = content.get("vehicle") or {}
    writer.writerow(
        ["Fahrzeug", f"{vehicle.get('make')} {vehicle.get('model')} ({vehicle.get('year')})"]
    )
    writer.writerow(["VIN", vehicle.get("vin") or NA])
    writer.writerow(["Kennzeichen", vehicle.get("license_plate") or NA])
    writer.writerow(["Kilometerstand", _na(vehicle.get("odometer_km"))])
    session = content.get("session") or {}
    writer.writerow(["Adapter", _na(session.get("adapter_name"))])
    writer.writerow(["Protokoll", _na(session.get("protocol_name"))])
    writer.writerow(["Notizen", content.get("notes") or NA])
    writer.writerow(["Empfehlungen (manuell)", content.get("recommendations") or NA])
    writer.writerow([])
    writer.writerow(["ECU", "Bezeichnung", "Geprüft", "Status", "Protokoll"])
    for ecu in content.get("ecus") or []:
        writer.writerow(
            [
                ecu.get("ecu_code"),
                ecu.get("ecu_label_de"),
                "ja" if ecu.get("checked") else "nein",
                ecu.get("status"),
                ecu.get("protocol_name") or NA,
            ]
        )
    writer.writerow([])
    writer.writerow(["DTC", "ECU", "Status", "Beschreibung", "Schwere"])
    for dtc in content.get("dtcs") or []:
        writer.writerow(
            [
                dtc.get("code"),
                dtc.get("ecu_code"),
                dtc.get("status"),
                dtc.get("description_de"),
                dtc.get("severity"),
            ]
        )
    writer.writerow([])
    writer.writerow(["PID", "Name", "Wert", "Einheit", "Zeit"])
    for reading in content.get("measurements") or []:
        writer.writerow(
            [
                reading.get("pid_hex"),
                reading.get("name"),
                reading.get("value"),
                reading.get("unit"),
                reading.get("recorded_at") or NA,
            ]
        )
    return buf.getvalue()


def _draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, max_width: float, font: str, size: int) -> float:
    c.setFont(font, size)
    words = str(text).split()
    if not words:
        return y
    line = words[0]
    for w in words[1:]:
        trial = f"{line} {w}"
        if c.stringWidth(trial, font, size) <= max_width:
            line = trial
        else:
            c.drawString(x, y, line)
            y -= size + 3
            line = w
    c.drawString(x, y, line)
    return y - (size + 3)


_BRAND_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
_BRAND_SYMBOL = _BRAND_ASSET_DIR / "diagnova_symbol_128.png"
_BRAND_WORDMARK = _BRAND_ASSET_DIR / "diagnova_wordmark_800.png"


def _draw_image_file(c: canvas.Canvas, path: Path, x: float, y: float, max_w: float, max_h: float) -> bool:
    if not path.is_file():
        return False
    try:
        from reportlab.lib.utils import ImageReader

        reader = ImageReader(str(path))
        iw, ih = reader.getSize()
        scale = min(max_w / iw, max_h / ih, 1.0)
        c.drawImage(reader, x, y - ih * scale, width=iw * scale, height=ih * scale, mask="auto")
        return True
    except Exception:
        return False


def _maybe_draw_logo(c: canvas.Canvas, data_url: str | None, x: float, y: float, max_w: float, max_h: float) -> None:
    if data_url and data_url.startswith("data:image"):
        try:
            _header, b64 = data_url.split(",", 1)
            raw = base64.b64decode(b64)
            img = io.BytesIO(raw)
            from reportlab.lib.utils import ImageReader

            reader = ImageReader(img)
            iw, ih = reader.getSize()
            scale = min(max_w / iw, max_h / ih, 1.0)
            c.drawImage(reader, x, y - ih * scale, width=iw * scale, height=ih * scale, mask="auto")
            return
        except Exception:
            pass
    # Fallback: DiagNova Brand-Symbol (kein Werkstattlogo)
    if not _draw_image_file(c, _BRAND_SYMBOL, x, y, max_w, max_h):
        _draw_image_file(c, _BRAND_WORDMARK, x, y, max_w * 1.4, max_h)


def report_to_pdf(report: DiagnosticReport) -> bytes:
    content = json.loads(report.content_json)
    font, font_bold = _register_fonts()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 18 * mm
    usable = width - 2 * margin
    page_num = 1

    def footer(page: int) -> None:
        c.setFont(font, 8)
        num = content.get("report_number") or report.report_number or report.id[:8]
        c.drawString(margin, 10 * mm, f"DiagNova · {num} · {_na(content.get('data_source'))}")
        c.drawRightString(width - margin, 10 * mm, f"Seite {page}")
        c.line(margin, 12 * mm, width - margin, 12 * mm)

    def header() -> float:
        y = height - 15 * mm
        workshop = content.get("workshop") or {}
        _maybe_draw_logo(c, workshop.get("logo_data_url"), margin, y + 2 * mm, 28 * mm, 14 * mm)
        c.setFont(font_bold, 14)
        c.drawString(margin + 32 * mm, y, workshop.get("name") or "DiagNova")
        y -= 6 * mm
        c.setFont(font, 9)
        addr_bits = [
            workshop.get("street"),
            " ".join(filter(None, [workshop.get("postal_code"), workshop.get("city")])),
            workshop.get("phone"),
            workshop.get("email"),
        ]
        addr = " · ".join(str(a) for a in addr_bits if a)
        if addr:
            y = _draw_wrapped(c, addr, margin + 32 * mm, y, usable - 32 * mm, font, 8)
        c.setFont(font_bold, 12)
        y -= 2 * mm
        c.drawString(margin, y, "Diagnosebericht")
        y -= 5 * mm
        c.setFont(font, 9)
        c.drawString(margin, y, f"Nr.: {_na(content.get('report_number') or report.report_number)}")
        c.drawRightString(
            width - margin,
            y,
            f"Datum: {_na((content.get('generated_at') or '')[:19].replace('T', ' '))} UTC",
        )
        y -= 4 * mm
        c.line(margin, y, width - margin, y)
        return y - 6 * mm

    def new_page() -> float:
        nonlocal page_num
        footer(page_num)
        c.showPage()
        page_num += 1
        return header()

    def ensure(y: float, need: float = 16) -> float:
        if y < 20 * mm + need:
            return new_page()
        return y

    y = header()

    # Demo-Wasserzeichen
    if content.get("demo_watermark"):
        c.saveState()
        c.setFont(font_bold, 48)
        c.setFillGray(0.85)
        c.translate(width / 2, height / 2)
        c.rotate(35)
        c.drawCentredString(0, 0, "DEMO / SIMULIERT")
        c.restoreState()

    y = _draw_wrapped(c, content.get("disclaimer_de", ""), margin, y, usable, font, 8)
    y -= 2 * mm

    vehicle = content.get("vehicle") or {}
    customer = content.get("customer") or {}
    session = content.get("session") or {}

    meta_lines = [
        f"Kunde: {_na(customer.get('display_name'))}",
        f"Fahrzeug: {_na(vehicle.get('make'))} {_na(vehicle.get('model'))} ({_na(vehicle.get('year'))})",
        f"VIN: {_na(vehicle.get('vin'))} · Kennzeichen: {_na(vehicle.get('license_plate'))}",
        f"Kilometerstand: {_na(vehicle.get('odometer_km'))} · Motor: {_na(vehicle.get('engine'))}",
        f"Adapter: {_na(session.get('adapter_name'))} · Protokoll: {_na(session.get('protocol_name'))}",
        f"Techniker: {_na(session.get('technician'))} · Sitzungsstatus: {_na(session.get('status'))}",
        f"Datenquelle: {_na(content.get('data_source'))} · Version: {_na(report.data_version)}",
        f"Snapshot-Hash: {_na((report.content_sha256 or '')[:16])}…",
    ]
    for line in meta_lines:
        y = ensure(y)
        y = _draw_wrapped(c, line, margin, y, usable, font, 9)

    y = ensure(y, 20)
    y -= 2 * mm
    c.setFont(font_bold, 10)
    c.drawString(margin, y, "Steuergeräte (geprüft / nicht geprüft)")
    y -= 5 * mm
    c.setFont(font, 8)
    for ecu in content.get("ecus") or []:
        y = ensure(y)
        flag = "geprüft" if ecu.get("checked") else "nicht geprüft"
        line = (
            f"{ecu.get('ecu_code')} – {ecu.get('ecu_label_de')} [{flag}] "
            f"Status={ecu.get('status')} Protokoll={_na(ecu.get('protocol_name'))}"
        )
        y = _draw_wrapped(c, line, margin, y, usable, font, 8)
    if not content.get("ecus"):
        y = _draw_wrapped(c, NA, margin, y, usable, font, 8)

    y = ensure(y, 20)
    y -= 2 * mm
    c.setFont(font_bold, 10)
    c.drawString(margin, y, "Fehlercodes (DTC)")
    y -= 5 * mm
    dtcs = content.get("dtcs") or []
    if not dtcs:
        y = _draw_wrapped(c, NA, margin, y, usable, font, 8)
    for dtc in dtcs:
        y = ensure(y)
        line = (
            f"{dtc.get('code')} [{dtc.get('status')}] ECU={dtc.get('ecu_code')} "
            f"– {dtc.get('description_de')} ({dtc.get('severity')})"
        )
        y = _draw_wrapped(c, line, margin, y, usable, font, 8)

    y = ensure(y, 20)
    y -= 2 * mm
    c.setFont(font_bold, 10)
    c.drawString(margin, y, "Messwerte")
    y -= 5 * mm
    measurements = content.get("measurements") or []
    if not measurements:
        y = _draw_wrapped(c, NA, margin, y, usable, font, 8)
    for reading in measurements:
        y = ensure(y)
        line = (
            f"{reading.get('pid_hex')} {reading.get('name')}: "
            f"{reading.get('value')} {reading.get('unit')}"
        )
        y = _draw_wrapped(c, line, margin, y, usable, font, 8)

    y = ensure(y, 20)
    y -= 2 * mm
    c.setFont(font_bold, 10)
    c.drawString(margin, y, "Freeze-Frame")
    y -= 5 * mm
    ff = content.get("freeze_frame")
    if ff == NA or ff is None:
        y = _draw_wrapped(c, NA, margin, y, usable, font, 8)
    elif isinstance(ff, dict):
        for k, v in ff.items():
            y = ensure(y)
            y = _draw_wrapped(c, f"{k}: {v}", margin, y, usable, font, 8)
    else:
        y = _draw_wrapped(c, str(ff), margin, y, usable, font, 8)

    y = ensure(y, 20)
    y -= 2 * mm
    c.setFont(font_bold, 10)
    c.drawString(margin, y, "Notizen")
    y -= 5 * mm
    y = _draw_wrapped(c, _na(content.get("notes")), margin, y, usable, font, 8)

    y = ensure(y, 20)
    y -= 2 * mm
    c.setFont(font_bold, 10)
    c.drawString(margin, y, "Empfehlungen (nur manuell, nicht automatisch)")
    y -= 5 * mm
    y = _draw_wrapped(c, _na(content.get("recommendations")), margin, y, usable, font, 8)

    footer(page_num)
    c.save()
    return buffer.getvalue()


def count_reports(db: Session, workshop_id: str) -> int:
    return (
        db.query(func.count(DiagnosticReport.id))
        .filter(
            DiagnosticReport.workshop_id == workshop_id,
            DiagnosticReport.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )
