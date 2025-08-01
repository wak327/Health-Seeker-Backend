from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.appointment import AppointmentStatus
from app.schemas.common import MutableTimestampedModel, ORMModel
from app.schemas.user import UserPublic


class AppointmentBase(ORMModel):
    patient_id: int
    doctor_id: Optional[int]
    scheduled_time: datetime
    reason: str = Field(max_length=255)
    status: AppointmentStatus = AppointmentStatus.PENDING
    notes: Optional[str] = None


class AppointmentCreate(ORMModel):
    patient_id: int
    doctor_id: Optional[int] = None
    scheduled_time: datetime
    reason: str = Field(max_length=255)


class AppointmentUpdate(ORMModel):
    scheduled_time: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class AppointmentPublic(AppointmentBase, MutableTimestampedModel):
    id: int
    patient: Optional[UserPublic] = None
    doctor: Optional[UserPublic] = None
