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

    model_config = ConfigDict(from_attributes=True)
