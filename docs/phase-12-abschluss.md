# Phase 12 – Abschlussbericht: Steuergerätecodierung und Programmierung

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-12-coding-2dd5`  
**Basis:** Phase 11 `cursor/diagnova-phase-11-service-8820` (PR #19) – Designsystem 10B beibehalten  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 13.

## Auftrag

ECU-Identifikation, Softwarestand, Codierprofil und J2534/D-PDU-Integration anhand dokumentierter Treiber. Herstellerzugänge und Flash nur autorisiert. VIN/ECU/SW/Signatur/Spannung/Verbindung/Berechtigung/Wiederherstellungsplan prüfen. Originalcodierung nur wenn offiziell unterstützt. Lokale Ausführung, kein Auto-Retry, Audit, Zustandsmaschine. Simulation zuerst; reale Schreib-/Flashfunktion bis Hardware, OEM-Daten und Freigabe **deaktivieren**.

## Umsetzung

### Katalog & Gates

- Statischer Katalog `apps/api/app/data/coding_catalog.py` – keine erfundenen OEM-Flashprotokolle
- Codierung/Flash: `release_status=disabled`, `enabled/write_allowed/flash_allowed=false`
- Identifikation lesend (`ECU_IDENTIFY_READ`); Codierprofil ohne Spec = `unavailable`
- Gate-Szenarien: `missing_prereq`, `wrong_vehicle`, `voltage_drop`, `abort`, `comm_loss`, `normal`
- Live `…/execute-live` und `…/flash` immer **403**; Auto-Retry verboten
- Persistenz `coding_runs` (Migration `009_phase12`) + Audit

### Spannungs-/Kompatibilitäts-Framework

- `POST /api/coding/compatibility-check` – VIN, Spannung, Spec, Berechtigung, Recovery, Signatur-Status
- Flash/Schreiben bleiben auch bei „overall_ok“ Framework-seitig blockiert (`flash_blocked`)

### J2534 / D-PDU

- Katalog + `/api/coding/interfaces` = `documented_prep`
- Keine Vendor-DLL, kein PassThruOpen, keine Flash-Routine

### UI (Designsystem 10B)

- `/coding` – Identifikation, Kompatibilitätsprüfung, Katalog, Gate-Test, Audit
- Nav/Dashboard/Settings verlinkt; Flash Live bleibt „Geplant“

## Tests

| Suite | Ergebnis |
|-------|----------|
| `pytest tests -q` | **97 passed** (+7 Phase 12) |
| `apps/web` `npm run build` | **OK** |
| Connector `dotnet test` | nicht ausgeführt |

Abnahme-Szenarien: falsches Fahrzeug → `blocked`; Spannungsabfall → `failed` ohne Retry; Abbruch → `aborted`; Live/Flash → 403.

## Reale Abdeckung (separat)

| Thema | Status |
|-------|--------|
| OEM-Codier-/Flashdaten | **nicht** vorhanden (BLK-OEM) |
| J2534 Hardware/DLL | **nicht** vorhanden (BLK-J2534, BLK-HW) |
| Live-Schreiben/Flash | **nicht** freigegeben (BLK-RELEASE) |
| Unautorisierter Flash / Abgas-Codierung | **ausgeschlossen** |

## Bewusst nicht

- **Phase 13 nicht gestartet**
- Keine erfundenen Flash-Routinen
- Kein Prod-Deploy / kein Fahrzeug-Schreibtest

## Geänderte Bereiche (Auszug)

- `apps/api/app/data/coding_catalog.py`, `services/coding.py`, `schemas/coding.py`, `models/coding.py`
- `apps/api/app/api/routes/coding.py`, `alembic/…/009_phase12_coding.py`
- `apps/web/src/pages/CodingPage.tsx`, Nav/API-Client
- `tests/api/test_phase12_coding.py`
- Docs: requirements, capabilities, phase-status, DIAGNOVA_PROGRESS, dieser Bericht
