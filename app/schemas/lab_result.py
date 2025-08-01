from datetime import datetime
from typing import Any, Dict

from pydantic import Field

from app.schemas.common import ORMModel, TimestampedModel


class LabResultBase(ORMModel):
    patient_id: int
    test_name: str = Field(max_length=255)
    result_data: Dict[str, Any]
    recorded_at: datetime


class LabResultCreate(LabResultBase):
    pass


class LabResultPublic(LabResultBase, TimestampedModel):
    id: int
