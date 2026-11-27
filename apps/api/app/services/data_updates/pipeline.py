"""Update-Pipeline: Fetch → Integrität → Staging → Risiko → Publish/Freigabe → Rollback."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.data_updates import UpdateChannel, UpdateChangelog, UpdateRun
from app.models.diagnostic_data import DiagDatasetVersion
from app.services.data_updates.fetcher import FetchError, fetch_channel_payload, parse_json_body
from app.services.data_updates.integrity import (
    extract_signature_header,
    sha256_hex,
    verify_hmac_sha256,
)
from app.services.data_updates.risk_policy import requires_manual_approval
from app.services.data_updates.scheduler import acquire_job_lock, release_job_lock
from app.services.data_updates.ssrf import SsrfBlocked
from app.services.diagnostic_data.import_pipeline import (
    apply_import_batch,
    preview_json_import,
    rollback_import_batch,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _changelog(db: Session, run: UpdateRun, channel_key: str, event: str, detail_de: str) -> None:
    db.add(
        UpdateChangelog(
            run_id=run.id,
            channel_key=channel_key,
            event=event,
            detail_de=detail_de,
        )
    )


def _finish(run: UpdateRun, status: str, *, error_de: str | None = None, summary: dict | None = None) -> None:
    run.status = status
    run.finished_at = _now()
    if error_de:
        run.error_de = error_de
    if summary is not None:
        run.summary_json = json.dumps(summary, ensure_ascii=False)


def _schedule_next(channel: UpdateChannel) -> None:
    channel.last_run_at = _now()
    hours = channel.interval_hours or get_settings().update_interval_hours or 24
    channel.next_run_at = _now() + timedelta(hours=hours)


def _active_published_version(db: Session) -> DiagDatasetVersion | None:
    return db.scalar(
        select(DiagDatasetVersion)
        .where(DiagDatasetVersion.status == "published")
        .order_by(DiagDatasetVersion.published_at.desc())
    )


def run_channel_update(
    db: Session,
    channel: UpdateChannel,
    *,
    trigger: str = "manual",
    force: bool = False,
    user_id: str | None = None,
    http_client: httpx.Client | None = None,
    skip_lock: bool = False,
) -> UpdateRun:
    """Führt einen Update-Lauf für einen Kanal aus."""
    holder = f"{trigger}-{uuid_short()}"
    if not skip_lock:
        if not acquire_job_lock(db, holder=holder):
            run = UpdateRun(
                channel_id=channel.id,
                trigger=trigger,
                status="failed",
                error_de="Paralleler Update-Job läuft bereits (Sperre).",
                finished_at=_now(),
                summary_json=json.dumps({"error": "locked"}),
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run

    run = UpdateRun(channel_id=channel.id, trigger=trigger, status="fetching")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        if not channel.enabled and not force:
            _finish(run, "failed", error_de="Kanal ist deaktiviert. Keine ungeprüften Auto-Downloads.")
            _changelog(db, run, channel.key, "failed", run.error_de or "")
            _schedule_next(channel)
            db.commit()
            db.refresh(run)
            return run

        if not channel.rights_verified and channel.fetch_mode == "https":
            _finish(
                run,
                "failed",
                error_de="Rechte für HTTPS-Quelle nicht verifiziert – Abruf gesperrt.",
            )
            _changelog(db, run, channel.key, "failed", run.error_de or "")
            _schedule_next(channel)
            db.commit()
            db.refresh(run)
            return run

        # --- Fetch ---
        try:
            result = fetch_channel_payload(
                fetch_mode=channel.fetch_mode,
                url=channel.url,
                etag=None if force else channel.last_etag,
                max_bytes=min(channel.max_bytes, get_settings().update_max_bytes),
                client=http_client,
            )
        except (FetchError, SsrfBlocked) as exc:
            msg = getattr(exc, "message_de", None) or str(exc)
            _finish(run, "failed", error_de=msg, summary={"phase": "fetch"})
            run.http_status = getattr(exc, "status_code", None)
            _changelog(db, run, channel.key, "failed", msg)
            _schedule_next(channel)
            db.commit()
            db.refresh(run)
            return run

        run.http_status = result.status_code
        run.etag = result.etag

        if result.not_modified:
            _finish(
                run,
                "skipped",
                summary={"reason": "not_modified", "etag": result.etag},
            )
            _changelog(db, run, channel.key, "skipped_same", "ETag unverändert – kein Download.")
            _schedule_next(channel)
            db.commit()
            db.refresh(run)
            return run

        body = result.body
        content_hash = sha256_hex(body)
        run.content_hash = content_hash

        if not force and channel.last_content_hash and channel.last_content_hash == content_hash:
            _finish(run, "skipped", summary={"reason": "same_hash", "hash": content_hash})
            channel.last_etag = result.etag
            _changelog(db, run, channel.key, "skipped_same", "Inhaltshash unverändert.")
            _schedule_next(channel)
            db.commit()
            db.refresh(run)
            return run

        # --- Signatur ---
        sig = extract_signature_header(result.headers)
        signature_ok: bool | None = None
        if channel.require_signature:
            secret = get_settings().update_hmac_demo_secret
            signature_ok = bool(sig) and verify_hmac_sha256(body=body, signature_hex=sig or "", secret=secret)
            run.signature_ok = signature_ok
            if not signature_ok:
                _finish(
                    run,
                    "failed",
                    error_de="Signaturprüfung fehlgeschlagen – Paket abgewiesen.",
                    summary={"phase": "signature"},
                )
                _changelog(db, run, channel.key, "failed", run.error_de or "")
                _schedule_next(channel)
                db.commit()
                db.refresh(run)
                return run
        elif sig:
            secret = get_settings().update_hmac_demo_secret
            signature_ok = verify_hmac_sha256(body=body, signature_hex=sig, secret=secret)
            run.signature_ok = signature_ok

        # --- Parse / Schema staging ---
        run.status = "staging"
        db.commit()

        try:
            payload = parse_json_body(body)
        except FetchError as exc:
            _finish(run, "failed", error_de=exc.message_de, summary={"phase": "parse"})
            _changelog(db, run, channel.key, "failed", exc.message_de)
            _schedule_next(channel)
            db.commit()
            db.refresh(run)
            return run

        detected_license = str(payload.get("license_name") or payload.get("license") or "")
        run.detected_license = detected_license or None
        license_changed = bool(
            detected_license and detected_license.strip().lower() != channel.expected_license.strip().lower()
        )
        run.license_changed = license_changed

        if license_changed:
            _changelog(
                db,
                run,
                channel.key,
                "license_changed",
                f"Erwartet '{channel.expected_license}', erkannt '{detected_license}'.",
            )

        # Import-Vorschau (Schema/Quarantäne) – staging
        preview = preview_json_import(
            db,
            payload,
            user_id=user_id,
            filename=f"update:{channel.key}",
        )
        run.import_batch_id = preview.batch_id
        run.staging_json = json.dumps(payload, ensure_ascii=False)
        run.version_label = str(payload.get("dataset_version_label") or "") or None
        run.summary_json = json.dumps(
            {
                "preview_status": preview.status,
                "can_apply": preview.can_apply,
                "conflicts": len(preview.conflicts),
                "quarantine": len(preview.quarantine),
                "message_de": preview.message_de,
            },
            ensure_ascii=False,
        )

        if preview.status in ("rejected", "quarantine") or not preview.can_apply:
            _finish(
                run,
                "failed",
                error_de=preview.message_de or "Schema-/Quarantäneprüfung fehlgeschlagen.",
                summary=json.loads(run.summary_json),
            )
            _changelog(db, run, channel.key, "failed", run.error_de or "")
            _schedule_next(channel)
            db.commit()
            db.refresh(run)
            return run

        _changelog(db, run, channel.key, "staged", "Paket in Staging validiert.")

        needs_manual, reason = requires_manual_approval(
            content_kind=channel.content_kind,
            auto_activate_allowed=channel.auto_activate_allowed,
            payload=payload,
            license_changed=license_changed,
            signature_required=channel.require_signature,
            signature_ok=run.signature_ok,
        )

        prev = _active_published_version(db)
        run.previous_dataset_version_id = prev.id if prev else None

        if needs_manual:
            run.status = "awaiting_approval"
            run.finished_at = None
            channel.last_etag = result.etag
            channel.last_content_hash = content_hash
            channel.last_version = run.version_label
            _changelog(db, run, channel.key, "awaiting_approval", reason)
            _schedule_next(channel)
            db.commit()
            db.refresh(run)
            return run

        # Auto-Publish (nur risikoarm)
        return _publish_run(db, run, channel, payload=payload, user_id=user_id, auto=True)

    finally:
        if not skip_lock:
            release_job_lock(db, holder=holder)


def _publish_run(
    db: Session,
    run: UpdateRun,
    channel: UpdateChannel,
    *,
    payload: dict[str, Any],
    user_id: str | None,
    auto: bool,
) -> UpdateRun:
    if not run.import_batch_id:
        # Preview erneut falls nötig
        preview = preview_json_import(db, payload, user_id=user_id, filename=f"update:{channel.key}")
        run.import_batch_id = preview.batch_id
        if not preview.can_apply:
            _finish(run, "failed", error_de=preview.message_de)
            db.commit()
            db.refresh(run)
            return run

    try:
        applied = apply_import_batch(db, run.import_batch_id, user_id=user_id)
    except ValueError as exc:
        _finish(run, "failed", error_de=str(exc))
        _changelog(db, run, channel.key, "failed", str(exc))
        db.commit()
        db.refresh(run)
        return run

    # Atomare Versionsmarkierung: vorher published → superseded
    if run.previous_dataset_version_id:
        old = db.get(DiagDatasetVersion, run.previous_dataset_version_id)
        if old and old.status == "published":
            old.status = "superseded"

    # Neue Version aus Apply (Label aus Payload)
    ver = db.scalar(
        select(DiagDatasetVersion).where(
            DiagDatasetVersion.version_label == (run.version_label or "")
        )
    )
    if ver:
        ver.status = "published"
        ver.published_at = _now()
        run.dataset_version_id = ver.id

    channel.last_etag = run.etag
    channel.last_content_hash = run.content_hash
    channel.last_version = run.version_label
    _finish(
        run,
        "published",
        summary={
            "auto": auto,
            "applied_count": applied.applied_count,
            "batch_id": applied.id,
            "version": run.version_label,
        },
    )
    _changelog(
        db,
        run,
        channel.key,
        "auto_published" if auto else "approved",
        f"Version {run.version_label} veröffentlicht ({applied.applied_count} Datensätze).",
    )
    _schedule_next(channel)
    db.commit()
    db.refresh(run)
    return run


def approve_run(db: Session, run_id: str, *, user_id: str) -> UpdateRun:
    run = db.get(UpdateRun, run_id)
    if run is None:
        raise ValueError("Update-Lauf nicht gefunden")
    if run.status != "awaiting_approval":
        raise ValueError(f"Lauf-Status '{run.status}' erlaubt keine Freigabe")
    if run.license_changed:
        # Freigabe trotzdem möglich – Admin bestätigt bewusst
        pass
    channel = db.get(UpdateChannel, run.channel_id)
    if channel is None:
        raise ValueError("Kanal nicht gefunden")
    if not run.staging_json:
        raise ValueError("Kein Staging-Payload")
    payload = json.loads(run.staging_json)
    run.approved_by = user_id
    run.approved_at = _now()
    holder = f"approve-{uuid_short()}"
    if not acquire_job_lock(db, holder=holder):
        raise ValueError("Paralleler Job – Freigabe später erneut versuchen")
    try:
        return _publish_run(db, run, channel, payload=payload, user_id=user_id, auto=False)
    finally:
        release_job_lock(db, holder=holder)


def reject_run(db: Session, run_id: str, *, user_id: str, reason_de: str | None = None) -> UpdateRun:
    run = db.get(UpdateRun, run_id)
    if run is None:
        raise ValueError("Update-Lauf nicht gefunden")
    if run.status != "awaiting_approval":
        raise ValueError(f"Lauf-Status '{run.status}' erlaubt keine Ablehnung")
    channel = db.get(UpdateChannel, run.channel_id)
    key = channel.key if channel else "?"
    _finish(
        run,
        "failed",
        error_de=reason_de or "Vom Admin abgelehnt.",
        summary={"rejected_by": user_id},
    )
    _changelog(db, run, key, "rejected", run.error_de or "")
    db.commit()
    db.refresh(run)
    return run


def rollback_run(db: Session, run_id: str, *, user_id: str | None = None) -> UpdateRun:
    run = db.get(UpdateRun, run_id)
    if run is None:
        raise ValueError("Update-Lauf nicht gefunden")
    if run.status not in ("published",):
        raise ValueError("Nur veröffentlichte Läufe können zurückgerollt werden")
    if not run.import_batch_id:
        raise ValueError("Kein Import-Batch für Rollback")

    channel = db.get(UpdateChannel, run.channel_id)
    key = channel.key if channel else "?"

    try:
        rollback_import_batch(db, run.import_batch_id)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    if run.dataset_version_id:
        ver = db.get(DiagDatasetVersion, run.dataset_version_id)
        if ver:
            ver.status = "rolled_back"

    if run.previous_dataset_version_id:
        prev = db.get(DiagDatasetVersion, run.previous_dataset_version_id)
        if prev and prev.status == "superseded":
            prev.status = "published"

    _finish(run, "rolled_back", summary={"rolled_back_by": user_id})
    _changelog(db, run, key, "rolled_back", "Atomarer Rollback der Veröffentlichung.")
    if channel:
        # Hash zurücksetzen, damit erneuter Fetch möglich ist
        channel.last_content_hash = None
    db.commit()
    db.refresh(run)
    return run


def run_due_channels(db: Session, *, trigger: str = "scheduler") -> list[UpdateRun]:
    """Führt fällige, freigeschaltete Kanäle aus (mit globaler Sperre)."""
    now = _now()
    channels = db.scalars(
        select(UpdateChannel).where(UpdateChannel.enabled.is_(True)).order_by(UpdateChannel.key)
    ).all()
    results: list[UpdateRun] = []
    holder = f"due-{uuid_short()}"
    if not acquire_job_lock(db, holder=holder):
        return results
    try:
        for ch in channels:
            if ch.next_run_at and ch.next_run_at > now:
                continue
            results.append(
                run_channel_update(db, ch, trigger=trigger, force=False, skip_lock=True)
            )
    finally:
        release_job_lock(db, holder=holder)
    return results


def uuid_short() -> str:
    import uuid

    return uuid.uuid4().hex[:10]
