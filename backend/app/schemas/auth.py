from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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
