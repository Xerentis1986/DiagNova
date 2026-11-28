# Phase 23 – Commerce E2E (intern)

| Fall | Ergebnis |
|------|----------|
| Stripe Webhook HMAC Fixture | PASS (`verify_stripe_signature`) |
| Stripe Checkout mit echten Keys | BLOCKED (keine Keys) |
| Live-Charges | BLOCKED (Policy) |
| SMTP Send-Pfad (Stub) | PASS |
| SMTP Prod | BLOCKED |
| Offline-License-Token | PASS (`/api/billing/licenses/offline-token`) |
| PDF Invoice | PASS |
| MFA Status | PASS |
| Steuerfreigabe | BLOCKED (`draft_needs_review`) |
