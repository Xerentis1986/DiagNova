"""phase 08 workshop customers tenants

Revision ID: 005_phase08
Revises: 004_phase07
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_phase08"
down_revision: Union[str, None] = "004_phase07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workshops",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("street", sa.String(255), nullable=True),
        sa.Column("postal_code", sa.String(32), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("country", sa.String(2), nullable=False, server_default="AT"),
        sa.Column("vat_id", sa.String(64), nullable=True),
        sa.Column("logo_data_url", sa.Text(), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_workshops_name", "workshops", ["name"])

    op.create_table(
        "customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("street", sa.String(255), nullable=True),
        sa.Column("postal_code", sa.String(32), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("workshop_id", "email", name="uq_customers_workshop_email"),
    )
    op.create_index("ix_customers_workshop_id", "customers", ["workshop_id"])
    op.create_index("ix_customers_display_name", "customers", ["display_name"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_phone", "customers", ["phone"])

    op.add_column("users", sa.Column("workshop_id", sa.String(36), nullable=True))
    op.create_foreign_key("fk_users_workshop_id", "users", "workshops", ["workshop_id"], ["id"])
    op.create_index("ix_users_workshop_id", "users", ["workshop_id"])

    op.add_column("vehicles", sa.Column("workshop_id", sa.String(36), nullable=True))
    op.add_column("vehicles", sa.Column("customer_id", sa.String(36), nullable=True))
    op.add_column("vehicles", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_vehicles_workshop_id", "vehicles", "workshops", ["workshop_id"], ["id"])
    op.create_foreign_key("fk_vehicles_customer_id", "vehicles", "customers", ["customer_id"], ["id"])
    op.create_index("ix_vehicles_workshop_id", "vehicles", ["workshop_id"])
    op.create_index("ix_vehicles_customer_id", "vehicles", ["customer_id"])
    # VIN global unique → mandantenspezifisch (workshop_id, vin)
    op.drop_index("ix_vehicles_vin", table_name="vehicles")
    op.create_index("ix_vehicles_vin", "vehicles", ["vin"], unique=False)
    op.create_index("uq_vehicles_workshop_vin", "vehicles", ["workshop_id", "vin"], unique=True)

    op.create_table(
        "customer_vehicles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("customer_id", "vehicle_id", name="uq_customer_vehicle"),
    )
    op.create_index("ix_customer_vehicles_workshop_id", "customer_vehicles", ["workshop_id"])
    op.create_index("ix_customer_vehicles_customer_id", "customer_vehicles", ["customer_id"])
    op.create_index("ix_customer_vehicles_vehicle_id", "customer_vehicles", ["vehicle_id"])

    op.create_table(
        "work_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("vehicles.id"), nullable=True),
        sa.Column("created_by_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("repair_summary", sa.Text(), nullable=True),
        sa.Column("odometer_km", sa.Integer(), nullable=True),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_work_orders_workshop_id", "work_orders", ["workshop_id"])
    op.create_index("ix_work_orders_customer_id", "work_orders", ["customer_id"])
    op.create_index("ix_work_orders_vehicle_id", "work_orders", ["vehicle_id"])
    op.create_index("ix_work_orders_status", "work_orders", ["status"])
    op.create_index("ix_work_orders_created_by_user_id", "work_orders", ["created_by_user_id"])

    op.add_column("audit_logs", sa.Column("workshop_id", sa.String(36), nullable=True))
    op.create_index("ix_audit_logs_workshop_id", "audit_logs", ["workshop_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_workshop_id", table_name="audit_logs")
    op.drop_column("audit_logs", "workshop_id")

    op.drop_table("work_orders")
    op.drop_table("customer_vehicles")

    op.drop_index("uq_vehicles_workshop_vin", table_name="vehicles")
    op.drop_index("ix_vehicles_vin", table_name="vehicles")
    op.create_index("ix_vehicles_vin", "vehicles", ["vin"], unique=True)
    op.drop_index("ix_vehicles_customer_id", table_name="vehicles")
    op.drop_index("ix_vehicles_workshop_id", table_name="vehicles")
    op.drop_constraint("fk_vehicles_customer_id", "vehicles", type_="foreignkey")
    op.drop_constraint("fk_vehicles_workshop_id", "vehicles", type_="foreignkey")
    op.drop_column("vehicles", "archived_at")
    op.drop_column("vehicles", "customer_id")
    op.drop_column("vehicles", "workshop_id")

    op.drop_index("ix_users_workshop_id", table_name="users")
    op.drop_constraint("fk_users_workshop_id", "users", type_="foreignkey")
    op.drop_column("users", "workshop_id")

    op.drop_table("customers")
    op.drop_table("workshops")
