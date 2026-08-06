from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

VisitType = Literal["Residence", "Office", "Permanent", "Business", "Other"]
VisitStatus = Literal["Pending", "Positive", "Negative"]


class CaseVisitBase(BaseModel):
    visit_type: VisitType = "Residence"
    address: str | None = None
    district_id: int | None = None
    district: str | None = None
    city: str | None = None
    landmark: str | None = None
    executive: str | None = None
    status: VisitStatus = "Pending"
    negative_reason: str | None = None
    receive_date: date | None = None
    remarks: str | None = None
    next_follow_up_at: datetime | None = None
    follow_up_note: str | None = None


class CaseVisitCreate(CaseVisitBase):
    pass


class CaseVisitUpdate(BaseModel):
    visit_type: VisitType | None = None
    address: str | None = None
    district_id: int | None = None
    city: str | None = None
    landmark: str | None = None
    executive: str | None = None
    status: VisitStatus | None = None
    negative_reason: str | None = None
    receive_date: date | None = None
    remarks: str | None = None
    next_follow_up_at: datetime | None = None
    follow_up_note: str | None = None


class CaseVisitResponse(CaseVisitBase):
    id: int
    case_id: int
    closed_date: date | None
    tat_days: int | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int | None
    updated_by_user_id: int | None
    model_config = ConfigDict(from_attributes=True)


class CaseVisitListRow(BaseModel):
    visit_id: int
    case_id: int
    visit_type: VisitType
    los_no: str | None = None
    company_id: int | None = None
    company: str | None = None
    bank: str | None = None
    applicant: str | None = None
    mobile: str | None = None
    loan_type: str | None = None
    receive_date: date | None = None
    closed_date: date | None = None
    tat_days: int | None = None
    address: str | None = None
    district_id: int | None = None
    district: str | None = None
    city: str | None = None
    landmark: str | None = None
    executive: str | None = None
    status: VisitStatus
    negative_reason: str | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class CaseVisitListResponse(BaseModel):
    items: list[CaseVisitListRow]
    total: int
    page: int
    page_size: int
