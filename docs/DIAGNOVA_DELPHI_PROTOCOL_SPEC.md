# Delphi/Autocom CDP+ – Protokollspezifikation (DiagNova, eigenständig)

**Stand:** 2026-11-27 (Europe/Vienna)  
**Status:** Forschungsstand / Teilimplementierung Safe-Reads  
**Hinweis:** Keine vollständige oder für alle Hardwareversionen bestätigte Spezifikation.

## Framing

```
Host → Gerät:  *<cmd>[_<arg>[_<arg>…]]\r
Gerät → Host:  *<payload>\r
```

| Element | Wert |
|---------|------|
| Start | `*` (0x2A) |
| Ende | `\r` (0x0D) |
| Feldtrenner | `_` (0x5F) |
| Zeichensatz | ASCII |

## Dokumentierte Geräte-Lesebefehle (Allowlist)

| Befehl | Bedeutung | Beispielantwort | Parsing |
|--------|-----------|-----------------|---------|
| `*200\r` | Seriennummer | `*1 100251\r` | Payload nach Flag |
| `*201\r` | Firmware | `*1 1622\r` | Payload |
| `*203\r` | Batterie | `*0 1362\r` | Wert/100 = Volt |
| `*20A\r` | Gerätename | `*CDP+\r` | Text |

## Gesperrte Befehlsklassen (ohne Freigabe)

| Befehl | Risiko |
|--------|--------|
| `*60b` / `*60bc` | Handshake/Init |
| `*668_…` | CAN-Bus-Config, mögliche Relais/Pin-Umschaltung |
| `*606_…` | Periodische CAN-Frames (z. B. TesterPresent) |
| `*608_…` / `*609_…` | ECU-Parameter / Raw-CAN |
| `*918x` | Self-Test / interne Pfade |

## USB

- Dokumentierte Variante: VID **0403**, PID **D6DA**
- EP-Hinweise aus Forschung: Modem-Status vs. Daten-Bulk – Windows-Implementierung über FTDI/D2XX oder Raw-USB erst nach Labor

## Implementierung in DiagNova

- `Adapters/DelphiCdp/CdpProtocol.cs` – Codec
- `CdpSession.cs` – Allowlist + Gate
- `FakeCdpTransport` / `FtdiCdpTransport`
- Tests: dokumentierte Nachrichtenbeispiele

**Nicht** aus GPL-Quellcode kopiert.
