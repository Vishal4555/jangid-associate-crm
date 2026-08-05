from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str
    module: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class UserPermissionsResponse(BaseModel):
    user_id: int
    permission_codes: list[str]


class UserPermissionsUpdate(BaseModel):
    permission_codes: list[str]
