"""phase 09 vehicle history digital record

Revision ID: 006_phase09
Revises: 005_phase08
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_phase09"
down_revision: Union[str, None] = "005_phase08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("diagnostic_sessions", sa.Column("workshop_id", sa.String(36), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("work_order_id", sa.String(36), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("auto_saved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("freeze_frame_json", sa.Text(), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("readiness_json", sa.Text(), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("odometer_km", sa.Integer(), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("adapter_name", sa.String(128), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("protocol_name", sa.String(64), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("abort_reason", sa.String(255), nullable=True))
    op.add_column("diagnostic_sessions", sa.Column("idempotency_key", sa.String(64), nullable=True))
    op.create_index("ix_diagnostic_sessions_workshop_id", "diagnostic_sessions", ["workshop_id"])
    op.create_index("ix_diagnostic_sessions_work_order_id", "diagnostic_sessions", ["work_order_id"])
    op.create_foreign_key(
        "fk_diagnostic_sessions_work_order_id",
        "diagnostic_sessions",
        "work_orders",
        ["work_order_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_session_workshop_idempotency",
        "diagnostic_sessions",
        ["workshop_id", "idempotency_key"],
    )

    op.create_table(
        "session_ecu_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("diagnostic_sessions.id"), nullable=False),
        sa.Column("ecu_code", sa.String(64), nullable=False),
        sa.Column("ecu_label_de", sa.String(128), nullable=False),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("protocol_name", sa.String(64), nullable=True),
        sa.Column("address_hex", sa.String(16), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ok"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("session_id", "ecu_code", name="uq_session_ecu"),
    )
    op.create_index("ix_session_ecu_results_session_id", "session_ecu_results", ["session_id"])
    op.create_index("ix_session_ecu_results_ecu_code", "session_ecu_results", ["ecu_code"])

    op.create_table(
        "session_dtc_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("diagnostic_sessions.id"), nullable=False),
        sa.Column("ecu_result_id", sa.String(36), sa.ForeignKey("session_ecu_results.id"), nullable=True),
        sa.Column("ecu_code", sa.String(64), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("dtc_status", sa.String(16), nullable=False),
        sa.Column("description_de", sa.String(255), nullable=False, server_default=""),
        sa.Column("severity", sa.String(16), nullable=False, server_default="info"),
        sa.UniqueConstraint("session_id", "ecu_code", "code", "dtc_status", name="uq_session_dtc"),
    )
    op.create_index("ix_session_dtc_results_session_id", "session_dtc_results", ["session_id"])
    op.create_index("ix_session_dtc_results_ecu_result_id", "session_dtc_results", ["ecu_result_id"])
    op.create_index("ix_session_dtc_results_ecu_code", "session_dtc_results", ["ecu_code"])
    op.create_index("ix_session_dtc_results_code", "session_dtc_results", ["code"])

    op.create_table(
        "session_measurement_samples",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("diagnostic_sessions.id"), nullable=False),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("workshop_id", sa.String(36), nullable=False),
        sa.Column("pid", sa.Integer(), nullable=False),
        sa.Column("pid_hex", sa.String(8), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False, server_default=""),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="simulated"),
    )
    op.create_index("ix_session_measurement_samples_session_id", "session_measurement_samples", ["session_id"])
    op.create_index("ix_session_measurement_samples_vehicle_id", "session_measurement_samples", ["vehicle_id"])
    op.create_index("ix_session_measurement_samples_workshop_id", "session_measurement_samples", ["workshop_id"])
    op.create_index("ix_session_measurement_samples_pid", "session_measurement_samples", ["pid"])
    op.create_index("ix_session_measurement_samples_recorded_at", "session_measurement_samples", ["recorded_at"])

    op.create_table(
        "vehicle_record_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), nullable=False),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("work_order_id", sa.String(36), sa.ForeignKey("work_orders.id"), nullable=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("diagnostic_sessions.id"), nullable=True),
        sa.Column("note_type", sa.String(32), nullable=False, server_default="note"),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("odometer_km", sa.Integer(), nullable=True),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vehicle_record_notes_workshop_id", "vehicle_record_notes", ["workshop_id"])
    op.create_index("ix_vehicle_record_notes_vehicle_id", "vehicle_record_notes", ["vehicle_id"])


def downgrade() -> None:
    op.drop_table("vehicle_record_notes")
    op.drop_table("session_measurement_samples")
    op.drop_table("session_dtc_results")
    op.drop_table("session_ecu_results")
    op.drop_constraint("uq_session_workshop_idempotency", "diagnostic_sessions", type_="unique")
    op.drop_constraint("fk_diagnostic_sessions_work_order_id", "diagnostic_sessions", type_="foreignkey")
    op.drop_index("ix_diagnostic_sessions_work_order_id", table_name="diagnostic_sessions")
    op.drop_index("ix_diagnostic_sessions_workshop_id", table_name="diagnostic_sessions")
    for col in (
        "idempotency_key",
        "abort_reason",
        "protocol_name",
        "adapter_name",
        "odometer_km",
        "readiness_json",
        "freeze_frame_json",
        "auto_saved_at",
        "work_order_id",
        "workshop_id",
    ):
        op.drop_column("diagnostic_sessions", col)
