from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.models.user import UserProfile
from app.services.auth_service import AuthenticationError, resolve_user_from_token
from app.storage.database import get_session

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserProfile:
    if credentials is None:
        raise _unauthorized()

    try:
        return resolve_user_from_token(credentials.credentials, settings.jwt_secret)
    except AuthenticationError as exc:
        raise _unauthorized() from exc


def require_permission(permission: str):
    def dependency(current_user: Annotated[UserProfile, Depends(get_current_user)]) -> UserProfile:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission",
            )

        return current_user

    return dependency


SessionDep = Annotated[Session, Depends(get_session)]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
