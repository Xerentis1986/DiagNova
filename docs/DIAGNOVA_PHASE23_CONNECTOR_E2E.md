# Phase 23 – Connector Live-Bridge E2E

## Kette
API (`connector_bridge`) → Loopback Connector (echter `dotnet run` Prozess) → `POST /adapter/connect/fake` → `/obd/init` + `/obd/live`

## Auth
`CONNECTOR_TOKEN` / `connector_bearer_token` (kein offenes Loopback ohne Token)

## SSRF
Nur Hosts in `connector_url_allowlist` (Default: 127.0.0.1, localhost, ::1). Externe Hosts → unreachable/400.

## data_source
- Fake-Adapter: `adapter_fake` (Connector)
- API LIVE Schema: mapped auf `live` (kein `simulated` Fallback)
- API-Simulator nur bei `mode=demo`

## Test
```
pytest tests/api/test_phase23_connector_e2e.py -q
```
**2 passed** (2026-11-28)

## HW
Physische Adapter: weiterhin NOT TESTED / BLOCKED (BLK-HW-01).
