from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class ReportMetadata(BaseModel):
    state: str
    contains_draft: bool
    contains_finalized: bool
    finalized_months: list[str] = []
    draft_months: list[str] = []
    generated_at: datetime
    limitations: list[str] = []


class CompanyBillingReportRow(BaseModel):
    date: date
    los: str | None
    bank: str | None
    visit_type: str | None
    applicant: str | None
    address: str | None
    dist: str | None
    city: str | None
    mobile_number: str | None
    executive: str | None
    status: str
    executive_rate: Decimal | None
    executive_rate_status: str
    company_rate: Decimal | None
    company_rate_status: str
    payment_status: str


class CompanyBillingReport(BaseModel):
    items: list[CompanyBillingReportRow]
    totals: dict
    applied_filters: dict
    metadata: ReportMetadata


class ExecutiveBankSummaryRow(BaseModel):
    executive: str
    bank_finance_company: str
    total_cases_visits: int
    pending: int
    positive: int
    negative: int
    executive_rate_total: Decimal | None
    rate_status: str
    details: list["ExecutiveVisitDetail"] = []


class ExecutiveVisitDetail(BaseModel):
    date: date
    los: str | None
    applicant: str | None
    address: str | None
    mobile: str | None
    visit_type: str | None
    company: str | None
    bank: str | None
    district: str | None
    city: str | None
    status: str
    executive_rate: Decimal | None
    executive_rate_status: str


class ExecutiveSummaryRow(BaseModel):
    executive: str
    total_visits: int
    pending: int
    positive: int
    negative: int
    total_payment: Decimal | None
    rate_status: str


class ExecutivePerformanceReport(BaseModel):
    items: list[ExecutiveBankSummaryRow]
    executive_summary: list[ExecutiveSummaryRow]
    totals: dict
    applied_filters: dict
    metadata: ReportMetadata


ExecutiveBankSummaryRow.model_rebuild()
