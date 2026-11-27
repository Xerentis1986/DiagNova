# DiagNova

Professionelle webbasierte Mehrmarken-Fahrzeugdiagnose für Werkstätten – **MVP Phase A/B** mit **simuliertem** OBD.

> **Wichtig:** Es findet **keine** echte Fahrzeugkommunikation statt. Alle DTCs, Live-PIDs, VIN- und Freeze-Frame-Daten sind **simuliert**.

## Stack

- **Web:** React, TypeScript, Vite, Tailwind, React Router, TanStack Query, Recharts (Deutsch, Dark Mode)
- **API:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL
- **Connector:** .NET 8 Skelett (`IDiagnosticAdapter` + Stub, ohne Fahrzeugbefehle)
- **Infra:** Docker Compose (api, web, postgres)

## Schnellstart mit Docker

Voraussetzungen: Docker Desktop / Docker Engine + Compose.

```bash
cp .env.example .env
docker compose up --build
```

- Web: http://localhost:3000  
- API: http://localhost:8000  
- Health: http://localhost:8000/health  
- OpenAPI: http://localhost:8000/docs  

### Demo-Login

| Rolle | E-Mail | Passwort |
|-------|--------|----------|
| Admin | `admin@example.com` | `AdminDemo123!` |
| Techniker | `tech@example.com` | `TechDemo123!` |

## Lokale Entwicklung (ohne Docker)

### API

```bash
cd apps/api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
pip install ../../packages/diagnostic-protocols

# SQLite für schnelle lokale Tests:
set DATABASE_URL=sqlite:///./diagnova.db   # Windows CMD
# export DATABASE_URL=sqlite:///./diagnova.db  # bash

uvicorn app.main:app --reload --port 8000
```

### Web

```bash
cd apps/web
npm install
npm run dev
```

Öffne http://localhost:5173 (Vite proxyt `/api` → `:8000`).

### Windows Connector (Skelett)

Siehe `apps/windows-connector/README.md` und `docs/windows-connector-auth.md`.  
Benötigt .NET 8 SDK auf Windows. **Keine** echten Fahrzeugbefehle.

## Tests

```bash
cd apps/api
pip install -r requirements.txt
pip install ../../packages/diagnostic-protocols
pytest ../../tests -q
```

Abgedeckt: Auth/Demo-Modus, Seed-Fahrzeuge, Simulator DTCs/Live, Bericht CSV/PDF, DTC-/PID-Parser.

## Dokumentation

- Fortschritt: [`DIAGNOVA_PROGRESS.md`](DIAGNOVA_PROGRESS.md)
- Anforderungsmatrix: [`docs/requirements.md`](docs/requirements.md)
- Fähigkeitenkatalog: [`docs/capabilities.md`](docs/capabilities.md)
- Phasenstatus + Baseline-Tests: [`docs/phase-status.md`](docs/phase-status.md)
- World4You / Plesk: [`docs/world4you-plesk-install.md`](docs/world4you-plesk-install.md)
- Deploy-Checkliste: [`docs/phase-16-deploy-checklist.md`](docs/phase-16-deploy-checklist.md)

### Produktion (Kurz)

```bash
# Nur auf dem Server, mit bestehender .env (chmod 600) – keine Secrets committen
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

Live (Ist): https://diagnova.codekreativ.at/ – Redeploy nur mit Betreiberfreigabe.

## Monorepo-Struktur

```
diagnova/
├── apps/web/
├── apps/api/
├── apps/windows-connector/
├── packages/shared-types/
├── packages/diagnostic-protocols/
├── infrastructure/docker/
├── infrastructure/nginx/
├── docs/
├── tests/
├── docker-compose.yml
├── DIAGNOVA_PROGRESS.md
├── .env.example
└── README.md
```


## Sicherheit (V1-Minimum)

- Keine Secrets im Repo (nur `.env.example`)
- Passwort-Hashes mit bcrypt
- JWT-Auth + Rollen (`admin` / `technician` / `viewer`)
- Pydantic-Input-Validation
- Audit-Log bei Login, Sitzung, Bericht

## Geplante Module

Stellglieddiagnose und Flash-Live bleiben in der UI als **Geplant**. Steuergeräte, Service, Guided und Codierung/Programmierung existieren als simulierte Gate-/Katalog-UIs; Schreiben und Flash ohne Spec/Freigabe sind **deaktiviert**.
