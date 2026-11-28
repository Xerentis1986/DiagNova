from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.data.dach_brands import (
    _brand_summary,
    capabilities_for_selection,
    get_brand,
    get_model,
    get_models,
    list_brands,
)
from app.schemas.api import BrandOut, CapabilitiesOut, CatalogModelOut, CatalogVariantOut

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/brands", response_model=list[BrandOut])
def catalog_brands(
    _user: CurrentUser,
    q: str | None = Query(default=None, max_length=64),
) -> list[dict]:
    return list_brands(q)


@router.get("/brands/{slug}", response_model=BrandOut)
def catalog_brand(slug: str, _user: CurrentUser) -> dict:
    brand = get_brand(slug)
    if brand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marke nicht gefunden")
    return _brand_summary(brand)


@router.get("/brands/{slug}/models", response_model=list[CatalogModelOut])
def catalog_models(slug: str, _user: CurrentUser) -> list[dict]:
    models = get_models(slug)
    if models is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marke nicht gefunden")
    return models


@router.get(
    "/brands/{slug}/models/{model_id}/variants",
    response_model=list[CatalogVariantOut],
)
def catalog_variants(slug: str, model_id: str, _user: CurrentUser) -> list[dict]:
    model = get_model(slug, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Modell nicht gefunden")
    return model["variants"]


@router.get("/capabilities", response_model=CapabilitiesOut)
def catalog_capabilities(
    _user: CurrentUser,
    brand_slug: str | None = Query(default=None),
) -> dict:
    # brand_slug reserved for spätere OEM-Matrix; aktuell einheitlich ehrlich
    _ = brand_slug
    return capabilities_for_selection()
