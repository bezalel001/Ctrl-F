from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.models.auth import AuthResponse, LoginRequest
from app.models.user import UserProfile
from app.services.auth_service import AuthenticationError, authenticate_user, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, settings: Annotated[Settings, Depends(get_settings)]) -> AuthResponse:
    try:
        user = authenticate_user(request.email, request.password)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return AuthResponse(access_token=create_access_token(user, settings.jwt_secret), user=user)


@router.get("/me", response_model=UserProfile)
def read_current_user(current_user: Annotated[UserProfile, Depends(get_current_user)]) -> UserProfile:
    return current_user

