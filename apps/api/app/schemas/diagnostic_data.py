"""Pydantic-Schemas für Phase-06 Diagnosedaten und Importe."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ProvenanceOut(BaseModel):
    source_key: str
    source_name: str
    license_name: str
    commercial_use: str
    attribution: str | None = None
    checked_at: str
    redistributable: bool
    url: str | None = None
    version: str | None = None


class DataSourceOut(BaseModel):
    key: str
    name: str
    url: str | None
    version: str | None
    license_name: str
    commercial_use: str
    attribution: str | None
    scope: str
    notes_de: str | None
    checked_at: str
    redistributable: bool


class DatasetVersionOut(BaseModel):
    id: str
    version_label: str
    status: str
    notes_de: str | None
    created_at: datetime
    published_at: datetime | None


class ManufacturerOut(BaseModel):
    id: str
    slug: str
    name: str
    data_scope: str
    provenance: ProvenanceOut


class EcuDefinitionOut(BaseModel):
    id: str
    code: str
    name_de: str
    category: str
    protocol_id: str
    request_address: str | None
    response_address: str | None
    software_variant: str | None
    data_scope: str
    verified: bool
    provenance: ProvenanceOut


class DtcLookupOut(BaseModel):
    code: str
    known: bool
    description_de: str
    description_status: Literal["known", "unknown", "withheld"]
    data_scope: str | None = None
    provenance: ProvenanceOut | None = None
    message_de: str


class PidDefinitionOut(BaseModel):
    id: str
    pid_hex: str
    name: str
    description_de: str
    unit: str
    bytes_needed: int
    conversion_formula: str | None
    data_scope: str
    kind: str
    provenance: ProvenanceOut


class ServiceProcedureOut(BaseModel):
    id: str
    code: str
    name_de: str
    prerequisites: list[Any]
    data_scope: str
    enabled: bool
    notes_de: str | None
    provenance: ProvenanceOut


# --- Import payload schemas ---

DtcCodePattern = r"^[PCBU][0-9A-Fa-f]{4}$"


class ImportManufacturerIn(BaseModel):
    slug: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    data_scope: Literal["generic", "oem"] = "generic"
    notes_de: str | None = None


class ImportModelIn(BaseModel):
    manufacturer_slug: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    year_from: int | None = Field(default=None, ge=1980, le=2100)
    year_to: int | None = Field(default=None, ge=1980, le=2100)
    data_scope: Literal["generic", "oem"] = "generic"


class ImportVariantIn(BaseModel):
    manufacturer_slug: str = Field(min_length=1, max_length=64)
    model_code: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    year_from: int | None = Field(default=None, ge=1980, le=2100)
    year_to: int | None = Field(default=None, ge=1980, le=2100)
    engine: str | None = Field(default=None, max_length=128)
    data_scope: Literal["generic", "oem"] = "generic"


class ImportEcuIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name_de: str = Field(min_length=1, max_length=128)
    category: str = Field(default="powertrain", max_length=64)
    protocol_id: str = Field(default="iso_15765_4", max_length=64)
    request_address: str | None = Field(default=None, max_length=16)
    response_address: str | None = Field(default=None, max_length=16)
    software_variant: str | None = Field(default=None, max_length=64)
    data_scope: Literal["generic", "oem"] = "generic"
    verified: bool = False
    notes_de: str | None = None


class ImportDtcIn(BaseModel):
    code: str = Field(min_length=5, max_length=5)
    description_de: str | None = Field(default=None, max_length=2000)
    description_status: Literal["known", "unknown", "withheld"] = "unknown"
    data_scope: Literal["generic", "oem"] = "generic"
    notes_de: str | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        code = v.strip().upper()
        import re

        if not re.match(DtcCodePattern, code):
            raise ValueError("DTC-Code muss dem Muster P/C/B/U + 4 Hex-Zeichen entsprechen")
        return code


class ImportPidIn(BaseModel):
    pid_hex: str = Field(min_length=1, max_length=8)
    name: str = Field(min_length=1, max_length=64)
    description_de: str = Field(min_length=1, max_length=255)
    unit: str = Field(min_length=1, max_length=32)
    bytes_needed: int = Field(default=1, ge=1, le=8)
    conversion_formula: str | None = Field(default=None, max_length=128)
    data_scope: Literal["generic", "oem"] = "generic"
    kind: Literal["pid", "did"] = "pid"

    @field_validator("pid_hex")
    @classmethod
    def normalize_hex(cls, v: str) -> str:
        h = v.strip().upper().removeprefix("0X")
        if not h or any(c not in "0123456789ABCDEF" for c in h):
            raise ValueError("pid_hex muss Hex sein")
        return h.zfill(2)


class ImportUnitIn(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    label_de: str = Field(min_length=1, max_length=64)
    symbol: str | None = Field(default=None, max_length=16)


class ImportServiceIn(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name_de: str = Field(min_length=1, max_length=255)
    prerequisites: list[Any] = Field(default_factory=list)
    data_scope: Literal["generic", "oem"] = "generic"
    enabled: bool = False
    notes_de: str | None = None


class DiagnosticImportPackage(BaseModel):
    """JSON-Importpaket-Schema (versioniert)."""

    schema_version: Literal["diagnova.diagnostic-import.v1"] = "diagnova.diagnostic-import.v1"
    dataset_version_label: str = Field(min_length=1, max_length=64)
    source_key: str = Field(min_length=1, max_length=64)
    manufacturers: list[ImportManufacturerIn] = Field(default_factory=list)
    models: list[ImportModelIn] = Field(default_factory=list)
    variants: list[ImportVariantIn] = Field(default_factory=list)
    ecus: list[ImportEcuIn] = Field(default_factory=list)
    dtcs: list[ImportDtcIn] = Field(default_factory=list)
    pids: list[ImportPidIn] = Field(default_factory=list)
    units: list[ImportUnitIn] = Field(default_factory=list)
    service_procedures: list[ImportServiceIn] = Field(default_factory=list)


class QuarantineItemOut(BaseModel):
    entity_type: str
    row_index: int
    reason_de: str
    payload: dict[str, Any]


class ConflictItemOut(BaseModel):
    entity_type: str
    key: str
    reason_de: str


class ImportPreviewOut(BaseModel):
    batch_id: str
    status: str
    format: str
    summary: dict[str, Any]
    conflicts: list[ConflictItemOut]
    quarantine: list[QuarantineItemOut]
    can_apply: bool
    message_de: str


class ImportBatchOut(BaseModel):
    id: str
    format: str
    status: str
    filename: str | None
    source_key: str | None
    summary: dict[str, Any]
    conflicts: list[Any]
    quarantine_count: int
    applied_count: int
    created_at: datetime
    applied_at: datetime | None
    rolled_back_at: datetime | None
