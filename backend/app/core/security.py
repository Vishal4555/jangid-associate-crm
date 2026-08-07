from datetime import datetime, timedelta, timezone
import os
import re
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, UserSession
from app.core.permissions import ALL_PERMISSION_CODES


SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> None:
    if len(password) < 12 or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"\d", password) or not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must be at least 12 characters and include uppercase, lowercase, number, and special character")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("Token is invalid") from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        if user_id is None or jti is None:
            raise ValueError("Token subject is missing")
        user = db.get(User, int(user_id))
    except (ValueError, TypeError):
        user = None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    session = db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.jti == jti).first()
    if session is None or session.revoked_at is not None:
        raise HTTPException(status_code=401, detail="SESSION_REVOKED", headers={"WWW-Authenticate": "Bearer"})
    session.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    user.current_session_jti = jti

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


def require_roles(*allowed_roles: str):
    def role_dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource"
            )
        return current_user

    return role_dependency


def has_permission(user: User, code: str) -> bool:
    if not user.is_active: return False
    if user.role == "Admin": return code in ALL_PERMISSION_CODES
    return code in user.permissions


def require_permission(code: str):
    if code not in ALL_PERMISSION_CODES: raise ValueError(f"Unknown permission: {code}")
    def permission_dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if not has_permission(current_user, code):
            raise HTTPException(status_code=403, detail=f"Missing permission: {code}")
        return current_user
    return permission_dependency


def require_any_permission(*codes: str):
    unknown = set(codes) - ALL_PERMISSION_CODES
    if unknown: raise ValueError(f"Unknown permissions: {sorted(unknown)}")
    def permission_dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if not any(has_permission(current_user, code) for code in codes):
            raise HTTPException(status_code=403, detail=f"One of these permissions is required: {', '.join(codes)}")
        return current_user
    return permission_dependency
