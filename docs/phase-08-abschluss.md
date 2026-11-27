# Phase 08 – Abschlussbericht: Werkstatt- und Kundenverwaltung

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-08-workshop-d09b`  
**Basis:** `origin/cursor/diagnova-phase-07-updates-4111` (PR #12)  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 09.

## Auftrag (Master-Prompt 08)

Werkstattprofil, Logo, Kontaktdaten, Benutzerrollen, Kunden und Fahrzeuge mit Suche, Filtern, Archivierung und Zuordnung. VIN/Kennzeichen/Kilometerstand/Motorisierung validieren; Dublettenprüfung mit manueller Zusammenführung. Werkstattaufträge, Notizen, Reparaturen und Status. Mandanten-ID serverseitig aus autorisierter Sitzung. Datenschutz: Export, Lösch-/Aufbewahrungsregeln, Audit, minimale Datenerhebung. Abnahme: CRUD, Suche, Rollen, Mandantentrennung, Migrationen und Löschkonflikte testen.

## Umsetzung

### Datenmodell

- Alembic `005_phase08` + ORM `app/models/workshop.py`
- Tabellen: `workshops`, `customers`, `customer_vehicles`, `work_orders`
- Erweiterungen: `users.workshop_id`, `vehicles.workshop_id`/`customer_id`/`archived_at`, `audit_logs.workshop_id`
- VIN-Uniqueness mandantenspezifisch `(workshop_id, vin)`

### Mandanten / Rollen

- `workshop_id` nur aus DB-User / JWT (`extra`), nie vom Client gesetzt
- Rollen: `admin` (Werkstattprofil), `technician`+`admin` (Schreiben), `viewer` (Lesen)
- Fremde Mandantenressourcen → **404** (kein Leak)

### API / UI

| Bereich | Endpunkte / UI |
|---------|----------------|
| Werkstatt | `/api/workshop/me`, Members, Logo; UI `/workshop` |
| Kunden | CRUD, Dubletten, Merge, Export, Delete-Modi; UI `/customers` |
| Aufträge | CRUD/Status/Archiv; UI `/work-orders` |
| Fahrzeuge | Mandantenfilter + Validierung; bestehendes `/vehicles` |

### DSGVO / Demo

- JSON-Export je Kunde (Auskunft/Portabilität)
- Archivieren, Anonymisieren, hartes Löschen (Admin); Konflikt bei offenen Aufträgen
- `retention_days` am Werkstattprofil
- Seed nur **Beispieldaten** (Demo-Werkstatt, Demo-Kunden) – keine Produktivdaten

### Docs

- Requirements REQ-08-*, Capabilities, Phase-Status, Progress aktualisiert

### Bewusst nicht

- Keine echten Kunden-/Werkstattdaten
- Keine Rechtsberatung / keine vollständige DSGVO-Zertifizierung (BLK-LEGAL)
- **Phase 09 nicht gestartet**
- Kein Prod-Deploy

## Tests (ausgeführt)

| Suite | Befehl | Ergebnis |
|-------|--------|----------|
| API + Protocols + Phase 06–08 | `PYTHONPATH=apps/api:packages/diagnostic-protocols/src python3 -m pytest tests -q` | **73 passed** |
| Connector xUnit | `dotnet test` | nicht ausgeführt (kein `dotnet`; Connector unverändert) |

Abnahme in `tests/api/test_phase08_workshop_customers.py`: Profil/Rollen, CRUD/Suche/Dublette/Merge, Aufträge, VIN-Validierung, Export, Löschkonflikt, Viewer-RO, Cross-Tenant-Isolation.

## Start

```bash
export PYTHONPATH="apps/api:packages/diagnostic-protocols/src"
# GET  /api/workshop/me
# GET  /api/customers?q=
# POST /api/customers  {"display_name":"…"}
# POST /api/work-orders {"title":"…"}
# GET  /api/customers/{id}/export
```

UI: `/workshop`, `/customers`, `/work-orders`. Migration: `alembic upgrade head` (Revision `005_phase08`).

## Offene Punkte / Blocker

| ID | Thema |
|----|-------|
| BLK-LEGAL | DSGVO-Aufbewahrung/Löschung rechtlich freigeben |
| BLK-HW | Hardware-Diagnose unverändert offen |
| BLK-DOCKER | Compose-Build in dieser Umgebung nicht ausgeführt |
| Phase 09 | Fahrzeugakte / Historie – nächster orchestrated Schritt |

## Geänderte Dateien (Kern)

- `apps/api/alembic/versions/005_phase08_workshop_customers.py`
- `apps/api/app/models/workshop.py`, `entities.py`
- `apps/api/app/api/routes/{workshop,customers,work_orders,vehicles,diagnostics,dashboard,auth}.py`
- `apps/api/app/services/{tenant,customers,workshop_validation}.py`
- `apps/web/src/pages/{Workshop,Customers,WorkOrders}Page.tsx`
- `docs/phase-08-abschluss.md`, requirements/capabilities/phase-status/PROGRESS
