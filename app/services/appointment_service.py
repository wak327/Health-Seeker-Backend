from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import BackgroundTaskRecord, BackgroundTaskStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import DoctorSchedule
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

    def _validate_schedule_for_booking(
        self,
        *,
        schedule_id: Optional[int],
        doctor_id: Optional[int],
        scheduled_time: datetime,
        patient_id: int,
    ) -> tuple[int, DoctorSchedule]:
        if schedule_id is None:
            raise ValueError("A doctor schedule must be supplied")

        schedule = self.session.get(DoctorSchedule, schedule_id)
        if not schedule or not schedule.is_active:
            raise ValueError("Selected schedule is unavailable")

        doctor_user_id = schedule.doctor_profile.user_id if schedule.doctor_profile else None
        if doctor_user_id is None:
            raise ValueError("Doctor schedule is not linked to an active doctor")

        if doctor_id is not None and doctor_user_id != doctor_id:
            raise ValueError("Schedule does not belong to the specified doctor")

        if scheduled_time < datetime.utcnow():
            raise ValueError("Cannot book appointments in the past")

        if scheduled_time < schedule.start_time or scheduled_time > schedule.end_time:
            raise ValueError("Scheduled time is outside the doctor's availability window")

        active_bookings = (
            self.session.query(func.count(Appointment.id))
            .filter(Appointment.schedule_id == schedule.id)
            .filter(Appointment.status != AppointmentStatus.CANCELLED)
            .scalar()
            or 0
        )
        if active_bookings >= schedule.max_patients:
            raise ValueError("Selected schedule is fully booked")

        patient_conflict = (
            self.session.query(Appointment)
            .filter(Appointment.patient_id == patient_id)
            .filter(Appointment.status != AppointmentStatus.CANCELLED)
            .filter(Appointment.scheduled_time == scheduled_time)
            .one_or_none()
        )
        if patient_conflict:
            raise ValueError("You already have an appointment at this time")

        return doctor_user_id, schedule

    def create_appointment(
        self,
        *,
        patient_id: int,
        doctor_id: Optional[int],
        schedule_id: Optional[int],
        scheduled_time: datetime,
        reason: str,
    ) -> Appointment:
        doctor_user_id, schedule = self._validate_schedule_for_booking(
            schedule_id=schedule_id,
            doctor_id=doctor_id,
            scheduled_time=scheduled_time,
            patient_id=patient_id,
        )
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_user_id,
            schedule_id=schedule.id,
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
                "schedule_id": appointment.schedule_id,
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
        diagnosis: Optional[str],
        prescription: Optional[str],
    ) -> Appointment:
        if scheduled_time is not None:
            appointment.scheduled_time = scheduled_time
        if notes is not None:
            appointment.notes = notes
        if diagnosis is not None:
            appointment.diagnosis = diagnosis
        if prescription is not None:
            appointment.prescription = prescription
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
