# Mollie Setup

## Env
```
MOLLIE_API_KEY=test_...          # oder live_...
MOLLIE_WEBHOOK_SECRET=           # optional
MOLLIE_WEBHOOK_URL=https://.../api/billing/webhooks/mollie
MOLLIE_LIVE_CHARGES_ALLOWED=false
```

## Endpunkte
- `GET /api/billing/mollie/status`
- `POST /api/billing/mollie/connection-test` (Admin) → `GET https://api.mollie.com/v2/profiles/me`
- `POST /api/billing/mollie/checkout` (Admin)
- `POST /api/billing/webhooks/mollie`

## Admin-UI
Administration → Panel „Mollie“ → Verbindungstest.

Stripe-Pfade antworten mit `removed` / Replacement Mollie.
