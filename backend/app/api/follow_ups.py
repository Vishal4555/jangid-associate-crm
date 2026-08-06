from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_permission
from app.core.company_scope import assigned_company_ids
from app.db.database import get_db
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.user import User
from app.schemas.case_visit import CaseVisitListRow


router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


def _scope(stmt, user: User):
    ids = assigned_company_ids(user)
    if ids is not None: stmt = stmt.where(Case.company_id.in_(ids))
    if user.role == "Executive":
        name = user.executive.full_name if user.executive else "__unlinked_executive__"
        stmt = stmt.where(CaseVisit.executive == name)
    return stmt


def _rows(db: Session, stmt, user: User):
    results = db.execute(_scope(stmt, user)).all()
    return [{
        "visit_id": visit.id, "case_id": parent.id, "visit_type": visit.visit_type,
        "los_no": parent.los_no, "company_id": parent.company_id, "company": parent.company,
        "bank": parent.bank, "applicant": parent.applicant, "mobile": parent.mobile,
        "loan_type": parent.loan_type, "receive_date": visit.receive_date,
        "closed_date": visit.closed_date, "tat_days": visit.tat_days, "address": visit.address,
        "district_id": visit.district_id, "district": visit.district, "city": visit.city,
        "landmark": visit.landmark, "executive": visit.executive, "status": visit.status,
        "negative_reason": visit.negative_reason, "remarks": visit.remarks,
        "next_follow_up_at": visit.next_follow_up_at, "follow_up_note": visit.follow_up_note,
        "created_at": visit.created_at, "updated_at": visit.updated_at,
    } for visit, parent in results]


def _get_server_now() -> datetime:
    return datetime.now()


@router.get("/today", response_model=list[CaseVisitListRow])
def get_today_follow_ups(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("followups.view")),
):
    today_start = datetime.combine(_get_server_now().date(), time.min)
    tomorrow_start = today_start + timedelta(days=1)
    stmt = (
        select(CaseVisit, Case).join(Case, Case.id == CaseVisit.case_id)
        .where(
            CaseVisit.next_follow_up_at >= today_start,
            CaseVisit.next_follow_up_at < tomorrow_start,
        )
        .order_by(CaseVisit.next_follow_up_at.asc())
    )
    return _rows(db, stmt, user)


@router.get("/upcoming", response_model=list[CaseVisitListRow])
def get_upcoming_follow_ups(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("followups.view")),
):
    today_start = datetime.combine(_get_server_now().date(), time.min)
    tomorrow_start = today_start + timedelta(days=1)
    stmt = (
        select(CaseVisit, Case).join(Case, Case.id == CaseVisit.case_id)
        .where(CaseVisit.next_follow_up_at >= tomorrow_start)
        .order_by(CaseVisit.next_follow_up_at.asc())
        .limit(20)
    )
    return _rows(db, stmt, user)


@router.get("/overdue", response_model=list[CaseVisitListRow])
def get_overdue_follow_ups(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("followups.view")),
):
    now = _get_server_now()
    stmt = (
        select(CaseVisit, Case).join(Case, Case.id == CaseVisit.case_id)
        .where(CaseVisit.next_follow_up_at < now)
        .order_by(CaseVisit.next_follow_up_at.asc())
    )
    return _rows(db, stmt, user)
