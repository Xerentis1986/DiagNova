# Automotive-Quellenkatalog – Technische Evidenz

**Branch:** `cursor/diagnova-automotive-catalog-9616`  
**Basis:** PR #36 Tip `0c66a83`  
**Stand:** 2026-11-28 (Europe/Vienna)

## Geliefert
- Katalog JSON (447 Quellen) in `apps/api/app/data/automotive_quellenkatalog.json` + `docs/`
- Redigierter Masterprompt ohne Passwort: `docs/Cursor_Masterprompt_Automotive_Gesamtliste.md`
- API `/api/automotive-catalog/summary|sources|probe|fixtures/*`
- UI `/automotive-catalog`
- Fixture-Import OBDex Sample 200 DTCs + 12 SAE-Mode-01-PIDs (`write_enabled` faktisch aus)
- Skript `scripts/automotive_catalog_probe_and_import.py` (Voll-OBDex → `.cache/`, nicht Git)

## Live-Probe (Priorität, diese Umgebung)
| ID | Quelle | HTTP |
|---|---|---|
| M0268 | OBDex generic.min.json | 200 (~31 MB) |
| M0266 | OBDb Prius signalset | 200 |
| M0267 | OBDb Focus signalset | 200 |
| M0269 | Wal33D dtc_codes.db | 200 |
| M0265 | python-obd Command Tables | 200 |
| M0077 | OpenDBC GitHub | 200 |

## Blockaden (ehrlich)
- OEM-RMI / SERMI / Secure Gateway: Auth/Portal
- MechanicDB/ALLDATA/Autodata: kostenpflichtig – **keine Bestellung**
- Firmware/Flash / Schreibdiagnose: **gesperrt**
- OBDb BY-SA: Attribution-Pipeline – v1 nur Metadaten, kein Bulk-Redistrib
- Keine vollständige Herstellerabdeckung behauptet

## GO
Pilot-Datenpfade nutzbar; **kommerzielles Voll-GO unverändert NO-GO**.
