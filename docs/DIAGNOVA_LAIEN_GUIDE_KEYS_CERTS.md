# Laienleitfaden: Keys, Zertifikate, Zahlung (Phase 25)

## Zahlung = Mollie (nicht Stripe)
1. Bei Mollie anmelden und API-Key (`test_…`) kopieren.  
2. Als Betreiber unter **`/operator` → Tab Mollie** den Key eintragen und speichern (wird verschlüsselt abgelegt – nicht ins Git).  
   Alternativ Server-Env: `MOLLIE_API_KEY=…`.  
3. „Verbindungstest“ drücken – prüft nur die Verbindung, **bucht nichts ab**.  
4. Echte Abbuchungen erst nach bewusster Freigabe (Live-Key + Live-Charges-Häkchen).

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
