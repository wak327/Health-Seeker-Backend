from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import Settings, get_settings
from app.core.events import event_bus
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.appointment_service import AppointmentService
from app.services.auth_service import AuthService
from app.services.background_task_service import BackgroundTaskService
from app.services.doctor_service import DoctorService
from app.services.event_bus import EventBus
from app.services.lab_result_service import LabResultService
from app.services.patient_service import PatientService
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


def get_doctor_service(
    session: Session = Depends(get_db_session),
) -> DoctorService:
    return DoctorService(session=session)


def get_patient_service(
    session: Session = Depends(get_db_session),
) -> PatientService:
    return PatientService(session=session)


def get_auth_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> AuthService:
    return AuthService(session=session, settings=settings)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().api_v1_prefix}/auth/login",
    auto_error=False,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dependency),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = security.decode_access_token(
            token,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        subject = payload.get("sub")
        if subject is None:
            raise ValueError("Token subject missing")
        user_id = int(subject)
    except (security.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or missing user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required",
        )
    return current_user


def require_doctor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.DOCTOR, UserRole.SUPERADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor privileges required",
        )
    return current_user


def require_patient(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in {UserRole.PATIENT, UserRole.SUPERADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient privileges required",
        )
    return current_user
