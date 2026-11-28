"""Phase 18 – Chiptuning-Architektur Schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PrerequisiteState(BaseModel):
    id: str
    label_de: str
    met: bool
    detail_de: str | None = None


class TuningOperationOut(BaseModel):
    code: str
    name_de: str
    category: str
    operation_type: str
    safety_class: str
    release_status: str
    enabled: bool
    write_allowed: bool
    map_change_allowed: bool = False
    flash_allowed: bool = False
    tuning_activation_allowed: bool = False
    prerequisites: list[dict[str, Any]]
    confirmation_phrase: str | None = None
    timeout_seconds: int
    abort_strategy_de: str
    result_checks_de: list[str]
    notes_de: str
    blockers: list[str] = Field(default_factory=list)
    requires_legal_approval: bool = True
    requires_technical_review: bool = True
    auto_retry_forbidden: bool = True
    productive_activation_locked: bool = True
    data_source: str = "catalog"
    oem_maps_invented: bool = False


class TuningCatalogOut(BaseModel):
    data_source: str
    module_status: str
    disclaimer_de: str
    operations: list[TuningOperationOut]
    excluded: list[dict[str, Any]]
    live_execution_available: bool
    map_change_available: bool
    flash_available: bool
    tuning_activation_available: bool
    hardware_live: bool
    auto_retry_forbidden: bool
    productive_activation_locked: bool
    legal_gates_required: bool


class TuningGateStateIn(BaseModel):
    """Simulierter Zustand für rechtliche/technische Gates – kein Live-Flash."""

    operator_confirm: bool = False
    legal_gate_ack: bool = False
    no_emission_defeat_ack: bool = False
    no_map_change_ack: bool = False
    legal_approval_present: bool = False
    technical_review_present: bool = False
    recovery_plan: bool = False
    oem_baseline_documented: bool = False
    hardware_suitable: bool = False
    expected_vin: str | None = None
    actual_vin: str | None = None
    expected_ecu_sw: str | None = None
    actual_ecu_sw: str | None = None


class LegalGateCheckOut(BaseModel):
    data_source: str = "simulated"
    legal_approval_ok: bool
    technical_review_ok: bool
    recovery_plan_ok: bool
    emission_policy_ok: bool
    map_change_blocked: bool = True
    flash_blocked: bool = True
    tuning_activation_blocked: bool = True
    vin_match: bool | None = None
    software_compatible: bool | None = None
    overall_ok: bool
    blockers: list[str] = Field(default_factory=list)
    message_de: str
    productive_activation_locked: bool = True


class TuningBaselineOut(BaseModel):
    id: str
    code: str
    ecu_role: str
    software_version: str
    part_number: str | None = None
    checksum_ref: str | None = None
    source_de: str
    authorization_status: str
    compatible_notes_de: str | None = None
    data_source: str
    created_at: datetime


class TuningBaselineCreate(BaseModel):
    code: str = Field(min_length=3, max_length=128)
    ecu_role: str = Field(default="engine", max_length=64)
    software_version: str = Field(min_length=1, max_length=64)
    part_number: str | None = Field(default=None, max_length=128)
    checksum_ref: str | None = Field(default=None, max_length=256)
    source_de: str = Field(min_length=3, max_length=2000)
    compatible_notes_de: str | None = Field(default=None, max_length=2000)
    acknowledge_no_map_binary: bool = False
    acknowledge_demo_only: bool = False


class TuningApprovalOut(BaseModel):
    id: str
    baseline_id: str | None = None
    vehicle_id: str | None = None
    doc_type: str
    title_de: str
    reference_code: str | None = None
    issuer_de: str | None = None
    status: str
    notes_de: str | None = None
    data_source: str
    created_at: datetime


class TuningApprovalCreate(BaseModel):
    baseline_id: str | None = None
    vehicle_id: str | None = None
    doc_type: Literal["type_approval", "workshop_ack", "technical_review", "other"] = "workshop_ack"
    title_de: str = Field(min_length=3, max_length=256)
    reference_code: str | None = Field(default=None, max_length=128)
    issuer_de: str | None = Field(default=None, max_length=256)
    notes_de: str | None = Field(default=None, max_length=2000)
    acknowledge_not_legal_advice: bool = False
    acknowledge_no_activation: bool = False


class TuningHistoryOut(BaseModel):
    id: str
    vehicle_id: str | None = None
    baseline_id: str | None = None
    ecu_role: str
    software_version: str
    event_type: str
    message_de: str | None = None
    data_source: str
    created_at: datetime


class TuningStartRequest(BaseModel):
    vehicle_id: str | None = None
    baseline_id: str | None = None
    confirmation_phrase: str | None = None
    gate_state: TuningGateStateIn = Field(default_factory=TuningGateStateIn)
    scenario: Literal[
        "normal",
        "missing_prereq",
        "missing_legal",
        "abort",
        "comm_loss",
        "wrong_vehicle",
    ] = "normal"
    acknowledge_disabled: bool = False
    acknowledge_no_map_change: bool = False
    acknowledge_no_emission_defeat: bool = False
    acknowledge_activation_locked: bool = False


class TuningRunOut(BaseModel):
    id: str
    operation_code: str
    status: str
    scenario: str | None = None
    data_source: str
    prerequisites: list[PrerequisiteState]
    gates: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any]
    message_de: str | None = None
    abort_reason_de: str | None = None
    map_commands_sent: bool = False
    flash_commands_sent: bool = False
    tuning_activated: bool = False
    auto_retry_attempted: bool = False
    started_at: datetime
    ended_at: datetime | None = None


class TuningAbortRequest(BaseModel):
    reason_de: str | None = Field(default="Bedienerabbruch", max_length=500)


class TuningModuleStatusOut(BaseModel):
    module: str = "chiptuning"
    phase: int = 18
    status: str = "planned_disabled"
    productive_activation_locked: bool = True
    map_change_available: bool = False
    flash_available: bool = False
    emission_defeat_excluded: bool = True
    disclaimer_de: str
