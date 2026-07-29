from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


ExecutiveStatus = Literal["Active", "Inactive"]


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class BankBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)


class BankCreate(BankBase):
    pass


class BankUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)


class BankResponse(BankBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BankPageResponse(PaginationMeta):
    items: list[BankResponse]


class BranchBase(BaseModel):
    bank_id: int
    name: str = Field(min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    bank_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)


class BranchResponse(BranchBase):
    id: int
    bank_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BranchPageResponse(PaginationMeta):
    items: list[BranchResponse]


class ExecutiveBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(default=None, max_length=20)
    status: ExecutiveStatus = "Active"


class ExecutiveCreate(ExecutiveBase):
    pass


class ExecutiveUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(default=None, max_length=20)
    status: Optional[ExecutiveStatus] = None


class ExecutiveResponse(ExecutiveBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutivePageResponse(PaginationMeta):
    items: list[ExecutiveResponse]


class LoanTypeBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)


class LoanTypeCreate(LoanTypeBase):
    pass


class LoanTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)


class LoanTypeResponse(LoanTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanTypePageResponse(PaginationMeta):
    items: list[LoanTypeResponse]


class ProductTypeBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)


class ProductTypeCreate(ProductTypeBase):
    pass


class ProductTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)


class ProductTypeResponse(ProductTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductTypePageResponse(PaginationMeta):
    items: list[ProductTypeResponse]