# OBD-DIAG 2055+ – Status (Phase 21)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Kompatibilitätsstatus:** `BlockedUndocumented`  
**hardware_tested:** false · **vehicle_tested:** false

## Recherche

1. **Bezeichnung:** In öffentlicher moDiag-Doku „OBD-DIAG 2055 / DIAMEX DX 25“ (USB). Variante „2055+“ im Auftrag – **exakte HW/Firmware dieser Einheit hier nicht inventarisiert** (keine physische Hardware in der Cloud-Umgebung).
2. **Hersteller:** OBD-DIAG / DIAMEX (laut Drittanbieter-Softwareliste) – nicht durch Hersteller-API bestätigt.
3. **USB VID/PID:** **unbekannt** – erfordert lokales Windows-Inventar (`GET /hardware/inventory` am Connector).
4. **Geräte-Manager / Treiber / COM:** ausstehend (lokale Inventur).
5. **Öffentliche Entwickler-API:** **nicht nachgewiesen**.
6. **SDK:** keines gefunden.
7. **Serielle Befehlsschnittstelle:** unbekannt – **ELM327-Kompatibilität wird nicht angenommen**.
8. **Kommerzielle Nutzbarkeit:** ohne Herstellerfreigabe **nicht** gegeben.

## Implementierung

| Datei | Inhalt |
|-------|--------|
| `Adapters/AdapterCompatibility.cs` | Profil `obd-diag-2055` |
| `Adapters/AdapterRegistry.cs` | Auswahl blockiert; AutoDetect nur Hinweis |
| `Adapters/HardwareInventoryProbe.cs` | Read-only Inventur + Hersteller-Anfrageentwurf |
| `GET /hardware/inventory` | Lokale Geräteinfos ohne Fahrzeugbefehle |

## Tests

- Unit: Auswahl blockiert, kein Fake-Erfolg (`Phase21AdapterRegistryTests`)
- Kein Hardware-/Fahrzeugtest durchgeführt

## Offen

- Physische Geräteinventur (VID/PID, COM, Treiber)
- Herstellerantwort auf API/Lizenz
- Erst dann spezifischer Treiber – sonst weiterhin blocked
