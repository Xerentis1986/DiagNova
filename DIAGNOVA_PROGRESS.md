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
| Letzte Aktualisierung | 2026-11-27 (Europe/Vienna) |

## Ampel

| Phase | Ampel | Kurzstatus |
|-------|-------|------------|
| 00 Bestandsaufnahme | 🟢 Docs | Matrix/Baseline auf Feature-Branch |
| 01 MVP Basis | 🟢 Simuliert | PR #1 – nicht erneut entwickeln |
| 02 Marken-Kacheln | 🟢 Simuliert getestet | Katalog, Theme, Wizard, E2E |
| 03 Windows-Connector | 🟢 Simuliert getestet | Discovery/Auth/Fake-Port |
| 04 OBD-II/EOBD | 🟢 Simuliert getestet | Parser/Allowlist/Clear-Gate – **keine HW-Freigabe** |
| 05 Multiprotokoll / Mehr-ECU | 🟢 Simuliert getestet | Schichten/Matrix/ISO-TP/UDS; OEM unavailable; **Phase 06 nicht gestartet** |
| 06–15 | ⚪ Offen | |
| 16 Deploy-Vorbereitung | 🟡 Parallel | World4You/Plesk außerhalb; kein Prod |
| 17 Abnahme | ⚪ Offen | |
| 18–19 Optional | ⚪ Später | J1939 in 19 |

## Chronik

### 2026-11-27 – Phase 05 Multiprotokoll und Mehrsteuergerätediagnose

**Erledigt**

- Branch von `origin/cursor/diagnova-phase-04-obd-606d` (PR #8)
- Schichtentrennung Transport/Protokoll/Adapter/Fahrzeugdefinition
- Protokollkatalog + Adapter-Capability-Matrix; ISO-TP Framing; UDS NRC (Write/Security aus)
- Mehr-ECU nur ISO 15765-4 (7E8/7E9 Simulator); kein Blindscan; ABS/Airbag/Komfort unavailable
- J2534/DoIP/J1939 Vorbereitung dokumentiert
- API `/api/protocols/*`, UI `/ecu`, Connector `/ecu/list`
- Tests: `dotnet test` **29 passed**; pytest **40 passed**
- Docs: `docs/phase-05-abschluss.md`, Architecture/Matrix/Prep, Progress/Requirements/Capabilities/Status

**Nicht gemacht (bewusst)**

- Keine erfundenen OEM-Adressen / kein Blindscan
- Keine DoIP/J2534/CAN-FD-Live-Implementierung
- Keine Hardwarefreigabe
- **Phase 06 nicht gestartet**
- Kein Prod-Deploy

**Nächster Schritt:** Coordinator orchestriert Phase 06.

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
- Phase-05-Abschluss: [docs/phase-05-abschluss.md](docs/phase-05-abschluss.md)
- Phase-04-Abschluss: [docs/phase-04-abschluss.md](docs/phase-04-abschluss.md)
- Phase-03-Abschluss: [docs/phase-03-abschluss.md](docs/phase-03-abschluss.md)
- Phase-02-Abschluss: [docs/phase-02-abschluss.md](docs/phase-02-abschluss.md)
