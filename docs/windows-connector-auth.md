# Windows-Connector: Localhost-Authentifizierung (Hinweis)

## Ziel
Der Connector lauscht nur auf `127.0.0.1` und akzeptiert Anfragen ausschließlich mit gültigem Token/Pairing.

## V1-Empfehlung

1. Beim Start erzeugt der Connector ein zufälliges Pairing-Geheimnis und speichert es lokal (DPAPI/User-Scope).
2. Die Web-App fordert ein Pairing an (QR/Code oder einmaliger Token).
3. Alle Diagnoseaufrufe tragen `Authorization: Bearer <connector-token>`.
4. Keine offenen Endpunkte ohne Auth; CORS nur für bekannte Origins; Bind ausschließlich an Loopback.
5. Schreibende Aktionen (Clear DTC etc.) erst nach expliziter Freigabe und Tests – **nicht** im MVP-Skelett.

## Nicht erlaubt
- Offene HTTP-Endpunkte ohne Auth
- Fernsteuerung von Fahrzeugaktionen ohne lokale Bestätigung
- Umgehung proprietärer Diagnose-Schutzmechanismen
