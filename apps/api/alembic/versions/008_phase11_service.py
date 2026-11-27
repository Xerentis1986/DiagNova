"""phase 11 service runs und safety gates

Revision ID: 008_phase11
Revises: 007_phase10
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_phase11"
down_revision: Union[str, None] = "007_phase10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("procedure_code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("scenario", sa.String(32), nullable=True),
        sa.Column("data_source", sa.String(16), nullable=False, server_default="simulated"),
        sa.Column("prerequisites_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("result_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("message_de", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abort_reason_de", sa.Text(), nullable=True),
    )
    op.create_index("ix_service_runs_workshop_id", "service_runs", ["workshop_id"])
    op.create_index("ix_service_runs_vehicle_id", "service_runs", ["vehicle_id"])
    op.create_index("ix_service_runs_procedure_code", "service_runs", ["procedure_code"])


def downgrade() -> None:
    op.drop_index("ix_service_runs_procedure_code", table_name="service_runs")
    op.drop_index("ix_service_runs_vehicle_id", table_name="service_runs")
    op.drop_index("ix_service_runs_workshop_id", table_name="service_runs")
    op.drop_table("service_runs")
