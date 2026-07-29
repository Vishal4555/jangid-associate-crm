from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.database import get_db
from app.models.user import User
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