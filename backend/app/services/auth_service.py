from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserSession
from uuid import uuid4
from app.schemas.auth import Token, UserCreate, UserLogin
from app.services.permission_service import grant_default_permissions


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    return (
        db.query(User)
        .filter((func.lower(User.username) == identifier.strip().lower()) | (func.lower(User.email) == identifier.strip().lower()))
        .first()
    )


def authenticate_user(db: Session, login_data: UserLogin) -> User | None:
    user = get_user_by_identifier(db, login_data.username)
    if user is None:
        return None
    if not verify_password(login_data.password, user.password_hash):
        return None
    if not user.is_active:
        return None
    user.last_login = datetime.now(timezone.utc)
    db.flush()
    return user


def create_user(db: Session, user_data: UserCreate) -> User:
    existing_user = get_user_by_identifier(db, user_data.username)
    if existing_user is not None:
        raise ValueError("Username already exists")

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email is not None:
        raise ValueError("Email already exists")

    user = User(
        full_name=user_data.full_name,
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    grant_default_permissions(db, user)
    db.commit()
    db.refresh(user)
    return user


def build_token_response(db: Session, user: User, user_agent: str | None = None, ip_address: str | None = None) -> Token:
    now = datetime.now(timezone.utc)
    locked = db.query(User).filter(User.id == user.id).with_for_update().one()
    if locked.role in {"Manager", "Executive"}:
        db.query(UserSession).filter(UserSession.user_id == locked.id, UserSession.revoked_at.is_(None)).update(
            {UserSession.revoked_at: now, UserSession.revoke_reason: "NEW_LOGIN"}, synchronize_session=False)
    jti = uuid4().hex
    db.add(UserSession(user_id=locked.id, jti=jti, user_agent=user_agent, ip_address=ip_address,
        created_at=now, last_seen_at=now))
    db.commit()
    token = create_access_token({
        "sub": str(locked.id), "username": locked.username, "role": locked.role, "jti": jti,
    })
    return Token(access_token=token, token_type="bearer")
