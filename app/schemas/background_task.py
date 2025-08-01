from typing import Optional

from app.models.background_task import BackgroundTaskStatus
from app.schemas.common import MutableTimestampedModel, ORMModel


class BackgroundTaskBase(ORMModel):
    task_name: str
    status: BackgroundTaskStatus
    appointment_id: Optional[int]
    external_reference: Optional[str]
    error_message: Optional[str]


class BackgroundTaskPublic(BackgroundTaskBase, MutableTimestampedModel):
    id: int
