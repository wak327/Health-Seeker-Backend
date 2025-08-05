from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Appointment, AppointmentStatus, DoctorProfile, DoctorSchedule, User, UserRole
from app.schemas import doctor as doctor_schema


class DoctorService:
    def __init__(self, session: Session) -> None:
        self.session = session

    # -- Doctor profile management -------------------------------------------------
    def get_profile(self, doctor_id: int) -> Optional[DoctorProfile]:
        return self.session.get(DoctorProfile, doctor_id)

    def get_profile_by_user_id(self, user_id: int) -> Optional[DoctorProfile]:
        return (
            self.session.query(DoctorProfile)
            .filter(DoctorProfile.user_id == user_id)
            .one_or_none()
        )

    def list_profiles(self, *, include_inactive_users: bool = False) -> List[DoctorProfile]:
        query = self.session.query(DoctorProfile).join(DoctorProfile.user)
        if not include_inactive_users:
            query = query.filter(User.is_active.is_(True))
        return query.order_by(DoctorProfile.specialization.asc(), DoctorProfile.id.asc()).all()

    def create_profile(self, profile_in: doctor_schema.DoctorProfileCreate) -> DoctorProfile:
        user = self.session.get(User, profile_in.user_id)
        if not user:
            raise ValueError("User does not exist")
        if user.role not in {UserRole.DOCTOR, UserRole.SUPERADMIN, UserRole.ADMIN}:
            raise ValueError("User must have doctor-capable role")
        existing = self.get_profile_by_user_id(profile_in.user_id)
        if existing:
            raise ValueError("Doctor profile already exists for this user")

        if user.role != UserRole.DOCTOR:
            user.role = UserRole.DOCTOR

        profile = DoctorProfile(
            user_id=profile_in.user_id,
            specialization=profile_in.specialization,
            license_number=profile_in.license_number,
            years_of_experience=profile_in.years_of_experience,
            contact_number=profile_in.contact_number,
            bio=profile_in.bio,
        )
        self.session.add(profile)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def update_profile(
        self, profile: DoctorProfile, profile_in: doctor_schema.DoctorProfileUpdate
    ) -> DoctorProfile:
        if profile_in.specialization is not None:
            profile.specialization = profile_in.specialization
        if profile_in.license_number is not None:
            profile.license_number = profile_in.license_number
        if profile_in.years_of_experience is not None:
            profile.years_of_experience = profile_in.years_of_experience
        if profile_in.contact_number is not None:
            profile.contact_number = profile_in.contact_number
        if profile_in.bio is not None:
            profile.bio = profile_in.bio
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    # -- Doctor schedule management -------------------------------------------------
    def _has_schedule_conflict(
        self,
        *,
        doctor_profile_id: int,
        start_time: datetime,
        end_time: datetime,
        schedule_id: Optional[int] = None,
    ) -> bool:
        query = (
            self.session.query(DoctorSchedule)
            .filter(DoctorSchedule.doctor_id == doctor_profile_id)
            .filter(DoctorSchedule.end_time > start_time)
            .filter(DoctorSchedule.start_time < end_time)
        )
        if schedule_id is not None:
            query = query.filter(DoctorSchedule.id != schedule_id)
        return self.session.query(query.exists()).scalar() or False

    def create_schedule(
        self,
        *,
        doctor_profile: DoctorProfile,
        schedule_in: doctor_schema.DoctorScheduleCreate,
    ) -> DoctorSchedule:
        if self._has_schedule_conflict(
            doctor_profile_id=doctor_profile.id,
            start_time=schedule_in.start_time,
            end_time=schedule_in.end_time,
        ):
            raise ValueError("Schedule overlaps with existing availability")

        schedule = DoctorSchedule(
            doctor_id=doctor_profile.id,
            start_time=schedule_in.start_time,
            end_time=schedule_in.end_time,
            max_patients=schedule_in.max_patients,
            is_active=schedule_in.is_active,
        )
        self.session.add(schedule)
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def update_schedule(
        self,
        *,
        schedule: DoctorSchedule,
        schedule_in: doctor_schema.DoctorScheduleUpdate,
    ) -> DoctorSchedule:
        new_start = schedule_in.start_time if schedule_in.start_time is not None else schedule.start_time
        new_end = schedule_in.end_time if schedule_in.end_time is not None else schedule.end_time
        if self._has_schedule_conflict(
            doctor_profile_id=schedule.doctor_id,
            start_time=new_start,
            end_time=new_end,
            schedule_id=schedule.id,
        ):
            raise ValueError("Schedule overlaps with existing availability")

        if schedule_in.start_time is not None:
            schedule.start_time = schedule_in.start_time
        if schedule_in.end_time is not None:
            schedule.end_time = schedule_in.end_time
        if schedule_in.max_patients is not None:
            schedule.max_patients = schedule_in.max_patients
        if schedule_in.is_active is not None:
            schedule.is_active = schedule_in.is_active

        self.session.add(schedule)
        self.session.commit()
        self.session.refresh(schedule)
        return schedule

    def delete_schedule(self, schedule: DoctorSchedule) -> None:
        self.session.delete(schedule)
        self.session.commit()

    def list_schedules(
        self,
        *,
        doctor_profile: DoctorProfile,
        active_only: bool = False,
        upcoming_only: bool = False,
    ) -> List[DoctorSchedule]:
        query = self.session.query(DoctorSchedule).filter(DoctorSchedule.doctor_id == doctor_profile.id)
        if active_only:
            query = query.filter(DoctorSchedule.is_active.is_(True))
        if upcoming_only:
            query = query.filter(DoctorSchedule.end_time >= datetime.utcnow())
        return query.order_by(DoctorSchedule.start_time.asc()).all()

    def get_schedule(self, schedule_id: int) -> Optional[DoctorSchedule]:
        return self.session.get(DoctorSchedule, schedule_id)

    def is_schedule_capacity_available(self, schedule: DoctorSchedule) -> bool:
        booked_count = (
            self.session.query(func.count(Appointment.id))
            .filter(Appointment.schedule_id == schedule.id)
            .filter(Appointment.status != AppointmentStatus.CANCELLED)
            .scalar()
            or 0
        )
        return booked_count < schedule.max_patients


def ensure_doctor_user(user: User) -> None:
    if user.role not in {UserRole.DOCTOR, UserRole.ADMIN, UserRole.SUPERADMIN}:
        raise ValueError("User does not have permissions for doctor operations")

