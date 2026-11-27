# Delphi/Autocom – Lizenzreview (Phase 21)

**Stand:** 2026-11-27 (Europe/Vienna)

## smooker/obd

| Feld | Wert |
|------|------|
| Lizenz | **GPL-3.0** |
| Risiko | Copyleft – Integration in proprietäre DiagNova-Codebasis ohne GPL-Compliance **unzulässig** |
| DiagNova-Vorgehen | **Kein** Quellcode übernommen. Eigene C#-Implementierung auf Basis dokumentierter Protokollbeobachtungen (Framing/Befehlscodes als Fakten). |
| Zitat/Quellenangabe | HOWTO.md / ANALYSE.md verlinkt in Docs und API-Status |

## delphi-ds150e/…

| Feld | Wert |
|------|------|
| Nutzung | Nicht als SDK eingebunden |
| Grund | Unklare Rechte; typisch keine freigegebene Drittanbieter-API |

## erdesigns-eu/Delphi-OBD

| Feld | Wert |
|------|------|
| Lizenz | GitHub: NOASSERTION / Other |
| Inhalt | Embarcadero-Delphi OBD-Bibliothek, nicht CDP+/DS150E-VCI |
| Nutzung | **Nicht** übernommen |

## Proprietäre Delphi-/Autocom-Software

- Installer/DLL/Datenbanken: **nicht** einbinden ohne Lizenz
- Kein Umgehen von Lizenzschutz
- Firmware-Dateien aus Dritt-Repos: **nicht** redistributieren

## Fazit

Rechtlich tragfähiger Pfad: eigenständige Protokollimplementierung + Laborverifikation. GPL-Tools dürfen ggf. **separat** zur Analyse genutzt werden, nicht in die DiagNova-Binary gelinkt.
