from __future__ import annotations

from datetime import datetime

from celery.utils.log import get_task_logger

from app.db.session import SessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.background_task import BackgroundTaskRecord, BackgroundTaskStatus
from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(name="app.tasks.appointment_tasks.schedule_appointment_task")
def schedule_appointment_task(appointment_id: int) -> None:
    session = SessionLocal()
    task_record: BackgroundTaskRecord | None = None
    try:
        task_record = (
            session.query(BackgroundTaskRecord)
            .filter(
                BackgroundTaskRecord.appointment_id == appointment_id,
                BackgroundTaskRecord.task_name == "schedule_appointment",
            )
            .order_by(BackgroundTaskRecord.created_at.desc())
            .first()
        )

        if task_record:
            task_record.status = BackgroundTaskStatus.RUNNING
            task_record.updated_at = datetime.utcnow()
            session.add(task_record)
            session.commit()

        appointment = session.get(Appointment, appointment_id)
        if appointment is None:
            if task_record:
                task_record.status = BackgroundTaskStatus.FAILED
                task_record.error_message = "Appointment not found"
                task_record.updated_at = datetime.utcnow()
                session.add(task_record)
                session.commit()
            logger.warning("Appointment %s not found", appointment_id)
            return

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.updated_at = datetime.utcnow()
        session.add(appointment)

        if task_record:
            task_record.status = BackgroundTaskStatus.SUCCEEDED
            task_record.updated_at = datetime.utcnow()
            session.add(task_record)

        session.commit()
        logger.info("Appointment %s confirmed", appointment_id)
    except Exception as exc:  # pragma: no cover - defensive logging
        session.rollback()
        if task_record:
            task_record.status = BackgroundTaskStatus.FAILED
            task_record.error_message = str(exc)
            task_record.updated_at = datetime.utcnow()
            session.add(task_record)
            session.commit()
        logger.exception("Failed to process appointment %s", appointment_id)
        raise
    finally:
        session.close()
