# Phase 24 – Technische Evidenz

**Stand:** 2026-11-28 Europe/Vienna  
**Branch:** `cursor/diagnova-phase-24-completion-fd1f`  
**Basis:** Phase 23 `0b05cb2` / PR #34  

## Tests

| Suite | Ergebnis |
|-------|----------|
| pytest `tests/api` | **156 passed** |
| dotnet test | **55 passed** |
| npm run build | **PASS** |
| GitHub Actions (Phase 23 tip) | **PASS** 8/8 (run 46088694592) |
| Phase-24 CI (dieser PR) | nach Push – Subscription |

## Highlights

| Thema | Status | Evidence |
|-------|--------|----------|
| UNSIGNED Inno EXE | PASS (Artefakt) | Name/Größe/SHA-256 unten |
| Asymmetrische Offline-Lizenz RSA | PASS | `license_crypto.py`, Connector Verify |
| Portable Install-E2E | PASS | `test_phase24_connector_install_e2e` |
| Hardware-Probe JSON | PASS (Code+API) | `GET /hardware/probe` – HW NOT TESTED |
| Steuer AT/EU/RC/OSS/UID/Drittland | PASS Tests | Freigabe weiter BLOCKED |
| Stripe/SMTP | Fixtures PASS | Keys/Prod BLOCKED |

## Installer Artefakt

Siehe `docs/artifacts/INSTALLER_SHA256SUMS.txt` und `/opt/cursor/artifacts/DiagNovaConnectorSetup-0.23.0-unsigned.exe`

- Name: `DiagNovaConnectorSetup-0.23.0-unsigned.exe`
- Größe: 32294999 Bytes
- SHA-256: `b6c4bcb53938ca4f3d2e6c409f2633225a7df41a2296ca6887d957148024f0a9`
- Quelle: CI run 46088694592 (UNSIGNED)
- Signing: **UNSIGNED** (BLK-CERT)

## Verdict

**NO-GO** kommerziell / Fahrzeug-Vollbetrieb. Interne Lücken weiter geschlossen.
