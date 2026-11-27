# Phase 21 – Abschlussbericht: B2B/B2C-Abrechnung & Adapter-Integration

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-21-billing-adapters-e3f2`  
**PR:** https://github.com/Xerentis1986/DiagNova/pull/32  
**Basis:** Phase 20 `cursor/diagnova-phase-20-readiness-e3f2` (PR #30)

## Auftrag

Verbindliche Ergänzung: vollständiges kaufmännisches Backend B2B+B2C (AT-Steuer/OSS/VIES), Multi-Adapter-Connector, Recherche OBD-DIAG 2055+ und Delphi/Autocom – ohne erfundene Hardwareerfolge und ohne proprietäre DLLs ohne Rechte.

## Erledigt

### Commerce

- Billing-Konten B2B/B2C, Consent, Lizenzen, Kündigung
- VIES-Prüfung (Stub + optional Live `VIES_LIVE=1`) mit Protokoll
- Steuerengine AT (Inland, EU Reverse Charge, B2C OSS-Demo, Drittland) – `draft_needs_review`
- Rechnungen + Gutschriften + JSON-Download
- UI `/commerce`
- Alembic `014_phase21`
- Tests `test_phase21_commerce.py`

### Connector / Adapter

- Multi-Adapter-Registry, Profile, AutoDetect-Kandidaten, Connection-Test
- Hardware-Inventur read-only + Hersteller-Anfrageentwurf
- J2534-Abstraktion ohne DLL-Bindung
- OBD-DIAG 2055+ und Delphi als **blocked** / Freigabe nötig – ELM nicht angenommen
- Unit-Tests Phase 21 (37 Connector-Tests gesamt)

### Dokumentation

- `DIAGNOVA_B2B_B2C_BILLING.md`
- `DIAGNOVA_TAX_CONFIGURATION.md`
- `DIAGNOVA_ADAPTER_RESEARCH.md`
- `DIAGNOVA_OBD_DIAG_2055_STATUS.md`
- `DIAGNOVA_DELPHI_AUTOCOM_STATUS.md`
- `DIAGNOVA_CONNECTOR_DRIVER_MATRIX.md`

## Tests

| Suite | Ergebnis |
|-------|----------|
| pytest | **154 passed** |
| `dotnet test` | **37 passed** |
| Web build | nach Commit prüfen |

## Bewusst nicht / offen

- Kein echter PSP (BLK-PAY)
- Keine produktive Steuerfreigabe
- Keine OBD-DIAG-/Delphi-Treiber ohne dokumentierte API
- Kein Hardware-/Fahrzeugtest
- Kein Prod-Redeploy
- Kein eigenständiger Herstellerkontakt (nur Anfrageentwurf)

## Verdict

Kaufmännische Simulation B2B/B2C **einsatzbereit für Demo**. Adapter-Hardware **nicht** freigegeben. Kommerzielle Echtzahlung und Live-Adapter weiter **NO-GO** bis Freigaben.
