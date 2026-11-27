# DiagNova – Phasenstatus

Aktualisiert: 2026-11-27 (Europe/Vienna) · Phase 00 Bestandsaufnahme

Quellen: Master-Promptpaket, Roadmap, Code auf `cursor/diagnova-phase-ab-mvp-bf17` / Phase-00-Branch.

| Phase | Thema | Status | Nachweis / Kommentar |
|-------|--------|--------|----------------------|
| **00** | Bestandsaufnahme & Anforderungskatalog | **abgeschlossen (Doku)** | `docs/requirements.md`, `capabilities.md`, dieser Status, `DIAGNOVA_PROGRESS.md`, `phase-00-abschluss.md` |
| **01** | MVP Basis (historisch A/B) | **erledigt – nicht anfassen** | PR #1 `cursor/diagnova-phase-ab-mvp-bf17`; Phase 00 baut darauf auf |
| 02 | Marken-Kacheln & Fahrzeugauswahl | offen | REQ-UI-001…008 |
| 03 | Windows-Connector & Bluetooth | offen | Connector-Stub vorhanden; HW fehlt |
| 04 | Echte OBD-II/EOBD | offen | nur Simulator |
| 05 | Multiprotokoll / Mehr-ECU | offen | |
| 06 | Diagnosedatenbank & Importe | offen | |
| 07 | Automatische Daten-Updates | offen | |
| 08 | Werkstatt- & Kundenverwaltung | offen | Auth/Rollen teilweise |
| 09 | Fahrzeug-History / Akte | offen | Sessions rudimentär |
| 10 | PDF-Berichte & Archiv | offen | MVP PDF/CSV vorhanden |
| 11 | Erweiterte Diagnose & Service | offen | UI „Geplant“ |
| 12 | Codierung & Programmierung | offen | gesperrt bis Freigabe |
| 13 | Abos & Administration | offen | |
| 14 | Software-/Connector-Updates | offen | |
| 15 | Sicherheit, Datenschutz, Qualität | offen | V1-Minimum vorhanden |
| 16 | World4You Ubuntu/Plesk Deploy | vorbereitet / offen | Domain/DB-Kontext; **kein Deploy in Phase 00** |
| 17 | Gesamtabnahme | offen | |
| 18 | Chiptuning (optional) | später optional | |
| 19 | LKW/Nutzfahrzeuge (optional) | später optional | |

## Regeln

- Keine automatische Weiterführung zur nächsten Phase.
- Phase 01 / MVP-Code nicht neu entwickeln oder überschreiben.
- Keine produktiven Deployments und keine Fahrzeug-Schreibtests ohne Zustimmung.
- Fehlende Hardware, Lizenzen und Herstellerdaten ausdrücklich als Blocker führen.
