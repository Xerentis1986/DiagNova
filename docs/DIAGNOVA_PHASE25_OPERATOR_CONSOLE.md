# Betreiberkonsole – Rollen & URLs

## Trennung
| Bereich | URL | Wer |
|---|---|---|
| Kundenportal + Diagnose | `/`, `/dashboard`, `/diagnostics`, … | Werkstatt-Nutzer |
| Betreiber / Admin | **`/operator`** (Alias `/admin` → Redirect) | nur `is_platform_admin` |

Kunden-Sidebar zeigt **keinen** Admin-Link. Plattform-Admin sieht Gruppe „Betreiber“ → Betreiberkonsole.

## Betreiber-Menü (Tabs unter `/operator`)
- Übersicht – Kennzahlen, Legal-Offen
- Kunden – Billing Accounts B2B/B2C
- Abos – plattformweite Subscriptions
- **Mollie** – API-Key im UI speichern (Secret-Store) + **Verbindungstest**
- Rechnungen / Lizenzen-Geräte / Updates / Adapter-Probe / Audit / MFA / Einstellungen

API-Hilfsinfo: `GET /api/admin/operator-nav`

## Mollie Speicherung
- UI: `/operator?tab=mollie`
- PUT `/api/billing/mollie/config` → verschlüsselte Datei unter `DIAGNOVA_SECRETS_DIR` (Default `.secrets/`)
- Env `MOLLIE_API_KEY` überschreibt Store
- Antworten nur maskiert; keine Klartext-Keys in Logs
- Live-Charges default aus

## MFA
- Setup/Confirm unter `/operator?tab=mfa`
- Login-Feld MFA-Code (wenn aktiv)

## Adapter-Proben
- Tab Adapter → „Hardware-Probe (Connector)“ → `GET /api/admin/hardware-probe`
- Connector: CDP+ inventur/identify-sim, OBD-DIAG inventur, Vgate connection-test
