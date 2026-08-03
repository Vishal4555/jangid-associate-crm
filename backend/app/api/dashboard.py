from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
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


@router.get("/summary", response_model=DashboardSummaryResponse)
def read_dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return get_dashboard_summary(db)


@router.get("/performance", response_model=DashboardPerformanceResponse)
def read_dashboard_performance(
    from_date: date | None = None,
    to_date: date | None = None,
    executive: str | None = None,
    city: str | None = None,
    bank: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return get_dashboard_performance(
        db,
        from_date=from_date,
        to_date=to_date,
        executive=executive,
        city=city,
        bank=bank,
    )


@router.get("/pending-ageing", response_model=PendingAgeingResponse)
def read_pending_ageing(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return get_pending_ageing(db)
