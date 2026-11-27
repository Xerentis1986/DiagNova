"""phase 06 diagnostic data model and import tables

Revision ID: 003_phase06
Revises: 002_phase02
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_phase06"
down_revision: Union[str, None] = "002_phase02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_license_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(512), nullable=True),
        sa.Column("version", sa.String(64), nullable=True),
        sa.Column("license_name", sa.String(128), nullable=False),
        sa.Column("commercial_use", sa.String(32), nullable=False),
        sa.Column("attribution", sa.Text(), nullable=True),
        sa.Column("scope", sa.String(32), nullable=False),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.String(32), nullable=False),
        sa.Column("redistributable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_data_license_sources_key", "data_license_sources", ["key"], unique=True)

    op.create_table(
        "diag_dataset_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("version_label", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=True),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_diag_dataset_versions_version_label", "diag_dataset_versions", ["version_label"], unique=True)

    op.create_table(
        "diag_manufacturers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_version_id", sa.String(36), sa.ForeignKey("diag_dataset_versions.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("data_scope", sa.String(16), nullable=False),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.UniqueConstraint("slug", "dataset_version_id", name="uq_diag_mfr_slug_ver"),
    )
    op.create_index("ix_diag_manufacturers_slug", "diag_manufacturers", ["slug"])

    op.create_table(
        "diag_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("manufacturer_id", sa.String(36), sa.ForeignKey("diag_manufacturers.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("year_from", sa.Integer(), nullable=True),
        sa.Column("year_to", sa.Integer(), nullable=True),
        sa.Column("data_scope", sa.String(16), nullable=False),
        sa.UniqueConstraint("manufacturer_id", "code", name="uq_diag_model_mfr_code"),
    )

    op.create_table(
        "diag_variants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("model_id", sa.String(36), sa.ForeignKey("diag_models.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("year_from", sa.Integer(), nullable=True),
        sa.Column("year_to", sa.Integer(), nullable=True),
        sa.Column("engine", sa.String(128), nullable=True),
        sa.Column("data_scope", sa.String(16), nullable=False),
        sa.UniqueConstraint("model_id", "code", name="uq_diag_variant_model_code"),
    )

    op.create_table(
        "diag_ecu_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_version_id", sa.String(36), sa.ForeignKey("diag_dataset_versions.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name_de", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("protocol_id", sa.String(64), nullable=False),
        sa.Column("request_address", sa.String(16), nullable=True),
        sa.Column("response_address", sa.String(16), nullable=True),
        sa.Column("software_variant", sa.String(64), nullable=True),
        sa.Column("data_scope", sa.String(16), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.UniqueConstraint("dataset_version_id", "code", name="uq_diag_ecu_ver_code"),
    )

    op.create_table(
        "diag_dtc_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_version_id", sa.String(36), sa.ForeignKey("diag_dataset_versions.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("description_de", sa.Text(), nullable=True),
        sa.Column("description_status", sa.String(16), nullable=False),
        sa.Column("data_scope", sa.String(16), nullable=False),
        sa.Column("system", sa.String(16), nullable=True),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.UniqueConstraint("dataset_version_id", "code", "data_scope", name="uq_diag_dtc_ver_code_scope"),
    )
    op.create_index("ix_diag_dtc_definitions_code", "diag_dtc_definitions", ["code"])

    op.create_table(
        "diag_pid_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_version_id", sa.String(36), sa.ForeignKey("diag_dataset_versions.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=False),
        sa.Column("pid_hex", sa.String(8), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("description_de", sa.String(255), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("bytes_needed", sa.Integer(), nullable=False),
        sa.Column("conversion_formula", sa.String(128), nullable=True),
        sa.Column("data_scope", sa.String(16), nullable=False),
        sa.Column("kind", sa.String(8), nullable=False),
        sa.UniqueConstraint("dataset_version_id", "pid_hex", name="uq_diag_pid_ver_hex"),
    )

    op.create_table(
        "diag_unit_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_version_id", sa.String(36), sa.ForeignKey("diag_dataset_versions.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("label_de", sa.String(64), nullable=False),
        sa.Column("symbol", sa.String(16), nullable=True),
        sa.UniqueConstraint("dataset_version_id", "code", name="uq_diag_unit_ver_code"),
    )

    op.create_table(
        "diag_service_procedures",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_version_id", sa.String(36), sa.ForeignKey("diag_dataset_versions.id"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("data_license_sources.id"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name_de", sa.String(255), nullable=False),
        sa.Column("prerequisites_json", sa.Text(), nullable=False),
        sa.Column("data_scope", sa.String(16), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.UniqueConstraint("dataset_version_id", "code", name="uq_diag_svc_ver_code"),
    )

    op.create_table(
        "import_batches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("format", sa.String(16), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("dataset_version_id", sa.String(36), sa.ForeignKey("diag_dataset_versions.id"), nullable=True),
        sa.Column("source_key", sa.String(64), nullable=True),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False),
        sa.Column("conflict_report_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "import_quarantine_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("import_batches.id"), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("row_index", sa.Integer(), nullable=False),
        sa.Column("reason_de", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "import_applied_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("batch_id", sa.String(36), sa.ForeignKey("import_batches.id"), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("import_applied_records")
    op.drop_table("import_quarantine_items")
    op.drop_table("import_batches")
    op.drop_table("diag_service_procedures")
    op.drop_table("diag_unit_definitions")
    op.drop_table("diag_pid_definitions")
    op.drop_table("diag_dtc_definitions")
    op.drop_table("diag_ecu_definitions")
    op.drop_table("diag_variants")
    op.drop_table("diag_models")
    op.drop_table("diag_manufacturers")
    op.drop_table("diag_dataset_versions")
    op.drop_table("data_license_sources")
