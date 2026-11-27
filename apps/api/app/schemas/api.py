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
    theme_preference: Literal["light", "dark", "system"] = "system"
    workshop_id: str | None = None
    is_platform_admin: bool = False


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: TokenUser


class PreferencesUpdate(BaseModel):
    theme_preference: Literal["light", "dark", "system"]


class PreferencesOut(BaseModel):
    theme_preference: Literal["light", "dark", "system"]


class VehicleOut(BaseModel):
    id: str
    workshop_id: str | None = None
    customer_id: str | None = None
    make: str
    model: str
    year: int
    vin: str
    license_plate: str | None
    engine: str | None
    fuel_type: str | None
    series: str | None = None
    odometer_km: int | None = None
    catalog_brand_slug: str | None = None
    catalog_model_id: str | None = None
    catalog_variant_id: str | None = None
    is_example_data: bool
    notes: str | None
    archived_at: datetime | None = None

    model_config = {"from_attributes": True}


class VehicleConfirmRequest(BaseModel):
    brand_slug: str = Field(min_length=1, max_length=64)
    model_id: str = Field(min_length=1, max_length=64)
    variant_id: str = Field(min_length=1, max_length=64)
    year: int = Field(ge=1980, le=2100)
    vin: str = Field(min_length=17, max_length=17)
    license_plate: str | None = Field(default=None, max_length=32)
    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    notes: str | None = Field(default=None, max_length=2000)


class VehicleUpdateRequest(BaseModel):
    vin: str | None = Field(default=None, min_length=17, max_length=17)
    license_plate: str | None = Field(default=None, max_length=32)
    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    notes: str | None = Field(default=None, max_length=2000)


class BrandOut(BaseModel):
    slug: str
    name: str
    group: str
    sort_order: int
    logo_mode: Literal["text_fallback", "image"]
    logo_initials: str
    logo_rights_cleared: bool
    coverage_disclaimer_de: str
    model_count: int


class CatalogModelOut(BaseModel):
    id: str
    name: str
    variant_count: int


class CatalogVariantOut(BaseModel):
    id: str
    series: str
    year_from: int
    year_to: int
    engine: str
    fuel_type: str


class CapabilityItem(BaseModel):
    id: str
    label_de: str
    status: Literal["simulated", "planned", "available", "unavailable"]
    phase: int


class CapabilitiesOut(BaseModel):
    disclaimer_de: str
    available: list[CapabilityItem]
    unavailable: list[CapabilityItem]
    adapter_next_step_de: str


class FavoritesOut(BaseModel):
    brand_slugs: list[str]


class FavoritesUpdate(BaseModel):
    brand_slugs: list[str] = Field(max_length=64)


class RecentSelectionOut(BaseModel):
    id: str
    vehicle_id: str | None
    brand_slug: str
    brand_name: str
    model_name: str
    series: str | None
    year: int | None
    engine: str | None
    vin: str | None
    used_at: datetime

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
    # aborted wird in Summary als closed gemappt; Detail-Endpoint zeigt aborted
    status: Literal["open", "closed", "aborted"]


class DashboardOut(BaseModel):
    active_vehicle: VehicleOut | None
    connection: ConnectionStatusOut
    recent_sessions: list[DiagnosticSessionOut]
    demo_mode: bool
    planned_modules: list[dict]


class ClearDtcRequest(BaseModel):
    confirmation_phrase: str = Field(min_length=3, max_length=64)
    acknowledge_freeze_frame_loss: bool
    acknowledge_readiness_reset: bool
    acknowledge_permanent_remain: bool
    pre_report_saved: bool
    operator_note: str | None = Field(default=None, max_length=500)


class ReportCreate(BaseModel):
    session_id: str
    title: str = Field(min_length=3, max_length=255)
    notes: str | None = Field(default=None, max_length=4000)
    # Nur manuelle Empfehlungen – keine Auto-Diagnose
    recommendations: str | None = Field(default=None, max_length=4000)
    auto_generate: bool = False


class ReportOut(BaseModel):
    id: str
    session_id: str
    title: str
    created_at: datetime
    content: dict
    report_number: str | None = None
    workshop_id: str | None = None
    vehicle_id: str | None = None
    customer_id: str | None = None
    data_source: str | None = None
    data_version: str | None = None
    content_sha256: str | None = None
    auto_generated: bool = False
    frozen_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    notes: str | None = None
    recommendations: str | None = None

    model_config = {"from_attributes": True}


class ReportSummaryOut(BaseModel):
    id: str
    session_id: str
    workshop_id: str | None = None
    vehicle_id: str | None = None
    customer_id: str | None = None
    report_number: str | None = None
    title: str
    data_source: str | None = None
    data_version: str | None = None
    content_sha256: str | None = None
    auto_generated: bool = False
    demo_watermark: bool = False
    created_at: datetime
    frozen_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    vehicle_label: str
    vin: str | None = None
    dtc_count: int = 0


class ReportPurgeOut(BaseModel):
    purged: int
    retention_days: int
