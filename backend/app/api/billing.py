from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import require_permission
from app.core.company_scope import assert_company_access, assigned_company_ids
from app.db.database import get_db
from app.models.user import User
from app.models.billing import Billing
from app.models.case import Case
from app.schemas.billing import (BillingCreate, BillingResponse, BillingUpdate, BulkBillingRequest,
    BulkCreateRequest, BulkCreateResponse, BulkPreviewResponse)
from app.schemas.monthly_billing import (MonthlyBillingResponse, PaymentRegisterResponse, PaymentRegisterUpdate,
    MonthStatusResponse, FinalizeMonthRequest, ReopenMonthRequest, RegenerateMonthRequest,
    BankPaymentUpdate, BankPaymentResponse, BillingDashboardResponse)
from app.services.billing_service import (bulk_create, bulk_preview, create_billing, get_billing,
    list_billing, update_billing)
from app.services.monthly_billing_service import (monthly_billing, save_payment_register, month_status,
    finalize_month, reopen_month, save_bank_payment, billing_dashboard)
from app.schemas.billing_reports import CompanyBillingReport, ExecutivePerformanceReport
from app.services.billing_report_service import company_report, executive_report


router = APIRouter(prefix="/billing", tags=["billing"])
access = Depends(require_permission("billing.view"))
payment_access = Depends(require_permission("billing.payment_register"))


@router.get("/reports/company", response_model=CompanyBillingReport)
def read_company_report(company_id: int, date_from: date, date_to: date, bank: str | None = None,
    district_id: int | None = None, city: str | None = None, executive: str | None = None,
    visit_type: str | None = None, status: str | None = None, payment_status: str | None = None,
    db: Session = Depends(get_db), user: User = Depends(require_permission("billing.company_export"))):
    return company_report(db, user, assigned_company_ids(user), company_id, date_from, date_to,
        bank=bank, district_id=district_id, city=city, executive=executive, visit_type=visit_type,
        status=status, payment_status=payment_status)


@router.get("/reports/executive", response_model=ExecutivePerformanceReport)
def read_executive_report(date_from: date, date_to: date, executive: str | None = None,
    company_id: int | None = None, bank: str | None = None, district_id: int | None = None,
    city: str | None = None, status: str | None = None, db: Session = Depends(get_db),
    user: User = Depends(require_permission("billing.executive_report"))):
    return executive_report(db, user, assigned_company_ids(user), date_from, date_to,
        executive=executive, company_id=company_id, bank=bank, district_id=district_id, city=city, status=status)


def _executive_scope(user: User) -> str | None:
    return user.executive.full_name if user.role == "Executive" and user.executive else ("__unlinked_executive__" if user.role == "Executive" else None)


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
    return monthly_billing(db, month, _executive_scope(_) or executive, bank, city, status, company, district, assigned_company_ids(_))


@router.post("/monthly/payment-register", response_model=PaymentRegisterResponse)
def update_monthly_payment_register(
    payload: PaymentRegisterUpdate,
    db: Session = Depends(get_db),
    user: User = payment_access,
):
    return save_payment_register(db, payload, user)


@router.get("/month-status", response_model=MonthStatusResponse)
def read_month_status(month: str, db: Session = Depends(get_db), _: User = access):
    return month_status(db, month)


@router.post("/month-finalize", response_model=MonthStatusResponse)
def finalize_billing_month(payload: FinalizeMonthRequest, db: Session = Depends(get_db), user: User = Depends(require_permission("billing.finalize"))):
    return finalize_month(db, payload.month, payload.notes, user)


@router.post("/month-reopen", response_model=MonthStatusResponse)
def reopen_billing_month(payload: ReopenMonthRequest, db: Session = Depends(get_db), user: User = Depends(require_permission("billing.reopen"))):
    return reopen_month(db, payload.month, payload.reason, user)


@router.post("/month-regenerate", response_model=MonthStatusResponse)
def regenerate_billing_month(payload: RegenerateMonthRequest, db: Session = Depends(get_db), user: User = Depends(require_permission("billing.regenerate"))):
    if not payload.confirm: raise HTTPException(status_code=422, detail="confirm must be true")
    return finalize_month(db, payload.month, None, user, regenerate=True)


@router.post("/monthly/bank-payment", response_model=BankPaymentResponse)
def update_bank_payment(payload: BankPaymentUpdate, db: Session = Depends(get_db), user: User = payment_access):
    return save_bank_payment(db, payload, user)


@router.get("/dashboard", response_model=BillingDashboardResponse)
def read_billing_dashboard(month: str, company: str | None = None, bank: str | None = None,
    district: str | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission("billing.dashboard"))):
    return billing_dashboard(db, month, company, bank, district, assigned_company_ids(user))


@router.post("/bulk-preview", response_model=BulkPreviewResponse)
def preview_bulk_billing(payload: BulkBillingRequest, db: Session = Depends(get_db), user: User = access):
    return bulk_preview(db, payload, assigned_company_ids(user))


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
    user: User = access,
):
    return list_billing(db, case_no, bank, executive, city, bank_payment_status, executive_payment_status, from_date, to_date, assigned_company_ids(user), _executive_scope(user))


@router.get("/{billing_id}", response_model=BillingResponse)
def read_billing_detail(billing_id: int, db: Session = Depends(get_db), user: User = access):
    return get_billing(db, billing_id, assigned_company_ids(user))


@router.post("", response_model=BillingResponse, status_code=status.HTTP_201_CREATED)
def add_billing(payload: BillingCreate, db: Session = Depends(get_db), current_user: User = access):
    return create_billing(db, payload, current_user)


@router.put("/{billing_id}", response_model=BillingResponse)
def edit_billing(billing_id: int, payload: BillingUpdate, db: Session = Depends(get_db), current_user: User = access):
    return update_billing(db, billing_id, payload, current_user)


@router.delete("/{billing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_billing(billing_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("billing.delete"))):
    row = db.get(Billing, billing_id)
    if row is None: raise HTTPException(status_code=404, detail="Billing record not found")
    case_item=db.get(Case,row.case_id); assert_company_access(user,case_item.company_id)
    db.delete(row); db.commit()
