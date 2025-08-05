from datetime import datetime
from typing import Optional

from pydantic import Field, FieldValidationInfo, field_validator

from app.schemas.common import MutableTimestampedModel, ORMModel
from app.schemas.user import UserPublic


class DoctorProfileBase(ORMModel):
    specialization: str = Field(max_length=255)
    license_number: Optional[str] = Field(default=None, max_length=100)
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    contact_number: Optional[str] = Field(default=None, max_length=50)
    bio: Optional[str] = None


class DoctorProfileCreate(DoctorProfileBase):
    user_id: int


class DoctorProfileUpdate(ORMModel):
    specialization: Optional[str] = Field(default=None, max_length=255)
    license_number: Optional[str] = Field(default=None, max_length=100)
    years_of_experience: Optional[int] = Field(default=None, ge=0)
    contact_number: Optional[str] = Field(default=None, max_length=50)
    bio: Optional[str] = None


class DoctorProfilePublic(DoctorProfileBase, MutableTimestampedModel):
    id: int
    user: Optional[UserPublic] = None


class DoctorScheduleBase(ORMModel):
    start_time: datetime
    end_time: datetime
    max_patients: int = Field(default=1, ge=1)
    is_active: bool = True

    @field_validator("end_time")
    @classmethod
    def validate_time_window(cls, value: datetime, info: FieldValidationInfo) -> datetime:
        start_time = info.data.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time must be greater than start_time")
        return value


class DoctorScheduleCreate(DoctorScheduleBase):
    pass


class DoctorScheduleUpdate(ORMModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_patients: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None

    @field_validator("end_time")
    @classmethod
    def validate_time_window(cls, value: Optional[datetime], info: FieldValidationInfo) -> Optional[datetime]:
        if value is None:
            return value
        start_time = info.data.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time must be greater than start_time")
        return value


class DoctorSchedulePublic(DoctorScheduleBase, MutableTimestampedModel):
    id: int
    doctor_id: int


class DoctorAvailability(ORMModel):
    doctor: DoctorProfilePublic
    schedules: list[DoctorSchedulePublic]

