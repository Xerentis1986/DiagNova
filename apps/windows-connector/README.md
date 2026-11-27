# DiagNova Windows Connector (Phase 04)

.NET 8 lokale Connector-Anwendung: Geräteerkennung, COM/USB/Bluetooth-Inventar, sichere Browser-Kopplung, serieller Transport inkl. Fake-Port, ELM327-Init und **OBD-II/EOBD** (Allowlist).

## Wichtig

- OBD nur über Allowlist (`ObdSession`) – keine freien Remote-Rohbefehle.
- Mode 04 Clear nur mit Freigabe (`ClearDtcGate`); permanente DTCs nicht löschbar.
- `data_source`: `simulated` (Fake/Simulator) vs. `live` (System-COM) – strikt getrennt.
- **Keine Hardwarefreigabe** in dieser Umgebung – Parser/Simulator-Tests.
- Delphi/Autocom: **nicht** angebunden – siehe `docs/delphi-autocom-interface.md`.
- Vgate: SPP ungeprüft – siehe `docs/vgate-elm327-prep.md`.
- Auth: Pairing + Bearer, nur Loopback – `docs/windows-connector-auth.md`.

## Build & Test

```powershell
cd apps\windows-connector
dotnet restore
dotnet build
dotnet test
dotnet run --project DiagNova.Connector
```

## API (Auszug, alle außer `/pair*` mit Bearer)

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | `/pair/info` | Pairing-Metadaten + Code (nur Loopback) |
| POST | `/pair` | Session-Token |
| GET | `/health` | Lebenszeichen (phase=4) |
| GET | `/status` | Adapter- vs. Fahrzeugstatus getrennt |
| GET | `/devices` | Gesamtinventar |
| GET | `/log` | Diagnoseprotokoll |
| POST | `/adapter/simulator` | Simulator-Pfad |
| POST | `/adapter/connect/fake` | Fake-Port |
| POST | `/adapter/connect/com` | COM (live wenn `transport=system`) |
| POST | `/obd/init` | Adapter-Init + Protokollerkennung |
| GET | `/obd/live` | Live-PIDs |
| GET | `/obd/dtcs` | stored/pending/permanent |
| GET | `/obd/freeze-frame` | Freeze-Frame |
| GET | `/obd/readiness` | Readiness |
| GET | `/obd/vin` | VIN Mode 09 |
| GET | `/obd/clear/warnings` | Clear-Warnungen |
| POST | `/obd/clear/approve` | Freigabe-Token |
| POST | `/obd/dtc/clear` | Mode 04 (Token erforderlich) |
| GET | `/capabilities` | Feature-/Blocker-Liste |
