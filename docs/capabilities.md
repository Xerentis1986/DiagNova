# DiagNova – Fähigkeitenkatalog (Phase 00)

**Stand:** 2026-11-27 (Europe/Vienna) – inkl. Phase 02 + 03  
**Datenmodus MVP/API:** ausschließlich **simuliert** (`data_source: "simulated"`).  
**Echte Fahrzeugkommunikation:** **nicht** vorhanden (Phase 03: nur Inventar/Transport/AT-Prep).  
**Markenkatalog:** Navigationshilfe – **keine** Diagnoseabdeckung.

## Architekturüberblick

| Komponente | Technologie | Pfad | Zustand |
|------------|-------------|------|---------|
| Web-UI | React 19, TypeScript, Vite 8, Tailwind 4, React Router, TanStack Query, Recharts | `apps/web` | MVP lauffähig (Build OK) |
| API | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT/bcrypt, ReportLab | `apps/api` | MVP lauffähig (12 Tests OK) |
| DB | PostgreSQL 16 (Compose) / SQLite für lokale Tests | Models + `001_initial` | Schema MVP |
| Connector | .NET 8, Loopback `127.0.0.1:8765`, Discovery/Auth/Transport | `apps/windows-connector` | Phase 03; `dotnet test` 14 passed |
| Shared TS | Typen Web↔API | `packages/shared-types` | MVP |
| Protocols | OBD-II DTC-/PID-Parser (Python) | `packages/diagnostic-protocols` | Unit-getestet |
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
| Bericht erzeugen | ReportsPage | `POST /api/reports` | `diagnostic_reports` | Inhalt markiert |
| CSV-/PDF-Export | ReportsPage | `…/export.csv`, `…/export.pdf` | — | Text enthält Hinweis |
| Geplante Module Platzhalter | PlannedPage | Dashboard `planned_modules` | — | Badge „Geplant“ |
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
| Fake-Port + AT-Init | simuliert getestet | keine OBD-Services |
| Simulator separat | ja | `POST /adapter/simulator` |
| Pairing + Origin + Loopback | simuliert getestet | siehe `docs/windows-connector-auth.md` |
| Adapter vs. Fahrzeugstatus | getrennt | Fahrzeug in P03 immer `false` |
| Diagnoseprotokoll | Ringpuffer `/log` | Transport/Status |
| Delphi/Autocom | **blocked** | `docs/delphi-autocom-interface.md` |
| Vgate SPP | **blocked** / ELM prep | `docs/vgate-elm327-prep.md` |

## Was nur als Skelett / geplant existiert

| Fähigkeit | Details | Fehlend |
|-----------|---------|---------|
| Echte OBD über Connector | Transport vorbereitet | Fahrzeugbefehle → Phase 04; Allowlist |
| Protocol-Package | DTC-Decode, PID-Scale für gängige Mode-01-PIDs | Multiprotokoll, UDS/DoIP, J1939 |
| nginx-Conf | Proxy `/api` + SPA | TLS, WebSocket, Plesk-Integration |
| Browser-Pairing-UI | Connector-API fertig | Web-UI Pairing-Seite optional später |

## Was bewusst nicht vorhanden / deaktiviert ist

| Thema | Status |
|-------|--------|
| Echte OBD-/Bluetooth-Kommunikation | fehlt (BLK-HW) |
| DTC löschen | nicht implementiert |
| OEM-Service / Codierung / Flash / Stellglieder | UI „Geplant“, keine Logik |
| Mandantenfähigkeit / Kundenverwaltung | fehlt |
| Abo/Zahlungen | fehlt |
| Diagnosedaten-Import/Updates | fehlt |
| Markenlogos (Bilddateien) | fehlt (BLK-LOGO → Text-Fallback) |
| Herstellerdatenbanken / ODX | fehlen; **keine Lizenzen im Repo** |
| LKW / Tuning | optional später; gesperrt |
| Produktives Deployment | nicht Teil Phase 00 |

## Datenbank-Inventar

| Tabelle | Zweck |
|---------|-------|
| `users` | Auth, Rolle, `theme_preference` |
| `vehicles` | Fahrzeuge inkl. VIN, Kennzeichen, `series`, `odometer_km`, Katalog-IDs |
| `user_brand_favorites` | Favoriten-Marken pro User |
| `user_recent_selections` | Zuletzt verwendete Auswahlen |
| `diagnostic_sessions` | Sitzungen mit `data_source`, DTC-Snapshot JSON |
| `diagnostic_reports` | Berichtsinhalt JSON |
| `audit_logs` | Aktion/Resource/Detail |

Migrationen: `001_initial`, `002_phase02`. Runtime zusätzlich `create_all` + Seed.

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
| POST | `/api/sessions?vehicle_id=` | JWT admin/technician |
| GET | `/api/sessions` | JWT |
| POST | `/api/sessions/{id}/close` | JWT admin/technician |
| POST | `/api/reports` | JWT admin/technician |
| GET | `/api/reports/{id}` | JWT |
| GET | `/api/reports/{id}/export.csv` | JWT |
| GET | `/api/reports/{id}/export.pdf` | JWT |

**Hinweis:** WebSocket-Endpunkte sind im MVP **nicht** implementiert (README erwähnt REST + WebSocket als Zielarchitektur; aktuell nur REST).

## UI-Inventar

| Route | Seite | Inhalt |
|-------|-------|--------|
| `/login` | LoginPage | Demo-Login |
| `/` | BrandsPage | Markenkacheln, Suche, Favoriten, Recent |
| `/select/:brandSlug` | VehicleSelectPage | Wizard Marke→…→VIN |
| `/dashboard` | DashboardPage | Aktives Fahrzeug, Simulator-Status |
| `/vehicles` | VehiclesPage | Fahrzeugliste |
| `/diagnostics` | DiagnosticsPage | DTCs, Live-Charts, Session |
| `/reports` | ReportsPage | Berichte / Export |
| `/planned/:moduleId` | PlannedPage | ecu, service, coding, … |

## Test-Inventar

| Suite | Datei | Abdeckung |
|-------|-------|-----------|
| API | `tests/api/test_auth_and_demo.py` | Health, Login, Seed, Simulator, Session, CSV/PDF |
| API Phase 02 | `tests/api/test_phase02_catalog.py` | Katalog, Theme, Favoriten, VIN, Capabilities |
| Protocols | `tests/protocols/test_dtc_pid.py` | DTC-Decode, PID-Scale |
| E2E | `apps/web/e2e/phase02.spec.ts` | Navigation, Suche, Theme, Wizard, Favoriten |
| Connector | `DiagNova.Connector.Tests` | Fake-Port, Auth, Inventar, Status – 14 passed |
| Docker | — | in dieser Umgebung nicht ausgeführt |

## Fehlende Herstellerdaten / Lizenzen / Hardware (explizit)

1. **Hardware:** kein OBD-Adapter, kein Bluetooth-SPP-Gerät, kein Delphi/Autocom-Interface verifiziert.  
2. **Lizenzen:** keine OEM-, ODX/PDX-, Markenlogo- oder Diagnosedatenbank-Lizenzen hinterlegt.  
3. **Adapter-Docs:** Vgate vLinker MC+ Windows-SPP-Variante und Autocom-Modell unbekannt → keine Implementierung.  
4. **Zahlung/Recht:** kein PSP; DACH-Steuer/AVV offen.  
5. **Deploy-Secrets:** nur `.env.example`; keine produktiven Secrets im Repo.
