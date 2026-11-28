"""Pydantic-Schemas Phase 07 – Update-Kanäle und Admin-Dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class UpdateChannelOut(BaseModel):
    id: str
    key: str
    name: str
    fetch_mode: str
    url: str
    enabled: bool
    rights_verified: bool
    interval_hours: int
    expected_license: str
    source_key: str
    content_kind: str
    auto_activate_allowed: bool
    max_bytes: int
    require_signature: bool
    signature_key_id: str | None
    last_etag: str | None
    last_version: str | None
    last_content_hash: str | None
    last_run_at: datetime | None
    next_run_at: datetime | None
    notes_de: str | None


class UpdateChannelPatch(BaseModel):
    enabled: bool | None = None
    rights_verified: bool | None = None
    interval_hours: int | None = Field(default=None, ge=1, le=24 * 30)
    auto_activate_allowed: bool | None = None
    notes_de: str | None = None


class UpdateRunOut(BaseModel):
    id: str
    channel_id: str
    channel_key: str | None = None
    trigger: str
    status: str
    etag: str | None
    version_label: str | None
    content_hash: str | None
    signature_ok: bool | None
    license_changed: bool
    detected_license: str | None
    http_status: int | None
    error_de: str | None
    summary: dict[str, Any]
    import_batch_id: str | None
    dataset_version_id: str | None
    previous_dataset_version_id: str | None
    started_at: datetime
    finished_at: datetime | None
    approved_by: str | None
    approved_at: datetime | None


class UpdateChangelogOut(BaseModel):
    id: str
    run_id: str
    channel_key: str
    event: str
    detail_de: str
    created_at: datetime


class UpdateDashboardOut(BaseModel):
    scheduler_enabled: bool
    default_interval_hours: int
    lock_held: bool
    lock_by: str | None
    channels: list[UpdateChannelOut]
    recent_runs: list[UpdateRunOut]
    pending_approvals: list[UpdateRunOut]
    recent_changelog: list[UpdateChangelogOut]
    next_scheduled_at: datetime | None
    last_run_at: datetime | None
    disclaimer_de: str


class TriggerUpdateIn(BaseModel):
    force: bool = False


class RejectUpdateIn(BaseModel):
    reason_de: str | None = Field(default=None, max_length=2000)


class SsrfCheckIn(BaseModel):
    url: str


class SsrfCheckOut(BaseModel):
    ok: bool
    message_de: str
