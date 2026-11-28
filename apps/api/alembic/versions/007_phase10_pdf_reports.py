"""phase 10 pdf diagnoseberichte und archiv

Revision ID: 007_phase10
Revises: 006_phase09
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_phase10"
down_revision: Union[str, None] = "006_phase09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("diagnostic_reports", sa.Column("workshop_id", sa.String(36), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("vehicle_id", sa.String(36), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("customer_id", sa.String(36), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("report_number", sa.String(32), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("data_source", sa.String(16), nullable=False, server_default="simulated"))
    op.add_column("diagnostic_reports", sa.Column("data_version", sa.String(64), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("content_sha256", sa.String(64), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("recommendations", sa.Text(), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("auto_generated", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("diagnostic_reports", sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("diagnostic_reports", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_diagnostic_reports_workshop_id", "diagnostic_reports", ["workshop_id"])
    op.create_index("ix_diagnostic_reports_vehicle_id", "diagnostic_reports", ["vehicle_id"])
    op.create_index("ix_diagnostic_reports_customer_id", "diagnostic_reports", ["customer_id"])
    op.create_index("ix_diagnostic_reports_report_number", "diagnostic_reports", ["report_number"])
    op.create_index("ix_diagnostic_reports_archived_at", "diagnostic_reports", ["archived_at"])
    op.create_unique_constraint(
        "uq_diagnostic_reports_workshop_number",
        "diagnostic_reports",
        ["workshop_id", "report_number"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_diagnostic_reports_workshop_number", "diagnostic_reports", type_="unique")
    op.drop_index("ix_diagnostic_reports_archived_at", table_name="diagnostic_reports")
    op.drop_index("ix_diagnostic_reports_report_number", table_name="diagnostic_reports")
    op.drop_index("ix_diagnostic_reports_customer_id", table_name="diagnostic_reports")
    op.drop_index("ix_diagnostic_reports_vehicle_id", table_name="diagnostic_reports")
    op.drop_index("ix_diagnostic_reports_workshop_id", table_name="diagnostic_reports")
    for col in (
        "deleted_at",
        "archived_at",
        "frozen_at",
        "auto_generated",
        "recommendations",
        "notes",
        "content_sha256",
        "data_version",
        "data_source",
        "report_number",
        "customer_id",
        "vehicle_id",
        "workshop_id",
    ):
        op.drop_column("diagnostic_reports", col)
