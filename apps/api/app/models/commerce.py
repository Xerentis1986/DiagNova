"""Phase 21 – B2B/B2C Abrechnung, Steuer, Rechnungen (Simulation; kein echter PSP)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class BillingAccount(Base):
    """Kaufmännisches Kundenkonto – B2B oder B2C, an Mandant gebunden."""

    __tablename__ = "billing_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    # b2b | b2c
    customer_type: Mapped[str] = mapped_column(String(8), index=True)
    # active | suspended | closed
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)

    # B2C: Person; B2B: Ansprechpartner
    contact_name: Mapped[str] = mapped_column(String(255))
    billing_email: Mapped[str] = mapped_column(String(255), index=True)

    # B2B-Felder (B2C: null)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    legal_form: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vat_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    # unknown | pending | valid | invalid | not_applicable | error
    vat_status: Mapped[str] = mapped_column(String(32), default="not_applicable")
    tax_classification: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Adresse / Standortnachweis
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="AT", index=True)
    # self_declared | billing_address | vies | ip_geo | other
    location_evidence: Mapped[str] = mapped_column(String(32), default="self_declared")

    # Zahlung / Abo (Stub)
    payment_method: Mapped[str] = mapped_column(String(32), default="mock")
    preferred_plan_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    license_seats: Mapped[int] = mapped_column(Integer, default=1)

    # Verbraucherschutz / Consent
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    privacy_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawal_info_ack_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)

    is_example_data: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VatCheckLog(Base):
    """Protokoll EU-VIES (oder Offline-Stub) – keine Secrets."""

    __tablename__ = "vat_check_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    billing_account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("billing_accounts.id"), nullable=True, index=True
    )
    workshop_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    country_code: Mapped[str] = mapped_column(String(2))
    vat_number: Mapped[str] = mapped_column(String(32))
    # valid | invalid | service_unavailable | invalid_input | timeout | stub
    result: Mapped[str] = mapped_column(String(32), index=True)
    request_mode: Mapped[str] = mapped_column(String(16), default="stub")  # live | stub
    name_returned: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_returned: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_summary_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaxRuleSnapshot(Base):
    """Konfigurierbare Steuerregel – fachliche Freigabe vor Prod Pflicht."""

    __tablename__ = "tax_rule_snapshots"
    __table_args__ = (UniqueConstraint("code", "version", name="uq_tax_rule_code_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[str] = mapped_column(String(32), default="1")
    # b2b_at | b2c_at | b2b_eu | b2c_eu_oss | b2b_reverse_charge | third_country | ...
    scenario: Mapped[str] = mapped_column(String(64), index=True)
    customer_type: Mapped[str] = mapped_column(String(8))
    supplier_country: Mapped[str] = mapped_column(String(2), default="AT")
    customer_country: Mapped[str] = mapped_column(String(2))
    vat_rate_bp: Mapped[int] = mapped_column(Integer)  # Basispunkte, 2000 = 20,00 %
    reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False)
    oss_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    display_gross: Mapped[bool] = mapped_column(Boolean, default=True)
    legal_basis_de: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(32), default="draft_needs_review")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Invoice(Base):
    """Rechnung oder Gutschrift – Demo/Simulation, PDF optional später."""

    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("workshop_id", "number", name="uq_invoice_workshop_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    billing_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("billing_accounts.id"), index=True
    )
    subscription_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("subscriptions.id"), nullable=True, index=True
    )
    # invoice | credit_note
    doc_type: Mapped[str] = mapped_column(String(16), default="invoice", index=True)
    number: Mapped[str] = mapped_column(String(64), index=True)
    # draft | issued | paid | void | credited
    status: Mapped[str] = mapped_column(String(32), default="issued", index=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    net_cents: Mapped[int] = mapped_column(Integer, default=0)
    vat_cents: Mapped[int] = mapped_column(Integer, default=0)
    gross_cents: Mapped[int] = mapped_column(Integer, default=0)
    vat_rate_bp: Mapped[int] = mapped_column(Integer, default=2000)
    tax_scenario: Mapped[str] = mapped_column(String(64))
    reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False)
    oss_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    line_items_json: Mapped[str] = mapped_column(Text, default="[]")
    buyer_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    tax_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    notes_de: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Aufbewahrungshinweis (AT typ. 7 Jahre) – nur Metadatum
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConsentRecord(Base):
    """Dokumentierte Zustimmung (AGB, Datenschutz, Widerrufsinfo)."""

    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    billing_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("billing_accounts.id"), index=True
    )
    workshop_id: Mapped[str] = mapped_column(String(36), index=True)
    # terms | privacy | withdrawal | order_confirmation | auto_renewal
    consent_type: Mapped[str] = mapped_column(String(64), index=True)
    version_label: Mapped[str] = mapped_column(String(64))
    text_hash: Mapped[str] = mapped_column(String(64))
    accepted: Mapped[bool] = mapped_column(Boolean, default=True)
    ip_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
