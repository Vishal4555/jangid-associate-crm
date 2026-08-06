from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import exists, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.billing import Billing
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.user import User
from app.core.company_scope import assert_company_access, assigned_company_ids
from app.schemas.billing import (BillingCreate, BillingResponse, BillingUpdate, BulkBillingRequest,
    BulkCreateResponse, BulkCreateResult, BulkPreviewResponse, BulkPreviewRow, BulkPreviewSummary)
from app.services.payout_rate_service import resolve_rates


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
        los_no=case_item.los_no,
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
        bank_payout_rate_id=billing.bank_payout_rate_id,
        executive_payout_rate_id=billing.executive_payout_rate_id,
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
    company_ids: set[int] | None = None,
    executive_scope: str | None = None,
) -> list[BillingResponse]:
    query = select(Billing, Case).join(Case, Billing.case_id == Case.id)
    if company_ids is not None: query = query.where(Case.company_id.in_(company_ids))
    if executive_scope is not None: query=query.where(or_(Case.executive==executive_scope,exists(select(CaseVisit.id).where(CaseVisit.case_id==Case.id,CaseVisit.executive==executive_scope))))
    if case_no:
        query = query.where(or_(Case.los_no.ilike(f"%{case_no}%"), Case.case_no.ilike(f"%{case_no}%")))
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


def get_billing(db: Session, billing_id: int, company_ids: set[int] | None = None) -> BillingResponse:
    query = select(Billing, Case).join(Case, Billing.case_id == Case.id).where(Billing.id == billing_id)
    if company_ids is not None: query = query.where(Case.company_id.in_(company_ids))
    row = db.execute(
        query
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing record not found")
    return _response(*row)


def create_billing(db: Session, payload: BillingCreate, current_user: User) -> BillingResponse:
    case_item = db.get(Case, payload.case_id)
    if case_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    assert_company_access(current_user, case_item.company_id)
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


def _case_query(payload: BulkBillingRequest):
    query = select(Case)
    if payload.case_ids is not None:
        query = query.where(Case.id.in_(set(payload.case_ids)))
    else:
        if payload.receive_date_from: query = query.where(Case.receive_date >= payload.receive_date_from)
        if payload.receive_date_to: query = query.where(Case.receive_date <= payload.receive_date_to)
        if payload.bank: query = query.where(Case.bank.ilike(payload.bank.strip()))
        if payload.city: query = query.where(Case.city.ilike(payload.city.strip()))
        if payload.executive: query = query.where(Case.executive.ilike(payload.executive.strip()))
        if payload.status: query = query.where(Case.status.ilike(payload.status.strip()))
    if payload.only_without_billing:
        query = query.where(~select(Billing.id).where(Billing.case_id == Case.id).exists())
    return query.order_by(Case.id)


def bulk_preview(db: Session, payload: BulkBillingRequest, company_ids: set[int] | None = None) -> BulkPreviewResponse:
    query = _case_query(payload)
    if company_ids is not None: query = query.where(Case.company_id.in_(company_ids))
    cases = db.scalars(query).all()
    billed_ids = set(db.scalars(select(Billing.case_id).where(Billing.case_id.in_([c.id for c in cases]))).all()) if cases else set()
    rows = []
    for case_item in cases:
        bank_rate, executive_rate = resolve_rates(db, case_item)
        errors = []
        if case_item.receive_date is None: errors.append("Case receive date is required")
        if bank_rate.status == "MISSING": errors.append("Bank Rate Not Configured")
        if executive_rate.status == "MISSING": errors.append("Executive Rate Not Configured")
        if bank_rate.status == "AMBIGUOUS" or executive_rate.status == "AMBIGUOUS": errors.append("Ambiguous Rate Configuration")
        existing = case_item.id in billed_ids
        if existing: errors.append("Billing already exists")
        margin = bank_rate.amount - executive_rate.amount if bank_rate.amount is not None and executive_rate.amount is not None else None
        rows.append(BulkPreviewRow(
            case_id=case_item.id, case_no=case_item.case_no, los_no=case_item.los_no, applicant=case_item.applicant,
            bank=case_item.bank, city=case_item.city, executive=case_item.executive,
            loan_type=case_item.loan_type, product_type=case_item.product_type,
            bank_rate_status=bank_rate.status, bank_rate_id=bank_rate.rate_id, bank_payout_amount=bank_rate.amount,
            executive_rate_status=executive_rate.status, executive_rate_id=executive_rate.rate_id,
            executive_payout_amount=executive_rate.amount, expected_gross_margin=margin,
            existing_billing=existing, validation_errors=errors, ready=not errors,
        ))
    return BulkPreviewResponse(rows=rows, summary=BulkPreviewSummary(
        selected_cases=len(rows), ready_cases=sum(r.ready for r in rows),
        missing_bank_rates=sum(r.bank_rate_status == "MISSING" for r in rows),
        missing_executive_rates=sum(r.executive_rate_status == "MISSING" for r in rows),
        ambiguous_rates=sum(r.bank_rate_status == "AMBIGUOUS" or r.executive_rate_status == "AMBIGUOUS" for r in rows),
        existing_billing_records=sum(r.existing_billing for r in rows),
    ))


def bulk_create(db: Session, case_ids: list[int], user: User) -> BulkCreateResponse:
    unique_ids = list(dict.fromkeys(case_ids))
    query = select(Case).where(Case.id.in_(unique_ids))
    company_ids = assigned_company_ids(user)
    if company_ids is not None: query = query.where(Case.company_id.in_(company_ids))
    cases = {c.id: c for c in db.scalars(query.with_for_update()).all()}
    existing = set(db.scalars(select(Billing.case_id).where(Billing.case_id.in_(unique_ids))).all())
    results, pending = [], []
    for case_id in unique_ids:
        case_item = cases.get(case_id)
        if case_item is None:
            results.append(BulkCreateResult(case_id=case_id, status="ERROR", errors=["Case not found"]))
            continue
        if case_id in existing:
            results.append(BulkCreateResult(case_id=case_id, case_no=case_item.case_no, los_no=case_item.los_no, status="SKIPPED", errors=["Billing already exists"]))
            continue
        bank_rate, executive_rate = resolve_rates(db, case_item)
        errors = []
        if bank_rate.status != "MATCHED": errors.append("Bank Rate Not Configured" if bank_rate.status == "MISSING" else "Ambiguous Rate Configuration")
        if executive_rate.status != "MATCHED": errors.append("Executive Rate Not Configured" if executive_rate.status == "MISSING" else "Ambiguous Rate Configuration")
        if errors:
            results.append(BulkCreateResult(case_id=case_id, case_no=case_item.case_no, los_no=case_item.los_no, status="ERROR", errors=list(dict.fromkeys(errors))))
            continue
        billing = Billing(case_id=case_id, bank_payout_amount=bank_rate.amount, executive_payout_amount=executive_rate.amount,
            bank_payout_rate_id=bank_rate.rate_id, executive_payout_rate_id=executive_rate.rate_id,
            created_by_user_id=user.id, updated_by_user_id=user.id)
        db.add(billing)
        pending.append((billing, case_item))
    try:
        db.flush()
        for billing, case_item in pending:
            results.append(BulkCreateResult(case_id=case_item.id, case_no=case_item.case_no, los_no=case_item.los_no, status="CREATED", billing_id=billing.id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Concurrent billing creation detected; no records were created") from exc
    except Exception:
        db.rollback()
        raise
    return BulkCreateResponse(created_count=sum(r.status == "CREATED" for r in results),
        skipped_count=sum(r.status == "SKIPPED" for r in results), error_count=sum(r.status == "ERROR" for r in results), results=results)


def update_billing(db: Session, billing_id: int, payload: BillingUpdate, current_user: User) -> BillingResponse:
    billing = db.get(Billing, billing_id)
    if billing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billing record not found")
    current_case = db.get(Case, billing.case_id); assert_company_access(current_user, current_case.company_id)
    data = payload.model_dump(exclude_unset=True)
    if "case_id" in data:
        target_case = db.get(Case, data["case_id"])
        if target_case is None: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        assert_company_access(current_user, target_case.company_id)
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
