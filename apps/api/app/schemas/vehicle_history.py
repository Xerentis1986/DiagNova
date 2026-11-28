"""Phase 09 – Schemas für Fahrzeugakte und Historie."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SessionStartRequest(BaseModel):
    vehicle_id: str = Field(min_length=1, max_length=36)
    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    work_order_id: str | None = Field(default=None, max_length=36)
    notes: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=64)
    # Optionale ECU-Liste: wenn leer, wird Simulator-Standard gespeichert
    ecu_codes: list[str] | None = Field(default=None, max_length=32)


class SessionAbortRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=255)


class SessionNoteUpdate(BaseModel):
    notes: str | None = Field(default=None, max_length=2000)


class VehicleRecordNoteCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    note_type: Literal["note", "service", "repair"] = "note"
    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    work_order_id: str | None = Field(default=None, max_length=36)
    session_id: str | None = Field(default=None, max_length=36)


class SessionEcuOut(BaseModel):
    ecu_code: str
    ecu_label_de: str
    checked: bool
    protocol_name: str | None
    address_hex: str | None
    status: str


class SessionDtcOut(BaseModel):
    ecu_code: str
    code: str
    dtc_status: str
    description_de: str
    severity: str


class SessionDetailOut(BaseModel):
    id: str
    vehicle_id: str
    vehicle_label: str
    workshop_id: str | None
    user_id: str
    user_name: str | None = None
    work_order_id: str | None
    status: Literal["open", "closed", "aborted"]
    data_source: Literal["simulated", "live"]
    started_at: datetime
    ended_at: datetime | None
    auto_saved_at: datetime | None
    odometer_km: int | None
    adapter_name: str | None
    protocol_name: str | None
    abort_reason: str | None
    notes: str | None
    dtc_count: int
    ecus: list[SessionEcuOut]
    dtcs: list[SessionDtcOut]
    freeze_frame: dict | None
    readiness: dict | None
    report_ids: list[str]
    measurement_sample_count: int


class TimelineItemOut(BaseModel):
    id: str
    kind: Literal["session", "note", "work_order", "report"]
    at: datetime
    title_de: str
    summary_de: str
    data_source: str | None = None
    status: str | None = None
    odometer_km: int | None = None
    session_id: str | None = None
    work_order_id: str | None = None
    report_id: str | None = None
    is_example_data: bool = False
    # Explizit: keine erfundenen Historien als echt
    authenticity: Literal["recorded", "example_seed", "simulated"] = "recorded"


class VehicleRecordOut(BaseModel):
    vehicle_id: str
    make: str
    model: str
    year: int
    vin: str
    license_plate: str | None
    odometer_km: int | None
    is_example_data: bool
    customer_id: str | None
    workshop_id: str | None
    session_count: int
    open_session_count: int
    timeline: list[TimelineItemOut]
    disclaimer_de: str


class MeasurementSampleOut(BaseModel):
    id: str
    session_id: str
    pid: int
    pid_hex: str
    name: str
    value: float
    unit: str
    recorded_at: datetime
    data_source: Literal["simulated", "live"]


class MeasurementSeriesOut(BaseModel):
    vehicle_id: str
    pid: int | None
    name: str | None
    unit: str | None
    from_at: datetime | None
    to_at: datetime | None
    count: int
    truncated: bool
    max_samples: int
    samples: list[MeasurementSampleOut]
    disclaimer_de: str


class DtcCompareItem(BaseModel):
    ecu_code: str
    code: str
    dtc_status: str
    description_de: str
    # neu | weiterhin_vorhanden | nicht_erneut_beobachtet
    # WICHTIG: nicht_erneut_beobachtet ≠ behoben, wenn ECU nicht geprüft
    outcome: Literal["neu", "weiterhin_vorhanden", "nicht_erneut_beobachtet"]
    ecu_checked_in_after: bool
    may_interpret_as_resolved: bool
    note_de: str


class SessionCompareOut(BaseModel):
    before_session_id: str
    after_session_id: str
    vehicle_id: str
    incomplete_scan: bool
    unchecked_ecus_in_after: list[str]
    items: list[DtcCompareItem]
    disclaimer_de: str


class VehicleLookupOut(BaseModel):
    query: str
    matches: list[VehicleRecordOut]
    disclaimer_de: str
