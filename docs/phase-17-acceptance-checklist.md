# Phase 17 – Abnahme-Checkliste (Gesamtabnahme)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Branch:** `cursor/diagnova-phase-17-acceptance-8ffe`  
**Basis:** Phase 16 `cursor/diagnova-phase-16-deploy-8876` (PR #25)  
**Regel:** **STOP** vor produktivem Voll-Rollout. Kein Flash-/Service-Live, kein Server-Redeploy neuer Phases ohne Coordinator-/Betreiberfreigabe. Keine Bosch/Gutmann-Gleichwertigkeit.

Statuslegende: ✅ erledigt · 🟡 simuliert / Docs · 🔴 blockiert · ⬜ offen (Freigabe)

---

## A. Durchgängiger Demo-Ablauf (simuliert)

| # | Schritt | Nachweis | Status |
|---|---------|----------|--------|
| A1 | Login Admin / Technician | `test_login_*`, Live Login-UI vorhanden | 🟡 |
| A2 | Marke → Modell → Variante → Bestätigen | API + E2E Phase 02 | 🟡 |
| A3 | Adapter/Verbindung (Simulator) | `GET /api/connection` `mode=simulator` | 🟡 |
| A4 | Live-Diagnose (PIDs/DTC/FF/Readiness) | Simulator + Protocol-Tests | 🟡 |
| A5 | Sitzung schließen → Historie | Phase 09 Tests | 🟡 |
| A6 | PDF/CSV erzeugen → Wiederaufruf | Phase 10 Tests | 🟡 |
| A7 | Demo-Kennzeichnung durchgängig | `data_source=simulated`, Demo-WM | 🟡 |

**Hardware-Live-Äquivalent A1–A7:** 🔴 BLK-HW – nicht freigegeben.

---

## B. Fehlerfälle & Sicherheit

| # | Check | Nachweis | Status |
|---|-------|----------|--------|
| B1 | Falsches Passwort / ungültiges JWT | Auth-Tests | 🟡 |
| B2 | Cross-Tenant → 404 | Phase 08/15 IDOR-Tests | 🟡 |
| B3 | Login-Rate-Limit → 429 | Phase 15 | 🟡 |
| B4 | Audit-Redaction (Passwort/VIN/E-Mail) | Phase 15 | 🟡 |
| B5 | Origin-Check / CSRF-nahe Header | Phase 15 | 🟡 |
| B6 | Clear-DTC ohne Freigabe-Token | Phase 04 Gate | 🟡 |
| B7 | Blindscan → 403 | Phase 05 | 🟡 |
| B8 | Flash/Schreiben → 403 | Phase 12 | 🟡 |
| B9 | ODX-Import → 403 | Phase 06 | 🟡 |
| B10 | Prod-Auto-Update ohne Zertifikat gesperrt | Phase 14 | 🟡 |

---

## C. Datenupdates, Mandant, Abo, Backup, Deploy

| # | Check | Nachweis | Status |
|---|-------|----------|--------|
| C1 | Diagnosedaten Import Preview/Apply/Rollback | Phase 06 | 🟡 |
| C2 | Daten-Update Staging/Freigabe (keine echten Feeds) | Phase 07 | 🟡 |
| C3 | Mandantenisolation / Rollen | Phase 08/13 | 🟡 |
| C4 | Abo-Entitlements (Stub-Zahlung) | Phase 13 – kein PSP | 🟡 / 🔴 BLK-PAY |
| C5 | Backup/Restore dokumentiert | Phase 15/16 Docs + Skripte | 🟡 |
| C6 | Deploy-Pfad dokumentiert | Phase 16 Install/Checkliste | 🟡 |
| C7 | Live Smoke `/` + `/health` | 200 (read-only) | ✅ |
| C8 | Produktiv-Redeploy Phase 15–17 | nur mit Freigabe | ⬜ STOP |

---

## D. Abdeckungsmatrix (Marke / Funktion / Adapter)

| Bereich | Implementiert | Simuliert getestet | Hardwaregetestet | Freigegeben | Blocker |
|---------|---------------|--------------------|------------------|-------------|---------|
| Markenkatalog DACH (Navigation) | ja | ja | n/a | nein (Pilot Demo) | BLK-LOGO |
| Demo-Fahrzeuge / Seed | ja | ja | nein | nein | — |
| OEM-Diagnoseabdeckung je Marke/ECU | nein | nein | nein | nein | BLK-OEM |
| OBD-II Parser/Allowlist | ja | ja | nein | nein | BLK-HW |
| Connector Fake-Port / AT | ja | ja | nein | nein | BLK-HW |
| Delphi/Autocom / Vgate SPP | Prep/Docs | begrenzt | nein | nein | BLK-ADAPTER |
| DoIP / J2534 / CAN-FD Live | Prep | nein | nein | nein | BLK-HW |
| Service Live-Schreiben | Gates only | Gates | nein | nein | BLK-OEM, BLK-RELEASE |
| Codierung / Flash | Gates; Write/Flash aus | Gates/403 | nein | nein | BLK-OEM, BLK-J2534 |
| PDF/Akte/Mandant/Abo-Stub | ja | ja | n/a | nein | BLK-LEGAL, BLK-PAY |
| Deploy Docs/Compose | ja | Docs + Live Smoke | n/a | Redeploy offen | BLK-DEPLOY |
| Chiptuning (18) / LKW (19) | geplant | — | — | gesperrt | optional |

---

## E. Lizenzen, Datenschutz, Betrieb

| # | Thema | Status | Hinweis |
|---|-------|--------|---------|
| E1 | OEM-/ODX-Lizenzen | 🔴 | keine im Repo |
| E2 | Markenlogo-Rechte | 🔴 / Text-Fallback | BLK-LOGO |
| E3 | Freie Quellen Attribution | 🟡 | `free-data-sources.md` |
| E4 | DSGVO-Prozesse dokumentiert | 🟡 | keine Konformität behauptet (BLK-LEGAL) |
| E5 | Threat Model | 🟡 | `threat-model.md` |
| E6 | Support-/Notfall-/Update-Docs | 🟡 | Install, Backup, Software-Updates |
| E7 | Monitoring/Alerting produktiv | ⬜ | dokumentiert, nicht aktiviert |
| E8 | Staging-Subdomain | ⬜ | dokumentiert, nicht angelegt |

---

## F. Smoke-Tests dieser Phase (ausgeführt)

| Check | Befehl / URL | Ergebnis |
|-------|--------------|----------|
| pytest | `python3 -m pytest tests -q` | **126 passed** |
| Web-Build | `npm ci && npm run build` (apps/web) | **OK** (0.15.0) |
| Compose YAML | `yaml.safe_load` prod + dev | **ok** |
| Live `/` | https://diagnova.codekreativ.at/ | **200** |
| Live `/health` | …/health | **200**, `demo_mode: true`, `data_source_default: simulated` |
| Docker Compose up | — | nicht ausgeführt (BLK-DOCKER in Agent-VM) |
| .NET Connector xUnit | — | nicht erneut (keine SDK-Pflicht für Docs-Phase) |
| Playwright E2E | — | nicht erneut in dieser Phase (Suite vorhanden) |

---

## G. Go / No-Go (Kurz)

| Entscheidung | Ergebnis |
|--------------|----------|
| Öffentlicher Launch / „voll produktiv“ | **NO-GO** |
| Live-OBD / Clear / Service-Schreiben / Flash | **NO-GO** |
| Prod-Redeploy neuer Feature-Branches | **STOP** – nur nach Betreiber- + Coordinator-Freigabe |
| Pilot Demo/Simulation auf bestehendem Live | **bedingt** – nur nach expliziter Betreiberfreigabe; Scope Demo |
| Phase 18 / 19 | **nicht starten** – Coordinator orchestriert optional |

Details und Verantwortlichkeiten: [phase-17-abschluss.md](./phase-17-abschluss.md).
