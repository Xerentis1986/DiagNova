"""Phase 24 – Asymmetrische Offline-Lizenzsignatur (RSA-SHA256).

Backend signiert mit Private Key; Connector verifiziert nur Public Key.
HMAC bleibt Legacy-Fallback. Demo-Keys sind NICHT für Produktion.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

from app.core.config import get_settings

_REPO_ROOT = Path(__file__).resolve().parents[4]
_REPO_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "license_rsa_private.demo.pem"
_DATA_PUB = Path(__file__).resolve().parents[1] / "data" / "license_rsa_public.demo.pem"


def _load_private_key() -> RSAPrivateKey | None:
    pem = (get_settings().license_rsa_private_pem or "").strip()
    if not pem:
        env = (os.environ.get("DIAGNOVA_LICENSE_RSA_PRIVATE_PEM") or "").strip()
        if env:
            pem = env if "BEGIN" in env else base64.b64decode(env).decode()
    if not pem:
        if _REPO_FIXTURE.is_file() and os.environ.get("DIAGNOVA_LICENSE_ALLOW_DEMO_PRIVATE", "1") == "1":
            pem = _REPO_FIXTURE.read_text(encoding="utf-8")
    if not pem:
        return None
    key = serialization.load_pem_private_key(pem.encode() if isinstance(pem, str) else pem, password=None)
    if not isinstance(key, RSAPrivateKey):
        raise TypeError("License key must be RSA private key")
    return key


def public_key_pem() -> str:
    s = get_settings()
    if (s.license_rsa_public_pem or "").strip():
        return s.license_rsa_public_pem.strip()
    if _DATA_PUB.is_file():
        return _DATA_PUB.read_text(encoding="utf-8").strip() + "\n"
    return ""


def sign_payload(payload: str) -> dict:
    """Signiert UTF-8 Payload; gibt algorithm + signature_b64 zurück."""
    key = _load_private_key()
    if key is None:
        return {
            "ok": False,
            "algorithm": None,
            "message_de": "Kein RSA-Private-Key konfiguriert (DIAGNOVA_LICENSE_RSA_PRIVATE_PEM).",
        }
    sig = key.sign(
        payload.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return {
        "ok": True,
        "algorithm": "RSA-SHA256-PKCS1v15",
        "signature_b64": base64.b64encode(sig).decode("ascii"),
        "public_key_pem": public_key_pem(),
    }


def verify_payload(payload: str, signature_b64: str) -> bool:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

    pem = public_key_pem()
    if not pem:
        return False
    pub = serialization.load_pem_public_key(pem.encode())
    if not isinstance(pub, RSAPublicKey):
        return False
    try:
        pub.verify(
            base64.b64decode(signature_b64),
            payload.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except Exception:  # noqa: BLE001
        return False
