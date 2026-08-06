from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, hash_password, has_permission, require_any_permission, require_permission
from app.db.database import get_db
from app.models.master import Company, Executive
from app.models.user import User, UserAuditLog, UserCompany
from app.schemas.auth import PasswordReset, UserCreate, UserResponse, UserUpdate
from app.schemas.permission import UserPermissionsResponse, UserPermissionsUpdate
from app.services.permission_service import grant_default_permissions, replace_permissions
from app.schemas.user_company import AssignedCompaniesResponse, UserCompaniesUpdate


router = APIRouter(prefix="/users", tags=["users"])
me_router = APIRouter(tags=["company assignments"])
read_access = Depends(require_permission("users.view"))


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _clean(value: str) -> str:
    return value.strip()


def _assert_unique_identity(db: Session, username: str, email: str, exclude_id: int | None = None) -> None:
    query = select(User).where(or_(func.lower(User.username) == username.casefold(), func.lower(User.email) == email.casefold()))
    if exclude_id is not None:
        query = query.where(User.id != exclude_id)
    if db.scalar(query) is not None:
        raise HTTPException(status_code=409, detail="Username or email already exists")


def _validate_link(db: Session, role: str, executive_id: int | None, is_active: bool, exclude_id: int | None = None) -> None:
    if role == "Executive":
        if executive_id is None:
            raise HTTPException(status_code=422, detail="Executive users must be linked to an Executive Master record")
        executive = db.get(Executive, executive_id)
        if executive is None:
            raise HTTPException(status_code=422, detail="Executive Master record not found")
        if is_active and executive.status != "Active":
            raise HTTPException(status_code=422, detail="Active Executive users require an active Executive Master record")
        duplicate = select(User).where(User.executive_id == executive_id, User.is_active.is_(True))
        if exclude_id is not None:
            duplicate = duplicate.where(User.id != exclude_id)
        if is_active and db.scalar(duplicate) is not None:
            raise HTTPException(status_code=409, detail="This Executive Master record is already linked to an active user")
    elif executive_id is not None:
        raise HTTPException(status_code=422, detail="Only Executive users can have an Executive link")


def _guard_admin_status(db: Session, user: User, current_user: User, new_role: str, new_active: bool) -> None:
    if user.id == current_user.id and not new_active:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account")
    removes_active_admin = user.role == "Admin" and user.is_active and (new_role != "Admin" or not new_active)
    if removes_active_admin:
        active_admins = db.scalar(select(func.count()).select_from(User).where(User.role == "Admin", User.is_active.is_(True))) or 0
        if active_admins <= 1:
            raise HTTPException(status_code=409, detail="The last active Admin cannot be deactivated or reassigned")


def _audit(db: Session, target: User, actor: User, action: str, old=None, new=None) -> None:
    db.add(UserAuditLog(target_user_id=target.id, actor_user_id=actor.id, action=action,
        old_value=None if old is None else str(old), new_value=None if new is None else str(new)))


@router.get("", response_model=list[UserResponse])
def list_users(search: str | None = None, role: str | None = None, is_active: bool | None = Query(None),
    db: Session = Depends(get_db), _: User = read_access):
    statement = select(User).order_by(User.id.asc())
    if search:
        term = f"%{search.strip()}%"
        statement = statement.where(or_(User.full_name.ilike(term), User.username.ilike(term), User.email.ilike(term), User.mobile.ilike(term)))
    if role:
        if role not in {"Admin", "Manager", "Executive"}: raise HTTPException(status_code=422, detail="Invalid role filter")
        statement = statement.where(User.role == role)
    if is_active is not None: statement = statement.where(User.is_active == is_active)
    return db.scalars(statement).all()


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db), _: User = read_access):
    return get_user_or_404(db, user_id)


@router.post("", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), actor: User = Depends(require_permission("users.create"))):
    username, email = _clean(payload.username), _clean(str(payload.email)).lower()
    _assert_unique_identity(db, username, email)
    _validate_link(db, payload.role, payload.executive_id, payload.is_active)
    try:
        user = User(full_name=_clean(payload.full_name), username=username, email=email, mobile=_clean(payload.mobile) if payload.mobile else None,
            password_hash=hash_password(payload.password), role=payload.role, is_active=payload.is_active, executive_id=payload.executive_id)
        db.add(user); db.flush(); grant_default_permissions(db, user, actor.id); _audit(db, user, actor, "USER_CREATED", new=f"role={user.role}, active={user.is_active}")
        db.commit(); db.refresh(user); return user
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=422, detail=str(exc))
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail="Username or email already exists")


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), actor: User = Depends(require_any_permission("users.edit", "users.deactivate"))):
    user = get_user_or_404(db, user_id); values = payload.model_dump(exclude_unset=True)
    if actor.role != "Admin" and (user.role == "Admin" or values.get("role") == "Admin"):
        raise HTTPException(status_code=403, detail="Only Admins can modify or assign the Admin role")
    non_status_fields = set(values) - {"is_active"}
    if non_status_fields and not has_permission(actor, "users.edit"):
        raise HTTPException(status_code=403, detail="Missing permission: users.edit")
    if "is_active" in values and values["is_active"] != user.is_active and not has_permission(actor, "users.deactivate"):
        raise HTTPException(status_code=403, detail="Missing permission: users.deactivate")
    username = _clean(values.get("username", user.username)); email = _clean(str(values.get("email", user.email))).lower()
    role = values.get("role", user.role); active = values.get("is_active", user.is_active)
    executive_id = values.get("executive_id", user.executive_id)
    if role != "Executive" and "role" in values and "executive_id" not in values: executive_id = None
    _assert_unique_identity(db, username, email, user.id); _validate_link(db, role, executive_id, active, user.id)
    _guard_admin_status(db, user, actor, role, active)
    old_role, old_active, old_link = user.role, user.is_active, user.executive_id
    user.full_name = _clean(values.get("full_name", user.full_name)); user.username = username; user.email = email
    if "mobile" in values: user.mobile = _clean(values["mobile"]) if values["mobile"] else None
    user.role, user.is_active, user.executive_id = role, active, executive_id
    if old_role != role: _audit(db, user, actor, "ROLE_CHANGED", old_role, role)
    if old_active != active: _audit(db, user, actor, "STATUS_CHANGED", old_active, active)
    if old_link != executive_id: _audit(db, user, actor, "EXECUTIVE_LINK_CHANGED", old_link, executive_id)
    if old_role != role: grant_default_permissions(db, user, actor.id)
    try: db.commit(); db.refresh(user); return user
    except IntegrityError: db.rollback(); raise HTTPException(status_code=409, detail="Username or email already exists")


@router.post("/{user_id}/reset-password", status_code=204)
def reset_password(user_id: int, payload: PasswordReset, db: Session = Depends(get_db), actor: User = Depends(require_permission("users.reset_password"))):
    user = get_user_or_404(db, user_id)
    try: user.password_hash = hash_password(payload.password)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc))
    _audit(db, user, actor, "PASSWORD_RESET"); db.commit()


@router.delete("/{user_id}", status_code=405)
def delete_user(user_id: int, _: User = Depends(require_permission("users.deactivate"))):
    raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Users cannot be deleted; deactivate the account instead")


@router.get("/{user_id}/permissions", response_model=UserPermissionsResponse)
def get_user_permissions(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("users.view"))):
    user = get_user_or_404(db, user_id)
    return {"user_id": user.id, "permission_codes": user.permissions}


@router.put("/{user_id}/permissions", response_model=UserPermissionsResponse)
def update_user_permissions(user_id: int, payload: UserPermissionsUpdate, db: Session = Depends(get_db), actor: User = Depends(require_permission("users.manage_permissions"))):
    user = get_user_or_404(db, user_id)
    try: old, new = replace_permissions(db, user, set(payload.permission_codes), actor)
    except ValueError as exc: db.rollback(); raise HTTPException(status_code=422, detail=str(exc))
    if new - old: _audit(db, user, actor, "PERMISSION_GRANTED", sorted(old), sorted(new))
    if old - new: _audit(db, user, actor, "PERMISSION_REMOVED", sorted(old), sorted(new))
    db.commit(); db.refresh(user)
    return {"user_id": user.id, "permission_codes": user.permissions}


@router.get("/{user_id}/companies", response_model=AssignedCompaniesResponse)
def get_user_companies(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_permission("users.view"))):
    user = get_user_or_404(db, user_id)
    return {"all_companies": user.role == "Admin", "companies": [row.company for row in user.company_assignments]}


@router.put("/{user_id}/companies", response_model=AssignedCompaniesResponse)
def update_user_companies(user_id: int, payload: UserCompaniesUpdate, db: Session = Depends(get_db), actor: User = Depends(require_permission("users.manage_permissions"))):
    if actor.role != "Admin": raise HTTPException(status_code=403, detail="Only Admins can change company assignments")
    user = get_user_or_404(db, user_id); company_ids = set(payload.company_ids)
    companies = db.scalars(select(Company).where(Company.id.in_(company_ids))).all() if company_ids else []
    if len(companies) != len(company_ids): raise HTTPException(status_code=422, detail="One or more companies were not found")
    old = sorted(row.company_id for row in user.company_assignments)
    for row in list(user.company_assignments): db.delete(row)
    db.flush()
    for company_id in sorted(company_ids): db.add(UserCompany(user_id=user.id, company_id=company_id, assigned_by_user_id=actor.id))
    _audit(db, user, actor, "COMPANY_ASSIGNMENTS_CHANGED", old, sorted(company_ids)); db.commit(); db.refresh(user)
    return {"all_companies": user.role == "Admin", "companies": [row.company for row in user.company_assignments]}


@me_router.get("/me/assigned-companies", response_model=AssignedCompaniesResponse)
def my_assigned_companies(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    if user.role == "Admin": return {"all_companies": True, "companies": []}
    return {"all_companies": False, "companies": [row.company for row in user.company_assignments]}
