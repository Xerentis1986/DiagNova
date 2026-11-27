# DiagNova – Phasenstatus

**Aktualisiert:** 2026-11-27 (Europe/Vienna)  
**Aktuelle Arbeitsphase:** 02 abgeschlossen (simuliert getestet). **Phase 03 nicht gestartet** – Coordinator orchestriert.  
**Basis:** MVP PR #1 + Phase-00-Branch; Arbeit auf `cursor/diagnova-phase-02-brands-c4de`.

## Phasenübersicht

| Phase | Thema | Status | Bemerkung |
|-------|--------|--------|-----------|
| **00** | Bestandsaufnahme & Anforderungskatalog | **Erledigt (Docs)** | Matrix/Baseline |
| **01** | MVP Basis | **Erledigt (simuliert)** | Web/API/Simulator/Berichte/Connector-Skelett |
| **02** | Marken-Kacheln & Fahrzeugauswahl | **Simuliert getestet** | Katalog, Theme, Wizard, E2E; Text-Fallback-Logos |
| 03 | Windows-Connector & Bluetooth | Offen | Skelett aus Phase 01 vorhanden |
| 04 | Echte OBD-II/EOBD | Offen | Parser-Basis vorhanden; Hardware fehlt |
| 05 | Multiprotokoll / Mehr-ECU | Offen | |
| 06 | Diagnosedatenbank & Importe | Offen | Katalog-Statik → spätere DB/Import |
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

## Phase 02 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| UI | Helle Markenübersicht (Theme umschaltbar), Text-Kacheln, Suche, Favoriten, Recent, Wizard |
| API | `/api/catalog/*`, Preferences, Favorites, Recent, Vehicle confirm/patch |
| DB | Alembic `002_phase02` (Theme, Favoriten, Recent, Vehicle-Felder) |
| Tests | pytest 18 passed; `npm run build` OK; Playwright E2E 4 passed |
| Blocker | BLK-LOGO (keine Markenlogos); BLK-OEM (keine Diagnoseabdeckung vorgetäuscht); BLK-HW |

Details: [phase-02-abschluss.md](./phase-02-abschluss.md), [requirements.md](./requirements.md), [capabilities.md](./capabilities.md).

## Nicht ausgeführt (weiterhin)

| Check | Grund |
|-------|-------|
| `docker compose up --build` | Docker nicht installiert (BLK-DOCKER) |
| `dotnet build` Connector | .NET SDK fehlt (BLK-DOTNET) |
| Hardware-/Fahrzeugtests | Keine Hardware; Schreibtests untersagt |
| Echte Markenlogos | Rechte ungeklärt (BLK-LOGO) |
