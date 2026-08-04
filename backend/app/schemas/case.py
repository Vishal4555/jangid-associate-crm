from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CaseBase(BaseModel):
    los_no: Optional[str] = None
    receive_date: Optional[date] = None
    bank: Optional[str] = None
    company_id: Optional[int] = None
    company: Optional[str] = None
    district_id: Optional[int] = None
    district: Optional[str] = None
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


class CaseActivityResponse(BaseModel):
    id: int
    case_id: int
    activity_type: str
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    performed_by_user_id: Optional[int] = None
    performed_by_name: Optional[str] = None
    performed_at: datetime
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str
