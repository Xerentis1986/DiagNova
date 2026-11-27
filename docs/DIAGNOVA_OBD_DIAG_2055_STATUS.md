# OBD-DIAG 2055+ – Status (Phase 21)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Kompatibilitätsstatus:** `BlockedUndocumented`  
**hardware_tested:** false · **vehicle_tested:** false

## Recherche

1. moDiag: „OBD-DIAG 2055 / DIAMEX DX 25“ (USB). Variante **2055+** nicht laborverifiziert.
2. Öffentliche Entwickler-API / SDK: **nicht nachgewiesen**.
3. ELM327: **nicht angenommen**.
4. VID/PID: **unbekannt** – lokale Inventur nötig.

## Implementierung

| Baustein | Status |
|----------|--------|
| Katalogprofil `obd-diag-2055` | ja (blocked) |
| `ObdDiagAdapterService` + `/adapters/obd-diag/*` | Status + Probe-Guidance |
| Auto-Connect / Fake-Erfolg | **nein** |

## Offen

Physische Inventur → Protokollnachweis → erst dann Treiber.
