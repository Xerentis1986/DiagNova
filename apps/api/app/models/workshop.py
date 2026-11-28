"""Phase 08 – Werkstatt (Mandant), Kunden, Aufträge."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Workshop(Base):
    """Mandant / Werkstattprofil. Mandanten-ID kommt serverseitig aus der Sitzung."""

    __tablename__ = "workshops"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), index=True)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="AT")
    vat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Optionales Logo als Data-URL (klein); keine externen Upload-Dienste
    logo_data_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=365)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customers: Mapped[list[Customer]] = relationship(back_populates="workshop")
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates="workshop")


class Customer(Base):
    """Kundendaten – minimale Erhebung, mandantengebunden."""

    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("workshop_id", "email", name="uq_customers_workshop_email"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    anonymized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    workshop: Mapped[Workshop] = relationship(back_populates="customers")
    vehicles: Mapped[list["CustomerVehicleLink"]] = relationship(back_populates="customer")
    work_orders: Mapped[list[WorkOrder]] = relationship(back_populates="customer")


class CustomerVehicleLink(Base):
    """Zuordnung Kunde ↔ Fahrzeug innerhalb einer Werkstatt (Many-to-Many light)."""

    __tablename__ = "customer_vehicles"
    __table_args__ = (
        UniqueConstraint("customer_id", "vehicle_id", name="uq_customer_vehicle"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped[Customer] = relationship(back_populates="vehicles")


class WorkOrder(Base):
    """Werkstattauftrag mit Status, Notizen und Reparaturhinweis."""

    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), ForeignKey("workshops.id"), index=True)
    customer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=True, index=True
    )
    vehicle_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vehicles.id"), nullable=True, index=True
    )
    created_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    repair_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    odometer_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    workshop: Mapped[Workshop] = relationship(back_populates="work_orders")
    customer: Mapped[Customer | None] = relationship(back_populates="work_orders")
