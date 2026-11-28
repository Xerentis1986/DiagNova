# Standard-OBD-II – Status

**hardware_tested:** false · **vehicle_tested:** false

## Implementiert

- Allowlist ELM-Befehle, Parser, PID-Skalierung
- Init, VIN, DTCs (stored/pending), Freeze-Frame, Readiness, Live-PIDs
- Clear-DTC nur mit Freigabe-Gate
- Simulator klar getrennt (`data_source=simulated`)

## Live-Modus

- COM-Connect vorhanden
- Keine simulierten Werte im Live-Pfad – fehlende Antworten = Fehler/leer
- Ohne physischen Adapter: nicht hardwaregetestet

## PDF / Historie

- Über Web/API-Berichte angebunden (Phase 10) – Snapshot aus Connector-Antworten
