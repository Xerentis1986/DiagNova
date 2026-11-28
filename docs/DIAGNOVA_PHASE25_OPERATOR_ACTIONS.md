# Phase 25 – Betreiberhandlungen (Asmir)

1. **Mollie:** Konto anlegen → als Plattform-Admin **`/operator?tab=mollie`** Key speichern + Verbindungstest.  
   Oder Env `MOLLIE_API_KEY`. Live erst mit `live_…` + Live-Charges-Flag. Nie Keys in Git/Chat.  
   Betreiberkonsole: `/operator` (Kundenportal ohne Admin-Menü).
2. **RSA-Lizenzen:** `python scripts/generate_license_rsa_keys.py` → Private nur Backend-Env, Public Connector.  
   `DIAGNOVA_LICENSE_ALLOW_DEMO_PRIVATE=0` in Produktion.
3. **Installer:** UNSIGNED nutzen; Code-Signing optional (Privatperson – nicht Pflicht).
4. **Adapter:** Vgate iCar Pro 2S kaufen (≤100€), Windows Bluetooth-SPP/COM notieren, Connection-Test.  
   CDP+/OBD-DIAG weiter Labor; OBD-DIAG ohne Protokolldoku blockiert.
5. **Österreich:** Steuerberater/Anwalt – `draft_needs_review` erst nach Freigabe ändern. AGB/Widerruf-Texte ersetzen.
6. OEM-Logos + Wordmark **ohne** Symbol-Icon beibehalten.
