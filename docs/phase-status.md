# DiagNova – Phasenstatus

**Aktualisiert:** 2026-11-27 (Europe/Vienna)  
**Aktuelle Arbeitsphase:** 00 (Bestandsaufnahme) – Dokumentation geliefert, **warte auf Freigabe** vor Phase 02.  
**MVP-Basis:** PR #1 Branch `cursor/diagnova-phase-ab-mvp-bf17` @ `6adfcc4` (= Prompt-Phase 01 / bisher A+B+C-Skelett).

## Phasenübersicht

| Phase | Thema | Status | Bemerkung |
|-------|--------|--------|-----------|
| **00** | Bestandsaufnahme & Anforderungskatalog | **Dokumentiert – Freigabe ausstehend** | Docs + Baseline-Tests; keine Feature-Neuentwicklung |
| **01** | MVP Basis (Prompt ausgelassen) | **Erledigt (simuliert)** | Web/API/Simulator/Berichte/Connector-Skelett |
| 02 | Marken-Kacheln & Fahrzeugauswahl | Offen | |
| 03 | Windows-Connector & Bluetooth | Offen | Skelett aus Phase 01 vorhanden |
| 04 | Echte OBD-II/EOBD | Offen | Parser-Basis vorhanden; Hardware fehlt |
| 05 | Multiprotokoll / Mehr-ECU | Offen | |
| 06 | Diagnosedatenbank & Importe | Offen | |
| 07 | Automatische Daten-Updates | Offen | |
| 08 | Werkstatt- & Kundenverwaltung | Offen | |
| 09 | Fahrzeug-History / Akte | Offen | |
| 10 | PDF-Berichte & Archiv | Offen | MVP-PDF rudimentär |
| 11 | Erweiterte Diagnose / Service | Offen | UI-Platzhalter |
| 12 | Codierung / Programmierung | Offen | UI-Platzhalter; Schreibpfade gesperrt |
| 13 | Abos & Administration | Offen | |
| 14 | Software-/Connector-Updates | Offen | |
| 15 | Sicherheit / Datenschutz / QA | Offen | Auth-Basis vorhanden |
| 16 | World4You Ubuntu/Plesk Deploy | Offen / parallel vorbereitet | Domain/DB außerhalb Repo; kein Prod-Deploy |
| 17 | Gesamtabnahme | Offen | |
| 18 | Chiptuning (optional) | Später | standardmäßig gesperrt |
| 19 | LKW (optional) | Später | |

## Inventar-Kurzfassung (Phase 00)

Siehe detailliert: [capabilities.md](./capabilities.md), Matrix: [requirements.md](./requirements.md).

| Bereich | Befund |
|---------|--------|
| Code | Monorepo ~85 Dateien; React/FastAPI/.NET-Skelett/Packages |
| DB | 5 Tabellen, Alembic `001_initial`, Seed Users+9 Fahrzeuge |
| API | REST Auth/Vehicles/Dashboard/Diagnostics/Sessions/Reports; kein WS |
| UI | Login, Dashboard, Fahrzeuge, Diagnose, Berichte, Planned |
| Connector | Loopback + Stub; **keine** Fahrzeugbefehle |
| Docker | Compose api/web/postgres; in Agent-VM **nicht** ausgeführt |
| Tests | 12 pytest passed; Web `npm run build` OK; kein .NET-/Compose-Test hier |

## Baseline-Build & Tests (Phase 00, ausgeführt)

Umgebung: Cloud-Agent Linux, Python 3.12.3, Node 22.23.4. **Kein** Docker, **kein** .NET SDK.

### Web

```bash
cd apps/web && npm ci && npm run build
```

**Ergebnis:** erfolgreich (Vite production build, 2026-11-27). Warnung: Chunk > 500 kB (Hinweis, kein Fehler).

### API / Protocols

```bash
pip3 install --user -r apps/api/requirements.txt
pip3 install --user ./packages/diagnostic-protocols
export DATABASE_URL='sqlite:////tmp/diagnova-phase00.db'
export PYTHONPATH="apps/api:packages/diagnostic-protocols/src"
python3 -m pytest tests -q
```

**Ergebnis:** `12 passed` (ca. 5.2 s), Deprecation-Warnings (jose `utcnow`, passlib/crypt, reportlab, pytest-asyncio Config) – nicht blockierend.

### Nicht ausgeführt (fehlende Voraussetzungen)

| Check | Grund |
|-------|-------|
| `docker compose up --build` | Docker nicht installiert (BLK-DOCKER) |
| `dotnet build` Connector | .NET SDK fehlt (BLK-DOTNET) |
| Hardware-/Fahrzeugtests | Keine Hardware; Schreibtests untersagt |
| E2E Browser | Keine E2E-Suite im Repo |

## Testlücken (ohne Neuentwicklung des Grundsystems)

1. Keine Frontend-Unit- oder Playwright/Cypress-E2E-Tests  
2. Keine Connector-Unit-Tests / Fake-Port-Suite  
3. Keine Mandanten-/IDOR-Tests (Feature fehlt)  
4. Keine Compose-Integrationspipeline in CI dokumentiert  
5. JWT `datetime.utcnow` Deprecation → später Phase 15 bereinigen  
6. PDF nur Smoke (`%PDF`-Header), kein Layout-/Unicode-Regressionstest

## Arbeitsregeln (weiterhin gültig)

- Eine Phase nach der anderen; nach Abschlussbericht **STOPP** und Freigabe abwarten  
- Simuliert vs. echt klar trennen  
- Keine erfundenen Diagnosedaten/Rechte  
- Keine Secrets, kein Prod-Deploy, keine Fahrzeug-Schreibtests ohne Zustimmung  
- Bestehende MVP-Komponenten erhalten; Phase 01 nicht neu bauen
