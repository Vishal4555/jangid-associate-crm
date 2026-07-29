from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard_service import get_dashboard_summary


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def read_dashboard_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return get_dashboard_summary(db)
