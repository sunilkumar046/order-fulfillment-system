from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )
    role: str = Field(
        default="Customer",
        min_length=3,
        max_length=50,
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        min_length=10,
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=72,
    )


class RoleResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    role: RoleResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)