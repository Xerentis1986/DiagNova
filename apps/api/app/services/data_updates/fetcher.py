"""Sicheres Abrufen von Update-Paketen (HTTPS Allowlist oder Fixture-Modus)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import httpx

from app.core.config import get_settings
from app.services.data_updates.ssrf import SsrfBlocked, validate_https_url

# Fixture-Root: apps/api/app/data/fixtures
_FIXTURES = Path(__file__).resolve().parents[2] / "data" / "fixtures"

FetchTransport = Callable[..., "FetchResult"]


@dataclass
class FetchResult:
    status_code: int
    body: bytes
    headers: dict[str, str]
    etag: str | None = None
    not_modified: bool = False
    error_de: str | None = None


class FetchError(RuntimeError):
    def __init__(self, message_de: str, *, status_code: int | None = None):
        super().__init__(message_de)
        self.message_de = message_de
        self.status_code = status_code


def _parse_fixture_ref(url: str) -> Path:
    """fixture://filename.json → lokaler Fixture-Pfad (nur Demo/Tests)."""
    name = url.removeprefix("fixture://").lstrip("/")
    if ".." in name or "/" in name or "\\" in name:
        raise FetchError("Ungültige Fixture-Referenz.")
    path = (_FIXTURES / name).resolve()
    if not str(path).startswith(str(_FIXTURES.resolve())):
        raise FetchError("Fixture-Pfad außerhalb des erlaubten Verzeichnisses.")
    if not path.is_file():
        raise FetchError(f"Fixture nicht gefunden: {name}")
    return path


def fetch_fixture(url: str, *, etag: str | None = None, max_bytes: int = 2_000_000) -> FetchResult:
    path = _parse_fixture_ref(url)
    body = path.read_bytes()
    if len(body) > max_bytes:
        raise FetchError(f"Fixture zu groß (>{max_bytes} Bytes).")
    # ETag = mtime-hash-ähnlich: Inhaltshaupt-Präfix
    import hashlib

    file_etag = '"' + hashlib.sha256(body).hexdigest()[:16] + '"'
    if etag and etag == file_etag:
        return FetchResult(status_code=304, body=b"", headers={}, etag=file_etag, not_modified=True)
    headers = {
        "etag": file_etag,
        "content-type": "application/json",
        "x-diagnova-version": _peek_version(body),
    }
    # Signatur optional aus sibling .sig Datei
    sig_path = path.with_suffix(path.suffix + ".sig")
    if sig_path.is_file():
        headers["x-diagnova-signature"] = sig_path.read_text(encoding="utf-8").strip()
    return FetchResult(status_code=200, body=body, headers=headers, etag=file_etag)


def _peek_version(body: bytes) -> str:
    try:
        data = json.loads(body.decode("utf-8"))
        if isinstance(data, dict):
            return str(data.get("dataset_version_label") or data.get("version") or "")
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return ""


def fetch_https(
    url: str,
    *,
    etag: str | None = None,
    max_bytes: int | None = None,
    timeout_sec: float | None = None,
    max_retries: int | None = None,
    backoff_sec: float | None = None,
    client: httpx.Client | None = None,
) -> FetchResult:
    settings = get_settings()
    max_bytes = max_bytes if max_bytes is not None else settings.update_max_bytes
    timeout_sec = timeout_sec if timeout_sec is not None else float(settings.update_fetch_timeout_sec)
    max_retries = max_retries if max_retries is not None else settings.update_max_retries
    backoff_sec = backoff_sec if backoff_sec is not None else settings.update_retry_backoff_sec

    safe_url = validate_https_url(url)
    headers: dict[str, str] = {"Accept": "application/json"}
    if etag:
        headers["If-None-Match"] = etag

    last_error: str | None = None
    own_client = client is None
    http = client or httpx.Client(timeout=timeout_sec, follow_redirects=False)
    try:
        for attempt in range(max_retries + 1):
            try:
                resp = http.get(safe_url, headers=headers)
            except httpx.TimeoutException as exc:
                last_error = "Netz-Timeout beim Abruf."
                if attempt >= max_retries:
                    raise FetchError(last_error) from exc
                time.sleep(backoff_sec * (2**attempt))
                continue
            except httpx.HTTPError as exc:
                last_error = f"Netzfehler: {type(exc).__name__}"
                if attempt >= max_retries:
                    raise FetchError(last_error) from exc
                time.sleep(backoff_sec * (2**attempt))
                continue

            if resp.status_code == 304:
                return FetchResult(
                    status_code=304,
                    body=b"",
                    headers=dict(resp.headers),
                    etag=resp.headers.get("etag") or etag,
                    not_modified=True,
                )

            if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                time.sleep(backoff_sec * (2**attempt))
                continue

            if resp.status_code != 200:
                raise FetchError(
                    f"HTTP {resp.status_code} von Update-Quelle.",
                    status_code=resp.status_code,
                )

            # Streaming-ähnliche Größenprüfung
            content = resp.content
            if len(content) > max_bytes:
                raise FetchError(f"Antwort zu groß (>{max_bytes} Bytes).")

            # Keine Archive in Phase 07 – nur JSON
            ctype = (resp.headers.get("content-type") or "").lower()
            if "zip" in ctype or "tar" in ctype or "gzip" in ctype:
                raise FetchError("Unsichere Archive werden nicht akzeptiert.")

            return FetchResult(
                status_code=200,
                body=content,
                headers={k.lower(): v for k, v in resp.headers.items()},
                etag=resp.headers.get("etag"),
            )

        raise FetchError(last_error or "Abruf nach Retries fehlgeschlagen.")
    finally:
        if own_client:
            http.close()


def fetch_channel_payload(
    *,
    fetch_mode: str,
    url: str,
    etag: str | None,
    max_bytes: int,
    client: httpx.Client | None = None,
) -> FetchResult:
    if fetch_mode == "fixture":
        return fetch_fixture(url, etag=etag, max_bytes=max_bytes)
    if fetch_mode == "https":
        return fetch_https(url, etag=etag, max_bytes=max_bytes, client=client)
    raise FetchError(f"Unbekannter fetch_mode: {fetch_mode}")


def parse_json_body(body: bytes) -> dict[str, Any]:
    try:
        data = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise FetchError("Antwort ist kein gültiges JSON.") from exc
    if not isinstance(data, dict):
        raise FetchError("JSON-Wurzel muss ein Objekt sein.")
    return data
