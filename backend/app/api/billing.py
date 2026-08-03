from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.database import get_db
from app.models.user import User
from app.schemas.billing import BillingCreate, BillingResponse, BillingUpdate
from app.services.billing_service import create_billing, get_billing, list_billing, update_billing


router = APIRouter(prefix="/billing", tags=["billing"])
access = Depends(require_roles("Admin", "Manager"))


@router.get("", response_model=list[BillingResponse])
def read_billing(
    case_no: str | None = None,
    bank: str | None = None,
    executive: str | None = None,
    city: str | None = None,
    bank_payment_status: str | None = None,
    executive_payment_status: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    _: User = access,
):
    return list_billing(db, case_no, bank, executive, city, bank_payment_status, executive_payment_status, from_date, to_date)


@router.get("/{billing_id}", response_model=BillingResponse)
def read_billing_detail(billing_id: int, db: Session = Depends(get_db), _: User = access):
    return get_billing(db, billing_id)


@router.post("", response_model=BillingResponse, status_code=status.HTTP_201_CREATED)
def add_billing(payload: BillingCreate, db: Session = Depends(get_db), current_user: User = access):
    return create_billing(db, payload, current_user)


@router.put("/{billing_id}", response_model=BillingResponse)
def edit_billing(billing_id: int, payload: BillingUpdate, db: Session = Depends(get_db), current_user: User = access):
    return update_billing(db, billing_id, payload, current_user)
