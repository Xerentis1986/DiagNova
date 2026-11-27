# DiagNova – Fähigkeitenkatalog (Phase 00)

**Stand:** 2026-11-27 (Europe/Vienna) – inkl. Phase 02–17 Abnahme + Phase 19 Architektur  
**Datenmodus API-UI:** Standard **simuliert** (`data_source: "simulated"`).  
**Connector OBD + Mehr-ECU:** Allowlist + Parser **simuliert getestet**; Hardwarepfad **nicht** hardwaregetestet/freigegeben.  
**Markenkatalog:** Navigationshilfe – **keine** Diagnoseabdeckung.  
**Phase 17:** Gesamtabnahme **NO-GO** für Voll-Launch; Flash/Service-Live weiterhin gesperrt.  
**Phase 19:** LKW Architektur/Flags/UI „Geplant“ – **keine** J1939-Diagnose.

## Architekturüberblick

| Komponente | Technologie | Pfad | Zustand |
|------------|-------------|------|---------|
| Web-UI | React 19, TypeScript, Vite 8, Tailwind 4, React Router, TanStack Query, Recharts | `apps/web` | MVP lauffähig (Build OK) |
| API | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT/bcrypt, ReportLab | `apps/api` | MVP lauffähig (12 Tests OK) |
| DB | PostgreSQL 16 (Compose) / SQLite für lokale Tests | Models + `001_initial` | Schema MVP |
| Connector | .NET 8, Loopback `127.0.0.1:8765`, Discovery/Auth/Transport/OBD/ECU | `apps/windows-connector` | Phase 05; siehe Testlauf |
| Shared TS | Typen Web↔API | `packages/shared-types` | MVP |
| Protocols | OBD-II + ISO-TP/UDS/Capability/Multi-ECU (Python) | `packages/diagnostic-protocols` | Unit-getestet |
| Infra | Docker Compose (postgres, api, web), nginx-Skizze | `docker-compose.yml`, `infrastructure/` | Compose hier nicht ausgeführt |

## Was funktioniert (simuliert)

| Fähigkeit | UI | API | Persistenz | Kennzeichnung |
|-----------|----|-----|------------|---------------|
| Login (admin/technician) | LoginPage | `POST /api/auth/login`, `GET /api/auth/me` | `users` | Demo-Seed |
| Dashboard | DashboardPage | `GET /api/dashboard` | Sessions-Liste | Sim-Banner |
| Fahrzeugliste (9 Demo-Marken) | VehiclesPage | `GET /api/vehicles` | `vehicles.is_example_data=true` | Beispieldaten |
| Markenübersicht DACH (38) | BrandsPage | `GET /api/catalog/brands` | statischer Katalog | Text-Fallback-Logos |
| Suche / Favoriten / Recent | BrandsPage | Favorites + Recent APIs | `user_brand_favorites`, `user_recent_selections` | lokal + Profil |
| Auswahlfluss + VIN | VehicleSelectPage | `POST /vehicles/confirm`, PATCH | vehicles + Katalog | Format-VIN |
| Theme Hell/Dunkel/System | ThemeToggle | `PATCH /api/preferences` | `users.theme_preference` | + localStorage |
| Capabilities ehrlich | Select-UI | `GET /catalog/capabilities` | — | nur MVP simuliert |
| Verbindungstatus Simulator | Diagnose | `GET /api/connection` | — | `mode=simulator` |
| DTCs stored/pending | DiagnosticsPage | `GET /api/diagnostics/{id}/dtcs` | Snapshot in Session | simulated |
| Live-PIDs + Diagramm | DiagnosticsPage | `GET /api/diagnostics/{id}/live` | — | simulated |
| Freeze-Frame / Readiness / VIN | DiagnosticsPage | Live-Payload | — | simulated |
| Sitzung starten/schließen | Diagnose | `POST /api/sessions`, `…/close` | `diagnostic_sessions` | `data_source=simulated` |
| Bericht erzeugen | ReportsPage | `POST /api/reports` | `diagnostic_reports` Snapshot+Hash | Demo/Simulation markiert |
| CSV-/PDF-Export | ReportsPage | `…/export.csv`, `…/export.pdf` | — | A4 Unicode, Demo-WM |
| Berichtsarchiv | ReportsPage | `GET /api/reports`, `…/archive`, Purge | `007_phase10` | Mandant 404 |
| Servicekatalog + Gates | ServicePage `/service` | `/api/service/*` | `service_runs` | Live deaktiviert; DPF-Off excluded |
| Geführte Diagnose | GuidedPage `/guided` | `/api/guided/*` | — | simuliert; keine Auto-Reparatur |
| Codierung / Programmierung Gates | CodingPage `/coding` | `/api/coding/*` | `coding_runs` | Flash/Schreiben DEAKTIVIERT; Identifikation lesend |
| Abos / Lizenzen (Stub) | SubscriptionsPage `/subscriptions` | `/api/subscriptions/*`, `/api/billing/*` | `subscriptions`, Geräte, Webhooks | SIMULATION – keine echte Zahlung |
| Plattform-Admin | AdminPage `/admin` | `/api/admin/*` | Audit/Abos/Nutzer | nur `is_platform_admin` |
| Geplante Module Platzhalter | PlannedPage | Dashboard `planned_modules` | — | Badge „Geplant“ (Flash Live, LKW); Abos/Admin → UI |
| LKW Architektur (Phase 19) | LkwPage `/lkw` | `/api/lkw/*` | — | Marken Nav; Caps planned; Diagnose 403 |
| Audit Login/Session/Report | — | `audit_logs` | ja | keine Passwörter |
| Health | — | `GET /health` | — | `demo_mode`, `data_source_default` |

### Seed-Marken (Beispieldaten, keine Diagnoseabdeckung)

Volkswagen, Audi, BMW, Mercedes-Benz, Škoda, Seat, Opel, Ford, Toyota — jeweils ein Demo-Modell mit Demo-VIN (`…DEMO…` / Seed-Suffix).

## Windows-Connector Phase 03 (lokal)

| Fähigkeit | Status | Hinweis |
|-----------|--------|---------|
| COM-Inventar | implementiert | `SerialPort.GetPortNames` |
| USB-Inventar | implementiert (Linux sysfs) / Windows eingeschränkt | COM deckt USB-Serial ab |
| Bluetooth gekoppelt | Win32 APIs / sonst Limitation | Fake-Injektion testbar |
| Fake-Port + AT-Init + OBD-Vektoren | simuliert getestet | `ObdSimulatorResponses` |
| OBD Init/Live/DTC/FF/RDY/VIN | simuliert getestet | `/obd/*` Allowlist |
| Clear DTC Gate | simuliert getestet | Freigabe-Token; permanent nicht löschbar |
| Mehr-ECU Inventar (OBD) | simuliert getestet | `/ecu/list` – nur beobachtete 7E8–7EF |
| Protokollkatalog / Matrix | simuliert getestet | `/protocols`, `/capability-matrix` |
| Blindscan | **deaktiviert** | `POST /ecu/blind-scan` → 403 |
| Simulator separat | ja | `POST /adapter/simulator` |
| Pairing + Origin + Loopback | simuliert getestet | siehe `docs/windows-connector-auth.md` |
| Adapter vs. Fahrzeugstatus | getrennt | Fahrzeug nach erfolgreichem `/obd/init` |
| Diagnoseprotokoll | Ringpuffer `/log` | Transport/Status/OBD |
| Delphi/Autocom | **blocked** | `docs/delphi-autocom-interface.md` |
| Vgate SPP | **blocked** / ELM prep | `docs/vgate-elm327-prep.md` |
| DoIP / J2534 / CAN-FD | **documented_prep** | `docs/j2534-doip-j1939-prep.md` |

## Was nur als Skelett / geplant existiert

| Fähigkeit | Details | Fehlend |
|-----------|---------|---------|
| Hardware-Live-OBD | Codepfad `data_source=live` für System-COM | BLK-HW Freigabe + realer Test |
| OEM ABS/Airbag/Komfort | Kategorien unavailable | BLK-OEM / Phase 06 Definitionen |
| DoIP / J2534 Live | nur Prep-Docs | BLK-HW |
| J1939 / RP1210 | Architektur Phase 19 (`documented_prep`); Diagnose aus | BLK-HW |
| nginx-Conf | Proxy `/api` + SPA + WS-Header; Plesk-Proxy-Snippet | Staging-Subdomain optional |
| Browser-Pairing-UI | Connector-API fertig | Web-UI Pairing-Seite optional später |

## Was bewusst nicht vorhanden / deaktiviert ist

| Thema | Status |
|-------|--------|
| Hardwaregetestete OBD-Kommunikation | fehlt (BLK-HW) – Parser/Simulator OK |
| Live-Clear ohne Freigabe | deaktiviert; Gate Pflicht |
| OEM-Service Live-Schreiben | Katalog Phase 11 mit Gates; Ausführung deaktiviert (BLK-OEM/HW/RELEASE) |
| Codierung / Flash | Phase 12 Gates/UI `/coding`; Identifikation lesend; Schreiben/Flash DEAKTIVIERT; J2534 Prep |
| Stellglieder | Gerüst im Servicekatalog, deaktiviert |
| DPF-Off / Abgas-Deaktivierung | ausgeschlossen |
| Mandantenfähigkeit / Kundenverwaltung | Phase 08 + 13: Registrierung/Einladungen/Geräte; serverseitige Isolation |
| Abo/Zahlungen | Phase 13 Stub/Simulation (HMAC-Webhooks); **kein** echter PSP (BLK-PAY) |
| Diagnosedaten-Import (JSON/CSV) | Phase 06 simuliert (Quarantäne/Rollback); ODX gesperrt |
| Automatische Daten-Updates | Phase 07 simuliert (Kanäle/Staging/Freigabe/Rollback); keine echten Feeds |
| Software-/Connector-Updates | Phase 14/15 Versionen 0.15.x; Signatur/Staging/Admin-Freigabe/Rollback/Busy-Gate; Prod-Auto ohne Zertifikat gesperrt |
| Sicherheit / Datenschutz / QA | Phase 15: Threat Model, Rate-Limits, Audit-Redaction, Security-Header, DSGVO-Prozess-Docs, Backup-Hinweise; UI `/security` |
| World4You / Plesk Deploy | Phase 16: Install-Doku, Compose Prod, Proxy/WS, Backup/Rollback; Live verifiziert (Smoke) |
| Gesamtabnahme / Freigabe | Phase 17: Checkliste + Go/No-Go; **kein** `freigegeben`; STOP vor Prod-Rollout |
| Markenlogos (Bilddateien) | fehlt (BLK-LOGO → Text-Fallback) |
| Herstellerdatenbanken / ODX | fehlen; **keine Lizenzen im Repo** |
| LKW | Phase 19 Architektur; Diagnose gesperrt (403) |
| Tuning | optional Phase 18; **nicht gestartet**; gesperrt |
| Produktives Deployment | Phase 16: Docs/Compose/Proxy/Backup; Live Ist unter diagnova.codekreativ.at; Redeploy nur mit Freigabe |

## Datenbank-Inventar

| Tabelle | Zweck |
|---------|-------|
| `users` | Auth, Rolle, `theme_preference`, `workshop_id`, `is_platform_admin` |
| `workshops` | Werkstattprofil, Logo, Aufbewahrungstage |
| `subscriptions` | Abo/Lizenzstatus, Entitlements (Phase 13 Stub) |
| `workshop_invitations` | Mandanten-Einladungen |
| `device_bindings` | Gerätebindung an Lizenz |
| `payment_webhook_events` | Idempotente Stub-Webhooks |
| `critical_operation_locks` | Laufende kritische Ops (kein Abrupt-Abbruch) |
| `tenant_registrations` | Selbstregistrierung Mandant |
| `customers` | Kunden mandantengebunden, Archiv/Anonymisierung |
| `customer_vehicles` | Zuordnung Kunde↔Fahrzeug |
| `work_orders` | Aufträge mit Status/Notizen/Reparatur |
| `vehicles` | Fahrzeuge inkl. VIN, Kennzeichen, `workshop_id`/`customer_id`, Archiv |
| `user_brand_favorites` | Favoriten-Marken pro User |
| `user_recent_selections` | Zuletzt verwendete Auswahlen |
| `diagnostic_sessions` | Sitzungen mit `data_source`, DTC-Snapshot, Adapter/Protokoll/km, Abort, Idempotenz |
| `session_ecu_results` / `session_dtc_results` | Geprüfte ECUs + beobachtete DTCs (Phase 09) |
| `session_measurement_samples` | Begrenzter Messwertverlauf |
| `vehicle_record_notes` | Notizen/Service/Reparatur im Zeitstrahl |
| `diagnostic_reports` | Berichtsinhalt JSON |
| `audit_logs` | Aktion/Resource/Detail + outcome/ip_hash (Phase 15) |
| `data_license_sources` | Lizenz/Attribution/Prüfdatum |
| `diag_*` | Versionierte Hersteller/Modelle/ECU/DTC/PID/Units/Service |
| `import_*` | Batches, Quarantäne, Applied-Records für Rollback |
| `update_channels` | Freigegebene Update-Quellen (HTTPS/Fixture), Rechteflag |
| `update_runs` | Update-Läufe inkl. Staging/Freigabe/Rollback |
| `update_changelogs` | Änderungsprotokoll |
| `update_job_locks` | Sperre gegen parallele Jobs |
| `service_runs` | Phase-11 Gate-/Audit-Läufe (kein Live-Schreiben) |
| `coding_runs` | Phase-12 Gate-/Identifikationsläufe (kein Flash/Schreiben) |
| `software_components` | Installierte API/Web/Connector-Versionen (Phase 14) |
| `software_update_channels` | Software-Updatekanäle (stable/production) |
| `software_update_packages` | Staging-Pakete inkl. Checksum/Signatur |
| `software_update_runs` | Install-/Rollback-Läufe + Healthcheck |
| `software_compatibility_rules` | Kompatibilitätsmatrix |
| `software_update_events` | Update-Ereignisprotokoll |

Migrationen: `001_initial` … `011_phase14`. Runtime zusätzlich `create_all` + Seed.

## API-Inventar (MVP)

| Methode | Pfad | Auth |
|---------|------|------|
| GET | `/health` | nein |
| POST | `/api/auth/login` | nein |
| GET | `/api/auth/me` | JWT |
| GET | `/api/vehicles`, `/api/vehicles/{id}` | JWT |
| POST | `/api/vehicles/confirm` | JWT |
| PATCH | `/api/vehicles/{id}` | JWT |
| GET | `/api/catalog/brands`, `…/models`, `…/variants`, `/capabilities` | JWT |
| GET/PATCH | `/api/preferences` | JWT |
| GET/PUT | `/api/favorites/brands` | JWT |
| GET | `/api/recent/selections` | JWT |
| GET | `/api/dashboard` | JWT |
| GET | `/api/connection` | JWT |
| GET | `/api/diagnostics/pids` | JWT |
| GET | `/api/diagnostics/{vehicle_id}/dtcs` | JWT |
| GET | `/api/diagnostics/{vehicle_id}/live` | JWT |
| POST | `/api/sessions?vehicle_id=` · `/api/sessions/v2` | JWT admin/technician |
| GET | `/api/sessions` · `/api/sessions/{id}` · `/api/sessions/compare` | JWT |
| POST | `/api/sessions/{id}/close` · `/abort` · `/snapshot` | JWT admin/technician |
| GET | `/api/vehicle-records/lookup` · `/{id}` · `/{id}/timeline` · `/{id}/measurements` | JWT |
| POST | `/api/vehicle-records/{id}/notes` | JWT admin/technician |
| GET | `/api/reports` | JWT (Suche/Archiv) |
| POST | `/api/reports` | JWT admin/technician |
| GET | `/api/reports/{id}` | JWT |
| GET | `/api/reports/{id}/export.csv` | JWT |
| GET | `/api/reports/{id}/export.pdf` | JWT |
| POST | `/api/reports/{id}/archive` | JWT admin/technician |
| DELETE | `/api/reports/{id}` | JWT admin |
| POST | `/api/reports/purge-expired` | JWT admin |
| GET | `/api/diagnostic-data/sources|versions|pids|ecus|coverage` | JWT |
| GET | `/api/diagnostic-data/dtcs/{code}` | JWT |
| POST | `/api/diagnostic-data/import/preview` · `preview-csv` · `preview-file` | JWT admin/technician |
| POST | `/api/diagnostic-data/import/{id}/apply` · `rollback` | JWT admin/technician |
| POST | `/api/diagnostic-data/import/odx` | JWT → 403 |
| GET | `/api/data-updates/dashboard` · `/channels` · `/runs` · `/changelog` | JWT admin |
| PATCH | `/api/data-updates/channels/{key}` | JWT admin |
| POST | `/api/data-updates/channels/{key}/run` · `/runs/{id}/approve|reject|rollback` | JWT admin |
| POST | `/api/data-updates/ssrf-check` · `/run-due` | JWT admin |
| GET | `/api/software-updates/dashboard` · `/components` · `/busy` · `/installer-docs` | JWT admin |
| POST | `/api/software-updates/packages/ingest` · `…/approve` · `…/reject` | JWT admin |
| POST | `/api/software-updates/components/{key}/rollback` · `/runs/{id}/abort` | JWT admin |
| POST | `/api/software-updates/compatibility/check` | JWT admin |
| GET | `/version` · `/health` (inkl. Komponentenversionen) | öffentlich |

**Hinweis:** WebSocket-Endpunkte sind im MVP **nicht** implementiert (README erwähnt REST + WebSocket als Zielarchitektur; aktuell nur REST).

## UI-Inventar

| Route | Seite | Inhalt |
|-------|-------|--------|
| `/login` | LoginPage | Demo-Login |
| `/` | BrandsPage | Markenkacheln, Suche, Favoriten, Recent |
| `/select/:brandSlug` | VehicleSelectPage | Wizard Marke→…→VIN |
| `/dashboard` | DashboardPage | Aktives Fahrzeug, Simulator-Status |
| `/vehicles` | VehiclesPage | Fahrzeugliste |
| `/vehicle-record` | VehicleRecordPage | Digitale Akte, Zeitstrahl, Vergleich, Messwerte |
| `/diagnostics` | DiagnosticsPage | DTCs, Live-Charts, Session |
| `/reports` | ReportsPage | Berichte, Vorschau, Archiv, PDF/CSV |
| `/ecu` | EcuPage | OBD-Mehr-ECU simuliert; kein Blindscan |
| `/service` | ServicePage | Servicekatalog + Gates |
| `/guided` | GuidedPage | Geführte Diagnose |
| `/coding` | CodingPage | Identifikation, Kompatibilitäts-/Spannungs-Gates; Flash aus |
| `/subscriptions` | SubscriptionsPage | Tarife, Stub-Zahlung, Geräte, Einladungen |
| `/admin` | AdminPage | Plattform-Admin: Nutzer, Abos, Audit, Support |
| `/diagnostic-data` | DiagnosticDataPage | Quellen, DTC-Lookup, Import-Demo |
| `/data-updates` | DataUpdatesPage | Admin: Diagnosedaten-Kanäle, Läufe, Freigabe, Rollback |
| `/software-updates` | SoftwareUpdatesPage | Admin: Software/Connector-Versionen, Signatur, Freigabe, Rollback |
| `/lkw` | LkwPage | Architektur / Caps „Geplant“ |
| `/planned/:moduleId` | PlannedPage | Flash Live, LKW-Platzhalter u. a. |
| `/security` | SecurityPage | Threat-/Backup-Hinweise (Phase 15) |
| `/workshop`, `/customers`, `/work-orders` | Workshop/Kunden | Phase 08 |

## Test-Inventar

| Suite | Datei | Abdeckung |
|-------|-------|-----------|
| API | `tests/api/test_auth_and_demo.py` | Health, Login, Seed, Simulator, Session, CSV/PDF |
| API Phase 02 | `tests/api/test_phase02_catalog.py` | Katalog, Theme, Favoriten, VIN, Capabilities |
| API Phase 06 | `tests/api/test_phase06_diagnostic_data.py` | Quellen, Lookup, Import/Quarantäne/Rollback, ODX 403 |
| API Phase 09 | `tests/api/test_phase09_vehicle_history.py` | Akte, Lookup, Abort, Vergleich, Mandant, Persistenz |
| API Phase 11 | `tests/api/test_phase11_service.py` | Servicekatalog, Gates, Guided |
| API Phase 12 | `tests/api/test_phase12_coding.py` | Identifikation, Spannungs-/VIN-Gates, Flash 403 |
| API Phase 13 | `tests/api/test_phase13_subscriptions.py` | Abos, Webhook-Stub, Kündigung, Mandanten, Admin |
| API Phase 14 | `tests/api/test_phase14_software_updates.py` | Signatur, Inkompatibilität, Busy, Install/Rollback, Zertifikat-Sperre |
| API Phase 15 | `tests/api/test_phase15_security.py` | Rate-Limit, Audit-Redaction, IDOR/RBAC, Threat-Dashboard, Origin, Headers |
| Protocols | `tests/protocols/test_dtc_pid.py` | DTC-Decode, PID-Scale |
| E2E | `apps/web/e2e/phase02.spec.ts` | Navigation, Suche, Theme, Wizard, Favoriten |
| Connector | `DiagNova.Connector.Tests` | Fake-Port, Auth, Inventar, Status – Phase 05 unverändert |
| Docker | — | in dieser Umgebung nicht ausgeführt |

## Fehlende Herstellerdaten / Lizenzen / Hardware (explizit)

1. **Hardware:** kein OBD-Adapter, kein Bluetooth-SPP-Gerät, kein Delphi/Autocom-Interface verifiziert.  
2. **Lizenzen:** keine OEM-, ODX/PDX-, Markenlogo- oder Diagnosedatenbank-Lizenzen hinterlegt.  
3. **Adapter-Docs:** Vgate vLinker MC+ Windows-SPP-Variante und Autocom-Modell unbekannt → keine Implementierung.  
4. **Zahlung/Recht:** kein PSP; DACH-Steuer/AVV offen.  
5. **Deploy-Secrets:** nur `.env.example`; keine produktiven Secrets im Repo.
