"""Phase 06 – versioniertes Diagnosedatenmodell mit Herkunftsnachweis."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class DataLicenseSource(Base):
    """Dokumentierte Datenquelle mit Lizenz/Attribution – nichts ohne Eintrag."""

    __tablename__ = "data_license_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    license_name: Mapped[str] = mapped_column(String(128))
    commercial_use: Mapped[str] = mapped_column(String(32), default="unknown")
    # allowed | restricted | prohibited | unknown | not_applicable
    attribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str] = mapped_column(String(32), default="generic")
    # generic | oem | structural | documentation_only
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[str] = mapped_column(String(32))  # ISO-Datum YYYY-MM-DD
    redistributable: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DiagDatasetVersion(Base):
    """Versionierte Datensatz-Veröffentlichung (manuell; Auto-Updates = Phase 07)."""

    __tablename__ = "diag_dataset_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    version_label: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    # draft | published | superseded | rolled_back
    source_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("data_license_sources.id"), nullable=True)
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped[DataLicenseSource | None] = relationship()


class DiagManufacturer(Base):
    __tablename__ = "diag_manufacturers"
    __table_args__ = (UniqueConstraint("slug", "dataset_version_id", name="uq_diag_mfr_slug_ver"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("diag_dataset_versions.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_license_sources.id"), index=True)
    slug: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128))
    data_scope: Mapped[str] = mapped_column(String(16), default="generic")  # generic | oem
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)

    models: Mapped[list[DiagModel]] = relationship(back_populates="manufacturer")


class DiagModel(Base):
    __tablename__ = "diag_models"
    __table_args__ = (UniqueConstraint("manufacturer_id", "code", name="uq_diag_model_mfr_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    manufacturer_id: Mapped[str] = mapped_column(String(36), ForeignKey("diag_manufacturers.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_license_sources.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    year_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_scope: Mapped[str] = mapped_column(String(16), default="generic")

    manufacturer: Mapped[DiagManufacturer] = relationship(back_populates="models")
    variants: Mapped[list[DiagVariant]] = relationship(back_populates="model")


class DiagVariant(Base):
    __tablename__ = "diag_variants"
    __table_args__ = (UniqueConstraint("model_id", "code", name="uq_diag_variant_model_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("diag_models.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_license_sources.id"), index=True)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    year_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    engine: Mapped[str | None] = mapped_column(String(128), nullable=True)
    data_scope: Mapped[str] = mapped_column(String(16), default="generic")

    model: Mapped[DiagModel] = relationship(back_populates="variants")


class DiagEcuDefinition(Base):
    __tablename__ = "diag_ecu_definitions"
    __table_args__ = (UniqueConstraint("dataset_version_id", "code", name="uq_diag_ecu_ver_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("diag_dataset_versions.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_license_sources.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name_de: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(64), default="powertrain")
    protocol_id: Mapped[str] = mapped_column(String(64), default="iso_15765_4")
    request_address: Mapped[str | None] = mapped_column(String(16), nullable=True)
    response_address: Mapped[str | None] = mapped_column(String(16), nullable=True)
    software_variant: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data_scope: Mapped[str] = mapped_column(String(16), default="generic")
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)


class DiagDtcDefinition(Base):
    """DTC-Eintrag. Fehlende Beschreibung → UI zeigt „unbekannt“."""

    __tablename__ = "diag_dtc_definitions"
    __table_args__ = (
        UniqueConstraint("dataset_version_id", "code", "data_scope", name="uq_diag_dtc_ver_code_scope"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("diag_dataset_versions.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_license_sources.id"), index=True)
    code: Mapped[str] = mapped_column(String(16), index=True)
    description_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_status: Mapped[str] = mapped_column(String(16), default="unknown")
    # known | unknown | withheld
    data_scope: Mapped[str] = mapped_column(String(16), default="generic")
    system: Mapped[str | None] = mapped_column(String(16), nullable=True)  # P/C/B/U
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)


class DiagPidDefinition(Base):
    __tablename__ = "diag_pid_definitions"
    __table_args__ = (UniqueConstraint("dataset_version_id", "pid_hex", name="uq_diag_pid_ver_hex"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("diag_dataset_versions.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_license_sources.id"), index=True)
    pid_hex: Mapped[str] = mapped_column(String(8), index=True)
    name: Mapped[str] = mapped_column(String(64))
    description_de: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(32))
    bytes_needed: Mapped[int] = mapped_column(Integer, default=1)
    conversion_formula: Mapped[str | None] = mapped_column(String(128), nullable=True)
    data_scope: Mapped[str] = mapped_column(String(16), default="generic")
    kind: Mapped[str] = mapped_column(String(8), default="pid")  # pid | did


class DiagUnitDefinition(Base):
    __tablename__ = "diag_unit_definitions"
    __table_args__ = (UniqueConstraint("dataset_version_id", "code", name="uq_diag_unit_ver_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("diag_dataset_versions.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_license_sources.id"), index=True)
    code: Mapped[str] = mapped_column(String(32))
    label_de: Mapped[str] = mapped_column(String(64))
    symbol: Mapped[str | None] = mapped_column(String(16), nullable=True)


class DiagServiceProcedure(Base):
    """Serviceprozedur-Gerüst – ohne OEM-Inhalte, solange keine Lizenz vorliegt."""

    __tablename__ = "diag_service_procedures"
    __table_args__ = (UniqueConstraint("dataset_version_id", "code", name="uq_diag_svc_ver_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("diag_dataset_versions.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_license_sources.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name_de: Mapped[str] = mapped_column(String(255))
    prerequisites_json: Mapped[str] = mapped_column(Text, default="[]")
    data_scope: Mapped[str] = mapped_column(String(16), default="generic")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)


class ImportBatch(Base):
    """Importlauf: Vorschau → Quarantäne/Apply → Rollback."""

    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    format: Mapped[str] = mapped_column(String(16))  # json | csv | odx
    status: Mapped[str] = mapped_column(String(24), default="preview")
    # preview | quarantine | applied | rolled_back | rejected
    dataset_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("diag_dataset_versions.id"), nullable=True, index=True
    )
    source_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    summary_json: Mapped[str] = mapped_column(Text, default="{}")
    conflict_report_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quarantine_items: Mapped[list[ImportQuarantineItem]] = relationship(back_populates="batch")
    applied_records: Mapped[list[ImportAppliedRecord]] = relationship(back_populates="batch")


class ImportQuarantineItem(Base):
    __tablename__ = "import_quarantine_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("import_batches.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(32))
    row_index: Mapped[int] = mapped_column(Integer)
    reason_de: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    batch: Mapped[ImportBatch] = relationship(back_populates="quarantine_items")


class ImportAppliedRecord(Base):
    """Für Rollback: welche Entity-IDs dieser Batch angelegt hat."""

    __tablename__ = "import_applied_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("import_batches.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(32))
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    batch: Mapped[ImportBatch] = relationship(back_populates="applied_records")
