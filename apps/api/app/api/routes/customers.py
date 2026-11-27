"""Phase 08 – Kundenverwaltung mit Mandantentrennung und DSGVO."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.api.deps import CurrentUser, DbSession
from app.models import Customer, CustomerVehicleLink, Vehicle
from app.schemas.workshop import (
    CustomerCreate,
    CustomerDeleteIn,
    CustomerMergeIn,
    CustomerOut,
    CustomerUpdate,
    CustomerVehicleAssign,
)
from app.services.audit import write_audit
from app.services.customers import (
    archive_or_delete_customer,
    create_customer,
    export_customer_bundle,
    export_json,
    find_customer_duplicates,
    list_customers_filtered,
    merge_customers,
)
from app.services.tenant import require_workshop_id, require_write_role
from app.services.workshop_validation import validate_optional_email, validate_optional_phone

router = APIRouter(prefix="/customers", tags=["customers"])


def _get_tenant_customer(db: DbSession, user: CurrentUser, customer_id: str) -> Customer:
    wid = require_workshop_id(user)
    customer = db.get(Customer, customer_id)
    if customer is None or customer.workshop_id != wid:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    return customer


@router.get("", response_model=list[CustomerOut])
def list_customers(
    user: CurrentUser,
    db: DbSession,
    q: str | None = Query(default=None, max_length=128),
    city: str | None = Query(default=None, max_length=128),
    include_archived: bool = False,
) -> list[Customer]:
    wid = require_workshop_id(user)
    return list_customers_filtered(
        db, workshop_id=wid, q=q, include_archived=include_archived, city=city
    )


@router.get("/duplicates", response_model=list[CustomerOut])
def preview_duplicates(
    user: CurrentUser,
    db: DbSession,
    display_name: str = Query(min_length=1, max_length=255),
    email: str | None = None,
    phone: str | None = None,
) -> list[Customer]:
    wid = require_workshop_id(user)
    return find_customer_duplicates(
        db,
        workshop_id=wid,
        display_name=display_name,
        email=email,
        phone=phone,
    )


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer_route(body: CustomerCreate, user: CurrentUser, db: DbSession) -> Customer:
    require_write_role(user)
    wid = require_workshop_id(user)
    customer = create_customer(
        db,
        workshop_id=wid,
        display_name=body.display_name,
        email=body.email,
        phone=body.phone,
        street=body.street,
        postal_code=body.postal_code,
        city=body.city,
        country=body.country,
        notes=body.notes,
        force=body.force,
        is_example_data=False,
    )
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="customer_create",
        resource=f"customer:{customer.id}",
        detail=customer.display_name,
    )
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, user: CurrentUser, db: DbSession) -> Customer:
    return _get_tenant_customer(db, user, customer_id)


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: str, body: CustomerUpdate, user: CurrentUser, db: DbSession
) -> Customer:
    require_write_role(user)
    customer = _get_tenant_customer(db, user, customer_id)
    if customer.anonymized_at is not None:
        raise HTTPException(status_code=400, detail="Anonymisierter Kunde nicht änderbar")

    if body.display_name is not None:
        customer.display_name = body.display_name.strip()
    if body.email is not None:
        ok, err = validate_optional_email(body.email)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        customer.email = (body.email or "").strip().lower() or None
    if body.phone is not None:
        ok, err = validate_optional_phone(body.phone)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        customer.phone = body.phone.strip() or None
    if body.street is not None:
        customer.street = body.street.strip() or None
    if body.postal_code is not None:
        customer.postal_code = body.postal_code.strip() or None
    if body.city is not None:
        customer.city = body.city.strip() or None
    if body.country is not None:
        customer.country = body.country.strip().upper() or None
    if body.notes is not None:
        customer.notes = body.notes.strip() or None

    db.add(customer)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=customer.workshop_id,
        action="customer_update",
        resource=f"customer:{customer.id}",
    )
    db.commit()
    db.refresh(customer)
    return customer


@router.post("/{customer_id}/merge", response_model=CustomerOut)
def merge_customer_route(
    customer_id: str, body: CustomerMergeIn, user: CurrentUser, db: DbSession
) -> Customer:
    require_write_role(user)
    wid = require_workshop_id(user)
    target = merge_customers(
        db,
        workshop_id=wid,
        target_id=customer_id,
        source_id=body.source_customer_id,
    )
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="customer_merge",
        resource=f"customer:{target.id}",
        detail=f"source={body.source_customer_id}",
    )
    db.commit()
    db.refresh(target)
    return target


@router.get("/{customer_id}/export")
def export_customer(customer_id: str, user: CurrentUser, db: DbSession) -> PlainTextResponse:
    wid = require_workshop_id(user)
    bundle = export_customer_bundle(db, workshop_id=wid, customer_id=customer_id)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="customer_export",
        resource=f"customer:{customer_id}",
        detail="dsgvo_export",
    )
    return PlainTextResponse(
        export_json(bundle),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="customer-{customer_id}.json"'},
    )


@router.post("/{customer_id}/delete")
def delete_customer_route(
    customer_id: str, body: CustomerDeleteIn, user: CurrentUser, db: DbSession
) -> dict:
    require_write_role(user)
    wid = require_workshop_id(user)
    if body.mode == "delete" and user.role != "admin":
        raise HTTPException(status_code=403, detail="Hartes Löschen nur Admin")
    if body.force and user.role != "admin":
        raise HTTPException(status_code=403, detail="force nur Admin")
    result = archive_or_delete_customer(
        db,
        workshop_id=wid,
        customer_id=customer_id,
        mode=body.mode,
        force=body.force,
    )
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action=f"customer_{body.mode}",
        resource=f"customer:{customer_id}",
        detail=str(result),
    )
    db.commit()
    return result


@router.post("/{customer_id}/vehicles", response_model=CustomerOut)
def assign_vehicle(
    customer_id: str, body: CustomerVehicleAssign, user: CurrentUser, db: DbSession
) -> Customer:
    require_write_role(user)
    customer = _get_tenant_customer(db, user, customer_id)
    vehicle = db.get(Vehicle, body.vehicle_id)
    if vehicle is None or vehicle.workshop_id != customer.workshop_id:
        raise HTTPException(status_code=404, detail="Fahrzeug nicht gefunden")

    if body.is_primary:
        vehicle.customer_id = customer.id
        db.add(vehicle)

    existing = (
        db.query(CustomerVehicleLink)
        .filter(
            CustomerVehicleLink.customer_id == customer.id,
            CustomerVehicleLink.vehicle_id == vehicle.id,
        )
        .first()
    )
    if existing is None:
        db.add(
            CustomerVehicleLink(
                workshop_id=customer.workshop_id,
                customer_id=customer.id,
                vehicle_id=vehicle.id,
                is_primary=body.is_primary,
            )
        )
    else:
        existing.is_primary = body.is_primary
        db.add(existing)

    write_audit(
        db,
        user_id=user.id,
        workshop_id=customer.workshop_id,
        action="customer_vehicle_assign",
        resource=f"customer:{customer.id}",
        detail=f"vehicle={vehicle.id}",
    )
    db.commit()
    db.refresh(customer)
    return customer
