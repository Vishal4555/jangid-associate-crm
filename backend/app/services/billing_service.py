from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.billing import Billing
from app.models.case import Case
from app.models.user import User
from app.schemas.billing import BillingCreate, BillingResponse, BillingUpdate


def _apply_payment_rules(data: dict, existing: Billing | None = None) -> None:
    for prefix in ("bank", "executive"):
        status_field = f"{prefix}_payment_status"
        date_field = f"{prefix}_paid_date"
        payout_field = f"{prefix}_payout_amount"
        paid_field = f"{prefix}_paid_amount"
        payout = Decimal(data.get(payout_field, getattr(existing, payout_field) if existing else 0))
        paid = Decimal(data.get(paid_field, getattr(existing, paid_field) if existing else 0))
        existing_paid = Decimal(getattr(existing, paid_field)) if existing else Decimal("0")
        if paid > payout:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{paid_field} cannot exceed {payout_field}",
            )

        requested_status = data.get(status_field, getattr(existing, status_field) if existing else "Pending")
        cancelled = requested_status == "Cancelled"
        if not cancelled:
            if paid == 0:
                data[status_field] = "Pending"
            elif paid < payout:
                data[status_field] = "Partially Paid"
            else:
                data[status_field] = "Paid"

        existing_date = getattr(existing, date_field) if existing else None
        supplied_date = data.get(date_field, existing_date)
        if cancelled:
            if date_field in data and data[date_field] is None and existing_date is not None:
                data[date_field] = existing_date
            elif paid > 0 and supplied_date is None:
                data[date_field] = existing_date or date.today()
        elif paid == 0:
            data[date_field] = None
        elif paid > existing_paid and existing_date is not None:
            data[date_field] = existing_date
        elif supplied_date is None:
            data[date_field] = existing_date or date.today()


def _response(billing: Billing, case_item: Case) -> BillingResponse:
    return BillingResponse(
        id=billing.id,
        case_id=billing.case_id,
        case_no=case_item.case_no,
        applicant=case_item.applicant,
        bank=case_item.bank,
        city=case_item.city,
        executive=case_item.executive,
        bank_payout_amount=billing.bank_payout_amount,
        bank_paid_amount=billing.bank_paid_amount,
        bank_payment_status=billing.bank_payment_status,
        bank_paid_date=billing.bank_paid_date,
        bank_payment_reference=billing.bank_payment_reference,
        executive_payout_amount=billing.executive_payout_amount,
        executive_paid_amount=billing.executive_paid_amount,
        executive_payment_status=billing.executive_payment_status,
        executive_paid_date=billing.executive_paid_date,
        executive_payment_reference=billing.executive_payment_reference,
        gross_margin=billing.bank_payout_amount - billing.executive_payout_amount,
        bank_balance=billing.bank_payout_amount - billing.bank_paid_amount,
        executive_balance=billing.executive_payout_amount - billing.executive_paid_amount,
        expected_gross_margin=billing.bank_payout_amount - billing.executive_payout_amount,
        realized_cash_margin=billing.bank_paid_amount - billing.executive_paid_amount,
        remarks=billing.remarks,
        created_at=billing.created_at,
        updated_at=billing.updated_at,
    )


def list_billing(
    db: Session,
    case_no: str | None = None,
    bank: str | None = None,
    executive: str | None = None,
    city: str | None = None,
    bank_payment_status: str | None = None,
    executive_payment_status: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[BillingResponse]:
    query = select(Billing, Case).join(Case, Billing.case_id == Case.id)
    if case_no:
        query = query.where(Case.case_no.ilike(f"%{case_no}%"))
    if bank:
        query = query.where(Case.bank == bank)
    if executive:
        query = query.where(Case.executive == executive)
    if city:
        query = query.where(Case.city == city)
    if bank_payment_status:
        query = query.where(Billing.bank_payment_status == bank_payment_status)
    if executive_payment_status:
        query = query.where(Billing.executive_payment_status == executive_payment_status)
    if from_date:
        query = query.where(Case.receive_date >= from_date)
    if to_date:
        query = query.where(Case.receive_date <= to_date)
    rows = db.execute(query.order_by(Billing.id.desc())).all()
    return [_response(billing, case_item) for billing, case_item in rows]


def get_billing(db: Session, billing_id: int) -> BillingResponse:
    row = db.execute(
        select(Billing, Case).join(Case, Billing.case_id == Case.id).where(Billing.id == billing_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing record not found")
    return _response(*row)


def create_billing(db: Session, payload: BillingCreate, current_user: User) -> BillingResponse:
    case_item = db.get(Case, payload.case_id)
    if case_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    data = payload.model_dump()
    _apply_payment_rules(data)
    billing = Billing(**data, created_by_user_id=current_user.id, updated_by_user_id=current_user.id)
    try:
        db.add(billing)
        db.commit()
        db.refresh(billing)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Billing already exists for this case") from exc
    except Exception:
        db.rollback()
        raise
    return _response(billing, case_item)


def update_billing(db: Session, billing_id: int, payload: BillingUpdate, current_user: User) -> BillingResponse:
    billing = db.get(Billing, billing_id)
    if billing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing record not found")
    data = payload.model_dump(exclude_unset=True)
    if "case_id" in data and db.get(Case, data["case_id"]) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    _apply_payment_rules(data, billing)
    for field, value in data.items():
        setattr(billing, field, value)
    billing.updated_by_user_id = current_user.id
    billing.updated_at = datetime.now()
    try:
        db.commit()
        db.refresh(billing)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Billing already exists for this case") from exc
    except Exception:
        db.rollback()
        raise
    case_item = db.get(Case, billing.case_id)
    return _response(billing, case_item)
