from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


PaymentStatus = Literal["Pending", "Partially Paid", "Paid", "Cancelled"]


class BillingBase(BaseModel):
    bank_payout_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    bank_paid_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    bank_payment_status: PaymentStatus = "Pending"
    bank_paid_date: date | None = None
    bank_payment_reference: str | None = None
    executive_payout_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    executive_paid_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    executive_payment_status: PaymentStatus = "Pending"
    executive_paid_date: date | None = None
    executive_payment_reference: str | None = None
    remarks: str | None = None


class BillingCreate(BillingBase):
    case_id: int


class BillingUpdate(BaseModel):
    case_id: int | None = None
    bank_payout_amount: Decimal | None = Field(default=None, ge=0)
    bank_paid_amount: Decimal | None = Field(default=None, ge=0)
    bank_payment_status: PaymentStatus | None = None
    bank_paid_date: date | None = None
    bank_payment_reference: str | None = None
    executive_payout_amount: Decimal | None = Field(default=None, ge=0)
    executive_paid_amount: Decimal | None = Field(default=None, ge=0)
    executive_payment_status: PaymentStatus | None = None
    executive_paid_date: date | None = None
    executive_payment_reference: str | None = None
    remarks: str | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        required_when_supplied = {
            "case_id",
            "bank_payout_amount",
            "bank_paid_amount",
            "bank_payment_status",
            "executive_payout_amount",
            "executive_paid_amount",
            "executive_payment_status",
        }
        for field in required_when_supplied & self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class BillingResponse(BillingBase):
    id: int
    case_id: int
    case_no: str
    los_no: str | None = None
    applicant: str | None = None
    bank: str | None = None
    city: str | None = None
    executive: str | None = None
    gross_margin: Decimal
    bank_balance: Decimal
    executive_balance: Decimal
    expected_gross_margin: Decimal
    realized_cash_margin: Decimal
    created_at: datetime
    updated_at: datetime
    bank_payout_rate_id: int | None = None
    executive_payout_rate_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class BulkBillingRequest(BaseModel):
    case_ids: list[int] | None = Field(default=None, max_length=5000)
    receive_date_from: date | None = None
    receive_date_to: date | None = None
    bank: str | None = None
    city: str | None = None
    executive: str | None = None
    status: str | None = None
    only_without_billing: bool = True

    @model_validator(mode="after")
    def validate_selection(self):
        if self.case_ids is not None and not self.case_ids:
            raise ValueError("case_ids cannot be empty")
        if self.receive_date_from and self.receive_date_to and self.receive_date_to < self.receive_date_from:
            raise ValueError("receive_date_to must be on or after receive_date_from")
        return self


class BulkPreviewRow(BaseModel):
    case_id: int
    case_no: str
    los_no: str | None = None
    applicant: str | None
    bank: str | None
    city: str | None
    location: str | None = None
    executive: str | None
    loan_type: str | None
    product_type: str | None
    bank_rate_status: Literal["MATCHED", "MISSING", "AMBIGUOUS"]
    bank_rate_id: int | None
    bank_payout_amount: Decimal | None
    executive_rate_status: Literal["MATCHED", "MISSING", "AMBIGUOUS"]
    executive_rate_id: int | None
    executive_payout_amount: Decimal | None
    expected_gross_margin: Decimal | None
    existing_billing: bool
    validation_errors: list[str]
    ready: bool


class BulkPreviewSummary(BaseModel):
    selected_cases: int
    ready_cases: int
    missing_bank_rates: int
    missing_executive_rates: int
    ambiguous_rates: int
    existing_billing_records: int


class BulkPreviewResponse(BaseModel):
    rows: list[BulkPreviewRow]
    summary: BulkPreviewSummary


class BulkCreateRequest(BaseModel):
    case_ids: list[int] = Field(min_length=1, max_length=5000)


class BulkCreateResult(BaseModel):
    case_id: int
    case_no: str | None = None
    los_no: str | None = None
    status: Literal["CREATED", "SKIPPED", "ERROR"]
    billing_id: int | None = None
    errors: list[str] = Field(default_factory=list)


class BulkCreateResponse(BaseModel):
    created_count: int
    skipped_count: int
    error_count: int
    results: list[BulkCreateResult]
