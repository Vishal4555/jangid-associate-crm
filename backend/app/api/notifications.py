from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_permission
from app.db.database import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import get_notifications


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def read_notifications(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("notifications.view")),
):
    executive_scope = (user.executive.full_name if user.executive else "__unlinked_executive__") if user.role == "Executive" else None
    return get_notifications(db, executive_scope=executive_scope)
