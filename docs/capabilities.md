# DiagNova – Fähigkeitenkatalog (Phase 00)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Datenmodus MVP:** ausschließlich **simuliert** (`data_source: "simulated"`).  
**Echte Fahrzeugkommunikation:** **nicht** vorhanden.

## Architekturüberblick

| Komponente | Technologie | Pfad | Zustand |
|------------|-------------|------|---------|
| Web-UI | React 19, TypeScript, Vite 8, Tailwind 4, React Router, TanStack Query, Recharts | `apps/web` | MVP lauffähig (Build OK) |
| API | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic, JWT/bcrypt, ReportLab | `apps/api` | MVP lauffähig (12 Tests OK) |
| DB | PostgreSQL 16 (Compose) / SQLite für lokale Tests | Models + `001_initial` | Schema MVP |
| Connector | .NET 8, Loopback `127.0.0.1:8765`, Stub-Adapter | `apps/windows-connector` | Skelett; Build hier nicht verifiziert |
| Shared TS | Typen Web↔API | `packages/shared-types` | MVP |
| Protocols | OBD-II DTC-/PID-Parser (Python) | `packages/diagnostic-protocols` | Unit-getestet |
| Infra | Docker Compose (postgres, api, web), nginx-Skizze | `docker-compose.yml`, `infrastructure/` | Compose hier nicht ausgeführt |

## Was funktioniert (simuliert)

| Fähigkeit | UI | API | Persistenz | Kennzeichnung |
|-----------|----|-----|------------|---------------|
| Login (admin/technician) | LoginPage | `POST /api/auth/login`, `GET /api/auth/me` | `users` | Demo-Seed |
| Dashboard | DashboardPage | `GET /api/dashboard` | Sessions-Liste | Sim-Banner |
| Fahrzeugliste (9 Demo-Marken) | VehiclesPage | `GET /api/vehicles` | `vehicles.is_example_data=true` | Beispieldaten |
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

## Was nur als Skelett existiert

| Fähigkeit | Details | Fehlend |
|-----------|---------|---------|
| Windows Connector | `IDiagnosticAdapter`, `StubDiagnosticAdapter`, `LocalAuthService`, Health/Status auf Loopback | Bluetooth/COM, Pairing-UI, echte Adapter, Allowlist-Fahrzeugbefehle |
| Protocol-Package | DTC-Decode, PID-Scale für gängige Mode-01-PIDs | Transport, Multiprotokoll, UDS/DoIP, J1939 |
| nginx-Conf | Proxy `/api` + SPA | TLS, WebSocket, Plesk-Integration |

## Was bewusst nicht vorhanden / deaktiviert ist

| Thema | Status |
|-------|--------|
| Echte OBD-/Bluetooth-Kommunikation | fehlt (BLK-HW) |
| DTC löschen | nicht implementiert |
| OEM-Service / Codierung / Flash / Stellglieder | UI „Geplant“, keine Logik |
| Mandantenfähigkeit / Kundenverwaltung | fehlt |
| Abo/Zahlungen | fehlt |
| Diagnosedaten-Import/Updates | fehlt |
| Marken-Kacheln / Theme-Switch / Favoriten | fehlt |
| Herstellerdatenbanken / ODX | fehlen; **keine Lizenzen im Repo** |
| LKW / Tuning | optional später; gesperrt |
| Produktives Deployment | nicht Teil Phase 00 |

## Datenbank-Inventar

| Tabelle | Zweck |
|---------|-------|
| `users` | Auth, Rolle (`admin`/`technician`/`viewer`) |
| `vehicles` | Demo-Fahrzeuge inkl. VIN, Kennzeichen, `is_example_data` |
| `diagnostic_sessions` | Sitzungen mit `data_source`, DTC-Snapshot JSON |
| `diagnostic_reports` | Berichtsinhalt JSON |
| `audit_logs` | Aktion/Resource/Detail |

Migration: `apps/api/alembic/versions/001_initial.py`. Runtime erstellt Tabellen zusätzlich via `Base.metadata.create_all` + Seed.

## API-Inventar (MVP)

| Methode | Pfad | Auth |
|---------|------|------|
| GET | `/health` | nein |
| POST | `/api/auth/login` | nein |
| GET | `/api/auth/me` | JWT |
| GET | `/api/vehicles`, `/api/vehicles/{id}` | JWT |
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
| `/` | DashboardPage | Aktives Fahrzeug, Simulator-Status, letzte Sitzungen |
| `/vehicles` | VehiclesPage | Liste Demo-Fahrzeuge |
| `/diagnostics` | DiagnosticsPage | DTCs, Live-Charts, Session |
| `/reports` | ReportsPage | Berichte / Export |
| `/planned/:moduleId` | PlannedPage | ecu, service, coding, … |

## Test-Inventar

| Suite | Datei | Abdeckung |
|-------|-------|-----------|
| API | `tests/api/test_auth_and_demo.py` | Health, Login, Seed, Simulator, Session, CSV/PDF, Connection |
| Protocols | `tests/protocols/test_dtc_pid.py` | DTC-Decode, PID-Scale |
| Frontend | — | kein Unit-/E2E-Test; Build als Smoke |
| Connector | — | keine automatisierten Tests |
| Docker | — | in dieser Umgebung nicht ausgeführt |

## Fehlende Herstellerdaten / Lizenzen / Hardware (explizit)

1. **Hardware:** kein OBD-Adapter, kein Bluetooth-SPP-Gerät, kein Delphi/Autocom-Interface verifiziert.  
2. **Lizenzen:** keine OEM-, ODX/PDX-, Markenlogo- oder Diagnosedatenbank-Lizenzen hinterlegt.  
3. **Adapter-Docs:** Vgate vLinker MC+ Windows-SPP-Variante und Autocom-Modell unbekannt → keine Implementierung.  
4. **Zahlung/Recht:** kein PSP; DACH-Steuer/AVV offen.  
5. **Deploy-Secrets:** nur `.env.example`; keine produktiven Secrets im Repo.
