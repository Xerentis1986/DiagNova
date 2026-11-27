# Release-Readiness

**Stand:** 2026-11-27 (Europe/Vienna)  
**Verdict:** **NO-GO** für kommerziellen Vollbetrieb.

Diese Datei ist die Kurzfassung. Die verbindliche technische Bestandsaufnahme mit Dateipfaden, Klassen, Endpunkten, Tabellen, Tests und Klassifikation **A–E** steht in:

→ **`docs/DIAGNOVA_PHASE21_TECHNICAL_EVIDENCE.md`**

## Kurzstatus (nach Evidenzprüfung)

| Bereich | Klasse |
|---------|--------|
| CDP+ Safe-Reads (Sim/Unit) | A / Live C–E |
| OBD-DIAG 2055+ | D / Treiber E |
| Connector Runtime | C (Installer E) |
| OBD-II Engine Connector Fake | A |
| Web Live-Diagnose | D (Simulator) |
| Service/Coding Live | E (gesperrt) |
| Admin-Backend | C (MFA E) |
| B2B/B2C Commerce | C |
| Abos | C (Stub) |
| Stripe | C (ohne Keys kein E2E) |
| Rechnungen/Steuer | C (PDF E, draft tax) |
| Lizenzen | C |
| E-Mail | C (dry_run; Auth nicht verdrahtet) |
| Security/Updates/Deploy | C |

## Automatisierte Tests (Evidenzlauf)

- `pytest tests/`: **159 passed**
- `dotnet test`: **46 passed**

## Freigabe Verkauf erst nach

1. HW-Labor (CDP+/OBD-DIAG/Fahrzeug)  
2. Web↔Connector Live-Bridge oder klar dokumentierter Workflow  
3. Stripe Test→Live nach Freigabe  
4. Steuer/Recht  
5. Signing + Deploy-Abnahme  
