from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_appointment_service,
    get_doctor_service,
    require_doctor,
)
from app.models.user import User
from app.schemas import appointment as appointment_schema
from app.schemas import doctor as doctor_schema
from app.services.appointment_service import AppointmentService
from app.services.doctor_service import DoctorService

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("/me/profile", response_model=doctor_schema.DoctorProfilePublic)
def get_my_profile(
    current_user: User = Depends(require_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> doctor_schema.DoctorProfilePublic:
    profile = doctor_service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return doctor_schema.DoctorProfilePublic.model_validate(profile)


@router.put("/me/profile", response_model=doctor_schema.DoctorProfilePublic)
def upsert_my_profile(
    profile_in: doctor_schema.DoctorProfileUpdate,
    current_user: User = Depends(require_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> doctor_schema.DoctorProfilePublic:
    existing = doctor_service.get_profile_by_user_id(current_user.id)
    if existing:
        updated = doctor_service.update_profile(existing, profile_in)
        return doctor_schema.DoctorProfilePublic.model_validate(updated)

    if profile_in.specialization is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="specialization is required when creating a profile",
        )

    create_data = doctor_schema.DoctorProfileCreate(
        user_id=current_user.id,
        specialization=profile_in.specialization,
        license_number=profile_in.license_number,
        years_of_experience=profile_in.years_of_experience,
        contact_number=profile_in.contact_number,
        bio=profile_in.bio,
    )
    profile = doctor_service.create_profile(create_data)
    return doctor_schema.DoctorProfilePublic.model_validate(profile)


@router.post(
    "/me/schedules",
    response_model=doctor_schema.DoctorSchedulePublic,
    status_code=status.HTTP_201_CREATED,
)
def create_schedule(
    schedule_in: doctor_schema.DoctorScheduleCreate,
    current_user: User = Depends(require_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> doctor_schema.DoctorSchedulePublic:
    profile = doctor_service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create your doctor profile before adding availability",
        )

    try:
        schedule = doctor_service.create_schedule(doctor_profile=profile, schedule_in=schedule_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return doctor_schema.DoctorSchedulePublic.model_validate(schedule)


@router.get("/me/schedules", response_model=list[doctor_schema.DoctorSchedulePublic])
def list_my_schedules(
    current_user: User = Depends(require_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> list[doctor_schema.DoctorSchedulePublic]:
    profile = doctor_service.get_profile_by_user_id(current_user.id)
    if not profile:
        return []
    schedules = doctor_service.list_schedules(doctor_profile=profile, active_only=False, upcoming_only=False)
    return [
        doctor_schema.DoctorSchedulePublic.model_validate(schedule)
        for schedule in schedules
    ]


@router.patch(
    "/me/schedules/{schedule_id}",
    response_model=doctor_schema.DoctorSchedulePublic,
)
def update_schedule(
    schedule_id: int,
    schedule_in: doctor_schema.DoctorScheduleUpdate,
    current_user: User = Depends(require_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> doctor_schema.DoctorSchedulePublic:
    profile = doctor_service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    schedule = doctor_service.get_schedule(schedule_id)
    if not schedule or schedule.doctor_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")

    try:
        schedule = doctor_service.update_schedule(schedule=schedule, schedule_in=schedule_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return doctor_schema.DoctorSchedulePublic.model_validate(schedule)


@router.delete("/me/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(require_doctor),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> None:
    profile = doctor_service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    schedule = doctor_service.get_schedule(schedule_id)
    if not schedule or schedule.doctor_id != profile.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")
    doctor_service.delete_schedule(schedule)


@router.get(
    "/me/appointments",
    response_model=list[appointment_schema.AppointmentPublic],
)
def list_my_appointments(
    current_user: User = Depends(require_doctor),
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> list[appointment_schema.AppointmentPublic]:
    return appointment_service.list_for_doctor(current_user.id)
