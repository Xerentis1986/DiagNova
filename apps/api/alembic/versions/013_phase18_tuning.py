"""phase 18 optional chiptuning architecture tables

Revision ID: 013_phase18
Revises: 012_phase15
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_phase18"
down_revision: Union[str, None] = "012_phase15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tuning_software_baselines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("code", sa.String(128), nullable=False),
        sa.Column("ecu_role", sa.String(64), nullable=False, server_default="engine"),
        sa.Column("software_version", sa.String(64), nullable=False),
        sa.Column("part_number", sa.String(128), nullable=True),
        sa.Column("checksum_ref", sa.String(256), nullable=True),
        sa.Column("source_de", sa.Text(), nullable=False, server_default=""),
        sa.Column("authorization_status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("compatible_notes_de", sa.Text(), nullable=True),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="simulated"),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tuning_software_baselines_workshop_id", "tuning_software_baselines", ["workshop_id"])
    op.create_index("ix_tuning_software_baselines_code", "tuning_software_baselines", ["code"])

    op.create_table(
        "tuning_approval_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column(
            "baseline_id",
            sa.String(36),
            sa.ForeignKey("tuning_software_baselines.id"),
            nullable=True,
        ),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=True),
        sa.Column("doc_type", sa.String(64), nullable=False, server_default="workshop_ack"),
        sa.Column("title_de", sa.String(256), nullable=False),
        sa.Column("reference_code", sa.String(128), nullable=True),
        sa.Column("issuer_de", sa.String(256), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="recorded"),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="simulated"),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tuning_approval_documents_workshop_id", "tuning_approval_documents", ["workshop_id"])
    op.create_index("ix_tuning_approval_documents_baseline_id", "tuning_approval_documents", ["baseline_id"])
    op.create_index("ix_tuning_approval_documents_vehicle_id", "tuning_approval_documents", ["vehicle_id"])

    op.create_table(
        "tuning_version_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=True),
        sa.Column(
            "baseline_id",
            sa.String(36),
            sa.ForeignKey("tuning_software_baselines.id"),
            nullable=True,
        ),
        sa.Column("ecu_role", sa.String(64), nullable=False, server_default="engine"),
        sa.Column("software_version", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False, server_default="recorded"),
        sa.Column("message_de", sa.Text(), nullable=True),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="simulated"),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tuning_version_history_workshop_id", "tuning_version_history", ["workshop_id"])
    op.create_index("ix_tuning_version_history_vehicle_id", "tuning_version_history", ["vehicle_id"])
    op.create_index("ix_tuning_version_history_baseline_id", "tuning_version_history", ["baseline_id"])

    op.create_table(
        "tuning_workflow_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("operation_code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("scenario", sa.String(32), nullable=True),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="simulated"),
        sa.Column("prerequisites_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("gates_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("message_de", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abort_reason_de", sa.Text(), nullable=True),
    )
    op.create_index("ix_tuning_workflow_runs_workshop_id", "tuning_workflow_runs", ["workshop_id"])
    op.create_index("ix_tuning_workflow_runs_vehicle_id", "tuning_workflow_runs", ["vehicle_id"])
    op.create_index("ix_tuning_workflow_runs_operation_code", "tuning_workflow_runs", ["operation_code"])


def downgrade() -> None:
    op.drop_index("ix_tuning_workflow_runs_operation_code", table_name="tuning_workflow_runs")
    op.drop_index("ix_tuning_workflow_runs_vehicle_id", table_name="tuning_workflow_runs")
    op.drop_index("ix_tuning_workflow_runs_workshop_id", table_name="tuning_workflow_runs")
    op.drop_table("tuning_workflow_runs")

    op.drop_index("ix_tuning_version_history_baseline_id", table_name="tuning_version_history")
    op.drop_index("ix_tuning_version_history_vehicle_id", table_name="tuning_version_history")
    op.drop_index("ix_tuning_version_history_workshop_id", table_name="tuning_version_history")
    op.drop_table("tuning_version_history")

    op.drop_index("ix_tuning_approval_documents_vehicle_id", table_name="tuning_approval_documents")
    op.drop_index("ix_tuning_approval_documents_baseline_id", table_name="tuning_approval_documents")
    op.drop_index("ix_tuning_approval_documents_workshop_id", table_name="tuning_approval_documents")
    op.drop_table("tuning_approval_documents")

    op.drop_index("ix_tuning_software_baselines_code", table_name="tuning_software_baselines")
    op.drop_index("ix_tuning_software_baselines_workshop_id", table_name="tuning_software_baselines")
    op.drop_table("tuning_software_baselines")
