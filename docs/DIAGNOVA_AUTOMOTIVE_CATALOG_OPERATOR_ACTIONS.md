# Automotive-Katalog – Betreiberhandlungen

1. UI: `/automotive-catalog` – Suche, Summary, Import-Preview  
2. Probe (Plattform-Admin): Button oder `POST /api/automotive-catalog/probe`  
3. Sample importieren: Preview → Apply (`batch_id` aus Preview)  
4. Voll-OBDex lokal:  
   `python scripts/automotive_catalog_probe_and_import.py --full-obdex`  
   → `.cache/automotive/` (gitignored), dann Import-API/Upload  
5. Mollie/SMTP/Recht/HW weiter über `/operator` – kein Fake-GO  
6. Keine Passwörter/Keys in Git; Registrierungs-Secrets nur Store `internal/`
