# Phase 02 – Abschlussbericht: Marken-Kacheln und Fahrzeugauswahl

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-02-brands-c4de`  
**Basis:** `origin/cursor/diagnova-phase-00-inventory-c287` (MVP + Phase-00-Docs)  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 03.

## Auftrag (Master-Prompt 02)

Helle/responsive Markenübersicht, Logo- oder Text-Kacheln, Suche, Favoriten, zuletzt verwendet, Theme Hell/Dunkel/System, Auswahlfluss Marke→Modell→Baureihe/Baujahr→Motor→Bestätigen→Adapter→Diagnose, VIN/Kennzeichen/km, DACH-Katalog, keine vorgetäuschte Diagnoseabdeckung.

## Umsetzung

### Backend

- Statischer DACH-Katalog `apps/api/app/data/dach_brands.py` (38 Marken laut Prompt)
- API: `/api/catalog/brands|models|variants|capabilities`
- Preferences (`theme_preference`), Favoriten, Recent Selections
- `POST /api/vehicles/confirm`, `PATCH /api/vehicles/{id}` inkl. VIN-Formatprüfung
- Alembic `002_phase02`
- Capabilities: nur MVP-Simulator als „available“; OEM/Service/Codierung als „planned“

### Frontend

- Startseite = Markenübersicht (`BrandsPage`), helles Default-Theme
- Text-Fallback-Kacheln (Initialen) – **keine** Markenbildlogos (BLK-LOGO)
- Suche, Favoriten, zuletzt verwendet
- Theme-Toggle Hell/Dunkel/System (localStorage + Profil)
- Wizard `VehicleSelectPage` mit VIN/Kennzeichen/km und Capabilities-Hinweis
- Responsive Grid, Tastatur-Fokus, `prefers-reduced-motion`

### Bewusst nicht

- Keine Markenlogos ohne Rechteklärung
- Keine Diagnoseabdeckung pro Marke vorgetäuscht
- Keine Phase 03 (Adapter/Bluetooth)
- Kein Prod-Deploy, keine Hardwaretests

## Tests (ausgeführt)

| Suite | Befehl | Ergebnis |
|-------|--------|----------|
| API + Protocols | `python3 -m pytest tests -q` | **18 passed** |
| Web Build | `cd apps/web && npm run build` | **OK** |
| E2E Playwright | `cd apps/web && npx playwright test` | **4 passed** (Suche, Theme, Wizard, Favoriten) |

Nicht ausgeführt: Docker Compose (BLK-DOCKER), .NET Connector-Build (BLK-DOTNET).

## Geänderte / neue Dateien (Auszug)

- `apps/api/app/data/dach_brands.py`, `services/vin.py`
- `apps/api/app/api/routes/catalog.py`, `preferences.py`, erweitert `vehicles.py`, `auth.py`
- `apps/api/alembic/versions/002_phase02_catalog_prefs.py`
- `apps/web/src/pages/BrandsPage.tsx`, `VehicleSelectPage.tsx`
- `apps/web/src/lib/theme.tsx`, `favorites.ts`, `components/BrandTile.tsx`, `ThemeToggle.tsx`
- `apps/web/e2e/phase02.spec.ts`, `playwright.config.ts`
- `tests/api/test_phase02_catalog.py`
- `docs/requirements.md`, `capabilities.md`, `phase-status.md`, `DIAGNOVA_PROGRESS.md`

## Start (Dev)

```bash
# API (Beispiel SQLite)
export DATABASE_URL='sqlite:////tmp/diagnova.db'
export PYTHONPATH="apps/api:packages/diagnostic-protocols/src"
cd apps/api && python3 -m uvicorn app.main:app --reload --port 8000

# Web
cd apps/web && VITE_API_URL=http://127.0.0.1:8000 npm run dev
```

Login: `admin@example.com` / `AdminDemo123!`

## Offene Punkte / Blocker

| ID | Thema |
|----|-------|
| BLK-LOGO | Markenlogo-Rechte → Text-Fallback |
| BLK-OEM | Keine OEM-Diagnosedaten |
| BLK-HW | Keine echte VIN vom Fahrzeug |
| Phase 03 | Adapter verbinden – nächster orchestrated Schritt |

## Abnahme-Checkliste Prompt 02

| Kriterium | Status |
|-----------|--------|
| Navigation Markenübersicht | OK (E2E) |
| Suche | OK (API + E2E) |
| Theme-Persistenz | OK (API + E2E) |
| Fallback-Logos | OK (nur Text) |
| Leere Zustände | OK (E2E Suche ohne Treffer) |
| Fahrzeugauswahl | OK (E2E Wizard) |
