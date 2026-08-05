from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import has_permission, require_any_permission, require_permission
from app.db.database import get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardPerformanceResponse,
    DashboardSummaryResponse,
    PendingAgeingResponse,
)
from app.services.dashboard_service import (
    get_dashboard_performance,
    get_dashboard_summary,
    get_pending_ageing,
)


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _scope(user: User) -> str | None:
    if user.role != "Executive" or has_permission(user, "reports.view_all"): return None
    if user.executive is None: return "__unlinked_executive__"
    return user.executive.full_name


@router.get("/summary", response_model=DashboardSummaryResponse)
def read_dashboard_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_any_permission("dashboard.view", "reports.view", "reports.view_own")),
):
    return get_dashboard_summary(db, executive_scope=_scope(user))


@router.get("/performance", response_model=DashboardPerformanceResponse)
def read_dashboard_performance(
    from_date: date | None = None,
    to_date: date | None = None,
    executive: str | None = None,
    city: str | None = None,
    bank: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_any_permission("dashboard.view", "reports.view", "reports.view_own")),
):
    return get_dashboard_performance(
        db,
        from_date=from_date,
        to_date=to_date,
        executive=_scope(user) or executive,
        city=city,
        bank=bank,
    )


@router.get("/pending-ageing", response_model=PendingAgeingResponse)
def read_pending_ageing(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("dashboard.view")),
):
    return get_pending_ageing(db, executive_scope=_scope(user))
