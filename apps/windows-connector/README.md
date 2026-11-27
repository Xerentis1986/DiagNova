# DiagNova Windows Connector (Phase 03)

.NET 8 lokale Connector-Anwendung: Geräteerkennung, COM/USB/Bluetooth-Inventar, sichere Browser-Kopplung, serieller Transport inkl. Fake-Port, ELM327-AT-Vorbereitung.

## Wichtig

- **Keine** echten Fahrzeug-/OBD-Befehle in Phase 03.
- Simulator ist ein **separater** Pfad (`POST /adapter/simulator`).
- Delphi/Autocom: **nicht** angebunden – siehe `docs/delphi-autocom-interface.md`.
- Vgate: nur Vorbereitung – siehe `docs/vgate-elm327-prep.md`.
- Auth: Pairing + Bearer, nur Loopback – `docs/windows-connector-auth.md`.

## Build & Test

```powershell
cd apps\windows-connector
dotnet restore
dotnet build
dotnet test
dotnet run --project DiagNova.Connector
```

Linux/CI (mit .NET 8 SDK):

```bash
cd apps/windows-connector
dotnet test
```

## API (Auszug, alle außer `/pair*` mit Bearer)

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | `/pair/info` | Pairing-Metadaten + Code (nur Loopback) |
| POST | `/pair` | Session-Token |
| GET | `/health` | Lebenszeichen |
| GET | `/status` | Adapter- vs. Fahrzeugstatus getrennt |
| GET | `/devices` | Gesamtinventar |
| GET | `/devices/com\|usb\|bluetooth` | Teilinventare |
| GET | `/log` | Diagnoseprotokoll (Transport/Status) |
| GET | `/capabilities` | Feature-/Blocker-Übersicht |
| POST | `/adapter/simulator` | Simulator wählen |
| POST | `/adapter/connect/fake` | Fake-Port + AT-Init |
| POST | `/adapter/connect/com` | COM öffnen (kein OBD) |
| POST | `/adapter/disconnect` | Trennen |

## Struktur

```
DiagNova.Connector/
  Auth/          Pairing, Origin, LocalAuth
  Discovery/     COM, USB, Bluetooth, Composite
  Transport/     ISerialTransport, System, Fake
  Adapters/      Manager, Simulator, Stub, ELM327-Prep
  Logging/       DiagnosticProtocolLog
DiagNova.Connector.Tests/
```
