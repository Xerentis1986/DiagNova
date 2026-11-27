"""Schemas Phase 15 – Sicherheit / Datenschutz / Qualität."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ThreatNode(BaseModel):
    id: str
    surface: str
    threat: str
    mitigation_de: str
    status: Literal["mitigated", "partial", "open", "accepted"]
    severity: Literal["critical", "high", "medium", "low", "info"]


class SecurityFinding(BaseModel):
    id: str
    title_de: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    status: Literal["open", "mitigated", "accepted", "documented"]
    detail_de: str


class SecurityDashboardOut(BaseModel):
    version: str
    demo_mode: bool
    jwt_secret_insecure_default: bool
    cors_origins: list[str]
    rate_limits: dict[str, float | int]
    auth: dict[str, str | bool | int]
    rbac_roles: list[str]
    audit_redaction: bool
    security_headers: bool
    ssrf_protection_data_updates: bool
    connector_loopback_only: bool
    productive_auto_updates_blocked: bool
    monitoring_enabled: bool
    disclaimer_de: str
    threat_model: list[ThreatNode]
    findings: list[SecurityFinding]
    open_risks_de: list[str]


class PrivacyProcessOut(BaseModel):
    id: str
    title_de: str
    description_de: str
    api_hint: str | None = None
    legal_note_de: str


class PrivacyOverviewOut(BaseModel):
    disclaimer_de: str
    processes: list[PrivacyProcessOut]
    retention_note_de: str
    av_note_de: str


class AuditEntryOut(BaseModel):
    id: str
    action: str
    resource: str
    detail: str | None
    user_id: str | None
    workshop_id: str | None
    created_at: str | None


class AuditListOut(BaseModel):
    items: list[AuditEntryOut]
    note_de: str


class BackupOverviewOut(BaseModel):
    disclaimer_de: str
    recommended_steps_de: list[str]
    restore_steps_de: list[str]
    monitoring_hints_de: list[str]
    phase16_checklist_hint: str


class PasswordPolicyOut(BaseModel):
    min_length: int
    require_classes: int = Field(description="Mindestanzahl Zeichenklassen")
    note_de: str


class PasswordCheckRequest(BaseModel):
    password: str


class PasswordCheckResponse(BaseModel):
    ok: bool
    message_de: str | None = None
