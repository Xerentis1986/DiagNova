"""phase 15 security audit metadata

Revision ID: 012_phase15
Revises: 011_phase14
Create Date: 2026-11-27

Erweitert audit_logs um optionale outcome/ip_hash-Spalten (rückwärtskompatibel).
Anwendungslogik schreibt weiterhin redigierte Details; Spalten für künftige Abfragen.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_phase15"
down_revision: Union[str, None] = "011_phase14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("audit_logs") as batch:
        batch.add_column(sa.Column("outcome", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("ip_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("audit_logs") as batch:
        batch.drop_column("ip_hash")
        batch.drop_column("outcome")
