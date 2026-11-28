# Windows-Connector: Localhost-Authentifizierung (Phase 03)

## Ziel

Der Connector lauscht nur auf `127.0.0.1:8765` und akzeptiert Diagnose-/Inventar-Aufrufe ausschließlich mit gültigem Token.

## Umgesetzt

1. **Loopback-Bindung** – `UseUrls("http://127.0.0.1:8765")`; Remote-IP muss Loopback sein.
2. **Kurzlebiges Pairing** – 6-stelliger Code (TTL konfigurierbar, Standard 10 Min.), Anzeige in der Connector-Konsole und `GET /pair/info`.
3. **`POST /pair`** mit `{ "pairingCode": "…" }` → Bearer-Session-Token (TTL Standard 120 Min.); Pairing-Code wird nach Erfolg rotiert.
4. **Bootstrap** – optional `CONNECTOR_TOKEN` als langlebiger Dev-/Service-Token.
5. **Origin-Allowlist** – Standard: lokale Vite/Dev-Origins; erweiterbar via `CONNECTOR_ALLOWED_ORIGINS`.
6. **Keine offenen Diagnose-Endpunkte** – `/devices`, `/status`, `/adapter/*`, `/log` erfordern Bearer.

## HTTPS / Browser

- Von einer **HTTPS**-Seite aus ist `fetch` zu `http://127.0.0.1` (Mixed Content) je nach Browser eingeschränkt.
- Empfohlen: lokale Dev-Origin (`http://127.0.0.1:5173`), gleicher Host, oder später authentifizierter Relay – **keine** Browser-Sicherheitsabschaltung.
- Secure-Context-Ausnahmen für Loopback bleiben browserabhängig; siehe Connector-`/capabilities`.

## Nicht erlaubt

- Offene HTTP-Endpunkte ohne Auth (außer Pairing-Info/Pair auf Loopback)
- Fernsteuerung von Fahrzeugaktionen
- Fahrzeugbefehle in Phase 03
- Umgehung proprietärer Diagnose-Schutzmechanismen

## Beispiel

```bash
# Pairing-Info (Loopback)
curl -s http://127.0.0.1:8765/pair/info

# Pairen
curl -s -X POST http://127.0.0.1:8765/pair \
  -H 'Content-Type: application/json' \
  -d '{"pairingCode":"123456"}'

# Status mit Token
curl -s http://127.0.0.1:8765/status -H "Authorization: Bearer <token>"
```
