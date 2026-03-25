from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from api.services.auth import AuthService


def build_auth_router(auth_service: AuthService) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post(
        "/register",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
        summary="注册用户",
        description="创建新用户账号，并将加密后的密码写入 SQLite。",
    )
    def register(request: UserRegisterRequest) -> UserResponse:
        try:
            user = auth_service.register_user(request.username, request.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return UserResponse(**user)

    @router.post(
        "/login",
        response_model=TokenResponse,
        summary="用户登录",
        description="校验用户名和密码，成功后返回 bearer token。",
    )
    def login(request: UserLoginRequest) -> TokenResponse:
        try:
            token_data = auth_service.login_user(request.username, request.password)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return TokenResponse(**token_data)

    return router
