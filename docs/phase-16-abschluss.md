# Phase 16 – Abschlussbericht: World4You Ubuntu/Plesk Deployment

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-16-deploy-8876`  
**Basis:** Phase 15 `cursor/diagnova-phase-15-security-4381` (PR #24) – Designsystem 10B beibehalten  
**Nächste Phase:** **nicht** gestartet – Freigabeprüfung durch Coordinator vor Phase 17.

## Auftrag

Installationsanleitung für V-Server M (Root/SSH). Ubuntu/Plesk/Docker/DNS/Ports prüfen ohne erfundene Werte. Docker Compose mit Volumes, Healthchecks, Restart, DB nicht öffentlich, sichere Secrets. Plesk-kompatibler Reverse Proxy mit HTTPS und WebSocket, ohne bestehende Sites zu ändern. Staging, Firewall, Migration, Backup, Logs, Monitoring, Rollback. Windows-Connector lokal. Abnahme: dokumentierter reproduzierbarer Deploy-Pfad; Live bereits vorhanden – **kein** destruktives Redeploy ohne Freigabe.

## Ist-Zustand (verifiziert, kein Server-Eingriff)

| Check | Ergebnis |
|-------|----------|
| `https://diagnova.codekreativ.at/` | **200** |
| `GET /health` | **200** `demo_mode: true`, Status ok |
| TLS | Let's Encrypt, HTTP→HTTPS (Ist aus vorherigen Deploys) |
| Stack | `/opt/diagnova`, Compose Prod, Proxy → web:80 / `127.0.0.1:3080` |
| Unangetastet | helix-ki, masterdesk, `/sv/`, MariaDB `admin_diagnova` |

Quellen: Store `docs/deploy-status.md`, interne Plesk-Notizen (ohne Secrets).

## Umsetzung (Repo)

### Dokumentation

- `docs/world4you-plesk-install.md` – Installation, Secrets, Proxy, Staging, Backup, Logs, Rollback, Connector
- `docs/phase-16-deploy-checklist.md` – Vor/Nach Deploy, Abnahme, Rollback
- `docs/backup-restore.md` – um Prod-Skripte ergänzt
- Matrix: `requirements.md` / `capabilities.md` / `phase-status.md` / `DIAGNOVA_PROGRESS.md`

### Infra (kleine Verbesserungen)

- `docker-compose.prod.yml` – Memory-Limits, Healthchecks api/web/postgres, `restart`, DB ohne Host-Port, Pflicht-Env (`:?`), Web nur Loopback
- `infrastructure/nginx/web.conf` – Proxy-Header, WebSocket Upgrade, `/version`
- `infrastructure/nginx/plesk-proxy.conf` – Plesk-Zusatzdirektiven inkl. WS
- `infrastructure/docker/deploy-plesk.sh` – Pull/Build, optional Pre-Deploy-`pg_dump`, helix unberührt
- `infrastructure/docker/backup-postgres.sh` – Dump + Alembic-Metadatei

### Bewusst nicht

- **Kein** SSH-/Plesk-Schreibzugriff in dieser Phase (dokumentarisch/operativ abschließen)
- **Keine** Secrets in Git
- **Phase 17 nicht gestartet**
- Kein erzwungenes Live-Redeploy auf Phase-16-Branch ohne Freigabe

## Tests

| Suite | Ergebnis |
|-------|----------|
| `pytest tests -q` | **126 passed** (Regression unverändert) |
| Compose-YAML | `yaml.safe_load` OK (Docker CLI in Agent-VM nicht verfügbar) |
| Live Smoke (read-only) | `/` + `/health` 200 |

## Blocker / offene Punkte

| Thema | Status |
|-------|--------|
| BLK-DEPLOY | Prod-Redeploy nur nach Freigabe; Live läuft auf älterem Feature-Branch |
| BLK-CERT | Software-Auto-Updates ohne Zertifikat gesperrt |
| BLK-LEGAL | DSGVO/AV unverändert offen |
| Staging-Subdomain | dokumentiert, nicht angelegt |
| Produktives Alerting | dokumentiert, nicht aktiviert |
| Live-Version vs. Phase-15/16-Code | Angleichung erst nach Merge + Freigabe-Deploy |

## Geänderte Bereiche (Auszug)

- `docker-compose.prod.yml`, `infrastructure/docker/*`, `infrastructure/nginx/*`
- Docs: Install, Checkliste, Abschluss, requirements/capabilities/phase-status, Progress, backup-restore
