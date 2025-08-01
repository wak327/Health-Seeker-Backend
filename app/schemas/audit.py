from datetime import datetime
from typing import Any, Dict

from app.schemas.common import ORMModel


class AuditLogPublic(ORMModel):
    id: int
    event_name: str
    payload: Dict[str, Any]
    created_at: datetime
