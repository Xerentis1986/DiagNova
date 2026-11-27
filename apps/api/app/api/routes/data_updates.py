"""Phase 07 – Admin-API für Diagnosedaten-Updates."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, require_roles
from app.core.config import get_settings
from app.models import User
from app.models.data_updates import UpdateChannel, UpdateChangelog, UpdateJobLock, UpdateRun
from app.schemas.data_updates import (
    RejectUpdateIn,
    SsrfCheckIn,
    SsrfCheckOut,
    TriggerUpdateIn,
    UpdateChannelOut,
    UpdateChannelPatch,
    UpdateChangelogOut,
    UpdateDashboardOut,
    UpdateRunOut,
)
from app.services.audit import write_audit
from app.services.data_updates.pipeline import (
    approve_run,
    reject_run,
    rollback_run,
    run_channel_update,
    run_due_channels,
)
from app.services.data_updates.scheduler import LOCK_ID, ensure_lock_row
from app.services.data_updates.ssrf import SsrfBlocked, validate_https_url

router = APIRouter(prefix="/data-updates", tags=["data-updates"])
AdminOnly = Annotated[User, Depends(require_roles("admin"))]


def _channel_out(c: UpdateChannel) -> UpdateChannelOut:
    return UpdateChannelOut(
        id=c.id,
        key=c.key,
        name=c.name,
        fetch_mode=c.fetch_mode,
        url=c.url,
        enabled=c.enabled,
        rights_verified=c.rights_verified,
        interval_hours=c.interval_hours,
        expected_license=c.expected_license,
        source_key=c.source_key,
        content_kind=c.content_kind,
        auto_activate_allowed=c.auto_activate_allowed,
        max_bytes=c.max_bytes,
        require_signature=c.require_signature,
        signature_key_id=c.signature_key_id,
        last_etag=c.last_etag,
        last_version=c.last_version,
        last_content_hash=c.last_content_hash,
        last_run_at=c.last_run_at,
        next_run_at=c.next_run_at,
        notes_de=c.notes_de,
    )


def _run_out(db, r: UpdateRun) -> UpdateRunOut:
    ch = db.get(UpdateChannel, r.channel_id)
    return UpdateRunOut(
        id=r.id,
        channel_id=r.channel_id,
        channel_key=ch.key if ch else None,
        trigger=r.trigger,
        status=r.status,
        etag=r.etag,
        version_label=r.version_label,
        content_hash=r.content_hash,
        signature_ok=r.signature_ok,
        license_changed=r.license_changed,
        detected_license=r.detected_license,
        http_status=r.http_status,
        error_de=r.error_de,
        summary=json.loads(r.summary_json or "{}"),
        import_batch_id=r.import_batch_id,
        dataset_version_id=r.dataset_version_id,
        previous_dataset_version_id=r.previous_dataset_version_id,
        started_at=r.started_at,
        finished_at=r.finished_at,
        approved_by=r.approved_by,
        approved_at=r.approved_at,
    )


@router.get("/dashboard", response_model=UpdateDashboardOut)
def dashboard(user: AdminOnly, db: DbSession) -> UpdateDashboardOut:
    settings = get_settings()
    ensure_lock_row(db)
    lock = db.get(UpdateJobLock, LOCK_ID)
    channels = db.scalars(select(UpdateChannel).order_by(UpdateChannel.key)).all()
    runs = db.scalars(select(UpdateRun).order_by(UpdateRun.started_at.desc()).limit(30)).all()
    pending_rows = db.scalars(
        select(UpdateRun)
        .where(UpdateRun.status == "awaiting_approval")
        .order_by(UpdateRun.started_at.desc())
        .limit(50)
    ).all()
    logs = db.scalars(select(UpdateChangelog).order_by(UpdateChangelog.created_at.desc()).limit(40)).all()

    next_at = None
    last_at = None
    for c in channels:
        if c.next_run_at and (next_at is None or c.next_run_at < next_at):
            next_at = c.next_run_at
        if c.last_run_at and (last_at is None or c.last_run_at > last_at):
            last_at = c.last_run_at

    _ = user  # admin gate
    return UpdateDashboardOut(
        scheduler_enabled=settings.update_scheduler_enabled,
        default_interval_hours=settings.update_interval_hours,
        lock_held=bool(lock and lock.locked),
        lock_by=lock.locked_by if lock else None,
        channels=[_channel_out(c) for c in channels],
        recent_runs=[_run_out(db, r) for r in runs],
        pending_approvals=[_run_out(db, r) for r in pending_rows],
        recent_changelog=[
            UpdateChangelogOut(
                id=e.id,
                run_id=e.run_id,
                channel_key=e.channel_key,
                event=e.event,
                detail_de=e.detail_de,
                created_at=e.created_at,
            )
            for e in logs
        ],
        next_scheduled_at=next_at,
        last_run_at=last_at,
        disclaimer_de=(
            "Keine ungeprüften Auto-Downloads. HTTPS-Quellen nur nach Rechteprüfung. "
            "Keine erfundenen kommerziellen Feeds. Prozeduren/Adressen brauchen Admin-Freigabe."
        ),
    )


@router.get("/channels", response_model=list[UpdateChannelOut])
def list_channels(_user: AdminOnly, db: DbSession) -> list[UpdateChannelOut]:
    rows = db.scalars(select(UpdateChannel).order_by(UpdateChannel.key)).all()
    return [_channel_out(c) for c in rows]


@router.patch("/channels/{channel_key}", response_model=UpdateChannelOut)
def patch_channel(
    channel_key: str,
    body: UpdateChannelPatch,
    user: AdminOnly,
    db: DbSession,
) -> UpdateChannelOut:
    ch = db.scalar(select(UpdateChannel).where(UpdateChannel.key == channel_key))
    if ch is None:
        raise HTTPException(status_code=404, detail="Kanal nicht gefunden")

    if body.enabled is True and ch.fetch_mode == "https" and not (
        body.rights_verified if body.rights_verified is not None else ch.rights_verified
    ):
        raise HTTPException(
            status_code=400,
            detail="HTTPS-Kanal ohne Rechteprüfung (rights_verified) nicht aktivierbar.",
        )

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(ch, k, v)

    # Auto-Aktivierung nur für dtc_descriptive erzwingen
    if ch.auto_activate_allowed and ch.content_kind != "dtc_descriptive":
        ch.auto_activate_allowed = False

    write_audit(
        db,
        user_id=user.id,
        action="data_updates.channel.patch",
        resource=f"channel:{ch.key}",
        detail=json.dumps(data, ensure_ascii=False),
    )
    db.commit()
    db.refresh(ch)
    return _channel_out(ch)


@router.post("/channels/{channel_key}/run", response_model=UpdateRunOut)
def trigger_channel(
    channel_key: str,
    body: TriggerUpdateIn,
    user: AdminOnly,
    db: DbSession,
) -> UpdateRunOut:
    ch = db.scalar(select(UpdateChannel).where(UpdateChannel.key == channel_key))
    if ch is None:
        raise HTTPException(status_code=404, detail="Kanal nicht gefunden")
    # Manueller Lauf: force erlaubt deaktivierte Fixture-Kanäle für Admin-Tests
    run = run_channel_update(
        db,
        ch,
        trigger="manual",
        force=body.force,
        user_id=user.id,
    )
    write_audit(
        db,
        user_id=user.id,
        action="data_updates.run",
        resource=f"run:{run.id}",
        detail=run.status,
    )
    return _run_out(db, run)


@router.post("/run-due", response_model=list[UpdateRunOut])
def trigger_due(user: AdminOnly, db: DbSession) -> list[UpdateRunOut]:
    runs = run_due_channels(db, trigger="manual")
    write_audit(
        db,
        user_id=user.id,
        action="data_updates.run_due",
        resource="scheduler",
        detail=f"{len(runs)} Läufe",
    )
    return [_run_out(db, r) for r in runs]


@router.get("/runs", response_model=list[UpdateRunOut])
def list_runs(_user: AdminOnly, db: DbSession) -> list[UpdateRunOut]:
    rows = db.scalars(select(UpdateRun).order_by(UpdateRun.started_at.desc()).limit(50)).all()
    return [_run_out(db, r) for r in rows]


@router.get("/runs/{run_id}", response_model=UpdateRunOut)
def get_run(run_id: str, _user: AdminOnly, db: DbSession) -> UpdateRunOut:
    run = db.get(UpdateRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Lauf nicht gefunden")
    return _run_out(db, run)


@router.post("/runs/{run_id}/approve", response_model=UpdateRunOut)
def approve(run_id: str, user: AdminOnly, db: DbSession) -> UpdateRunOut:
    try:
        run = approve_run(db, run_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit(
        db,
        user_id=user.id,
        action="data_updates.approve",
        resource=f"run:{run_id}",
        detail=run.status,
    )
    return _run_out(db, run)


@router.post("/runs/{run_id}/reject", response_model=UpdateRunOut)
def reject(run_id: str, body: RejectUpdateIn, user: AdminOnly, db: DbSession) -> UpdateRunOut:
    try:
        run = reject_run(db, run_id, user_id=user.id, reason_de=body.reason_de)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit(
        db,
        user_id=user.id,
        action="data_updates.reject",
        resource=f"run:{run_id}",
        detail=run.status,
    )
    return _run_out(db, run)


@router.post("/runs/{run_id}/rollback", response_model=UpdateRunOut)
def rollback(run_id: str, user: AdminOnly, db: DbSession) -> UpdateRunOut:
    try:
        run = rollback_run(db, run_id, user_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit(
        db,
        user_id=user.id,
        action="data_updates.rollback",
        resource=f"run:{run_id}",
        detail=run.status,
    )
    return _run_out(db, run)


@router.post("/ssrf-check", response_model=SsrfCheckOut)
def ssrf_check(body: SsrfCheckIn, _user: AdminOnly) -> SsrfCheckOut:
    try:
        validate_https_url(body.url, allow_unresolved=True)
        return SsrfCheckOut(ok=True, message_de="URL besteht SSRF-Basisprüfung (HTTPS, kein Privat-Host).")
    except SsrfBlocked as exc:
        return SsrfCheckOut(ok=False, message_de=str(exc))


@router.get("/changelog", response_model=list[UpdateChangelogOut])
def changelog(_user: AdminOnly, db: DbSession) -> list[UpdateChangelogOut]:
    rows = db.scalars(select(UpdateChangelog).order_by(UpdateChangelog.created_at.desc()).limit(100)).all()
    return [
        UpdateChangelogOut(
            id=e.id,
            run_id=e.run_id,
            channel_key=e.channel_key,
            event=e.event,
            detail_de=e.detail_de,
            created_at=e.created_at,
        )
        for e in rows
    ]
