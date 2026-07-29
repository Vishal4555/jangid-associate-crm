from __future__ import annotations

import math

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.master import Bank, Branch, Executive, LoanType, ProductType
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
    ExecutiveUpdate,
    LoanTypeCreate,
    LoanTypePageResponse,
    LoanTypeResponse,
    LoanTypeUpdate,
    PaginationMeta,
    ProductTypeCreate,
    ProductTypePageResponse,
    ProductTypeResponse,
    ProductTypeUpdate,
)


def _build_page(items, total: int, page: int, page_size: int):
    return PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)) if page_size else 1,
    )


def _paginate(query, page: int, page_size: int):
    total = query.count()
    if page_size <= 0:
        page_size = 10
    offset = max(page - 1, 0) * page_size
    items = query.offset(offset).limit(page_size).all()
    return items, total, page, page_size


def _apply_text_search(query, model, search: str | None, fields: list[str]):
    if not search:
        return query

    expression = f"%{search.strip()}%"
    conditions = [getattr(model, field).ilike(expression) for field in fields]
    return query.filter(or_(*conditions))


def _handle_integrity_error(db: Session, detail: str):
    db.rollback()
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def list_banks(db: Session, *, search: str | None, page: int, page_size: int, all_items: bool) -> BankPageResponse:
    query = db.query(Bank).order_by(Bank.id.asc())
    query = _apply_text_search(query, Bank, search, ["name", "code"])

    if all_items:
        items = query.all()
        total = len(items)
        return BankPageResponse(
            items=items,
            total=total,
            page=1,
            page_size=total or 1,
            total_pages=1,
        )

    items, total, page, page_size = _paginate(query, page, page_size)
    return BankPageResponse(items=items, **_build_page(items, total, page, page_size).model_dump())


def get_bank(db: Session, bank_id: int) -> Bank:
    bank = db.get(Bank, bank_id)
    if bank is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bank with id {bank_id} not found")
    return bank


def create_bank(db: Session, payload: BankCreate) -> Bank:
    bank = Bank(**payload.model_dump())
    db.add(bank)

    try:
        db.commit()
        db.refresh(bank)
    except IntegrityError:
        _handle_integrity_error(db, "Bank name or code already exists")

    return bank


def update_bank(db: Session, bank_id: int, payload: BankUpdate) -> Bank:
    bank = get_bank(db, bank_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(bank, field, value)

    try:
        db.commit()
        db.refresh(bank)
    except IntegrityError:
        _handle_integrity_error(db, "Bank name or code already exists")

    return bank


def delete_bank(db: Session, bank_id: int) -> None:
    bank = get_bank(db, bank_id)
    db.delete(bank)
    db.commit()


def list_branches(
    db: Session,
    *,
    search: str | None,
    bank_id: int | None,
    page: int,
    page_size: int,
    all_items: bool,
) -> BranchPageResponse:
    query = db.query(Branch).options(joinedload(Branch.bank)).order_by(Branch.id.asc())
    query = _apply_text_search(query.join(Branch.bank), Branch, search, ["name", "code"])

    if bank_id is not None:
        query = query.filter(Branch.bank_id == bank_id)

    if all_items:
        items = query.all()
        total = len(items)
        return BranchPageResponse(
            items=items,
            total=total,
            page=1,
            page_size=total or 1,
            total_pages=1,
        )

    items, total, page, page_size = _paginate(query, page, page_size)
    return BranchPageResponse(items=items, **_build_page(items, total, page, page_size).model_dump())


def get_branch(db: Session, branch_id: int) -> Branch:
    branch = db.query(Branch).options(joinedload(Branch.bank)).filter(Branch.id == branch_id).first()
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Branch with id {branch_id} not found")
    return branch


def create_branch(db: Session, payload: BranchCreate) -> Branch:
    branch = Branch(**payload.model_dump())
    db.add(branch)

    try:
        db.commit()
        db.refresh(branch)
    except IntegrityError:
        _handle_integrity_error(db, "Branch name already exists for this bank")

    return db.query(Branch).options(joinedload(Branch.bank)).get(branch.id) or branch


def update_branch(db: Session, branch_id: int, payload: BranchUpdate) -> Branch:
    branch = get_branch(db, branch_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(branch, field, value)

    try:
        db.commit()
        db.refresh(branch)
    except IntegrityError:
        _handle_integrity_error(db, "Branch name already exists for this bank")

    return db.query(Branch).options(joinedload(Branch.bank)).get(branch.id) or branch


def delete_branch(db: Session, branch_id: int) -> None:
    branch = get_branch(db, branch_id)
    db.delete(branch)
    db.commit()


def list_executives(
    db: Session,
    *,
    search: str | None,
    status_filter: str | None,
    page: int,
    page_size: int,
    all_items: bool,
) -> ExecutivePageResponse:
    query = db.query(Executive).order_by(Executive.id.asc())
    query = _apply_text_search(query, Executive, search, ["full_name", "email", "mobile", "status"])

    if status_filter:
        query = query.filter(Executive.status == status_filter)

    if all_items:
        items = query.all()
        total = len(items)
        return ExecutivePageResponse(
            items=items,
            total=total,
            page=1,
            page_size=total or 1,
            total_pages=1,
        )

    items, total, page, page_size = _paginate(query, page, page_size)
    return ExecutivePageResponse(items=items, **_build_page(items, total, page, page_size).model_dump())


def get_executive(db: Session, executive_id: int) -> Executive:
    executive = db.get(Executive, executive_id)
    if executive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Executive with id {executive_id} not found")
    return executive


def create_executive(db: Session, payload: ExecutiveCreate) -> Executive:
    executive = Executive(**payload.model_dump())
    db.add(executive)

    try:
        db.commit()
        db.refresh(executive)
    except IntegrityError:
        _handle_integrity_error(db, "Executive already exists")

    return executive


def update_executive(db: Session, executive_id: int, payload: ExecutiveUpdate) -> Executive:
    executive = get_executive(db, executive_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(executive, field, value)

    try:
        db.commit()
        db.refresh(executive)
    except IntegrityError:
        _handle_integrity_error(db, "Executive already exists")

    return executive


def delete_executive(db: Session, executive_id: int) -> None:
    executive = get_executive(db, executive_id)
    db.delete(executive)
    db.commit()


def list_loan_types(db: Session, *, search: str | None, page: int, page_size: int, all_items: bool) -> LoanTypePageResponse:
    query = db.query(LoanType).order_by(LoanType.id.asc())
    query = _apply_text_search(query, LoanType, search, ["name", "code"])

    if all_items:
        items = query.all()
        total = len(items)
        return LoanTypePageResponse(
            items=items,
            total=total,
            page=1,
            page_size=total or 1,
            total_pages=1,
        )

    items, total, page, page_size = _paginate(query, page, page_size)
    return LoanTypePageResponse(items=items, **_build_page(items, total, page, page_size).model_dump())


def get_loan_type(db: Session, loan_type_id: int) -> LoanType:
    loan_type = db.get(LoanType, loan_type_id)
    if loan_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Loan type with id {loan_type_id} not found")
    return loan_type


def create_loan_type(db: Session, payload: LoanTypeCreate) -> LoanType:
    loan_type = LoanType(**payload.model_dump())
    db.add(loan_type)

    try:
        db.commit()
        db.refresh(loan_type)
    except IntegrityError:
        _handle_integrity_error(db, "Loan type name or code already exists")

    return loan_type


def update_loan_type(db: Session, loan_type_id: int, payload: LoanTypeUpdate) -> LoanType:
    loan_type = get_loan_type(db, loan_type_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(loan_type, field, value)

    try:
        db.commit()
        db.refresh(loan_type)
    except IntegrityError:
        _handle_integrity_error(db, "Loan type name or code already exists")

    return loan_type


def delete_loan_type(db: Session, loan_type_id: int) -> None:
    loan_type = get_loan_type(db, loan_type_id)
    db.delete(loan_type)
    db.commit()


def list_product_types(db: Session, *, search: str | None, page: int, page_size: int, all_items: bool) -> ProductTypePageResponse:
    query = db.query(ProductType).order_by(ProductType.id.asc())
    query = _apply_text_search(query, ProductType, search, ["name", "code"])

    if all_items:
        items = query.all()
        total = len(items)
        return ProductTypePageResponse(
            items=items,
            total=total,
            page=1,
            page_size=total or 1,
            total_pages=1,
        )

    items, total, page, page_size = _paginate(query, page, page_size)
    return ProductTypePageResponse(items=items, **_build_page(items, total, page, page_size).model_dump())


def get_product_type(db: Session, product_type_id: int) -> ProductType:
    product_type = db.get(ProductType, product_type_id)
    if product_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product type with id {product_type_id} not found")
    return product_type


def create_product_type(db: Session, payload: ProductTypeCreate) -> ProductType:
    product_type = ProductType(**payload.model_dump())
    db.add(product_type)

    try:
        db.commit()
        db.refresh(product_type)
    except IntegrityError:
        _handle_integrity_error(db, "Product type name or code already exists")

    return product_type


def update_product_type(db: Session, product_type_id: int, payload: ProductTypeUpdate) -> ProductType:
    product_type = get_product_type(db, product_type_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product_type, field, value)

    try:
        db.commit()
        db.refresh(product_type)
    except IntegrityError:
        _handle_integrity_error(db, "Product type name or code already exists")

    return product_type


def delete_product_type(db: Session, product_type_id: int) -> None:
    product_type = get_product_type(db, product_type_id)
    db.delete(product_type)
    db.commit()