# Phase 23 – Completion Matrix

| ID | Thema | Status | Evidence |
|----|-------|--------|----------|
| I1 | Inno Setup Projekt | PASS (Projekt) / NOT TESTED (Build Windows) | `.iss` + `build-installer.ps1` |
| I2 | Publish win-x64 | PASS Script | `publish-win-x64.ps1` |
| I3 | Code-Signing | BLOCKED | UNSIGNED markiert |
| C1 | GitHub Actions CI | PASS (Dateien) / NOT TESTED (Run) | `.github/workflows/ci.yml` |
| B1 | Live-Bridge SSRF | PASS | Allowlist Loopback |
| B2 | E2E Connector+Fake | PASS | pytest E2E |
| L1 | License Gate all OBD | PASS | Program.cs + Tests |
| L2 | HMAC Offline Token | PASS | API + Connector |
| D1 | CDP+ VCP/Reconnect | PARTIAL | Code; HW NOT TESTED |
| D2 | OBD-DIAG Driver | FAIL/BLOCKED | Undocumented |
| S1 | Stripe Fixture E2E | PASS (Signatur) / BLOCKED Keys | |
| S2 | SMTP intern | PASS Stub / BLOCKED Prod | |
| P1 | PDF/MFA Härte | PASS | Regression |

**Ziel A:** NO-GO (Stripe Keys, SMTP Prod, Steuer)  
**Ziel B:** NO-GO (HW, OBD-DIAG, signed Installer)  
**Release:** **NO-GO**
