# Ziel A – Commerce Acceptance (Phase 22)

Abnahmekriterien laut Masterprompt – ehrliche Bewertung.

| Kriterium | Ergebnis | Nachweis |
|-----------|----------|----------|
| B2B/B2C Registrierung & Konten | PASS | API-Tests Phase 21/22 |
| Tarife / Abo-Stub | PASS | Commerce Routes |
| Stripe Checkout + Webhook E2E | BLOCKED | Keine Keys (BLK-STRIPE-01) |
| PDF-Rechnung downloadbar | PASS | `?format=pdf`, Test magic bytes |
| Gutschriften / Refunds live | BLOCKED | Policy |
| AT/EU Steuer freigegeben | FAIL/BLOCKED | `draft_needs_review` |
| E-Mail Bestätigung/Reset Prod | BLOCKED | dry_run only |
| MFA Plattform-Admin | PASS | Setup/Confirm/Login Test |
| Lizenz nach Zahlung | PARTIAL | Phase-21 License Mgmt; Stripe E2E fehlt |
| **Ziel A Gesamt** | **NO-GO** | Externe + fachliche Blocker |
