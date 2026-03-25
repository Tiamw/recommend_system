from __future__ import annotations

from pydantic import BaseModel, Field


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名，需保持唯一。")
    password: str = Field(..., min_length=6, max_length=128, description="登录密码。")


class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="已注册用户名。")
    password: str = Field(..., min_length=6, max_length=128, description="登录密码。")


class UserResponse(BaseModel):
    id: int = Field(..., description="用户 ID。")
    username: str = Field(..., description="用户名。")
    created_at: str = Field(..., description="创建时间。")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT 访问令牌。")
    token_type: str = Field(..., description="令牌类型，固定为 bearer。")
    user: UserResponse = Field(..., description="当前登录用户信息。")


class CurrentUser(BaseModel):
    id: int = Field(..., description="当前登录用户 ID。")
    username: str = Field(..., description="当前登录用户名。")
