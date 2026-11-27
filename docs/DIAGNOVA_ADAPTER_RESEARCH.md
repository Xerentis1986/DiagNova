# DiagNova – Adapter-Recherche (Phase 21)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Methode:** Öffentliche Quellen + Codebestand. Kein Herstellerkontakt durch den Agenten. Keine Reverse-Engineering-Claims.

## Quellen

| Thema | URL / Hinweis |
|-------|----------------|
| moDiag unterstützte Interfaces | https://modiag.de/expert.htm – listet **OBD-DIAG 2055 / DIAMEX DX 25** (USB) |
| moDiag Ultimate | https://www.modiag.de/ultimate.htm |
| Delphi DS Hardware | https://www.delphiautoparts.com/en-gb/diagnostics-test-equipment/obd-diagnostics/ds-diagnostic-hardware |
| Delphi DS Software DE | https://www.delphiautoparts.com/de-de/test-equipment/obd-diagnose/… |
| CDP+ Protokollforschung | https://github.com/smooker/obd (GPL-3.0 – nur Fakten, kein Code-Copy) |
| ELM/STN Doku | https://www.obdlink.com/developers/ ; OBDLink FRPM PDF (ScanTool) |
| J2534 | Softing PassThru; scandoc.de SDK – Lizenz prüfen |

## Ergebnis Kurz

| Adapter | Dokumentierte Drittanbieter-API? | ELM annehmen? | Status in DiagNova |
|---------|----------------------------------|---------------|--------------------|
| OBD-DIAG 2055+ | **Nein** (nicht nachgewiesen) | **Nein** | `BlockedUndocumented` |
| Delphi/Autocom DS150E | Offizielle API **Nein**; CDP+-ASCII-Forschung ja | **Nein** | `PartiallySupported` (Safe-Reads sim; Live-HW offen) |
| ELM327/STN | Ja (AT/ST Doku) | nur bei Nachweis | `PartiallySupported` (HW ungetestet) |
| J2534 PassThru | Standard | n/a | `Planned` Abstraktion |

Siehe auch: `DIAGNOVA_DELPHI_GITHUB_RESEARCH.md`, `DIAGNOVA_DELPHI_LICENSE_REVIEW.md`.

## Protokollstandards (nur wo bekannt)

SAE J1979, ISO 15765-2/4, ISO 14230, ISO 9141-2, ISO 14229, ISO 13400, SAE J2534, SAE J1939 – Implementierung nur mit bekannten Abläufen; J1939 weiter Architektur (Phase 19).
