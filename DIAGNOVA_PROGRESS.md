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
| Phase-10-Branch | `cursor/diagnova-phase-10-pdf-7d82` |
| Branding-Branch | `cursor/diagnova-branding-1a2e` |
| Phase-10B-Branch | `cursor/diagnova-phase-10b-brand-4bc4` |
| Phase-11-Branch | `cursor/diagnova-phase-11-service-8820` |
| Phase-12-Branch | `cursor/diagnova-phase-12-coding-2dd5` |
| Phase-13-Branch | `cursor/diagnova-phase-13-subscriptions-66ed` |
| Phase-14-Branch | `cursor/diagnova-phase-14-software-updates-8f1e` |
| Phase-15-Branch | `cursor/diagnova-phase-15-security-4381` |
| Phase-16-Branch | `cursor/diagnova-phase-16-deploy-8876` |
| Phase-17-Branch | `cursor/diagnova-phase-17-acceptance-8ffe` |
| Phase-18-Branch | `cursor/diagnova-phase-18-chiptuning-c46a` |
| Phase-19-Branch | `cursor/diagnova-phase-19-lkw-arch-9892` |
| Phase-20-Branch | `cursor/diagnova-phase-20-readiness-e3f2` |
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
| 09 Fahrzeugakte/Historie | 🟢 Simuliert getestet | Zeitstrahl/Vergleich/Messwerte |
| 10 PDF-Berichte/Archiv | 🟢 Simuliert getestet | A4/Unicode/Snapshot/Archiv |
| 10B Premium-Branding | 🟢 Simuliert getestet | Designsystem + Shell + Tokens |
| 11 Erweiterte Diagnose/Service | 🟢 Simuliert getestet | Katalog/Gates/Guided |
| 12 Codierung/Programmierung | 🟢 Simuliert getestet | Gates/Identifikation; Flash DEAKTIVIERT |
| 13 Abos/Administration | 🟢 Simuliert getestet | Stub-Zahlung; Entitlements; Admin |
| 14 Software-/Connector-Updates | 🟢 Simuliert getestet | Signatur/Staging/Freigabe/Rollback |
| 15 Sicherheit/QA | 🟢 Simuliert getestet | Threat Model, Rate-Limits, Audit, DSGVO-Docs |
| 16 World4You/Plesk Deploy | 🟢 Docs/Ops | Install/Compose/Proxy/Backup; Live Smoke |
| 17 Abnahme | 🟢 Docs/Abnahme | Checkliste + **NO-GO** Voll-Launch; **STOP** Prod-Rollout |
| 18 Chiptuning (optional) | 🟢 Architektur / simuliert | Gates/Baselines/UI; Aktivierung **gesperrt**; keine Maps |
| 19 LKW (optional) | 🟢 Architektur | J1939/RP1210 Prep, Flags, UI „Geplant“; Diagnose 403 |
| 20 Systemprüfung | 🟢 Docs/Audit | Integration 18+19; **NO-GO** kommerziell; Fixes + Tests |

## Chronik

### 2026-11-27 – Phase 20 Systemprüfung und Einsatzbereitschaft

**Erledigt**

- Basis: Merge Phase 18 (PR #29) + Phase 19 (PR #27) auf Phase-17-Tip (PR #26) → `cursor/diagnova-phase-20-readiness-e3f2`
- Audit-Matrix implementiert / getestet / simuliert / nicht verifiziert
- Fixes: doppelter Dashboard-`lkw`, `using Xunit` Phase14-Tests, csproj-Version 0.15.0, Publish-Doku, `.gitignore`
- Tests: pytest **148 passed**, Web-Build OK, `dotnet test` **32 passed**
- Live Smoke read-only: `/` + `/health` 200; kein Redeploy
- Berichte: `docs/phase-20-abschluss.md`, `phase-20-commercial-readiness.md`, `phase-20-checklist.md`

**Nicht gemacht (bewusst)**

- Keine Flash-/Service-Schreibfreigaben
- Kein Prod-Redeploy
- Keine erfundenen HW-/Lizenz-Ergebnisse

**Verdict:** **NO-GO** kommerzieller Vollbetrieb; Pilot-Demo bedingt nach Betreiberfreigabe.

Details: [docs/phase-20-abschluss.md](docs/phase-20-abschluss.md)

### 2026-11-27 – Phase 19 LKW/Nutzfahrzeug Architektur

**Erledigt**

- Basis: Phase 17 `cursor/diagnova-phase-17-acceptance-8ffe` (PR #26); parallel zu Phase 18
- Architektur-Docs, Capability-Flags, Markennavigation, UI `/lkw` „Geplant“
- Diagnose-POSTs bewusst 403; kein Parser/Fake-Simulator

**Nicht gemacht (bewusst)**

- Kein J1939-SPN/FMI-Stack, keine RP1210-DLL, keine LKW-Live-Diagnose

Details: [docs/phase-19-abschluss.md](docs/phase-19-abschluss.md)

### 2026-11-27 – Phase 18 Optionales Chiptuning (Architektur)

**Erledigt**

- Basis: `cursor/diagnova-phase-17-acceptance-8ffe` (PR #26)
- Modul-Skelett: Katalog, Baselines, Genehmigungen, Historie, Legal-Gates, Workflow-Simulation
- API `/api/tuning/*` + UI `/tuning` (Geplant/deaktiviert); Map/Flash/Aktivierung 403
- Alembic `013_phase18`; Tests `test_phase18_tuning.py`
- **Keine** Tuning-Algorithmen, keine Abgasmanipulation

**Nicht gemacht (bewusst)**

- Keine produktive Aktivierung / kein Flash / keine Kennfeldänderungen
- Kein Prod-Redeploy

Details: [docs/phase-18-abschluss.md](docs/phase-18-abschluss.md)

### 2026-11-27 – Phase 17 Gesamtabnahme und Freigabeprüfung

**Erledigt**

- Basis: `cursor/diagnova-phase-16-deploy-8876` (PR #25)
- Abnahme-Checkliste + Go/No-Go-Bericht; Abdeckung implementiert vs. simuliert vs. blockiert
- Smoke: pytest **126 passed**, Web-Build OK, Live `/` + `/health` 200
- Matrix/Capabilities/phase-status/Progress aktualisiert (REQ-17-ACC)

**Nicht gemacht (bewusst)**

- **Kein** produktiver Voll-Rollout / kein Server-Redeploy
- **Keine** Flash-/Service-Freigaben; nichts als `hardwaregetestet`/`freigegeben`
- **Phase 18/19 nicht gestartet**

**Verdict:** NO-GO Voll-Launch; Pilot Demo nur nach Betreiberfreigabe.

Details: [docs/phase-17-abschluss.md](docs/phase-17-abschluss.md), [docs/phase-17-acceptance-checklist.md](docs/phase-17-acceptance-checklist.md)

### 2026-11-27 – Phase 16 World4You Ubuntu/Plesk Deployment

**Erledigt**

- Basis: `cursor/diagnova-phase-15-security-4381` (PR #24)
- Installationsanleitung, Checkliste, Backup/Rollback, Proxy/WS-Confs
- `docker-compose.prod.yml` + Deploy-/Backup-Skripte (helix/Sites unberührt)
- Live Smoke read-only: `/` + `/health` 200 unter https://diagnova.codekreativ.at/
- Keine Secrets in Git; kein destruktives Server-Redeploy

**Nicht gemacht (bewusst)**

- **Phase 17 nicht gestartet**
- Kein Staging-Subdomain-Anlegen; kein Live-Redeploy ohne Freigabe

**Nächster Schritt:** Coordinator meldet Freigabeprüfung vor Phase 17.

Details: [docs/phase-16-abschluss.md](docs/phase-16-abschluss.md)

### 2026-11-27 – Phase 14 Software- und Connector-Updates

**Erledigt**

- Basis: `cursor/diagnova-phase-13-subscriptions-66ed` (PR #21)
- Software-Updates getrennt von Diagnosedaten-Updates; Versionen API/Web/Connector `0.14.0`
- Checksum/HMAC, Kompatibilitätsmatrix, Staging, Admin-Freigabe, Healthcheck, Rollback
- Busy-Gate (Diagnose/Service/Flash); Prod-Auto-Updates ohne Zertifikat gesperrt
- UI `/software-updates` (Designsystem 10B); Connector `/version` + Update-Busy-Gate; Alembic `011_phase14`
- Tests: pytest **113 passed**, Frontend build OK

**Nicht gemacht (bewusst)**

- **Phase 15 nicht gestartet**
- Kein echtes Code-Signing-Zertifikat / kein Prod-Auto-Update; kein Prod-Deploy

**Nächster Schritt:** Coordinator orchestriert Phase 15.

Details: [docs/phase-14-abschluss.md](docs/phase-14-abschluss.md)

### 2026-11-27 – Phase 13 Abonnements und Administration

**Erledigt**

- Basis: `cursor/diagnova-phase-12-coding-2dd5` (PR #20)
- Tarife PKW + LKW/Kombi geplant; Entitlements serverseitig; Trial/Kündigung
- Payment nur Stub (HMAC-Webhooks, Idempotenz); keine echten Abbuchungen
- Mandantenregistrierung, Einladungen, Gerätebindung; kritische Ops ohne Abrupt-Abbruch
- Admin-UI `/admin`, Abo-UI `/subscriptions` (Designsystem 10B); Alembic `010_phase13`
- Tests: pytest **104 passed**, Frontend build OK

**Nicht gemacht (bewusst)**

- **Phase 14 nicht gestartet** (zum Zeitpunkt des Phase-13-Abschlusses)
- Kein echter Payment-Provider; DACH-Steuer/AVV offen; kein Prod-Deploy

Details: [docs/phase-13-abschluss.md](docs/phase-13-abschluss.md)

### 2026-11-27 – Phase 12 Steuergerätecodierung und Programmierung

**Erledigt**

- Basis: `cursor/diagnova-phase-11-service-8820` (PR #19)
- Katalog Identifikation/Codierung/Flash/J2534-Prep; Schreiben & Flash DEAKTIVIERT
- Gates: falsches Fahrzeug, Spannungsabfall, fehlende Spec/Berechtigung, Abbruch, Comm-Loss; kein Auto-Retry
- UI `/coding` (Designsystem 10B); Alembic `009_phase12`
- Tests: pytest **97 passed**, Frontend build OK

**Nicht gemacht (bewusst)**

- **Phase 13 nicht gestartet**
- Keine echten Flash-Routinen; keine OEM-Codierdaten; kein Prod-Deploy

**Nächster Schritt:** Coordinator orchestriert Phase 13.

Details: [docs/phase-12-abschluss.md](docs/phase-12-abschluss.md)

### 2026-11-27 – Phase 11 Erweiterte Diagnose und Servicefunktionen

**Erledigt**

- Basis: `cursor/diagnova-phase-10b-brand-4bc4` (PR #18)
- Servicekatalog mit Specs/Voraussetzungen/Safety-Gates; DPF-Regen/EPB etc. deaktiviert
- Gate-Simulation: fehlende Voraussetzungen, Abbruch, Kommunikationsverlust
- Geführte Diagnose: ECU, Messwertgruppen, DTC-Hilfe; DPF-Off ausgeschlossen
- UI `/service`, `/guided`; Alembic `008_phase11`
- Tests: pytest **90 passed**, Frontend build OK

**Nicht gemacht (bewusst)**

- **Phase 12 nicht gestartet**
- Keine OEM-Schreibprozeduren; kein Live-Service; kein Prod-Deploy

**Nächster Schritt:** Coordinator orchestriert Phase 12.

Details: [docs/phase-11-abschluss.md](docs/phase-11-abschluss.md)

### 2026-11-27 – Phase 10B Premium-Branding und Designsystem

**Erledigt**

- Merge Phase 10 + Branding #16 auf `cursor/diagnova-phase-10b-brand-4bc4`
- Tokens Charcoal/Teal `#00B3A3`/Hell `#F8FAFB`/Dunkel `#111A20`
- Designsystem UI-Primitives; AppShell Sidebar+Topbar nach Mockup (Brand-Logo, Teal)
- Fahrzeugauswahl Hero + Aktionskarten; Settings-Seite; PDF Brand-Fallback
- Tests: Frontend build OK, pytest **83 passed**

**Nicht gemacht (bewusst)**

- **Phase 11 nicht gestartet**
- Kein Prod-Deploy; keine OEM-Logos; keine Vektor-Logos

**Nächster Schritt:** Coordinator orchestriert Phase 11.

Details: [docs/phase-10b-abschluss.md](docs/phase-10b-abschluss.md)

### 2026-11-27 – Logo-/Brand-Paket integriert

**Erledigt**

- Basis: `origin/cursor/diagnova-phase-09-history-f3fe` (PR #14); Branding-PR separat
- Web: Favicons, PWA-Icons, Apple-Touch, Manifest → `apps/web/public/`
- Brand-Tokens; Theme-aware `BrandMark`
- Windows-Connector ApplicationIcon
- Doku: [docs/branding.md](docs/branding.md)

### 2026-11-27 – Phase 10 PDF-Diagnoseberichte und Archiv

**Erledigt**

- Alembic `007_phase10`, A4-PDF, Archiv/Suche/Auto-PDF
- UI `/reports`; Tests: pytest **83 passed**

**Nicht gemacht (bewusst)**

- Keine echten Live-Berichte; **Phase 11 damals nicht gestartet**

### 2026-11-27 – Phase 09 Fahrzeug-History und digitale Fahrzeugakte

Details: `docs/phase-09-abschluss.md`.

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
- Branding: [docs/branding.md](docs/branding.md)
- Phasenstatus: [docs/phase-status.md](docs/phase-status.md)
- Phase-11-Abschluss: [docs/phase-11-abschluss.md](docs/phase-11-abschluss.md)
- Phase-10B-Abschluss: [docs/phase-10b-abschluss.md](docs/phase-10b-abschluss.md)
- Phase-10-Abschluss: [docs/phase-10-abschluss.md](docs/phase-10-abschluss.md)
- Phase-09-Abschluss: [docs/phase-09-abschluss.md](docs/phase-09-abschluss.md)
- Phase-08-Abschluss: [docs/phase-08-abschluss.md](docs/phase-08-abschluss.md)
- Phase-07-Abschluss: [docs/phase-07-abschluss.md](docs/phase-07-abschluss.md)
- Phase-06-Abschluss: [docs/phase-06-abschluss.md](docs/phase-06-abschluss.md)
- Freie Quellen: [docs/free-data-sources.md](docs/free-data-sources.md)
