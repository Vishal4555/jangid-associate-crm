from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import exists, or_, select
from sqlalchemy.orm import Session

from app.core.security import require_permission
from app.core.company_scope import assigned_company_ids
from app.db.database import get_db
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.user import User
from app.schemas.case import CaseResponse


router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


def _scope(stmt, user: User):
    ids = assigned_company_ids(user)
    if ids is not None: stmt = stmt.where(Case.company_id.in_(ids))
    if user.role == "Executive":
        name = user.executive.full_name if user.executive else "__unlinked_executive__"
        stmt = stmt.where(or_(Case.executive == name, exists(select(CaseVisit.id).where(CaseVisit.case_id == Case.id, CaseVisit.executive == name))))
    return stmt


def _get_server_now() -> datetime:
    return datetime.now()


@router.get("/today", response_model=list[CaseResponse])
def get_today_follow_ups(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("followups.view")),
):
    today_start = datetime.combine(_get_server_now().date(), time.min)
    tomorrow_start = today_start + timedelta(days=1)
    stmt = (
        select(Case)
        .where(
            Case.next_follow_up_at >= today_start,
            Case.next_follow_up_at < tomorrow_start,
        )
        .order_by(Case.next_follow_up_at.asc())
    )
    return db.scalars(_scope(stmt, user)).all()


@router.get("/upcoming", response_model=list[CaseResponse])
def get_upcoming_follow_ups(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("followups.view")),
):
    today_start = datetime.combine(_get_server_now().date(), time.min)
    tomorrow_start = today_start + timedelta(days=1)
    stmt = (
        select(Case)
        .where(Case.next_follow_up_at >= tomorrow_start)
        .order_by(Case.next_follow_up_at.asc())
        .limit(20)
    )
    return db.scalars(_scope(stmt, user)).all()


@router.get("/overdue", response_model=list[CaseResponse])
def get_overdue_follow_ups(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("followups.view")),
):
    now = _get_server_now()
    stmt = (
        select(Case)
        .where(Case.next_follow_up_at < now)
        .order_by(Case.next_follow_up_at.asc())
    )
    return db.scalars(_scope(stmt, user)).all()
