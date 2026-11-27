# DiagNova – Capabilities (Bestandsaufnahme Phase 00)

Stand: 2026-11-27 (Europe/Vienna)  
Codebasis: `cursor/diagnova-phase-ab-mvp-bf17` (Phase A/B MVP, PR #1)

## Architekturüberblick

| Schicht | Technologie | Pfad | Zustand |
|---------|-------------|------|---------|
| Web-UI | React 19, TypeScript, Vite 8, Tailwind 4, React Router, TanStack Query, Recharts | `apps/web/` | MVP Demo, Dark UI, DE |
| API | FastAPI, SQLAlchemy 2, Alembic, Pydantic, JWT/bcrypt | `apps/api/` | MVP, Demo-Mode default |
| DB | PostgreSQL 16 (Compose); Tests: SQLite in-memory | Modelle in `apps/api/app/models/` | Migration `001_initial` |
| Protokolle | Python-Paket Mode-01/03 Subset | `packages/diagnostic-protocols/` | Parser, keine Transportschicht |
| Shared Types | TypeScript Contracts | `packages/shared-types/` | MVP-Typen inkl. `DataSource` |
| Connector | .NET 8 Minimal API, Loopback `:8765` | `apps/windows-connector/` | Stub, keine Fahrzeugbefehle |
| Infra | Docker Compose + nginx Proxy-Conf | `docker-compose.yml`, `infrastructure/` | Compose hier nicht gebaut |

## Was funktioniert (simuliert / lokal)

### Authentifizierung & Rollen
- Login (`POST /api/auth/login`), `/api/auth/me`
- Rollen: `admin`, `technician`, `viewer` (Seed: Admin + Techniker)
- bcrypt-Passwort-Hashes, JWT Bearer
- Audit bei Login

### Fahrzeuge
- 9 Seed-Beispielfahrzeuge (VW, Audi, BMW, Mercedes-Benz, Škoda, Seat, Opel, Ford, Toyota)
- Felder: make, model, year, vin, license_plate, engine, fuel_type, `is_example_data=true`
- API: Liste + Detail (read-only); UI: Fahrzeuge-Seite
- **Keine** echte Markenabdeckung / Diagnosekompetenz

### Diagnose (ausschließlich Simulator)
- Connection-Status: Mode `simulator`, `data_source: simulated`
- DTCs stored/pending (deterministisch pro vehicle_id)
- Live-PIDs: Last, Kühlmittel, RPM, Speed, Ansaugtemp, MAF, Throttle, Tank, Spannung
- Readiness + Freeze-Frame (simuliert)
- Sessions: starten/schließen mit DTC-Snapshot; Reports JSON + CSV + PDF
- UI-Banner „Simulierte Daten“ (`SimBanner`)

### Berichte
- Speichern, Abruf, CSV- und PDF-Export
- Disclaimer: simulierte Daten
- Kein Werkstatt-Branding, kein Archiv-Suchindex

### Windows-Connector
- `IDiagnosticAdapter` + `StubDiagnosticAdapter`
- Localhost-Auth Middleware; Health/Status ohne Fahrzeug-I/O
- Dokumentation: `docs/windows-connector-auth.md`

### Sicherheit (V1-Minimum)
- Keine Secrets im Repo (`.env.example` nur Platzhalter)
- CORS konfigurierbar; Input-Validation Pydantic
- Keine Remote-Rohbefehle an Fahrzeuge

## Was fehlt / deaktiviert

| Bereich | Status |
|---------|--------|
| Echte OBD-/Adapter-Kommunikation | **nicht vorhanden** |
| Bluetooth/COM/USB-Inventar | **nicht vorhanden** |
| Multiprotokoll (UDS, DoIP, CAN FD, …) | **nicht vorhanden** |
| OEM-/ODX-Diagnosedaten | **fehlende Lizenzen/Quellen** |
| Mandanten / Werkstattkunden | **nicht vorhanden** |
| Marken-Kacheln / Theme Hell | **nicht vorhanden** |
| DTC-Löschung / Service / Codierung / Flash | **UI „Geplant“, Backend fehlt** |
| Abos / Zahlungen / Auto-Updates | **nicht vorhanden** |
| World4You Produktionsdeploy | **kein Deploy in Phase 00** |
| Hardwaregetestete Funktionen | **0** |

## Datenbankschema (Ist)

Tabellen: `users`, `vehicles`, `diagnostic_sessions`, `diagnostic_reports`, `audit_logs`  
Kein Tenant, kein Customer, kein ECU-Katalog, keine Import-Versionierung.

## API-Oberfläche (Ist)

| Methode | Pfad | Bemerkung |
|---------|------|-----------|
| GET | `/health` | Demo/simulated Kennzeichnung |
| POST | `/api/auth/login` | |
| GET | `/api/auth/me` | |
| GET | `/api/dashboard` | inkl. planned_modules |
| GET | `/api/vehicles`, `/api/vehicles/{id}` | |
| GET | `/api/connection` | Simulator |
| GET | `/api/diagnostics/pids` | |
| GET | `/api/diagnostics/{id}/dtcs` | simulated |
| GET | `/api/diagnostics/{id}/live` | simulated |
| POST/GET | `/api/sessions`, close | |
| POST/GET | `/api/reports`, export.csv/pdf | |

## UI-Routen (Ist)

`/login`, `/` Dashboard, `/vehicles`, `/diagnostics`, `/reports`, `/planned/:moduleId` (ecu/service/coding)

## Test- & Build-Lage (Phase 00 Ausführung)

| Check | Ergebnis | Umgebung |
|-------|----------|----------|
| `pytest tests -q` | **12 passed**, 13 warnings | Python 3.12 venv, SQLite in-memory |
| `npm run build` (apps/web) | **Erfolg** | Node 22.23.4 / npm 10.9.9 |
| `docker compose` | **nicht ausgeführt** | Docker nicht installiert |
| .NET Connector Build | **nicht ausgeführt** | `dotnet` nicht installiert |
| Hardware / Fahrzeug | **nicht getestet** | keine Hardware |

## Simuliert vs. echt

| Signal | Verwendung |
|--------|------------|
| `data_source: "simulated"` | API-Antworten, Sessions, Reports, Connector |
| `demo_mode` | Settings / Health |
| `is_example_data` | Seed-Fahrzeuge |
| UI `SimBanner` | Dauerhafte Kennzeichnung |
| `live` | Typ vorgesehen, **kein** Live-Pfad implementiert |
