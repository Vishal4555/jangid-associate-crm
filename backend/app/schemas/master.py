from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


ExecutiveStatus = Literal["Active", "Inactive"]
SourceType = Literal["WhatsApp", "Email", "Both", "Other"]


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


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)
    source_type: SourceType = "Other"
    contact_person: Optional[str] = Field(default=None, max_length=200)
    email: Optional[EmailStr] = None
    mobile: Optional[str] = Field(default=None, max_length=20)
    is_active: bool = True
    remarks: Optional[str] = None


class CompanyCreate(CompanyBase): pass
class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, max_length=50)
    source_type: Optional[SourceType] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CompanyPageResponse(PaginationMeta): items: list[CompanyResponse]


class CompanyBankBase(BaseModel):
    company_id: int
    bank_id: int
    is_active: bool = True
    remarks: Optional[str] = None


class CompanyBankCreate(CompanyBankBase): pass
class CompanyBankUpdate(BaseModel):
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class CompanyBankResponse(CompanyBankBase):
    id: int
    company_name: str
    bank_name: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CompanyBankPageResponse(PaginationMeta): items: list[CompanyBankResponse]


class CompanyBankBulkCreate(BaseModel):
    company_id: int
    bank_ids: list[int] = Field(min_length=1, max_length=10000)
    remarks: Optional[str] = None


class CompanyBankBulkResponse(BaseModel):
    created_count: int
    reactivated_count: int
    skipped_count: int
    items: list[CompanyBankResponse]


class DistrictBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    state: str = Field(default="Rajasthan", max_length=100)
    is_active: bool = True


class DistrictCreate(DistrictBase): pass
class DistrictUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class DistrictResponse(DistrictBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DistrictPageResponse(PaginationMeta): items: list[DistrictResponse]
