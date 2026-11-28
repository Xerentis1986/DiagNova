# Phase 24 – Installer Evidence

## Artefakt (verifiziert)

| Feld | Wert |
|------|------|
| Dateiname | DiagNovaConnectorSetup-0.23.0-unsigned.exe |
| Größe | 32 294 999 Bytes |
| SHA-256 | b6c4bcb53938ca4f3d2e6c409f2633225a7df41a2296ca6887d957148024f0a9 |
| Signing | UNSIGNED |
| CI Run | https://github.com/Xerentis1986/DiagNova/actions/runs/46088694592 |
| Lokal | `/opt/cursor/artifacts/DiagNovaConnectorSetup-0.23.0-unsigned.exe` |

## Build-Kette
Inno Setup 6 + `scripts/build-installer.ps1` auf windows-latest.  
Nächste Builds: Version **0.24.0** im `.iss` / csproj; SHA wird in CI mitgeschrieben.

## Install/Uninstall
- Windows Inno Install/Uninstall/Upgrade: **NOT TESTED** auf diesem Linux-Agent
- Portable Install-E2E (Linux publish→Start→API→Stop→Remove): **PASS**

OEM Logos + Wordmark ohne Symbol-Icon: unverändert.
