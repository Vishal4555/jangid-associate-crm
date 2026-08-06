from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import has_permission, require_any_permission, require_permission
from app.core.company_scope import apply_company_scope, assert_company_access
from app.db.database import get_db
from app.models.case import Case
from app.models.case_activity import CaseActivity
from app.models.case_visit import CaseVisit
from app.models.billing import Billing
from app.models.billing_month import BankMonthlyBillingSnapshot, BillingMonth
from app.models.master import District
from app.models.user import User
from app.schemas.case import MessageResponse
from app.schemas.case_visit import (
    CaseVisitCreate, CaseVisitListResponse, CaseVisitResponse, CaseVisitUpdate,
)

router = APIRouter(prefix="/cases/{case_id}/visits", tags=["case visits"])
list_router = APIRouter(prefix="/case-visits", tags=["case visits"])


@list_router.get("", response_model=CaseVisitListResponse)
def list_case_visits(
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    visit_type: str | None = None,
    company_id: int | None = None,
    bank: str | None = None,
    district_id: int | None = None,
    city: str | None = None,
    executive: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("cases.view")),
):
    stmt = select(CaseVisit, Case).join(Case, Case.id == CaseVisit.case_id)
    stmt = apply_company_scope(stmt, Case.company_id, user)
    if user.role == "Executive" and not has_permission(user, "cases.view_all"):
        stmt = stmt.where(CaseVisit.executive == _executive_name(user))
    if search and (term := search.strip()):
        pattern = f"%{term.casefold()}%"
        stmt = stmt.where(or_(
            func.lower(Case.los_no).like(pattern), func.lower(Case.applicant).like(pattern),
            func.lower(Case.mobile).like(pattern), func.lower(CaseVisit.address).like(pattern),
            func.lower(CaseVisit.executive).like(pattern), func.lower(CaseVisit.visit_type).like(pattern),
        ))
    if status_filter: stmt = stmt.where(CaseVisit.status == status_filter)
    if visit_type: stmt = stmt.where(CaseVisit.visit_type == visit_type)
    if company_id is not None: stmt = stmt.where(Case.company_id == company_id)
    if bank: stmt = stmt.where(Case.bank == bank)
    if district_id is not None: stmt = stmt.where(CaseVisit.district_id == district_id)
    if city: stmt = stmt.where(func.lower(CaseVisit.city) == city.strip().casefold())
    if executive: stmt = stmt.where(CaseVisit.executive == executive)
    if date_from: stmt = stmt.where(CaseVisit.receive_date >= date_from)
    if date_to: stmt = stmt.where(CaseVisit.receive_date <= date_to)

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    results = db.execute(stmt.order_by(CaseVisit.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    items = [{
        "visit_id": visit.id, "case_id": case.id, "visit_type": visit.visit_type,
        "los_no": case.los_no, "company_id": case.company_id, "company": case.company,
        "bank": case.bank, "applicant": case.applicant, "mobile": case.mobile,
        "loan_type": case.loan_type, "receive_date": visit.receive_date,
        "closed_date": visit.closed_date, "tat_days": visit.tat_days, "address": visit.address,
        "district_id": visit.district_id, "district": visit.district, "city": visit.city,
        "landmark": visit.landmark, "executive": visit.executive, "status": visit.status,
        "negative_reason": visit.negative_reason, "remarks": visit.remarks,
        "created_at": visit.created_at, "updated_at": visit.updated_at,
    } for visit, case in results]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def _case(db: Session, case_id: int, user: User) -> Case:
    item = db.get(Case, case_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")
    assert_company_access(user, item.company_id)
    return item


def _visit(db: Session, case_id: int, visit_id: int) -> CaseVisit:
    item = db.scalar(select(CaseVisit).where(CaseVisit.id == visit_id, CaseVisit.case_id == case_id))
    if item is None:
        raise HTTPException(status_code=404, detail=f"Visit with id {visit_id} not found for case {case_id}")
    return item


def _executive_name(user: User) -> str:
    if user.role != "Executive" or user.executive is None:
        raise HTTPException(status_code=403, detail="Executive account is not linked to an Executive Master record")
    return user.executive.full_name


def _assert_assigned(visit: CaseVisit, user: User) -> None:
    if user.role == "Executive" and visit.executive != _executive_name(user):
        raise HTTPException(status_code=403, detail="This visit is not assigned to you")


def _dimensions(db: Session, data: dict) -> None:
    if "district_id" not in data:
        return
    district_id = data.get("district_id")
    if district_id is None:
        data["district"] = None
        return
    district = db.get(District, district_id)
    if district is None or not district.is_active:
        raise HTTPException(status_code=422, detail="Active Rajasthan district not found")
    data["district"] = district.name


def _activity(case_id: int, kind: str, user: User, visit: CaseVisit, field=None, old=None, new=None):
    return CaseActivity(case_id=case_id, activity_type=kind, field_name=field,
        old_value=None if old is None else str(old), new_value=None if new is None else str(new),
        performed_by_user_id=user.id, performed_by_name=user.full_name,
        remarks=f"Visit #{visit.id} ({visit.visit_type})")


@router.get("", response_model=list[CaseVisitResponse])
def list_visits(case_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("cases.view"))):
    _case(db, case_id, user)
    stmt = select(CaseVisit).where(CaseVisit.case_id == case_id)
    if user.role == "Executive": stmt = stmt.where(CaseVisit.executive == _executive_name(user))
    return db.scalars(stmt.order_by(CaseVisit.id)).all()


@router.post("", response_model=CaseVisitResponse, status_code=status.HTTP_201_CREATED)
def create_visit(case_id: int, payload: CaseVisitCreate, db: Session = Depends(get_db), user: User = Depends(require_permission("visits.create"))):
    _case(db, case_id, user)
    data = payload.model_dump()
    _dimensions(db, data)
    data["closed_date"] = date.today() if data["status"] in {"Positive", "Negative"} else None
    visit = CaseVisit(case_id=case_id, created_by_user_id=user.id, updated_by_user_id=user.id, **data)
    try:
        db.add(visit); db.flush(); db.add(_activity(case_id, "VISIT_CREATED", user, visit)); db.commit(); db.refresh(visit)
    except Exception:
        db.rollback(); raise
    return visit


@router.get("/{visit_id}", response_model=CaseVisitResponse)
def get_visit(case_id: int, visit_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("cases.view"))):
    _case(db, case_id, user)
    visit = _visit(db, case_id, visit_id); _assert_assigned(visit, user); return visit


@router.put("/{visit_id}", response_model=CaseVisitResponse)
def update_visit(case_id: int, visit_id: int, payload: CaseVisitUpdate, db: Session = Depends(get_db), user: User = Depends(require_any_permission("visits.edit", "cases.edit_assigned"))):
    _case(db, case_id, user); visit = _visit(db, case_id, visit_id); _assert_assigned(visit, user)
    data = payload.model_dump(exclude_unset=True); _dimensions(db, data)
    if user.role == "Executive" and not has_permission(user, "visits.edit"):
        allowed = {"status", "negative_reason", "remarks", "next_follow_up_at", "follow_up_note"}
        forbidden = set(data) - allowed
        if forbidden: raise HTTPException(status_code=403, detail=f"Executives cannot update: {', '.join(sorted(forbidden))}")
    old_status = visit.status
    new_status = data.get("status", old_status)
    if new_status == "Pending": data["closed_date"] = None
    elif old_status == "Pending" and new_status in {"Positive", "Negative"}: data["closed_date"] = date.today()
    activities = []
    for field, value in data.items():
        old = getattr(visit, field)
        if old != value:
            kind = "VISIT_STATUS_CHANGED" if field == "status" else "VISIT_EXECUTIVE_CHANGED" if field == "executive" else "VISIT_UPDATED"
            activities.append(_activity(case_id, kind, user, visit, field, old, value)); setattr(visit, field, value)
    visit.updated_by_user_id = user.id
    try:
        db.add_all(activities); db.commit(); db.refresh(visit)
    except Exception:
        db.rollback(); raise
    return visit


@router.delete("/{visit_id}", response_model=MessageResponse)
def delete_visit(case_id: int, visit_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("visits.delete"))):
    parent = _case(db, case_id, user); visit = _visit(db, case_id, visit_id)
    if user.role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admin may delete a visit")
    visit_count = db.scalar(select(func.count(CaseVisit.id)).where(CaseVisit.case_id == case_id)) or 0
    if visit_count == 1:
        protected = db.scalar(select(Billing.id).where(Billing.case_id == case_id).limit(1)) is not None
        protected = protected or db.scalar(
            select(BankMonthlyBillingSnapshot.id)
            .join(BillingMonth, BillingMonth.id == BankMonthlyBillingSnapshot.billing_month_id)
            .where(BankMonthlyBillingSnapshot.case_id == case_id, BillingMonth.status == "FINALIZED").limit(1)
        ) is not None
        if protected:
            raise HTTPException(status_code=409, detail="This visit is part of finalized billing or payment history and cannot be deleted.")
        try:
            db.execute(delete(CaseActivity).where(CaseActivity.case_id == case_id))
            db.delete(visit); db.delete(parent); db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(status_code=409, detail="This visit has protected history and cannot be deleted.") from exc
        return {"message": f"Only visit {visit_id} and its parent case were deleted successfully"}
    activity = _activity(case_id, "VISIT_DELETED", user, visit)
    db.delete(visit); db.add(activity); db.commit()
    return {"message": f"Visit with id {visit_id} deleted successfully"}
