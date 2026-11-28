# DiagNova Windows-Connector – Installation & Deinstallation

**Phase 14** · Simulation/Demo. Produktive Auto-Updates sind **gesperrt**, solange kein Code-Signing-Zertifikat konfiguriert ist.

Software-Updates (API / Web / Connector) sind **getrennt** von Diagnosedaten-Updates (`/data-updates`).

## Voraussetzungen

- Windows 10/11
- .NET 8 Runtime (bzw. Self-Contained-Build)
- Loopback `http://127.0.0.1:8765` – keine offenen Netzwerk-Ports
- Keine laufende Diagnose, Service- oder Flash-/Codieroperation

## Installation (dokumentiert)

1. Release-Paket nur aus vertrauenswürdigem Kanal laden (Admin-UI `/software-updates`).
2. SHA-256 und Signatur gegen die Admin-Anzeige prüfen; manipulierte Pakete ablehnen.
3. Ohne gültiges Signaturzertifikat: **kein** produktives Auto-Update – nur manuelle Freigabe in der Demo.
4. Diagnose/Service/Flash beenden (Busy-Gate).
5. Archiv entpacken bzw. Installer ausführen (Benutzerrechte lokal).
6. Connector starten; prüfen: `GET /health`, `GET /version`, `GET /updates/status`.
7. Browser erneut pairen (`POST /pair`), Origin-Allowlist beachten.

## Deinstallation

1. Connector-Prozess beenden (kein offenes Fahrzeug).
2. Programm deinstallieren bzw. Installationsordner entfernen.
3. Optionale lokale Pairing-/Logdateien löschen.
4. Gerätebindung in der Web-Admin-UI widerrufen, falls nötig.

## Rollback

- API-Admin: Rollback auf `previous_version` unter `/software-updates`.
- Lokal: vorherige Release-Version wiederherstellen und Healthcheck prüfen.
- Bei fehlgeschlagenem Healthcheck nach Installation erfolgt automatischer Rollback (Simulation).

## Sicherheit

| Regel | Status |
|-------|--------|
| Ungeprüfte Auto-Installs | **aus** |
| Signatur/Checksum | Pflicht |
| Prod-Auto-Update ohne Zertifikat | **gesperrt** |
| Update während Diagnose/Service/Flash | **gesperrt** |

## API (Connector, Loopback)

| Methode | Pfad | Zweck |
|---------|------|-------|
| GET | `/version` | Komponentenversion |
| GET | `/updates/status` | Update-Status |
| GET | `/updates/busy` | Busy-Gate |
| POST | `/updates/stage` | Staging/Install (nur mit Admin-Freigabe-Flag) |
| POST | `/updates/rollback` | Rollback |
