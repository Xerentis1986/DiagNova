# Windows-Connector – Status

**Stand:** 2026-11-27 (Europe/Vienna)  
**Version:** siehe `ConnectorVersion` im Projekt  
**Loopback:** `http://127.0.0.1:8765`

## Funktionen

- Pairing / Origin-Guard / lokale Auth
- Geräteinventur COM/USB/BT (read-only)
- Multi-Adapter-Auswahl inkl. CDP+ Safe-Reads und OBD-DIAG blocked
- OBD-II Init/Live/DTC/VIN über Fake oder COM
- Updates Busy-Gate, kein ungeprüftes Auto-Install
- Firmware-Import mit Hash – Flash 403

## Build / Installer

- `dotnet build` / `dotnet test` (net8.0)
- Installer-Hinweise: `docs/connector-installer.md`
- Reproduzierbarer Release-Build: lokal Windows + Code-Signing vorbereiten (BLK-CERT)

## Offen

- Live FTDI/D2XX-Bindung am realen CDP+
- OBD-DIAG Protokoll nach Inventur
- MSI/Setup mit Signatur
