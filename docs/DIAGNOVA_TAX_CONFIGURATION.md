# DiagNova – Steuerkonfiguration AT (Phase 21)

**Stand:** 2026-11-27 (Europe/Vienna)  
**review_status:** `draft_needs_review` – **keine** produktive Steuerfreigabe  
**Engine:** `apps/api/app/services/commerce/tax_engine.py`  
**Seed:** `apps/api/app/data/tax_rules_at.py`

## Szenarien

| Szenario | Beschreibung | Demo-Verhalten |
|----------|--------------|----------------|
| `b2b_at` | B2B Inland AT | 20 % USt, Netto-Darstellung |
| `b2c_at` | B2C Inland AT | 20 % USt, **Bruttopreise** |
| `b2b_reverse_charge` | B2B EU + gültige VIES-UID | 0 % / Reverse Charge |
| `b2b_eu_uid_required` | B2B EU ohne gültige UID | vorsichtig AT-Satz; Prod sperren/prüfen |
| `b2c_eu_oss` | B2C EU elektronische DL | OSS-Landessatz (Demo-Tabelle) |
| `third_country` | Drittland | Demo 0 % AT-USt – Einzelfall |

## Quellen (Orientierung)

- USP.at – elektronisch erbrachte Dienstleistungen
- USP.at – One-Stop-Shop (OSS)
- EU – Place of taxation / VAT Directive

## Regeln

- Keine Pauschalisierung grenzüberschreitender B2C-Softwareabos
- Leistungsort und OSS vor Prod fachlich prüfen
- Aufbewahrungshinweis Rechnungen: 7 Jahre (Metadatum `retention_until`)
- Endgültige Konfiguration **muss** vor produktiver Freigabe geprüft werden
