"""TOTP MFA für Plattform-Admins (RFC 6238, stdlib)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import time
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import User
from app.services.audit import write_audit


def _b32_secret(nbytes: int = 20) -> str:
    return base64.b32encode(os.urandom(nbytes)).decode("ascii").rstrip("=")


def _normalize_secret(secret: str) -> bytes:
    pad = "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode(secret.upper() + pad, casefold=True)


def totp_at(secret: str, for_time: int | None = None, step: int = 30, digits: int = 6) -> str:
    counter = int((for_time if for_time is not None else time.time()) // step)
    key = _normalize_secret(secret)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code_int % (10**digits)).zfill(digits)


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    if not code or not code.isdigit():
        return False
    now = int(time.time())
    for w in range(-window, window + 1):
        if hmac.compare_digest(totp_at(secret, now + w * 30), code.strip()):
            return True
    return False


def provisioning_uri(secret: str, email: str) -> str:
    issuer = get_settings().mfa_issuer
    label = f"{issuer}:{email}"
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
    )


def ensure_mfa_columns_loaded(user: User) -> None:
    # Attribute existieren nach Migration 015
    _ = getattr(user, "mfa_enabled", False)
    _ = getattr(user, "mfa_secret", None)


def start_mfa_setup(db: Session, user: User) -> dict[str, Any]:
    if not user.is_platform_admin:
        raise HTTPException(status_code=403, detail="MFA nur für Plattform-Admins")
    secret = _b32_secret()
    user.mfa_secret = secret  # type: ignore[attr-defined]
    user.mfa_enabled = False  # type: ignore[attr-defined]
    db.commit()
    return {
        "ok": True,
        "secret": secret,
        "otpauth_uri": provisioning_uri(secret, user.email),
        "message_de": "Secret erzeugt. Nach TOTP-Bestätigung wird MFA aktiv.",
    }


def confirm_mfa(db: Session, user: User, code: str) -> dict[str, Any]:
    secret = getattr(user, "mfa_secret", None)
    if not secret:
        raise HTTPException(status_code=400, detail="Kein MFA-Setup gestartet")
    if not verify_totp(secret, code):
        raise HTTPException(status_code=400, detail="Ungültiger TOTP-Code")
    user.mfa_enabled = True  # type: ignore[attr-defined]
    db.commit()
    write_audit(
        db,
        user_id=user.id,
        action="mfa_enabled",
        resource="user",
        detail=user.id,
        workshop_id=user.workshop_id,
    )
    return {"ok": True, "mfa_enabled": True, "message_de": "MFA aktiviert."}


def require_mfa_if_enabled(user: User, code: str | None) -> None:
    if not getattr(user, "mfa_enabled", False):
        return
    secret = getattr(user, "mfa_secret", None)
    if not secret or not code or not verify_totp(secret, code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA-Code erforderlich oder ungültig",
        )


def mfa_status(user: User) -> dict[str, Any]:
    return {
        "is_platform_admin": bool(user.is_platform_admin),
        "mfa_enabled": bool(getattr(user, "mfa_enabled", False)),
        "mfa_required_for_platform_admin": True,
        "has_secret": bool(getattr(user, "mfa_secret", None)),
        "message_de": (
            "Plattform-Admins müssen MFA aktivieren (Phase 22)."
            if user.is_platform_admin and not getattr(user, "mfa_enabled", False)
            else "MFA-Status OK."
        ),
    }
