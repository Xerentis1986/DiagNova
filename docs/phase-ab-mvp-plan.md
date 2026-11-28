# DiagNova Phase A + B MVP – Umsetzungsplan

## Ziel
Lokal startbares Monorepo: React-Web, FastAPI, PostgreSQL, Docker Compose, Werkstatt-Dashboard, Fahrzeugauswahl, **simulierter** OBD-Diagnose-Flow, Berichte, Windows-Connector-Skelett (ohne Fahrzeugbefehle).

## Lieferumfang

| Bereich | Inhalt |
|---------|--------|
| Auth | Demo-Login, bcrypt-Hashes, JWT, Rollen (admin/technician) |
| Dashboard | Aktives Fahrzeug, Simulator-Status, letzte Sitzungen, Schnellzugriff |
| Fahrzeuge | Seed: VW, Audi, BMW, Mercedes-Benz, Škoda, Seat, Opel, Ford, Toyota |
| Diagnose | DTCs stored/pending, Live-PIDs, Freeze-Frame, Readiness, VIN (alles simuliert) |
| Berichte | Speichern, CSV- und PDF-Export |
| Navigation | Geplante Module als „Geplant“ markiert |
| Connector | .NET 8 Skelett + `IDiagnosticAdapter` + Stub |
| Infra | Docker Compose (api, web, postgres), Alembic, Seeds, Tests, README |

## Nicht enthalten
Echte OBD-Kommunikation, proprietäre Protokolle, DPF-Deaktivierung, Hersteller-Servicefunktionen.

## Kennzeichnung
Alle Simulator-Antworten tragen `data_source: "simulated"`. UI zeigt Banner „Simulierte Daten“.
