# DiagNova – Anforderungsmatrix (Phase 00)

Stand: 2026-11-27 (Europe/Vienna)  
Basis-Code: Branch `cursor/diagnova-phase-ab-mvp-bf17` (PR #1, Phase A/B MVP)  
Inventar: siehe [capabilities.md](capabilities.md), Phasenstatus: [phase-status.md](phase-status.md)

## Statuslegende

| Status | Bedeutung |
|--------|-----------|
| `geplant` | Anforderung erfasst, noch nicht umgesetzt |
| `implementiert` | Code vorhanden, Tests/Hardware ausstehend oder teilweise |
| `simuliert getestet` | Gegen Simulator/Fake-Daten getestet (keine Hardware) |
| `hardwaregetestet` | An realem Adapter/Fahrzeug geprüft |
| `freigegeben` | Fachlich/betrieblich freigegeben |

**Hinweis:** Keine Anforderung ist `hardwaregetestet` oder `freigegeben`. Keine echten Fahrzeugdaten, Herstellerlizenzen oder Adapter-Hardware in dieser Umgebung.

## Matrix

| ID | Anforderung | Phase | Status | Quelle / Nachweis | Tests | Blocker |
|----|-------------|-------|--------|-------------------|-------|---------|
| REQ-UI-001 | Marken-Kacheln Startseite (DACH-Katalog) | 02 | geplant | Seed nur 9 Beispielmarken in `apps/api/app/db/seed.py`; keine Logo-Kacheln | – | Markenlogos/Nutzungsrechte; voller DACH-Katalog |
| REQ-UI-002 | Marke → Modell → Baureihe → Motor → Bestätigen | 02 | geplant | UI: Fahrzeugliste, kein Wizard | – | – |
| REQ-UI-003 | Suche / Favoriten / zuletzt verwendet | 02 | geplant | nicht vorhanden | – | – |
| REQ-UI-004 | Theme Hell/Dunkel/System + Persistenz | 02 | geplant | UI aktuell Dark-only (`Layout.tsx`) | – | – |
| REQ-UI-005 | VIN-Erkennung mit manueller Korrektur | 02 / 04 | geplant | VIN nur Seed/Simulator; keine Erkennung | – | Hardware/Adapter |
| REQ-UI-006 | Kennzeichen & Kilometerstand | 02 / 08 | teilweise | Kennzeichen in Seed; km nicht modelliert | API Seed | – |
| REQ-UI-007 | Verfügbare Funktionen pro Fahrzeug anzeigen | 02 | geplant | Katalog ≠ Abdeckung noch nicht modelliert | – | Diagnosedaten |
| REQ-UI-008 | Fallback-Textkacheln ohne Markenlogos | 02 | geplant | – | – | Logo-Rechte |
| REQ-CONN-001 | Windows-Connector Geräteerkennung (BT/COM/USB) | 03 | geplant | Stub ohne Hardware (`StubDiagnosticAdapter`) | – | Windows + Adapter-HW; Delphi/Autocom-Modell unbekannt |
| REQ-CONN-002 | Serieller Adaptertreiber (exklusiv, Timeout, Dispose) | 03 | geplant | nicht implementiert | – | Hersteller-Doku Adapter |
| REQ-CONN-003 | Simulator-Adapter getrennt von Live | 03 / 04 | implementiert | API-Simulator + Connector-Stub; `data_source: simulated` | API Tests | – |
| REQ-CONN-004 | Browser↔Connector Auth (Loopback, Origin, kurzlebig) | 03 | implementiert | Localhost-Auth Skelett; siehe `docs/windows-connector-auth.md` | manuell dok. | .NET-Build hier nicht ausgeführt (kein SDK) |
| REQ-CONN-005 | Adapter- vs. Fahrzeugverbindungsstatus getrennt | 03 / 04 | geplant | ein kombinierter Connection-Status | – | – |
| REQ-OBD-001 | Adapterinit & Protokollerkennung | 04 | geplant | nur Simulator | – | Hardware |
| REQ-OBD-002 | Supported-PID-Bitmap | 04 | geplant | feste PID-Liste im Simulator | Parser-Unit | Hardware |
| REQ-OBD-003 | Live-Daten (RPM, Speed, Temp, Last, Throttle, …) | 04 | simuliert getestet | `simulator.live_data` | `test_simulator_dtcs_and_live` | Hardware für Live-Freigabe |
| REQ-OBD-004 | DTCs stored / pending / permanent | 04 | simuliert getestet | stored+pending im Simulator; permanent im Typ, nicht erzeugt | API + Parser | Hardware |
| REQ-OBD-005 | Freeze-Frame | 04 | simuliert getestet | Simulator Freeze-Frame | API | Hardware |
| REQ-OBD-006 | Readiness-Monitore | 04 | simuliert getestet | Simulator readiness | API | Hardware |
| REQ-OBD-007 | VIN lesen (soweit Adapter) | 04 | simuliert getestet | Seed-VIN / Demo-VIN | API | Hardware |
| REQ-OBD-008 | Mehrere ECU-Antworten getrennt | 04 / 05 | geplant | Ein-ECU-Simulator | – | Protokoll/HW |
| REQ-OBD-009 | NO DATA / NRC / Timeout / Abbruch | 04 | geplant | nicht implementiert | – | – |
| REQ-OBD-010 | DTC-Löschung mit Freigabe, Vorher-Bericht, Nachprüfung | 04 / 11 | geplant | bewusst nicht im MVP | – | Sicherheit + Hardware |
| REQ-PROTO-001 | Transport/Protokoll/Adapter/Fahrzeugdefinition trennen | 05 | geplant | Ansatz in Packages, nicht ausgeprägt | – | Spezifikationen |
| REQ-PROTO-002 | ISO 9141-2, KWP2000, J1850, CAN, ISO-TP, UDS | 05 | geplant | nur Mode-01/03-Parser-Subset | Parser | Spez + HW |
| REQ-PROTO-003 | CAN FD / DoIP | 05 | geplant | – | – | Adapter kein Universal-Interface |
| REQ-PROTO-004 | J2534 / D-PDU Hardware-APIs | 05 / 12 | geplant | – | – | Treiber/Lizenzen |
| REQ-PROTO-005 | Steuergeräteübersicht (Motor, ABS, Airbag, …) | 05 / 11 | geplant | UI „Geplant“ | – | verifizierte Adressen |
| REQ-DATA-001 | Versioniertes Datenmodell Hersteller/Modell/ECU/DTC/PID | 06 | geplant | flaches Vehicle-Modell + JSON-Snapshots | – | – |
| REQ-DATA-002 | JSON/CSV-Import mit Schema/Quarantäne/Rollback | 06 | geplant | – | – | – |
| REQ-DATA-003 | Lizenzierte ODX/PDX-Importe | 06 | geplant | – | – | Lizenz + Spezifikation |
| REQ-DATA-004 | Freie Quellen mit Attribution/Lizenzprüfung | 06 | geplant | – | – | Rechteprüfung |
| REQ-DATA-005 | Unbekannte DTCs als unbekannt anzeigen | 06 | geplant | Katalog fest; Unbekannte nicht modelliert | – | – |
| REQ-UPD-001 | Scheduler Diagnosedaten-Updates (ETag/Hash/Retry) | 07 | geplant | – | – | Quellenrechte |
| REQ-UPD-002 | Staging, manuelle Freigabe sicherheitsrelevanter Daten | 07 | geplant | – | – | – |
| REQ-UPD-003 | Admin-Dashboard Update-Läufe | 07 / 13 | geplant | – | – | – |
| REQ-WS-001 | Werkstattprofil, Logo, Kontaktdaten | 08 | geplant | kein Mandanten-/Werkstattmodell | – | – |
| REQ-WS-002 | Benutzerrollen (CRUD, Einladungen) | 08 / 13 | teilweise | Rollen admin/technician/viewer; Seed-Login | Auth-Tests | Mandanten |
| REQ-WS-003 | Kunden & Fahrzeuge CRUD, Suche, Archiv | 08 | teilweise | Fahrzeuge read-only Liste + Seed | API | Kundenentität fehlt |
| REQ-WS-004 | Dublettenprüfung VIN/Kennzeichen | 08 | geplant | VIN unique in DB | – | – |
| REQ-WS-005 | Werkstattaufträge / Notizen / Status | 08 | geplant | Session-Notizenfeld nur | – | – |
| REQ-WS-006 | Mandanten-ID serverseitig, IDOR-Schutz | 08 / 15 | geplant | kein Tenant; alle Fahrzeuge global | – | Multi-Tenancy |
| REQ-WS-007 | Datenschutz Export/Löschung/Aufbewahrung | 08 / 15 | geplant | – | – | rechtl. Prüfung |
| REQ-HIST-001 | Digitale Fahrzeugakte / Zeitstrahl | 09 | geplant | Session-Liste rudimentär | – | – |
| REQ-HIST-002 | Automatisches Speichern nach Sitzungsende | 09 | teilweise | Session start/close + DTC-Snapshot | API | – |
| REQ-HIST-003 | Vorher/Nachher-DTC-Vergleich | 09 | geplant | – | – | – |
| REQ-HIST-004 | Messwertverlauf begrenzt speichern | 09 | geplant | nur Live-Snapshot im Report | – | – |
| REQ-PDF-001 | A4-PDF mit Werkstatt-/Fahrzeugdaten | 10 | teilweise | ReportLab A4 MVP; kein Werkstattlogo | API PDF-Test | Branding |
| REQ-PDF-002 | Demo-Wasserzeichen / Disclaimer | 10 | simuliert getestet | Disclaimer „SIMULIERTEN Daten“ | API | – |
| REQ-PDF-003 | CSV-Export | 10 | simuliert getestet | `/reports/{id}/export.csv` | API | – |
| REQ-PDF-004 | Archiv, Suche, unveränderlicher Snapshot | 10 | teilweise | Report als JSON-Snapshot; kein Archiv-UI | API | – |
| REQ-PDF-005 | Autorisierte Downloads, Mandantenschutz | 10 / 15 | teilweise | JWT nötig; kein Mandant | API | Tenant |
| REQ-SVC-001 | Servicekatalog (Ölreset, EPB, DPF, …) | 11 | geplant | UI „Geplant“; DPF-Off ausgeschlossen | – | OEM-Daten + Freigabe |
| REQ-SVC-002 | Geführte Diagnose / DTC-Hilfe | 11 | geplant | – | – | – |
| REQ-SVC-003 | Stellgliedtests / Grundeinstellungen | 11 | geplant | UI „Geplant“ | – | Sicherheit |
| REQ-COD-001 | ECU-Identifikation / Codierprofil | 12 | geplant | UI „Geplant“ | – | OEM + HW |
| REQ-COD-002 | Flash/Programmierung (deaktiviert bis Freigabe) | 12 | geplant | bewusst gesperrt | – | OEM, HW, rechtl. |
| REQ-SUB-001 | Mandantenregistrierung, Tarife, Entitlements | 13 | geplant | – | – | Zahlungsanbieter-Zustimmung |
| REQ-SUB-002 | Zahlungs-Sandbox/Mock | 13 | geplant | – | – | Zustimmung |
| REQ-SUB-003 | Admin-Dashboard Nutzer/Abos/Audit | 13 | geplant | Audit-Log Backend vorhanden | – | – |
| REQ-SW-001 | Versionierung API/Web/Connector + Kompatibilität | 14 | geplant | API version 0.1.0 | – | Signaturzertifikat |
| REQ-SW-002 | Windows-Installer, signierte Updates | 14 | geplant | – | – | Zertifikat |
| REQ-SW-003 | Keine Updates während Diagnose/Flash | 14 | geplant | – | – | – |
| REQ-SEC-001 | Threat Model Browser/API/Connector | 15 | geplant | V1-Minimum in README | – | – |
| REQ-SEC-002 | Auth: bcrypt, JWT, Rollen, CORS | 15 | simuliert getestet | `security.py`, Auth-Routes | Auth-Tests | CSRF/Cookies noch nicht |
| REQ-SEC-003 | Rate Limits, IDOR, SSRF-Schutz | 15 | geplant | – | – | – |
| REQ-SEC-004 | Audit ohne Secrets/unnötige PII | 15 | teilweise | `audit_logs` bei Login/Session/Report | – | Review PII |
| REQ-SEC-005 | DSGVO-Prozesse dokumentieren (keine Konformitätsbehauptung) | 15 | geplant | – | – | rechtl. Beratung |
| REQ-SEC-006 | Backup/Restore praktisch testen | 15 / 16 | geplant | Postgres-Volume in Compose | – | – |
| REQ-DEP-001 | Docker Compose (api, web, postgres) | 16 | implementiert | `docker-compose.yml` | Compose hier **nicht** ausgeführt (kein Docker) | Docker auf Zielhost |
| REQ-DEP-002 | World4You Ubuntu/Plesk Staging | 16 | geplant | Domain/DB vorbereitet (Projektkontext); kein produktives Deploy | – | Freigabe; Secrets lokal |
| REQ-DEP-003 | HTTPS Reverse Proxy / WebSocket | 16 | teilweise | nginx `web.conf` HTTP-Proxy; kein TLS in Repo | – | Plesk/TLS |
| REQ-DEP-004 | Keine produktiven Deploys ohne Zustimmung | 16 / 17 | implementiert (Regel) | Arbeitsregel; Phase 00 kein Deploy | – | – |
| REQ-ACC-001 | End-to-End Gesamtabnahme | 17 | geplant | – | – | vorherige Phasen |
| REQ-ACC-002 | Abdeckungsmatrix Marke/Modell/ECU/Adapter | 17 | geplant | – | – | Hardware + Daten |
| REQ-TUN-001 | Optionales Chiptuning (nur Verwaltung, Flash gesperrt) | 18 | geplant | optional später | – | rechtl./technisch |
| REQ-LKW-001 | LKW/Nutzfahrzeuge J1939/RP1210 | 19 | geplant | optional später | – | 24-V-HW, Spez |
| REQ-CMP-001 | Diagnosevergleich Sitzungen | 09 | geplant | – | – | – |
| REQ-CMP-002 | Live-Daten-Diagramme UI | 04 / 02 | teilweise | Recharts im Web; Live-Poll Simulator | Web-Build | Hardware |
| REQ-LIC-001 | Lizenzherkunft Diagnosedaten nachvollziehbar | 06 / 07 | geplant | keine OEM-Daten im Repo | – | Quellenrechte |
| REQ-HW-001 | Delphi/Autocom-Interface (Modell unbekannt) | 03 | geplant | **fehlende Hardware/Dokumentation** | – | genaues Modell + Doku |
| REQ-HW-002 | Vgate vLinker MC+ (Windows-SPP) | 03 | geplant | **nicht geprüft** | – | Herstellerdoku |
| REQ-DEMO-001 | Demo vs. Live strikt trennen | 00 / alle | simuliert getestet | `data_source`, SimBanner, Health | API + UI | Live noch nicht existent |

## Aggregat

| Status | Anzahl (ca.) |
|--------|--------------|
| geplant | Mehrheit der REQ-* |
| implementiert / teilweise | Auth, Compose, Connector-Skelett, Fahrzeugliste, Reports-Grundlage |
| simuliert getestet | OBD-Simulator-Pfad, PDF/CSV, Auth, Parser |
| hardwaregetestet | 0 |
| freigegeben | 0 |

## Explizit fehlend / blockiert

1. **Keine OBD-/Adapter-Hardware** und keine Windows-.NET-Ausführung in dieser Cloud-VM → REQ-CONN-*, REQ-OBD-* Live, REQ-HW-*  
2. **Keine Herstellerdaten / ODX / kommerzielle Lizenzen** → REQ-DATA-*, REQ-SVC-*, REQ-COD-*, REQ-LIC-001  
3. **Delphi/Autocom-Modell unbekannt**; Vgate nicht spezifiziert → REQ-HW-001/002  
4. **Kein Mandantenmodell** → REQ-WS-006, PDF/Historie-Mandantenschutz  
5. **Docker in dieser Umgebung nicht verfügbar** → Compose-Build hier nicht verifiziert (Code vorhanden)  
6. **Phase 01 / MVP** liegt auf PR #1 – hier nur inventarisiert, nicht neu gebaut
