# Protokollarchitektur – Schichtentrennung (Phase 05)

**Stand:** 2026-11-27 (Europe/Vienna)

## Schichten

| Schicht | Verantwortung | Beispiele |
|---------|---------------|----------|
| **Transport** | Verbindung, Bytes senden/empfangen | `ISerialTransport`, Fake-Port, später DoIP/Ethernet, J2534 |
| **Protokoll** | Semantik, Framing, NRC, Sitzungskonzepte | OBD-II/J1979, ISO-TP, UDS, KWP2000 |
| **Adapter** | Was die Hardware tatsächlich kann | Capability-Matrix pro Adapter-ID |
| **Fahrzeugdefinition** | Verifizierte ECU-Adressen/Funktionen | Nur ISO 15765-4 OBD-Slots; OEM später mit Lizenz |

## Regeln

1. Keine Vermischung: ELM-ASCII ist Transport+Adapter-Pfad, nicht OEM-Definition.
2. Implementierung nur mit verfügbaren Specs und Simulator.
3. Kein Blindscan unbekannter Bus-Adressen.
4. Günstiger OBD/ELM-Adapter ≠ DoIP/CAN-FD/J2534.
5. Schreiben/Security/Flash bleiben gesperrt (Phase 04 Clear-Gate ausgenommen, OBD Mode 04).

## Code-Pfade

| Schicht | Python | .NET Connector |
|---------|--------|----------------|
| Transport | (API nutzt Simulator) | `Transport/*` |
| Protokoll | `diagnova_protocols/*` | `Obd/*`, `Protocol/*` |
| Adapter | `capability_matrix.py` | `Adapters/*`, `AdapterCapabilityMatrix` |
| Fahrzeugdef. | `ecu_definition.py`, `obd_addresses.py` | `Ecu/*` |

Siehe auch: [adapter-capability-matrix.md](./adapter-capability-matrix.md), [j2534-doip-j1939-prep.md](./j2534-doip-j1939-prep.md).
