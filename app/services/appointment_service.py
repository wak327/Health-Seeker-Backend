from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import BackgroundTaskRecord, BackgroundTaskStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.services.event_bus import EventBus
from app.tasks import appointment_tasks


class AppointmentService:
    def __init__(self, session: Session, event_bus: EventBus, settings: Settings) -> None:
        self.session = session
        self.event_bus = event_bus
        self.settings = settings

    def _enqueue_background_task(self, appointment: Appointment) -> BackgroundTaskRecord:
        task = BackgroundTaskRecord(
            task_name="schedule_appointment",
            status=BackgroundTaskStatus.QUEUED,
            appointment=appointment,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)

        if self.settings.enable_background_workers:
            appointment_tasks.schedule_appointment_task.delay(appointment.id)

        return task

    def create_appointment(
        self, *, patient_id: int, doctor_id: Optional[int], scheduled_time: datetime, reason: str
    ) -> Appointment:
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            scheduled_time=scheduled_time,
            reason=reason,
            status=AppointmentStatus.PENDING,
        )
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)

        self._enqueue_background_task(appointment)

        self.event_bus.publish(
            "appointment.created",
            {
                "appointment_id": appointment.id,
                "patient_id": appointment.patient_id,
                "doctor_id": appointment.doctor_id,
                "scheduled_time": appointment.scheduled_time.isoformat(),
            },
        )
        return appointment

    def update_status(self, appointment: Appointment, status: AppointmentStatus) -> Appointment:
        appointment.status = status
        appointment.updated_at = datetime.utcnow()
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)

        self.event_bus.publish(
            "appointment.updated",
            {
                "appointment_id": appointment.id,
                "status": appointment.status.value,
            },
        )
        return appointment

    def update_details(
        self,
        appointment: Appointment,
        *,
        scheduled_time: Optional[datetime],
        notes: Optional[str],
    ) -> Appointment:
        if scheduled_time is not None:
            appointment.scheduled_time = scheduled_time
        if notes is not None:
            appointment.notes = notes
        appointment.updated_at = datetime.utcnow()
        self.session.add(appointment)
        self.session.commit()
        self.session.refresh(appointment)
        return appointment

    def get(self, appointment_id: int) -> Optional[Appointment]:
        return self.session.get(Appointment, appointment_id)

    def list_for_patient(self, patient_id: int) -> list[Appointment]:
        return (
            self.session.query(Appointment)
            .filter(Appointment.patient_id == patient_id)
            .order_by(Appointment.scheduled_time.desc())
            .all()
        )

    def list_for_doctor(self, doctor_id: int) -> list[Appointment]:
        return (
            self.session.query(Appointment)
            .filter(Appointment.doctor_id == doctor_id)
            .order_by(Appointment.scheduled_time.desc())
            .all()
        )
