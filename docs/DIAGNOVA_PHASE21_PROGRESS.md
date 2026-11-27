# Phase 21 – Fortschritt

**Stand:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-21-billing-adapters-e3f2`  
**PR:** https://github.com/Xerentis1986/DiagNova/pull/32

## Ampel je Teilbereich

| Bereich | Status | Hinweis |
|---------|--------|---------|
| A Adapter / CDP+ | 🟡 Partial | Safe-Reads sim; Live-HW offen |
| A OBD-DIAG 2055+ | 🔴 Blocked | Keine API; Inventur nötig |
| A ELM/STN/J2534 | 🟡 Partial/Planned | ELM sim; J2534 Abstraktion |
| B OBD-II Engine | 🟡 Sim + Live-Pfad | Live nur mit COM; HW ungetestet |
| B OEM/Service/Coding | 🟡 Architektur | Schreibend gesperrt |
| C Connector | 🟡 Vollständig sim | Installer-Doku; kein HW-Labor |
| D Commerce B2B/B2C | 🟢 Sim | Steuer draft_needs_review |
| D Stripe | 🟡 Testmodus-Code | Keys fehlen → kein Fake-Success |
| D Admin-Kennzahlen | 🟢 DB | MRR Katalog-Näherung |
| E E-Mail | 🟡 dry_run | SMTP optional |
| F Tests | 🟢 Automatisiert | HW-Tests nur Anleitung |
| Release | 🔴 NO-GO | siehe RELEASE_BLOCKERS |

## Nächste externe Abhängigkeiten

1. Adapter physisch inventarisieren (VID/PID, Serial Präfix 10)
2. Stripe Test-Keys setzen (`STRIPE_*`)
3. SMTP für Mails
4. Rechts-/Steuerfreigabe
5. Kein Prod-Redeploy ohne Freigabe
