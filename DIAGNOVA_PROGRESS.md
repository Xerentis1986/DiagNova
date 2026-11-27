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
| Letzte Aktualisierung | 2026-11-27 (Europe/Vienna) |

## Ampel

| Phase | Ampel | Kurzstatus |
|-------|-------|------------|
| 00 Bestandsaufnahme | 🟢 Docs | Matrix/Baseline auf Feature-Branch |
| 01 MVP Basis | 🟢 Simuliert | PR #1 – nicht erneut entwickeln |
| 02 Marken-Kacheln | 🟢 Simuliert getestet | Katalog, Theme, Wizard, E2E |
| 03 Windows-Connector | 🟢 Simuliert getestet | Discovery/Auth/Fake-Port |
| 04 OBD-II/EOBD | 🟢 Simuliert getestet | Parser/Allowlist/Clear-Gate – **keine HW-Freigabe**; **Phase 05 nicht gestartet** |
| 05–15 | ⚪ Offen | |
| 16 Deploy-Vorbereitung | 🟡 Parallel | World4You/Plesk außerhalb; kein Prod |
| 17 Abnahme | ⚪ Offen | |
| 18–19 Optional | ⚪ Später | |

## Chronik

### 2026-11-27 – Phase 04 Echte OBD-II/EOBD-Diagnose

**Erledigt**

- Branch von `origin/cursor/diagnova-phase-03-connector-90c7` (PR #7)
- ELM/OBD-Parser (Multi-ECU, NO DATA, Timeout, Negativ); PID-Bitmap; Readiness; VIN; Freeze-Frame
- Connector `ObdSession` + Allowlist; Fake-Simulatorvektoren; Fahrzeuglink nach Init
- Clear-DTC freigabegeschützt (Phrase, Acks, Token) – permanente DTCs nicht löschbar
- API/UI: simulierte Clear-Flow, Live/Demo-Kennzeichnung
- Tests: `dotnet test` **23 passed**; pytest **27 passed**
- Docs: `docs/phase-04-abschluss.md`, Progress/Requirements/Capabilities/Status

**Nicht gemacht (bewusst)**

- Kein realer Fahrzeugtest / keine Hardwarefreigabe
- Keine Phase 05
- Kein Prod-Deploy

**Nächster Schritt:** Coordinator orchestriert Phase 05.

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
- Phase-02-Abschluss: [docs/phase-02-abschluss.md](docs/phase-02-abschluss.md)
- Phase-03-Abschluss: [docs/phase-03-abschluss.md](docs/phase-03-abschluss.md)
- Phase-04-Abschluss: [docs/phase-04-abschluss.md](docs/phase-04-abschluss.md)
