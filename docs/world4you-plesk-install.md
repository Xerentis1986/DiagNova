# DiagNova – Installationsanleitung World4You (Ubuntu / Plesk)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Ziel:** reproduzierbarer Betrieb unter `https://diagnova.codekreativ.at/`  
**Regel:** Keine Secrets in Git/Chat. Bestehende Sites (`masterdesk`, `/sv/`, `helix-ki`) **nicht** verändern. Kein produktives Redeploy ohne Betreiberfreigabe.

## 1. Voraussetzungen prüfen (keine Werte erfinden)

Auf dem V-Server (SSH als root oder berechtigt):

```bash
uname -a
lsb_release -a 2>/dev/null || cat /etc/os-release
nproc; free -m; df -h /
docker --version
docker compose version
plesk version 2>/dev/null || true
ss -tlnp | head -40
```

Erwarteter Ist-Zustand (bereits dokumentiert, Stand Deploy Phase 10B/16):

| Punkt | Bekannt |
|-------|---------|
| Host | World4You V-Server, IP `212.227.48.90` |
| Domain | `diagnova.codekreativ.at` (Webspace vorhanden) |
| Docker | Plesk Docker-Extension; Compose verfügbar |
| App-Pfad | `/opt/diagnova` |
| Compose | `docker-compose.prod.yml` |
| Proxy | Plesk Docker Proxy Rule → `diagnova-web-1:80` (Host `127.0.0.1:3080`) |
| TLS | Let's Encrypt, HTTP→HTTPS 301 |
| Parallel | `helix-ki` / `helix-ollama` – **unangetastet** |
| MariaDB | `admin_diagnova` existiert, App nutzt **Postgres im Compose** |

DNS: Zone bei World4You (`ns1`/`ns2.world4you.at`) – siehe Store `docs/diagnova-dns-world4you.md`.

## 2. Secrets / `.env` (nur auf dem Server)

```bash
cd /opt/diagnova
cp .env.example .env   # nur wenn neu; bestehende .env behalten
chmod 600 .env
# Editor: starke Zufallswerte setzen – niemals committen
```

Pflichtfelder Produktion:

| Variable | Hinweis |
|----------|---------|
| `POSTGRES_PASSWORD` | lang, zufällig |
| `JWT_SECRET` | lang, zufällig; **nicht** Default aus `.env.example` |
| `CORS_ORIGINS` | `https://diagnova.codekreativ.at` (+ Staging falls genutzt) |
| `SEED_*_PASSWORD` | Demo-Seed nur wenn Demo erlaubt; sonst rotieren |
| HMAC-Demo-Secrets | **nicht** als Prod-Signing missbrauchen |

Nach Start prüfen:

```bash
curl -fsS https://diagnova.codekreativ.at/health
# security.jwt_secret_insecure_default muss false sein
```

## 3. Docker Compose (Prod)

Dateien im Repo:

- `docker-compose.prod.yml` – Volumes, Healthchecks, `restart: unless-stopped`, Memory-Limits, DB ohne Host-Port, Web nur `127.0.0.1:3080`
- `infrastructure/docker/deploy-plesk.sh` – Clone/Pull, optionales Pre-Deploy-Backup, Build/Up
- `infrastructure/docker/backup-postgres.sh` – `pg_dump -Fc` + Alembic-Metadatei

Manuell:

```bash
cd /opt/diagnova
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
docker compose -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:3080/health
```

Oder Skript:

```bash
BRANCH=cursor/diagnova-phase-16-deploy-8876 \
  bash infrastructure/docker/deploy-plesk.sh
```

**Alembic:** läuft beim API-Container-Start (`alembic upgrade head`). Vor Migration immer Backup.

## 4. Plesk Reverse Proxy & HTTPS

Empfohlen (Ist): **Docker → Proxy Rules** für Domain `diagnova.codekreativ.at` → Container `diagnova-web-1`, Port 80.

Alternative: zusätzliche nginx-Direktiven aus `infrastructure/nginx/plesk-proxy.conf` (inkl. WebSocket-Header). SSL It! / Let's Encrypt und HTTP→HTTPS in Plesk belassen.

In-Container-Proxy: `infrastructure/nginx/web.conf` (SPA, `/api`, `/health`, Upgrade-Header).

Firewall: nur 80/443 öffentlich; Compose-Ports nicht nach außen.

## 5. Staging-Subdomain (optional)

1. DNS `staging.diagnova` A → Server-IP (World4You-Kundencenter).
2. Eigenen Plesk-Webspace **oder** Subdomain anlegen – andere Domains nicht überschreiben.
3. Separates Compose-Projekt/Verzeichnis (z. B. `/opt/diagnova-staging`), anderer Host-Port (z. B. `127.0.0.1:3081`), eigene `.env` und DB-Volume-Namen.
4. `CORS_ORIGINS` um Staging-Origin ergänzen.
5. Gleiche Proxy-/TLS-Schritte wie Produktion.

Ohne Freigabe kein Staging anlegen (Agenten: nur dokumentieren).

## 6. Backup

Siehe auch `docs/backup-restore.md`.

```bash
APP_DIR=/opt/diagnova bash infrastructure/docker/backup-postgres.sh
# Ausgabe unter /var/backups/diagnova/ (chmod 600)
```

Zusätzlich optional: Plesk-Domain-Backup. Dumps **außerhalb** Git lagern (PII).

## 7. Logs & Monitoring

```bash
docker compose -f docker-compose.prod.yml logs -f --tail=200 api web
curl -fsS https://diagnova.codekreativ.at/health
# Admin: /security Dashboard; GET /api/security/backup
```

Produktives Alerting erst nach Zustimmung. Periodisch: Health, `jwt_secret_insecure_default`, Login-429, Audit `login_failed`.

## 8. Rollback

1. Wartungsfenster / Traffic prüfen.
2. Letztes Dump + bekannte Git-Revision bereithalten.
3. Code: `git -C /opt/diagnova checkout <vorherige-revision>` und Compose neu bauen **oder** Image-Tag zurücksetzen.
4. DB nur bei Bedarf: Stack stoppen → `pg_restore` → Alembic-Stand prüfen (siehe `docs/backup-restore.md`).
5. Secrets aus Secret-Store, nicht aus Dump.
6. Verifikation: `/health`, Login, Mandantenisolation, `/security`.

## 9. Windows-Connector

Bleibt **lokal** auf dem Werkstatt-PC. Kein Connector-Deploy auf dem V-Server. Pairing/Origin gemäß Connector-Docs; HTTPS-Origin der Live-Domain in Allowlist.

## 10. Abnahme-Checkliste (Staging / nach Freigabe)

Siehe `docs/phase-16-deploy-checklist.md`. Kurz:

- [ ] TLS gültig, HTTP→HTTPS
- [ ] `/` 200, `/health` 200, API ohne 502
- [ ] Login Admin + Technician
- [ ] PDF/Bericht Stichprobe
- [ ] Update-Job / Software-Updates: Auto ohne Zertifikat gesperrt
- [ ] Connector-Kopplung lokal
- [ ] Andere Sites unverändert

## 11. Was Agenten **nicht** tun

- Keine destruktiven Serveränderungen ohne Freigabe
- Keine Secrets auslesen/ausgeben
- `helix-ki`, `masterdesk`, `/sv/` und andere Hosts unberührt
- Phase 17 nicht starten
