# DiagNova Connector – Treiber-/Adapter-Matrix (Phase 21)

**Stand:** 2026-11-27 (Europe/Vienna)  
**API:** `/adapters`, `/adapters/auto-detect`, `/adapters/connection-test`, `/hardware/inventory`, `/j2534/status`

## Matrix

| Adapter-ID | Status | Treiber | Schnittstelle | HW-Test | Fahrzeugtest | Bemerkung |
|------------|--------|---------|---------------|---------|--------------|-----------|
| simulator | TechnicallyIntegrated | built-in | Fake/Sim | nein | nein | simuliert getestet |
| elm327-stn | PartiallySupported | ELM AT/ST Prep | COM/Fake | nein | nein | nur nachweislich kompatible HW |
| obd-diag-2055 | BlockedUndocumented | — | unbekannt | nein | nein | keine freie API |
| delphi-autocom | ManufacturerApprovalRequired | — | unbekannt | nein | nein | keine Drittanbieter-API |
| j2534-passthru | Planned | — | PassThru DLL | nein | nein | Abstraktion, keine DLL geladen |
| vgate-vlinker | blocked (alt) | — | SPP ungeprüft | nein | nein | BLK-ADAPTER |

## Architektur

- Automatische Erkennung → nur **Kandidaten**
- Manuelle Auswahl mit Statusprüfung
- Adapterprofile + Capabilities + Logging
- Gerätewechsel über `/adapters/select`
- Verbindungstest ohne Fake-Erfolg für blocked Adapter

## Dateien

- `Adapters/AdapterCompatibility.cs`, `AdapterRegistry.cs`
- `Adapters/J2534PassThruAbstraction.cs`, `HardwareInventoryProbe.cs`
- `Program.cs` Endpunkte Phase 21
