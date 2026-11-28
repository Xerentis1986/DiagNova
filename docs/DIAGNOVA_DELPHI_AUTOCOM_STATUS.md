# Delphi / Autocom – Status (Phase 21 Ergänzung)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Kompatibilitätsstatus:** `PartiallySupported` (nur Geräte-Lese-Pfad / Simulator)  
**hardware_tested:** false · **vehicle_tested:** false

## Recherche (GitHub)

Primärquelle [smooker/obd](https://github.com/smooker/obd) (GPL-3.0): FTDI **0403:D6DA**, ASCII `*cmd_\r`, Safe-Reads `*200`/`*201`/`*203`/`*20A`.  
Details: `DIAGNOVA_DELPHI_GITHUB_RESEARCH.md`, Protokoll: `DIAGNOVA_DELPHI_PROTOCOL_SPEC.md`, Lizenzen: `DIAGNOVA_DELPHI_LICENSE_REVIEW.md`.

## Betreiber-Hardware

- Seriennummer beginnt mit **10**
- SW **2017.R3** / **2020.23** – Wechsel erfordert Firmwareupdate (DiagNova flasht **nicht**)
- Originale Installer auf Dev-PC fehlen – für unabhängige Entwicklung nicht Voraussetzung

## Implementierung (eigenständig, kein GPL-Copy)

| Baustein | Status |
|----------|--------|
| `Adapters/DelphiCdp/*` ASCII-Codec + Session | ja (Unit-Tests) |
| Fake-Transport / Simulator-Identität | ja |
| FTDI-Transport-Abstraktion | ja (ehrlicher Fail ohne D2XX/HW) |
| Kompatibilitätsmatrix | ja |
| Connector API `/adapters/delphi-cdp/*` | ja |
| `DiagNova.CdpProbe` | ja |
| Live-HW / CAN / Relais / Flash | **gesperrt** |

## Offen (Labor)

- VID/PID und Treiber am realen Adapter
- Live `*200`/`*201` gegen Serienpräfix 10
- Firmware-Mapping zu Host-SW – siehe `DIAGNOVA_DELPHI_HARDWARE_TEST.md`

## Rechtliches

GPL-3.0-Code aus smooker/obd **nicht** in die proprietäre Codebasis übernommen. Proprietäre Delphi-DLLs/Firmware **nicht** eingebunden.
