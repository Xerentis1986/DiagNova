"""Phase 08 – Werkstattaufträge (Status, Notizen, Reparaturen)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.models import Customer, Vehicle, WorkOrder
from app.schemas.workshop import WorkOrderCreate, WorkOrderOut, WorkOrderUpdate
from app.services.audit import write_audit
from app.services.tenant import require_workshop_id, require_write_role
from app.services.workshop_validation import validate_odometer

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

VALID_STATUSES = {"open", "in_progress", "done", "cancelled"}


def _get_order(db: DbSession, user: CurrentUser, order_id: str) -> WorkOrder:
    wid = require_workshop_id(user)
    order = db.get(WorkOrder, order_id)
    if order is None or order.workshop_id != wid:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden")
    return order


def _assert_customer(db: DbSession, workshop_id: str, customer_id: str | None) -> None:
    if customer_id is None:
        return
    c = db.get(Customer, customer_id)
    if c is None or c.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="Kunde nicht gefunden")


def _assert_vehicle(db: DbSession, workshop_id: str, vehicle_id: str | None) -> None:
    if vehicle_id is None:
        return
    v = db.get(Vehicle, vehicle_id)
    if v is None or v.workshop_id != workshop_id:
        raise HTTPException(status_code=404, detail="Fahrzeug nicht gefunden")


@router.get("", response_model=list[WorkOrderOut])
def list_work_orders(
    user: CurrentUser,
    db: DbSession,
    status_filter: str | None = Query(default=None, alias="status"),
    customer_id: str | None = None,
    vehicle_id: str | None = None,
    q: str | None = Query(default=None, max_length=128),
    include_archived: bool = False,
) -> list[WorkOrder]:
    wid = require_workshop_id(user)
    query = db.query(WorkOrder).filter(WorkOrder.workshop_id == wid)
    if not include_archived:
        query = query.filter(WorkOrder.archived_at.is_(None))
    if status_filter:
        if status_filter not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="Ungültiger Status")
        query = query.filter(WorkOrder.status == status_filter)
    if customer_id:
        query = query.filter(WorkOrder.customer_id == customer_id)
    if vehicle_id:
        query = query.filter(WorkOrder.vehicle_id == vehicle_id)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(WorkOrder.title.ilike(term))
    return query.order_by(WorkOrder.created_at.desc()).all()


@router.post("", response_model=WorkOrderOut, status_code=201)
def create_work_order(body: WorkOrderCreate, user: CurrentUser, db: DbSession) -> WorkOrder:
    require_write_role(user)
    wid = require_workshop_id(user)
    _assert_customer(db, wid, body.customer_id)
    _assert_vehicle(db, wid, body.vehicle_id)
    ok, err = validate_odometer(body.odometer_km)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    order = WorkOrder(
        workshop_id=wid,
        customer_id=body.customer_id,
        vehicle_id=body.vehicle_id,
        created_by_user_id=user.id,
        title=body.title.strip(),
        status=body.status,
        notes=(body.notes or "").strip() or None,
        repair_summary=(body.repair_summary or "").strip() or None,
        odometer_km=body.odometer_km,
        is_example_data=False,
    )
    db.add(order)
    db.flush()
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="work_order_create",
        resource=f"work_order:{order.id}",
        detail=order.title,
    )
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=WorkOrderOut)
def get_work_order(order_id: str, user: CurrentUser, db: DbSession) -> WorkOrder:
    return _get_order(db, user, order_id)


@router.patch("/{order_id}", response_model=WorkOrderOut)
def update_work_order(
    order_id: str, body: WorkOrderUpdate, user: CurrentUser, db: DbSession
) -> WorkOrder:
    require_write_role(user)
    order = _get_order(db, user, order_id)
    wid = order.workshop_id

    if body.title is not None:
        order.title = body.title.strip()
    if body.status is not None:
        order.status = body.status
    if body.notes is not None:
        order.notes = body.notes.strip() or None
    if body.repair_summary is not None:
        order.repair_summary = body.repair_summary.strip() or None
    if body.odometer_km is not None:
        ok, err = validate_odometer(body.odometer_km)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        order.odometer_km = body.odometer_km
    if body.customer_id is not None:
        _assert_customer(db, wid, body.customer_id)
        order.customer_id = body.customer_id
    if body.vehicle_id is not None:
        _assert_vehicle(db, wid, body.vehicle_id)
        order.vehicle_id = body.vehicle_id

    db.add(order)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=wid,
        action="work_order_update",
        resource=f"work_order:{order.id}",
        detail=order.status,
    )
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/archive", response_model=WorkOrderOut)
def archive_work_order(order_id: str, user: CurrentUser, db: DbSession) -> WorkOrder:
    require_write_role(user)
    order = _get_order(db, user, order_id)
    order.archived_at = datetime.now(timezone.utc)
    db.add(order)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=order.workshop_id,
        action="work_order_archive",
        resource=f"work_order:{order.id}",
    )
    db.commit()
    db.refresh(order)
    return order
