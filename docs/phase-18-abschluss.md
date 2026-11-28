# Phase 18 – Abschlussbericht: Optionales Chiptuning (Architektur)

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-18-chiptuning-c46a`  
**Basis:** Phase 17 `cursor/diagnova-phase-17-acceptance-8ffe` (PR #26)  
**Nächste Phase:** **19 nicht gestartet**

## Auftrag

Separates optionales Modul nach PKW-Freigabe. Zunächst nur Verwaltung autorisierter Originalsoftwarestände, Versionshistorie, Kompatibilität, Genehmigungsnachweise, Audit und simulierte Arbeitsabläufe. Keine aktiven Kennfeldänderungen oder Flashfunktionen. Keine Manipulation vorgeschriebener Abgas-/Sicherheitssysteme. Produktive Aktivierung standardmäßig gesperrt.

## Implementiert

| Bereich | Inhalt |
|---------|--------|
| Katalog | `apps/api/app/data/tuning_catalog.py` – Baselines, Historie, Kompatibilität, Genehmigung, Legal-Gates, Workflow-Sim |
| Ausgeschlossen | MAP_CHANGE_ACTIVE, TUNING_FLASH, EMISSION_DEFEAT_TUNE, SAFETY_SYSTEM_DISABLE, RAW_REMOTE_TUNE |
| Persistenz | Alembic `013_phase18` – Baselines, Approvals, Version History, Workflow Runs |
| API | `/api/tuning/*` – Status, Katalog, Baselines, Approvals, Historie, Legal-Gates, Runs |
| Gates | Legal/technisch; Map/Flash/Aktivierung immer blockiert (`…/activate`, `…/map-change`, `…/flash` → 403) |
| UI | `/tuning` mit Badges **Geplant / Deaktiviert**; Nav „Geplant“ |
| Audit | `tuning.baseline_register`, `tuning.approval_register`, `tuning.run_*` |
| Tests | `tests/api/test_phase18_tuning.py` |

## Bewusst nicht enthalten

- Keine Tuning-Algorithmen / Kennfeldänderungen  
- Keine Flash-Routinen / Map-Binaries  
- Keine Abgas- oder Sicherheitsmanipulation  
- Keine produktive Aktivierung  
- Phase 19 (LKW) nicht gestartet  

## Abnahme

| Kriterium | Ergebnis |
|-----------|----------|
| Rollen (admin/technician für Schreib-/Sim-Pfade) | OK |
| Dokumente (Genehmigungsnachweise) | OK (Metadaten) |
| Versionen / Baselines | OK (Demo-Metadaten) |
| Simulation / Gates | OK |
| Produktive Aktivierung gesperrt | OK (403 + Flags) |

## Blocker

| ID | Thema |
|----|-------|
| BLK-LEGAL | Rechtliche Freigabe / Genehmigung offen |
| BLK-OEM | Keine lizenzierten OEM-Softwarestände/Maps |
| BLK-HW | Keine geeignete Programmier-Hardware |
| BLK-RELEASE | Explizite Freigabe für Aktivierung fehlt |

## Tests / Build (Europe/Vienna)

| Check | Ergebnis |
|-------|----------|
| `pytest tests/api` | **115 passed** |
| `pytest tests/api/test_phase18_tuning.py` | **8 passed** |
| Web-Build (`apps/web` 0.18.0) | OK |
| Prod-Redeploy | **nicht** ausgeführt |

## Status

**Phase 18: Architektur implementiert, Modul geplant/deaktiviert.** Kein Prod-Redeploy ohne Freigabe. Phase 19 nicht gestartet.
