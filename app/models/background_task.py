from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class BackgroundTaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class BackgroundTaskRecord(Base):
    __tablename__ = "background_task_records"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    status = Column(
        Enum(BackgroundTaskStatus), nullable=False, default=BackgroundTaskStatus.QUEUED
    )
    appointment_id = Column(
        Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
    )
    external_reference = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    error_message = Column(String(255))

    appointment = relationship("Appointment", back_populates="tasks")
