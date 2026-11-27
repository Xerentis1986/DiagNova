# DiagNova – Backup & Restore (Phase 15)

**Stand:** 2026-11-27 (Europe/Vienna)  
Simulation/Dev dokumentiert und stichprobenartig prüfbar. **Kein** automatisches Prod-Backup ohne Zustimmung. Secrets nie in Git oder Chat.

## Empfohlenes Backup

1. Vor Migration/Deploy: `pg_dump` (custom oder plain) mit Zeitstempel + Alembic-Revision.
2. Optional Plesk → Datenbanken → Backup; Dump-Integrität prüfen (`pg_restore --list` / Dateigröße).
3. Web/API-Artefakte und Connector-Installer getrennt versionieren (Phase 14).
4. Dump außerhalb Git lagern; Zugriff beschränken (PII).

## Restore

1. Wartungsmodus / API+Web stoppen.
2. `pg_restore` aus bekanntem Stand; Alembic-Version prüfen.
3. `JWT_SECRET`, `CORS_ORIGINS` und Demo-HMAC-Secrets aus Secret-Store wiederherstellen (nicht aus Dump ableiten).
4. Healthcheck `GET /health` und Security-Dashboard prüfen.
5. Stichprobe: Login + Mandantenisolation (fremder Kunde → 404).

## Monitoring (Hinweise)

- `GET /health` periodisch (Uptime); Feld `security.jwt_secret_insecure_default`
- Login-Rate-Limit: HTTP 429 beobachten
- Audit: Häufung `login_failed` / `login_rate_limited`
- Produktives Alerting erst nach Zustimmung – siehe `docs/phase-16-deploy-checklist.md`

## API

- `GET /api/security/backup` (Admin) – strukturierte Schritte
