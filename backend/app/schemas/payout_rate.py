from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class RateBase(BaseModel):
    city: str | None = None
    loan_type: str | None = None
    product_type: str | None = None
    payout_rate: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    effective_from: date
    effective_to: date | None = None
    is_active: bool = True
    remarks: str | None = None

    @field_validator("city", "loan_type", "product_type", "remarks", mode="before")
    @classmethod
    def trim_optional(cls, value):
        return clean(value) if isinstance(value, str) or value is None else value

    @model_validator(mode="after")
    def dates_are_ordered(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to must be on or after effective_from")
        return self


class BankRateCreate(RateBase):
    bank_id: int
    company_id: int | None = None
    district_id: int | None = None
    state: str | None = "Rajasthan"

    @field_validator("state", mode="before")
    @classmethod
    def trim_state(cls, value):
        return clean(value) if isinstance(value, str) or value is None else value


class BankRateBulkCreate(RateBase):
    company_id: int
    bank_ids: list[int] = Field(min_length=1, max_length=10000)
    district_id: int
    state: str | None = "Rajasthan"

    @field_validator("state", mode="before")
    @classmethod
    def trim_state(cls, value):
        return clean(value) if isinstance(value, str) or value is None else value


class ExecutiveRateCreate(RateBase):
    executive_id: int
    bank_id: int | None = None


class BankRateUpdate(BankRateCreate):
    pass


class ExecutiveRateUpdate(ExecutiveRateCreate):
    pass


class RateResponseBase(RateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int | None
    updated_by_user_id: int | None
    model_config = ConfigDict(from_attributes=True)


class BankRateResponse(RateResponseBase):
    bank_id: int
    bank_name: str
    company_id: int | None
    company_name: str | None
    district_id: int | None
    district_name: str | None
    state: str | None


class BankRateBulkResponse(BaseModel):
    created_count: int
    failed_count: int
    items: list[BankRateResponse]
    errors: list[str]


class ExecutiveRateResponse(RateResponseBase):
    executive_id: int
    executive_name: str
    bank_id: int | None
    bank_name: str | None


class RateImportRow(BaseModel):
    row_number: int
    bank: str | None = None
    executive: str | None = None
    company: str | None = None
    district: str | None = None
    state: str | None = None
    city: str | None = None
    location: str | None = None
    loan_type: str | None = None
    product_type: str | None = None
    payout_rate: Decimal | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    active: bool = True
    remarks: str | None = None


class RateImportRequest(BaseModel):
    rows: list[RateImportRow] = Field(min_length=1, max_length=5000)
    confirm: bool = False


class RateImportResultRow(BaseModel):
    row_number: int
    valid: bool
    errors: list[str]


class RateImportResponse(BaseModel):
    valid_count: int
    invalid_count: int
    imported_count: int
    rows: list[RateImportResultRow]


RateKind = Literal["bank", "executive"]
