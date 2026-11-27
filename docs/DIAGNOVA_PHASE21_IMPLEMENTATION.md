# Phase 21 – Implementierungsübersicht

## Connector (C#)

| Modul | Pfad |
|-------|------|
| CDP+ Protocol/Session | `apps/windows-connector/.../Adapters/DelphiCdp/` |
| Firmware-Store (kein Flash) | `CdpFirmwareManager.cs` |
| OBD-DIAG Stub | `Adapters/ObdDiag/ObdDiagAdapterService.cs` |
| Probe | `DiagNova.CdpProbe` |
| OBD-II Session | `Obd/ObdSession.cs` |
| Adapter-Registry | `Adapters/AdapterRegistry.cs` |

## API (Python)

| Modul | Pfad |
|-------|------|
| Commerce | `app/api/routes/commerce.py`, `services/commerce/` |
| Stripe | `services/payments/stripe_provider.py`, `/api/billing/stripe/*` |
| Lizenzen | `services/license_management.py` |
| E-Mail | `services/email_service.py` |
| Admin | `services/admin_platform.py` |

## UI

| Seite | Pfad |
|-------|------|
| Commerce | `apps/web/src/pages/CommercePage.tsx` |
| Admin | `apps/web/src/pages/AdminPage.tsx` |

## Bewusst nicht

- Kein Auto-Firmwareflash
- Keine Live-Charges ohne Freigabe
- Keine erfundenen Fahrzeug-/Zahlungserfolge
