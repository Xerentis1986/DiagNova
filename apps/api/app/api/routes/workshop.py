"""Phase 08 – Werkstattprofil, Mitglieder, Mandantenkontext."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.models import User, Workshop
from app.schemas.workshop import WorkshopMemberOut, WorkshopOut, WorkshopUpdate
from app.services.audit import write_audit
from app.services.tenant import get_user_workshop, require_admin_role, require_workshop_id
from app.services.workshop_validation import (
    validate_logo_data_url,
    validate_optional_email,
    validate_optional_phone,
)

router = APIRouter(prefix="/workshop", tags=["workshop"])


def _workshop_out(w: Workshop) -> WorkshopOut:
    return WorkshopOut(
        id=w.id,
        name=w.name,
        legal_name=w.legal_name,
        email=w.email,
        phone=w.phone,
        street=w.street,
        postal_code=w.postal_code,
        city=w.city,
        country=w.country,
        vat_id=w.vat_id,
        has_logo=bool(w.logo_data_url),
        retention_days=w.retention_days,
        notes=w.notes,
        is_example_data=w.is_example_data,
        archived_at=w.archived_at,
    )


@router.get("/me", response_model=WorkshopOut)
def get_my_workshop(user: CurrentUser, db: DbSession) -> WorkshopOut:
    workshop = get_user_workshop(db, user)
    return _workshop_out(workshop)


@router.get("/me/logo")
def get_my_workshop_logo(user: CurrentUser, db: DbSession) -> dict:
    workshop = get_user_workshop(db, user)
    if not workshop.logo_data_url:
        raise HTTPException(status_code=404, detail="Kein Logo hinterlegt")
    return {"logo_data_url": workshop.logo_data_url}


@router.patch("/me", response_model=WorkshopOut)
def update_my_workshop(body: WorkshopUpdate, user: CurrentUser, db: DbSession) -> WorkshopOut:
    require_admin_role(user)
    workshop = get_user_workshop(db, user)

    if body.name is not None:
        workshop.name = body.name.strip()
    if body.legal_name is not None:
        workshop.legal_name = body.legal_name.strip() or None
    if body.email is not None:
        ok, err = validate_optional_email(body.email)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        workshop.email = (body.email or "").strip().lower() or None
    if body.phone is not None:
        ok, err = validate_optional_phone(body.phone)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        workshop.phone = body.phone.strip() or None
    if body.street is not None:
        workshop.street = body.street.strip() or None
    if body.postal_code is not None:
        workshop.postal_code = body.postal_code.strip() or None
    if body.city is not None:
        workshop.city = body.city.strip() or None
    if body.country is not None:
        workshop.country = body.country.strip().upper()
    if body.vat_id is not None:
        workshop.vat_id = body.vat_id.strip() or None
    if body.retention_days is not None:
        workshop.retention_days = body.retention_days
    if body.notes is not None:
        workshop.notes = body.notes.strip() or None
    if body.clear_logo:
        workshop.logo_data_url = None
    elif body.logo_data_url is not None:
        ok, err = validate_logo_data_url(body.logo_data_url)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        workshop.logo_data_url = body.logo_data_url.strip() or None

    db.add(workshop)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=workshop.id,
        action="workshop_update",
        resource=f"workshop:{workshop.id}",
        detail="profile",
    )
    db.commit()
    db.refresh(workshop)
    return _workshop_out(workshop)


@router.get("/me/members", response_model=list[WorkshopMemberOut])
def list_workshop_members(user: CurrentUser, db: DbSession) -> list[WorkshopMemberOut]:
    wid = require_workshop_id(user)
    members = (
        db.query(User)
        .filter(User.workshop_id == wid)
        .order_by(User.full_name)
        .all()
    )
    return [
        WorkshopMemberOut(
            id=m.id,
            email=m.email,
            full_name=m.full_name,
            role=m.role,  # type: ignore[arg-type]
            is_active=m.is_active,
        )
        for m in members
    ]
