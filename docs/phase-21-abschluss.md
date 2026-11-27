# Phase 21 – Abschlussbericht: B2B/B2C-Abrechnung & Adapter-Integration

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-21-billing-adapters-e3f2`  
**PR:** https://github.com/Xerentis1986/DiagNova/pull/32  
**Basis:** Phase 20 `cursor/diagnova-phase-20-readiness-e3f2` (PR #30)

## Auftrag

Verbindliche Ergänzung: vollständiges kaufmännisches Backend B2B+B2C (AT-Steuer/OSS/VIES), Multi-Adapter-Connector, Recherche OBD-DIAG 2055+ und Delphi/Autocom – ohne erfundene Hardwareerfolge und ohne proprietäre DLLs ohne Rechte.

**Ergänzung Delphi GitHub:** unabhängige CDP+-Protokollimplementierung (smooker/obd als Forschungsquelle, kein GPL-Copy).

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
- OBD-DIAG 2055+: **BlockedUndocumented** – ELM nicht angenommen
- Delphi/Autocom CDP+: **PartiallySupported** – eigenes Safe-Read-Modul (`*200`/`*201`/`*203`/`*20A`), Fake-Transport, FTDI-Abstraktion (ehrlicher Fail), Probe-Tool, CAN/Relais/Flash gesperrt
- Unit-Tests Phase 21 (Connector inkl. DelphiCdp)

### Dokumentation

- `DIAGNOVA_B2B_B2C_BILLING.md`
- `DIAGNOVA_TAX_CONFIGURATION.md`
- `DIAGNOVA_ADAPTER_RESEARCH.md`
- `DIAGNOVA_OBD_DIAG_2055_STATUS.md`
- `DIAGNOVA_DELPHI_AUTOCOM_STATUS.md`
- `DIAGNOVA_DELPHI_GITHUB_RESEARCH.md`
- `DIAGNOVA_DELPHI_PROTOCOL_SPEC.md`
- `DIAGNOVA_DELPHI_DRIVER_STATUS.md`
- `DIAGNOVA_DELPHI_HARDWARE_TEST.md`
- `DIAGNOVA_DELPHI_LICENSE_REVIEW.md`
- `DIAGNOVA_CONNECTOR_DRIVER_MATRIX.md`

## Tests

| Suite | Ergebnis |
|-------|----------|
| pytest | unverändert (Commerce) – bei Push erneut |
| `dotnet test` | **44 passed** (inkl. DelphiCdp) |
| Web build | nach Commit prüfen |

## Bewusst nicht / offen

- Kein echter PSP (BLK-PAY)
- Keine produktive Steuerfreigabe
- Kein Live-Labor am Delphi-Adapter (VID/PID/`*200`/`*201` offen)
- Keine Fahrzeug-/Relais-/CAN-Befehle, kein Auto-Firmwareupdate
- Kein GPL-Code aus smooker/obd in der Binary
- Kein Prod-Redeploy

## Verdict

Kaufmännische Simulation B2B/B2C **einsatzbereit für Demo**. CDP+-Geräte-Lese-Pfad **simuliert/codec-fertig**, Hardware **nicht** freigegeben. Kommerzielle Echtzahlung und Live-Adapter weiter **NO-GO** bis Freigaben.
