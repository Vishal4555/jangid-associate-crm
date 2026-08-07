from pydantic import BaseModel

class CaseImportError(BaseModel):
    row: int
    field: str
    value: str | None = None
    message: str

class CaseImportResponse(BaseModel):
    success: bool
    created_applications: int = 0
    created_visits: int = 0
    updated_existing_applications: int = 0
    errors: list[CaseImportError] = []
