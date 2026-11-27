# DiagNova – Fortschritt

Dauerhafte Fortschrittsdatei (Repo-Root). Nach jeder Phase aktualisieren.

## Meta

| Feld | Wert |
|------|------|
| Produkt | DiagNova – webbasierte Mehrmarken-Fahrzeugdiagnose |
| Repo | https://github.com/Xerentis1986/DiagNova |
| MVP-Branch / PR | `cursor/diagnova-phase-ab-mvp-bf17` / PR #1 @ `6adfcc4` |
| Phase-00-Branch | `cursor/diagnova-phase-00-inventory-c287` (basiert auf MVP-Branch) |
| Letzte Aktualisierung | 2026-11-27 (Europe/Vienna) |

## Ampel

| Phase | Ampel | Kurzstatus |
|-------|-------|------------|
| 00 Bestandsaufnahme | 🟡 Freigabe | Docs/Matrix/Baseline fertig – **warte auf User-Freigabe** |
| 01 MVP Basis | 🟢 Simuliert | PR #1 – nicht erneut entwickeln |
| 02–15 | ⚪ Offen | |
| 16 Deploy-Vorbereitung | 🟡 Parallel | World4You/Plesk Domain/DB außerhalb; kein Prod |
| 17 Abnahme | ⚪ Offen | |
| 18–19 Optional | ⚪ Später | |

## Chronik

### 2026-11-27 – Phase 00 Bestandsaufnahme

**Erledigt**

- Git: von `origin/cursor/diagnova-phase-ab-mvp-bf17` gebrancht (nicht von leerem `main`)
- Inventar Code/DB/API/UI/Connector/Docker/Tests
- Anforderungsmatrix mit IDs → Phasen 02–19
- Docs: `docs/requirements.md`, `docs/capabilities.md`, `docs/phase-status.md`
- Baseline: `pytest` **12 passed**; `apps/web` **npm run build** OK
- Blocker markiert: Hardware, OEM-Lizenzen, Docker/.NET in Agent-VM, kein Prod-Deploy

**Nicht gemacht (bewusst)**

- Keine Phase-01-Neuentwicklung
- Keine Phase 02+
- Kein Docker-Compose-/dotnet-Build (Tools fehlen)
- Keine Fahrzeug-Schreibtests / kein Deployment

**Nächster Schritt:** User-/Coordinator-Freigabe → erst dann Phase 02.

### Früher – Phase 01 / A+B MVP (PR #1)

Simuliertes Monorepo: React-Web, FastAPI, PostgreSQL/Alembic, Docker Compose, OBD-Simulator, Berichte CSV/PDF, .NET-Connector-Skelett. Details: `docs/phase-ab-mvp-plan.md`, README.

## Verweise

- Matrix: [docs/requirements.md](docs/requirements.md)
- Fähigkeiten: [docs/capabilities.md](docs/capabilities.md)
- Phasenstatus: [docs/phase-status.md](docs/phase-status.md)
- Promptpaket (Projekt-Store): `docs/DiagNova_Alle_Master_Prompts.md`
