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

class ImportFieldIssue(BaseModel):
    field: str
    entered_value: str | None = None
    message: str
    suggested_value: str | None = None
    suggested_id: int | None = None
    confidence: str | None = None

class ImportPreviewRow(BaseModel):
    row_number: int
    data: dict
    state: str
    intended_action: str
    errors: list[ImportFieldIssue] = []
    warnings: list[ImportFieldIssue] = []

class ImportPreviewSummary(BaseModel):
    total_rows: int
    valid_rows: int
    warning_rows: int
    error_rows: int
    imported_rows: int = 0
    new_applications: int
    new_visits_existing_application: int

class ImportPreviewResponse(BaseModel):
    import_token: str
    filename: str
    uploaded_at: str
    expires_at: str
    summary: ImportPreviewSummary
    rows: list[ImportPreviewRow]
    options: dict

class ImportCommitRow(BaseModel):
    row_number: int
    resolved_data: dict

class ImportCommitRequest(BaseModel):
    import_token: str
    rows: list[ImportCommitRow]

class ImportCommitFailure(BaseModel):
    row_number: int
    errors: list[ImportFieldIssue]

class ImportCommitResponse(BaseModel):
    success: bool
    imported_rows: int
    created_applications: int
    created_visits: int
    added_to_existing_applications: int
    failed_rows: list[ImportCommitFailure] = []
    remaining_rows: int
