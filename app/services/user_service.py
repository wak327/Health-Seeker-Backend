from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core import security
from app.models.user import User
from app.schemas import user as user_schema


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_user(self, user_in: user_schema.UserCreate) -> User:
        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            role=user_in.role,
            hashed_password=security.hash_password(user_in.password),
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).one_or_none()

    def get(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    def update(self, user: User, user_in: user_schema.UserUpdate) -> User:
        if user_in.full_name is not None:
            user.full_name = user_in.full_name
        if user_in.password:
            user.hashed_password = security.hash_password(user_in.password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
