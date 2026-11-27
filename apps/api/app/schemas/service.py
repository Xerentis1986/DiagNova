"""Phase 11 – Service & Guided Diagnosis Schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class PrerequisiteState(BaseModel):
    id: str
    label_de: str
    met: bool
    detail_de: str | None = None


class ServiceProcedureOut(BaseModel):
    code: str
    name_de: str
    category: str
    safety_class: str
    release_status: str
    enabled: bool
    write_allowed: bool
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
    data_source: str = "catalog"
    oem_procedure_invented: bool = False


class ServiceCatalogOut(BaseModel):
    data_source: str
    disclaimer_de: str
    procedures: list[ServiceProcedureOut]
    excluded: list[dict[str, Any]]
    live_execution_available: bool
    hardware_live: bool


class VehicleStateIn(BaseModel):
    """Simulierter Fahrzeugzustand für Gate-Prüfung – keine Live-Sensorik."""

    ignition_on: bool = True
    adapter_connected: bool = True
    battery_voltage_ok: bool = True
    operator_confirm: bool = False
    oem_spec_present: bool = False
    safe_work_area: bool = True
    exhaust_safe: bool = True


class ServiceStartRequest(BaseModel):
    vehicle_id: str | None = None
    confirmation_phrase: str | None = None
    vehicle_state: VehicleStateIn = Field(default_factory=VehicleStateIn)
    scenario: Literal["normal", "missing_prereq", "abort", "comm_loss"] = "normal"
    acknowledge_disabled: bool = False
    acknowledge_no_oem_write: bool = False


class ServiceRunOut(BaseModel):
    id: str
    procedure_code: str
    status: str
    scenario: str | None = None
    data_source: str
    prerequisites: list[PrerequisiteState]
    result: dict[str, Any]
    message_de: str | None = None
    abort_reason_de: str | None = None
    write_commands_sent: bool = False
    started_at: datetime
    ended_at: datetime | None = None


class ServiceAbortRequest(BaseModel):
    reason_de: str | None = Field(default="Bedienerabbruch", max_length=500)


class MeasurementGroupOut(BaseModel):
    id: str
    label_de: str
    pid_names: list[str]
    notes_de: str
    data_source: str = "simulated"


class DtcHelpOut(BaseModel):
    code: str
    description_de: str | None
    description_status: str  # known | unknown
    severity: str | None = None
    help_de: str
    source: str
    data_source: str
    repair_auto_generated: bool = False


class GuidedOverviewOut(BaseModel):
    data_source: str
    disclaimer_de: str
    ecu_summary: dict[str, Any]
    measurement_groups: list[MeasurementGroupOut]
    dtc_help_hint_de: str
