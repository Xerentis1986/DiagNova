# DiagNova – Phasenstatus

**Aktualisiert:** 2026-11-27 (Europe/Vienna)  
**Aktuelle Arbeitsphase:** 17 abgeschlossen (Abnahme Docs; **NO-GO** Voll-Launch). **STOP** vor Prod-Rollout. Phase 18/19 nicht starten.  
**Basis:** Phase-16-Branch `cursor/diagnova-phase-16-deploy-8876` (PR #25); Arbeit auf `cursor/diagnova-phase-17-acceptance-8ffe`.

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
| **13** | Abos & Administration | **Simuliert getestet** | Stub-Zahlung, Entitlements, Mandanten/Einladungen, Admin-UI; kein echter PSP |
| **14** | Software-/Connector-Updates | **Simuliert getestet** | Versionierung/Signatur/Staging/Freigabe/Rollback; getrennt von Daten-Updates; kein Auto-Install |
| **15** | Sicherheit / Datenschutz / QA | **Simuliert getestet** | Threat Model, Rate-Limits, Audit-Redaction, DSGVO-Docs, Backup; UI `/security` |
| **16** | World4You Ubuntu/Plesk Deploy | **Implementiert (Docs/Ops)** | Install/Compose/Proxy/Backup/Rollback; Live Smoke; kein destruktives Redeploy |
| **17** | Gesamtabnahme | **Erledigt (Docs/Abnahme)** | Checkliste + Go/No-Go; **NO-GO** Voll-Launch; STOP Prod-Rollout |
| 18 | Chiptuning (optional) | Später | **nicht gestartet**; standardmäßig gesperrt |
| 19 | LKW (optional) | Später | **nicht gestartet**; J1939/RP1210 |

## Phase 17 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Abnahme-Checkliste | `docs/phase-17-acceptance-checklist.md` |
| Go/No-Go | **NO-GO** Voll-Launch; Live-OBD/Service/Flash **NO-GO**; Pilot Demo bedingt |
| Smoke | pytest **126 passed**; Web-Build OK; Live `/`+`/health` 200 |
| Blocker | BLK-HW, BLK-OEM, BLK-ADAPTER, BLK-LEGAL, BLK-PAY, BLK-CERT, BLK-DEPLOY |
| Prod-Rollout | **STOP** – nur nach Betreiber- + Coordinator-Freigabe |
| Nächste Phase | **18/19 nicht gestartet** |

Details: [phase-17-abschluss.md](./phase-17-abschluss.md).

## Phase 16 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Install | `docs/world4you-plesk-install.md` (SSH/Plesk/Docker/DNS, Secrets, Staging) |
| Compose Prod | Volumes, Healthchecks, Restart, Memory-Limits, DB ohne Host-Port |
| Proxy / TLS / WS | Plesk LE Ist; `web.conf` + `plesk-proxy.conf` mit Upgrade |
| Backup / Rollback | Skripte + Docs; Pre-Deploy-Dump im Deploy-Skript |
| Live Smoke | `/` + `/health` 200 (kein Server-Schreibzugriff in dieser Phase) |
| Unangetastet | helix-ki, masterdesk, `/sv/` |
| Blocker | BLK-DEPLOY (Redeploy nur mit Freigabe); Staging nicht angelegt |
| Nächste Phase | **17 nicht gestartet** |

Details: [phase-16-abschluss.md](./phase-16-abschluss.md), Checkliste [phase-16-deploy-checklist.md](./phase-16-deploy-checklist.md).

## Phase 15 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Threat Model | Browser/API/Connector/Adapter/Updates/Mandanten dokumentiert |
| Auth | bcrypt, JWT iat/typ/exp, Login-Rate-Limit, Origin-Check, Logout-Audit |
| RBAC/IDOR | Mandant 404 + Rollen; Regressionstests |
| Audit | Redaction Passwort/VIN/E-Mail/Telefon; outcome/ip_hash |
| DSGVO | Prozess-Docs; keine Konformität behauptet |
| Backup | Docs + API; Phase-16-Checkliste ergänzt |
| UI | `/security` – Designsystem 10B |
| Versionen | API/Web/Connector `0.15.0` |
| Tests | pytest **126 passed**; Web-Build OK |
| Blocker | BLK-LEGAL, BLK-CERT, Default-JWT nur Dev/Tests |

Details: [phase-15-abschluss.md](./phase-15-abschluss.md).

## Phase 14 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Trennung | Software-Updates ≠ Diagnosedaten-Updates (Phase 07) |
| Versionen | Linie jetzt `0.15.0` (Phase 15); Integrität/Busy/Rollback unverändert |
| Integrität | SHA-256 + HMAC; manipulierte Pakete abgelehnt |
| Freigabe | Staging → Admin-Freigabe; keine ungeprüften Auto-Installs |
| Busy-Gate | Keine Installation während Diagnose/Service/Flash |
| Rollback | Manuell + automatisch bei Healthcheck-Fail |
| Prod | Auto-Updates ohne Signaturzertifikat gesperrt |
| UI | `/software-updates` – Designsystem 10B |
| Tests | pytest (Regression in Phase-15-Suite) |
| Blocker | BLK-CERT (echtes Code-Signing) |

Details: [phase-14-abschluss.md](./phase-14-abschluss.md).

## Phase 13 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Tarife | PKW Trial/Basic/Pro; LKW/Kombi geplant (nicht buchbar) |
| Zahlung | Nur Mock/Stub, HMAC-Webhooks, Idempotenz; keine echten Abbuchungen |
| Entitlements | Serverseitig; past_due/canceled sperren neue Ops |
| Kritische Ops | Abo-Ablauf/Kündigung bricht laufende Ops nicht ab |
| Mandanten | Registrierung, Einladungen, Gerätebindung, Isolation |
| Admin | Plattform-Dashboard Nutzer/Abos/Audit/Support/Datenversionen |
| UI | `/subscriptions`, `/admin` – Designsystem 10B |
| Tests | pytest **104 passed**; Build OK |
| Blocker | BLK-PAY, BLK-LEGAL |

Details: [phase-13-abschluss.md](./phase-13-abschluss.md).

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
