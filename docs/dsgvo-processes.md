# DiagNova – DSGVO-Prozesse (technisch, Phase 15)

**Wichtig:** Diese Dokumentation beschreibt technische Unterstützung.  
**Keine** rechtliche Beratung und **keine** Konformitätszusage (BLK-LEGAL).

## Prozesse

### Auskunft / Datenportabilität

- Werkstatt-Admin: `GET /api/customers/{id}/export` → JSON-Bundle (nur eigener Mandant)
- Identitätsprüfung der anfragenden Person: organisatorisch

### Löschung / Anonymisierung

- `POST /api/customers/{id}/privacy` mit `mode`: `archive` | `anonymize` | `delete`
- Offene Aufträge blockieren Löschen/Anonymisieren (Konfliktmeldung)
- UI: Kundenverwaltung

### Aufbewahrung

- `workshop.retention_days` (30–3650, Default 365)
- Berichts-Purge: `POST /api/reports/purge`
- Rechtliche Fristen (Steuer/Gewähr) vor Löschung klären

### Auftragsverarbeitung (AV)

- Technisch: Mandantentrennung, Rollen, Audit
- Vertrag / TOMs: extern, nicht Teil dieses Repos

## Audit

- Aktionen werden in `audit_logs` geschrieben
- Passwörter/Tokens nie speichern; VIN/E-Mail/Telefon maskiert
- Einsicht: `GET /api/security/audit` (Werkstatt-Admin)

## UI

- `/security` – Prozessübersicht + Disclaimer
- `/customers` – Export / Privacy-Aktionen
