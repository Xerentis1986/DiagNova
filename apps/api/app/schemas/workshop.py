"""Schemas Phase 08 – Werkstatt, Kunden, Aufträge."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WorkshopOut(BaseModel):
    id: str
    name: str
    legal_name: str | None
    email: str | None
    phone: str | None
    street: str | None
    postal_code: str | None
    city: str | None
    country: str
    vat_id: str | None
    has_logo: bool
    retention_days: int
    notes: str | None
    is_example_data: bool
    archived_at: datetime | None

    model_config = {"from_attributes": True}


class WorkshopUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    street: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=32)
    city: str | None = Field(default=None, max_length=128)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    vat_id: str | None = Field(default=None, max_length=64)
    logo_data_url: str | None = None
    clear_logo: bool = False
    retention_days: int | None = Field(default=None, ge=30, le=3650)
    notes: str | None = Field(default=None, max_length=2000)


class WorkshopMemberOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: Literal["admin", "technician", "viewer"]
    is_active: bool


class CustomerOut(BaseModel):
    id: str
    workshop_id: str
    display_name: str
    email: str | None
    phone: str | None
    street: str | None
    postal_code: str | None
    city: str | None
    country: str | None
    notes: str | None
    is_example_data: bool
    archived_at: datetime | None
    anonymized_at: datetime | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CustomerCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    street: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=32)
    city: str | None = Field(default=None, max_length=128)
    country: str | None = Field(default=None, max_length=2)
    notes: str | None = Field(default=None, max_length=2000)
    force: bool = False


class CustomerUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=64)
    street: str | None = Field(default=None, max_length=255)
    postal_code: str | None = Field(default=None, max_length=32)
    city: str | None = Field(default=None, max_length=128)
    country: str | None = Field(default=None, max_length=2)
    notes: str | None = Field(default=None, max_length=2000)


class CustomerMergeIn(BaseModel):
    source_customer_id: str = Field(min_length=36, max_length=36)


class CustomerDeleteIn(BaseModel):
    mode: Literal["archive", "anonymize", "delete"] = "archive"
    force: bool = False


class CustomerVehicleAssign(BaseModel):
    vehicle_id: str
    is_primary: bool = True


class WorkOrderOut(BaseModel):
    id: str
    workshop_id: str
    customer_id: str | None
    vehicle_id: str | None
    created_by_user_id: str | None
    title: str
    status: Literal["open", "in_progress", "done", "cancelled"]
    notes: str | None
    repair_summary: str | None
    odometer_km: int | None
    is_example_data: bool
    archived_at: datetime | None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class WorkOrderCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    customer_id: str | None = None
    vehicle_id: str | None = None
    notes: str | None = Field(default=None, max_length=4000)
    repair_summary: str | None = Field(default=None, max_length=4000)
    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    status: Literal["open", "in_progress", "done", "cancelled"] = "open"


class WorkOrderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    customer_id: str | None = None
    vehicle_id: str | None = None
    notes: str | None = Field(default=None, max_length=4000)
    repair_summary: str | None = Field(default=None, max_length=4000)
    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    status: Literal["open", "in_progress", "done", "cancelled"] | None = None


class VehicleWorkshopOut(BaseModel):
    id: str
    workshop_id: str | None
    customer_id: str | None
    make: str
    model: str
    year: int
    vin: str
    license_plate: str | None
    engine: str | None
    fuel_type: str | None
    series: str | None = None
    odometer_km: int | None = None
    is_example_data: bool
    notes: str | None
    archived_at: datetime | None = None

    model_config = {"from_attributes": True}


class VehicleWorkshopCreate(BaseModel):
    make: str = Field(min_length=1, max_length=64)
    model: str = Field(min_length=1, max_length=64)
    year: int = Field(ge=1980, le=2100)
    vin: str = Field(min_length=17, max_length=17)
    license_plate: str | None = Field(default=None, max_length=32)
    engine: str | None = Field(default=None, max_length=64)
    fuel_type: str | None = Field(default=None, max_length=32)
    series: str | None = Field(default=None, max_length=64)
    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    customer_id: str | None = None
    notes: str | None = Field(default=None, max_length=2000)
    force_duplicate_plate: bool = False


class VehicleWorkshopUpdate(BaseModel):
    make: str | None = Field(default=None, min_length=1, max_length=64)
    model: str | None = Field(default=None, min_length=1, max_length=64)
    year: int | None = Field(default=None, ge=1980, le=2100)
    vin: str | None = Field(default=None, min_length=17, max_length=17)
    license_plate: str | None = Field(default=None, max_length=32)
    engine: str | None = Field(default=None, max_length=64)
    fuel_type: str | None = Field(default=None, max_length=32)
    series: str | None = Field(default=None, max_length=64)
    odometer_km: int | None = Field(default=None, ge=0, le=9_999_999)
    customer_id: str | None = None
    notes: str | None = Field(default=None, max_length=2000)
    archive: bool | None = None
