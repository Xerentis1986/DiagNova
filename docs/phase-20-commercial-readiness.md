# DiagNova – Kommerzielle Einsatzbereitschaft (Phase 20)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Gesamtverdict:** **NO-GO** für kommerziellen Vollbetrieb  
**Pilot-Demo (Simulation):** bedingt möglich nach Betreiberfreigabe

## Entscheidungsmatrix

| Einsatzart | Verdict | Minimale Kriterien |
|------------|---------|-------------------|
| Öffentlicher Voll-Launch / Verkauf als „echte Diagnose“ | **NO-GO** | Alle GO-Kriterien unten erfüllt |
| Werkstatt-Pilot nur Simulation/Demo | **bedingt GO** | Live-Smoke OK; Demo-Accounts; keine HW-Claims; Betreiber OK |
| Live-OBD am Fahrzeug | **NO-GO** | BLK-HW geschlossen + Freigabeprotokoll |
| OEM-Service / Codierung Schreiben | **NO-GO** | BLK-OEM + BLK-RELEASE |
| Flash / Programmierung | **NO-GO** | BLK-J2534/HW + Legal + BLK-RELEASE |
| Chiptuning-Aktivierung | **NO-GO** | BLK-LEGAL + keine Abgasmanipulation; aktuell 403 |
| LKW-Diagnose | **NO-GO** | RP1210/J1939 Spec+HW; aktuell Architektur only |
| Produktives Redeploy Feature-Stand | **STOP** | Explizite Betreiber- + Coordinator-Freigabe |

## GO-Kriterien (alle erforderlich für Vollbetrieb)

| # | Kriterium | Ist | Blocker |
|---|-----------|-----|---------|
| G1 | Hardwaregetestete OBD/Adapter-Kommunikation dokumentiert | offen | BLK-HW |
| G2 | Lizenzierte Diagnosedaten / OEM wo behauptet | offen | BLK-OEM |
| G3 | Markenlogo-Rechte geklärt oder nur Text-Fallback kommuniziert | Text-Fallback OK; Bildrechte offen | BLK-LOGO |
| G4 | Echter PSP oder klar „Zahlung Simulation“ in Prod | Stub only | BLK-PAY |
| G5 | DSGVO-AV, Auftragsverarbeitung, Steuer/Abo-Recht | Docs vorhanden, Prüfung offen | BLK-LEGAL |
| G6 | Code-Signing für Connector-Updates (falls Auto-Update) | fehlt | BLK-CERT |
| G7 | Prod-Redeploy des abgenommenen Stands | Live hinter Branch | BLK-DEPLOY |
| G8 | Schreibfunktionen nur nach Freigabeprozess | korrekt gesperrt | BLK-RELEASE (OK als Sperre) |
| G9 | Keine irreführenden Marketing-Claims | Docs ehrlich | Review vor Launch |
| G10 | Automatisierte Tests grün auf Release-Tag | 148/32/Build OK auf Branch | Merge + CI auf main |

## NO-GO-Begründung (kompakt)

Das Produkt ist als **simuliertes MVP + Architektur** stark: Auth, Mandant, Diagnose-UI, Gates, Updates, Security-Basics, Deploy-Docs, optionale Module Tuning/LKW als „Geplant“. Es fehlt die verifizierte Hardware-/OEM-/Rechts-/Zahlungs- und Freigabelinie für einen verkaufbaren „Echtdiagnose“-Betrieb. Jede Behauptung echter Fahrzeugkommunikation oder OEM-Vollabdeckung wäre falsch.

## Was kommerziell ehrlich angeboten werden darf (nach Pilot-Freigabe)

- Demo/Training der webbasierten Diagnose-Oberfläche mit Simulator
- Werkstatt-/Kunden-/Berichts-Workflows mit Beispieldaten
- Architektur-Roadmap LKW/Tuning als **nicht freigegeben**

## Was nicht verkauft / beworben werden darf

- Hardwaregetestete Mehrmarken-Diagnose
- Delphi/Autocom/Vgate-Live ohne Nachweis
- Flash, Codier-Schreiben, DPF-Off, Chiptuning-Aktivierung
- Gleichwertigkeit zu Bosch/Gutmann/Hersteller-Tools
