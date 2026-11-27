# DiagNova – Threat Model (Phase 15)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Status:** technisch dokumentiert / teilweise mitigiert – **keine** Produktionsfreigabe bei kritischen offenen Lücken.  
**API:** `GET /api/security/dashboard` (Admin)

## Oberflächen

| ID | Oberfläche | Hauptbedrohung | Mitigation | Status |
|----|------------|----------------|------------|--------|
| T-BROWSER | Browser / Web-UI | XSS, Token-Diebstahl, Clickjacking | React-Escaping, Security-Header, HTTPS in Prod | partial |
| T-API-AUTH | API Auth | Brute-Force, schwache Secrets | bcrypt, JWT exp/iat/typ, Login-Rate-Limit, Audit | mitigated |
| T-RBAC-IDOR | Mandanten / Rollen | IDOR fremde IDs | workshop_id aus Session, 404, RBAC | mitigated |
| T-CORS-CSRF | CORS / CSRF | Cross-Origin | CORS-Allowlist, Bearer ohne Cookie-Session | mitigated |
| T-CONNECTOR | Windows-Connector | Offene Ports, Remote-Befehle | Loopback, Pairing, Origin-Allowlist | mitigated |
| T-ADAPTER | OBD / Fahrzeug | Unkontrollierte Schreibbefehle | Allowlist, Gates, Live-Schreiben gesperrt | partial |
| T-UPDATES | Software-/Daten-Updates | Manipulation, SSRF | HMAC/SHA-256, SSRF-Guard, Admin-Freigabe | mitigated |
| T-SECRETS | Secrets / Config | Leak in Git/Chat | .env/Plesk, Demo-Secrets gekennzeichnet | partial |
| T-INJECTION | SQL / XSS / SSRF | Injection | ORM, Pydantic, SSRF-Guard | mitigated |
| T-AUDIT-PII | Audit / Logs | Passwörter/VIN in Logs | Redaction | mitigated |
| T-BACKUP | Backup / Restore | Datenverlust | dokumentierte Schritte | partial |

## Abnahmekriterien (Phase 15)

- Kritische Auth/IDOR-Befunde behoben oder als Blocker markiert
- Rate-Limit Login nachweisbar (429)
- Audit ohne Passwörter
- Offene Risiken dokumentiert (JWT-Default in Tests, BLK-CERT, BLK-LEGAL)
- Keine Secrets in Git

## Bewusst offen

- Multi-Worker-Rate-Limit (In-Memory akzeptiert für Demo)
- Produktives Alerting (Phase-16-Checkliste)
- Rechtliche DSGVO/AV-Prüfung (BLK-LEGAL)
