"""Audit-Schreibhilfe mit Redaction (keine Passwörter / unnötige PII)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog

# Muster für sensible Felder in Freitext-Details
_PASSWORD_RE = re.compile(
    r"(?i)(password|passwd|passwort|secret|token|authorization|bearer)\s*[=:]\s*\S+"
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_VIN_RE = re.compile(r"\b([A-HJ-NPR-Z0-9]{17})\b")
_PHONE_RE = re.compile(r"\+?\d[\d\s\-()/]{7,}\d")


def redact_audit_detail(detail: str | None, *, keep_structure: bool = True) -> str | None:
    """Entfernt/maskiert Passwörter, Tokens; kürzt VIN/E-Mail/Telefon.

    Bewusst keine vollständige Anonymisierung – Audit braucht Nachvollziehbarkeit.
    Keine Passwörter oder Bearer-Tokens speichern.
    """
    if detail is None:
        return None
    text = str(detail)
    text = _PASSWORD_RE.sub(r"\1=[REDACTED]", text)
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*", "Bearer [REDACTED]", text)

    def _mask_vin(m: re.Match[str]) -> str:
        vin = m.group(1)
        return f"{vin[:3]}…{vin[-4:]}" if keep_structure else "[VIN]"

    def _mask_email(m: re.Match[str]) -> str:
        raw = m.group(0)
        local, _, domain = raw.partition("@")
        if not domain:
            return "[EMAIL]"
        return f"{local[:1]}…@{domain}"

    def _mask_phone(m: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) < 6:
            return m.group(0)
        return f"…{digits[-4:]}"

    text = _VIN_RE.sub(_mask_vin, text)
    text = _EMAIL_RE.sub(_mask_email, text)
    text = _PHONE_RE.sub(_mask_phone, text)
    # Harte Längenbegrenzung gegen Log-Flooding
    if len(text) > 2000:
        text = text[:2000] + "…[truncated]"
    return text


def hash_ip_hint(ip: str | None) -> str | None:
    """Einweg-Hash der Client-IP für Rate-Limit-/Audit-Korrelation (kein Klartext)."""
    if not ip:
        return None
    digest = hashlib.sha256(ip.strip().encode("utf-8")).hexdigest()
    return digest[:16]


def write_audit(
    db: Session,
    *,
    user_id: str | None,
    action: str,
    resource: str,
    detail: str | None = None,
    workshop_id: str | None = None,
    outcome: str | None = None,
    ip_hint: str | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            workshop_id=workshop_id,
            action=action,
            resource=resource,
            detail=redact_audit_detail(detail),
            outcome=outcome,
            ip_hash=ip_hint,
        )
    )
    db.commit()


def audit_dict_safe(payload: dict[str, Any]) -> dict[str, Any]:
    """Kopiert ein Dict und redaktiert bekannte Sensitiv-Keys."""
    blocked = {
        "password",
        "passwd",
        "passwort",
        "hashed_password",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "hmac",
        "signature",
    }
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if k.lower() in blocked:
            out[k] = "[REDACTED]"
        elif isinstance(v, dict):
            out[k] = audit_dict_safe(v)
        elif isinstance(v, str) and k.lower() in {"vin", "license_plate", "email", "phone"}:
            out[k] = redact_audit_detail(v) or "[REDACTED]"
        else:
            out[k] = v
    return out
