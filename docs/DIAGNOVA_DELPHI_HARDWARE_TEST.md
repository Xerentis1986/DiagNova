# Delphi/Autocom – Hardwaretest-Checkliste

**Stand:** 2026-11-27 (Europe/Vienna)  
**Laborstatus:** **nicht ausgeführt** in der Cloud-Agent-Umgebung

## Vorbereitung (Windows-PC mit Adapter)

1. Adapter anschließen (USB).
2. Geräte-Manager / USBDeview: VID **0403**, PID **D6DA** (oder abweichende Clone-ID notieren).
3. Treibername (FTDI VCP / D2XX) notieren – CDP-Protokoll ist **kein** ELM-AT-Strom.
4. Probe starten:

```powershell
cd apps\windows-connector
dotnet run --project DiagNova.CdpProbe
```

5. Optional Connector: `POST /adapters/delphi-cdp/identify-sim` (ohne HW) vs. später Live.

## Mit Adapter prüfen (nach Laborfreigabe)

| Schritt | Erwartung | Ergebnis |
|---------|-----------|----------|
| Inventur VID/PID | 0403:D6DA oder dokumentierte Abweichung | offen |
| `*200` Serial | beginnt mit 10 (Betreiber) | offen |
| `*201` Firmware | Wert dokumentieren; passt zu 2017/2020 | offen |
| `*203` Spannung | plausibel mit/ohne Fahrzeug | offen |
| `*20A` Name | z. B. CDP+ | offen |
| CAN/`*668` | **nicht** ohne Freigabe | gesperrt |

## Explizit verboten ohne Freigabe

- Firmware flashen / Auto-Update
- Relais-/Pin-Umschaltung
- Ungeprüfte CAN-Init-Sequenzen am Fahrzeug
- Behauptung „Fahrzeugdiagnose erfolgreich“ ohne Nachweis

## Was erst mit realem Adapter verifiziert werden kann

- Ob die untersuchte USB-ID exakt zutrifft
- Ob Framing über VCP oder nur Bulk funktioniert
- Firmware-String-Mapping zu 2017.R3 / 2020.23
- Clone vs. Originalverhalten
- Alle nicht-Allowlist-Befehle
