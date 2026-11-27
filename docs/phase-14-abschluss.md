# Phase 14 – Abschlussbericht: Software- und Connector-Updates

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-14-software-updates-8f1e`  
**Basis:** Phase 13 `cursor/diagnova-phase-13-subscriptions-66ed` (PR #21) – Designsystem 10B beibehalten  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 15.

## Auftrag

Softwareupdates von Diagnosedatenupdates trennen. API, Web und Connector versionieren; Kompatibilitätsmatrix, Release Notes, Updatekanäle, Migrationsplan. Signierte Releases / Integrität; ohne Signaturzertifikat produktive Auto-Updates sperren. Keine Updates während Diagnose, Service oder Flash. Staging, atomare Installation, Healthcheck, Rollback. Admin-Anzeige für Versionen und Updatefehler. Abnahme: manipuliertes Paket ablehnen, inkompatible Version erkennen, Abbruch/Rollback simulieren.

## Umsetzung

### Trennung & Versionierung

- Software-Updates unter `/api/software-updates` und UI `/software-updates`
- Diagnosedaten-Updates bleiben `/api/data-updates` / `/data-updates`
- Komponentenversionen: API / Web / Connector **0.14.0** (`COMPONENT_VERSIONS`)
- `/version` und `/health` melden Komponentenversionen

### Integrität & Kanäle

- SHA-256-Checksum + HMAC-SHA256 (Demo-Secret, nicht für Prod)
- `software_update_signing_cert_configured=false` → produktive Auto-Updates gesperrt
- `software_update_auto_install_enabled=false` – keine ungeprüften Auto-Installs
- Kanäle: `stable-fixture` (Simulation), `production-blocked` (Zertifikatspflicht)

### Pipeline

1. Ingest (Fixture) → Integrität → Kompatibilität  
2. `awaiting_approval` (immer Admin-Freigabe)  
3. Busy-Gate (offene Diagnose / laufender Service / Codierung / kritische Ops)  
4. Atomare Installation (Simulation) → Healthcheck  
5. Healthcheck-Fail → automatischer Rollback; manueller Rollback auf `previous_version`

### Connector

- `Updates/ConnectorVersion`, `UpdateBusyGate`, `UpdateService`
- Endpunkte: `/version`, `/updates/status`, `/updates/busy`, `/updates/stage`, `/updates/rollback`
- Installer-Dokumentation: `docs/connector-installer.md`

### Persistenz

- Alembic `011_phase14` – components, channels, packages, runs, compatibility, events

### UI

- `/software-updates` mit Designsystem 10B (PageHeader/Panel/Badge)
- Nav: Software-Updates getrennt von Daten-Updates
- Link von `/admin`

## Tests

| Suite | Ergebnis |
|-------|----------|
| `pytest tests -q` | **113 passed** (+9 Phase 14) |
| `apps/web` `npm run build` | **OK** |
| Connector-Unit (dotnet) | Umgebung ohne `dotnet` – Code + `Phase14UpdateTests.cs` hinterlegt |

Abnahme: manipuliertes Paket rejected; Web 0.15 inkompatibel rejected; Busy während Diagnose; Healthcheck-Fail → Rollback; Production ohne Zertifikat gesperrt.

## Blocker

| Thema | Status |
|-------|--------|
| Echtes Code-Signing-Zertifikat | **fehlt** (BLK-CERT) – Prod-Auto-Updates gesperrt |
| Echte Windows-Installer-Pipeline | dokumentiert, nicht produktiv ausgerollt |
| Prod-Deploy | nicht Teil dieser Phase |

## Bewusst nicht

- **Phase 15 nicht gestartet**
- Keine ungeprüften Auto-Installs
- Kein Prod-Deploy / kein echtes Zertifikat

## Geänderte Bereiche (Auszug)

- `apps/api/app/models/software_updates.py`, `services/software_updates/*`, `api/routes/software_updates.py`
- Migration `011_phase14`; Seed Komponenten/Kanäle/Matrix; Fixtures `phase14_*.json`
- `apps/web`: `SoftwareUpdatesPage`, Nav, API-Client
- `apps/windows-connector`: Updates-Namespace + Endpunkte
- Docs: requirements, capabilities, phase-status, DIAGNOVA_PROGRESS, connector-installer, dieser Bericht
