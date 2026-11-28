"""Phase 13 – Abos, Entitlements, Geräte, kritische Ops (Mandant)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.subscriptions import (
    ActivatePlanRequest,
    CancelSubscriptionRequest,
    CriticalOpOut,
    CriticalOpStartRequest,
    DeviceBindRequest,
    DeviceOut,
    EntitlementCheckOut,
    PlanOut,
    StartTrialRequest,
    SubscriptionOut,
)
from app.models.subscriptions import CriticalOperationLock, DeviceBinding
from app.services import subscriptions as subsvc
from app.services.tenant import require_admin_role, require_workshop_id

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=list[PlanOut])
def list_plans(_user: CurrentUser) -> list[PlanOut]:
    return [PlanOut(**p) for p in subsvc.plans_public()]


@router.get("/me", response_model=SubscriptionOut)
def my_subscription(user: CurrentUser, db: DbSession) -> SubscriptionOut:
    wid = require_workshop_id(user)
    sub = subsvc.get_workshop_subscription(db, wid)
    if sub is None:
        # Leerer Zustand – kein auto-create bei GET
        return SubscriptionOut(
            id="",
            workshop_id=wid,
            plan_code="none",
            status="incomplete",
            payment_provider="none",
            entitlements=[],
            license_active=False,
            allows_new_operations=False,
            message_de="Kein Abo vorhanden.",
            payment_note_de=subsvc.PAYMENT_NOTE,
        )
    return SubscriptionOut(**subsvc.subscription_to_dict(db, sub))


@router.post("/me/trial", response_model=SubscriptionOut)
def start_trial(body: StartTrialRequest, user: CurrentUser, db: DbSession) -> SubscriptionOut:
    require_admin_role(user)
    wid = require_workshop_id(user)
    sub = subsvc.start_trial(db, wid, user, body.plan_code)
    return SubscriptionOut(**subsvc.subscription_to_dict(db, sub))


@router.post("/me/activate-stub", response_model=SubscriptionOut)
def activate_stub(body: ActivatePlanRequest, user: CurrentUser, db: DbSession) -> SubscriptionOut:
    """Stub-Aktivierung – klar als Simulation gekennzeichnet, keine echte Zahlung."""
    require_admin_role(user)
    wid = require_workshop_id(user)
    sub = subsvc.activate_plan_stub(
        db,
        wid,
        user,
        body.plan_code,
        acknowledge_stub_payment=body.acknowledge_stub_payment,
    )
    return SubscriptionOut(**subsvc.subscription_to_dict(db, sub))


@router.post("/me/cancel", response_model=SubscriptionOut)
def cancel(body: CancelSubscriptionRequest, user: CurrentUser, db: DbSession) -> SubscriptionOut:
    require_admin_role(user)
    wid = require_workshop_id(user)
    sub = subsvc.get_workshop_subscription(db, wid)
    if sub is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Kein Abo")
    sub = subsvc.cancel_subscription(
        db, sub, user, at_period_end=body.at_period_end, reason_de=body.reason_de
    )
    return SubscriptionOut(**subsvc.subscription_to_dict(db, sub))


@router.get("/me/entitlements/{feature}", response_model=EntitlementCheckOut)
def entitlement(
    feature: str,
    user: CurrentUser,
    db: DbSession,
    for_new_operation: bool = Query(True),
) -> EntitlementCheckOut:
    wid = require_workshop_id(user)
    return EntitlementCheckOut(**subsvc.check_entitlement(db, wid, feature, for_new_operation=for_new_operation))


@router.get("/me/devices", response_model=list[DeviceOut])
def list_devices(user: CurrentUser, db: DbSession) -> list[DeviceOut]:
    wid = require_workshop_id(user)
    rows = (
        db.query(DeviceBinding)
        .filter(DeviceBinding.workshop_id == wid)
        .order_by(DeviceBinding.created_at.desc())
        .all()
    )
    return [
        DeviceOut(
            id=d.id,
            workshop_id=d.workshop_id,
            device_name=d.device_name,
            device_fingerprint=d.device_fingerprint,
            platform=d.platform,
            last_seen_at=d.last_seen_at,
            revoked_at=d.revoked_at,
            is_example_data=d.is_example_data,
        )
        for d in rows
    ]


@router.post("/me/devices", response_model=DeviceOut)
def bind_device(body: DeviceBindRequest, user: CurrentUser, db: DbSession) -> DeviceOut:
    require_admin_role(user)
    wid = require_workshop_id(user)
    d = subsvc.bind_device(
        db,
        wid,
        user,
        device_name=body.device_name,
        device_fingerprint=body.device_fingerprint,
        platform=body.platform,
    )
    return DeviceOut(
        id=d.id,
        workshop_id=d.workshop_id,
        device_name=d.device_name,
        device_fingerprint=d.device_fingerprint,
        platform=d.platform,
        last_seen_at=d.last_seen_at,
        revoked_at=d.revoked_at,
        is_example_data=d.is_example_data,
    )


@router.post("/me/devices/{device_id}/revoke", response_model=DeviceOut)
def revoke_device(device_id: str, user: CurrentUser, db: DbSession) -> DeviceOut:
    require_admin_role(user)
    wid = require_workshop_id(user)
    d = db.get(DeviceBinding, device_id)
    from fastapi import HTTPException

    if d is None or d.workshop_id != wid:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")
    d = subsvc.revoke_device(db, d, user)
    return DeviceOut(
        id=d.id,
        workshop_id=d.workshop_id,
        device_name=d.device_name,
        device_fingerprint=d.device_fingerprint,
        platform=d.platform,
        last_seen_at=d.last_seen_at,
        revoked_at=d.revoked_at,
        is_example_data=d.is_example_data,
    )


@router.post("/me/critical-ops", response_model=CriticalOpOut)
def start_critical(body: CriticalOpStartRequest, user: CurrentUser, db: DbSession) -> CriticalOpOut:
    wid = require_workshop_id(user)
    lock = subsvc.start_critical_op(
        db,
        wid,
        user,
        operation_kind=body.operation_kind,
        resource_ref=body.resource_ref,
        message_de=body.message_de,
    )
    return CriticalOpOut(
        id=lock.id,
        workshop_id=lock.workshop_id,
        operation_kind=lock.operation_kind,
        resource_ref=lock.resource_ref,
        status=lock.status,
        started_at=lock.started_at,
        ended_at=lock.ended_at,
        message_de=lock.message_de,
    )


@router.post("/me/critical-ops/{op_id}/finish", response_model=CriticalOpOut)
def finish_critical(op_id: str, user: CurrentUser, db: DbSession) -> CriticalOpOut:
    wid = require_workshop_id(user)
    lock = db.get(CriticalOperationLock, op_id)
    from fastapi import HTTPException

    if lock is None or lock.workshop_id != wid:
        raise HTTPException(status_code=404, detail="Operation nicht gefunden")
    # Auch nach Abo-Ablauf: Finish erlaubt (kein Abrupt-Abbruch)
    lock = subsvc.finish_critical_op(db, lock, status_value="completed")
    return CriticalOpOut(
        id=lock.id,
        workshop_id=lock.workshop_id,
        operation_kind=lock.operation_kind,
        resource_ref=lock.resource_ref,
        status=lock.status,
        started_at=lock.started_at,
        ended_at=lock.ended_at,
        message_de=lock.message_de,
    )


@router.get("/me/critical-ops", response_model=list[CriticalOpOut])
def list_critical(user: CurrentUser, db: DbSession) -> list[CriticalOpOut]:
    wid = require_workshop_id(user)
    rows = (
        db.query(CriticalOperationLock)
        .filter(CriticalOperationLock.workshop_id == wid)
        .order_by(CriticalOperationLock.started_at.desc())
        .limit(50)
        .all()
    )
    return [
        CriticalOpOut(
            id=r.id,
            workshop_id=r.workshop_id,
            operation_kind=r.operation_kind,
            resource_ref=r.resource_ref,
            status=r.status,
            started_at=r.started_at,
            ended_at=r.ended_at,
            message_de=r.message_de,
        )
        for r in rows
    ]
