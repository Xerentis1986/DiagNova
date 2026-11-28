# Laienleitfaden: Keys, Zertifikate, Zahlung (Phase 25)

## Zahlung = Mollie (nicht Stripe)
1. Bei Mollie anmelden.  
2. API-Key kopieren (`test_…` zum Üben).  
3. Auf dem Server als Geheimnis speichern: `MOLLIE_API_KEY=…` (nicht in Dateien ins Git legen).  
4. In der Admin-Oberfläche „Verbindungstest“ drücken – das prüft nur die Verbindung, **bucht nichts ab**.  
5. Echte Kundenabbuchungen erst, wenn du das bewusst freigibst (`MOLLIE_LIVE_CHARGES_ALLOWED`).

## Lizenz-Schlüssel (RSA)
1. Auf dem Rechner: `python scripts/generate_license_rsa_keys.py`  
2. Es entstehen Dateien unter `.secrets/license/` (privat bleiben!).  
3. Private nur auf dem Backend, Public auf dem Windows-Connector.  
4. Demo-Schlüssel in Produktion ausschalten.

## Installer ohne Unterschrift
Das Windows-Setup ist **UNSIGNED** – für Privatpersonen ok.  
Optionales Code-Signing später möglich, aber **nicht Pflicht**.

## Adapter-Tipp
Empfohlen unter 100 €: **Vgate iCar Pro 2S** (Bluetooth).  
Nach dem Koppeln den COM-Port notieren und im Connector testen.
