"""phase 02 catalog prefs favorites recent vehicle fields

Revision ID: 002_phase02
Revises: 001_initial
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_phase02"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("theme_preference", sa.String(length=16), nullable=False, server_default="system"),
    )
    op.add_column("vehicles", sa.Column("series", sa.String(length=64), nullable=True))
    op.add_column("vehicles", sa.Column("odometer_km", sa.Integer(), nullable=True))
    op.add_column("vehicles", sa.Column("catalog_brand_slug", sa.String(length=64), nullable=True))
    op.add_column("vehicles", sa.Column("catalog_model_id", sa.String(length=64), nullable=True))
    op.add_column("vehicles", sa.Column("catalog_variant_id", sa.String(length=64), nullable=True))
    op.create_index("ix_vehicles_catalog_brand_slug", "vehicles", ["catalog_brand_slug"])

    op.create_table(
        "user_brand_favorites",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("brand_slug", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_brand_favorites_user_id", "user_brand_favorites", ["user_id"])
    op.create_index("ix_user_brand_favorites_brand_slug", "user_brand_favorites", ["brand_slug"])

    op.create_table(
        "user_recent_selections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vehicle_id", sa.String(length=36), sa.ForeignKey("vehicles.id"), nullable=True),
        sa.Column("brand_slug", sa.String(length=64), nullable=False),
        sa.Column("brand_name", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("series", sa.String(length=64), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("engine", sa.String(length=64), nullable=True),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_user_recent_selections_user_id", "user_recent_selections", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_recent_selections")
    op.drop_table("user_brand_favorites")
    op.drop_index("ix_vehicles_catalog_brand_slug", table_name="vehicles")
    op.drop_column("vehicles", "catalog_variant_id")
    op.drop_column("vehicles", "catalog_model_id")
    op.drop_column("vehicles", "catalog_brand_slug")
    op.drop_column("vehicles", "odometer_km")
    op.drop_column("vehicles", "series")
    op.drop_column("users", "theme_preference")
