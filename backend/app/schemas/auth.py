from datetime import datetime
from typing import Literal

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


UserRole = Literal["Admin", "Manager", "Executive"]


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    mobile: str = Field(min_length=7, max_length=20)
    password: str = Field(min_length=12, max_length=128)
    role: UserRole = "Executive"
    is_active: bool = True
    executive_id: int | None = None
    @field_validator('full_name', 'username', 'mobile', mode='before')
    @classmethod
    def trim_text(cls, value: str):
        return value.strip() if isinstance(value, str) else value

    @field_validator('email', mode='before')
    @classmethod
    def normalize_email(cls, value: str):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, value: str):
        normalized = ''.join(value.split())
        if not (len(normalized) == 10 and normalized.isdigit() and normalized[0] in '6789'): raise ValueError('Must be a valid 10-digit Indian mobile number')
        return normalized

    @field_validator('password')
    @classmethod
    def validate_password(cls, value: str):
        if not (re.search(r'[A-Z]', value) and re.search(r'[a-z]', value) and re.search(r'\d', value) and re.search(r'[^A-Za-z0-9]', value)): raise ValueError('Must include uppercase, lowercase, number, and special character')
        return value

    @model_validator(mode="after")
    def validate_executive_link(self):
        if self.role == "Executive" and self.executive_id is None:
            raise ValueError("Executive users must be linked to an Executive Master record")
        if self.role != "Executive" and self.executive_id is not None:
            raise ValueError("Only Executive users can have an Executive link")
        return self


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: EmailStr
    mobile: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None
    executive_id: int | None
    executive_name: str | None
    permissions: list[str]
    active_session: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    username: str | None = Field(default=None, min_length=3, max_length=100)
    email: EmailStr | None = None
    mobile: str | None = Field(default=None, max_length=20)
    role: UserRole | None = None
    is_active: bool | None = None
    executive_id: int | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordReset(BaseModel):
    password: str = Field(min_length=12, max_length=128)
