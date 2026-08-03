from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    case_id: int
    case_no: str
    applicant: str | None = None
    executive: str | None = None
    occurred_at: str | None = None
    due_at: str | None = None
    severity: str
