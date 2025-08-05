from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    __table_args__ = (
        CheckConstraint(
            "years_of_experience IS NULL OR years_of_experience >= 0",
            name="ck_doctor_profile_experience_non_negative",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization = Column(String(255), nullable=False)
    license_number = Column(String(100), unique=True)
    years_of_experience = Column(Integer)
    contact_number = Column(String(50))
    bio = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = relationship("User", back_populates="doctor_profile")
    schedules = relationship(
        "DoctorSchedule",
        back_populates="doctor_profile",
        cascade="all, delete-orphan",
    )


class DoctorSchedule(Base):
    __tablename__ = "doctor_schedules"
    __table_args__ = (
        CheckConstraint("start_time < end_time", name="ck_doctor_schedule_time_order"),
        CheckConstraint("max_patients > 0", name="ck_doctor_schedule_max_patients_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    max_patients = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    doctor_profile = relationship("DoctorProfile", back_populates="schedules")
    appointments = relationship("Appointment", back_populates="schedule")
