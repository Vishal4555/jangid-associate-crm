from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_permission
from app.db.database import get_db
from app.models.case import Case
from app.models.user import User
from app.schemas.case import CaseResponse


router = APIRouter(prefix="/follow-ups", tags=["follow-ups"])


def _scope(stmt, user: User):
    if user.role != "Executive": return stmt
    name = user.executive.full_name if user.executive else "__unlinked_executive__"
    return stmt.where(Case.executive == name)


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
