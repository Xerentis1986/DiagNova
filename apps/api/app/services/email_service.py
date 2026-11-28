"""E-Mail-Versand: SMTP konfigurierbar; ohne SMTP ehrlicher Queue-/Log-Modus.

Keine erfundenen Zustellungen. Prod-SMTP erst nach Freigabe/Secrets.
"""

from __future__ import annotations

import hashlib
import json
import smtplib
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any

from app.core.config import get_settings


@dataclass
class OutboundMail:
    id: str
    template: str
    to_email: str
    subject: str
    body_text: str
    status: str  # queued | sent | failed | dry_run
    detail: str
    created_at: str


_MAIL_LOG: list[OutboundMail] = []


TEMPLATES: dict[str, tuple[str, str]] = {
    "registration": (
        "DiagNova – Registrierung",
        "Willkommen bei DiagNova.\nBitte bestätigen Sie Ihre E-Mail über den Link in der Anwendung.",
    ),
    "email_confirm": (
        "DiagNova – E-Mail bestätigen",
        "Bitte bestätigen Sie Ihre E-Mail-Adresse.",
    ),
    "password_reset": (
        "DiagNova – Passwort zurücksetzen",
        "Es wurde eine Passwortzurücksetzung angefordert. Nutzen Sie den Link in der App.",
    ),
    "subscription_confirm": (
        "DiagNova – Abonnement bestätigt",
        "Ihr Abonnement wurde bestätigt.",
    ),
    "invoice": (
        "DiagNova – Rechnung",
        "Im Anhang bzw. in der App finden Sie Ihre Rechnung.",
    ),
    "payment_reminder": (
        "DiagNova – Zahlungserinnerung",
        "Bitte begleichen Sie die offene Rechnung.",
    ),
    "cancellation": (
        "DiagNova – Kündigung bestätigt",
        "Ihre Kündigung wurde registriert.",
    ),
    "license_activation": (
        "DiagNova – Lizenz aktiviert",
        "Ihre Lizenz wurde aktiviert.",
    ),
    "security_alert": (
        "DiagNova – Sicherheitsmeldung",
        "Es gab ein sicherheitsrelevantes Ereignis an Ihrem Konto.",
    ),
}


def email_status() -> dict[str, Any]:
    s = get_settings()
    host = (s.smtp_host or "").strip()
    return {
        "smtp_configured": bool(host and s.smtp_from_email),
        "smtp_host": host or None,
        "from_email": s.smtp_from_email or None,
        "dry_run_default": not bool(host),
        "templates": sorted(TEMPLATES.keys()),
        "queued_or_logged": len(_MAIL_LOG),
        "message_de": (
            "SMTP nicht konfiguriert – Mails nur als dry_run protokolliert (keine Fake-Zustellung)."
            if not host
            else "SMTP konfiguriert – Versand möglich."
        ),
    }


def recent_mail_log(limit: int = 50) -> list[dict[str, Any]]:
    return [
        {
            "id": m.id,
            "template": m.template,
            "to_email": m.to_email,
            "subject": m.subject,
            "status": m.status,
            "detail": m.detail,
            "created_at": m.created_at,
            "body_hash": hashlib.sha256(m.body_text.encode()).hexdigest()[:16],
        }
        for m in list(reversed(_MAIL_LOG))[:limit]
    ]


def send_template_email(
    *,
    template: str,
    to_email: str,
    extra_body: str | None = None,
    force_dry_run: bool = False,
) -> dict[str, Any]:
    if template not in TEMPLATES:
        return {"ok": False, "status": "unknown_template", "message_de": f"Unbekanntes Template: {template}"}

    subject, body = TEMPLATES[template]
    if extra_body:
        body = f"{body}\n\n{extra_body}"

    s = get_settings()
    host = (s.smtp_host or "").strip()
    dry = force_dry_run or not host or not s.smtp_from_email
    mail_id = str(uuid.uuid4())
    created = datetime.now(timezone.utc).isoformat()

    if dry:
        entry = OutboundMail(
            id=mail_id,
            template=template,
            to_email=to_email,
            subject=subject,
            body_text=body,
            status="dry_run",
            detail="Kein SMTP oder dry_run – nicht zugestellt.",
            created_at=created,
        )
        _MAIL_LOG.append(entry)
        return {
            "ok": True,
            "status": "dry_run",
            "id": mail_id,
            "message_de": "E-Mail nur protokolliert (dry_run). Keine Zustellung behauptet.",
        }

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = s.smtp_from_email
    msg["To"] = to_email
    msg.set_content(body)

    try:
        port = int(s.smtp_port or 587)
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            if s.smtp_use_tls:
                smtp.starttls()
            user = (s.smtp_user or "").strip()
            if user:
                smtp.login(user, s.smtp_password or "")
            smtp.send_message(msg)
        entry = OutboundMail(
            id=mail_id,
            template=template,
            to_email=to_email,
            subject=subject,
            body_text=body,
            status="sent",
            detail="SMTP send_message OK",
            created_at=created,
        )
        _MAIL_LOG.append(entry)
        return {"ok": True, "status": "sent", "id": mail_id, "message_de": "E-Mail über SMTP gesendet."}
    except Exception as exc:  # noqa: BLE001 – Operator braucht Fehlertext
        entry = OutboundMail(
            id=mail_id,
            template=template,
            to_email=to_email,
            subject=subject,
            body_text=body,
            status="failed",
            detail=str(exc)[:500],
            created_at=created,
        )
        _MAIL_LOG.append(entry)
        return {
            "ok": False,
            "status": "failed",
            "id": mail_id,
            "message_de": "SMTP-Versand fehlgeschlagen.",
            "detail": str(exc)[:300],
        }


def export_mail_audit_json() -> str:
    return json.dumps(recent_mail_log(200), ensure_ascii=False, indent=2)
