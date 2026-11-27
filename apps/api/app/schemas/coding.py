"""Phase 12 – Codierung / Programmierung Schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PrerequisiteState(BaseModel):
    id: str
    label_de: str
    met: bool
    detail_de: str | None = None


class CodingOperationOut(BaseModel):
    code: str
    name_de: str
    category: str
    operation_type: str
    safety_class: str
    release_status: str
    enabled: bool
    write_allowed: bool
    flash_allowed: bool
    prerequisites: list[dict[str, Any]]
    confirmation_phrase: str | None = None
    timeout_seconds: int
    abort_strategy_de: str
    result_checks_de: list[str]
    ecu_roles: list[str]
    compatibility_de: str
    source_license_de: str
    notes_de: str
    blockers: list[str] = Field(default_factory=list)
    requires_j2534: bool = False
    requires_authorization: bool = True
    backup_supported: bool = False
    auto_retry_forbidden: bool = True
    data_source: str = "catalog"
    oem_procedure_invented: bool = False


class CodingCatalogOut(BaseModel):
    data_source: str
    disclaimer_de: str
    operations: list[CodingOperationOut]
    excluded: list[dict[str, Any]]
    live_execution_available: bool
    flash_available: bool
    hardware_live: bool
    auto_retry_forbidden: bool
    j2534_status: str
    dpdu_status: str


class CodingVehicleStateIn(BaseModel):
    """Simulierter Zustand für Gate-Prüfung – keine Live-Sensorik / kein Flash."""

    ignition_on: bool = True
    adapter_connected: bool = True
    battery_voltage_ok: bool = True
    battery_voltage_v: float | None = Field(default=12.6, ge=0, le=30)
    stable_connection: bool = True
    vin_ecu_match: bool = True
    oem_spec_present: bool = False
    authorization_present: bool = False
    recovery_plan: bool = False
    operator_confirm: bool = False
    expected_vin: str | None = None
    actual_vin: str | None = None
    expected_ecu_sw: str | None = None
    actual_ecu_sw: str | None = None


class CodingStartRequest(BaseModel):
    vehicle_id: str | None = None
    confirmation_phrase: str | None = None
    vehicle_state: CodingVehicleStateIn = Field(default_factory=CodingVehicleStateIn)
    scenario: Literal[
        "normal",
        "missing_prereq",
        "abort",
        "comm_loss",
        "voltage_drop",
        "wrong_vehicle",
    ] = "normal"
    acknowledge_disabled: bool = False
    acknowledge_no_flash: bool = False
    acknowledge_no_oem_write: bool = False


class CodingRunOut(BaseModel):
    id: str
    operation_code: str
    status: str
    scenario: str | None = None
    data_source: str
    prerequisites: list[PrerequisiteState]
    checks: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any]
    message_de: str | None = None
    abort_reason_de: str | None = None
    write_commands_sent: bool = False
    flash_commands_sent: bool = False
    auto_retry_attempted: bool = False
    started_at: datetime
    ended_at: datetime | None = None


class CodingAbortRequest(BaseModel):
    reason_de: str | None = Field(default="Bedienerabbruch", max_length=500)


class EcuIdentificationOut(BaseModel):
    data_source: str
    disclaimer_de: str
    vin: str | None = None
    ecu_id: str | None = None
    part_number: str | None = None
    software_version: str | None = None
    hardware_version: str | None = None
    coding_profile: str | None = None
    coding_profile_status: str  # unavailable | placeholder | simulated
    oem_fields_available: bool
    message_de: str


class CompatibilityCheckOut(BaseModel):
    data_source: str
    vin_match: bool
    ecu_match: bool
    software_compatible: bool | None
    signature_verified: bool | None
    voltage_ok: bool
    voltage_v: float | None
    stable_connection: bool
    authorization_ok: bool
    oem_spec_ok: bool
    recovery_plan_ok: bool
    overall_ok: bool
    blockers: list[str]
    message_de: str
    flash_blocked: bool = True
    write_blocked: bool = True


class InterfacePrepOut(BaseModel):
    j2534_status: str
    dpdu_status: str
    vendor_dll_present: bool
    notes_de: str
    docs: list[str]
