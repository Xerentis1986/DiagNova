"""Phase 05 – Protokollkatalog, Capability-Matrix, Steuergeräteübersicht."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter

from app.api.deps import CurrentUser

# Protocol-Package aus dem Monorepo laden
_PROTO_SRC = Path(__file__).resolve().parents[5] / "packages" / "diagnostic-protocols" / "src"
if _PROTO_SRC.exists() and str(_PROTO_SRC) not in sys.path:
    sys.path.insert(0, str(_PROTO_SRC))

from diagnova_protocols import (  # noqa: E402
    architecture_overview,
    build_ecu_inventory,
    capability_matrix,
    ecu_overview_static,
    parse_elm_response,
    protocol_summary,
    uds_catalog,
)

router = APIRouter(prefix="/protocols", tags=["protocols"])


# Dokumentierter Simulator-Vektor (wie Connector Fake) – keine Hardware
_SIM_MULTI_ECU_BITMAP = "7E8 41 00 BE 1F A8 13\r\n7E9 41 00 88 18 80 00\r\n>"


@router.get("/architecture")
def get_architecture(_user: CurrentUser) -> dict:
    return architecture_overview()


@router.get("/catalog")
def get_protocol_catalog(_user: CurrentUser) -> dict:
    return protocol_summary()


@router.get("/capability-matrix")
def get_capability_matrix(_user: CurrentUser) -> dict:
    return capability_matrix()


@router.get("/uds")
def get_uds_catalog(_user: CurrentUser) -> dict:
    return uds_catalog()


@router.get("/ecu/overview")
def get_ecu_overview(_user: CurrentUser) -> dict:
    """Statische Kategorien + Standardadressen – kein Blindscan."""
    return ecu_overview_static()


@router.get("/ecu/simulated")
def get_ecu_simulated(_user: CurrentUser) -> dict:
    """Simulierte Mehr-ECU-Entdeckung aus dokumentiertem Testvektor."""
    parsed = parse_elm_response(_SIM_MULTI_ECU_BITMAP)
    inventory = build_ecu_inventory(
        parsed.frames,
        data_source="simulated",
        protocol_name="ISO 15765-4 (CAN 11/500)",
    )
    return {
        **inventory,
        "categories": ecu_overview_static()["categories"],
        "identification_read_first": {
            "status": "ok",
            "vin": "WVWZZZ1JZXW000001",
            "note_de": "Simulator-VIN (Mode 09) – keine echte Fahrzeugablesung.",
        },
        "disclaimer_de": (
            "Simulierte Steuergeräteübersicht. ABS/Airbag/Komfort ohne Definition. "
            "Kein Blindscan."
        ),
    }
