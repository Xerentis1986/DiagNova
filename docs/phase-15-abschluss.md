# Phase 15 – Abschlussbericht: Sicherheit, Datenschutz und Qualität

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-15-security-4381`  
**Basis:** Phase 14 `cursor/diagnova-phase-14-software-updates-8f1e` (PR #22) – Designsystem 10B beibehalten  
**Nächste Phase:** **nicht** gestartet – Phase 16 nur Checkliste ergänzt (Deploy bereits weitgehend live).

## Auftrag

Threat Model für Browser, API, Connector, Adapter, Updates und Mandanten. Auth, Passwort-Hashing, Session/Cookie/CSRF/CORS, Origin, Rate Limits, Rollen, IDOR, Secrets, Injection, XSS, SSRF prüfen. Connector minimal privilegiert. Audit ohne Passwörter/unnötige VIN/Kundendaten. DSGVO-Prozesse dokumentieren (keine Konformität). Backup/Restore und Monitoring. Security- und Regressionstests. Kritische Befunde beheben; offene Risiken dokumentieren.

## Umsetzung

### Threat Model & Dashboard

- `docs/threat-model.md` + `GET /api/security/dashboard`
- UI `/security` (Designsystem 10B: PageHeader/Panel/Badge)

### Auth / RBAC / CORS

- bcrypt unverändert; Passwortpolitik (Länge/Klassen) als Check-Endpoint
- JWT mit `iat`, `exp`, `typ=access`
- Login-Rate-Limit (IP + E-Mail) → HTTP 429
- Origin-Allowlist bei Login (abweichende Origin → 403)
- Logout mit Audit (JWT bleibt stateless)
- CORS-Allowlist; Bearer-Auth → CSRF-Risiko gering (dokumentiert)
- RBAC/IDOR: bestehende Mandantentrennung + Regressionstests

### Audit / DSGVO

- `write_audit` mit Redaction (Passwort/Token/VIN/E-Mail/Telefon)
- Spalten `outcome`, `ip_hash` (Alembic `012_phase15`)
- `docs/dsgvo-processes.md` – Auskunft/Export/Löschung/Aufbewahrung/AV
- Keine rechtliche Konformität behauptet (BLK-LEGAL)

### Backup / Monitoring

- `docs/backup-restore.md`, `GET /api/security/backup`
- Health um Security-Hinweis erweitert
- `docs/phase-16-deploy-checklist.md` – **Phase 16 nicht implementiert**

### Versionen

- API / Web / Connector **0.15.0**
- Update-Fixtures `phase15_*`; Inkompatibilitätstests mit 0.16.0

## Tests

| Suite | Ergebnis |
|-------|----------|
| `pytest tests -q` | **126 passed** (+13 Phase 15) |
| `apps/web` `npm run build` | **OK** |
| Security-Regression | Rate-Limit, Redaction, IDOR, Origin, Dashboard, RBAC |

## Blocker / offene Risiken

| Thema | Status |
|-------|--------|
| JWT-Default in Dev/Tests | bewusst; Prod-Secret Pflicht |
| BLK-CERT Code-Signing | unverändert – Auto-Updates gesperrt |
| BLK-LEGAL DSGVO/AV | dokumentiert, nicht freigegeben |
| Multi-Worker-Rate-Limit | In-Memory akzeptiert (Demo) |
| Produktives Alerting | Checkliste Phase 16 |

## Bewusst nicht

- **Phase 16 nicht gestartet** (nur Docs/Checkliste)
- Keine Secrets committen
- Keine Produktionsfreigabe bei Default-JWT / kritischen Lücken
- Keine rechtlichen Konformitätsaussagen

## Geänderte Bereiche (Auszug)

- `apps/api/app/core/{rate_limit,security,security_headers,config}.py`
- `apps/api/app/services/{audit,security_overview}.py`
- `apps/api/app/api/routes/{auth,security}.py` + Migration `012_phase15`
- `apps/web`: `SecurityPage`, Nav, API-Client
- Docs: threat-model, dsgvo-processes, backup-restore, phase-16-checklist, requirements/capabilities/phase-status
