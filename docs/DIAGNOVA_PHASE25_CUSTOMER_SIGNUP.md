# Kunden-Registrierung (Pilot)

## GO-Status
| Stufe | Status |
|---|---|
| **Kommerzielles Voll-GO** | **NO-GO** – Mollie-Key, SMTP, Rechtsfreigabe, HW fehlen |
| **Pilot-GO (Demo/Trial)** | **PILOT** – `pilot_mode=true`, Banner „PILOT“, `commercial_go=false` |

Health: `GET /health` → `go_status: "PILOT"`.

## Wie registriert sich ein Kunde?
1. **`/register`** – Werkstatt + Admin-User + Trial-Abo (Demo-Bestätigung Pflicht)  
   API: `POST /api/tenants/register`
2. Danach Login → **`/commerce`** – B2B- oder B2C-Billing-Konto anlegen  
3. Team: Einladung vom Werkstatt-Admin → **`/invite?token=…`**
4. Bestehend: **`/login`**

## Betreiber
- **`/operator`** – Mollie-Key, Adapter, Audit (nur Plattform-Admin)

## Fehlt für echten Self-Service (kommerziell)
- E-Mail-Verifikation / SMTP
- Mollie-Zahlung für bezahlte Pläne
- Geprüfte AGB/Widerruf/AVV
- Physische Adapter-HW-Freigabe
