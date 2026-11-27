"""Capability-Matrix pro Adapter – ehrlich und spezifikationsgebunden.

Ein günstiger ELM327/OBD-Dongle ist kein universelles DoIP/CAN-FD/J2534-Interface.
"""

from __future__ import annotations

from typing import Any, Literal

CapLevel = Literal[
    "supported_simulated",
    "supported_code_untested_hw",
    "partial_documented",
    "not_supported",
    "blocked",
    "planned",
]


ADAPTER_CAPABILITIES: list[dict[str, Any]] = [
    {
        "adapter_id": "simulator",
        "name": "DiagNova Fake/Simulator",
        "data_source": "simulated",
        "hardware_tested": False,
        "protocols": {
            "sae_j1979_obd": "supported_simulated",
            "iso_15765_2_isotp": "supported_simulated",
            "iso_15765_4_obd_can": "supported_simulated",
            "iso_14229_uds": "partial_documented",
            "iso_9141_2": "partial_documented",
            "iso_14230_kwp2000": "partial_documented",
            "sae_j1850": "partial_documented",
            "iso_11898_can": "partial_documented",
            "can_fd": "not_supported",
            "iso_13400_doip": "not_supported",
            "sae_j2534": "not_supported",
            "iso_22900_dpdu": "not_supported",
            "sae_j1939": "not_supported",
            "rp1210": "not_supported",
        },
        "notes_de": "Separater Simulator-Pfad; dokumentierte Testvektoren.",
    },
    {
        "adapter_id": "elm327-obd",
        "name": "ELM327-kompatibel (seriell/SPP)",
        "data_source": "live",
        "hardware_tested": False,
        "protocols": {
            "sae_j1979_obd": "supported_code_untested_hw",
            "iso_15765_2_isotp": "partial_documented",
            "iso_15765_4_obd_can": "supported_code_untested_hw",
            "iso_14229_uds": "partial_documented",
            "iso_9141_2": "partial_documented",
            "iso_14230_kwp2000": "partial_documented",
            "sae_j1850": "partial_documented",
            "iso_11898_can": "partial_documented",
            "can_fd": "not_supported",
            "iso_13400_doip": "not_supported",
            "sae_j2534": "not_supported",
            "iso_22900_dpdu": "not_supported",
            "sae_j1939": "not_supported",
            "rp1210": "not_supported",
        },
        "notes_de": (
            "Codepfad vorhanden, Allowlist aktiv. Keine Hardwarefreigabe (BLK-HW). "
            "Kein DoIP, kein CAN-FD, kein J2534."
        ),
        "blocker": "BLK-HW",
    },
    {
        "adapter_id": "vgate-vlinker-mc-plus",
        "name": "Vgate vLinker MC+",
        "data_source": "live",
        "hardware_tested": False,
        "protocols": {
            "sae_j1979_obd": "blocked",
            "iso_15765_4_obd_can": "blocked",
            "can_fd": "not_supported",
            "iso_13400_doip": "not_supported",
            "sae_j2534": "not_supported",
        },
        "notes_de": "Windows-SPP-Variante nicht verifiziert (BLK-ADAPTER).",
        "blocker": "BLK-ADAPTER",
    },
    {
        "adapter_id": "delphi-autocom",
        "name": "Delphi / Autocom Interface",
        "data_source": "live",
        "hardware_tested": False,
        "protocols": {
            "sae_j1979_obd": "blocked",
            "sae_j2534": "blocked",
            "iso_22900_dpdu": "blocked",
            "iso_13400_doip": "blocked",
        },
        "notes_de": "Keine dokumentierte öffentliche Schnittstelle; Modell unbekannt.",
        "blocker": "BLK-ADAPTER",
    },
    {
        "adapter_id": "j2534-passthru",
        "name": "J2534 PassThru (generisch)",
        "data_source": "live",
        "hardware_tested": False,
        "protocols": {
            "sae_j2534": "planned",
            "sae_j1979_obd": "planned",
            "iso_15765_2_isotp": "planned",
            "iso_14229_uds": "planned",
            "can_fd": "planned",
            "iso_13400_doip": "not_supported",
        },
        "notes_de": "Nur Vorbereitung/Dokumentation – keine DLL-Bindung ohne Gerät.",
        "blocker": "BLK-HW",
    },
    {
        "adapter_id": "doip-ethernet",
        "name": "DoIP Ethernet Interface",
        "data_source": "live",
        "hardware_tested": False,
        "protocols": {
            "iso_13400_doip": "planned",
            "iso_14229_uds": "planned",
            "iso_15765_2_isotp": "not_supported",
            "sae_j1979_obd": "planned",
        },
        "notes_de": "Vorbereitung; ELM-Adapter ersetzt DoIP nicht.",
        "blocker": "BLK-HW",
    },
]


def capability_matrix() -> dict[str, Any]:
    return {
        "disclaimer_de": (
            "Capability ≠ Freigabe. hardware_tested ist überall false. "
            "Günstiger OBD-Adapter ist kein universelles DoIP/CAN-FD-Interface."
        ),
        "adapters": ADAPTER_CAPABILITIES,
    }


def adapter_capabilities(adapter_id: str) -> dict[str, Any] | None:
    for a in ADAPTER_CAPABILITIES:
        if a["adapter_id"] == adapter_id:
            return a
    return None
