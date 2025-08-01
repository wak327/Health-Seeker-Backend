from typing import Optional

from pydantic import EmailStr, Field

from app.models.user import UserRole
from app.schemas.common import MutableTimestampedModel, ORMModel


class UserBase(ORMModel):
    email: EmailStr
    full_name: str
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(ORMModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class UserPublic(UserBase, MutableTimestampedModel):
    id: int
