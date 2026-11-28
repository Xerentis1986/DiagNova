# Phase 23 – Installer Evidence

## Lieferumfang
- `apps/windows-connector/installer/DiagNovaConnector.iss` (Inno Setup 6)
- `apps/windows-connector/scripts/build-installer.ps1`
- `apps/windows-connector/scripts/publish-win-x64.ps1` (schreibt `INSTALLER_NOTE.txt`)
- CI Job `connector-installer-windows` (windows-latest, choco innosetup)

## Eigenschaften
- Startmenü, Uninstall, Version 0.23.0, SetupLogging
- Output: `DiagNovaConnectorSetup-0.23.0-unsigned.exe`
- **Kein SignTool** – klar UNSIGNED / BLK-CERT

## Testergebnis lokal (Linux-Agent)
- Inno/ISCC nicht verfügbar → Build **NOT TESTED** hier
- Projekt + Skripte vorhanden (PASS als Implementierung)

## OEM
OEM-Logos + Wordmark ohne Symbol-Icon unverändert belassen.
