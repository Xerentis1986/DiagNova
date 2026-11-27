# LKW / Nutzfahrzeug – Architektur (Phase 19)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Status:** `documented_prep` / Architektur only – **keine** Diagnose-Freigabe  
**API:** `GET /api/lkw/architecture`, `/brands`, `/capabilities`  
**UI:** `/lkw` (Badge „Geplant“)

## Kernaussage

Phase 19 bereitet J1939/RP1210 und Nutzfahrzeug-Marken vor.  
Es gibt **keinen** laufenden J1939-Parser, **keine** SPN/FMI-Auswertung, **keine** RP1210-DLL-Bindung und **keinen** LKW-Simulator mit Fake-Werten.  
Diagnose-Endpunkte (`POST /api/lkw/diagnose`, `/j1939/read`, `/rp1210/connect`) antworten mit **403**.

## Schichtentrennung

| Schicht | Geplant | Abgrenzung |
|---------|---------|------------|
| Transport | RP1210, ggf. J2534/DoIP wo belegt | 24-V-Hardware; PKW-ELM ≠ RP1210 |
| Protokoll | SAE J1939, optional J1708/J1587, UDS wo dokumentiert | Kein Stack ohne Spec-Beleg |
| Adapter | `rp1210-commercial` in Capability-Matrix (`planned`) | `hardware_tested=false` |
| Fahrzeugdefinition | Markennavigation (MAN, MB Trucks, Scania, Volvo Trucks, DAF, Iveco, Renault Trucks) | Keine OEM-ECU-Adressen |

## Capability-Flags

Maschinenlesbar: `GET /api/lkw/capabilities` und `packages/.../capability_matrix.py` (Adapter `rp1210-commercial`).  
Alle LKW-Flags: `enabled=false`, Status `planned` oder `unavailable`.

## Tarife / Entitlements

- `vehicle.lkw` – nicht freigegeben  
- Pläne `lkw_planned`, `kombi_planned` – nicht buchbar (Phase 13)

## Blocker

| ID | Bedeutung |
|----|-----------|
| BLK-HW | Keine 24-V/RP1210-Hardware verifiziert |
| BLK-OEM | Keine lizenzierten LKW-OEM-/Service-Daten |
| BLK-ADAPTER | Keine Vendor-RP1210-DLL im Repo |

## Abgrenzung zu PKW

| PKW (heute) | LKW (Phase 19) |
|-------------|----------------|
| OBD-II/ELM Simulator | kein Fake-LKW-Simulator |
| ISO-TP/UDS Parser-Tests | J1939 nur Docs/Flags |
| 12-V-Annahme üblich | 24 V typisch, nicht unterstellen |

Siehe auch: [j2534-doip-j1939-prep.md](./j2534-doip-j1939-prep.md), [adapter-capability-matrix.md](./adapter-capability-matrix.md).
