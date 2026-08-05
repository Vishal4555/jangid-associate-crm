from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import ALL_PERMISSION_CODES, PERMISSION_CATALOG, default_permissions
from app.models.user import Permission, User, UserPermission


def ensure_permission_catalog(db: Session) -> dict[str, Permission]:
    existing = {row.code: row for row in db.scalars(select(Permission)).all()}
    for code, name, description, module in PERMISSION_CATALOG:
        row = existing.get(code)
        if row is None:
            row = Permission(code=code, name=name, description=description, module=module, is_active=True)
            db.add(row); existing[code] = row
        else:
            row.name, row.description, row.module = name, description, module
    db.flush()
    return existing


def grant_default_permissions(db: Session, user: User, granted_by_user_id: int | None = None) -> None:
    if user.role == "Admin": return
    catalog = ensure_permission_catalog(db)
    current = {grant.permission.code for grant in user.permission_grants}
    for code in default_permissions(user.role) - current:
        db.add(UserPermission(user_id=user.id, permission_id=catalog[code].id, granted_by_user_id=granted_by_user_id))


def replace_permissions(db: Session, user: User, codes: set[str], actor: User) -> tuple[set[str], set[str]]:
    unknown = codes - ALL_PERMISSION_CODES
    if unknown: raise ValueError(f"Unknown permission codes: {', '.join(sorted(unknown))}")
    if user.role == "Admin": raise ValueError("Admin permissions are implicit and cannot be changed")
    catalog = ensure_permission_catalog(db)
    old = set(user.permissions)
    for grant in list(user.permission_grants): db.delete(grant)
    db.flush()
    for code in sorted(codes):
        db.add(UserPermission(user_id=user.id, permission_id=catalog[code].id, granted_by_user_id=actor.id))
    db.flush()
    return old, codes
