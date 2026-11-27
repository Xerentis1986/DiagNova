# Adapter-Capability-Matrix (Phase 05 + 19)

**Stand:** 2026-11-27 (Europe/Vienna)  
**API:** `GET /api/protocols/capability-matrix`  
**Connector:** `GET /capability-matrix`  
**LKW-Flags:** `GET /api/lkw/capabilities`

## Kernaussage

Capability beschreibt Code-/Simulationspfade – **nicht** Hardwarefreigabe.  
`hardware_tested` ist überall `false`. Nichts ist `freigegeben`.  
PKW-OBD-Adapter ≠ DoIP/CAN-FD/J1939/RP1210.

## Kurzmatrix

| Adapter | OBD-II | ISO-TP / OBD-CAN | UDS | DoIP | CAN-FD | J2534 | J1939 | RP1210 |
|---------|--------|------------------|-----|------|--------|-------|-------|--------|
| Simulator | simulated | simulated | partial | — | — | — | **nein** | **nein** |
| ELM327-OBD | code, untested HW | code, untested HW | partial | **nein** | **nein** | **nein** | **nein** | **nein** |
| Vgate vLinker | blocked | blocked | — | — | — | — | — | — |
| Delphi/Autocom | blocked | — | — | blocked | — | blocked | — | — |
| J2534 PassThru | planned | planned | planned | — | planned | planned | — | — |
| DoIP Ethernet | planned | — | planned | planned | — | — | **nein** | **nein** |
| RP1210 Commercial | **nein** | — | planned | **nein** | **nein** | **nein** | planned | planned |

## Quellen / Blocker

| ID | Bedeutung |
|----|-----------|
| BLK-HW | Keine verifizierte Diagnosehardware in der Umgebung |
| BLK-ADAPTER | Delphi/Autocom / Vgate-SPP undokumentiert |
| BLK-OEM | Keine lizenzierten OEM-Adressen für ABS/Airbag/Komfort |

Maschinenlesbar: `packages/diagnostic-protocols/src/diagnova_protocols/capability_matrix.py`.
