# Phase 22 – Hardwaretest-Plan

Auszuführen auf Windows mit physischem Adapter. Keine erfundenen PASS.

## Vorbereitung
1. `dotnet` 8 SDK; `scripts/publish-win-x64.ps1`
2. Connector starten (Port 8765), Bearer falls konfiguriert
3. API `CONNECTOR_BASE_URL=http://127.0.0.1:8765`, `DIAGNOVA_DIAG_MODE=live`

## Fälle
| # | Schritt | Erwartung | Ergebnis (leer) |
|---|---------|-----------|-----------------|
| H1 | Bridge Status | reachable=true | |
| H2 | LIVE Connect | Session ohne Simulator-Felder | |
| H3 | VIN/DTCs/Live | Echte Adapterwerte | |
| H4 | CDP+ VID 0403:D6DA + COM | Open OK; `*200` SN Prefix 10 | |
| H5 | Firmware Query only | Version gelesen; kein Flash | |
| H6 | OBD-DIAG inventory-probe | VID/PID/COM Inventur; kein ELM | |
| H7 | License Gate off | Live-OBD → 402 | |
| H8 | License Gate apply | Live-OBD erlaubt | |
| H9 | DEMO Umschalter | Explizit Simulator; Label DEMO | |

Bei Fail: Log + Screenshot; Status NOT TESTED belassen bis belegt.
