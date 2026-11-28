# Vgate / ELM327 – Treiber-Vorbereitung (Phase 03)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Status:** **Vorbereitung implementiert**, Hardware **nicht** freigegeben

## Vgate vLinker MC+

| Punkt | Befund |
|-------|--------|
| Konkrete Windows-SPP-Variante | **Nicht verifiziert** |
| Herstellerdokumentation | **Nicht** im Repo |
| Konsequenz | Status `blocked` unter Capabilities; kein automatischer SPP-Connect |

## ELM327-Treiber-Vorbereitung

Implementiert in `apps/windows-connector`:

- `Elm327DriverPrep` – nur sichere AT-Init-Sequenz: `ATZ`, `ATE0`, `ATL0`, `ATH0`, `ATI`
- Transport über `ISerialTransport` (System oder Fake)
- OBD-Service-Requests (`0100`, `03`, `04`, …) werden **blockiert** (`IsVehicleObdCommand`)
- Fake-Port-Tests decken AT-Init und Blockade ab

## Nächste Schritte (nicht Phase 03)

- Herstellerdokumentation / SPP-Variante prüfen
- Echte Adapter-Init + Protokollerkennung → **Phase 04**
- Keine Fahrzeugbefehle ohne Allowlist und Freigabe
