"""phase 13 subscriptions admin invitations devices webhooks

Revision ID: 010_phase13
Revises: 009_phase12
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_phase13"
down_revision: Union[str, None] = "009_phase12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_platform_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("plan_code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="incomplete"),
        sa.Column("payment_provider", sa.String(32), nullable=False, server_default="mock"),
        sa.Column("external_ref", sa.String(128), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("entitlements_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_workshop_id", "subscriptions", ["workshop_id"])
    op.create_index("ix_subscriptions_plan_code", "subscriptions", ["plan_code"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])
    op.create_index("ix_subscriptions_external_ref", "subscriptions", ["external_ref"])

    op.create_table(
        "workshop_invitations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="technician"),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("invited_by_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("workshop_id", "email", name="uq_invitation_workshop_email"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_workshop_invitations_workshop_id", "workshop_invitations", ["workshop_id"])
    op.create_index("ix_workshop_invitations_email", "workshop_invitations", ["email"])
    op.create_index("ix_workshop_invitations_token", "workshop_invitations", ["token"])
    op.create_index("ix_workshop_invitations_status", "workshop_invitations", ["status"])

    op.create_table(
        "device_bindings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("subscription_id", sa.String(36), sa.ForeignKey("subscriptions.id"), nullable=True),
        sa.Column("device_name", sa.String(128), nullable=False),
        sa.Column("device_fingerprint", sa.String(128), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False, server_default="windows"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("workshop_id", "device_fingerprint", name="uq_device_workshop_fp"),
    )
    op.create_index("ix_device_bindings_workshop_id", "device_bindings", ["workshop_id"])
    op.create_index("ix_device_bindings_subscription_id", "device_bindings", ["subscription_id"])

    op.create_table(
        "payment_webhook_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False, server_default="mock"),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("signature_valid", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(32), nullable=False, server_default="received"),
        sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("subscription_id", sa.String(36), nullable=True),
        sa.Column("workshop_id", sa.String(36), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "event_id", name="uq_payment_webhook_event"),
    )
    op.create_index("ix_payment_webhook_events_event_id", "payment_webhook_events", ["event_id"])
    op.create_index("ix_payment_webhook_events_status", "payment_webhook_events", ["status"])
    op.create_index(
        "ix_payment_webhook_events_subscription_id", "payment_webhook_events", ["subscription_id"]
    )
    op.create_index(
        "ix_payment_webhook_events_workshop_id", "payment_webhook_events", ["workshop_id"]
    )

    op.create_table(
        "critical_operation_locks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("operation_kind", sa.String(64), nullable=False),
        sa.Column("resource_ref", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_de", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_critical_operation_locks_workshop_id", "critical_operation_locks", ["workshop_id"]
    )
    op.create_index("ix_critical_operation_locks_status", "critical_operation_locks", ["status"])

    op.create_table(
        "tenant_registrations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("admin_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_code", sa.String(64), nullable=False, server_default="pkw_trial"),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_tenant_registrations_workshop_id", "tenant_registrations", ["workshop_id"])
    op.create_index(
        "ix_tenant_registrations_admin_user_id", "tenant_registrations", ["admin_user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_registrations_admin_user_id", table_name="tenant_registrations")
    op.drop_index("ix_tenant_registrations_workshop_id", table_name="tenant_registrations")
    op.drop_table("tenant_registrations")
    op.drop_index("ix_critical_operation_locks_status", table_name="critical_operation_locks")
    op.drop_index("ix_critical_operation_locks_workshop_id", table_name="critical_operation_locks")
    op.drop_table("critical_operation_locks")
    op.drop_index("ix_payment_webhook_events_workshop_id", table_name="payment_webhook_events")
    op.drop_index("ix_payment_webhook_events_subscription_id", table_name="payment_webhook_events")
    op.drop_index("ix_payment_webhook_events_status", table_name="payment_webhook_events")
    op.drop_index("ix_payment_webhook_events_event_id", table_name="payment_webhook_events")
    op.drop_table("payment_webhook_events")
    op.drop_index("ix_device_bindings_subscription_id", table_name="device_bindings")
    op.drop_index("ix_device_bindings_workshop_id", table_name="device_bindings")
    op.drop_table("device_bindings")
    op.drop_index("ix_workshop_invitations_status", table_name="workshop_invitations")
    op.drop_index("ix_workshop_invitations_token", table_name="workshop_invitations")
    op.drop_index("ix_workshop_invitations_email", table_name="workshop_invitations")
    op.drop_index("ix_workshop_invitations_workshop_id", table_name="workshop_invitations")
    op.drop_table("workshop_invitations")
    op.drop_index("ix_subscriptions_external_ref", table_name="subscriptions")
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_plan_code", table_name="subscriptions")
    op.drop_index("ix_subscriptions_workshop_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_column("users", "is_platform_admin")
