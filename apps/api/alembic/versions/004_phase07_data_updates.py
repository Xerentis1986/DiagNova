"""phase 07 automatic diagnostic data updates

Revision ID: 004_phase07
Revises: 003_phase06
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_phase07"
down_revision: Union[str, None] = "003_phase06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "update_channels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("fetch_mode", sa.String(16), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rights_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("interval_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("expected_license", sa.String(128), nullable=False),
        sa.Column("source_key", sa.String(64), nullable=False),
        sa.Column("content_kind", sa.String(32), nullable=False),
        sa.Column("auto_activate_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_bytes", sa.Integer(), nullable=False, server_default="2000000"),
        sa.Column("require_signature", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("signature_key_id", sa.String(64), nullable=True),
        sa.Column("last_etag", sa.String(255), nullable=True),
        sa.Column("last_version", sa.String(64), nullable=True),
        sa.Column("last_content_hash", sa.String(64), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_update_channels_key", "update_channels", ["key"], unique=True)

    op.create_table(
        "update_job_locks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("locked_by", sa.String(128), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "update_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel_id", sa.String(36), sa.ForeignKey("update_channels.id"), nullable=False),
        sa.Column("trigger", sa.String(16), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("etag", sa.String(255), nullable=True),
        sa.Column("version_label", sa.String(64), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("signature_ok", sa.Boolean(), nullable=True),
        sa.Column("license_changed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("detected_license", sa.String(128), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error_de", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("staging_json", sa.Text(), nullable=True),
        sa.Column("import_batch_id", sa.String(36), nullable=True),
        sa.Column(
            "dataset_version_id",
            sa.String(36),
            sa.ForeignKey("diag_dataset_versions.id"),
            nullable=True,
        ),
        sa.Column("previous_dataset_version_id", sa.String(36), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(36), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_update_runs_channel_id", "update_runs", ["channel_id"])
    op.create_index("ix_update_runs_status", "update_runs", ["status"])

    op.create_table(
        "update_changelogs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("update_runs.id"), nullable=False),
        sa.Column("channel_key", sa.String(64), nullable=False),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("detail_de", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_update_changelogs_run_id", "update_changelogs", ["run_id"])
    op.create_index("ix_update_changelogs_channel_key", "update_changelogs", ["channel_key"])


def downgrade() -> None:
    op.drop_table("update_changelogs")
    op.drop_table("update_runs")
    op.drop_table("update_job_locks")
    op.drop_table("update_channels")
