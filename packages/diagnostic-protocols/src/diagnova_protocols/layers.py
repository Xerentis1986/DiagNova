"""Schichtentrennung: Transport / Protokoll / Adapter / Fahrzeugdefinition.

Jede Schicht hat eine klare Verantwortung. Keine Vermischung von
ELM-ASCII-Transport mit UDS-Semantik oder OEM-Adressen.
"""

from __future__ import annotations

from enum import Enum


class ArchitectureLayer(str, Enum):
    TRANSPORT = "transport"
    PROTOCOL = "protocol"
    ADAPTER = "adapter"
    VEHICLE_DEFINITION = "vehicle_definition"


LAYER_DESCRIPTIONS_DE: dict[ArchitectureLayer, str] = {
    ArchitectureLayer.TRANSPORT: (
        "Physische/logische Verbindung: seriell (COM/SPP), Fake-Port, "
        "später Ethernet/DoIP oder J2534-PassThru. Kennt keine DTCs/DIDs."
    ),
    ArchitectureLayer.PROTOCOL: (
        "Diagnoseprotokoll-Semantik: OBD-II/J1979, ISO-TP, UDS, KWP2000, … "
        "Framing, Segmentierung, NRC, Sitzungskonzepte – unabhängig vom Adapter."
    ),
    ArchitectureLayer.ADAPTER: (
        "Hardware-/Treiberfähigkeiten: welche Protokolle und Bitrates ein Adapter "
        "tatsächlich unterstützt (Capability-Matrix). Günstiger ELM ≠ DoIP/CAN-FD."
    ),
    ArchitectureLayer.VEHICLE_DEFINITION: (
        "Verifizierte Steuergeräteadressen und Funktionen je Fahrzeug. "
        "Nur belegte Specs/Definitionen – kein blindes Netzwerkscan, keine erfundenen OEM-Adressen."
    ),
}


def architecture_overview() -> dict:
    return {
        "layers": [
            {
                "id": layer.value,
                "description_de": LAYER_DESCRIPTIONS_DE[layer],
            }
            for layer in ArchitectureLayer
        ],
        "rule_de": (
            "Implementierung nur mit verfügbaren Spezifikationen und Simulator. "
            "Fehlende Hardware/OEM-Daten → Funktion deaktiviert und als Blocker markiert."
        ),
    }
