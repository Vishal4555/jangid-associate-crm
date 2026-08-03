from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CaseBase(BaseModel):
    receive_date: Optional[date] = None
    bank: Optional[str] = None
    branch: Optional[str] = None
    loan_type: Optional[str] = None
    applicant: Optional[str] = None
    product_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    mobile: Optional[str] = None
    executive: Optional[str] = None
    status: Optional[str] = None
    negative_reason: Optional[str] = None
    landmark: Optional[str] = None
    remarks: Optional[str] = None
    next_follow_up_at: Optional[datetime] = None
    follow_up_note: Optional[str] = None


class CaseCreate(CaseBase):
    case_no: str


class CaseUpdate(CaseBase):
    case_no: Optional[str] = None
    closed_date: Optional[date] = None


class CaseResponse(CaseBase):
    id: int
    case_no: str
    closed_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
