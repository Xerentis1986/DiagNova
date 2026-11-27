# Phase 19 – Abschlussbericht: LKW / Nutzfahrzeug (Architektur)

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-19-lkw-arch-9892`  
**PR:** https://github.com/Xerentis1986/DiagNova/pull/27  
**Basis:** Phase 17 `cursor/diagnova-phase-17-acceptance-8ffe` (PR #26) – kein Phase-18-Branch vorhanden  
**Nächste Phase:** **nicht** gestartet – kein J1939-Parser/HW ohne Freigabe; Phase 18 optional separat.

## Auftrag (Scope)

Architektur only laut Coordinator: J1939/RP1210 Prep, Capability-Flags, UI „Geplant“.  
**Keine** vorgetäuschten LKW-Diagnosefunktionen (kein SPN/FMI-Stack, kein Fake-Simulator).

## Umsetzung

### Architektur & Docs

- `docs/lkw-j1939-architecture.md` – Schichtentrennung, Blocker, Abgrenzung PKW
- `docs/j2534-doip-j1939-prep.md` / `adapter-capability-matrix.md` aktualisiert
- Protokollkatalog: `sae_j1939`, `rp1210`, `sae_j1708_j1587` → `documented_prep`

### Capability-Flags

- API `GET /api/lkw/capabilities` – alle Flags `enabled=false`
- Adapter `rp1210-commercial` in Python- + Connector-Matrix (`planned`, `hardware_tested=false`)
- ELM/Simulator: J1939/RP1210 explizit `not_supported`
- Katalog-Cap `lkw_j1939_rp1210` unter unavailable/planned

### Marken (Navigation only)

MAN, Mercedes-Benz Trucks, Scania, Volvo Trucks, DAF, Iveco, Renault Trucks –  
`release_status=planned`, `diagnosis_available=false`

### API / Gates

| Endpoint | Verhalten |
|----------|-----------|
| `GET /api/lkw/architecture` | Prep-Status |
| `GET /api/lkw/brands` | Markenkatalog |
| `GET /api/lkw/capabilities` | Flags |
| `POST /api/lkw/diagnose` | **403** |
| `POST /api/lkw/j1939/read` | **403** |
| `POST /api/lkw/rp1210/connect` | **403** |

### UI

- `/lkw` – Architektur, Marken, Flags mit Badge „Geplant“
- Nav „Weitere“ + Dashboard-Schnellzugriff
- `/planned/lkw` Platzhalter mit Link zur Architekturseite
- Tarife `lkw_planned` / `kombi_planned` unverändert nicht buchbar

## Tests

| Suite | Ergebnis |
|-------|----------|
| `pytest tests -q` | **134 passed** (+8 Phase 19) |
| `apps/web` `npm run build` | **OK** |

## Bewusst nicht enthalten

- J1939-Parser / SPN/FMI / Transport BAM
- RP1210-DLL-Bindung
- LKW-Simulator mit Messwerten
- OEM-Service/Schreiben
- Hardwarefreigabe / Live-Tests

## Blocker

| ID | Wirkung |
|----|---------|
| BLK-HW | Keine 24-V/RP1210-Hardware |
| BLK-OEM | Keine LKW-OEM-Daten |
| BLK-ADAPTER | Keine Vendor-RP1210-API im Repo |

## Abnahme

| Kriterium | Status |
|-----------|--------|
| Architektur dokumentiert | OK |
| Capability-Flags ehrlich (aus) | OK |
| UI „Geplant“ | OK |
| Keine Fake-Diagnose | OK (403) |
| Parser/HW-Test | N/A – bewusst nicht |
