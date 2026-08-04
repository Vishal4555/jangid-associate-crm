from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.security import require_roles
from app.db.database import get_db
from app.models.user import User
from app.models.master import Bank, Company, CompanyBank, District
from app.schemas.master import (
    BankCreate,
    BankPageResponse,
    BankResponse,
    BankUpdate,
    BranchCreate,
    BranchPageResponse,
    BranchResponse,
    BranchUpdate,
    ExecutiveCreate,
    ExecutivePageResponse,
    ExecutiveResponse,
    ExecutiveStatus,
    ExecutiveUpdate,
    LoanTypeCreate,
    LoanTypePageResponse,
    LoanTypeResponse,
    LoanTypeUpdate,
    ProductTypeCreate,
    ProductTypePageResponse,
    ProductTypeResponse,
    ProductTypeUpdate,
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanyPageResponse,
    CompanyBankCreate, CompanyBankUpdate, CompanyBankResponse, CompanyBankPageResponse,
    CompanyBankBulkCreate, CompanyBankBulkResponse,
    DistrictCreate, DistrictUpdate, DistrictResponse, DistrictPageResponse,
)
from app.services.masters_service import (
    create_bank,
    create_branch,
    create_executive,
    create_loan_type,
    create_product_type,
    delete_bank,
    delete_branch,
    delete_executive,
    delete_loan_type,
    delete_product_type,
    get_bank,
    get_branch,
    get_executive,
    get_loan_type,
    get_product_type,
    list_banks,
    list_branches,
    list_executives,
    list_loan_types,
    list_product_types,
    update_bank,
    update_branch,
    update_executive,
    update_loan_type,
    update_product_type,
)


router = APIRouter(prefix="/masters", tags=["masters"])
read_access = Depends(require_roles("Admin", "Manager"))
write_access = Depends(require_roles("Admin"))


@router.get("/banks", response_model=BankPageResponse)
def get_banks(
    db: Session = Depends(get_db),
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
    all_items: bool = Query(False, alias="all"),
    _: User = read_access,
):
    return list_banks(db, search=search, page=page, page_size=page_size, all_items=all_items)


@router.get("/banks/{bank_id}", response_model=BankResponse)
def get_bank_detail(bank_id: int, db: Session = Depends(get_db), _: User = read_access):
    return get_bank(db, bank_id)


@router.post("/banks", response_model=BankResponse, status_code=status.HTTP_201_CREATED)
def add_bank(bank: BankCreate, db: Session = Depends(get_db), _: User = write_access):
    return create_bank(db, bank)


@router.put("/banks/{bank_id}", response_model=BankResponse)
def edit_bank(bank_id: int, bank: BankUpdate, db: Session = Depends(get_db), _: User = write_access):
    return update_bank(db, bank_id, bank)


@router.delete("/banks/{bank_id}")
def remove_bank(bank_id: int, db: Session = Depends(get_db), _: User = write_access):
    delete_bank(db, bank_id)
    return {"message": "Bank deleted successfully"}


@router.get("/branches", response_model=BranchPageResponse)
def get_branches(
    db: Session = Depends(get_db),
    search: str | None = None,
    bank_id: int | None = None,
    page: int = 1,
    page_size: int = 10,
    all_items: bool = Query(False, alias="all"),
    _: User = read_access,
):
    return list_branches(db, search=search, bank_id=bank_id, page=page, page_size=page_size, all_items=all_items)


@router.get("/branches/{branch_id}", response_model=BranchResponse)
def get_branch_detail(branch_id: int, db: Session = Depends(get_db), _: User = read_access):
    return get_branch(db, branch_id)


@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def add_branch(branch: BranchCreate, db: Session = Depends(get_db), _: User = write_access):
    return create_branch(db, branch)


@router.put("/branches/{branch_id}", response_model=BranchResponse)
def edit_branch(branch_id: int, branch: BranchUpdate, db: Session = Depends(get_db), _: User = write_access):
    return update_branch(db, branch_id, branch)


@router.delete("/branches/{branch_id}")
def remove_branch(branch_id: int, db: Session = Depends(get_db), _: User = write_access):
    delete_branch(db, branch_id)
    return {"message": "Branch deleted successfully"}


@router.get("/executives", response_model=ExecutivePageResponse)
def get_executives(
    db: Session = Depends(get_db),
    search: str | None = None,
    status_filter: ExecutiveStatus | None = None,
    page: int = 1,
    page_size: int = 10,
    all_items: bool = Query(False, alias="all"),
    active_only: bool = False,
    _: User = read_access,
):
    effective_status = "Active" if active_only else status_filter
    return list_executives(db, search=search, status_filter=effective_status, page=page, page_size=page_size, all_items=all_items)


@router.get("/executives/{executive_id}", response_model=ExecutiveResponse)
def get_executive_detail(executive_id: int, db: Session = Depends(get_db), _: User = read_access):
    return get_executive(db, executive_id)


@router.post("/executives", response_model=ExecutiveResponse, status_code=status.HTTP_201_CREATED)
def add_executive(executive: ExecutiveCreate, db: Session = Depends(get_db), _: User = write_access):
    return create_executive(db, executive)


@router.put("/executives/{executive_id}", response_model=ExecutiveResponse)
def edit_executive(executive_id: int, executive: ExecutiveUpdate, db: Session = Depends(get_db), _: User = write_access):
    return update_executive(db, executive_id, executive)


@router.delete("/executives/{executive_id}")
def remove_executive(executive_id: int, db: Session = Depends(get_db), _: User = write_access):
    delete_executive(db, executive_id)
    return {"message": "Executive deleted successfully"}


@router.get("/loan-types", response_model=LoanTypePageResponse)
def get_loan_types(
    db: Session = Depends(get_db),
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
    all_items: bool = Query(False, alias="all"),
    _: User = read_access,
):
    return list_loan_types(db, search=search, page=page, page_size=page_size, all_items=all_items)


@router.get("/loan-types/{loan_type_id}", response_model=LoanTypeResponse)
def get_loan_type_detail(loan_type_id: int, db: Session = Depends(get_db), _: User = read_access):
    return get_loan_type(db, loan_type_id)


@router.post("/loan-types", response_model=LoanTypeResponse, status_code=status.HTTP_201_CREATED)
def add_loan_type(loan_type: LoanTypeCreate, db: Session = Depends(get_db), _: User = write_access):
    return create_loan_type(db, loan_type)


@router.put("/loan-types/{loan_type_id}", response_model=LoanTypeResponse)
def edit_loan_type(loan_type_id: int, loan_type: LoanTypeUpdate, db: Session = Depends(get_db), _: User = write_access):
    return update_loan_type(db, loan_type_id, loan_type)


@router.delete("/loan-types/{loan_type_id}")
def remove_loan_type(loan_type_id: int, db: Session = Depends(get_db), _: User = write_access):
    delete_loan_type(db, loan_type_id)
    return {"message": "Loan type deleted successfully"}


@router.get("/product-types", response_model=ProductTypePageResponse)
def get_product_types(
    db: Session = Depends(get_db),
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
    all_items: bool = Query(False, alias="all"),
    _: User = read_access,
):
    return list_product_types(db, search=search, page=page, page_size=page_size, all_items=all_items)


@router.get("/product-types/{product_type_id}", response_model=ProductTypeResponse)
def get_product_type_detail(product_type_id: int, db: Session = Depends(get_db), _: User = read_access):
    return get_product_type(db, product_type_id)


@router.post("/product-types", response_model=ProductTypeResponse, status_code=status.HTTP_201_CREATED)
def add_product_type(product_type: ProductTypeCreate, db: Session = Depends(get_db), _: User = write_access):
    return create_product_type(db, product_type)


@router.put("/product-types/{product_type_id}", response_model=ProductTypeResponse)
def edit_product_type(product_type_id: int, product_type: ProductTypeUpdate, db: Session = Depends(get_db), _: User = write_access):
    return update_product_type(db, product_type_id, product_type)


@router.delete("/product-types/{product_type_id}")
def remove_product_type(product_type_id: int, db: Session = Depends(get_db), _: User = write_access):
    delete_product_type(db, product_type_id)
    return {"message": "Product type deleted successfully"}


company_write_access = Depends(require_roles("Admin", "Manager"))


def _page(items):
    return {"items": items, "total": len(items), "page": 1, "page_size": len(items) or 1, "total_pages": 1}


@router.get("/companies", response_model=CompanyPageResponse)
def get_companies(search: str | None = None, active_only: bool = False, db: Session = Depends(get_db), _: User = read_access):
    query = db.query(Company).order_by(Company.name)
    if search: query = query.filter(Company.name.ilike(f"%{search.strip()}%"))
    if active_only: query = query.filter(Company.is_active.is_(True))
    return _page(query.all())


@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def add_company(payload: CompanyCreate, db: Session = Depends(get_db), _: User = company_write_access):
    if db.query(Company).filter(func.lower(func.trim(Company.name)) == payload.name.strip().casefold()).first():
        raise HTTPException(status_code=409, detail="Company name already exists")
    row = Company(**payload.model_dump()); db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Company name or code already exists") from exc
    return row


@router.put("/companies/{item_id}", response_model=CompanyResponse)
def edit_company(item_id: int, payload: CompanyUpdate, db: Session = Depends(get_db), _: User = company_write_access):
    row = db.get(Company, item_id)
    if not row: raise HTTPException(status_code=404, detail="Company not found")
    values = payload.model_dump(exclude_unset=True)
    if "name" in values and db.query(Company).filter(Company.id != item_id, func.lower(func.trim(Company.name)) == values["name"].strip().casefold()).first():
        raise HTTPException(status_code=409, detail="Company name already exists")
    for key, value in values.items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return row


@router.get("/company-banks", response_model=CompanyBankPageResponse, deprecated=True)
def get_company_banks(company_id: int | None = None, active_only: bool = False, db: Session = Depends(get_db), _: User = read_access):
    query = db.query(CompanyBank).options(joinedload(CompanyBank.company), joinedload(CompanyBank.bank)).order_by(CompanyBank.id)
    if company_id: query = query.filter(CompanyBank.company_id == company_id)
    if active_only: query = query.filter(CompanyBank.is_active.is_(True))
    return _page(query.all())


@router.post("/company-banks", response_model=CompanyBankResponse, status_code=status.HTTP_201_CREATED, deprecated=True)
def add_company_bank(payload: CompanyBankCreate, db: Session = Depends(get_db), _: User = company_write_access):
    if not db.get(Company, payload.company_id) or not db.get(Bank, payload.bank_id): raise HTTPException(status_code=422, detail="Company or bank not found")
    row = CompanyBank(**payload.model_dump()); db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Bank is already mapped to this company") from exc
    return db.query(CompanyBank).options(joinedload(CompanyBank.company), joinedload(CompanyBank.bank)).get(row.id)


@router.post("/company-banks/bulk", response_model=CompanyBankBulkResponse, deprecated=True)
def add_company_banks_bulk(payload: CompanyBankBulkCreate, db: Session = Depends(get_db), _: User = company_write_access):
    company = db.get(Company, payload.company_id)
    if company is None: raise HTTPException(status_code=422, detail="Company not found")
    if not company.is_active: raise HTTPException(status_code=422, detail="Company is inactive")
    bank_ids = list(dict.fromkeys(payload.bank_ids))
    banks = db.query(Bank).filter(Bank.id.in_(bank_ids)).all()
    by_id = {bank.id: bank for bank in banks}
    missing = [bank_id for bank_id in bank_ids if bank_id not in by_id]
    if missing: raise HTTPException(status_code=422, detail=f"Bank IDs not found: {missing}")
    inactive = [bank.id for bank in banks if getattr(bank, "is_active", True) is False]
    if inactive: raise HTTPException(status_code=422, detail=f"Bank IDs are inactive: {inactive}")
    existing = {row.bank_id: row for row in db.query(CompanyBank).filter(
        CompanyBank.company_id == company.id, CompanyBank.bank_id.in_(bank_ids)).all()}
    created_count = reactivated_count = skipped_count = 0
    touched: list[CompanyBank] = []
    remarks = payload.remarks.strip() if payload.remarks and payload.remarks.strip() else None
    for bank_id in bank_ids:
        row = existing.get(bank_id)
        if row is None:
            row = CompanyBank(company_id=company.id, bank_id=bank_id, is_active=True, remarks=remarks)
            db.add(row); touched.append(row); created_count += 1
        elif not row.is_active:
            row.is_active = True
            if remarks is not None: row.remarks = remarks
            touched.append(row); reactivated_count += 1
        else:
            touched.append(row); skipped_count += 1
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Company-bank mapping conflict") from exc
    ids = [row.id for row in touched]
    items = db.query(CompanyBank).options(joinedload(CompanyBank.company), joinedload(CompanyBank.bank)).filter(
        CompanyBank.id.in_(ids)).order_by(CompanyBank.id).all()
    return CompanyBankBulkResponse(created_count=created_count, reactivated_count=reactivated_count,
        skipped_count=skipped_count, items=items)


@router.put("/company-banks/{item_id}", response_model=CompanyBankResponse, deprecated=True)
def edit_company_bank(item_id: int, payload: CompanyBankUpdate, db: Session = Depends(get_db), _: User = company_write_access):
    row = db.get(CompanyBank, item_id)
    if not row: raise HTTPException(status_code=404, detail="Company-bank mapping not found")
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return db.query(CompanyBank).options(joinedload(CompanyBank.company), joinedload(CompanyBank.bank)).get(row.id)


@router.get("/districts", response_model=DistrictPageResponse)
def get_districts(active_only: bool = False, db: Session = Depends(get_db), _: User = read_access):
    query = db.query(District).filter(District.state == "Rajasthan").order_by(District.name)
    if active_only: query = query.filter(District.is_active.is_(True))
    return _page(query.all())


@router.post("/districts", response_model=DistrictResponse, status_code=status.HTTP_201_CREATED)
def add_district(payload: DistrictCreate, db: Session = Depends(get_db), _: User = company_write_access):
    row = District(**payload.model_dump()); db.add(row)
    try: db.commit(); db.refresh(row)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="District already exists") from exc
    return row


@router.put("/districts/{item_id}", response_model=DistrictResponse)
def edit_district(item_id: int, payload: DistrictUpdate, db: Session = Depends(get_db), _: User = company_write_access):
    row = db.get(District, item_id)
    if not row: raise HTTPException(status_code=404, detail="District not found")
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(row, key, value)
    db.commit(); db.refresh(row); return row
