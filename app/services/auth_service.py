from __future__ import annotations

from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core import security
from app.models.user import User


class AuthService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.session.query(User).filter(User.email == email).one_or_none()
        if not user:
            return None
        if not user.is_active:
            return None
        if not security.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, *, user: User, expires_minutes: Optional[int] = None) -> str:
        expires_delta = None
        if expires_minutes is not None:
            expires_delta = timedelta(minutes=expires_minutes)
        return security.create_access_token(
            subject=user.id,
            secret_key=self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
            expires_delta=expires_delta,
            default_expiry_minutes=self.settings.access_token_expire_minutes,
        )

