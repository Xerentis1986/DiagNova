"""Sichere Mollie-Konfiguration (Secret-Store + Env).

Priorität: nicht-leere Env-Variablen schlagen den lokalen Secret-Store.
UI speichert in verschlüsselte Datei unter DIAGNOVA_SECRETS_DIR (Default: .secrets/).
Niemals Klartext-Keys in Logs oder API-Antworten.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

_log = logging.getLogger("diagnova.mollie_secrets")

_STORE_NAME = "mollie.enc"
_META_NAME = "mollie.meta.json"


def secrets_dir() -> Path:
    raw = (os.environ.get("DIAGNOVA_SECRETS_DIR") or "").strip()
    if raw:
        return Path(raw)
    # Repo-Root .secrets/ (gitignored): …/payments → services → app → api → apps → repo
    return Path(__file__).resolve().parents[5] / ".secrets"


def _fernet() -> Fernet:
    explicit = (os.environ.get("DIAGNOVA_SECRETS_FERNET_KEY") or "").strip()
    if explicit:
        try:
            # akzeptiert fertigen Fernet-Key oder beliebigen Passphrase-String
            if len(explicit) == 44:
                return Fernet(explicit.encode("ascii"))
            digest = hashlib.sha256(explicit.encode("utf-8")).digest()
            return Fernet(base64.urlsafe_b64encode(digest))
        except Exception:  # noqa: BLE001
            digest = hashlib.sha256(explicit.encode("utf-8")).digest()
            return Fernet(base64.urlsafe_b64encode(digest))
    material = f"diagnova-mollie-secrets-v1:{get_settings().jwt_secret}".encode("utf-8")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(material).digest()))


def _store_path() -> Path:
    return secrets_dir() / _STORE_NAME


def _meta_path() -> Path:
    return secrets_dir() / _META_NAME


def mask_secret(value: str | None, *, keep: int = 4) -> str | None:
    if not value:
        return None
    v = value.strip()
    if len(v) <= keep + 4:
        return "***"
    return f"{v[:keep]}…{v[-keep:]}"


def _read_store() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {}
    try:
        token = path.read_bytes()
        raw = _fernet().decrypt(token)
        data = json.loads(raw.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except (InvalidToken, OSError, json.JSONDecodeError, ValueError):
        _log.warning("mollie_secret_store_unreadable path=%s", path.name)
        return {}


def _write_store(data: dict[str, Any]) -> None:
    d = secrets_dir()
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    blob = _fernet().encrypt(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    path = _store_path()
    path.write_bytes(blob)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    meta = {
        "configured": bool((data.get("api_key") or "").strip()),
        "has_webhook_secret": bool((data.get("webhook_secret") or "").strip()),
        "webhook_url_set": bool((data.get("webhook_url") or "").strip()),
        "live_charges_allowed": bool(data.get("live_charges_allowed")),
        "key_prefix": mask_secret(data.get("api_key"), keep=5),
        "storage": "encrypted_file",
        "note_de": "Werte verschlüsselt; Klartext nie in Meta/Logs.",
    }
    meta_path = _meta_path()
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(meta_path, 0o600)
    except OSError:
        pass
    _log.info(
        "mollie_secret_store_updated configured=%s live=%s",
        meta["configured"],
        meta["live_charges_allowed"],
    )


def load_stored() -> dict[str, Any]:
    return _read_store()


def save_config(
    *,
    api_key: str | None = None,
    webhook_secret: str | None = None,
    webhook_url: str | None = None,
    live_charges_allowed: bool | None = None,
    clear_api_key: bool = False,
    clear_webhook_secret: bool = False,
) -> dict[str, Any]:
    """Merge in Secret-Store. Leere Strings = Feld unverändert (außer clear_*)."""
    current = _read_store()
    if clear_api_key:
        current.pop("api_key", None)
    elif api_key is not None and api_key.strip():
        current["api_key"] = api_key.strip()
    if clear_webhook_secret:
        current.pop("webhook_secret", None)
    elif webhook_secret is not None and webhook_secret.strip():
        current["webhook_secret"] = webhook_secret.strip()
    if webhook_url is not None:
        current["webhook_url"] = webhook_url.strip()
    if live_charges_allowed is not None:
        current["live_charges_allowed"] = bool(live_charges_allowed)
    _write_store(current)
    return public_config()


def resolve_api_key() -> tuple[str, str]:
    """Returns (key, source) where source is env|secret_store|none."""
    env = (get_settings().mollie_api_key or "").strip()
    if env:
        return env, "env"
    stored = (_read_store().get("api_key") or "").strip()
    if stored:
        return stored, "secret_store"
    return "", "none"


def resolve_webhook_secret() -> tuple[str, str]:
    env = (get_settings().mollie_webhook_secret or "").strip()
    if env:
        return env, "env"
    stored = (_read_store().get("webhook_secret") or "").strip()
    if stored:
        return stored, "secret_store"
    return "", "none"


def resolve_webhook_url() -> tuple[str, str]:
    env = (get_settings().mollie_webhook_url or "").strip()
    if env:
        return env, "env"
    stored = (_read_store().get("webhook_url") or "").strip()
    if stored:
        return stored, "secret_store"
    return "", "none"


def resolve_live_charges_allowed() -> bool:
    """Env true gewinnt; sonst Store; Default false."""
    s = get_settings()
    # Wenn Env-Key live und Flag gesetzt
    if s.mollie_live_charges_allowed:
        return True
    return bool(_read_store().get("live_charges_allowed"))


def public_config() -> dict[str, Any]:
    key, key_src = resolve_api_key()
    wh_sec, wh_src = resolve_webhook_secret()
    wh_url, url_src = resolve_webhook_url()
    live = resolve_live_charges_allowed()
    test_mode = key.startswith("test_") if key else True
    live_keys = key.startswith("live_") if key else False
    return {
        "provider": "mollie",
        "configured": bool(key),
        "api_key_masked": mask_secret(key, keep=5),
        "api_key_source": key_src,
        "webhook_secret_set": bool(wh_sec),
        "webhook_secret_source": wh_src,
        "webhook_url": wh_url or None,
        "webhook_url_source": url_src,
        "live_charges_allowed": live and live_keys,
        "live_charges_flag": live,
        "test_mode": test_mode and not live_keys,
        "live_keys_present": live_keys,
        "storage_path_hint": str(_store_path().name),
        "editable_via_admin": True,
        "env_overrides_store": True,
        "message_de": (
            "API-Key fehlt – im Admin-UI eintragen oder MOLLIE_API_KEY setzen."
            if not key
            else (
                f"Key gesetzt ({key_src}, {mask_secret(key, keep=5)}). "
                "Verbindungstest ohne Abbuchung möglich."
            )
        ),
        "security_de": (
            "Secret-Store verschlüsselt (Fernet). Keine Klartext-Keys in Logs/API. "
            "Env überschreibt Store wenn gesetzt."
        ),
    }
