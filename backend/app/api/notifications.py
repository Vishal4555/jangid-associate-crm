from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import get_notifications


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def read_notifications(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return get_notifications(db)
