# Phase 22 – Implementierungsübersicht

**Stand:** 2026-11-28 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-22-completion-fb46`  
**Basis:** Phase 21 Tip `6404f5c` / PR #32  
**Worker:** Phase-22 vollautonom, keine Betreiber-Rückfragen

## Entscheidungen

1. **DEMO vs LIVE strikt getrennt** – LIVE ruft nur Connector; Fehler = 503, kein Simulator-Fallback.
2. **CDP+ Transport** – VCP via `System.IO.Ports` wenn preferred COM gesetzt; kein gebündeltes FTDI D2XX (Lizenz/Deploy).
3. **OBD-DIAG** – bleibt BlockedUndocumented; neuer Inventur-Probe statt ELM-Fake.
4. **PDF** – reportlab lokal; SHA-256 Notiz in Metadaten; keine Steuerfreigabe.
5. **MFA** – TOTP Pflichtpfad für Platform-Admins; Login mit `mfa_code`.
6. **Lizenz-Gate** – Connector prüft vor Live-OBD; Simulator-Pfad bleibt für Dev.
7. **Installer** – nur self-contained publish Script; kein Fake-Signing.

## Priorität §24 – Status

| Prio | Thema | Status |
|------|-------|--------|
| 1 | Live-Bridge | DONE (DEMO A; LIVE E2E BLOCKED/HW) |
| 2 | FTDI CDP+ | PARTIAL (VCP Code) |
| 3 | OBD-DIAG | PARTIAL (Inventur) |
| 4 | Installer | PARTIAL (publish.ps1) |
| 5 | Stripe E2E | BLOCKED Keys |
| 6 | PDF | DONE |
| 7 | E-Mail | PARTIAL dry_run |
| 8–9 | Admin/MFA | DONE Code+Test |
| 10 | Lizenz-Gate | PARTIAL |
| 11 | Tests | 144+46 grün |
| 12 | Deploy-Prep | Docs only |
| 13 | Abschluss | Docs + PR |

## Neue/geänderte Kernpfade

- `apps/api/app/services/connector_bridge.py`
- `apps/api/app/services/mfa_totp.py`
- `apps/api/app/services/commerce/invoice_pdf.py`
- `apps/api/alembic/versions/015_phase22_mfa_bridge.py`
- `apps/windows-connector/.../ICdpTransport.cs` (FtdiCdpTransport)
- `apps/windows-connector/.../LicenseGateService.cs`
- `apps/windows-connector/scripts/publish-win-x64.ps1`
- `tests/api/test_phase22_bridge_mfa_pdf.py`
- `apps/web/src/pages/DiagnosticsPage.tsx` (DEMO/LIVE)

## BLOCKED (Policy)

Prod-Deploy, Live-Stripe, Firmware-Flash, Schreib-Diagnose, destruktive Prod-DB, unlizenzierte IP, Rechts-/Steuerfreigabe.
OEM-Logos + Wordmark ohne Symbol-Icon: unverändert (Deploy-Gate).
