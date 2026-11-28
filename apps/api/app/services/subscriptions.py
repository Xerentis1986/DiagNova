"""Phase 13 – Abo-/Lizenzlogik, Entitlements, kritische Ops ohne Abrupt-Abbruch."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.data.subscription_plans import (
    ACTIVE_LICENSE_STATUSES,
    BLOCKED_NEW_OP_STATUSES,
    get_plan,
    list_plans,
)
from app.models import User, Workshop
from app.models.subscriptions import (
    CriticalOperationLock,
    DeviceBinding,
    Subscription,
    TenantRegistration,
    WorkshopInvitation,
)
from app.services.audit import write_audit

PAYMENT_NOTE = (
    "SIMULATION / STUB – keine echte Zahlung. Kein Payment-Provider ohne ausdrückliche Zustimmung."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite liefert oft naive UTC-Zeiten – für Vergleiche normalisieren."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_ents(raw: str | None) -> list[str]:
    try:
        data = json.loads(raw or "[]")
        return [str(x) for x in data] if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def refresh_subscription_status(sub: Subscription) -> Subscription:
    """Zeitbasierte Statusübergänge (Trial/Periodenende) – ohne PSP."""
    now = _now()
    trial_ends = _aware(sub.trial_ends_at)
    period_end = _aware(sub.current_period_end)
    grace_until = _aware(sub.grace_until)
    if sub.status == "trialing" and trial_ends and trial_ends <= now:
        sub.status = "expired"
        sub.notes = (sub.notes or "") + " | Trial abgelaufen (lokal, Stub)"
    if sub.status == "active" and period_end and period_end <= now:
        if sub.cancel_at_period_end:
            sub.status = "canceled"
            sub.canceled_at = sub.canceled_at or now
        else:
            # Ohne echten PSP: Periode verlängert sich nicht automatisch → expired
            sub.status = "expired"
    if sub.status == "past_due" and grace_until and grace_until <= now:
        sub.status = "unpaid"
    return sub


def license_active(sub: Subscription | None) -> bool:
    if sub is None:
        return False
    refresh_subscription_status(sub)
    return sub.status in ACTIVE_LICENSE_STATUSES


def allows_new_operations(sub: Subscription | None) -> bool:
    if sub is None:
        return False
    refresh_subscription_status(sub)
    if sub.status in BLOCKED_NEW_OP_STATUSES:
        return False
    if sub.status == "past_due":
        # Grace: Lesen ok, neue kritische Starts eingeschränkt → hier False für Gate
        return False
    return sub.status in {"trialing", "active"}


def get_workshop_subscription(db: Session, workshop_id: str) -> Subscription | None:
    sub = (
        db.query(Subscription)
        .filter(Subscription.workshop_id == workshop_id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if sub:
        refresh_subscription_status(sub)
    return sub


def running_critical_ops(db: Session, workshop_id: str) -> list[CriticalOperationLock]:
    return (
        db.query(CriticalOperationLock)
        .filter(
            CriticalOperationLock.workshop_id == workshop_id,
            CriticalOperationLock.status == "running",
        )
        .order_by(CriticalOperationLock.started_at.desc())
        .all()
    )


def subscription_to_dict(db: Session, sub: Subscription) -> dict:
    refresh_subscription_status(sub)
    plan = get_plan(sub.plan_code)
    running = running_critical_ops(db, sub.workshop_id)
    active = license_active(sub)
    new_ops = allows_new_operations(sub)
    msg = "Lizenz aktiv (Simulation)."
    if sub.status == "trialing":
        msg = "Testzeitraum aktiv (Simulation)."
    elif sub.status == "past_due":
        msg = (
            "Zahlungsausfall (Stub). Laufende sicherheitskritische Operationen werden "
            "nicht abgebrochen; neue Starts gesperrt."
        )
    elif sub.status in BLOCKED_NEW_OP_STATUSES:
        if running:
            msg = (
                f"Abo {sub.status}: neue Operationen gesperrt. "
                f"{len(running)} laufende kritische Op(s) dürfen zu Ende laufen."
            )
        else:
            msg = f"Abo-Status {sub.status}: keine neuen Operationen."
    return {
        "id": sub.id,
        "workshop_id": sub.workshop_id,
        "plan_code": sub.plan_code,
        "plan_name_de": plan["name_de"] if plan else None,
        "status": sub.status,
        "payment_provider": sub.payment_provider,
        "external_ref": sub.external_ref,
        "trial_ends_at": sub.trial_ends_at,
        "current_period_start": sub.current_period_start,
        "current_period_end": sub.current_period_end,
        "cancel_at_period_end": sub.cancel_at_period_end,
        "canceled_at": sub.canceled_at,
        "grace_until": sub.grace_until,
        "entitlements": _parse_ents(sub.entitlements_json),
        "is_example_data": sub.is_example_data,
        "license_active": active,
        "allows_new_operations": new_ops,
        "has_running_critical_ops": bool(running),
        "message_de": msg,
        "payment_note_de": PAYMENT_NOTE,
    }


def ensure_demo_subscription(db: Session, workshop: Workshop) -> Subscription:
    existing = get_workshop_subscription(db, workshop.id)
    if existing:
        return existing
    plan = get_plan("pkw_pro")
    assert plan is not None
    now = _now()
    sub = Subscription(
        workshop_id=workshop.id,
        plan_code="pkw_pro",
        status="active",
        payment_provider="mock",
        external_ref=f"mock_sub_demo_{workshop.id[:8]}",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        entitlements_json=json.dumps(plan["entitlements"]),
        is_example_data=True,
        notes="Demo-Abo (Seed) – Stub, keine echte Zahlung.",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def start_trial(db: Session, workshop_id: str, user: User, plan_code: str = "pkw_trial") -> Subscription:
    plan = get_plan(plan_code)
    if plan is None or plan["release_status"] != "available" or plan["trial_days"] <= 0:
        raise HTTPException(status_code=400, detail="Kein gültiger Testzeitraum-Tarif")
    current = get_workshop_subscription(db, workshop_id)
    if current and current.status in ACTIVE_LICENSE_STATUSES:
        raise HTTPException(status_code=409, detail="Bereits aktives Abo/Trial vorhanden")
    now = _now()
    sub = Subscription(
        workshop_id=workshop_id,
        plan_code=plan_code,
        status="trialing",
        payment_provider="mock",
        external_ref=f"mock_trial_{secrets.token_hex(6)}",
        trial_ends_at=now + timedelta(days=int(plan["trial_days"])),
        current_period_start=now,
        current_period_end=now + timedelta(days=int(plan["trial_days"])),
        entitlements_json=json.dumps(plan["entitlements"]),
        is_example_data=True,
        notes="Testzeitraum – Stub, keine Zahlung.",
    )
    db.add(sub)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=workshop_id,
        action="subscription_trial_start",
        resource=f"subscription:{plan_code}",
        detail="stub",
    )
    db.commit()
    db.refresh(sub)
    return sub


def activate_plan_stub(
    db: Session,
    workshop_id: str,
    user: User,
    plan_code: str,
    *,
    acknowledge_stub_payment: bool,
) -> Subscription:
    if not acknowledge_stub_payment:
        raise HTTPException(
            status_code=400,
            detail="Stub-Zahlung muss bestätigt werden (acknowledge_stub_payment). Kein echter PSP.",
        )
    plan = get_plan(plan_code)
    if plan is None or plan["release_status"] != "available":
        raise HTTPException(status_code=400, detail="Tarif nicht buchbar (planned oder unbekannt)")
    if plan["trial_days"] > 0 and plan_code == "pkw_trial":
        raise HTTPException(status_code=400, detail="Bitte start-trial für Testzeitraum nutzen")
    now = _now()
    # Bestehendes ersetzen / neu
    sub = Subscription(
        workshop_id=workshop_id,
        plan_code=plan_code,
        status="active",
        payment_provider="mock",
        external_ref=f"mock_sub_{secrets.token_hex(8)}",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        entitlements_json=json.dumps(plan["entitlements"]),
        is_example_data=True,
        notes="Stub-Aktivierung – SIMULATION, keine echte Abbuchung.",
    )
    db.add(sub)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=workshop_id,
        action="subscription_activate_stub",
        resource=f"subscription:{plan_code}",
        detail="mock_payment_stub",
    )
    db.commit()
    db.refresh(sub)
    return sub


def cancel_subscription(
    db: Session,
    sub: Subscription,
    user: User,
    *,
    at_period_end: bool,
    reason_de: str | None,
) -> Subscription:
    refresh_subscription_status(sub)
    if sub.status in {"canceled", "expired"}:
        raise HTTPException(status_code=409, detail="Abo bereits beendet")
    now = _now()
    if at_period_end and _aware(sub.current_period_end) and _aware(sub.current_period_end) > now:
        sub.cancel_at_period_end = True
        sub.notes = (sub.notes or "") + f" | Kündigung zum Periodenende: {reason_de or ''}"
    else:
        running = running_critical_ops(db, sub.workshop_id)
        sub.status = "canceled"
        sub.canceled_at = now
        sub.cancel_at_period_end = False
        if running:
            sub.notes = (
                (sub.notes or "")
                + f" | Sofortkündigung Stub; {len(running)} kritische Op(s) laufen weiter"
            )
        else:
            sub.notes = (sub.notes or "") + f" | Sofortkündigung Stub: {reason_de or ''}"
    write_audit(
        db,
        user_id=user.id,
        workshop_id=sub.workshop_id,
        action="subscription_cancel",
        resource=f"subscription:{sub.id}",
        detail=reason_de or ("at_period_end" if at_period_end else "immediate"),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def check_entitlement(
    db: Session,
    workshop_id: str,
    feature: str,
    *,
    for_new_operation: bool = True,
) -> dict:
    sub = get_workshop_subscription(db, workshop_id)
    running = running_critical_ops(db, workshop_id)
    if sub is None:
        return {
            "feature": feature,
            "allowed": False,
            "subscription_status": None,
            "reason_de": "Kein Abo für diesen Mandanten.",
            "running_critical_ops": len(running),
            "interrupt_forbidden": bool(running),
        }
    refresh_subscription_status(sub)
    ents = _parse_ents(sub.entitlements_json)
    if feature not in ents:
        return {
            "feature": feature,
            "allowed": False,
            "subscription_status": sub.status,
            "reason_de": f"Feature „{feature}“ nicht im Tarif {sub.plan_code}.",
            "running_critical_ops": len(running),
            "interrupt_forbidden": bool(running),
        }
    if for_new_operation and not allows_new_operations(sub):
        return {
            "feature": feature,
            "allowed": False,
            "subscription_status": sub.status,
            "reason_de": (
                f"Neue Operationen bei Status „{sub.status}“ gesperrt. "
                "Laufende kritische Ops werden nicht abgebrochen."
            ),
            "running_critical_ops": len(running),
            "interrupt_forbidden": True if running else False,
        }
    # Bestehende Ops / Lesezugriff bei past_due: erlaubt wenn Feature im Tarif
    if not for_new_operation and sub.status in ACTIVE_LICENSE_STATUSES | {"canceled", "expired"}:
        if running and sub.status in BLOCKED_NEW_OP_STATUSES | {"past_due"}:
            return {
                "feature": feature,
                "allowed": True,
                "subscription_status": sub.status,
                "reason_de": "Laufende kritische Operation darf fortgesetzt werden (kein Abrupt-Abbruch).",
                "running_critical_ops": len(running),
                "interrupt_forbidden": True,
            }
    if license_active(sub) or (not for_new_operation and running):
        return {
            "feature": feature,
            "allowed": True,
            "subscription_status": sub.status,
            "reason_de": "Berechtigung erteilt (serverseitig).",
            "running_critical_ops": len(running),
            "interrupt_forbidden": bool(running) and sub.status not in {"trialing", "active"},
        }
    return {
        "feature": feature,
        "allowed": False,
        "subscription_status": sub.status,
        "reason_de": f"Lizenzstatus „{sub.status}“ erlaubt Feature nicht.",
        "running_critical_ops": len(running),
        "interrupt_forbidden": bool(running),
    }


def start_critical_op(
    db: Session,
    workshop_id: str,
    user: User,
    *,
    operation_kind: str,
    resource_ref: str,
    message_de: str | None,
) -> CriticalOperationLock:
    gate = check_entitlement(db, workshop_id, "coding.simulated", for_new_operation=True)
    # Generischer Gate: neue kritische Ops brauchen aktives Abo
    sub = get_workshop_subscription(db, workshop_id)
    if not allows_new_operations(sub):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=gate["reason_de"] if not gate["allowed"] else "Abo erlaubt keine neuen Operationen",
        )
    lock = CriticalOperationLock(
        workshop_id=workshop_id,
        user_id=user.id,
        operation_kind=operation_kind,
        resource_ref=resource_ref,
        status="running",
        message_de=message_de or "Sicherheitskritische Operation läuft (Simulation).",
    )
    db.add(lock)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=workshop_id,
        action="critical_op_start",
        resource=f"{operation_kind}:{resource_ref}",
        detail="phase13",
    )
    db.commit()
    db.refresh(lock)
    return lock


def finish_critical_op(
    db: Session,
    lock: CriticalOperationLock,
    *,
    status_value: str = "completed",
    message_de: str | None = None,
) -> CriticalOperationLock:
    if lock.status != "running":
        raise HTTPException(status_code=409, detail="Operation nicht laufend")
    lock.status = status_value
    lock.ended_at = _now()
    if message_de:
        lock.message_de = message_de
    db.add(lock)
    db.commit()
    db.refresh(lock)
    return lock


def bind_device(
    db: Session,
    workshop_id: str,
    user: User,
    *,
    device_name: str,
    device_fingerprint: str,
    platform: str,
) -> DeviceBinding:
    sub = get_workshop_subscription(db, workshop_id)
    if not license_active(sub):
        raise HTTPException(status_code=402, detail="Keine aktive Lizenz für Gerätebindung")
    plan = get_plan(sub.plan_code) if sub else None
    max_devices = int(plan["max_devices"]) if plan else 1
    active = (
        db.query(DeviceBinding)
        .filter(
            DeviceBinding.workshop_id == workshop_id,
            DeviceBinding.revoked_at.is_(None),
        )
        .all()
    )
    existing = next((d for d in active if d.device_fingerprint == device_fingerprint), None)
    if existing:
        existing.last_seen_at = _now()
        existing.device_name = device_name.strip()
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    if len(active) >= max_devices:
        raise HTTPException(
            status_code=409,
            detail=f"Geräte-Limit erreicht ({max_devices}). Bitte Gerät freigeben.",
        )
    device = DeviceBinding(
        workshop_id=workshop_id,
        subscription_id=sub.id if sub else None,
        device_name=device_name.strip(),
        device_fingerprint=device_fingerprint.strip(),
        platform=platform.strip() or "windows",
        last_seen_at=_now(),
        is_example_data=True,
    )
    db.add(device)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=workshop_id,
        action="device_bind",
        resource=f"device:{device_fingerprint[:16]}",
    )
    db.commit()
    db.refresh(device)
    return device


def revoke_device(db: Session, device: DeviceBinding, user: User) -> DeviceBinding:
    device.revoked_at = _now()
    db.add(device)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=device.workshop_id,
        action="device_revoke",
        resource=f"device:{device.id}",
    )
    db.commit()
    db.refresh(device)
    return device


def create_invitation(
    db: Session,
    workshop_id: str,
    user: User,
    *,
    email: str,
    role: str,
) -> WorkshopInvitation:
    email_n = email.lower().strip()
    existing_user = db.query(User).filter(User.email == email_n).first()
    if existing_user and existing_user.workshop_id == workshop_id:
        raise HTTPException(status_code=409, detail="Benutzer bereits Mitglied")
    pending = (
        db.query(WorkshopInvitation)
        .filter(
            WorkshopInvitation.workshop_id == workshop_id,
            WorkshopInvitation.email == email_n,
            WorkshopInvitation.status == "pending",
        )
        .first()
    )
    if pending:
        raise HTTPException(status_code=409, detail="Offene Einladung existiert bereits")
    inv = WorkshopInvitation(
        workshop_id=workshop_id,
        email=email_n,
        role=role,
        token=secrets.token_urlsafe(24),
        invited_by_user_id=user.id,
        status="pending",
        expires_at=_now() + timedelta(days=7),
    )
    db.add(inv)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=workshop_id,
        action="invitation_create",
        resource=f"invite:{email_n}",
        detail=role,
    )
    db.commit()
    db.refresh(inv)
    return inv


def accept_invitation(
    db: Session,
    *,
    token: str,
    full_name: str,
    password: str,
) -> tuple[User, WorkshopInvitation]:
    inv = db.query(WorkshopInvitation).filter(WorkshopInvitation.token == token).first()
    if inv is None:
        raise HTTPException(status_code=404, detail="Einladung nicht gefunden")
    if inv.status != "pending":
        raise HTTPException(status_code=409, detail=f"Einladung Status: {inv.status}")
    if _aware(inv.expires_at) and _aware(inv.expires_at) <= _now():
        inv.status = "expired"
        db.add(inv)
        db.commit()
        raise HTTPException(status_code=410, detail="Einladung abgelaufen")
    email = inv.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            full_name=full_name.strip(),
            hashed_password=hash_password(password),
            role=inv.role,
            workshop_id=inv.workshop_id,
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        if user.workshop_id and user.workshop_id != inv.workshop_id:
            raise HTTPException(status_code=409, detail="Benutzer gehört bereits zu anderem Mandanten")
        user.workshop_id = inv.workshop_id
        user.role = inv.role
        user.full_name = full_name.strip()
        user.hashed_password = hash_password(password)
        user.is_active = True
        db.add(user)
    inv.status = "accepted"
    inv.accepted_at = _now()
    inv.accepted_user_id = user.id
    db.add(inv)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=inv.workshop_id,
        action="invitation_accept",
        resource=f"invite:{inv.id}",
    )
    db.commit()
    db.refresh(user)
    db.refresh(inv)
    return user, inv


def register_tenant(
    db: Session,
    *,
    workshop_name: str,
    admin_email: str,
    admin_full_name: str,
    password: str,
    country: str,
    plan_code: str,
    acknowledge_demo: bool,
) -> dict:
    if not acknowledge_demo:
        raise HTTPException(
            status_code=400,
            detail="Demo-Registrierung muss bestätigt werden (acknowledge_demo).",
        )
    email = admin_email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="E-Mail bereits registriert")
    plan = get_plan(plan_code) or get_plan("pkw_trial")
    assert plan is not None
    workshop = Workshop(
        name=workshop_name.strip(),
        legal_name=workshop_name.strip(),
        email=email,
        country=country.upper()[:2],
        retention_days=365,
        notes="Selbstregistrierung Phase 13 – Beispieldaten/Demo.",
        is_example_data=True,
    )
    db.add(workshop)
    db.flush()
    user = User(
        email=email,
        full_name=admin_full_name.strip(),
        hashed_password=hash_password(password),
        role="admin",
        workshop_id=workshop.id,
        is_active=True,
        is_platform_admin=False,
    )
    db.add(user)
    db.flush()
    now = _now()
    if plan["trial_days"] > 0:
        status_val = "trialing"
        trial_end = now + timedelta(days=int(plan["trial_days"]))
        period_end = trial_end
    else:
        status_val = "active"
        trial_end = None
        period_end = now + timedelta(days=30)
    sub = Subscription(
        workshop_id=workshop.id,
        plan_code=plan["code"],
        status=status_val,
        payment_provider="mock",
        external_ref=f"mock_reg_{secrets.token_hex(6)}",
        trial_ends_at=trial_end,
        current_period_start=now,
        current_period_end=period_end,
        entitlements_json=json.dumps(plan["entitlements"]),
        is_example_data=True,
        notes="Registrierungs-Abo Stub.",
    )
    db.add(sub)
    db.flush()
    reg = TenantRegistration(
        workshop_id=workshop.id,
        admin_user_id=user.id,
        plan_code=plan["code"],
        is_example_data=True,
    )
    db.add(reg)
    write_audit(
        db,
        user_id=user.id,
        workshop_id=workshop.id,
        action="tenant_register",
        resource=f"workshop:{workshop.id}",
        detail=plan["code"],
    )
    db.commit()
    return {
        "workshop_id": workshop.id,
        "user_id": user.id,
        "subscription_id": sub.id,
        "message_de": (
            f"Mandant „{workshop.name}“ angelegt (Demo). Abo {plan['code']} ({status_val}). "
            + PAYMENT_NOTE
        ),
        "is_example_data": True,
    }


def plans_public() -> list[dict]:
    return [
        {
            **p,
            "payment_note_de": PAYMENT_NOTE,
        }
        for p in list_plans(include_planned=True)
    ]
