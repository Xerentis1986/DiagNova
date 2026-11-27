"""Phase 22 – Web ↔ Windows-Connector Live-Bridge.

LIVE: nur echte Connector-Antworten (kein Simulator-Fallback).
DEMO: explizit simulator.py.
Ohne erreichbaren Connector im LIVE-Modus: Fehler, keine Fake-Daten.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Literal

import httpx

from app.core.config import get_settings
from app.schemas.api import ConnectionStatusOut, DtcOut, LiveDataOut, PidReadingOut
from app.services import simulator

DiagMode = Literal["demo", "live"]


def resolve_mode(requested: str | None = None) -> DiagMode:
    raw = (requested or os.environ.get("DIAGNOVA_DIAG_MODE") or get_settings().diag_default_mode or "demo").lower()
    return "live" if raw == "live" else "demo"


def connector_base_url() -> str:
    s = get_settings()
    return (s.connector_base_url or "http://127.0.0.1:8765").rstrip("/")


def _headers() -> dict[str, str]:
    token = (get_settings().connector_bearer_token or "").strip()
    h = {"Accept": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


async def _get_json(path: str, timeout: float = 5.0) -> dict[str, Any]:
    url = f"{connector_base_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url, headers=_headers())
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
    url = f"{connector_base_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=_headers(), json=body or {})
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


async def probe_connector() -> dict[str, Any]:
    try:
        health = await _get_json("/health", timeout=2.5)
        version = await _get_json("/version", timeout=2.5)
        return {
            "reachable": True,
            "health": health,
            "version": version,
            "base_url": connector_base_url(),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "reachable": False,
            "base_url": connector_base_url(),
            "error_de": str(exc)[:400],
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
                f"({connector_base_url()}). Kein Simulator-Fallback."
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
    return ConnectionStatusOut(
        connected=True,
        mode="connector",
        adapter_name=str(adapter),
        data_source="live",
        message_de=(
            "LIVE: Connector erreichbar."
            + (" Fahrzeug verknüpft." if vehicle_ok else " Noch kein Fahrzeug (OBD-Init nötig).")
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

    # LIVE: kein Fallback
    try:
        raw = await _get_json("/obd/live", timeout=6.0)
    except ConnectorBridgeError:
        raise

    ds = str(raw.get("data_source") or "live")
    if ds == "simulated":
        raise ConnectorBridgeError(
            "LIVE-Modus verweigert simulierte Connector-Antwort (data_source=simulated).",
            status_code=409,
        )

    vin = str(raw.get("vin") or vin_hint or "")
    readiness = raw.get("readiness") if isinstance(raw.get("readiness"), dict) else {}
    ff = raw.get("freeze_frame") if isinstance(raw.get("freeze_frame"), dict) else None
    return LiveDataOut(
        data_source="live",
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
    ds = str(raw.get("data_source") or "live")
    if ds == "simulated":
        raise ConnectorBridgeError(
            "LIVE-Modus verweigert simulierte DTC-Antwort.",
            status_code=409,
        )
    return _map_dtcs(raw)


async def ensure_obd_init(mode: DiagMode) -> dict[str, Any]:
    if mode == "demo":
        return {"ok": True, "mode": "demo", "skipped": True}
    return await _post_json("/obd/init", {})
