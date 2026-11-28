# Phase 23 – Betreiberhandlungen

1. PR # (Phase 23) reviewen; GitHub Actions Lauf prüfen (Windows Installer-Artefakt UNSIGNED).
2. Windows: Inno Setup 6 + `build-installer.ps1`; Code-Signing-Zertifikat beschaffen (BLK-CERT).
3. Connector: `CONNECTOR_TOKEN` setzen; Preferred COM für CDP+; HW-Labor nach Phase-22 Hardwareplan.
4. Stripe Test-Keys + Webhook Secret (keine Live-Charges).
5. SMTP Prod konfigurieren und echten Zustelltest.
6. Lizenz-HMAC Secret Prod setzen (`license_hmac_secret` / `DIAGNOVA_LICENSE_HMAC_SECRET`) – gleiches Secret API+Connector.
7. Steuer/Recht freigeben.
8. OBD-DIAG: Protokolldoku/Lizenz beschaffen – sonst Treiber weiter blockiert.
9. Prod-Deploy nur nach Freigabe; OEM Wordmark ohne Symbol-Icon beibehalten.
