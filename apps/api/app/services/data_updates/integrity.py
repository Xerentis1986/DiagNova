"""Integrität und optionale Signaturprüfung (HMAC-SHA256)."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_hmac_sha256(*, body: bytes, signature_hex: str, secret: str) -> bool:
    if not signature_hex or not secret:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected.lower(), signature_hex.strip().lower())


def extract_signature_header(headers: dict[str, str]) -> str | None:
    """Unterstützte Header: X-DiagNova-Signature, X-Content-Signature."""
    lowered = {k.lower(): v for k, v in headers.items()}
    return lowered.get("x-diagnova-signature") or lowered.get("x-content-signature")


def package_risk_flags(payload: dict[str, Any]) -> dict[str, bool]:
    """Erkennt risikoerhöhende Inhalte im Import-Paket."""
    has_procedures = bool(payload.get("service_procedures"))
    has_ecus = bool(payload.get("ecus"))
    has_addresses = False
    for ecu in payload.get("ecus") or []:
        if isinstance(ecu, dict) and (ecu.get("request_address") or ecu.get("response_address")):
            has_addresses = True
            break
    dtc_with_text = False
    for dtc in payload.get("dtcs") or []:
        if isinstance(dtc, dict) and dtc.get("description_de") and dtc.get("description_status") == "known":
            dtc_with_text = True
            break
    return {
        "has_procedures": has_procedures,
        "has_ecu_addresses": has_addresses or has_ecus,
        "has_dtc_descriptive_text": dtc_with_text,
        "has_manufacturers": bool(payload.get("manufacturers")),
        "has_pids": bool(payload.get("pids")),
    }
