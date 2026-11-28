# Phase 23 – Technische Evidenz

**Stand:** 2026-11-28 Europe/Vienna  
**Branch:** `cursor/diagnova-phase-23-completion-806e`  
**Basis:** Phase 22 `dff8d32` / PR #33  

## Tests (ehrlich, keine Doppelzählung)

| Suite | Befehl | Ergebnis |
|-------|--------|----------|
| pytest `tests/api` | `pytest tests/api -q` | **151 passed** |
| davon Phase-23 SSRF/Commerce | `test_phase23_ssrf_license_commerce.py` | 5 passed (in 151) |
| davon Connector-E2E | `test_phase23_connector_e2e.py` | 2 passed (Connector-Prozess+Fake) |
| dotnet | `dotnet test -c Release` | **52 passed** |
| Web | `npm run build` (tsc+vite) | **PASS** |
| GitHub Actions | Workflows im Repo | **NOT TESTED** auf GitHub (lokal validiert) |
| Inno Setup EXE | Windows-Runner CI | **NOT TESTED** lokal (Linux); Artefakt-Job vorhanden |

## Kernnachweise

| Thema | Klasse | Pfad / Test |
|-------|--------|-------------|
| SSRF Connector-URL | A | `connector_bridge.validate_connector_base_url`, Test |
| Live-Bridge E2E | A | Connector-Prozess + Fake-Adapter + API LIVE |
| Lizenz-Gate voll | A | HMAC Token/Revoke/Fremdgerät; alle `/obd/*` |
| Offline-Token API | A | `POST /api/billing/licenses/offline-token` |
| Invoice PDF / MFA | A | Regression Phase 23 |
| Stripe Signatur Fixture | A | `verify_stripe_signature` |
| SMTP intern | A | smtplib-Stub (Prod SMTP BLOCKED) |
| Inno Installer-Projekt | B | `installer/DiagNovaConnector.iss` UNSIGNED |
| CDP+ Reconnect/Caps | B | `FtdiCdpTransport.ReconnectAsync` |
| OBD-DIAG Treiber | E | Stub Transport; BlockedUndocumented |

## Blocker

BLK-HW-01, BLK-STRIPE-KEYS, BLK-SMTP-PROD, BLK-CERT (Signing), BLK-OBDDIAG-PROTO, BLK-TAX, BLK-DEPLOY, BLK-GA-RUN (CI auf GitHub noch nicht gelaufen).
