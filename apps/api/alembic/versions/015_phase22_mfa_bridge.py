"""Phase 22 – MFA columns on users.

Revision ID: 015_phase22
Revises: 014_phase21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "015_phase22"
down_revision = "014_phase21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("mfa_secret", sa.String(length=64), nullable=True))
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_secret")
