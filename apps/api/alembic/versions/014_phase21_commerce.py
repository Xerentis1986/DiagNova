"""phase 21 b2b/b2c commerce tables

Revision ID: 014_phase21
Revises: 013_phase18
Create Date: 2026-11-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_phase21"
down_revision: Union[str, None] = "013_phase18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "billing_accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("customer_type", sa.String(8), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("contact_name", sa.String(255), nullable=False),
        sa.Column("billing_email", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("legal_form", sa.String(64), nullable=True),
        sa.Column("vat_id", sa.String(32), nullable=True),
        sa.Column("vat_status", sa.String(32), nullable=False, server_default="not_applicable"),
        sa.Column("tax_classification", sa.String(64), nullable=True),
        sa.Column("street", sa.String(255), nullable=True),
        sa.Column("postal_code", sa.String(32), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("country", sa.String(2), nullable=False, server_default="AT"),
        sa.Column("location_evidence", sa.String(32), nullable=False, server_default="self_declared"),
        sa.Column("payment_method", sa.String(32), nullable=False, server_default="mock"),
        sa.Column("preferred_plan_code", sa.String(64), nullable=True),
        sa.Column("license_seats", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("privacy_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawal_info_ack_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("marketing_opt_in", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_billing_accounts_workshop_id", "billing_accounts", ["workshop_id"])
    op.create_index("ix_billing_accounts_customer_type", "billing_accounts", ["customer_type"])
    op.create_index("ix_billing_accounts_billing_email", "billing_accounts", ["billing_email"])
    op.create_index("ix_billing_accounts_vat_id", "billing_accounts", ["vat_id"])

    op.create_table(
        "vat_check_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("billing_account_id", sa.String(36), sa.ForeignKey("billing_accounts.id"), nullable=True),
        sa.Column("workshop_id", sa.String(36), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=False),
        sa.Column("vat_number", sa.String(32), nullable=False),
        sa.Column("result", sa.String(32), nullable=False),
        sa.Column("request_mode", sa.String(16), nullable=False, server_default="stub"),
        sa.Column("name_returned", sa.String(255), nullable=True),
        sa.Column("address_returned", sa.Text(), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("raw_summary_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_vat_check_logs_billing_account_id", "vat_check_logs", ["billing_account_id"])
    op.create_index("ix_vat_check_logs_result", "vat_check_logs", ["result"])

    op.create_table(
        "tax_rule_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("version", sa.String(32), nullable=False, server_default="1"),
        sa.Column("scenario", sa.String(64), nullable=False),
        sa.Column("customer_type", sa.String(8), nullable=False),
        sa.Column("supplier_country", sa.String(2), nullable=False, server_default="AT"),
        sa.Column("customer_country", sa.String(2), nullable=False),
        sa.Column("vat_rate_bp", sa.Integer(), nullable=False),
        sa.Column("reverse_charge", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("oss_applicable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_gross", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("legal_basis_de", sa.Text(), nullable=False),
        sa.Column("review_status", sa.String(32), nullable=False, server_default="draft_needs_review"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("code", "version", name="uq_tax_rule_code_version"),
    )
    op.create_index("ix_tax_rule_snapshots_code", "tax_rule_snapshots", ["code"])
    op.create_index("ix_tax_rule_snapshots_scenario", "tax_rule_snapshots", ["scenario"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workshop_id", sa.String(36), sa.ForeignKey("workshops.id"), nullable=False),
        sa.Column("billing_account_id", sa.String(36), sa.ForeignKey("billing_accounts.id"), nullable=False),
        sa.Column("subscription_id", sa.String(36), sa.ForeignKey("subscriptions.id"), nullable=True),
        sa.Column("doc_type", sa.String(16), nullable=False, server_default="invoice"),
        sa.Column("number", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="issued"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("net_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vat_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gross_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vat_rate_bp", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("tax_scenario", sa.String(64), nullable=False),
        sa.Column("reverse_charge", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("oss_applicable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("line_items_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("buyer_snapshot_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("tax_snapshot_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("notes_de", sa.Text(), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retention_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_example_data", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("workshop_id", "number", name="uq_invoice_workshop_number"),
    )
    op.create_index("ix_invoices_workshop_id", "invoices", ["workshop_id"])
    op.create_index("ix_invoices_billing_account_id", "invoices", ["billing_account_id"])
    op.create_index("ix_invoices_number", "invoices", ["number"])

    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("billing_account_id", sa.String(36), sa.ForeignKey("billing_accounts.id"), nullable=False),
        sa.Column("workshop_id", sa.String(36), nullable=False),
        sa.Column("consent_type", sa.String(64), nullable=False),
        sa.Column("version_label", sa.String(64), nullable=False),
        sa.Column("text_hash", sa.String(64), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ip_hint", sa.String(64), nullable=True),
        sa.Column("user_agent_hint", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_consent_records_billing_account_id", "consent_records", ["billing_account_id"])
    op.create_index("ix_consent_records_consent_type", "consent_records", ["consent_type"])


def downgrade() -> None:
    op.drop_table("consent_records")
    op.drop_table("invoices")
    op.drop_table("tax_rule_snapshots")
    op.drop_table("vat_check_logs")
    op.drop_table("billing_accounts")
