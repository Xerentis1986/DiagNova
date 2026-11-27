"""Phase 09 – Digitale Fahrzeugakte, Sitzungsdetails, Messwertverlauf."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class SessionEcuResult(Base):
    """Pro Sitzung geprüfte Steuergeräte – Grundlage für ehrliche Vorher/Nachher-Vergleiche."""

    __tablename__ = "session_ecu_results"
    __table_args__ = (
        UniqueConstraint("session_id", "ecu_code", name="uq_session_ecu"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("diagnostic_sessions.id"), index=True
    )
    ecu_code: Mapped[str] = mapped_column(String(64), index=True)
    ecu_label_de: Mapped[str] = mapped_column(String(128))
    checked: Mapped[bool] = mapped_column(Boolean, default=True)
    protocol_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address_hex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ok")  # ok | error | no_response
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped[object] = relationship("DiagnosticSession", back_populates="ecu_results")
    dtcs: Mapped[list["SessionDtcResult"]] = relationship(back_populates="ecu_result")


class SessionDtcResult(Base):
    """Beobachtete DTCs einer Sitzung – nie als „behoben“ ohne erneute ECU-Prüfung."""

    __tablename__ = "session_dtc_results"
    __table_args__ = (
        UniqueConstraint("session_id", "ecu_code", "code", "dtc_status", name="uq_session_dtc"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("diagnostic_sessions.id"), index=True
    )
    ecu_result_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("session_ecu_results.id"), nullable=True, index=True
    )
    ecu_code: Mapped[str] = mapped_column(String(64), index=True)
    code: Mapped[str] = mapped_column(String(16), index=True)
    dtc_status: Mapped[str] = mapped_column(String(16))  # stored | pending | permanent
    description_de: Mapped[str] = mapped_column(String(255), default="")
    severity: Mapped[str] = mapped_column(String(16), default="info")

    ecu_result: Mapped[SessionEcuResult | None] = relationship(back_populates="dtcs")


class SessionMeasurementSample(Base):
    """Begrenzte Messwertspeicherung – große Streams werden gekürzt."""

    __tablename__ = "session_measurement_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("diagnostic_sessions.id"), index=True
    )
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), index=True)
    workshop_id: Mapped[str] = mapped_column(String(36), index=True)
    pid: Mapped[int] = mapped_column(Integer, index=True)
    pid_hex: Mapped[str] = mapped_column(String(8))
    name: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32), default="")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    data_source: Mapped[str] = mapped_column(String(16), default="simulated")


class VehicleRecordNote(Base):
    """Manuelle Notizen in der Fahrzeugakte (Zeitstrahl)."""

    __tablename__ = "vehicle_record_notes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workshop_id: Mapped[str] = mapped_column(String(36), index=True)
    vehicle_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicles.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    work_order_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("work_orders.id"), nullable=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("diagnostic_sessions.id"), nullable=True
    )
    note_type: Mapped[str] = mapped_column(String(32), default="note")  # note | service | repair
    body: Mapped[str] = mapped_column(Text)
    odometer_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_example_data: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
