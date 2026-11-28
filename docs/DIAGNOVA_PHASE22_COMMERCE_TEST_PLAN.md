# Phase 22 – Commerce-Testplan

| # | Schritt | Erwartung | Ergebnis |
|---|---------|-----------|----------|
| C1 | B2B/B2C Account | 201/200 | PASS lokal |
| C2 | Subscribe Stub | Abo angelegt | PASS lokal |
| C3 | Invoice JSON | Felder vollständig | PASS |
| C4 | Invoice PDF | Content-Type PDF, `%PDF` | PASS |
| C5 | Stripe status ohne Keys | not_configured | PASS |
| C6 | Stripe Checkout Test-Keys | Session URL | BLOCKED Keys |
| C7 | Webhook Signatur | 200 idempotent | BLOCKED Keys |
| C8 | MFA Admin Login | ohne Code 401; mit Code OK | PASS |
| C9 | Password-Reset | dry_run Payload | PASS |
| C10 | Steuerpreview | draft_needs_review | PASS (noch nicht freigegeben) |

**Live-Charges:** BLOCKED ohne explizite Freigabe.
