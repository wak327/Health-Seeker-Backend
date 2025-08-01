from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedModel(ORMModel):
    created_at: datetime


class MutableTimestampedModel(TimestampedModel):
    updated_at: datetime
