from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.security import require_permission
from app.db.database import get_db
from app.models.user import User
from app.schemas.payout_rate import (BankRateBulkCreate, BankRateBulkResponse, BankRateCreate, BankRateResponse, BankRateUpdate,
    ExecutiveRateCreate, ExecutiveRateResponse, ExecutiveRateUpdate, RateImportRequest, RateImportResponse)
from app.services.payout_rate_service import create_bank_rates_bulk, create_rate, delete_bank_rate, import_rates, list_rates, update_rate

router = APIRouter(prefix="/billing/rates", tags=["billing rates"])
bulk_router = APIRouter(prefix="/payout-rates", tags=["billing rates"])
access = Depends(require_permission("billing.rate_master"))


@router.get("/bank", response_model=list[BankRateResponse])
def get_bank_rates(search: str | None = None, active: bool | None = None, company_id: int | None = None,
        bank_id: int | None = None, district_id: int | None = None,
        scope: str | None = Query(None, pattern="^(rajasthan_except_jaipur|jaipur|specific)$"),
        db: Session = Depends(get_db), _: User = access):
    return list_rates(db, "bank", search, active, company_id, bank_id, district_id, scope)


@router.post("/bank", response_model=BankRateResponse, status_code=status.HTTP_201_CREATED)
def add_bank_rate(payload: BankRateCreate, db: Session = Depends(get_db), user: User = access):
    return create_rate(db, "bank", payload, user)


@router.post("/bank/bulk", response_model=BankRateBulkResponse, status_code=status.HTTP_201_CREATED)
@bulk_router.post("/bank/bulk", response_model=BankRateBulkResponse, status_code=status.HTTP_201_CREATED)
def add_bank_rates_bulk(payload: BankRateBulkCreate, db: Session = Depends(get_db), user: User = access):
    return create_bank_rates_bulk(db, payload, user)


@router.put("/bank/{rate_id}", response_model=BankRateResponse)
def edit_bank_rate(rate_id: int, payload: BankRateUpdate, db: Session = Depends(get_db), user: User = access):
    return update_rate(db, "bank", rate_id, payload, user)


@bulk_router.delete("/bank/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_bank_rate(rate_id: int, db: Session = Depends(get_db), _: User = access):
    delete_bank_rate(db, rate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/executive", response_model=list[ExecutiveRateResponse])
def get_executive_rates(search: str | None = None, active: bool | None = None, db: Session = Depends(get_db), _: User = access):
    return list_rates(db, "executive", search, active)


@router.post("/executive", response_model=ExecutiveRateResponse, status_code=status.HTTP_201_CREATED)
def add_executive_rate(payload: ExecutiveRateCreate, db: Session = Depends(get_db), user: User = access):
    return create_rate(db, "executive", payload, user)


@router.put("/executive/{rate_id}", response_model=ExecutiveRateResponse)
def edit_executive_rate(rate_id: int, payload: ExecutiveRateUpdate, db: Session = Depends(get_db), user: User = access):
    return update_rate(db, "executive", rate_id, payload, user)


@router.post("/bank/import", response_model=RateImportResponse)
def import_bank_rates(payload: RateImportRequest, db: Session = Depends(get_db), user: User = access):
    return import_rates(db, "bank", payload, user)


@router.post("/executive/import", response_model=RateImportResponse)
def import_executive_rates(payload: RateImportRequest, db: Session = Depends(get_db), user: User = access):
    return import_rates(db, "executive", payload, user)
