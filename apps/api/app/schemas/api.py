from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenUser(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: Literal["admin", "technician", "viewer"]
    is_active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: TokenUser


class VehicleOut(BaseModel):
    id: str
    make: str
    model: str
    year: int
    vin: str
    license_plate: str | None
    engine: str | None
    fuel_type: str | None
    is_example_data: bool
    notes: str | None

    model_config = {"from_attributes": True}


class DtcOut(BaseModel):
    code: str
    status: Literal["stored", "pending", "permanent"]
    description_de: str
    severity: Literal["info", "warning", "critical"]


class PidReadingOut(BaseModel):
    pid: int
    pid_hex: str
    name: str
    description_de: str
    value: float
    unit: str
    timestamp: datetime


class LiveDataOut(BaseModel):
    data_source: Literal["simulated", "live"]
    vehicle_id: str
    vin: str
    readings: list[PidReadingOut]
    readiness: dict[str, bool]
    freeze_frame: dict[str, float | str] | None


class ConnectionStatusOut(BaseModel):
    connected: bool
    mode: Literal["simulator", "connector", "none"]
    adapter_name: str
    data_source: Literal["simulated", "live"]
    message_de: str
    last_heartbeat: datetime | None


class DiagnosticSessionOut(BaseModel):
    id: str
    vehicle_id: str
    vehicle_label: str
    started_at: datetime
    ended_at: datetime | None
    data_source: Literal["simulated", "live"]
    dtc_count: int
    status: Literal["open", "closed"]


class DashboardOut(BaseModel):
    active_vehicle: VehicleOut | None
    connection: ConnectionStatusOut
    recent_sessions: list[DiagnosticSessionOut]
    demo_mode: bool
    planned_modules: list[dict]


class ReportCreate(BaseModel):
    session_id: str
    title: str = Field(min_length=3, max_length=255)


class ReportOut(BaseModel):
    id: str
    session_id: str
    title: str
    created_at: datetime
    content: dict

    model_config = {"from_attributes": True}
