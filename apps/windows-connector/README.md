# DiagNova Windows Connector (Skelett)

.NET 8 Worker-/Host-Grundstruktur für eine **lokale** Connector-Anwendung.

## Wichtig

- **Keine** echten Fahrzeugbefehle in diesem Skelett.
- `IDiagnosticAdapter` beschreibt die Schnittstelle; `StubDiagnosticAdapter` liefert nur simulierte Platzhalter.
- Die localhost-API muss authentifiziert werden (siehe `docs/windows-connector-auth.md`).
- Proprietäre Protokolle (Delphi/Autocom etc.) werden weder implementiert noch umgangen.

## Build (auf Windows mit .NET 8 SDK)

```powershell
cd apps\windows-connector
dotnet restore
dotnet build
dotnet run --project DiagNova.Connector
```

Ohne .NET SDK kompiliert dieses Skelett hier nicht – der Quellcode dient als Vertragsgrundlage für Phase C+.
