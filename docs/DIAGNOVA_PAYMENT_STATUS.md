# Zahlungsstatus

| Modus | Status |
|-------|--------|
| Mock-Stub Webhooks | vorhanden (Phase 13) |
| Stripe Checkout + Webhooks | implementiert (Testmodus) |
| Live-Charges | **gesperrt** (`stripe_live_charges_allowed=false`) |

Env: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`.  
Ohne Keys: Checkout liefert `not_configured` – **kein Fake-Success**.
