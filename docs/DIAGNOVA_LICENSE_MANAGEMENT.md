# Lizenzverwaltung

- Abo-Status serverseitig (`Subscription`)
- Gerätebindung `DeviceBinding` + Activate/Verify unter `/api/billing/licenses/*`
- Offline-Toleranz-Hinweis 72h – kein Ersatz für Servercheck
- Connector prüft Entitlements über Backend; unautorisierte Diagnosebefehle über Allowlists/Gates
