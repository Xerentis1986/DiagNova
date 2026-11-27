# Delphi/Autocom CDP+ – Treiberstatus (DiagNova)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Kompatibilität:** `PartiallySupported` (nur Geräte-Lese-Pfad / Simulator)  
**hardware_tested:** false · **vehicle_tested:** false

## Implementiert

| Komponente | Pfad | Status |
|------------|------|--------|
| ASCII-Codec | `DelphiCdp/CdpProtocol.cs` | Unit-getestet |
| Safe Session | `DelphiCdp/CdpSession.cs` | Allowlist *200/201/203/20A |
| Fake-Transport | `FakeCdpTransport` | Simulator |
| FTDI-Abstraktion | `FtdiCdpTransport` | ehrlicher Fail ohne D2XX/HW |
| Compatibility Matrix | `CdpCompatibility.cs` | inkl. SW 2017/2020 Hinweis |
| Connector API | `/adapters/delphi-cdp/*` | status, identify-sim, open-live→fail, vehicle→403 |
| Probe-Tool | `DiagNova.CdpProbe` | Inventur + Sim-Identität |

## Nicht implementiert / gesperrt

- Live Bulk-Open mit echter Hardware
- CAN-Config / Relais / TesterPresent / ECU-Reads
- Automatisches Firmwareupdate
- Bluetooth-CDP-Pfad
- Übernahme GPL-Code oder proprietärer Delphi-DLLs

## Nächste Laborschritte

1. Windows: VID/PID 0403:D6DA bestätigen  
2. `*200`/`*201` live gegen Adapter (Serienpräfix 10)  
3. Firmware zu Host-SW 2017.R3 / 2020.23 dokumentieren (manuell)  
4. Erst danach Freigabeentscheidung für weitere Befehle  
