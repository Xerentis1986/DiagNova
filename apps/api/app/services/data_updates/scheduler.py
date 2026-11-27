"""Job-Sperre und optionaler Hintergrund-Scheduler."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.data_updates import UpdateJobLock

logger = logging.getLogger("diagnova.updates")

LOCK_ID = "global"
LOCK_TTL_SEC = 600

_scheduler_thread: threading.Thread | None = None
_scheduler_stop = threading.Event()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_lock_row(db: Session) -> UpdateJobLock:
    row = db.get(UpdateJobLock, LOCK_ID)
    if row is None:
        row = UpdateJobLock(id=LOCK_ID, locked=False)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _aware(dt: datetime | None) -> datetime | None:
    """SQLite liefert oft naive UTC – für Vergleiche normalisieren."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def acquire_job_lock(db: Session, *, holder: str | None = None) -> bool:
    """Atomare Sperre gegen parallele Jobs. True = erworben."""
    ensure_lock_row(db)
    row = db.get(UpdateJobLock, LOCK_ID)
    assert row is not None
    now = _now()
    expires = _aware(row.expires_at)
    if row.locked and expires and expires > now:
        return False
    # abgelaufene Sperre übernehmen
    row.locked = True
    row.locked_by = holder or f"job-{uuid.uuid4().hex[:8]}"
    row.locked_at = now
    row.expires_at = now + timedelta(seconds=LOCK_TTL_SEC)
    db.commit()
    return True


def release_job_lock(db: Session, *, holder: str | None = None) -> None:
    row = db.get(UpdateJobLock, LOCK_ID)
    if row is None:
        return
    if holder and row.locked_by and row.locked_by != holder:
        return
    row.locked = False
    row.locked_by = None
    row.locked_at = None
    row.expires_at = None
    db.commit()


def start_background_scheduler(session_factory: Callable[[], Session]) -> None:
    """Startet Daemon-Thread wenn UPDATE_SCHEDULER_ENABLED=true."""
    global _scheduler_thread
    settings = get_settings()
    if not settings.update_scheduler_enabled:
        logger.info("Update-Scheduler deaktiviert (UPDATE_SCHEDULER_ENABLED=false).")
        return
    if _scheduler_thread and _scheduler_thread.is_alive():
        return

    _scheduler_stop.clear()

    def _loop() -> None:
        from app.services.data_updates.pipeline import run_due_channels

        poll = max(10, settings.update_scheduler_poll_sec)
        logger.info("Update-Scheduler gestartet (Poll %ss, Intervall %sh).", poll, settings.update_interval_hours)
        while not _scheduler_stop.is_set():
            db = session_factory()
            try:
                run_due_channels(db, trigger="scheduler")
            except Exception:  # noqa: BLE001 – Scheduler darf nicht abstürzen
                logger.exception("Scheduler-Lauf fehlgeschlagen")
            finally:
                db.close()
            _scheduler_stop.wait(poll)

    _scheduler_thread = threading.Thread(target=_loop, name="diagnova-update-scheduler", daemon=True)
    _scheduler_thread.start()


def stop_background_scheduler() -> None:
    _scheduler_stop.set()
    # kurzes Warten ohne Blockieren der Shutdown-Pipeline
    time.sleep(0.05)
