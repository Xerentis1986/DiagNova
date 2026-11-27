# DiagNova – Phasenstatus

**Aktualisiert:** 2026-11-27 (Europe/Vienna)  
**Aktuelle Arbeitsphase:** 03 abgeschlossen (simuliert getestet). **Phase 04 nicht gestartet** – Coordinator orchestriert.  
**Basis:** Phase-02-Branch `cursor/diagnova-phase-02-brands-c4de`; Arbeit auf `cursor/diagnova-phase-03-connector-90c7`.

## Phasenübersicht

| Phase | Thema | Status | Bemerkung |
|-------|--------|--------|-----------|
| **00** | Bestandsaufnahme & Anforderungskatalog | **Erledigt (Docs)** | Matrix/Baseline |
| **01** | MVP Basis | **Erledigt (simuliert)** | Web/API/Simulator/Berichte/Connector-Skelett |
| **02** | Marken-Kacheln & Fahrzeugauswahl | **Simuliert getestet** | Katalog, Theme, Wizard, E2E |
| **03** | Windows-Connector & Bluetooth | **Simuliert getestet** | Discovery, Auth, Fake-Port, ELM-Prep; keine Fahrzeugbefehle |
| 04 | Echte OBD-II/EOBD | Offen | Parser-Basis vorhanden; Hardware fehlt |
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

## Phase 03 – Kurzfazit

| Bereich | Ergebnis |
|---------|----------|
| Discovery | COM, USB (Linux/Limitation Windows), Bluetooth (Win32/Limitation), Simulator-Eintrag |
| Transport | `ISerialTransport` System + Fake; exklusiv, Timeout, Cancel, Dispose |
| ELM327 | AT-Init-Vorbereitung; OBD-Befehle blockiert |
| Auth | Pairing-Code, Session-Token, Origin-Allowlist, Loopback-only |
| Status | Adapter- vs. Fahrzeugverbindung getrennt (Fahrzeug = false) |
| Tests | `dotnet test` **14 passed**; pytest Regression **18 passed** |
| Blocker | BLK-HW, BLK-ADAPTER (Delphi/Autocom, Vgate-SPP) |

Details: [phase-03-abschluss.md](./phase-03-abschluss.md), [requirements.md](./requirements.md), [capabilities.md](./capabilities.md).

## Nicht ausgeführt (weiterhin)

| Check | Grund |
|-------|-------|
| `docker compose up --build` | Docker nicht installiert (BLK-DOCKER) |
| Echte BT/COM-Hardwareerkennung | Keine Hardware (BLK-HW); Fake-Port getestet |
| Hardware-/Fahrzeugtests | Schreib-/OBD-Tests untersagt in Phase 03 |
| Echte Markenlogos | Rechte ungeklärt (BLK-LOGO) |
