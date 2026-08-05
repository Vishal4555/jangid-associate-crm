from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

RateStatus = Literal["MATCHED", "MISSING", "AMBIGUOUS"]
RegisterStatus = Literal["Pending", "Partially Paid", "Paid", "Cancelled"]


class ExecutiveMonthlyRow(BaseModel):
    executive_id: int | None
    executive: str
    rate: Decimal | None
    rate_display: str
    bank_counts: dict[str, int]
    total_points: int
    gross_payment: Decimal | None
    advance: Decimal
    net_payment: Decimal | None
    paid: Decimal
    balance: Decimal | None
    payment_status: RegisterStatus
    rate_status: RateStatus
    register_id: int | None
    is_finalized: bool
    payment_date: date | None = None
    payment_reference: str | None = None
    remarks: str | None = None
    snapshot_revision: int | None = None


class BankMonthlyRow(BaseModel):
    case_id: int | None
    visit_id: int | None = None
    visit_type: str | None = None
    date: date
    company: str | None
    bank: str | None
    los_no: str | None
    name: str | None
    address: str | None
    city: str | None
    district: str | None
    mobile: str | None
    status: str
    remark: str | None
    rate: Decimal | None
    rate_status: RateStatus
    bank_rate_id: int | None = None


class MonthlySummary(BaseModel):
    total_cases: int
    billable_cases: int
    missing_executive_rates: int
    missing_bank_rates: int
    ambiguous_rates: int
    total_executive_payment: Decimal
    total_bank_billing: Decimal


class MonthlyBillingResponse(BaseModel):
    month: str
    executive_billing: list[ExecutiveMonthlyRow]
    bank_billing: list[BankMonthlyRow]
    summary: MonthlySummary
    month_status: "MonthStatusResponse"


class PaymentRegisterUpdate(BaseModel):
    billing_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    executive_id: int
    advance_amount: Decimal = Field(default=Decimal("0"), ge=0)
    paid_amount: Decimal = Field(default=Decimal("0"), ge=0)
    payment_date: date | None = None
    payment_reference: str | None = None
    remarks: str | None = None
    finalize: bool = False
    regenerate: bool = False


class PaymentRegisterResponse(BaseModel):
    id: int
    billing_month: date
    executive_id: int
    executive: str
    gross_payment: Decimal
    advance_amount: Decimal
    net_payment: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    status: RegisterStatus
    payment_date: date | None
    payment_reference: str | None
    remarks: str | None
    is_finalized: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MonthStatusResponse(BaseModel):
    month: str
    status: Literal["DRAFT", "FINALIZED", "REOPENED"]
    revision_number: int = 0
    finalized_at: datetime | None = None
    reopened_at: datetime | None = None
    notes: str | None = None


class FinalizeMonthRequest(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    notes: str | None = None


class ReopenMonthRequest(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    reason: str = Field(min_length=1)


class RegenerateMonthRequest(BaseModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    confirm: bool


class BankPaymentUpdate(BaseModel):
    billing_month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    bank: str
    company: str = ""
    district: str = ""
    city: str = ""
    received_amount: Decimal = Field(ge=0)
    status: RegisterStatus | None = None
    payment_date: date | None = None
    payment_reference: str | None = None
    remarks: str | None = None


class BankPaymentResponse(BaseModel):
    id: int
    billing_month: date
    bank: str
    company: str
    district: str
    city: str
    billed_amount: Decimal
    received_amount: Decimal
    balance_amount: Decimal
    status: RegisterStatus
    payment_date: date | None
    payment_reference: str | None
    remarks: str | None
    is_finalized: bool
    model_config = ConfigDict(from_attributes=True)


class BillingDashboardResponse(BaseModel):
    month: str
    month_status: MonthStatusResponse
    total_bank_billing: Decimal
    bank_received: Decimal
    bank_outstanding: Decimal
    total_executive_payout: Decimal
    executive_paid: Decimal
    executive_outstanding: Decimal
    expected_gross_margin: Decimal
    realized_cash_margin: Decimal
    bank_summary: list[BankPaymentResponse]
    executive_summary: list[ExecutiveMonthlyRow]


MonthlyBillingResponse.model_rebuild()
