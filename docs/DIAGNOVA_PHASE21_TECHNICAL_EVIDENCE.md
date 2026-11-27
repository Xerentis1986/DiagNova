# DIAGNOVA Phase 21 – Technische Evidenz (Bestandsaufnahme)

**Erstellt:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-21-billing-adapters-e3f2`  
**Commit-Stand bei Prüfung:** HEAD nach Produktfertigstellung (PR #32)  
**Methode:** Quellcode-Inspektion + automatisierte Tests. Keine Hardware, keine Stripe-/SMTP-Keys, kein Prod-Deploy.

### Ampel-Legende

| Kennzeichen | Bedeutung |
|-------------|-----------|
| **A** | Vollständig implementiert und automatisiert getestet |
| **B** | Implementiert, aber noch nicht (HW-/Integrations-)getestet |
| **C** | Teilweise implementiert |
| **D** | Nur vorbereitet oder simuliert |
| **E** | Nicht implementiert |

### Gesamttests (diese Prüfung)

| Suite | Ergebnis | Zeitpunkt (Europe/Vienna) |
|-------|----------|---------------------------|
| `pytest tests/` | **159 passed** | 2026-11-28 ~00:20 |
| `dotnet test` Connector | **46 passed** | 2026-11-28 ~00:20 |

---

## 1. Delphi-/Autocom-Treiber + Protokollrecherche + Firmware

**Klassifikation: C (teilweise) – Safe-Reads A (Unit), Live/CAN/Flash E**

### Quellcode

| Artefakt | Pfad |
|----------|------|
| ASCII-Codec | `apps/windows-connector/DiagNova.Connector/Adapters/DelphiCdp/CdpProtocol.cs` |
| Session + Allowlist | `…/CdpSession.cs` |
| Fake- / FTDI-Transport | `…/ICdpTransport.cs` (`FakeCdpTransport`, `FtdiCdpTransport`) |
| Fassade | `…/DelphiCdpAdapterService.cs` |
| Kompatibilitätsmatrix | `…/CdpCompatibility.cs` |
| Firmware-Store | `…/CdpFirmwareManager.cs` |
| Probe-EXE | `apps/windows-connector/DiagNova.CdpProbe/Program.cs` |
| Katalogeintrag | `…/Adapters/AdapterCompatibility.cs` (`delphi-autocom`) |
| Registry-Auswahl | `…/Adapters/AdapterRegistry.cs` |

### Klassen (Kern)

`CdpProtocol`, `CdpResponse`, `CdpSession`, `CdpIdentity`, `FakeCdpTransport`, `FtdiCdpTransport`, `DelphiCdpAdapterService`, `CdpCompatibility`, `CdpFirmwareManager`, `FirmwarePackageMeta`

### Connector-API

| Methode | Pfad | Verhalten (geprüft im Code) |
|---------|------|------------------------------|
| GET | `/adapters/delphi-cdp/status` | Status + Research-Links |
| GET | `/adapters/delphi-cdp/compatibility` | Matrix inkl. 2017.R3 / 2020.23 |
| GET | `/adapters/delphi-cdp/encode-demo` | Framing-Beispiele |
| POST | `/adapters/delphi-cdp/identify-sim` | Fake-Transport Identität |
| POST | `/adapters/delphi-cdp/open-live` | **schlägt fehl** ohne D2XX/HW |
| POST | `/adapters/delphi-cdp/vehicle-command` | **403** fest |
| GET | `/adapters/delphi-cdp/firmware` | Store-Status, `auto_flash=false` |
| POST | `/adapters/delphi-cdp/firmware/import` | Hash-Import nur mit Rechtebestätigung |
| POST | `/adapters/delphi-cdp/firmware/flash` | **403**, nicht implementiert |

### Funktionalität (nicht nur Dateien)

- Framing `*<cmd>[_args]\r` Encode/Parse inkl. Batterie `/100` – **funktioniert** (Unit-Tests).
- Safe-Reads `200/201/203/20A` über Fake – **funktioniert**.
- `FtdiCdpTransport.OpenAsync` wirft bewusst `InvalidOperationException` – **kein** echter USB-Bulk.
- CAN/`668`/`606`/`608`/`609` – **gesperrt**.
- Firmware: Import+SHA256 ja; Flash nein; kein Auto-Update; Paarung 2017↔2020 nur dokumentiert, **nicht** verifiziert.
- GPL: smooker/obd **nicht** kopiert (eigene Implementierung) – Docs `DIAGNOVA_DELPHI_LICENSE_REVIEW.md`.

### DB

Keine Delphi-spezifischen Tabellen (Connector-lokal).

### Tests

| Test | Datei |
|------|-------|
| Encode/Parse/Battery/Serial-Prefix | `Phase21DelphiCdpTests.cs` |
| Fake Identity Session | `Phase21DelphiCdpTests.cs` |
| CAN blockiert | `Phase21DelphiCdpTests.cs` |
| FTDI open fail | `Phase21DelphiCdpTests.cs` |
| Firmware Import/Flash 403 | `Phase21FirmwareAndObdDiagTests.cs` |
| Katalog PartiallySupported | `Phase21AdapterRegistryTests.cs` |

### Recherche-Docs

`docs/DIAGNOVA_DELPHI_GITHUB_RESEARCH.md`, `PROTOCOL_SPEC.md`, `DRIVER_STATUS.md`, `HARDWARE_TEST.md`, `LICENSE_REVIEW.md`, `AUTOCOM_STATUS.md`

---

## 2. OBD DIAG 2055+

**Klassifikation: D (vorbereitet/blocked) – Treiber E**

### Quellcode

| Artefakt | Pfad |
|----------|------|
| Status-Service | `…/Adapters/ObdDiag/ObdDiagAdapterService.cs` |
| Katalog | `AdapterCompatibility.cs` → `obd-diag-2055` = `BlockedUndocumented` |
| Endpunkte | `Program.cs` `/adapters/obd-diag/status`, `/probe-guidance` |

### Funktionalität

- Kein Transport, kein Serial-Protokoll, **keine** ELM-Annahme.
- Auswahl über Registry für blocked Adapter → **wird verweigert** (getestet).
- VID/PID/COM: unbekannt – Inventur offen.

### Tests

`Phase21FirmwareAndObdDiagTests.ObdDiag_Remains_Blocked_Without_Invented_Success`  
`Phase21AdapterRegistryTests.Select_Blocked_Adapter_Does_Not_Switch`

### Docs

`docs/DIAGNOVA_OBD_DIAG_2055_STATUS.md`

---

## 3. Windows-Connector und Installationsdatei

**Klassifikation: C – Laufzeit/API weitgehend A (Unit/Fake); Installer E; Publish-Skript dokumentiert B**

### Quellcode / Projekte

| Projekt | Pfad |
|---------|------|
| Connector Host | `apps/windows-connector/DiagNova.Connector/` |
| Tests | `apps/windows-connector/DiagNova.Connector.Tests/` |
| CdpProbe | `apps/windows-connector/DiagNova.CdpProbe/` |
| Solution | `apps/windows-connector/DiagNova.Connector.sln` |

### Kernklassen

`Program` (Minimal API), `AdapterConnectionManager`, `AdapterRegistry`, `Elm327DriverPrep`, `ObdSession`, `ClearDtcGate`, `PairingService`, `LocalAuthService`, `OriginGuard`, `UpdateService`, `SerialTransportFactory`, `FakeSerialTransport`, Discovery-Scanner (COM/USB/BT)

### Auth / Sicherheit Connector

- Loopback `http://127.0.0.1:8765`
- Pairing + Bearer (außer `/pair*`)
- Allowlist OBD-Befehle

### Installer

| Erwartung | Ist |
|-----------|-----|
| MSI / Inno / WiX Artefakt im Repo | **fehlt** |
| Self-contained publish Anleitung | `apps/windows-connector/README.md`, `docs/connector-installer.md` |
| Code-Signing | **nicht** konfiguriert (`software_update_signing_cert_configured=false`) |

### Tests

46 Dotnet-Tests gesamt inkl. Auth/Inventory, ObdSession, Phase05/14/21.

---

## 4. Echte OBD-II-Diagnose und Live-Daten

**Klassifikation: C – Connector-Engine A (Fake-Unit); Web/API Live-Pfad D (Simulator); HW B/E**

### Connector (kann echte COM-Antworten parsen)

| Endpunkt | Implementierung |
|----------|-----------------|
| POST `/obd/init` | `AdapterConnectionManager.InitObdAsync` → `ObdSession` |
| GET `/obd/live` | `ReadLiveAsync` |
| GET `/obd/dtcs` | stored/pending/permanent |
| GET `/obd/freeze-frame` | |
| GET `/obd/readiness` | |
| GET `/obd/vin` | |
| POST `/adapter/connect/com` | System-COM möglich |
| POST `/adapter/connect/fake` | Simulator |

Klassen: `ObdSession`, `ObdResponseParser`, `ObdPidScaler`, `ObdCommandAllowlist`, `ObdSimulatorResponses`, `ClearDtcGate`

### Web/API (Diagnose-UI)

| Endpunkt | Datenquelle |
|----------|-------------|
| GET `/api/diagnostics/{vehicle_id}/live` | **`simulator.live_data`** → immer `data_source=simulated` |
| GET `/api/diagnostics/{vehicle_id}/dtcs` | Simulator |
| Sessions | Simulator |

Pfad: `apps/api/app/api/routes/diagnostics.py`, `apps/api/app/services/simulator.py`  
UI: `apps/web/src/pages/DiagnosticsPage.tsx` ruft `api.live(vehicleId)` auf dem **Backend-Simulator**, nicht den Connector `/obd/live`.

### Funktionale Lücke

Es gibt **keine** serverseitige Bridge, die Web-Live-Daten aus dem Windows-Connector speist. „Echte“ Live-Daten erfordern direkten Connector-Aufruf (lokal) – in der Web-Oberfläche derzeit Demo.

### Tests

- Connector: `ObdSessionTests` (Parser, Scaler, Fake-Session Init/Live/DTC/FF/VIN/Clear-Gate)
- API: `test_phase04_clear_dtc.py` (Simulator-Clear)

---

## 5. Herstellerdiagnose, Service, Codierung

**Klassifikation: D (Architektur/Simulation) – Live-Schreiben E (hart gesperrt)**

### Hersteller / Multi-ECU / UDS

| Bereich | Pfad | Status |
|---------|------|--------|
| Protokollkatalog | `apps/api/app/api/routes/protocols.py` | Docs/Overview |
| Diagnosedaten DB | `routes/diagnostic_data.py`, Models `diagnostic_data.py` | Import/Quarantäne |
| Connector Multi-ECU | `Ecu/MultiEcuService.cs` | aus beobachteten Frames, kein Blindscan (`/ecu/blind-scan` → abgelehnt) |

### Service

| Endpunkt | Verhalten |
|----------|-----------|
| GET `/api/service/catalog` | Katalog |
| POST `/api/service/procedures/{code}/start` | simulierte Runs |
| POST `/api/service/procedures/{code}/execute-live` | **blockiert** (`execute_live_blocked`) |

Dateien: `routes/service.py`, `models/service.py`, Tests `test_phase11_service.py`

### Codierung

| Endpunkt | Verhalten |
|----------|-----------|
| Katalog / Identify / Compatibility | vorhanden |
| start/abort Runs | Simulation |
| `/execute-live`, `/flash` | **blockiert** |

Dateien: `routes/coding.py`, `models/coding.py`, Tests `test_phase12_coding.py`

---

## 6. DiagNova Betreiber-Backend

**Klassifikation: C – Admin-Dashboard A (API-Tests); MFA E; Trennung Plattform/Werkstatt A**

### API

| Pfad | Datei |
|------|-------|
| `/api/admin/dashboard` | `routes/admin.py` → `admin_platform.build_admin_dashboard` |
| `/api/admin/users` | |
| `/api/admin/subscriptions` | |
| `/api/admin/audit` | |
| `/api/admin/support` | |

### UI

`apps/web/src/pages/AdminPage.tsx` (nur `is_platform_admin`)

### Kennzahlen (Code)

workshops, users, customers B2B/B2C, Abos, Trial, MRR/ARR (Katalog-Näherung `price_cents_demo`), Rechnungen open/paid/overdue, Geräte, Stripe-Status-Block – **aus DB**, keine erfundenen Zahlungseingänge.

### Fehlend

- MFA für Betreiber (**E**)
- Dedizierte Betreiber-App getrennt vom Werkstatt-Frontend (gleiche Web-App, Rollen-Gate) – **C**

### Tests

`test_phase13_subscriptions.py::test_admin_dashboard_platform_only`  
`test_phase21_stripe_licenses.py::test_admin_dashboard_has_commerce_metrics`

---

## 7. B2B- und B2C-Kundenverwaltung

**Klassifikation: C – Commerce-Accounts A (API); Werkstatt-Kunden A; Deep-Link Zahlung/Geräte C**

### Commerce-Konten (kaufmännisch)

| Tabelle | Model |
|---------|-------|
| `billing_accounts` | `models/commerce.py::BillingAccount` |
| `consent_records` | `ConsentRecord` |
| `vat_check_logs` | `VatCheckLog` |

API Prefix `/api/commerce`: `POST/GET /accounts`, Contract, Licenses, Cancel  
Service: `services/commerce/billing.py`  
UI: `CommercePage.tsx`  
Migration: `alembic/versions/014_phase21_commerce.py`

### Werkstatt-Kunden (operativ)

`/api/customers/*` – CRUD, Merge, Export, Delete – `models` Workshop-Kunden (Phase 08)  
Tests: `test_phase08_workshop_customers.py`, `test_phase21_commerce.py`

### Grenzen

- Commerce-Accounts setzen `is_example_data=True` / `payment_method=mock` bei Subscribe-Pfad.
- Keine vollständige CRM-Historie Zahlung↔Lizenz über alle Kanäle vereinheitlicht.

---

## 8. Abonnementverwaltung

**Klassifikation: C – Stub-Abo A; Stripe-Sync C; Auto-Renew echte PSP E ohne Keys**

### Tabellen

`subscriptions`, `workshop_invitations`, `critical_operation_locks`, `tenant_registrations` (`models/subscriptions.py`)  
Tarife: `app/data/subscription_plans.py` (`pkw_trial`, `pkw_basic`, `pkw_pro`, geplante LKW…)

### API

`/api/subscriptions/*` – plans, me, trial, activate-stub, cancel, devices, entitlements, critical-ops  
Commerce: `POST /accounts/{id}/subscribe` erzeugt Subscription + Invoice (Stub)

### Tests

`test_phase13_subscriptions.py`, Commerce-Subscribe in `test_phase21_commerce.py`

---

## 9. Stripe-Integration

**Klassifikation: C – Codepfad A (Unit/API ohne Keys); Ende-zu-Ende mit Stripe E (keine Keys)**

### Code

| Datei | Inhalt |
|-------|--------|
| `services/payments/stripe_provider.py` | Status, Checkout (httpx), Webhook+Signatur, Idempotenz |
| `routes/billing.py` | `/stripe/status`, `/stripe/checkout`, `/webhooks/stripe` |
| Config | `stripe_secret_key`, `stripe_publishable_key`, `stripe_webhook_secret`, `stripe_live_charges_allowed=false` |

### Funktionalität geprüft

- Ohne Keys: `configured=false`, Checkout → `ok=false`, `status=not_configured` (**kein Fake-Success**) – getestet.
- Signaturhelper `verify_stripe_signature` – Unit-getestet.
- Live-Charges: Flag default false.
- Webhook-Verarbeitung gegen echte Stripe-Events: **nicht** ausgeführt (keine Secrets).

### Tabelle

`payment_webhook_events` (provider `stripe` | `mock`)

---

## 10. Rechnungsstellung + AT/EU-Steuer

**Klassifikation: C – Steuerengine A (Unit); Rechnungen JSON A; PDF E; Prod-Steuerfreigabe E**

### Steuer

| Datei | Rolle |
|-------|-------|
| `services/commerce/tax_engine.py` | `resolve_tax` |
| `data/tax_rules_at.py` | Seed, OSS-Demo-Sätze, Disclaimers |
| Tabelle `tax_rule_snapshots` | Persistenz-Seed |

Szenarien implementiert: `b2c_at`, `b2b_at`, `b2b_reverse_charge`, `b2b_eu_uid_required`, `b2c_eu_oss`, `third_country` – alle `review_status=draft_needs_review`.

VIES: `services/commerce/vies.py` – Stub default, Live optional `VIES_LIVE` (nicht in dieser Prüfung aktiv).

### Rechnungen

Tabelle `invoices` – Subscribe erzeugt Invoice; Credit Notes; Download **nur JSON** (`Content-Disposition …json`).  
**Kein** Rechnungs-PDF trotz reportlab für Diagnoseberichte.

### Tests

`test_tax_preview_scenarios`, B2B/B2C Subscribe+Invoice in `test_phase21_commerce.py`

---

## 11. Lizenz- und Geräteverwaltung

**Klassifikation: C – API A (teilweise getestet); Connector-Offline-Enforcement C**

### Code

`services/license_management.py`  
API: `/api/billing/licenses/overview|activate-device|verify`  
Tabelle: `device_bindings`  
Phase-13 Devices auch unter `/api/subscriptions/...`

### Funktionalität

- Activate/Verify an Abo-Status gekoppelt (`trialing`/`active`).
- Offline-Toleranz **72h als Hinweis**, keine kryptografische Offline-Lizenzdatei.
- Connector-seitige Pflichtprüfung vor jedem OBD-Befehl gegen Backend: **nicht** als hartes Gate in `ObdSession` verdrahtet (Allowlist lokal; Lizenz eher Web/Billing).

### Tests

Stripe/Lizenz-Datei prüft Overview indirekt über Admin; dedizierte Activate-Tests minimal – Signatur/Status getestet. **Empfehlung:** weitere API-Tests Activate/Verify (sicher nachrüstbar).

---

## 12. E-Mail-Versand

**Klassifikation: C – Templates+dry_run A; SMTP optional B; Auth-Flows E**

### Code

`services/email_service.py` – Templates: registration, email_confirm, password_reset, subscription_confirm, invoice, payment_reminder, cancellation, license_activation, security_alert  
API: `/api/billing/email/status`, `/send-template` (default `force_dry_run=true`)

### Nicht verdrahtet

- `auth.py` Login/Register ruft **kein** `send_template_email` auf.
- Keine automatische Rechnungsmail nach Subscribe.
- SMTP-Env leer → nur dry_run (getestet).

---

## 13. Sicherheit, Updates und Deployment

**Klassifikation: C**

### Sicherheit (API)

| Thema | Status | Nachweis |
|-------|--------|----------|
| JWT Auth | A | `routes/auth.py`, Tests |
| Rollen / Plattform-Admin | A | Admin 403 für Tech |
| Mandantentrennung | A | Phase 08/15 Tests |
| Rate-Limits | A/C | Config + Phase 15 |
| Audit-Log | A | `services/audit.py` |
| MFA Betreiber | **E** | keine Treffer `mfa`/`totp` |
| Secrets | C | Env/Settings, Demo-Secrets |

### Updates

| Ebene | Status |
|-------|--------|
| Diagnosedaten-Updates | A (Staging/Approve/SSRF) Phase 07 |
| Software-Updates API | A/C Busy-Gate, HMAC-Demo, Auto-Install aus | Phase 14 |
| Connector UpdateService | C | lokal, Signing-Flag false |
| Code-Signing Prod | **E** | |

### Deployment

| Artefakt | Status |
|----------|--------|
| `docker-compose.yml` / `docker-compose.prod.yml` | vorhanden |
| Phase-16 Deploy-Docs/Checklist | Docs |
| Prod-Redeploy dieser Phase | **nicht** ausgeführt (Freigabe) |

Tests: `test_phase15_security.py`, `test_phase14_software_updates.py`, `test_phase07_data_updates.py`

---

## Querschnitt: Was die UI wirklich tut

| UI-Seite | Datenrealität |
|----------|---------------|
| Diagnostics | Backend-Simulator |
| Commerce | Stub-Rechnung + Steuerpreview |
| Admin | echte DB-Zähler + Stripe-Status-Objekt |
| Service/Coding | Simulation; Live 403 |
| Subscriptions | Stub-Zahlung klar gekennzeichnet |

---

## Behobene Punkte in dieser Prüfung (ohne HW/Keys)

1. `GET /api/commerce/overview` listet jetzt ehrlich `stripe`-Status und `missing_de` (PDF, SMTP, Steuer, Live-Charges) – statt nur „kein PSP“.
2. Connector-README: Delphi-Hinweis von „nicht angebunden“ auf CDP+ Safe-Read-Stand korrigiert.

---

## Vollständige Liste fehlender Implementierungen und Freigaben

### Implementierungslücken (Code)

1. Echter FTDI/D2XX-Bulk-Transport für CDP+ (heute Fail-Stub)
2. CDP+ CAN/Init/Relais – bewusst gesperrt; Freigabe + Spec nötig
3. Firmware-Flash-Pfad (heute 403)
4. OBD-DIAG 2055+ Treiber nach Geräteinventur
5. Web/API-Bridge: Live-Daten aus Connector statt nur `simulator.py`
6. Rechnungs-PDF + E-Mail-Versand angebunden an Subscribe/Stripe
7. Auth-Flows: E-Mail-Bestätigung, Passwort-Reset mit echtem Versand
8. MFA für Plattform-Admins
9. Windows-Installer-Artefakt (MSI/Setup) + Code-Signing
10. J2534 echte DLL-Bindung (nur Abstraktion)
11. Service/Coding Live-Schreiben (gesperrt)
12. Connector-seitige serverseitige Lizenzprüfung vor Diagnosebefehlen
13. Stripe Ende-zu-Ende mit Test-Keys (Checkout+Webhook) – Code da, Keys fehlen
14. VIES Live-Betrieb abgesichert produktiv
15. Steuerregeln aus `draft_needs_review` → fachlich freigegeben
16. Einheitliche Betreiber-Oberfläche (optional separate Admin-App)

### Externe Freigaben / Labor

| ID | Thema |
|----|-------|
| BLK-HW | Adapter + Fahrzeugtests |
| BLK-OEM | OEM-Daten/Rechte |
| BLK-LOGO | Markenlogos |
| BLK-PAY | Stripe-Keys + Live-Freigabe |
| BLK-LEGAL | AVV, AGB, Widerruf, Steuer |
| BLK-CERT | Code-Signing |
| BLK-DEPLOY | Prod-Redeploy |
| BLK-RELEASE | Gesamtabnahme Verkauf |

### Verdict

**Kein „fertig“ für kommerziellen Betrieb.** Automatisierte Tests grün (159/46). Wesentliche produktive Diagnose- und Zahlungswege sind simuliert, geblockt oder ohne Keys/HW nicht nachweisbar.

Siehe auch: `DIAGNOVA_RELEASE_BLOCKERS.md`, `DIAGNOVA_RELEASE_READINESS.md` (wird auf dieses Dokument verwiesen).
