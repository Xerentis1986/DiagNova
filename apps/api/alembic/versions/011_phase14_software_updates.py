"""phase 14 software connector updates

Revision ID: 011_phase14
Revises: 010_phase13
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_phase14"
down_revision: Union[str, None] = "010_phase13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "software_components",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(32), nullable=False),
        sa.Column("label_de", sa.String(128), nullable=False),
        sa.Column("current_version", sa.String(32), nullable=False),
        sa.Column("previous_version", sa.String(32), nullable=True),
        sa.Column("channel_key", sa.String(64), nullable=False, server_default="stable-fixture"),
        sa.Column("health_status", sa.String(32), nullable=False, server_default="ok"),
        sa.Column("last_healthcheck_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_de", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_software_components_key", "software_components", ["key"], unique=True)

    op.create_table(
        "software_update_channels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel_type", sa.String(32), nullable=False, server_default="stable"),
        sa.Column("fetch_mode", sa.String(16), nullable=False, server_default="fixture"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_install_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("require_signature", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("require_signing_cert", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_software_update_channels_key", "software_update_channels", ["key"], unique=True)

    op.create_table(
        "software_update_packages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "channel_id",
            sa.String(36),
            sa.ForeignKey("software_update_channels.id"),
            nullable=False,
        ),
        sa.Column("component", sa.String(32), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("package_filename", sa.String(255), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("signature_hex", sa.String(128), nullable=True),
        sa.Column("signature_ok", sa.Boolean(), nullable=True),
        sa.Column("release_notes_de", sa.Text(), nullable=False, server_default=""),
        sa.Column("migration_plan_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="staged"),
        sa.Column("error_de", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("approved_by", sa.String(36), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_software_update_packages_channel_id", "software_update_packages", ["channel_id"])
    op.create_index("ix_software_update_packages_component", "software_update_packages", ["component"])
    op.create_index("ix_software_update_packages_version", "software_update_packages", ["version"])
    op.create_index("ix_software_update_packages_status", "software_update_packages", ["status"])

    op.create_table(
        "software_update_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "package_id",
            sa.String(36),
            sa.ForeignKey("software_update_packages.id"),
            nullable=False,
        ),
        sa.Column("component", sa.String(32), nullable=False),
        sa.Column("action", sa.String(16), nullable=False, server_default="install"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("from_version", sa.String(32), nullable=True),
        sa.Column("to_version", sa.String(32), nullable=True),
        sa.Column("healthcheck_ok", sa.Boolean(), nullable=True),
        sa.Column("busy_reason_de", sa.Text(), nullable=True),
        sa.Column("error_de", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("triggered_by", sa.String(36), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_software_update_runs_package_id", "software_update_runs", ["package_id"])
    op.create_index("ix_software_update_runs_component", "software_update_runs", ["component"])
    op.create_index("ix_software_update_runs_status", "software_update_runs", ["status"])

    op.create_table(
        "software_compatibility_rules",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("component", sa.String(32), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("requires_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("notes_de", sa.Text(), nullable=True),
    )
    op.create_index("ix_software_compatibility_rules_component", "software_compatibility_rules", ["component"])
    op.create_index("ix_software_compatibility_rules_version", "software_compatibility_rules", ["version"])

    op.create_table(
        "software_update_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("package_id", sa.String(36), nullable=True),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("component", sa.String(32), nullable=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("detail_de", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_software_update_events_package_id", "software_update_events", ["package_id"])
    op.create_index("ix_software_update_events_run_id", "software_update_events", ["run_id"])
    op.create_index("ix_software_update_events_component", "software_update_events", ["component"])
    op.create_index("ix_software_update_events_event", "software_update_events", ["event"])


def downgrade() -> None:
    op.drop_index("ix_software_update_events_event", table_name="software_update_events")
    op.drop_index("ix_software_update_events_component", table_name="software_update_events")
    op.drop_index("ix_software_update_events_run_id", table_name="software_update_events")
    op.drop_index("ix_software_update_events_package_id", table_name="software_update_events")
    op.drop_table("software_update_events")

    op.drop_index("ix_software_compatibility_rules_version", table_name="software_compatibility_rules")
    op.drop_index("ix_software_compatibility_rules_component", table_name="software_compatibility_rules")
    op.drop_table("software_compatibility_rules")

    op.drop_index("ix_software_update_runs_status", table_name="software_update_runs")
    op.drop_index("ix_software_update_runs_component", table_name="software_update_runs")
    op.drop_index("ix_software_update_runs_package_id", table_name="software_update_runs")
    op.drop_table("software_update_runs")

    op.drop_index("ix_software_update_packages_status", table_name="software_update_packages")
    op.drop_index("ix_software_update_packages_version", table_name="software_update_packages")
    op.drop_index("ix_software_update_packages_component", table_name="software_update_packages")
    op.drop_index("ix_software_update_packages_channel_id", table_name="software_update_packages")
    op.drop_table("software_update_packages")

    op.drop_index("ix_software_update_channels_key", table_name="software_update_channels")
    op.drop_table("software_update_channels")

    op.drop_index("ix_software_components_key", table_name="software_components")
    op.drop_table("software_components")
