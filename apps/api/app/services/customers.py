"""Kunden-CRUD, Dubletten, Merge, DSGVO-Export/Löschung (Phase 08)."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Customer, CustomerVehicleLink, Vehicle, WorkOrder
from app.services.workshop_validation import (
    validate_optional_email,
    validate_optional_phone,
)


OPEN_ORDER_STATUSES = {"open", "in_progress"}


def _norm_email(email: str | None) -> str | None:
    if not email or not email.strip():
        return None
    return email.strip().lower()


def _norm_phone(phone: str | None) -> str | None:
    if not phone or not phone.strip():
        return None
    return "".join(ch for ch in phone if ch.isdigit() or ch == "+")


def find_customer_duplicates(
    db: Session,
    *,
    workshop_id: str,
    display_name: str,
    email: str | None,
    phone: str | None,
    exclude_id: str | None = None,
) -> list[Customer]:
    """Heuristik: gleiche E-Mail, gleiches Telefon oder gleicher Name (nicht archiviert)."""
    q = db.query(Customer).filter(
        Customer.workshop_id == workshop_id,
        Customer.archived_at.is_(None),
        Customer.anonymized_at.is_(None),
    )
    if exclude_id:
        q = q.filter(Customer.id != exclude_id)

    candidates: dict[str, Customer] = {}
    name = display_name.strip().lower()
    email_n = _norm_email(email)
    phone_n = _norm_phone(phone)

    for c in q.all():
        score_hit = False
        if email_n and _norm_email(c.email) == email_n:
            score_hit = True
        if phone_n and _norm_phone(c.phone) == phone_n:
            score_hit = True
        if c.display_name.strip().lower() == name:
            score_hit = True
        if score_hit:
            candidates[c.id] = c
    return list(candidates.values())


def create_customer(
    db: Session,
    *,
    workshop_id: str,
    display_name: str,
    email: str | None,
    phone: str | None,
    street: str | None,
    postal_code: str | None,
    city: str | None,
    country: str | None,
    notes: str | None,
    force: bool,
    is_example_data: bool = False,
) -> Customer:
    name = display_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name fehlt")
    ok, err = validate_optional_email(email)
    if not ok:
        raise HTTPException(status_code=400, detail=err)
    ok, err = validate_optional_phone(phone)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    email_n = _norm_email(email)
    duplicates = find_customer_duplicates(
        db,
        workshop_id=workshop_id,
        display_name=name,
        email=email_n,
        phone=phone,
    )
    if duplicates and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message_de": "Mögliche Dublette – manuelle Prüfung oder force=true",
                "duplicates": [
                    {
                        "id": d.id,
                        "display_name": d.display_name,
                        "email": d.email,
                        "phone": d.phone,
                    }
                    for d in duplicates
                ],
            },
        )

    customer = Customer(
        workshop_id=workshop_id,
        display_name=name,
        email=email_n,
        phone=(phone or "").strip() or None,
        street=(street or "").strip() or None,
        postal_code=(postal_code or "").strip() or None,
        city=(city or "").strip() or None,
        country=(country or "").strip().upper() or None,
        notes=(notes or "").strip() or None,
        is_example_data=is_example_data,
    )
    db.add(customer)
    db.flush()
    return customer


def merge_customers(
    db: Session,
    *,
    workshop_id: str,
    target_id: str,
    source_id: str,
) -> Customer:
    if target_id == source_id:
        raise HTTPException(status_code=400, detail="Quelle und Ziel identisch")
    target = db.get(Customer, target_id)
    source = db.get(Customer, source_id)
    if (
        target is None
        or source is None
        or target.workshop_id != workshop_id
        or source.workshop_id != workshop_id
        or target.archived_at is not None
        or source.anonymized_at is not None
    ):
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    # Fahrzeuge umhängen
    for v in db.query(Vehicle).filter(Vehicle.customer_id == source.id).all():
        v.customer_id = target.id
        db.add(v)

    links = db.query(CustomerVehicleLink).filter(CustomerVehicleLink.customer_id == source.id).all()
    for link in links:
        exists = (
            db.query(CustomerVehicleLink)
            .filter(
                CustomerVehicleLink.customer_id == target.id,
                CustomerVehicleLink.vehicle_id == link.vehicle_id,
            )
            .first()
        )
        if exists:
            db.delete(link)
        else:
            link.customer_id = target.id
            db.add(link)

    for order in db.query(WorkOrder).filter(WorkOrder.customer_id == source.id).all():
        order.customer_id = target.id
        db.add(order)

    # Leere Felder am Ziel aus Quelle ergänzen (minimale Daten)
    if not target.email and source.email:
        target.email = source.email
    if not target.phone and source.phone:
        target.phone = source.phone
    if not target.street and source.street:
        target.street = source.street
        target.postal_code = source.postal_code
        target.city = source.city
        target.country = source.country

    source.archived_at = datetime.now(timezone.utc)
    source.notes = ((source.notes or "") + f"\n[Zusammengeführt in {target.id}]").strip()
    db.add(target)
    db.add(source)
    db.flush()
    return target


def export_customer_bundle(db: Session, *, workshop_id: str, customer_id: str) -> dict:
    customer = db.get(Customer, customer_id)
    if customer is None or customer.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.workshop_id == workshop_id, Vehicle.customer_id == customer.id)
        .all()
    )
    orders = (
        db.query(WorkOrder)
        .filter(WorkOrder.workshop_id == workshop_id, WorkOrder.customer_id == customer.id)
        .all()
    )
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "purpose_de": "DSGVO-Auskunft / Datenportabilität – nur eigener Mandant",
        "customer": {
            "id": customer.id,
            "display_name": customer.display_name,
            "email": customer.email,
            "phone": customer.phone,
            "street": customer.street,
            "postal_code": customer.postal_code,
            "city": customer.city,
            "country": customer.country,
            "notes": customer.notes,
            "archived_at": customer.archived_at.isoformat() if customer.archived_at else None,
            "anonymized_at": customer.anonymized_at.isoformat() if customer.anonymized_at else None,
            "is_example_data": customer.is_example_data,
        },
        "vehicles": [
            {
                "id": v.id,
                "vin": v.vin,
                "license_plate": v.license_plate,
                "make": v.make,
                "model": v.model,
                "year": v.year,
                "engine": v.engine,
                "odometer_km": v.odometer_km,
                "archived_at": v.archived_at.isoformat() if v.archived_at else None,
            }
            for v in vehicles
        ],
        "work_orders": [
            {
                "id": o.id,
                "title": o.title,
                "status": o.status,
                "notes": o.notes,
                "repair_summary": o.repair_summary,
                "odometer_km": o.odometer_km,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ],
    }


def archive_or_delete_customer(
    db: Session,
    *,
    workshop_id: str,
    customer_id: str,
    mode: str,
    force: bool = False,
) -> dict:
    """mode: archive | anonymize | delete. Offene Aufträge blockieren Löschen."""
    customer = db.get(Customer, customer_id)
    if customer is None or customer.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

    open_orders = (
        db.query(WorkOrder)
        .filter(
            WorkOrder.customer_id == customer.id,
            WorkOrder.workshop_id == workshop_id,
            WorkOrder.status.in_(OPEN_ORDER_STATUSES),
            WorkOrder.archived_at.is_(None),
        )
        .count()
    )
    if open_orders and mode in {"delete", "anonymize"} and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message_de": "Löschkonflikt: offene Werkstattaufträge vorhanden",
                "open_work_orders": open_orders,
                "hint_de": "Aufträge zuerst abschließen/archivieren oder force=true (Admin).",
            },
        )

    now = datetime.now(timezone.utc)
    if mode == "archive":
        customer.archived_at = now
        db.add(customer)
        return {"status": "archived", "customer_id": customer.id}

    if mode == "anonymize":
        customer.display_name = f"Anonymisiert-{customer.id[:8]}"
        customer.email = None
        customer.phone = None
        customer.street = None
        customer.postal_code = None
        customer.city = None
        customer.country = None
        customer.notes = None
        customer.anonymized_at = now
        customer.archived_at = customer.archived_at or now
        db.add(customer)
        return {"status": "anonymized", "customer_id": customer.id}

    if mode == "delete":
        # Harte Löschung nur ohne abhängige Fahrzeuge/Aufträge oder mit force (Aufträge/Links lösen)
        vehicle_count = db.query(Vehicle).filter(Vehicle.customer_id == customer.id).count()
        if (vehicle_count or open_orders) and not force:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message_de": "Löschkonflikt: Fahrzeuge oder Aufträge verknüpft",
                    "vehicles": vehicle_count,
                    "open_work_orders": open_orders,
                },
            )
        if force:
            db.query(Vehicle).filter(Vehicle.customer_id == customer.id).update(
                {"customer_id": None}, synchronize_session=False
            )
            db.query(WorkOrder).filter(WorkOrder.customer_id == customer.id).update(
                {"customer_id": None}, synchronize_session=False
            )
            db.query(CustomerVehicleLink).filter(CustomerVehicleLink.customer_id == customer.id).delete(
                synchronize_session=False
            )
        db.delete(customer)
        return {"status": "deleted", "customer_id": customer_id}

    raise HTTPException(status_code=400, detail="Unbekannter Löschmodus")


def list_customers_filtered(
    db: Session,
    *,
    workshop_id: str,
    q: str | None,
    include_archived: bool,
    city: str | None = None,
) -> list[Customer]:
    query = db.query(Customer).filter(Customer.workshop_id == workshop_id)
    if not include_archived:
        query = query.filter(Customer.archived_at.is_(None), Customer.anonymized_at.is_(None))
    if city:
        query = query.filter(Customer.city.ilike(f"%{city.strip()}%"))
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Customer.display_name.ilike(term),
                Customer.email.ilike(term),
                Customer.phone.ilike(term),
                Customer.city.ilike(term),
            )
        )
    return query.order_by(Customer.display_name).all()


def export_json(bundle: dict) -> str:
    return json.dumps(bundle, ensure_ascii=False, indent=2)
