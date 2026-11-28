# Phase 13 – Abschlussbericht: Abonnements und Administration

**Datum:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-13-subscriptions-66ed`  
**Basis:** Phase 12 `cursor/diagnova-phase-12-coding-2dd5` (PR #20) – Designsystem 10B beibehalten  
**Nächste Phase:** **nicht** gestartet – Coordinator orchestriert Phase 14.

## Auftrag

Mandantenregistrierung, Einladungen, Rollen, Gerätebindung, Tarife PKW und spätere LKW/Kombi, Entitlements serverseitig, Testzeitraum, Kündigung und Lizenzstatus. Zahlungsanbieter erst nach Zustimmung – Sandbox/Mock, keine echten Abbuchungen. Signierte Webhooks, Idempotenz, Statusabgleich. Admin-Dashboard. Abo-Ablauf darf keine laufende sicherheitskritische Operation abrupt unterbrechen.

## Umsetzung

### Tarife & Entitlements

- Statischer Katalog `apps/api/app/data/subscription_plans.py`
- PKW: `pkw_trial`, `pkw_basic`, `pkw_pro` (verfügbar)
- LKW/Kombi: `lkw_planned`, `kombi_planned` – nicht buchbar
- Serverseitige Feature-Keys; Prüfung über `/api/subscriptions/me/entitlements/{feature}`

### Zahlung (Stub)

- Provider `mock` – klar als **SIMULATION / STUB** gekennzeichnet
- HMAC-Webhooks `POST /api/billing/webhooks/mock` + Demo-Signatur
- Idempotenz über `event_id`; ungültige Signatur → 401
- Events: paid, payment_failed → `past_due` (Grace), canceled, renewed, expired
- **Kein** Stripe/PayPal/Adyen o. Ä.

### Kündigung & kritische Ops

- Kündigung zum Periodenende oder sofort
- `critical_operation_locks`: laufende Ops dürfen nach Abo-Ende noch `finish`en
- Neue Starts bei `past_due` / `canceled` / `expired` → 402

### Mandanten

- Selbstregistrierung `POST /api/tenants/register` (Demo-Flag Pflicht)
- Einladungen + Accept; Gerätebindung mit Limit pro Tarif
- Isolation: Cross-Tenant Einladungen/Geräte nicht sichtbar

### Admin

- Plattform-Admin (`is_platform_admin` auf Seed-Admin)
- `/api/admin/dashboard|users|subscriptions|audit|support`
- UI `/admin`, Abo-UI `/subscriptions` (Designsystem 10B)

### Persistenz

- Alembic `010_phase13` – subscriptions, invitations, devices, webhooks, critical ops, tenant_registrations, `users.is_platform_admin`

## Tests

| Suite | Ergebnis |
|-------|----------|
| `pytest tests -q` | **104 passed** (+7 Phase 13) |
| `apps/web` `npm run build` | **OK** |

Abnahme: Berechtigungen (Tech ≠ Admin ≠ Platform), Mandantenisolation, Webhook-Replay, Kündigung ohne Abrupt-Abbruch, Zahlungsausfall → neue Ops gesperrt.

## Rechtliches / Blocker

| Thema | Status |
|-------|--------|
| Echter Payment-Provider | **nicht** angebunden (BLK-PAY) – Zustimmung ausstehend |
| DACH Rechnung/Steuer/AVV | offen (BLK-LEGAL) – keine Konformität behauptet |
| LKW-Tarif | geplant, nicht freigegeben |

## Bewusst nicht

- **Phase 14 nicht gestartet**
- Keine echten Abbuchungen / kein Prod-PSP
- Kein Prod-Deploy

## Geänderte Bereiche (Auszug)

- `apps/api/app/models/subscriptions.py`, `services/subscriptions.py`, `services/payment_stub.py`, `services/admin_platform.py`
- Routes: `subscriptions`, `invitations`, `billing`, `admin`; Migration `010_phase13`
- `apps/web`: `SubscriptionsPage`, `AdminPage`, Nav/API-Client
- `tests/api/test_phase13_subscriptions.py`
- Docs: requirements, capabilities, phase-status, DIAGNOVA_PROGRESS, dieser Bericht
