# DiagNova – Anforderungsmatrix (Phase 00)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Basis:** MVP `6adfcc4` + Phase 00; Phase 02 auf Branch `cursor/diagnova-phase-02-brands-c4de`  
**Quelle:** Master-Prompt 00 sowie Promptpaket Phasen 02–19

## Statuslegende

| Status | Bedeutung |
|--------|-----------|
| `geplant` | Anforderung erfasst, noch nicht umgesetzt |
| `implementiert` | Code vorhanden, aber noch nicht (ausreichend) getestet |
| `simuliert getestet` | Gegen Simulator/Fake-Daten und Unit-/API-Tests geprüft |
| `hardwaregetestet` | Mit realer Adapter-/Fahrzeughardware geprüft |
| `freigegeben` | Explizit für produktiven Einsatz freigegeben |

**Hinweis:** Nichts in diesem Repo ist `hardwaregetestet` oder `freigegeben`. Alle Fahrzeugdiagnosedaten im MVP sind **simuliert**.

## Blocker (übergreifend)

| ID | Blocker |
|----|---------|
| BLK-HW | Keine verifizierte OBD-/Bluetooth-/COM-Hardware in dieser Umgebung |
| BLK-OEM | Keine lizenzierten OEM-/ODX-/Herstellerdaten |
| BLK-ADAPTER | Delphi/Autocom-Modell und Vgate-SPP-Variante unklar / undokumentiert |
| BLK-DOTNET | .NET 8 SDK in Cloud-Agent-Umgebung nicht verfügbar → Connector-Build hier nicht ausführbar |
| BLK-DOCKER | Docker Engine in dieser Cloud-Umgebung nicht verfügbar → Compose-Build hier nicht ausgeführt |
| BLK-PAY | Zahlungsanbieter erst nach Zustimmung |
| BLK-LEGAL | Rechtliche Prüfung DACH (Abo/Rechnung/DSGVO-AV) offen |
| BLK-DEPLOY | Produktives Deployment / Fahrzeug-Schreibtests nur nach Freigabe |
| BLK-LOGO | Markenlogo-Nutzungsrechte ungeklärt → nur Text-Fallback-Kacheln |

---

## Matrix

| ID | Anforderung | Phase | Status | Quelle / Code | Tests | Blocker |
|----|-------------|-------|--------|---------------|-------|---------|
| REQ-00-INV | Bestandsaufnahme Code/DB/API/UI/Connector/Docker/Tests | 00 | `implementiert` | dieses Dokument, `docs/capabilities.md`, `docs/phase-status.md` | Baseline 2026-11-27 | — |
| REQ-00-MAT | Zentrale Anforderungsmatrix mit Phasen-Zuordnung | 00 | `implementiert` | `docs/requirements.md` | Review | — |
| REQ-00-PROG | Fortschrittspflege `DIAGNOVA_PROGRESS.md` | 00 | `implementiert` | Repo-Root | Review | — |
| REQ-01-MONO | Monorepo Web/API/Connector/Packages/Docker | 01 (erledigt) | `simuliert getestet` | `apps/*`, `packages/*`, `docker-compose.yml` | API 12 passed; Web build | BLK-DOCKER, BLK-DOTNET |
| REQ-01-AUTH | Login, bcrypt, JWT, Rollen | 01 | `simuliert getestet` | `apps/api/app/api/routes/auth.py`, `core/security.py` | `test_login_*` | — |
| REQ-01-DEMO | Demo-Modus + `data_source: simulated` Kennzeichnung | 01 | `simuliert getestet` | Simulator, `SimBanner`, Health | `test_health`, `test_connection_is_simulator` | — |
| REQ-01-VEH | Seed-Fahrzeuge (Beispieldaten) | 01 | `simuliert getestet` | `apps/api/app/db/seed.py` | `test_demo_vehicles_seeded` | Keine echte Markenabdeckung |
| REQ-01-DTC | Simulierte DTCs stored/pending | 01 | `simuliert getestet` | `services/simulator.py` | `test_simulator_dtcs_and_live` | BLK-HW |
| REQ-01-LIVE | Simulierte Live-PIDs, Freeze-Frame, Readiness, VIN | 01 | `simuliert getestet` | Simulator + `diagnova_protocols` | API + Protocol-Tests | BLK-HW |
| REQ-01-SESS | Diagnosesitzungen speichern/schließen | 01 | `simuliert getestet` | `routes/diagnostics.py` | `test_session_and_report_export` | — |
| REQ-01-RPT | Berichte CSV/PDF (simulierter Inhalt) | 01 | `simuliert getestet` | `services/reports.py` | Export-Tests | — |
| REQ-01-CONN-SKEL | Windows-Connector Skelett + Stub-Adapter | 01/03 | `implementiert` | `apps/windows-connector` | Quellcode-Review; Build hier nicht | BLK-DOTNET, BLK-HW |
| REQ-01-AUDIT | Audit-Log Login/Session/Report | 01 | `implementiert` | `services/audit.py` | indirekt über API-Flows | — |
| REQ-02-TILES | Marken-Kacheln, Logos, Suche, Favoriten | 02 | `simuliert getestet` | `BrandsPage`, Text-Fallback, Favoriten-API | API + E2E | BLK-LOGO |
| REQ-02-SELECT | Marke→Modell→Baureihe→Motor→Bestätigen | 02 | `simuliert getestet` | `VehicleSelectPage`, `POST /vehicles/confirm` | API + E2E | — |
| REQ-02-THEME | Hell/Dunkel/System, Persistenz | 02 | `simuliert getestet` | ThemeProvider + `users.theme_preference` | API + E2E | — |
| REQ-02-VIN | VIN-Erkennung + manuelle Korrektur | 02 | `simuliert getestet` | Formatprüfung + PATCH; keine Hardware-VIN | API | BLK-HW |
| REQ-02-CAP | Verfügbare Funktionen pro Fahrzeug anzeigen | 02 | `simuliert getestet` | `/catalog/capabilities` (MVP simuliert vs. geplant) | API + UI | BLK-OEM |
| REQ-02-A11Y | Kontrast, Tastatur, mobil | 02 | `implementiert` | Focus-Styles, Labels, responsive Grid | E2E Desktop | manuelle Kontrastprüfung offen |
| REQ-03-BT | Bluetooth-Geräteerkennung / SPP | 03 | `geplant` | Connector-Skelett | — | BLK-HW, BLK-ADAPTER |
| REQ-03-COM | COM-/USB-Inventar, exklusiver Portzugriff | 03 | `geplant` | — | Fake-Port geplant | BLK-DOTNET |
| REQ-03-PAIR | Browser↔Connector Auth, Loopback, Origin | 03 | `implementiert` (Skelett) | `LocalAuthService`, `docs/windows-connector-auth.md` | nicht automatisiert | Pairing-Flow unvollständig |
| REQ-03-SEP | Adapter- vs. Fahrzeugverbindungsstatus getrennt | 03 | `geplant` | nur Simulator-Status | — | — |
| REQ-04-INIT | Adapter-Init + Protokollerkennung (echt) | 04 | `geplant` | nur Simulator | — | BLK-HW |
| REQ-04-PID | Supported-PID-Bitmap, Live mit Einheiten | 04 | `geplant` (Parser-Teil MVP) | `pids.py` + Simulator | Unit-Tests Parser | BLK-HW |
| REQ-04-DTC-R | Stored/pending/permanent DTCs echt | 04 | `geplant` | Decoder vorhanden | Unit-Tests Decoder | BLK-HW |
| REQ-04-FF | Freeze-Frame echt | 04 | `geplant` | Simulator liefert Fake | — | BLK-HW |
| REQ-04-RDY | Readiness echt | 04 | `geplant` | Simulator Fake | — | BLK-HW |
| REQ-04-CLR | DTC-Löschung mit Freigabe/Audit | 04 | `geplant` | **nicht** implementiert (bewusst) | — | BLK-HW + Freigabe |
| REQ-04-MULTI | Mehrere ECU-Antworten getrennt | 04 | `geplant` | — | — | BLK-HW |
| REQ-05-PROTO | Multiprotokoll (ISO/KWP/CAN/UDS/DoIP/…) | 05 | `geplant` | Package nur OBD-II Basis | — | BLK-HW, Spezifikationen |
| REQ-05-ECU | Steuergeräteübersicht mit verifizierten Adressen | 05 | `geplant` | UI „Geplant“ | — | BLK-OEM |
| REQ-05-CAP-MAT | Capability-Matrix pro Adapter | 05 | `geplant` | — | — | BLK-ADAPTER |
| REQ-06-MODEL | Versioniertes Diagnosedatenmodell | 06 | `geplant` | nur Demo-Seed-Fahrzeuge | — | BLK-OEM |
| REQ-06-IMPORT | JSON/CSV-Import, Quarantäne, Rollback | 06 | `geplant` | — | — | — |
| REQ-06-ODX | ODX/PDX nur mit Lizenz | 06 | `geplant` | — | — | BLK-OEM |
| REQ-06-LIC | Lizenzherkunft / Attribution | 06 | `geplant` | — | — | BLK-OEM |
| REQ-07-SCHED | Scheduler Diagnosedaten-Updates | 07 | `geplant` | — | — | Quellenrechte |
| REQ-07-SAFE | SSRF-/Integritäts-/Staging-Schutz | 07 | `geplant` | — | — | — |
| REQ-07-PUB | Atomare Veröffentlichung + Rollback | 07 | `geplant` | — | — | — |
| REQ-08-WS | Werkstattprofil, Rollen, Kunden | 08 | `geplant` | nur User-Rollen ohne Mandant | — | — |
| REQ-08-CUST | Kunden/Fahrzeuge CRUD, Dubletten | 08 | `geplant` | Fahrzeuge read-only Seed | — | — |
| REQ-08-TENANT | Mandanten-ID serverseitig | 08 | `geplant` | kein Multi-Tenant | — | — |
| REQ-08-DSGVO | Export/Löschung/Aufbewahrung | 08 | `geplant` | — | — | BLK-LEGAL |
| REQ-09-HIST | Fahrzeugakte / Zeitstrahl | 09 | `geplant` | Sessions-Liste rudimentär | — | — |
| REQ-09-CMP | Vorher/Nachher DTC-Vergleich | 09 | `geplant` | — | — | — |
| REQ-09-TREND | Messwertverlauf begrenzt speichern | 09 | `geplant` | — | — | — |
| REQ-10-PDF | A4-PDF Werkstattlayout, Wasserzeichen Demo | 10 | `geplant` (MVP-PDF rudimentär) | `report_to_pdf` ReportLab | Export-Test | Layout/Archiv fehlen |
| REQ-10-ARCH | Archiv, Suche, unveränderlicher Snapshot | 10 | `geplant` | Reports in DB | — | — |
| REQ-10-CSV | CSV-Export | 10 / 01 | `simuliert getestet` | Export-Endpoint | API-Test | — |
| REQ-11-SVC | Servicekatalog (Öl, EPB, DPF, …) | 11 | `geplant` | UI „Geplant“ | — | BLK-OEM; DPF-Off ausgeschlossen |
| REQ-11-GUIDED | Geführte Diagnose | 11 | `geplant` | — | — | BLK-OEM |
| REQ-11-ACT | Stellgliedtests | 11 | `geplant` | UI „Geplant“ | — | Freigabe + Hardware |
| REQ-12-CODE | Steuergerätecodierung | 12 | `geplant` | UI „Geplant“ | — | BLK-OEM, Freigabe |
| REQ-12-FLASH | Programmierung / J2534 | 12 | `geplant` | UI „Geplant“ | — | BLK-OEM, Hardware, Freigabe |
| REQ-13-SUB | Abos, Entitlements, Tarife | 13 | `geplant` | — | — | BLK-PAY, BLK-LEGAL |
| REQ-13-ADMIN | Admin-Dashboard Nutzer/Abo/Audit | 13 | `geplant` | — | — | — |
| REQ-14-UPD | Software-/Connector-Updates, Signatur | 14 | `geplant` | Version API `0.1.0` hardcodiert | — | Zertifikat |
| REQ-14-MIG | DB-Migrationen mit Backup-Plan | 14 | `geplant` | Alembic `001_initial` vorhanden | — | — |
| REQ-15-SEC | Threat Model, Rate Limits, IDOR, CSRF | 15 | `geplant` (Basis Auth vorhanden) | bcrypt/JWT/CORS/Audit | Auth-Tests | — |
| REQ-15-BACKUP | Backup/Restore, Monitoring | 15 | `geplant` | — | — | — |
| REQ-15-QA | E2E, Last, Security-Regression | 15 | `geplant` | nur Unit/API | keine E2E | — |
| REQ-16-DEP | World4You Ubuntu/Plesk Deploy | 16 | `geplant` (Infra vorbereitet außerhalb Repo) | Compose + nginx-Skizze | Compose hier nicht | BLK-DEPLOY, BLK-DOCKER |
| REQ-16-TLS | HTTPS Reverse Proxy, WS | 16 | `geplant` | nginx nur HTTP-Skizze | — | DNS/TLS |
| REQ-17-ACC | Gesamtabnahme, Abdeckungsmatrix, Go/No-Go | 17 | `geplant` | — | — | alle vorgelagerten Blocker |
| REQ-18-TUNE | Optionales Chiptuning (gesperrt) | 18 | `geplant` | bewusst nicht aktiv | — | Rechtlich/technisch |
| REQ-19-LKW | LKW/J1939/RP1210 | 19 | `geplant` | — | — | Hardware 24 V, Spezifikationen |

---

## Quer-Themen (explizit im Prompt 00 genannt)

| Thema | IDs | Bemerkung |
|-------|-----|-----------|
| Diagnosevergleich | REQ-09-CMP | Phase 09 |
| Live-Daten | REQ-01-LIVE, REQ-04-PID | MVP simuliert; echt Phase 04 |
| Freeze-Frame | REQ-01-LIVE, REQ-04-FF | |
| Readiness | REQ-01-LIVE, REQ-04-RDY | |
| DTC-Löschung | REQ-04-CLR | deaktiviert bis Freigabe |
| CSV | REQ-10-CSV | MVP vorhanden |
| Audit | REQ-01-AUDIT, REQ-15-SEC | Basis vorhanden |
| Backups | REQ-15-BACKUP | geplant |
| Lizenzherkunft | REQ-06-LIC | geplant; keine OEM-Daten im Repo |

## Nicht enthalten / ausgeschlossen

- DPF-Off / Abgasreinigung deaktivieren
- Blindes Scannen unbekannter Netze
- Kopieren von Bosch/Gutmann/Delphi-Daten
- Produktive Fahrzeug-Schreibtests ohne Zustimmung
- Erfundene kommerzielle Nutzungsrechte
