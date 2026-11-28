"""Phase 19 – LKW/Nutzfahrzeug Architektur-API.

Nur Lesen von Architektur-/Katalogdaten. Jede Diagnose-Aktion → 403.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.data.lkw_brands import (
    get_lkw_brand,
    list_lkw_brands,
    lkw_architecture,
    lkw_capabilities,
)

router = APIRouter(prefix="/lkw", tags=["lkw"])

_DISABLED_DETAIL = (
    "LKW-Diagnose ist nicht freigegeben (Phase 19 Architektur only). "
    "Keine J1939/RP1210-Ausführung ohne Hardware, Spec und Freigabe."
)


@router.get("/architecture")
def get_lkw_architecture(_user: CurrentUser) -> dict:
    return lkw_architecture()


@router.get("/brands")
def get_lkw_brands(
    _user: CurrentUser,
    q: str | None = Query(default=None, max_length=64),
) -> dict:
    brands = list_lkw_brands(q)
    return {
        "disclaimer_de": (
            "Nutzfahrzeug-Markenkatalog (Navigation). Keine Diagnoseabdeckung. "
            "release_status überall planned."
        ),
        "count": len(brands),
        "brands": brands,
    }


@router.get("/brands/{slug}")
def get_lkw_brand_detail(slug: str, _user: CurrentUser) -> dict:
    brand = get_lkw_brand(slug)
    if brand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="LKW-Marke nicht gefunden")
    return brand


@router.get("/capabilities")
def get_lkw_capabilities(_user: CurrentUser) -> dict:
    return lkw_capabilities()


@router.post("/diagnose", status_code=status.HTTP_403_FORBIDDEN)
def refuse_lkw_diagnose(_user: CurrentUser) -> None:
    """Bewusst gesperrt – verhindert vorgetäuschte LKW-Diagnose."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_DISABLED_DETAIL)


@router.post("/j1939/read", status_code=status.HTTP_403_FORBIDDEN)
def refuse_j1939_read(_user: CurrentUser) -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_DISABLED_DETAIL)


@router.post("/rp1210/connect", status_code=status.HTTP_403_FORBIDDEN)
def refuse_rp1210_connect(_user: CurrentUser) -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_DISABLED_DETAIL)
