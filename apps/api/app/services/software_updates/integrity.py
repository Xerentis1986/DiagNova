"""Checksum (SHA-256) und HMAC-Signatur für Software-Pakete."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from app.core.config import get_settings


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_package_bytes(payload: dict[str, Any]) -> bytes:
    """Kanonische Serialisierung für Signatur/Checksum (sortierte Keys)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sign_package_bytes(body: bytes, *, secret: str | None = None) -> str:
    secret = secret or get_settings().software_update_hmac_demo_secret
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_hmac_sha256(*, body: bytes, signature_hex: str, secret: str) -> bool:
    if not signature_hex or not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.lower(), signature_hex.strip().lower())


def verify_package_integrity(
    payload: dict[str, Any],
    *,
    claimed_sha256: str,
    signature_hex: str | None,
    require_signature: bool,
) -> dict[str, Any]:
    """Prüft Checksum und optionale Signatur. Manipulierte Pakete → ok=False."""
    body = canonical_package_bytes(payload)
    actual = sha256_hex(body)
    checksum_ok = hmac.compare_digest(actual.lower(), (claimed_sha256 or "").strip().lower())
    settings = get_settings()
    signature_ok: bool | None = None
    errors: list[str] = []

    if not checksum_ok:
        errors.append("Checksum stimmt nicht – Paket abgelehnt (Manipulation oder Übertragungsfehler).")

    if require_signature:
        if not signature_hex:
            signature_ok = False
            errors.append("Signatur fehlt – Paket abgelehnt.")
        else:
            signature_ok = verify_hmac_sha256(
                body=body,
                signature_hex=signature_hex,
                secret=settings.software_update_hmac_demo_secret,
            )
            if not signature_ok:
                errors.append("Signatur ungültig – Paket abgelehnt.")
    elif signature_hex:
        signature_ok = verify_hmac_sha256(
            body=body,
            signature_hex=signature_hex,
            secret=settings.software_update_hmac_demo_secret,
        )

    return {
        "ok": checksum_ok and (signature_ok is not False if require_signature else checksum_ok),
        "checksum_ok": checksum_ok,
        "signature_ok": signature_ok,
        "actual_sha256": actual,
        "errors_de": errors,
        "body": body,
    }
