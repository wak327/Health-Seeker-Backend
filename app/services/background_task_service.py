from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.background_task import BackgroundTaskRecord


class BackgroundTaskService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_appointment(self, appointment_id: int) -> List[BackgroundTaskRecord]:
        return (
            self.session.query(BackgroundTaskRecord)
            .filter(BackgroundTaskRecord.appointment_id == appointment_id)
            .order_by(BackgroundTaskRecord.created_at.desc())
            .all()
        )

    def get(self, task_id: int) -> Optional[BackgroundTaskRecord]:
        return self.session.get(BackgroundTaskRecord, task_id)
