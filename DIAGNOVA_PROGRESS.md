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
| Letzte Aktualisierung | 2026-11-27 (Europe/Vienna) |

## Ampel

| Phase | Ampel | Kurzstatus |
|-------|-------|------------|
| 00 Bestandsaufnahme | 🟢 Docs | Matrix/Baseline auf Feature-Branch |
| 01 MVP Basis | 🟢 Simuliert | PR #1 – nicht erneut entwickeln |
| 02 Marken-Kacheln | 🟢 Simuliert getestet | Katalog, Theme, Wizard, E2E – **Phase 03 nicht gestartet** |
| 03–15 | ⚪ Offen | |
| 16 Deploy-Vorbereitung | 🟡 Parallel | World4You/Plesk außerhalb; kein Prod |
| 17 Abnahme | ⚪ Offen | |
| 18–19 Optional | ⚪ Später | |

## Chronik

### 2026-11-27 – Phase 02 Marken-Kacheln und Fahrzeugauswahl

**Erledigt**

- Branch von `origin/cursor/diagnova-phase-00-inventory-c287` (enthält MVP)
- DACH-Markenkatalog (38 Marken) mit Text-Fallback-Logos (keine ungeklärten Markenrechte)
- Suche, Favoriten (lokal + Profil-API), zuletzt verwendet
- Theme Hell/Dunkel/System (localStorage + `users.theme_preference`)
- Auswahlfluss Marke→Modell→Baureihe/Motor→VIN/Kennzeichen/km→Bestätigen→Diagnose
- Capabilities ehrlich: nur MVP-Simulator verfügbar; OEM geplant
- Alembic `002_phase02`, API-Routen `/catalog/*`, `/preferences`, `/favorites`, `/recent`, `POST /vehicles/confirm`
- Tests: pytest **18 passed**; Web build OK; Playwright E2E **4 passed**
- Docs: requirements/capabilities/phase-status + `docs/phase-02-abschluss.md`

**Nicht gemacht (bewusst)**

- Keine echten Markenlogos (BLK-LOGO)
- Keine Phase 03 (Connector/Bluetooth)
- Kein Prod-Deploy / keine Hardwaretests

**Nächster Schritt:** Coordinator orchestriert Phase 03.

### 2026-11-27 – Phase 00 Bestandsaufnahme

Inventar, Anforderungsmatrix, Baseline-Tests. Details: `docs/phase-status.md`.

### Früher – Phase 01 / A+B MVP (PR #1)

Simuliertes Monorepo. Details: `docs/phase-ab-mvp-plan.md`.

## Verweise

- Matrix: [docs/requirements.md](docs/requirements.md)
- Fähigkeiten: [docs/capabilities.md](docs/capabilities.md)
- Phasenstatus: [docs/phase-status.md](docs/phase-status.md)
- Phase-02-Abschluss: [docs/phase-02-abschluss.md](docs/phase-02-abschluss.md)
