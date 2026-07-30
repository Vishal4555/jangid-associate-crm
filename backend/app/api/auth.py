from collections import deque
from ipaddress import ip_address
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import get_current_active_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import ProfileUpdate, Token, UserLogin, UserResponse
from app.services.auth_service import authenticate_user, build_token_response


router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW_SECONDS = 15 * 60
STALE_ATTEMPT_CLEANUP_INTERVAL_SECONDS = 60
failed_login_attempts: dict[str, deque[float]] = {}
failed_login_attempts_lock = Lock()
last_stale_attempt_cleanup = 0.0


def _get_client_ip(request: Request) -> str:
    proxy_ip = request.client.host if request.client else None
    if proxy_ip in {"127.0.0.1", "::1"}:
        real_ip = request.headers.get("X-Real-IP", "").strip()
        try:
            if real_ip:
                return str(ip_address(real_ip))
        except ValueError:
            pass
    return proxy_ip or "unknown"


def _cleanup_stale_attempts(now: float) -> None:
    global last_stale_attempt_cleanup

    if now - last_stale_attempt_cleanup < STALE_ATTEMPT_CLEANUP_INTERVAL_SECONDS:
        return

    cutoff = now - LOGIN_ATTEMPT_WINDOW_SECONDS
    for client_ip, attempts in list(failed_login_attempts.items()):
        if not attempts or attempts[-1] <= cutoff:
            failed_login_attempts.pop(client_ip, None)
    last_stale_attempt_cleanup = now


def _prune_failed_attempts(client_ip: str, now: float) -> deque[float]:
    attempts = failed_login_attempts.setdefault(client_ip, deque())
    cutoff = now - LOGIN_ATTEMPT_WINDOW_SECONDS
    while attempts and attempts[0] <= cutoff:
        attempts.popleft()
    return attempts


@router.post("/login", response_model=Token)
def login(request: Request, login_data: UserLogin, db: Session = Depends(get_db)):
    client_ip = _get_client_ip(request)
    with failed_login_attempts_lock:
        now = monotonic()
        _cleanup_stale_attempts(now)
        attempts = _prune_failed_attempts(client_ip, now)
        if len(attempts) >= MAX_FAILED_LOGIN_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later.",
            )

    user = authenticate_user(db, login_data)
    if user is None:
        with failed_login_attempts_lock:
            now = monotonic()
            attempts = _prune_failed_attempts(client_ip, now)
            attempts.append(now)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    with failed_login_attempts_lock:
        failed_login_attempts.pop(client_ip, None)
    return build_token_response(user)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if payload.email and payload.email != current_user.email:
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unable to update profile")

    return current_user
