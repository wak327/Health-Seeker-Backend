from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_appointment_service,
    get_patient_service,
    require_patient,
)
from app.models.user import User
from app.schemas import appointment as appointment_schema
from app.schemas import doctor as doctor_schema
from app.schemas import patient as patient_schema
from app.services.appointment_service import AppointmentService
from app.services.patient_service import PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/me/profile", response_model=patient_schema.PatientProfilePublic)
def get_my_profile(
    current_user: User = Depends(require_patient),
    patient_service: PatientService = Depends(get_patient_service),
) -> patient_schema.PatientProfilePublic:
    profile = patient_service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/me/profile", response_model=patient_schema.PatientProfilePublic)
def upsert_my_profile(
    profile_in: patient_schema.PatientProfileUpdate,
    current_user: User = Depends(require_patient),
    patient_service: PatientService = Depends(get_patient_service),
) -> patient_schema.PatientProfilePublic:
    profile = patient_service.get_profile_by_user_id(current_user.id)
    if profile:
        return patient_service.update_profile(profile, profile_in)

    create_data = patient_schema.PatientProfileCreate(
        user_id=current_user.id,
        **profile_in.model_dump(exclude_unset=True),
    )
    return patient_service.create_profile(create_data)


@router.get("/doctors", response_model=list[doctor_schema.DoctorAvailability])
def list_available_doctors(
    current_user: User = Depends(require_patient),
    patient_service: PatientService = Depends(get_patient_service),
    specialization: Optional[str] = Query(default=None, description="Filter by specialization"),
    earliest: Optional[datetime] = Query(default=None, description="Earliest schedule start"),
    latest: Optional[datetime] = Query(default=None, description="Latest schedule end"),
) -> list[doctor_schema.DoctorAvailability]:
    doctors = patient_service.list_available_doctor_profiles(specialization=specialization)
    effective_earliest = earliest or datetime.utcnow()
    availability: list[doctor_schema.DoctorAvailability] = []

    for profile in doctors:
        schedules = patient_service.list_active_schedules(
            doctor_profile_id=profile.id,
            earliest=effective_earliest,
            latest=latest,
        )
        if not schedules:
            continue
        availability.append(
            doctor_schema.DoctorAvailability(
                doctor=doctor_schema.DoctorProfilePublic.model_validate(profile),
                schedules=[
                    doctor_schema.DoctorSchedulePublic.model_validate(schedule)
                    for schedule in schedules
                ],
            )
        )

    return availability


@router.get(
    "/doctors/{doctor_user_id}/schedules",
    response_model=list[doctor_schema.DoctorSchedulePublic],
)
def list_doctor_schedules(
    doctor_user_id: int,
    current_user: User = Depends(require_patient),
    patient_service: PatientService = Depends(get_patient_service),
) -> list[doctor_schema.DoctorSchedulePublic]:
    profile = patient_service.get_doctor_profile_by_user_id(doctor_user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    schedules = patient_service.list_active_schedules(
        doctor_profile_id=profile.id,
        earliest=datetime.utcnow(),
    )
    return [
        doctor_schema.DoctorSchedulePublic.model_validate(schedule)
        for schedule in schedules
    ]


@router.get(
    "/me/appointments",
    response_model=list[appointment_schema.AppointmentPublic],
)
def list_my_appointments(
    current_user: User = Depends(require_patient),
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> list[appointment_schema.AppointmentPublic]:
    return appointment_service.list_for_patient(current_user.id)
