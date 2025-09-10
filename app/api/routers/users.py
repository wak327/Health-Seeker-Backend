from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_user_service, require_superadmin
from app.models.user import User, UserRole
from app.schemas import user as user_schema
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/",
    response_model=user_schema.UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_in: user_schema.UserCreate,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_superadmin),
) -> user_schema.UserPublic:
    existing = service.get_by_email(user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = service.create_user(user_in)
    return user  # FastAPI handles to schema


@router.get("/{user_id}", response_model=user_schema.UserPublic)
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
) -> user_schema.UserPublic:
    user = service.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.role != UserRole.SUPERADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return user


@router.patch("/{user_id}", response_model=user_schema.UserPublic)
def update_user(
    user_id: int,
    user_in: user_schema.UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user),
) -> user_schema.UserPublic:
    user = service.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if current_user.role != UserRole.SUPERADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    updated = service.update(user, user_in)
    return updated
