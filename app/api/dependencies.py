from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.events import event_bus
from app.db.session import get_db
from app.services.appointment_service import AppointmentService
from app.services.background_task_service import BackgroundTaskService
from app.services.event_bus import EventBus
from app.services.lab_result_service import LabResultService
from app.services.user_service import UserService


def get_settings_dependency() -> Settings:
    return get_settings()


def get_event_bus() -> EventBus:
    return event_bus


def get_db_session() -> Session:
    yield from get_db()


def get_user_service(
    session: Session = Depends(get_db_session),
) -> UserService:
    return UserService(session=session)


def get_appointment_service(
    session: Session = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    settings: Settings = Depends(get_settings_dependency),
) -> AppointmentService:
    return AppointmentService(session=session, event_bus=event_bus, settings=settings)


def get_lab_result_service(
    session: Session = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
) -> LabResultService:
    return LabResultService(session=session, event_bus=event_bus)


def get_background_task_service(
    session: Session = Depends(get_db_session),
) -> BackgroundTaskService:
    return BackgroundTaskService(session=session)
