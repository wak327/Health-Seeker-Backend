from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    schedule_id = Column(Integer, ForeignKey("doctor_schedules.id", ondelete="SET NULL"))
    scheduled_time = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(
        Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.PENDING
    )
    notes = Column(Text)
    diagnosis = Column(Text)
    prescription = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    patient = relationship(
        "User", foreign_keys=[patient_id], back_populates="patient_appointments"
    )
    doctor = relationship(
        "User", foreign_keys=[doctor_id], back_populates="doctor_appointments"
    )
    tasks = relationship("BackgroundTaskRecord", back_populates="appointment")
    schedule = relationship("DoctorSchedule", back_populates="appointments")
