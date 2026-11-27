# DiagNova – Phasenstatus

**Aktualisiert:** 2026-11-27 (Europe/Vienna)  
**Aktuelle Arbeitsphase:** 12 abgeschlossen (simuliert getestet). **STOP** – Phase 13 nicht starten (Coordinator).  
**Basis:** Phase-11-Branch `cursor/diagnova-phase-11-service-8820` (PR #19); Arbeit auf `cursor/diagnova-phase-12-coding-2dd5`.

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
| **09** | Fahrzeug-History / Akte | **Simuliert getestet** | Zeitstrahl, Vergleich, Messwerte; Demo getrennt |
| **10** | PDF-Berichte & Archiv | **Simuliert getestet** | A4/Unicode/Archiv/Snapshot; Demo-WM |
| **10B** | Premium-Branding | **Simuliert getestet** | Designsystem/Shell |
| **11** | Erweiterte Diagnose / Service | **Simuliert getestet** | Katalog/Gates/Guided; Live deaktiviert; DPF-Off excluded |
| **12** | Codierung / Programmierung | **Simuliert getestet** | Identifikation + Gates; Flash/Schreiben DEAKTIVIERT; J2534 Prep |
| 13 | Abos & Administration | Offen | |
| 14 | Software-/Connector-Updates | Offen | |
| 15 | Sicherheit / Datenschutz / QA | Offen | Auth-Basis vorhanden |
| 16 | World4You Ubuntu/Plesk Deploy | Offen / parallel vorbereitet | kein Prod-Deploy |
| 17 | Gesamtabnahme | Offen | |
| 18 | Chiptuning (optional) | Später | standardmäßig gesperrt |
| 19 | LKW (optional) | Später | J1939/RP1210 |

## Phase 12 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Identifikation | Lesend simuliert; OEM-Codierprofil unavailable |
| Gates | VIN-Mismatch, Spannungsabfall, fehlende Spec/Berechtigung, Abbruch, Comm-Loss |
| Codierung/Flash | Katalog vorhanden; `enabled/write/flash=false`; Live+Flash 403 |
| J2534/D-PDU | documented_prep; keine Vendor-DLL |
| UI | `/coding` – Designsystem 10B |
| Tests | pytest **97 passed**; Build OK |
| Blocker | BLK-OEM, BLK-HW, BLK-J2534, BLK-RELEASE |

Details: [phase-12-abschluss.md](./phase-12-abschluss.md).

## Phase 11 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Katalog | Öl/Batterie/EPB/DPF/Injektor/Drossel/Lenkwinkel/Stellglied/Grundeinstellung – Specs + Gates |
| Safety | Voraussetzungen, Phrase, Timeout, Abbruch, Audit; Live 403; DPF-Off excluded |
| Guided | ECU-Überblick, Messwertgruppen, DTC-Hilfe (unbekannt bleibt unbekannt) |
| UI | `/service`, `/guided` – Designsystem 10B |
| Tests | pytest **90 passed**; Build OK |
| Blocker | BLK-OEM, BLK-HW, BLK-RELEASE, BLK-SAFETY |

Details: [phase-11-abschluss.md](./phase-11-abschluss.md).

## Phase 10 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| PDF | A4 ReportLab, Werkstattlogo, Unicode, Kopf/Fuß, Demo-Wasserzeichen |
| Snapshot | `content_sha256` + `data_version`; keine Auto-Reparaturdiagnose |
| Archiv | Suche/VIN, Archivieren, Soft-Delete, Purge nach Retention |
| Auto-PDF | optional bei Session-Close `?auto_pdf=true` |
| UI | `/reports` Vorschau/Download/Druck |
| Blocker | BLK-HW, BLK-LEGAL |

Details: [phase-10-abschluss.md](./phase-10-abschluss.md).

## Phase 09 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Akte | Zeitstrahl Sitzungen/Notizen/Aufträge/Berichte; Authentizität markiert |
| Lookup | VIN / Kennzeichen mandantenspezifisch |
| Sitzung | Auto-Save, Abort, Idempotenz; Adapter/Protokoll/km/ECU/DTC/FF |
| Vergleich | neu / weiterhin / nicht erneut beobachtet; ohne ECU-Check ≠ behoben |
| Messwerte | begrenzt (500/Sitzung, 5000/Fahrzeug) |
| UI | `/vehicle-record` |
| Blocker | BLK-HW (keine Live-Historie), BLK-LEGAL |

Details: [phase-09-abschluss.md](./phase-09-abschluss.md).

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
