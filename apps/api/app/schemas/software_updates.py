"""Pydantic-Schemas Phase 14 Software-Updates."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SoftwareComponentOut(BaseModel):
    key: str
    label_de: str
    current_version: str
    previous_version: str | None = None
    channel_key: str
    health_status: str
    last_healthcheck_at: datetime | None = None
    last_error_de: str | None = None
    updated_at: datetime | None = None


class SoftwareChannelOut(BaseModel):
    id: str
    key: str
    name: str
    channel_type: str
    fetch_mode: str
    enabled: bool
    auto_install_allowed: bool
    require_signature: bool
    require_signing_cert: bool
    notes_de: str | None = None


class SoftwarePackageOut(BaseModel):
    id: str
    channel_id: str
    channel_key: str | None = None
    component: str
    version: str
    package_filename: str
    content_sha256: str
    signature_ok: bool | None = None
    release_notes_de: str
    migration_plan: list[Any] = Field(default_factory=list)
    status: str
    error_de: str | None = None
    created_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None


class SoftwareRunOut(BaseModel):
    id: str
    package_id: str
    component: str
    action: str
    status: str
    from_version: str | None = None
    to_version: str | None = None
    healthcheck_ok: bool | None = None
    busy_reason_de: str | None = None
    error_de: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    triggered_by: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class SoftwareEventOut(BaseModel):
    id: str
    package_id: str | None = None
    run_id: str | None = None
    component: str | None = None
    event: str
    detail_de: str
    created_at: datetime | None = None


class CompatibilityRuleOut(BaseModel):
    id: str
    component: str
    version: str
    requires: dict[str, str]
    notes_de: str | None = None


class BusyGateOut(BaseModel):
    allowed: bool
    reason_de: str | None = None
    blockers: list[dict[str, Any]] = Field(default_factory=list)


class IngestPackageIn(BaseModel):
    channel_key: str = "stable-fixture"
    fixture_name: str
    claimed_sha256: str | None = None
    signature_hex: str | None = None
    tamper: bool = False


class RejectPackageIn(BaseModel):
    reason_de: str = "Admin abgelehnt"


class ApproveInstallIn(BaseModel):
    force_healthcheck_fail: bool = False


class AbortRunIn(BaseModel):
    reason_de: str = "Abbruch durch Admin"


class CompatibilityCheckIn(BaseModel):
    component: str
    version: str
    proposed_versions: dict[str, str] | None = None


class CompatibilityCheckOut(BaseModel):
    compatible: bool
    warnings_de: list[str] = Field(default_factory=list)
    violations: list[dict[str, Any]] = Field(default_factory=list)
    installed: dict[str, str] = Field(default_factory=dict)
    rules_checked: list[str] = Field(default_factory=list)


class MigrationPlanOut(BaseModel):
    revision: str
    from_revision: str
    backup_required: bool
    backup_steps_de: list[str]
    restore_steps_de: list[str]
    notes_de: str | None = None


class SoftwareUpdatesDashboardOut(BaseModel):
    disclaimer_de: str
    signing_cert_configured: bool
    auto_install_enabled: bool
    productive_auto_updates_blocked: bool
    components: list[SoftwareComponentOut]
    channels: list[SoftwareChannelOut]
    pending_packages: list[SoftwarePackageOut]
    recent_packages: list[SoftwarePackageOut]
    recent_runs: list[SoftwareRunOut]
    recent_events: list[SoftwareEventOut]
    compatibility_rules: list[CompatibilityRuleOut]
    migration_plan: list[MigrationPlanOut]
    busy: BusyGateOut
    data_updates_note_de: str = (
        "Diagnosedaten-Updates bleiben unter /api/data-updates und /data-updates – getrennt."
    )
