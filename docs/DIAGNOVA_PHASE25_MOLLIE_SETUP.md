# Mollie Setup

## Betreiber-UI (bevorzugt)
1. Als Plattform-Admin → **`/operator?tab=mollie`**
2. API-Key (`test_…`) eintragen → Speichern (Secret-Store, verschlüsselt)
3. **Verbindungstest** (ohne Abbuchung)
4. Live nur mit `live_…` + Checkbox „Live-Charges“ (Standard aus)

## Env (überschreibt Store wenn gesetzt)
```
MOLLIE_API_KEY=test_...
MOLLIE_WEBHOOK_SECRET=
MOLLIE_WEBHOOK_URL=https://.../api/billing/webhooks/mollie
MOLLIE_LIVE_CHARGES_ALLOWED=false
DIAGNOVA_SECRETS_DIR=.secrets
DIAGNOVA_SECRETS_FERNET_KEY=
```

## Endpunkte
- `GET/PUT /api/billing/mollie/config` (Plattform-Admin, Keys maskiert)
- `GET /api/billing/mollie/status`
- `POST /api/billing/mollie/connection-test` → Mollie `profiles/me`
- `POST /api/billing/mollie/checkout` / `POST /api/billing/webhooks/mollie`

Stripe-Pfade: `removed` / Replacement Mollie.
