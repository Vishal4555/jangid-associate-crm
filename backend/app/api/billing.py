from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.database import get_db
from app.models.user import User
from app.schemas.billing import (BillingCreate, BillingResponse, BillingUpdate, BulkBillingRequest,
    BulkCreateRequest, BulkCreateResponse, BulkPreviewResponse)
from app.schemas.monthly_billing import (MonthlyBillingResponse, PaymentRegisterResponse, PaymentRegisterUpdate,
    MonthStatusResponse, FinalizeMonthRequest, ReopenMonthRequest, RegenerateMonthRequest,
    BankPaymentUpdate, BankPaymentResponse, BillingDashboardResponse)
from app.services.billing_service import (bulk_create, bulk_preview, create_billing, get_billing,
    list_billing, update_billing)
from app.services.monthly_billing_service import (monthly_billing, save_payment_register, month_status,
    finalize_month, reopen_month, save_bank_payment, billing_dashboard)


router = APIRouter(prefix="/billing", tags=["billing"])
access = Depends(require_roles("Admin", "Manager"))
admin_access = Depends(require_roles("Admin"))


@router.get("/monthly", response_model=MonthlyBillingResponse)
def read_monthly_billing(
    month: str,
    executive: str | None = None,
    bank: str | None = None,
    company: str | None = None,
    district: str | None = None,
    city: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = access,
):
    return monthly_billing(db, month, executive, bank, city, status, company, district)


@router.post("/monthly/payment-register", response_model=PaymentRegisterResponse)
def update_monthly_payment_register(
    payload: PaymentRegisterUpdate,
    db: Session = Depends(get_db),
    user: User = access,
):
    return save_payment_register(db, payload, user)


@router.get("/month-status", response_model=MonthStatusResponse)
def read_month_status(month: str, db: Session = Depends(get_db), _: User = access):
    return month_status(db, month)


@router.post("/month-finalize", response_model=MonthStatusResponse)
def finalize_billing_month(payload: FinalizeMonthRequest, db: Session = Depends(get_db), user: User = admin_access):
    return finalize_month(db, payload.month, payload.notes, user)


@router.post("/month-reopen", response_model=MonthStatusResponse)
def reopen_billing_month(payload: ReopenMonthRequest, db: Session = Depends(get_db), user: User = admin_access):
    return reopen_month(db, payload.month, payload.reason, user)


@router.post("/month-regenerate", response_model=MonthStatusResponse)
def regenerate_billing_month(payload: RegenerateMonthRequest, db: Session = Depends(get_db), user: User = admin_access):
    if not payload.confirm: raise HTTPException(status_code=422, detail="confirm must be true")
    return finalize_month(db, payload.month, None, user, regenerate=True)


@router.post("/monthly/bank-payment", response_model=BankPaymentResponse)
def update_bank_payment(payload: BankPaymentUpdate, db: Session = Depends(get_db), user: User = access):
    return save_bank_payment(db, payload, user)


@router.get("/dashboard", response_model=BillingDashboardResponse)
def read_billing_dashboard(month: str, company: str | None = None, bank: str | None = None,
    district: str | None = None, db: Session = Depends(get_db), _: User = access):
    return billing_dashboard(db, month, company, bank, district)


@router.post("/bulk-preview", response_model=BulkPreviewResponse)
def preview_bulk_billing(payload: BulkBillingRequest, db: Session = Depends(get_db), _: User = access):
    return bulk_preview(db, payload)


@router.post("/bulk-create", response_model=BulkCreateResponse)
def create_bulk_billing(payload: BulkCreateRequest, db: Session = Depends(get_db), user: User = access):
    return bulk_create(db, payload.case_ids, user)


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
