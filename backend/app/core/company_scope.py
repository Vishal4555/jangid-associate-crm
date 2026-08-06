from fastapi import HTTPException
from sqlalchemy import Select

from app.core.security import has_permission
from app.models.user import User


def assigned_company_ids(user: User) -> set[int] | None:
    """None means unrestricted; an empty set means deliberately no access."""
    if user.role == "Admin" or has_permission(user, "companies.view_all"): return None
    return {assignment.company_id for assignment in user.company_assignments}


def apply_company_scope(statement: Select, column, user: User):
    ids = assigned_company_ids(user)
    return statement if ids is None else statement.where(column.in_(ids))


def assert_company_access(user: User, company_id: int | None, *, write: bool = False) -> None:
    if user.role == "Admin" or (write and has_permission(user, "companies.manage_all")) or (not write and has_permission(user, "companies.view_all")): return
    if company_id is None: raise HTTPException(status_code=403, detail="A company assignment is required")
    if company_id not in {assignment.company_id for assignment in user.company_assignments}:
        raise HTTPException(status_code=403, detail="Company is not assigned to this user")
