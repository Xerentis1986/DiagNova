# DiagNova – Backup & Restore (Phase 15/16)

**Stand:** 2026-11-27 (Europe/Vienna)  
Simulation/Dev dokumentiert und stichprobenartig prüfbar. **Kein** automatisches Prod-Backup ohne Zustimmung. Secrets nie in Git oder Chat.

## Empfohlenes Backup

1. Vor Migration/Deploy: `pg_dump` (custom oder plain) mit Zeitstempel + Alembic-Revision.
2. Prod-Hilfsskript (World4You):  
   `APP_DIR=/opt/diagnova bash infrastructure/docker/backup-postgres.sh`  
   → `/var/backups/diagnova/diagnova-<UTC>.dump` + `.alembic.txt` (`chmod 600`).
3. Optional Plesk → Domain/DB-Backup; Dump-Integrität prüfen (`pg_restore --list` / Dateigröße).
4. Web/API-Artefakte und Connector-Installer getrennt versionieren (Phase 14).
5. Dump außerhalb Git lagern; Zugriff beschränken (PII).

`deploy-plesk.sh` versucht vor Rebuild automatisch einen Pre-Deploy-Dump, wenn Postgres bereits läuft.

## Restore

1. Wartungsmodus / API+Web stoppen (`docker compose -f docker-compose.prod.yml stop api web`).
2. `pg_restore` aus bekanntem Stand in den Postgres-Container; Alembic-Version prüfen.
3. `JWT_SECRET`, `CORS_ORIGINS` und Demo-HMAC-Secrets aus Secret-Store wiederherstellen (nicht aus Dump ableiten).
4. Stack starten; Healthcheck `GET /health` und Security-Dashboard prüfen.
5. Stichprobe: Login + Mandantenisolation (fremder Kunde → 404).

Beispiel (Anpassung Pfade/User – **keine** Passwörter hier):

```bash
cd /opt/diagnova
docker compose -f docker-compose.prod.yml --env-file .env stop api web
docker compose -f docker-compose.prod.yml --env-file .env exec -T postgres \
  pg_restore -U diagnova -d diagnova --clean --if-exists < /var/backups/diagnova/diagnova-YYYYMMDD.dump
docker compose -f docker-compose.prod.yml --env-file .env up -d
```

## Monitoring (Hinweise)

- `GET /health` periodisch (Uptime); Feld `security.jwt_secret_insecure_default`
- Login-Rate-Limit: HTTP 429 beobachten
- Audit: Häufung `login_failed` / `login_rate_limited`
- Produktives Alerting erst nach Zustimmung – siehe `docs/phase-16-deploy-checklist.md`

## API

- `GET /api/security/backup` (Admin) – strukturierte Schritte

## Siehe auch

- `docs/world4you-plesk-install.md` §6–8
- `docs/phase-16-deploy-checklist.md`
