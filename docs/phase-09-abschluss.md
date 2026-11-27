# Phase 09 – Abschlussbericht: Fahrzeug-History und digitale Fahrzeugakte

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-09-history-f3fe`  
**Basis:** `origin/cursor/diagnova-phase-08-workshop-d09b` (PR #13)  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 10.

## Auftrag (Master-Prompt 09)

Fahrzeugakte mit chronologischem Zeitstrahl: Diagnosesitzungen, Datum, Kilometerstand, Benutzer, Adapter, Protokoll, ECU, DTC-Status, Messwerte, Freeze-Frame, Service, Reparaturen und Notizen. Automatisch nach Abschluss speichern; abgebrochene Sitzungen markieren; Wiederholungen idempotent. Vorher/Nachher-Vergleich pro ECU und DTC (neu / weiterhin vorhanden / nicht erneut beobachtet – letzteres nicht als behoben ohne ECU-Prüfung). Messwertverlauf begrenzt. Berichte und Aufträge verknüpfen. Abnahme: Lookup VIN/Kennzeichen, unvollständige Scans, Demo-Trennung, Mandantenschutz, Persistenz.

## Umsetzung

### Datenmodell

- Alembic `006_phase09` + ORM `app/models/vehicle_history.py`
- Erweiterung `diagnostic_sessions`: `workshop_id`, `work_order_id`, `odometer_km`, `adapter_name`, `protocol_name`, `abort_reason`, `idempotency_key`, `freeze_frame_json`, `readiness_json`, `auto_saved_at`, Status `aborted`
- Tabellen: `session_ecu_results`, `session_dtc_results`, `session_measurement_samples`, `vehicle_record_notes`

### Services / Regeln

- `app/services/vehicle_history.py`: Snapshot, Close/Abort mit ECU-Erhalt, Vergleich, Timeline, Lookup, Messwert-Pruning (500/Sitzung, 5000/Fahrzeug)
- Vergleich: `may_interpret_as_resolved=false`, wenn ECU in der späteren Sitzung nicht geprüft
- Authentizität am Zeitstrahl: `recorded` | `example_seed` | `simulated` – keine erfundenen Historien als echt

### API / UI

| Bereich | Endpunkte / UI |
|---------|----------------|
| Akte | `GET /api/vehicle-records/{id}`, `/timeline`, `/lookup?vin|license_plate` |
| Notizen | `POST /api/vehicle-records/{id}/notes` |
| Messwerte | `GET /api/vehicle-records/{id}/measurements` |
| Sitzung | `POST /sessions/v2`, `GET /sessions/{id}`, `/close`, `/abort`, `/snapshot`, `/compare` |
| UI | `/vehicle-record`, Link „Akte“ in Fahrzeugliste |

### Docs

- Requirements REQ-09-*, Capabilities, Phase-Status, Progress aktualisiert

### Bewusst nicht

- Keine echten Fahrzeug-Historien / keine Live-Hardware-Daten
- Keine erfundenen Historien als echt gekennzeichnet
- **Phase 10 nicht gestartet**
- Kein Prod-Deploy

## Tests (ausgeführt)

| Suite | Befehl | Ergebnis |
|-------|--------|----------|
| API + Protocols + Phase 06–09 | `PYTHONPATH=apps/api:packages/diagnostic-protocols/src python3 -m pytest tests -q` | **78 passed** |
| Connector xUnit | `dotnet test` | nicht ausgeführt (kein `dotnet`; Connector unverändert) |

Abnahme in `tests/api/test_phase09_vehicle_history.py`: Persistenz/Lookup/Timeline, Abort, Incomplete-Scan-Vergleich, Cross-Tenant 404.

## Start

```bash
export PYTHONPATH="apps/api:packages/diagnostic-protocols/src"
# GET  /api/vehicle-records/lookup?vin=…
# GET  /api/vehicle-records/{id}
# POST /api/sessions/v2  {"vehicle_id":"…","idempotency_key":"…"}
# POST /api/sessions/{id}/close | /abort
# GET  /api/sessions/compare?before=…&after=…
```

UI: `/vehicle-record`. Migration: `alembic upgrade head` (Revision `006_phase09`).

## Offene Punkte / Blocker

| ID | Thema |
|----|-------|
| BLK-HW | Keine echte Fahrzeug-Historie ohne Hardware |
| BLK-LEGAL | Aufbewahrung Historie rechtlich freigeben |
| Phase 10 | PDF-Berichte & Archiv – nächster orchestrated Schritt |
