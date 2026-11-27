"""Protokollkatalog Phase 05 – Status ehrlich, keine Vortäuschung von Hardwareabdeckung.

Quellen (öffentlich referenzierbar, keine OEM-Geheimnisse):
- SAE J1979 / ISO 15031 (OBD Mode-Dienste)
- ISO 15765-2 (ISO-TP), ISO 15765-4 (OBD on CAN Adressen)
- ISO 14229 (UDS) – NRC und Dienst-IDs öffentlich bekannt
- ISO 9141-2, ISO 14230 (KWP2000), SAE J1850 – ELM ATSP-Zuordnung
- ISO 13400 (DoIP), SAE J2534, ISO 22900, SAE J1939/RP1210 – Vorbereitung
"""

from __future__ import annotations

from typing import Any, Literal

ImplStatus = Literal[
    "simulated_tested",
    "parser_only",
    "documented_prep",
    "blocked",
    "planned_later",
]


PROTOCOLS: list[dict[str, Any]] = [
    {
        "id": "sae_j1979_obd",
        "name": "OBD-II / EOBD (SAE J1979 / ISO 15031)",
        "layer": "protocol",
        "status": "simulated_tested",
        "phase": 4,
        "notes_de": "Mode 01–0A Parser, Allowlist, Simulator – keine Hardwarefreigabe.",
        "source": "SAE J1979 / ISO 15031",
    },
    {
        "id": "iso_15765_2_isotp",
        "name": "ISO 15765-2 (ISO-TP Segmentierung)",
        "layer": "protocol",
        "status": "parser_only",
        "phase": 5,
        "notes_de": "Single/First/Consecutive/Flow-Control Framing an dokumentierten Testvektoren.",
        "source": "ISO 15765-2",
    },
    {
        "id": "iso_15765_4_obd_can",
        "name": "ISO 15765-4 (OBD on CAN Adressen)",
        "layer": "protocol",
        "status": "simulated_tested",
        "phase": 5,
        "notes_de": "Nur Standard-Adressen 0x7DF / 0x7E0–0x7E7 / 0x7E8–0x7EF – keine OEM-Erweiterungen.",
        "source": "ISO 15765-4",
    },
    {
        "id": "iso_14229_uds",
        "name": "UDS ISO 14229",
        "layer": "protocol",
        "status": "parser_only",
        "phase": 5,
        "notes_de": "NRC-Tabelle + lesende Dienst-IDs; keine Schreib-/Security-Sessions aktiv.",
        "source": "ISO 14229",
    },
    {
        "id": "iso_9141_2",
        "name": "ISO 9141-2",
        "layer": "protocol",
        "status": "documented_prep",
        "phase": 5,
        "notes_de": "ELM ATSP-Zuordnung (typisch Protocol 3); kein eigener K-Line-Stack ohne Hardware.",
        "source": "ISO 9141-2 / ELM327 ATDP",
        "elm_atsp": "3",
    },
    {
        "id": "iso_14230_kwp2000",
        "name": "ISO 14230 / KWP2000",
        "layer": "protocol",
        "status": "documented_prep",
        "phase": 5,
        "notes_de": "ELM ATSP 4/5; UDS-ähnliche Dienste – Implementierung nur bei belegter Hardware.",
        "source": "ISO 14230",
        "elm_atsp": "4/5",
    },
    {
        "id": "sae_j1850",
        "name": "SAE J1850 PWM/VPW",
        "layer": "protocol",
        "status": "documented_prep",
        "phase": 5,
        "notes_de": "ELM ATSP 1/2; in Europa selten – kein aktiver Stack ohne Adapterbeleg.",
        "source": "SAE J1850",
        "elm_atsp": "1/2",
    },
    {
        "id": "iso_11898_can",
        "name": "CAN / ISO 11898",
        "layer": "transport",
        "status": "documented_prep",
        "phase": 5,
        "notes_de": "Physikschicht; über ELM/ISO-TP indirekt. Kein Raw-CAN-Interface im ELM-Pfad.",
        "source": "ISO 11898",
    },
    {
        "id": "can_fd",
        "name": "CAN FD",
        "layer": "transport",
        "status": "blocked",
        "phase": 5,
        "notes_de": "Günstiger OBD-ELM-Adapter ist kein CAN-FD-Interface. Benötigt geeignetes Interface.",
        "source": "ISO 11898-1 CAN FD",
        "blocker": "BLK-HW",
    },
    {
        "id": "iso_13400_doip",
        "name": "DoIP ISO 13400",
        "layer": "transport",
        "status": "documented_prep",
        "phase": 5,
        "notes_de": "Vorbereitung/Dokumentation; kein Ethernet-Stack ohne DoIP-fähige Hardware.",
        "source": "ISO 13400",
        "blocker": "BLK-HW",
    },
    {
        "id": "sae_j2534",
        "name": "SAE J2534 PassThru",
        "layer": "adapter",
        "status": "documented_prep",
        "phase": 5,
        "notes_de": "Hardware-API-Vorbereitung; DLL-Bindung erst mit verifiziertem Interface.",
        "source": "SAE J2534",
        "blocker": "BLK-HW",
    },
    {
        "id": "iso_22900_dpdu",
        "name": "ISO 22900 D-PDU API",
        "layer": "adapter",
        "status": "documented_prep",
        "phase": 5,
        "notes_de": "MVCI/D-PDU – nur Dokumentation; keine Implementierung ohne Runtime/Lizenz.",
        "source": "ISO 22900",
        "blocker": "BLK-HW",
    },
    {
        "id": "sae_j1939",
        "name": "SAE J1939",
        "layer": "protocol",
        "status": "planned_later",
        "phase": 19,
        "notes_de": "LKW-Erweiterung Phase 19; 24-V/RP1210-Hardware erforderlich.",
        "source": "SAE J1939",
        "blocker": "BLK-HW",
    },
    {
        "id": "rp1210",
        "name": "RP1210",
        "layer": "adapter",
        "status": "planned_later",
        "phase": 19,
        "notes_de": "LKW-Adapter-API; bewusst später.",
        "source": "TMC RP1210",
        "blocker": "BLK-HW",
    },
]


def list_protocols(*, status: str | None = None) -> list[dict[str, Any]]:
    if status is None:
        return list(PROTOCOLS)
    return [p for p in PROTOCOLS if p["status"] == status]


def protocol_by_id(protocol_id: str) -> dict[str, Any] | None:
    for p in PROTOCOLS:
        if p["id"] == protocol_id:
            return p
    return None


def protocol_summary() -> dict[str, Any]:
    by_status: dict[str, int] = {}
    for p in PROTOCOLS:
        by_status[p["status"]] = by_status.get(p["status"], 0) + 1
    return {
        "count": len(PROTOCOLS),
        "by_status": by_status,
        "disclaimer_de": (
            "Status bezieht sich auf Code/Simulator – nicht auf hardwaregetestete Abdeckung. "
            "Kein Protokoll ist freigegeben."
        ),
        "protocols": PROTOCOLS,
    }
