# DiagNova – Phasenstatus

**Aktualisiert:** 2026-11-27 (Europe/Vienna)  
**Aktuelle Arbeitsphase:** 08 abgeschlossen (simuliert getestet). **Phase 09 nicht gestartet** – Coordinator orchestriert.  
**Basis:** Phase-07-Branch `cursor/diagnova-phase-07-updates-4111` (PR #12); Arbeit auf `cursor/diagnova-phase-08-workshop-d09b`.

## Phasenübersicht

| Phase | Thema | Status | Bemerkung |
|-------|--------|--------|-----------|
| **00** | Bestandsaufnahme & Anforderungskatalog | **Erledigt (Docs)** | Matrix/Baseline |
| **01** | MVP Basis | **Erledigt (simuliert)** | Web/API/Simulator/Berichte/Connector-Skelett |
| **02** | Marken-Kacheln & Fahrzeugauswahl | **Simuliert getestet** | Katalog, Theme, Wizard, E2E |
| **03** | Windows-Connector & Bluetooth | **Simuliert getestet** | Discovery, Auth, Fake-Port, ELM-Prep |
| **04** | Echte OBD-II/EOBD | **Simuliert getestet** | Parser/Allowlist/Clear-Gate; **keine HW-Freigabe** |
| **05** | Multiprotokoll / Mehr-ECU | **Simuliert getestet** | Schichten, Matrix, ISO-TP/UDS-NRC, OBD-ECUs; DoIP/J2534 Prep |
| **06** | Diagnosedatenbank & Importe | **Simuliert getestet** | Modell/Import/Quarantäne/Rollback; DTC unbekannt; ODX 403 |
| **07** | Automatische Daten-Updates | **Simuliert getestet** | Scheduler/SSRF/Signatur/Staging/Freigabe/Rollback; keine echten Feeds |
| **08** | Werkstatt- & Kundenverwaltung | **Simuliert getestet** | Mandant/Rollen/Kunden/Aufträge/DSGVO; keine Produktivdaten |
| 09 | Fahrzeug-History / Akte | Offen | |
| 10 | PDF-Berichte & Archiv | Offen | MVP-PDF rudimentär |
| 11 | Erweiterte Diagnose / Service | Offen | UI-Platzhalter |
| 12 | Codierung / Programmierung | Offen | UI-Platzhalter; Schreibpfade gesperrt |
| 13 | Abos & Administration | Offen | |
| 14 | Software-/Connector-Updates | Offen | |
| 15 | Sicherheit / Datenschutz / QA | Offen | Auth-Basis vorhanden |
| 16 | World4You Ubuntu/Plesk Deploy | Offen / parallel vorbereitet | kein Prod-Deploy |
| 17 | Gesamtabnahme | Offen | |
| 18 | Chiptuning (optional) | Später | standardmäßig gesperrt |
| 19 | LKW (optional) | Später | J1939/RP1210 |

## Phase 08 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Mandant | `workshop_id` serverseitig aus Sitzung/JWT; Cross-Tenant → 404 |
| Werkstatt | Profil, Logo-Data-URL, Aufbewahrungstage, Mitglieder/Rollen |
| Kunden | CRUD, Suche, Dubletten 409 + Merge, Archiv/Anonymize |
| Aufträge | Status/Notizen/Reparatur; Löschkonflikt bei offenen Aufträgen |
| Fahrzeuge | Mandantenfilter, VIN/Kennzeichen/km-Validierung |
| UI | `/workshop`, `/customers`, `/work-orders` |
| Blocker | BLK-LEGAL (Rechtsberatung DSGVO), BLK-HW, BLK-DOCKER |

Details: [phase-08-abschluss.md](./phase-08-abschluss.md).

## Phase 07 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Kanäle | Allowlist Fixture/HTTPS; default disabled; keine kommerziellen Feeds |
| Scheduler | Intervall 24h, Lock, Retry/Backoff; default aus |
| Sicherheit | SSRF, Größenlimit, keine Archive, Hash/HMAC |
| Publish | Auto nur DTC-beschreibend; Prozeduren/Adressen manuell |
| UI | `/data-updates` Admin-Dashboard |
| Blocker | BLK-OEM (echte Quellen), BLK-HW, BLK-DOCKER |

Details: [phase-07-abschluss.md](./phase-07-abschluss.md).

## Phase 06 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Datenmodell | Versioniert + Herkunft (`003_phase06`) |
| Import | JSON/CSV Preview → Quarantäne/Apply/Rollback |
| DTC | Unbekannt ohne Text; keine Bosch/Gutmann/Delphi |
| ODX | 403 bis Lizenz |
| UI | `/diagnostic-data` mit Provenance |
| Blocker | BLK-OEM, BLK-HW, BLK-DOCKER |

Details: [phase-06-abschluss.md](./phase-06-abschluss.md), [free-data-sources.md](./free-data-sources.md), [diagnostic-data-model.md](./diagnostic-data-model.md).

## Phase 05 – Kurzfazit

Details: [phase-05-abschluss.md](./phase-05-abschluss.md).

## Nicht ausgeführt (weiterhin)

| Check | Grund |
|-------|-------|
| `docker compose up --build` | Docker nicht installiert (BLK-DOCKER) |
| Echter Fahrzeug-/Multiprotokoll-Hardwaretest | Keine Hardware (BLK-HW) |
| Live-Freigabe | Explizit ausstehend |
| OEM-ECU-Definitionen | BLK-OEM |
