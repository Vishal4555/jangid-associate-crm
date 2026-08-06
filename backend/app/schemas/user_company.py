from pydantic import BaseModel

from app.schemas.master import CompanyResponse


class UserCompaniesUpdate(BaseModel):
    company_ids: list[int]


class AssignedCompaniesResponse(BaseModel):
    all_companies: bool
    companies: list[CompanyResponse]
