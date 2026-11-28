"""Phase 22/23 – Web ↔ Windows-Connector Live-Bridge.

LIVE: nur Connector-Antworten (kein API-Simulator-Fallback).
DEMO: explizit simulator.py.
adapter_fake: bewusster Connector-Test-Double (E2E), kein silent Fallback.
SSRF: Connector-URL nur Loopback/Allowlist.
"""

from __future__ import annotations

import ipaddress
import os
from datetime import datetime, timezone
from typing import Any, Literal
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.schemas.api import ConnectionStatusOut, DtcOut, LiveDataOut, PidReadingOut
from app.services import simulator

DiagMode = Literal["demo", "live"]

# LIVE akzeptiert diese data_source-Werte vom Connector (nicht API-Simulator)
_LIVE_OK_SOURCES = frozenset({"live", "adapter_fake", "live_unverified", "live_test_double"})


def resolve_mode(requested: str | None = None) -> DiagMode:
    raw = (requested or os.environ.get("DIAGNOVA_DIAG_MODE") or get_settings().diag_default_mode or "demo").lower()
    return "live" if raw == "live" else "demo"


def _host_allowed(hostname: str, allowlist: list[str]) -> bool:
    host = (hostname or "").strip().lower().rstrip(".")
    if not host:
        return False
    for entry in allowlist:
        e = entry.strip().lower()
        if not e:
            continue
        if host == e:
            return True
    # Loopback IPs
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_loopback:
            return True
    except ValueError:
        pass
    return host in {"localhost", "127.0.0.1", "::1"}


def validate_connector_base_url(url: str | None = None) -> str:
    """SSRF-Schutz: nur http(s) zu Allowlist/Loopback, keine Userinfo, keine freien Hosts."""
    s = get_settings()
    raw = (url or s.connector_base_url or "http://127.0.0.1:8765").strip()
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        raise ConnectorBridgeError("Connector-URL: nur http/https erlaubt (SSRF-Schutz).", status_code=400)
    if parsed.username or parsed.password:
        raise ConnectorBridgeError("Connector-URL darf keine Credentials enthalten.", status_code=400)
    if not parsed.hostname:
        raise ConnectorBridgeError("Connector-URL ohne Host.", status_code=400)
    allow = [x.strip() for x in (s.connector_url_allowlist or "127.0.0.1,localhost,::1").split(",") if x.strip()]
    if not _host_allowed(parsed.hostname, allow):
        raise ConnectorBridgeError(
            f"Connector-Host '{parsed.hostname}' nicht in Allowlist (SSRF-Schutz).",
            status_code=400,
        )
    # Block cloud metadata-ish paths via host already; reject odd ports only if 0
    if parsed.port == 0:
        raise ConnectorBridgeError("Ungültiger Connector-Port.", status_code=400)
    return raw.rstrip("/")


def connector_base_url() -> str:
    return validate_connector_base_url()


def _headers() -> dict[str, str]:
    token = (get_settings().connector_bearer_token or "").strip()
    h = {"Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def _get_json(path: str, timeout: float = 5.0) -> dict[str, Any]:
    base = connector_base_url()
    url = f"{base}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=_headers())
    except ConnectorBridgeError:
        raise
    except httpx.HTTPError as exc:
        raise ConnectorBridgeError(
            f"Connector nicht erreichbar ({url}): {exc}",
            status_code=503,
        ) from exc
    if resp.status_code >= 400:
        raise ConnectorBridgeError(
            f"Connector {path} HTTP {resp.status_code}: {resp.text[:300]}",
            status_code=resp.status_code,
        )
    data = resp.json()
    if not isinstance(data, dict):
        raise ConnectorBridgeError("Connector lieferte kein JSON-Objekt")
    return data


async def _post_json(path: str, body: dict | None = None, timeout: float = 8.0) -> dict[str, Any]:
    base = connector_base_url()
    url = f"{base}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=_headers(), json=body or {})
    except ConnectorBridgeError:
        raise
    except httpx.HTTPError as exc:
        raise ConnectorBridgeError(
            f"Connector nicht erreichbar ({url}): {exc}",
            status_code=503,
        ) from exc
    if resp.status_code >= 400:
        raise ConnectorBridgeError(
            f"Connector {path} HTTP {resp.status_code}: {resp.text[:300]}",
            status_code=resp.status_code,
        )
    data = resp.json()
    if not isinstance(data, dict):
        raise ConnectorBridgeError("Connector lieferte kein JSON-Objekt")
    return data


class ConnectorBridgeError(Exception):
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.status_code = status_code


def _assert_live_source(raw: dict[str, Any], what: str) -> str:
    ds = str(raw.get("data_source") or "live")
    if ds == "simulated":
        raise ConnectorBridgeError(
            f"LIVE-Modus verweigert simulierte Connector-Antwort ({what}, data_source=simulated).",
            status_code=409,
        )
    if ds not in _LIVE_OK_SOURCES:
        raise ConnectorBridgeError(
            f"LIVE-Modus: unbekannte data_source={ds!r} für {what}.",
            status_code=409,
        )
    # API-facing: adapter_fake bleibt als solches markiert (ehrlich)
    return "live" if ds == "live" else ds


async def probe_connector() -> dict[str, Any]:
    try:
        base = connector_base_url()
    except ConnectorBridgeError as exc:
        return {"reachable": False, "base_url": None, "error_de": str(exc)[:400], "ssrf_blocked": True}
    try:
        health = await _get_json("/health", timeout=2.5)
        version = await _get_json("/version", timeout=2.5)
        return {
            "reachable": True,
            "health": health,
            "version": version,
            "base_url": base,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "reachable": False,
            "base_url": base,
            "error_de": str(exc)[:400],
        }


async def hardware_probe() -> dict[str, Any]:
    """Proxy zu Connector /hardware/probe – keine Fahrzeugbefehle, kein Flash."""
    probe = await probe_connector()
    if not probe.get("reachable"):
        return {
            "ok": False,
            "connector": probe,
            "message_de": (
                "Windows-Connector nicht erreichbar – Hardware-Probe nicht möglich. "
                "Kein Fake-Erfolg."
            ),
        }
    try:
        data = await _get_json("/hardware/probe", timeout=8.0)
        return {
            "ok": True,
            "connector": {"reachable": True, "base_url": probe.get("base_url")},
            "probe": data,
            "message_de": "Hardware-Probe vom Connector (nichtinvasiv).",
        }
    except ConnectorBridgeError as exc:
        return {
            "ok": False,
            "connector": probe,
            "message_de": str(exc)[:400],
        }


async def connection_status(mode: DiagMode) -> ConnectionStatusOut:
    if mode == "demo":
        return simulator.connection_status()

    probe = await probe_connector()
    if not probe.get("reachable"):
        return ConnectionStatusOut(
            connected=False,
            mode="none",
            adapter_name="—",
            data_source="live",
            message_de=(
                "LIVE-Modus: Windows-Connector nicht erreichbar "
                f"({probe.get('base_url') or 'ssrf-blocked'}). Kein Simulator-Fallback."
            ),
            last_heartbeat=None,
        )

    try:
        status = await _get_json("/status", timeout=3.0)
    except ConnectorBridgeError:
        status = {}

    adapter = (
        status.get("adapter_name")
        or status.get("selected_adapter")
        or (probe.get("health") or {}).get("adapter")
        or "Windows-Connector"
    )
    vehicle_ok = bool(status.get("vehicle_connected") or status.get("vehicle_linked"))
    ds_raw = str(status.get("data_source") or "live")
    return ConnectionStatusOut(
        connected=True,
        mode="connector",
        adapter_name=str(adapter),
        data_source="live",
        message_de=(
            "LIVE: Connector erreichbar."
            + (" Fahrzeug verknüpft." if vehicle_ok else " Noch kein Fahrzeug (OBD-Init nötig).")
            + (" [adapter_fake E2E-Double]" if ds_raw == "adapter_fake" else "")
        ),
        last_heartbeat=datetime.now(timezone.utc),
    )


def _map_readings(raw: dict[str, Any]) -> list[PidReadingOut]:
    readings_in = raw.get("readings") or raw.get("pids") or []
    out: list[PidReadingOut] = []
    now = datetime.now(timezone.utc)
    if isinstance(readings_in, list):
        for i, r in enumerate(readings_in):
            if not isinstance(r, dict):
                continue
            name = str(r.get("name") or r.get("pid_name") or r.get("id") or f"pid_{i}")
            val = r.get("value")
            try:
                fval = float(val) if val is not None else 0.0
            except (TypeError, ValueError):
                fval = 0.0
            pid = int(r.get("pid") or r.get("pid_id") or i)
            pid_hex = str(r.get("pid_hex") or f"{pid:02X}")
            out.append(
                PidReadingOut(
                    pid=pid,
                    pid_hex=pid_hex,
                    name=name,
                    description_de=str(r.get("description_de") or r.get("description") or name),
                    value=fval,
                    unit=str(r.get("unit") or ""),
                    timestamp=now,
                )
            )
    return out


def _map_dtcs(raw: dict[str, Any]) -> list[DtcOut]:
    items: list[Any] = []
    for key in ("dtcs", "codes", "stored", "pending", "permanent"):
        chunk = raw.get(key)
        if isinstance(chunk, list):
            items.extend(chunk)
    out: list[DtcOut] = []
    seen: set[str] = set()
    for d in items:
        if isinstance(d, str):
            code, desc, sev, st = d, d, "info", "stored"
        elif isinstance(d, dict):
            code = str(d.get("code") or d.get("dtc") or "")
            desc = str(d.get("description_de") or d.get("description") or code)
            sev_raw = str(d.get("severity") or "info")
            sev = sev_raw if sev_raw in {"info", "warning", "critical"} else "info"
            st_raw = str(d.get("status") or "stored")
            st = st_raw if st_raw in {"stored", "pending", "permanent"} else "stored"
        else:
            continue
        if not code or code in seen:
            continue
        seen.add(code)
        out.append(DtcOut(code=code, description_de=desc or code, severity=sev, status=st))  # type: ignore[arg-type]
    return out


async def live_data(mode: DiagMode, vehicle_id: str, vin_hint: str) -> LiveDataOut:
    if mode == "demo":
        return simulator.live_data(vehicle_id, vin_hint)

    raw = await _get_json("/obd/live", timeout=6.0)
    ds = _assert_live_source(raw, "live")
    # API schema: data_source typically live|simulated – map adapter_fake → live with honesty in readings empty ok
    api_source = "live" if ds in _LIVE_OK_SOURCES else "live"

    vin = str(raw.get("vin") or vin_hint or "")
    readiness = raw.get("readiness") if isinstance(raw.get("readiness"), dict) else {}
    ff = raw.get("freeze_frame") if isinstance(raw.get("freeze_frame"), dict) else None
    return LiveDataOut(
        data_source=api_source,  # type: ignore[arg-type]
        vehicle_id=vehicle_id,
        vin=vin,
        readings=_map_readings(raw),
        readiness={str(k): bool(v) for k, v in readiness.items()},
        freeze_frame=ff,  # type: ignore[arg-type]
    )


async def list_dtcs(mode: DiagMode, vehicle_id: str) -> list[DtcOut]:
    if mode == "demo":
        return simulator.list_dtcs(vehicle_id)
    raw = await _get_json("/obd/dtcs", timeout=6.0)
    _assert_live_source(raw, "dtcs")
    return _map_dtcs(raw)


async def ensure_obd_init(mode: DiagMode) -> dict[str, Any]:
    if mode == "demo":
        return {"ok": True, "mode": "demo", "skipped": True}
    return await _post_json("/obd/init", {})


async def connect_fake_adapter() -> dict[str, Any]:
    """E2E: Fake-Adapter am Connector anwählen (nur Loopback)."""
    return await _post_json("/adapter/connect/fake", {})
