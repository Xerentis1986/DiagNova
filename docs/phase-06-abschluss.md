# Phase 06 – Abschlussbericht: Diagnosedatenbank und Datenimporte

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-06-database-80ce`  
**Basis:** `origin/cursor/diagnova-phase-05-multiprotocol-dd50` (PR #9)  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 07.

## Auftrag (Master-Prompt 06)

Versioniertes Datenmodell (Hersteller/Modelle/Varianten/ECU/Adressen/Protokolle/DTC/PID/DID/Einheiten/Service); JSON/CSV-Import mit Validierung, Quarantäne, Konfliktbericht, Vorschau, Transaktion, Rollback; freie Quellen mit Lizenz/Attribution; keine Bosch/Gutmann/Delphi-Kopien; unbekannte DTCs als unbekannt; Herkunft bis UI; keine Vollständigkeit vortäuschen.

## Umsetzung

### Datenmodell

- Alembic `003_phase06` + ORM in `app/models/diagnostic_data.py`
- Pflicht-Herkunft über `data_license_sources`
- Trennung `generic` / `oem`; Dataset-Versionen

### Import

- Schema `diagnova.diagnostic-import.v1` (Pydantic)
- JSON-Preview/Apply/Rollback; CSV für DTC/PID
- Quarantäne bei Schema-/Zeilenfehlern; Blocklist Bosch/Gutmann/Delphi
- ODX/PDX → **403** (REQ-06-ODX)

### Lookup / UI

- `GET /api/diagnostic-data/dtcs/{code}` → „unbekannt“ ohne Text
- UI `/diagnostic-data`: Quellen, Lookup, Demo-Import, PID/ECU-Herkunft
- Coverage-Endpoint ohne Vollständigkeitsanspruch

### Baseline-Seed

- Generische PIDs (bestehendes Subset), ISO-15765-4 ECUs 7E0/7E8 & 7E1/7E9
- DTC-Codes **ohne** Beschreibungstext
- Dokumentierte Quellen inkl. „DTC-Texte nicht redistribuierbar“

### Docs

- `docs/free-data-sources.md`, `docs/diagnostic-data-model.md`
- Requirements / Capabilities / Phase-Status / Progress aktualisiert

### Bewusst nicht

- Keine erfundenen OEM-DTC-Texte / Service-Schritte
- Keine Bosch/Gutmann/Delphi-Daten
- Kein ODX-Live-Import
- **Phase 07 nicht gestartet**
- Kein Prod-Deploy, keine Hardwarefreigabe

## Tests (ausgeführt)

| Suite | Befehl | Ergebnis |
|-------|--------|----------|
| API + Protocols + Phase 06 | `PYTHONPATH=apps/api:packages/diagnostic-protocols/src python3 -m pytest tests -q` | **50 passed** |
| Connector xUnit | `dotnet test` | **nicht ausgeführt** (kein `dotnet` in dieser Umgebung); Phase-05-Connector unverändert |

Nicht ausgeführt: Docker Compose (BLK-DOCKER); echte OEM-Datenimporte (BLK-OEM).

## Start

```bash
export PYTHONPATH="apps/api:packages/diagnostic-protocols/src"
# GET /api/diagnostic-data/sources · /dtcs/P0301 · /coverage
# POST /api/diagnostic-data/import/preview  (JSON)
# POST /api/diagnostic-data/import/{batch_id}/apply|rollback
```

UI: `/diagnostic-data` (angemeldet).

## Offene Punkte / Blocker

| ID | Thema |
|----|-------|
| BLK-OEM | Keine lizenzierten OEM-/ODX-Daten |
| BLK-HW | Unverändert |
| BLK-DOCKER | Compose hier nicht ausgeführt |
| Phase 07 | Auto-Updates – nächster orchestrated Schritt |

## Abnahme-Checkliste Prompt 06

| Kriterium | Status |
|-----------|--------|
| Versioniertes Modell inkl. Herkunft | OK |
| JSON/CSV Validierung + Quarantäne | OK |
| Konfliktbericht / Vorschau / Rollback | OK |
| Unbekannte DTCs → „unbekannt“ | OK |
| Freie Quellen dokumentiert, nichts erfunden | OK |
| Keine Bosch/Gutmann/Delphi-Kopien | OK (Blocklist + Docs) |
| ODX nur mit Lizenz – hier gesperrt | OK (403) |
| Herkunft bis UI | OK |
| Keine Vollständigkeit vortäuschen | OK (Coverage-Disclaimer) |
| Phase 07 nicht gestartet | OK |
