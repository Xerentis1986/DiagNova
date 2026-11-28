# Phase 10 – Abschlussbericht: PDF-Diagnoseberichte und Archiv

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-10-pdf-7d82`  
**Basis:** `origin/cursor/diagnova-phase-09-history-f3fe` (PR #14)  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 11.

## Auftrag (Master-Prompt 10)

Serverseitige A4-PDFs mit Werkstattlogo, Berichtsnummer, Datum, Kunden-/Fahrzeugdaten, VIN, Kilometerstand, Adapter, Protokoll, geprüften/nicht geprüften ECU, DTCs, Messwerten, Freeze-Frame, Notizen und Empfehlungen. Fehlende Daten als „nicht verfügbar“; Demo-Wasserzeichen; keine automatisch erfundene Reparaturdiagnose. Druckfreundliche Umbrüche, Unicode, Kopf-/Fußzeile. Vorschau, Download, Druck, CSV, Archiv, Suche; optionale Auto-PDF-Erstellung. Unveränderlicher Snapshot mit Datenversion, autorisierte Downloads, Aufbewahrung/Löschung. Abnahme: lange Tabellen, Umlaute, leere Daten, Demo, erneuter Download, fremde Mandanten.

## Umsetzung

### Datenmodell

- Alembic `007_phase10` + Erweiterung `DiagnosticReport`
- Felder: `workshop_id`, `vehicle_id`, `customer_id`, `report_number` (DN-YYYY-NNNNNN), `data_source`, `data_version`, `content_sha256`, `notes`, `recommendations` (nur manuell), `auto_generated`, `frozen_at`, `archived_at`, `deleted_at`
- Unveränderlicher JSON-Snapshot nach Create (Hash); PDF wird aus Snapshot regeneriert

### Services / PDF

- `app/services/reports.py`: Snapshot aus Sitzungshistorie (ECU/DTC/Messwerte/FF), Werkstatt/Kunde; Fallback nur Simulator klar als `simulated`
- ReportLab A4, DejaVu-Unicode, Kopf/Fuß, Demo-Wasserzeichen, Seitenumbrüche
- Fehlende Felder → „nicht verfügbar“; `repair_diagnosis_auto=false`
- Archiv, Soft-Delete, Purge nach `workshop.retention_days`

### API / UI

| Bereich | Endpunkte / UI |
|---------|----------------|
| Liste/Suche | `GET /api/reports?q=&vin=&include_archived=` |
| Erzeugen | `POST /api/reports` (+ optionale Notizen/Empfehlungen) |
| Vorschau | `GET /api/reports/{id}` |
| Export | `…/export.pdf`, `…/export.csv` |
| Archiv/Löschen | `POST …/archive`, `DELETE …` (Admin), `POST /reports/purge-expired` |
| Auto-PDF | `POST /sessions/{id}/close?auto_pdf=true` |
| UI | `/reports` – Suche, Vorschau, PDF/CSV, Archiv |

### Docs

- Requirements REQ-10-*, Capabilities, Phase-Status, Progress aktualisiert

### Bewusst nicht

- Keine echten Live-Fahrzeugberichte als echt
- Keine automatisch erfundenen Reparaturempfehlungen
- **Phase 11 nicht gestartet**
- Kein Prod-Deploy

## Tests (ausgeführt)

| Suite | Befehl | Ergebnis |
|-------|--------|----------|
| API + Protocols + Phase 06–10 | `PYTHONPATH=apps/api:packages/diagnostic-protocols/src python3 -m pytest tests -q` | **83 passed** |
| Connector xUnit | `dotnet test` | nicht ausgeführt (kein `dotnet`; Connector unverändert) |

Abnahme in `tests/api/test_phase10_pdf_reports.py`: Umlaute/Demo/Redownload-Hash, lange Tabellen, Auto-PDF+Archiv, Cross-Tenant 404, Snapshot-Immutabilität.

## Start

```bash
export PYTHONPATH="apps/api:packages/diagnostic-protocols/src"
# POST /api/reports  {"session_id":"…","title":"…","notes":"…","recommendations":"…"}
# GET  /api/reports?q=…&vin=…
# GET  /api/reports/{id}/export.pdf | export.csv
# POST /api/sessions/{id}/close?auto_pdf=true
```

UI: `/reports`. Migration: `alembic upgrade head` (Revision `007_phase10`).

## Offene Punkte / Blocker

| ID | Thema |
|----|-------|
| BLK-HW | Keine echten Live-Berichte ohne Hardware |
| BLK-LEGAL | Aufbewahrung/Löschung rechtlich freigeben |
| Phase 11 | Erweiterte Diagnose / Service – nächster orchestrated Schritt |
