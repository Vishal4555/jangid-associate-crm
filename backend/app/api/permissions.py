from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_permission
from app.db.database import get_db
from app.models.user import Permission, User
from app.schemas.permission import PermissionResponse


router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=list[PermissionResponse])
def list_permissions(db: Session = Depends(get_db), _: User = Depends(require_permission("users.manage_permissions"))):
    return db.scalars(select(Permission).where(Permission.is_active.is_(True)).order_by(Permission.module, Permission.code)).all()
