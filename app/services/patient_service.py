from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import DoctorProfile, DoctorSchedule, PatientProfile, User, UserRole
from app.schemas import patient as patient_schema


class PatientService:
    def __init__(self, session: Session) -> None:
        self.session = session

    # -- Patient profile management -------------------------------------------------
    def get_profile(self, patient_id: int) -> Optional[PatientProfile]:
        return self.session.get(PatientProfile, patient_id)

    def get_profile_by_user_id(self, user_id: int) -> Optional[PatientProfile]:
        return (
            self.session.query(PatientProfile)
            .filter(PatientProfile.user_id == user_id)
            .one_or_none()
        )

    def create_profile(self, profile_in: patient_schema.PatientProfileCreate) -> PatientProfile:
        user = self.session.get(User, profile_in.user_id)
        if not user:
            raise ValueError("User does not exist")
        if user.role not in {UserRole.PATIENT, UserRole.SUPERADMIN, UserRole.ADMIN}:
            raise ValueError("User must have patient-capable role")
        existing = self.get_profile_by_user_id(profile_in.user_id)
        if existing:
            raise ValueError("Patient profile already exists for this user")

        if user.role != UserRole.PATIENT:
            user.role = UserRole.PATIENT

        profile = PatientProfile(
            user_id=profile_in.user_id,
            date_of_birth=profile_in.date_of_birth,
            gender=profile_in.gender,
            blood_type=profile_in.blood_type,
            contact_number=profile_in.contact_number,
            emergency_contact=profile_in.emergency_contact,
        )
        self.session.add(profile)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def update_profile(
        self, profile: PatientProfile, profile_in: patient_schema.PatientProfileUpdate
    ) -> PatientProfile:
        if profile_in.date_of_birth is not None:
            profile.date_of_birth = profile_in.date_of_birth
        if profile_in.gender is not None:
            profile.gender = profile_in.gender
        if profile_in.blood_type is not None:
            profile.blood_type = profile_in.blood_type
        if profile_in.contact_number is not None:
            profile.contact_number = profile_in.contact_number
        if profile_in.emergency_contact is not None:
            profile.emergency_contact = profile_in.emergency_contact
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    # -- Discover doctors & availability -------------------------------------------
    def list_available_doctor_profiles(
        self,
        *,
        specialization: Optional[str] = None,
    ) -> List[DoctorProfile]:
        query = self.session.query(DoctorProfile).join(DoctorProfile.user).filter(User.is_active.is_(True))
        if specialization:
            query = query.filter(DoctorProfile.specialization.ilike(f"%{specialization}%"))
        return query.order_by(DoctorProfile.specialization.asc(), DoctorProfile.id.asc()).all()

    def get_doctor_profile_by_user_id(self, user_id: int) -> Optional[DoctorProfile]:
        return (
            self.session.query(DoctorProfile)
            .filter(DoctorProfile.user_id == user_id)
            .one_or_none()
        )

    def list_active_schedules(
        self,
        *,
        doctor_profile_id: Optional[int] = None,
        earliest: Optional[datetime] = None,
        latest: Optional[datetime] = None,
    ) -> List[DoctorSchedule]:
        query = (
            self.session.query(DoctorSchedule)
            .join(DoctorSchedule.doctor_profile)
            .join(DoctorProfile.user)
            .filter(DoctorSchedule.is_active.is_(True))
            .filter(User.is_active.is_(True))
        )
        if doctor_profile_id is not None:
            query = query.filter(DoctorSchedule.doctor_id == doctor_profile_id)
        if earliest is not None:
            query = query.filter(DoctorSchedule.end_time >= earliest)
        if latest is not None:
            query = query.filter(DoctorSchedule.start_time <= latest)
        return query.order_by(DoctorSchedule.start_time.asc()).all()


def ensure_patient_user(user: User) -> None:
    if user.role not in {UserRole.PATIENT, UserRole.SUPERADMIN, UserRole.ADMIN}:
        raise ValueError("User does not have permissions for patient operations")
