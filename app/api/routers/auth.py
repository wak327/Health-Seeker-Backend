from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_auth_service
from app.schemas import auth as auth_schema
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=auth_schema.Token)
def login(
    credentials: auth_schema.LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> auth_schema.Token:
    user = auth_service.authenticate(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = auth_service.create_access_token(user=user)
    token_user = auth_schema.TokenUser(
        id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
        is_active=user.is_active,
        issued_at=datetime.now(timezone.utc),
    )
    return auth_schema.Token(access_token=access_token, user=token_user)
