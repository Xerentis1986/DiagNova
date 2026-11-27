# Phase 16 – Deploy-Checkliste (World4You / Plesk)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Live:** https://diagnova.codekreativ.at/ (Docker/Plesk, LE) – siehe Installationsanleitung `docs/world4you-plesk-install.md`.  
**Regel:** Kein neues Produktiv-Deploy durch Agenten ohne Zustimmung. Secrets nie in Git/Chat.

## Vor jedem Deploy

- [ ] `pg_dump` / `infrastructure/docker/backup-postgres.sh` mit Zeitstempel + Alembic-Revision
- [ ] Optional Plesk-Domain-Backup
- [ ] `JWT_SECRET` lang & zufällig (nicht Default); `chmod 600` auf `.env`
- [ ] `CORS_ORIGINS` enthält die Live-Origin(s) (+ Staging falls vorhanden)
- [ ] Demo-HMAC-Secrets nicht als Prod-Signing missbrauchen
- [ ] Keine Secrets in Git / Chat
- [ ] Alembic-Stand bekannt; Migration nur mit Backup
- [ ] Branch/Commit dokumentiert (`git rev-parse HEAD`)
- [ ] RAM prüfen (helix-Stack parallel – nicht anfassen)

## Deploy-Schritte

- [ ] `docker compose -f docker-compose.prod.yml --env-file .env up -d --build` **oder** `deploy-plesk.sh`
- [ ] `docker compose … ps` – postgres/api/web healthy
- [ ] Plesk Proxy Rule / nginx → `127.0.0.1:3080` unverändert bzw. geprüft
- [ ] TLS / HTTP→HTTPS 301

## Nach Deploy

- [ ] `GET /health` → 200; `security.jwt_secret_insecure_default == false`
- [ ] Login Admin + Technician
- [ ] Mandantenisolation: fremde Kunden-ID → 404
- [ ] `/security` Dashboard erreichbar (Admin)
- [ ] PDF/Bericht Stichprobe
- [ ] Software-Updates: Prod-Auto ohne Zertifikat weiterhin gesperrt
- [ ] Update-Scheduler nur bewusst aktiviert
- [ ] Login-Rate-Limit Stichprobe → 429
- [ ] Bestehende Sites (`masterdesk`, `/sv/`, helix) unberührt
- [ ] Windows-Connector lokal: Origin/Pairing gegen Live-HTTPS

## Rollback (Kurz)

- [ ] Vorherige Git-Revision / Image
- [ ] Bei DB-Schaden: `pg_restore` aus Timestamp-Dump (siehe `docs/backup-restore.md`)
- [ ] Secrets aus Secret-Store; Health + Login erneut prüfen

## Staging (optional)

- [ ] Eigene Subdomain/Port/Volume/`.env`
- [ ] Gleiche Checks wie oben, ohne Prod-Daten zu überschreiben

## Abnahme Phase 16 (dokumentarisch)

| Kriterium | Status |
|-----------|--------|
| Installationsanleitung | `docs/world4you-plesk-install.md` |
| Compose Prod (Volumes/Health/Restart/Secrets) | `docker-compose.prod.yml` |
| Proxy + WebSocket-Header | `infrastructure/nginx/{web,plesk-proxy}.conf` |
| Backup-Skript | `infrastructure/docker/backup-postgres.sh` |
| HTTPS | Let's Encrypt via Plesk (Ist) |
| Rollback dokumentiert | Install-Doc §8 + Backup-Restore |
| Live verifiziert (ohne Redeploy) | `/` + `/health` 200 |
| Phase 17 | **nicht** gestartet |
