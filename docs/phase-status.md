# DiagNova – Phasenstatus

**Aktualisiert:** 2026-11-27 (Europe/Vienna)  
**Aktuelle Arbeitsphase:** 04 abgeschlossen (simuliert getestet). **Phase 05 nicht gestartet** – Coordinator orchestriert.  
**Basis:** Phase-03-Branch `cursor/diagnova-phase-03-connector-90c7`; Arbeit auf `cursor/diagnova-phase-04-obd-606d`.

## Phasenübersicht

| Phase | Thema | Status | Bemerkung |
|-------|--------|--------|-----------|
| **00** | Bestandsaufnahme & Anforderungskatalog | **Erledigt (Docs)** | Matrix/Baseline |
| **01** | MVP Basis | **Erledigt (simuliert)** | Web/API/Simulator/Berichte/Connector-Skelett |
| **02** | Marken-Kacheln & Fahrzeugauswahl | **Simuliert getestet** | Katalog, Theme, Wizard, E2E |
| **03** | Windows-Connector & Bluetooth | **Simuliert getestet** | Discovery, Auth, Fake-Port, ELM-Prep |
| **04** | Echte OBD-II/EOBD | **Simuliert getestet** | Parser/Allowlist/Clear-Gate; **keine HW-Freigabe** |
| 05 | Multiprotokoll / Mehr-ECU | Offen | |
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
| 19 | LKW (optional) | Später | |

## Phase 04 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Init/Protokoll | AT-Init + 0100/ATDP/ATDPN; Fahrzeuglink nach Erfolg |
| PID/Live | Bitmap + Mode-01 Live mit Einheiten/Zeitstempel |
| DTC | stored/pending/permanent; Multi-ECU |
| FF/Readiness/VIN | Mode 02/01-01/09-02 |
| Fehlerbehandlung | NO DATA, Timeout, Negativ, Abbruch – Status explizit |
| Clear | Freigabe-Phrase + Acks + Token; permanente nicht löschbar |
| Live vs Demo | `data_source` simulated\|live strikt |
| Tests | `dotnet test` **23 passed**; pytest **27 passed** |
| Blocker | BLK-HW (keine Live-Freigabe), BLK-ADAPTER |

Details: [phase-04-abschluss.md](./phase-04-abschluss.md), [requirements.md](./requirements.md), [capabilities.md](./capabilities.md).

## Nicht ausgeführt (weiterhin)

| Check | Grund |
|-------|-------|
| `docker compose up --build` | Docker nicht installiert (BLK-DOCKER) |
| Echter Fahrzeug-/OBD-Hardwaretest | Keine Hardware (BLK-HW); Fake/Simulator getestet |
| Live-Freigabe | Explizit ausstehend bis Hardware + Zustimmung |
| Echte Markenlogos | Rechte ungeklärt (BLK-LOGO) |
