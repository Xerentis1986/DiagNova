# Phase 25 – Technische Evidenz

**Branch:** `cursor/diagnova-phase-25-mollie-adapters-01c8`  
**Basis:** Phase 24 tip `ab23248` / PR #35  
**Stand:** 2026-11-28 (Europe/Vienna)

## Änderungen
- Stripe entfernt → **Mollie** (Status, Connection-Test via `profiles/me`, Checkout-Gate, Webhook-Pfad); Alt-Stripe-Routen: Shim `removed` / Replacement Mollie
- Admin-UI: Mollie-Panel + Verbindungstest (keine Live-Charges)
- Keys nur Env (`MOLLIE_API_KEY`, `MOLLIE_LIVE_CHARGES_ALLOWED`) – nie Git
- RSA: Demo-Private default **aus** (`DIAGNOVA_LICENSE_ALLOW_DEMO_PRIVATE=0`); Skript `scripts/generate_license_rsa_keys.py` → `.secrets/license/` (gitignored)
- UNSIGNED Installer bewusst belassen; Signing optional (Privatperson) – siehe Laienleitfaden
- BT-Adapter: **Vgate iCar Pro 2S** (ELM327 V2.3, ca. 38–42 €) in Registry + Treiberpfad (ELM327 AT only; HW hier NOT TESTED)
- AT: technische Defaults + `AT_LEGAL_TECHNICAL.md` – **keine Rechtsfreigabe**

## Tests (lokal)
| Suite | Ergebnis |
|---|---|
| `dotnet test -c Release` (windows-connector) | **59 passed**, 0 failed |
| `npm run build` (web) | **OK** |
| `pytest tests/api` | **162 passed** (nach Fix Mollie-Assertions in Phase-13/21) |
| Phase-25 Mollie-Subset | covered in `tests/api/test_phase25_mollie.py` |
| Phase-25 Vgate C# | `Phase25VgateAdapterTests.cs` |

## Follow-up (Betreiberkonsole + Mollie-UI)
- `/operator` Betreiberkonsole (RBAC platform_admin); `/admin` → Redirect
- Mollie-Key im UI → Secret-Store (Fernet); Verbindungstest
- CDP+ `inventory-probe`; Hardware-Probe Proxy `GET /api/admin/hardware-probe`
- Kunden-Nav ohne Admin-Link

## GO/NO-GO
**NO-GO** für Produktion: kein Live-Mollie-Key, kein physischer Vgate/CDP+/OBD-HW-Test in dieser Umgebung, keine juristische Freigabe AT, UNSIGNED Installer, Demo-Private bewusst aus.

## Betreiberhandlungen
Siehe `docs/DIAGNOVA_PHASE25_OPERATOR_ACTIONS.md`.
