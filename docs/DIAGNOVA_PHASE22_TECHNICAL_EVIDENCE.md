# Phase 22 – Technische Evidenz

**Stand:** 2026-11-28 Europe/Vienna  
**Branch:** `cursor/diagnova-phase-22-completion-fb46`  
**Basis:** Phase 21 `6404f5c` / PR #32  
**Methode:** Code-Review + automatisierte Tests. Keine physische Hardware, keine Stripe-Live-Keys, kein Prod-Deploy.

## Evidence-Klassen

| Klasse | Bedeutung |
|--------|-----------|
| A | Automatisiert grün (pytest/dotnet) |
| B | Code vorhanden, HW/externe Umgebung ungetestet |
| C | Code/Dry-run; Prod-Pfad BLOCKED |
| D | Dokumentiert, nicht implementiert |
| E | Explizit nicht möglich / undokumentiert |

## Automatisierte Tests (ehrlich)

| Suite | Befehl | Ergebnis |
|-------|--------|----------|
| API | `pytest tests/api -q` | **144 passed** |
| Phase-22 neu | `pytest tests/api/test_phase22_bridge_mfa_pdf.py -q` | **4 passed** |
| Connector | `dotnet test` | **46 passed** |
| GitHub Actions | – | **nicht vorhanden** (weder rot noch grün) |

## Inventar A–E (Auszug)

| Bereich | Klasse | Pfade / APIs | Hinweis |
|---------|--------|--------------|---------|
| Live-Bridge DEMO | A | `services/connector_bridge.py`, `routes/diagnostics.py`, `DiagnosticsPage.tsx` | `mode=demo` → Simulator |
| Live-Bridge LIVE HTTP | A/B | Bridge `GET/POST` → Connector | Ohne Connector: 503, kein Fake |
| LIVE am Adapter | BLOCKED / NOT TESTED | – | Windows+HW nötig |
| CDP+ VCP mit preferred COM | B | `ICdpTransport.cs` `FtdiCdpTransport` | SerialPort 115200 |
| CDP+ ohne Port | A | Unit: ehrlicher Fail | Kein D2XX Bundle |
| OBD-DIAG Treiber | E | `ObdDiagAdapterService` | Nur Inventur |
| OBD-DIAG Probe | B | `POST /adapters/obd-diag/inventory-probe` | Nichtinvasiv |
| Invoice PDF | A | `commerce/invoice_pdf.py`, `?format=pdf` | Magic `%PDF` |
| MFA TOTP Admin | A | `mfa_totp.py`, `/api/admin/mfa/*` | Migration 015 |
| E-Mail Auth | C | password-reset / email-confirm | dry_run ohne SMTP |
| Lizenz-Gate | C | `LicenseGateService`, OBD 402 | Sim-Pfad erlaubt |
| Installer | E/PARTIAL | `scripts/publish-win-x64.ps1` | Kein MSI/Signing |
| Stripe E2E | BLOCKED | Phase-21 Provider | Keys fehlen |
| Steuer | BLOCKED | `draft_needs_review` | Fachprüfung |
| Prod-Deploy | BLOCKED | – | Freigabe |

## Migrationen

- `015_phase22_mfa_bridge.py` – MFA-Spalten auf `users`

## Blocker (BLK)

| ID | Beschreibung | Typ |
|----|--------------|-----|
| BLK-HW-01 | Kein physischer CDP+/OBD-DIAG am Runner | Extern |
| BLK-STRIPE-01 | Keine Test-/Live-Keys | Extern |
| BLK-SMTP-01 | Kein Prod-SMTP | Extern |
| BLK-SIGN-01 | Kein Code-Signing-Zertifikat | Extern |
| BLK-MSI-01 | Kein WiX/MSIX Pipeline | Intern/extern |
| BLK-OBDDIAG-01 | Undokumentiertes Protokoll | Extern/IP |
| BLK-TAX-01 | Steuerfreigabe offen | Extern |
| BLK-DEPLOY-01 | Prod-Deploy gesperrt | Policy |

## Verdict

**NO-GO** für kommerziellen Verkauf und Fahrzeug-Vollbetrieb.  
Softwareketten lokal signifikant verbessert; externe Abhängigkeiten blockieren Abnahme.
