from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_appointment_service
from app.schemas import appointment as appointment_schema
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=appointment_schema.AppointmentPublic, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_in: appointment_schema.AppointmentCreate,
    service: AppointmentService = Depends(get_appointment_service),
) -> appointment_schema.AppointmentPublic:
    appointment = service.create_appointment(
        patient_id=appointment_in.patient_id,
        doctor_id=appointment_in.doctor_id,
        scheduled_time=appointment_in.scheduled_time,
        reason=appointment_in.reason,
    )
    return appointment


@router.get("/{appointment_id}", response_model=appointment_schema.AppointmentPublic)
def get_appointment(
    appointment_id: int,
    service: AppointmentService = Depends(get_appointment_service),
) -> appointment_schema.AppointmentPublic:
    appointment = service.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment


@router.get("/patients/{patient_id}", response_model=list[appointment_schema.AppointmentPublic])
def list_patient_appointments(
    patient_id: int,
    service: AppointmentService = Depends(get_appointment_service),
) -> list[appointment_schema.AppointmentPublic]:
    return service.list_for_patient(patient_id)


@router.get("/doctors/{doctor_id}", response_model=list[appointment_schema.AppointmentPublic])
def list_doctor_appointments(
    doctor_id: int,
    service: AppointmentService = Depends(get_appointment_service),
) -> list[appointment_schema.AppointmentPublic]:
    return service.list_for_doctor(doctor_id)


@router.patch("/{appointment_id}", response_model=appointment_schema.AppointmentPublic)
def update_appointment(
    appointment_id: int,
    appointment_in: appointment_schema.AppointmentUpdate,
    service: AppointmentService = Depends(get_appointment_service),
) -> appointment_schema.AppointmentPublic:
    appointment = service.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if appointment_in.status is not None:
        appointment = service.update_status(appointment, appointment_in.status)

    if appointment_in.notes is not None or appointment_in.scheduled_time is not None:
        appointment = service.update_details(
            appointment,
            scheduled_time=appointment_in.scheduled_time,
            notes=appointment_in.notes,
        )

    return appointment
