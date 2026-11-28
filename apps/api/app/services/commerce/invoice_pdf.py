"""PDF-Rechnungen (unveränderlicher Snapshot) – Phase 22."""

from __future__ import annotations

import hashlib
import io
import json
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.models.commerce import Invoice


def render_invoice_pdf(inv: Invoice) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 20 * mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, "DiagNova – Rechnung" if inv.doc_type == "invoice" else "DiagNova – Gutschrift")
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    lines = [
        f"Nummer: {inv.number}",
        f"Status: {inv.status}",
        f"Währung: {inv.currency}",
        f"Netto: {inv.net_cents / 100:.2f}",
        f"USt: {inv.vat_cents / 100:.2f} ({inv.vat_rate_bp / 100:.2f} %)",
        f"Brutto: {inv.gross_cents / 100:.2f}",
        f"Szenario: {inv.tax_scenario}",
        f"Reverse Charge: {'ja' if inv.reverse_charge else 'nein'}",
        f"OSS: {'ja' if inv.oss_applicable else 'nein'}",
        f"Ausgestellt: {inv.issued_at.isoformat() if inv.issued_at else '—'}",
        f"Fällig: {inv.due_at.isoformat() if inv.due_at else '—'}",
        f"Beispiel/Demo-Flag: {inv.is_example_data}",
    ]
    for line in lines:
        c.drawString(20 * mm, y, line)
        y -= 6 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Positionen")
    y -= 7 * mm
    c.setFont("Helvetica", 9)
    try:
        items = json.loads(inv.line_items_json or "[]")
    except json.JSONDecodeError:
        items = []
    for it in items:
        if not isinstance(it, dict):
            continue
        label = str(it.get("label") or it.get("description") or it.get("plan_code") or "Position")
        amount = it.get("gross_cents") or it.get("net_cents") or 0
        c.drawString(20 * mm, y, f"- {label}: {int(amount) / 100:.2f} {inv.currency}")
        y -= 5 * mm
        if y < 30 * mm:
            c.showPage()
            y = h - 20 * mm
            c.setFont("Helvetica", 9)

    y -= 8 * mm
    c.setFont("Helvetica", 8)
    note = inv.notes_de or ""
    c.drawString(20 * mm, y, "Hinweis: Steuerkonfiguration draft_needs_review bis fachliche Freigabe.")
    y -= 5 * mm
    if note:
        c.drawString(20 * mm, max(20 * mm, y), note[:110])

    # Integritätshinweis (Hash über kanonischen Snapshot)
    snap = json.dumps(
        {
            "id": inv.id,
            "number": inv.number,
            "gross_cents": inv.gross_cents,
            "net_cents": inv.net_cents,
            "vat_cents": inv.vat_cents,
            "tax_scenario": inv.tax_scenario,
            "line_items_json": inv.line_items_json,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    digest = hashlib.sha256(snap).hexdigest()
    c.setFont("Helvetica", 7)
    c.drawString(20 * mm, 12 * mm, f"SHA-256 Snapshot: {digest}")
    c.drawString(20 * mm, 8 * mm, f"Gerendert: {datetime.now(timezone.utc).isoformat()}")
    c.showPage()
    c.save()
    return buf.getvalue()
