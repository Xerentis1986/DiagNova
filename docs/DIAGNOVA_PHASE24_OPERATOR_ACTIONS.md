# Phase 24 – Betreiberhandlungen

1. UNSIGNED EXE prüfen: SHA-256 gegen `docs/artifacts/INSTALLER_SHA256SUMS.txt`
2. Windows: Install/Uninstall/Upgrade manuell; Code-Signing (BLK-CERT)
3. Prod RSA-Keys setzen (`DIAGNOVA_LICENSE_RSA_PRIVATE_PEM` nur Backend; Public im Connector)
4. Demo-Private-Key deaktivieren (`DIAGNOVA_LICENSE_ALLOW_DEMO_PRIVATE=0`)
5. Stripe Test-Keys / SMTP / Steuerfreigabe / HW-Labor
6. OBD-DIAG Protokolldoku beschaffen
7. Prod-Deploy nur nach Freigabe; OEM Wordmark ohne Symbol behalten
