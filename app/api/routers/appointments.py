from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_appointment_service, get_current_user
from app.schemas import appointment as appointment_schema
from app.services.appointment_service import AppointmentService
from app.models.user import User, UserRole

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=appointment_schema.AppointmentPublic, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_in: appointment_schema.AppointmentCreate,
    service: AppointmentService = Depends(get_appointment_service),
    current_user: User = Depends(get_current_user),
) -> appointment_schema.AppointmentPublic:
    if current_user.role == UserRole.PATIENT:
        patient_id = current_user.id
    elif current_user.role == UserRole.SUPERADMIN:
        if appointment_in.patient_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id is required when booking on behalf of a patient",
            )
        patient_id = appointment_in.patient_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients or superadmins can create appointments",
        )

    try:
        appointment = service.create_appointment(
            patient_id=patient_id,
            doctor_id=appointment_in.doctor_id,
            schedule_id=appointment_in.schedule_id,
            scheduled_time=appointment_in.scheduled_time,
            reason=appointment_in.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return appointment


@router.get("/{appointment_id}", response_model=appointment_schema.AppointmentPublic)
def get_appointment(
    appointment_id: int,
    service: AppointmentService = Depends(get_appointment_service),
    current_user: User = Depends(get_current_user),
) -> appointment_schema.AppointmentPublic:
    appointment = service.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if current_user.role != UserRole.SUPERADMIN and current_user.id not in {
        appointment.patient_id,
        appointment.doctor_id,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return appointment


@router.get("/patients/{patient_id}", response_model=list[appointment_schema.AppointmentPublic])
def list_patient_appointments(
    patient_id: int,
    service: AppointmentService = Depends(get_appointment_service),
    current_user: User = Depends(get_current_user),
) -> list[appointment_schema.AppointmentPublic]:
    if current_user.role != UserRole.SUPERADMIN and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return service.list_for_patient(patient_id)


@router.get("/doctors/{doctor_id}", response_model=list[appointment_schema.AppointmentPublic])
def list_doctor_appointments(
    doctor_id: int,
    service: AppointmentService = Depends(get_appointment_service),
    current_user: User = Depends(get_current_user),
) -> list[appointment_schema.AppointmentPublic]:
    if current_user.role not in {UserRole.SUPERADMIN, UserRole.DOCTOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if current_user.role == UserRole.DOCTOR and current_user.id != doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return service.list_for_doctor(doctor_id)


@router.patch("/{appointment_id}", response_model=appointment_schema.AppointmentPublic)
def update_appointment(
    appointment_id: int,
    appointment_in: appointment_schema.AppointmentUpdate,
    service: AppointmentService = Depends(get_appointment_service),
    current_user: User = Depends(get_current_user),
) -> appointment_schema.AppointmentPublic:
    appointment = service.get(appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if current_user.role not in {UserRole.SUPERADMIN, UserRole.DOCTOR}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors or superadmins can update appointments",
        )
    if current_user.role == UserRole.DOCTOR and appointment.doctor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage your own appointments",
        )

    if appointment_in.scheduled_time is not None and current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmins can reschedule appointments",
        )

    if appointment_in.status is not None:
        appointment = service.update_status(appointment, appointment_in.status)

    if (
        appointment_in.notes is not None
        or appointment_in.scheduled_time is not None
        or appointment_in.diagnosis is not None
        or appointment_in.prescription is not None
    ):
        appointment = service.update_details(
            appointment,
            scheduled_time=appointment_in.scheduled_time,
            notes=appointment_in.notes,
            diagnosis=appointment_in.diagnosis,
            prescription=appointment_in.prescription,
        )

    return appointment
