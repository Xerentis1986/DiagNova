# Phase 07 – Abschlussbericht: Automatische Diagnosedaten-Updates

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-07-updates-4111`  
**Basis:** `origin/cursor/diagnova-phase-06-database-80ce` (PR #11)  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 08.

## Auftrag (Master-Prompt 07)

Serverseitiger Scheduler (Standard täglich), freigegebene Quellenliste, ETag/Version/Hash, Timeout, Retry/Backoff, Parallel-Job-Sperre; nur HTTPS-Allowlist mit SSRF-/Größen-/Archivschutz; Lizenz-/Schema-/Signatur-/Integritätsprüfung in Staging; Auto-Aktivierung nur für risikoarme beschreibende DTC-Texte; Prozeduren/Adressen manuell; atomare Veröffentlichung, Backup/Rollback, Changelog, Admin-Dashboard. Abnahme: simulierte neu/gleich/defekt/Lizenzwechsel/Netzfehler/Rollback; keine echten Quellen ohne Rechte.

## Umsetzung

### Datenmodell

- Alembic `004_phase07` + ORM `app/models/data_updates.py`
- `update_channels`, `update_runs`, `update_changelogs`, `update_job_locks`

### Pipeline

- Fixture-Modus (Demo/Tests) und HTTPS-Modus (nur nach `rights_verified`)
- SSRF-Guard, Größenlimit, keine Archive
- SHA-256 + optionale HMAC-Signatur (`X-DiagNova-Signature`)
- Staging über Phase-06-Importvorschau
- Risikopolitik: Auto nur `dtc_descriptive`; Prozeduren/Adressen/Lizenzwechsel → `awaiting_approval`
- Atomare Publish über Import-Apply; Rollback über Import-Rollback + Versionsstatus
- Scheduler-Thread optional (`UPDATE_SCHEDULER_ENABLED`, Default **false**)

### Seed-Kanäle (alle default disabled)

| Key | Modus | Hinweis |
|-----|-------|---------|
| `sim-dtc-descriptive` | fixture | Auto erlaubt (Demo-Texte klar als simuliert) |
| `sim-procedures` | fixture | immer manuell |
| `sim-ecu-addresses` | fixture | immer manuell |
| `https-placeholder-disabled` | https | `example.invalid`, keine Rechte – nicht aktivierbar ohne Freigabe |

Keine erfundenen kommerziellen Feeds.

### API / UI

- `/api/data-updates/*` (Admin)
- UI `/data-updates`: Kanäle, letzter/nächster Lauf, Fehler, Freigabe, Rollback, Changelog

### Docs

- Requirements REQ-07-*, Capabilities, Phase-Status, Progress, free-data-sources aktualisiert

### Bewusst nicht

- Keine echten Auto-Downloads unbekannter Quellen
- Keine erfundenen kommerziellen Feeds
- **Phase 08 nicht gestartet**
- Kein Prod-Deploy, keine Hardwarefreigabe

## Tests (ausgeführt)

| Suite | Befehl | Ergebnis |
|-------|--------|----------|
| API + Protocols + Phase 06/07 | `PYTHONPATH=apps/api:packages/diagnostic-protocols/src python3 -m pytest tests -q` | **66 passed** |
| Connector xUnit | `dotnet test` | nicht ausgeführt (kein `dotnet`; Connector unverändert) |

Abnahme-Szenarien in `tests/api/test_phase07_data_updates.py`: neu, gleich/skip, defektes Schema, Lizenzwechsel, Netzfehler (Mock), Rollback, SSRF, Lock, manuelle Freigabe.

## Start

```bash
export PYTHONPATH="apps/api:packages/diagnostic-protocols/src"
# GET  /api/data-updates/dashboard
# POST /api/data-updates/channels/sim-dtc-descriptive/run  {"force": true}
# POST /api/data-updates/runs/{id}/approve|reject|rollback
```

UI: `/data-updates` (Admin). Scheduler: `UPDATE_SCHEDULER_ENABLED=true` nur bewusst setzen.

## Offene Punkte / Blocker

| ID | Thema |
|----|-------|
| BLK-OEM | Keine lizenzierten echten Update-Feeds |
| BLK-HW | Unverändert |
| BLK-DOCKER | Compose hier nicht ausgeführt |
| Phase 08 | Werkstatt-/Kundenverwaltung – nächster orchestrated Schritt |

## Geänderte / neue Dateien (Auswahl)

- `apps/api/alembic/versions/004_phase07_data_updates.py`
- `apps/api/app/models/data_updates.py`
- `apps/api/app/services/data_updates/*`
- `apps/api/app/api/routes/data_updates.py`
- `apps/api/app/data/phase07_channels.py` + Fixtures
- `apps/web/src/pages/DataUpdatesPage.tsx`
- `tests/api/test_phase07_data_updates.py`
- Docs / Progress
