# Delphi/Autocom – GitHub-Recherche (Phase 21 Ergänzung)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Primärquelle:** https://github.com/smooker/obd (GPL-3.0)

## smooker/obd – Befund

| Thema | Ergebnis |
|-------|----------|
| Hardware | Autocom CDP+ / Delphi DS150E-Familie, FTDI + STM32 |
| USB-ID (untersuchte Variante) | **0403:D6DA** |
| Transport | FTDI Bulk (nicht klassisches Terminal); `ftdi_sio` erzeugt ttyUSB, Protokoll ist custom ASCII über Bulk |
| Framing | `*<cmd>[_args…]\r` → Antwort `*…\r` |
| Safe device queries | `*200` Serial, `*201` Firmware, `*203` Batterie, `*20A` Name (`CDP+`) |
| Gefährlich | `*668` CAN-Config (Relaisrisiko), `*606` periodische CAN-Slots, `*608`/`*609` ECU/CAN |
| Autor-Hinweis | Replay/Synthese gefährlich; falsch Init kann Dongle/ECU beschädigen |
| Lizenz | **GPL-3.0** – Code nicht in proprietäres DiagNova kopiert |

Docs: `HOWTO.md`, `ANALYSE.md`. Capture/Tools dienen der Analyse; DiagNova nutzt **Protokollfakten**, eigene C#-Implementierung.

## Weitere Repos

| Repo | Einschätzung | Lizenz |
|------|---------------|--------|
| delphi-ds150e/delphi-ds150e-diagnostic-software | Typisch Installer-/Spiegel-Material, keine klare Drittanbieter-API | unklar / nicht als SDK genutzt |
| erdesigns-eu/Delphi-OBD | Allgemeine OBD-Bibliothek (Delphi-Language), **nicht** DS150E-VCI-Treiber | NOASSERTION – nicht übernommen |

## Betreiber-Hardware

- Seriennummer beginnt mit **10** (konsistent mit Forschungsbeispiel `*100251`)
- Funktioniert mit SW **2017.R3** und **2020.23**; Wechsel erfordert Firmwareupdate
- DiagNova führt **kein** automatisches Firmwareupdate durch
- Originale Installer auf Dev-PC fehlen – für unabhängige Adapterentwicklung laut Auftrag nicht Voraussetzung

## Abgrenzung

- Offizielle Delphi-Diagnosesoftware ≠ freie Drittanbieter-API
- J2534-Abstraktion ≠ CDP+-Protokoll
- ELM327-Annahme für diesen Adapter: **nein**
