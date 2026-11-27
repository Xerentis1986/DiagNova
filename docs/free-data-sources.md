# Freie / dokumentierte Datenquellen (Phase 06)

**Prüfdatum:** 2026-11-27 (Europe/Vienna)  
**Regel:** Öffentlich sichtbar ≠ frei verwendbar. Nichts erfinden. Keine Bosch/Gutmann/Delphi-Kopien.

## Erfasste Quellen

| Key | URL / Bezug | Version | Lizenz | Kommerzielle Nutzung | Attribution | Redistributable | Scope |
|-----|-------------|---------|--------|----------------------|-------------|-----------------|-------|
| `diagnova-structural` | intern | phase-06-v1 | DiagNova structural | n/a | DiagNova Katalogstruktur | ja | structural |
| `sae-j1979-pid-subset` | [SAE J1979](https://www.sae.org/standards/content/j1979/) | subset-mvp | SAE (Kauf) | restricted | nur Repo-Implementierungs-Subset | ja (Subset) | generic |
| `iso-15765-4-obd-addresses` | [ISO 15765-4](https://www.iso.org/standard/66322.html) | 7E0/7E8, 7E1/7E9 | ISO | restricted | Standardadressen | ja (Adressen) | generic |
| `dtc-descriptions-unavailable` | — | — | none | prohibited | — | **nein** | documentation_only |
| `odx-pdx-placeholder` | — | — | pending | prohibited | — | **nein** | documentation_only |

## Recherche-Ergebnis DTC-Texte

Vollständige DTC-Beschreibungskataloge (SAE J2012-Texte, OEM-Listen, Werkstattkataloge von Bosch ESI[tronic], Gutmann, Delphi/Autocom) sind **nicht** frei kommerziell redistribuierbar. Daher:

- Codes können gespeichert werden.
- Beschreibungstext nur mit dokumentierter, redistributable Quelle.
- Sonst UI/API: **„unbekannt“** (`description_status=unknown`).

## Bewusst abgelehnt

- Kopien aus Bosch / Gutmann / Delphi / Autocom
- ODX/PDX ohne Spezifikation und Nutzungsrecht (Import → 403)
- Erfundene OEM-Adressen, Serviceprozedur-Schritte oder DTC-Texte

## Später (mit Lizenz)

- Lizenzierte ODX/PDX-Pakete (REQ-06-ODX)
- OEM-ECU-Definitionen ABS/Airbag/Komfort (BLK-OEM)
- Automatische Updates: Phase 07 implementiert (simuliert); HTTPS-Kanäle nur nach Rechteprüfung; keine kommerziellen Feeds aktiv
