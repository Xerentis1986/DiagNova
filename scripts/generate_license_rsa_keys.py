#!/usr/bin/env python3
"""Erzeugt RSA-2048 Keypaar für Offline-Lizenzen (Phase 25).

Schreibt NUR lokal nach .secrets/license/ (gitignored).
Niemals Private Key committen oder in Chat posten.

Usage:
  python scripts/generate_license_rsa_keys.py
  export DIAGNOVA_LICENSE_RSA_PRIVATE_PEM="$(cat .secrets/license/private.pem)"
  # Connector: Public Key als DIAGNOVA_LICENSE_RSA_PUBLIC_PEM oder Datei Auth/LicenseRsaPublic.pem
"""

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".secrets" / "license"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    (OUT / "private.pem").write_bytes(priv)
    (OUT / "public.pem").write_bytes(pub)
    (OUT / "README.txt").write_text(
        "PRIVATE nur Backend (Env DIAGNOVA_LICENSE_RSA_PRIVATE_PEM).\n"
        "PUBLIC in Connector (DIAGNOVA_LICENSE_RSA_PUBLIC_PEM).\n"
        "DIAGNOVA_LICENSE_ALLOW_DEMO_PRIVATE=0 in Produktion.\n"
        "Diese Dateien nie committen.\n",
        encoding="utf-8",
    )
    print(f"OK: {OUT / 'private.pem'}")
    print(f"OK: {OUT / 'public.pem'}")
    print("Setze Env laut README.txt – keine Keys in Git.")


if __name__ == "__main__":
    main()
