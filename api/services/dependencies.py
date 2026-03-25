from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.schemas.auth import CurrentUser
from api.services.auth import AuthService


bearer_scheme = HTTPBearer(auto_error=False)


def build_current_user_dependency(auth_service: AuthService):
    def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> CurrentUser:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token.",
            )

        try:
            user = auth_service.get_current_user_from_token(credentials.credentials)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        return CurrentUser(**user)

    return get_current_user
