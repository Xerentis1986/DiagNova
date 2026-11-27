from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import desc

from app.api.deps import CurrentUser, DbSession
from app.data.dach_brands import get_brand
from app.models import UserBrandFavorite, UserRecentSelection, Vehicle
from app.schemas.api import (
    FavoritesOut,
    FavoritesUpdate,
    PreferencesOut,
    PreferencesUpdate,
    RecentSelectionOut,
)
from app.services.audit import write_audit

router = APIRouter(tags=["preferences"])


@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(user: CurrentUser) -> PreferencesOut:
    theme = user.theme_preference if user.theme_preference in {"light", "dark", "system"} else "system"
    return PreferencesOut(theme_preference=theme)  # type: ignore[arg-type]


@router.patch("/preferences", response_model=PreferencesOut)
def update_preferences(body: PreferencesUpdate, user: CurrentUser, db: DbSession) -> PreferencesOut:
    user.theme_preference = body.theme_preference
    db.add(user)
    write_audit(
        db,
        user_id=user.id,
        action="preferences_update",
        resource="user",
        detail=f"theme={body.theme_preference}",
    )
    db.commit()
    db.refresh(user)
    return PreferencesOut(theme_preference=body.theme_preference)


@router.get("/favorites/brands", response_model=FavoritesOut)
def get_favorite_brands(user: CurrentUser, db: DbSession) -> FavoritesOut:
    rows = (
        db.query(UserBrandFavorite)
        .filter(UserBrandFavorite.user_id == user.id)
        .order_by(UserBrandFavorite.created_at.asc())
        .all()
    )
    return FavoritesOut(brand_slugs=[r.brand_slug for r in rows])


@router.put("/favorites/brands", response_model=FavoritesOut)
def put_favorite_brands(body: FavoritesUpdate, user: CurrentUser, db: DbSession) -> FavoritesOut:
    slugs: list[str] = []
    seen: set[str] = set()
    for slug in body.brand_slugs:
        if slug in seen:
            continue
        if get_brand(slug) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unbekannte Marke: {slug}",
            )
        seen.add(slug)
        slugs.append(slug)

    db.query(UserBrandFavorite).filter(UserBrandFavorite.user_id == user.id).delete()
    for slug in slugs:
        db.add(UserBrandFavorite(user_id=user.id, brand_slug=slug))
    write_audit(
        db,
        user_id=user.id,
        action="favorites_update",
        resource="brands",
        detail=",".join(slugs) or "(leer)",
    )
    db.commit()
    return FavoritesOut(brand_slugs=slugs)


@router.get("/recent/selections", response_model=list[RecentSelectionOut])
def list_recent_selections(user: CurrentUser, db: DbSession) -> list[UserRecentSelection]:
    return (
        db.query(UserRecentSelection)
        .filter(UserRecentSelection.user_id == user.id)
        .order_by(desc(UserRecentSelection.used_at))
        .limit(12)
        .all()
    )


def record_recent_selection(
    db: DbSession,
    *,
    user_id: str,
    vehicle: Vehicle,
) -> None:
    row = UserRecentSelection(
        user_id=user_id,
        vehicle_id=vehicle.id,
        brand_slug=vehicle.catalog_brand_slug or vehicle.make.casefold().replace(" ", "-"),
        brand_name=vehicle.make,
        model_name=vehicle.model,
        series=vehicle.series,
        year=vehicle.year,
        engine=vehicle.engine,
        vin=vehicle.vin,
        used_at=datetime.now(timezone.utc),
    )
    db.add(row)
