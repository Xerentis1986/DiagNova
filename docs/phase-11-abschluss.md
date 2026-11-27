# Phase 11 – Abschlussbericht: Erweiterte Diagnose und Servicefunktionen

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-11-service-8820`  
**Basis:** Phase 10B `cursor/diagnova-phase-10b-brand-4bc4` (PR #18) – Designsystem beibehalten  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 12.

## Auftrag

Geführte Diagnose, ECU-Übersicht, Messwertgruppen, DTC-Hilfe und Servicekatalog (Öl/Inspektion, Batterie, EPB, DPF, Injektor, Drosselklappe, Lenkwinkel, Stellglieder, Grundeinstellungen). Jede Prozedur mit Specs, Voraussetzungen, Safety-Gates, Timeout, Abbruch, Ergebnisprüfung, Audit. Keine erfundenen OEM-Prozeduren. DPF-Off ausgeschlossen. Sicherheitskritische Funktionen ohne Freigabe klar deaktiviert.

## Umsetzung

### Servicekatalog & Gates

- Statischer Katalog `apps/api/app/data/service_catalog.py` – keine OEM-Schreibschritte
- Prozeduren inkl. DPF-Regen/EPB/Lenkwinkel: `release_status=disabled`, `enabled=false`, `write_allowed=false`
- `DPF_OFF` nur unter `excluded` (403)
- Gate-Simulation: Voraussetzungen, Bestätigungsphrase, Szenarien `missing_prereq` / `abort` / `comm_loss` / `normal`
- Live-Pfad `POST …/execute-live` immer 403
- Persistenz `service_runs` (Migration `008_phase11`) + Audit

### Geführte Diagnose

- `/api/guided/overview` – ECU-Kurzüberblick (kein Blindscan)
- Messwertgruppen (OBD-PIDs, simuliert)
- DTC-Hilfe: DB-Herkunft oder Simulator; unbekannt bleibt unbekannt; keine Auto-Reparatur

### UI (Designsystem 10B)

- `/service` – Katalog, Details, Gate-Test, Audit-Liste, Ausschlusshinweis
- `/guided` – ECU, Gruppen, DTC-Hilfe
- Nav/Dashboard/Settings verlinkt; Codierung bleibt „Geplant“

## Tests

| Suite | Ergebnis |
|-------|----------|
| `pytest tests -q` | **90 passed** (+7 Phase 11) |
| `apps/web` `npm run build` | **OK** |
| Connector `dotnet test` | nicht ausgeführt |

Abnahme-Szenarien abgedeckt: fehlende Voraussetzungen → `blocked`; Abbruch → `aborted`; Kommunikationsverlust → `failed`; Statusanzeige; keine Schreibbefehle.

## Reale Abdeckung (separat)

| Thema | Status |
|-------|--------|
| OEM-Serviceprozeduren | **nicht** vorhanden (BLK-OEM) |
| Hardware-Live-Service | **nicht** freigegeben (BLK-HW, BLK-RELEASE) |
| DPF-Regeneration / EPB / Bremsen | Katalog + Gates, Ausführung **deaktiviert** |
| DPF-Off / Abgas-Deaktivierung | **ausgeschlossen** |

## Bewusst nicht

- **Phase 12 nicht gestartet**
- Keine erfundenen UDS-/OEM-Schreibbefehle
- Kein Prod-Deploy / kein Fahrzeug-Schreibtest

## Geänderte Bereiche (Auszug)

- `apps/api/app/data/service_catalog.py`, `services/service_functions.py`, `services/guided_diagnosis.py`
- `apps/api/app/api/routes/{service,guided}.py`, `models/service.py`, `alembic/…/008_phase11_service.py`
- `apps/web/src/pages/{ServicePage,GuidedPage}.tsx`, Nav/API-Client
- `tests/api/test_phase11_service.py`
- Docs: requirements, capabilities, phase-status, DIAGNOVA_PROGRESS, dieser Bericht
