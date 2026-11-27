# DiagNova – Fortschritt

Dauerhafte Fortschrittsdatei (Repo-Root). Nach jeder Phase aktualisieren.

## Meta

| Feld | Wert |
|------|------|
| Produkt | DiagNova – webbasierte Mehrmarken-Fahrzeugdiagnose |
| Repo | https://github.com/Xerentis1986/DiagNova |
| MVP-Branch / PR | `cursor/diagnova-phase-ab-mvp-bf17` / PR #1 @ `6adfcc4` |
| Phase-00-Branch | `cursor/diagnova-phase-00-inventory-c287` |
| Phase-02-Branch | `cursor/diagnova-phase-02-brands-c4de` |
| Phase-03-Branch | `cursor/diagnova-phase-03-connector-90c7` |
| Phase-04-Branch | `cursor/diagnova-phase-04-obd-606d` |
| Phase-05-Branch | `cursor/diagnova-phase-05-multiprotocol-dd50` |
| Phase-06-Branch | `cursor/diagnova-phase-06-database-80ce` |
| Phase-07-Branch | `cursor/diagnova-phase-07-updates-4111` |
| Phase-08-Branch | `cursor/diagnova-phase-08-workshop-d09b` |
| Phase-09-Branch | `cursor/diagnova-phase-09-history-f3fe` |
| Letzte Aktualisierung | 2026-11-27 (Europe/Vienna) |

## Ampel

| Phase | Ampel | Kurzstatus |
|-------|-------|------------|
| 00 Bestandsaufnahme | 🟢 Docs | Matrix/Baseline auf Feature-Branch |
| 01 MVP Basis | 🟢 Simuliert | PR #1 – nicht erneut entwickeln |
| 02 Marken-Kacheln | 🟢 Simuliert getestet | Katalog, Theme, Wizard, E2E |
| 03 Windows-Connector | 🟢 Simuliert getestet | Discovery/Auth/Fake-Port |
| 04 OBD-II/EOBD | 🟢 Simuliert getestet | Parser/Allowlist/Clear-Gate – **keine HW-Freigabe** |
| 05 Multiprotokoll / Mehr-ECU | 🟢 Simuliert getestet | Schichten/Matrix/ISO-TP/UDS |
| 06 Diagnosedatenbank | 🟢 Simuliert getestet | Modell/Import/Quarantäne; DTC unbekannt |
| 07 Auto-Daten-Updates | 🟢 Simuliert getestet | Kanäle/SSRF/Signatur/Staging/Freigabe |
| 08 Werkstatt/Kunden | 🟢 Simuliert getestet | Mandant/Rollen/CRUD/DSGVO |
| 09 Fahrzeugakte/Historie | 🟢 Simuliert getestet | Zeitstrahl/Vergleich/Messwerte; **Phase 10 nicht gestartet** |
| 10–15 | ⚪ Offen | |
| 16 Deploy-Vorbereitung | 🟡 Parallel | World4You/Plesk außerhalb; kein Prod |
| 17 Abnahme | ⚪ Offen | |
| 18–19 Optional | ⚪ Später | J1939 in 19 |

## Chronik

### 2026-11-27 – Phase 09 Fahrzeug-History und digitale Fahrzeugakte

**Erledigt**

- Branch von `origin/cursor/diagnova-phase-08-workshop-d09b` (PR #13)
- Alembic `006_phase09` + Sitzungsdetails/ECU/DTC/Messwerte/Notizen
- Lookup VIN/Kennzeichen, Zeitstrahl, Abort, Idempotenz, DTC-Vergleich
- UI `/vehicle-record`; Demo/Beispiel/Simulation gekennzeichnet
- Tests: pytest **78 passed**

**Nicht gemacht (bewusst)**

- Keine echten Historien als echt; keine Hardware-Daten
- **Phase 10 nicht gestartet**
- Kein Prod-Deploy

**Nächster Schritt:** Coordinator orchestriert Phase 10.

### 2026-11-27 – Phase 08 Werkstatt- und Kundenverwaltung

Details: `docs/phase-08-abschluss.md`.

### 2026-11-27 – Phase 07 Automatische Diagnosedaten-Updates

Details: `docs/phase-07-abschluss.md`.

### 2026-11-27 – Phase 06 Diagnosedatenbank und Datenimporte

Details: `docs/phase-06-abschluss.md`.

### 2026-11-27 – Phase 05 Multiprotokoll und Mehrsteuergerätediagnose

Details: `docs/phase-05-abschluss.md`.

### 2026-11-27 – Phase 04 Echte OBD-II/EOBD-Diagnose

Details: `docs/phase-04-abschluss.md`.

### 2026-11-27 – Phase 03 Windows-Connector und Bluetooth

Details: `docs/phase-03-abschluss.md`.

### 2026-11-27 – Phase 02 Marken-Kacheln und Fahrzeugauswahl

Details: `docs/phase-02-abschluss.md`.

### 2026-11-27 – Phase 00 Bestandsaufnahme

Inventar, Anforderungsmatrix, Baseline-Tests. Details: `docs/phase-status.md`.

### Früher – Phase 01 / A+B MVP (PR #1)

Simuliertes Monorepo. Details: `docs/phase-ab-mvp-plan.md`.

## Verweise

- Matrix: [docs/requirements.md](docs/requirements.md)
- Fähigkeiten: [docs/capabilities.md](docs/capabilities.md)
- Phasenstatus: [docs/phase-status.md](docs/phase-status.md)
- Phase-09-Abschluss: [docs/phase-09-abschluss.md](docs/phase-09-abschluss.md)
- Phase-08-Abschluss: [docs/phase-08-abschluss.md](docs/phase-08-abschluss.md)
- Phase-07-Abschluss: [docs/phase-07-abschluss.md](docs/phase-07-abschluss.md)
- Phase-06-Abschluss: [docs/phase-06-abschluss.md](docs/phase-06-abschluss.md)
- Freie Quellen: [docs/free-data-sources.md](docs/free-data-sources.md)
