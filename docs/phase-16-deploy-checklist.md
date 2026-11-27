# Phase 16 – Deploy-Checkliste (Ergänzung, kein Start der Phase)

**Hinweis:** Deploy ist weitgehend live (`diagnova.codekreativ.at`).  
Diese Datei ergänzt nur die Checkliste. **Phase 16 nicht automatisch starten.**

## Vor jedem Deploy

- [ ] `pg_dump` / Plesk-DB-Backup mit Zeitstempel
- [ ] `JWT_SECRET` lang & zufällig (nicht Default)
- [ ] `CORS_ORIGINS` enthält die Live-Origin(s)
- [ ] Demo-HMAC-Secrets nicht als Prod-Signing missbrauchen
- [ ] Keine Secrets in Git / Chat
- [ ] Alembic-Stand bekannt; Migration nur mit Backup
- [ ] `GET /health` → `security.jwt_secret_insecure_default == false`
- [ ] Login-Rate-Limit aktiv; Stichprobe 429

## Nach Deploy

- [ ] Login Admin + Technician
- [ ] Mandantenisolation: fremde Kunden-ID → 404
- [ ] `/security` Dashboard erreichbar (Admin)
- [ ] Software-Updates: Prod-Auto ohne Zertifikat weiterhin gesperrt
- [ ] Bestehende Sites unter `/sv/` und andere Plesk-Hosts unberührt

## Nicht Teil dieser Ergänzung

- Kein neues Produktiv-Deploy durch Agenten ohne Zustimmung
- Keine Phase-16-Feature-Implementierung hier
