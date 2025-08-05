from datetime import date
from typing import Optional

from pydantic import Field

from app.schemas.common import MutableTimestampedModel, ORMModel
from app.schemas.user import UserPublic


class PatientProfileBase(ORMModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(default=None, max_length=20)
    blood_type: Optional[str] = Field(default=None, max_length=5)
    contact_number: Optional[str] = Field(default=None, max_length=50)
    emergency_contact: Optional[str] = Field(default=None, max_length=255)


class PatientProfileCreate(PatientProfileBase):
    user_id: int


class PatientProfileUpdate(ORMModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(default=None, max_length=20)
    blood_type: Optional[str] = Field(default=None, max_length=5)
    contact_number: Optional[str] = Field(default=None, max_length=50)
    emergency_contact: Optional[str] = Field(default=None, max_length=255)


class PatientProfilePublic(PatientProfileBase, MutableTimestampedModel):
    id: int
    user: Optional[UserPublic] = None

