from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class DomainEvent(BaseModel):
    name: str
    payload: Dict[str, Any]
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)
