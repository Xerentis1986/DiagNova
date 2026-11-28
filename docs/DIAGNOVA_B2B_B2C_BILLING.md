# DiagNova – B2B/B2C Abrechnung (Phase 21)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Status:** implementiert (Simulation) – **kein** echter PSP (BLK-PAY)  
**API:** `/api/commerce/*`

## Kundentypen

| Typ | Zielgruppe | UID | Pflichtfelder |
|-----|------------|-----|---------------|
| B2B | Werkstätten, Einzelunternehmen, Kapitalgesellschaften, gewerbliche Diagnostiker | Pflicht + VIES-Prüfung | Firmenname, Ansprechpartner, Rechnungsadresse/Land, UID, Rechnungs-E-Mail, Steuerklassifikation, Zahlungsart, Abo, Lizenzanzahl |
| B2C | Privatpersonen, Hobbymechaniker, private Fahrzeugbesitzer | **nicht** erlaubt | Mindestdaten + AGB/Datenschutz/Widerrufs-Ack |

## Implementierte Fähigkeiten

- Billing-Konten anlegen/listen
- VIES-UID-Prüfung (Stub standard; Live mit `VIES_LIVE=1`)
- Abo buchen (bestehende Plan-Kataloge Phase 13) + Rechnung erzeugen
- Rechnung JSON-Download, Gutschrift
- Kündigung (Periodenende / sofort)
- Lizenz-/Geräteliste
- Consent-Protokoll (AGB, Datenschutz, Widerruf, Bestellbestätigung, Auto-Renewal)

## Code

| Bereich | Pfad |
|---------|------|
| Models | `apps/api/app/models/commerce.py` |
| Service | `apps/api/app/services/commerce/billing.py` |
| VIES | `apps/api/app/services/commerce/vies.py` |
| Routes | `apps/api/app/api/routes/commerce.py` |
| Migration | `apps/api/alembic/versions/014_phase21_commerce.py` |
| Tests | `tests/api/test_phase21_commerce.py` |

## Offen vor Prod

- Echter Payment-Provider nach Zustimmung
- Fachliche Steuerfreigabe (`draft_needs_review`)
- Rechtstexte Verbraucherschutz / Widerruf
- PDF-Rechnungen (aktuell JSON-Download)
