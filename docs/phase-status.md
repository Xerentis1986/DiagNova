# DiagNova – Phasenstatus

**Aktualisiert:** 2026-11-27 (Europe/Vienna)  
**Aktuelle Arbeitsphase:** 05 abgeschlossen (simuliert getestet). **Phase 06 nicht gestartet** – Coordinator orchestriert.  
**Basis:** Phase-04-Branch `cursor/diagnova-phase-04-obd-606d`; Arbeit auf `cursor/diagnova-phase-05-multiprotocol-dd50`.

## Phasenübersicht

| Phase | Thema | Status | Bemerkung |
|-------|--------|--------|-----------|
| **00** | Bestandsaufnahme & Anforderungskatalog | **Erledigt (Docs)** | Matrix/Baseline |
| **01** | MVP Basis | **Erledigt (simuliert)** | Web/API/Simulator/Berichte/Connector-Skelett |
| **02** | Marken-Kacheln & Fahrzeugauswahl | **Simuliert getestet** | Katalog, Theme, Wizard, E2E |
| **03** | Windows-Connector & Bluetooth | **Simuliert getestet** | Discovery, Auth, Fake-Port, ELM-Prep |
| **04** | Echte OBD-II/EOBD | **Simuliert getestet** | Parser/Allowlist/Clear-Gate; **keine HW-Freigabe** |
| **05** | Multiprotokoll / Mehr-ECU | **Simuliert getestet** | Schichten, Matrix, ISO-TP/UDS-NRC, OBD-ECUs; DoIP/J2534 Prep |
| 06 | Diagnosedatenbank & Importe | Offen | |
| 07 | Automatische Daten-Updates | Offen | |
| 08 | Werkstatt- & Kundenverwaltung | Offen | |
| 09 | Fahrzeug-History / Akte | Offen | |
| 10 | PDF-Berichte & Archiv | Offen | MVP-PDF rudimentär |
| 11 | Erweiterte Diagnose / Service | Offen | UI-Platzhalter |
| 12 | Codierung / Programmierung | Offen | UI-Platzhalter; Schreibpfade gesperrt |
| 13 | Abos & Administration | Offen | |
| 14 | Software-/Connector-Updates | Offen | |
| 15 | Sicherheit / Datenschutz / QA | Offen | Auth-Basis vorhanden |
| 16 | World4You Ubuntu/Plesk Deploy | Offen / parallel vorbereitet | kein Prod-Deploy |
| 17 | Gesamtabnahme | Offen | |
| 18 | Chiptuning (optional) | Später | standardmäßig gesperrt |
| 19 | LKW (optional) | Später | J1939/RP1210 |

## Phase 05 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Schichten | Transport / Protokoll / Adapter / Fahrzeugdefinition getrennt |
| Capability-Matrix | Pro Adapter; ELM ≠ DoIP/CAN-FD |
| ISO-TP / UDS | Parser + Testvektoren; Write/Security aus |
| Mehr-ECU | 7E8/7E9 aus beobachteten Antworten; kein Blindscan |
| OEM | ABS/Airbag/Komfort unavailable (BLK-OEM) |
| Prep-Docs | J2534 / DoIP / J1939 |
| Blocker | BLK-HW, BLK-OEM, BLK-ADAPTER |

Details: [phase-05-abschluss.md](./phase-05-abschluss.md), [protocol-architecture.md](./protocol-architecture.md), [requirements.md](./requirements.md).

## Nicht ausgeführt (weiterhin)

| Check | Grund |
|-------|-------|
| `docker compose up --build` | Docker nicht installiert (BLK-DOCKER) |
| Echter Fahrzeug-/Multiprotokoll-Hardwaretest | Keine Hardware (BLK-HW) |
| Live-Freigabe | Explizit ausstehend |
| OEM-ECU-Definitionen | BLK-OEM |
