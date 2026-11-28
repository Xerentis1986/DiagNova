# Betreiberhandlungen – Phase 22

Pflichtschritte außerhalb der Cloud-Agent-Umgebung:

1. **Windows-Host:** .NET 8 Runtime/SDK; `apps/windows-connector/scripts/publish-win-x64.ps1` ausführen und Connector starten.
2. **Hardware:** Delphi/Autocom CDP+ und/oder OBD DIAG anschließen; VID/PID und COM-Port dokumentieren; Preferred COM setzen.
3. **LIVE-Bridge:** API `CONNECTOR_BASE_URL` + optional Bearer; UI auf LIVE; H1–H8 aus Hardware-Testplan.
4. **Stripe (Test):** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, Publishable Key – nur Testmodus; keine Live-Charges.
5. **SMTP:** Produktions-SMTP für echte Bestätigungs-/Reset-Mails.
6. **MFA:** Platform-Admin `/api/admin/mfa/setup` → Confirm; Backup-Codes sichern.
7. **Steuer/Recht:** Externe Prüfung; Flag `draft_needs_review` erst nach Freigabe entfernen.
8. **Signing/MSI:** Zertifikat beschaffen; WiX/MSIX oder vergleichbar; kein Fake-Signing.
9. **Prod-Deploy:** Nur nach Freigabe; OEM-Logos + Wordmark **ohne** Symbol-Icon beibehalten (Deploy-Gate).
10. **OBD-DIAG:** Lizenzierte Protokolldoku oder OEM-Kooperation – sonst weiter Inventur-only.
