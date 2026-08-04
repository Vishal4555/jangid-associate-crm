import logging
from datetime import date, datetime
from pathlib import Path
import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.db.base

from app.api.auth import router as auth_router
from app.api.billing import router as billing_router
from app.api.payout_rates import bulk_router as payout_rates_bulk_router, router as payout_rates_router
from app.api.dashboard import router as dashboard_router
from app.api.follow_ups import router as follow_ups_router
from app.api.masters import router as masters_router
from app.api.notifications import router as notifications_router
from app.api.users import router as users_router
from app.core.security import get_current_active_user
from app.db.database import Base, engine, get_db
from app.models.case import Case
from app.models.case_activity import CaseActivity
from app.models.master import Company, District, Bank
from app.models.user import User
from app.schemas.case import (
    CaseActivityResponse,
    CaseCreate,
    CaseResponse,
    CaseUpdate,
    MessageResponse,
)

logger = logging.getLogger(__name__)
MAX_REQUEST_BODY_SIZE = 2 * 1024 * 1024

ACTIVITY_TYPES_BY_FIELD = {
    "los_no": "LOS_NUMBER_CHANGED",
    "status": "STATUS_CHANGED",
    "executive": "EXECUTIVE_CHANGED",
    "bank": "BANK_CHANGED",
    "company": "COMPANY_CHANGED",
    "district": "DISTRICT_CHANGED",
    "city": "CITY_CHANGED",
    "address": "ADDRESS_CHANGED",
    "applicant": "APPLICANT_CHANGED",
    "mobile": "MOBILE_CHANGED",
    "next_follow_up_at": "FOLLOW_UP_CHANGED",
    "follow_up_note": "FOLLOW_UP_NOTE_CHANGED",
    "closed_date": "CLOSED_DATE_CHANGED",
}
INITIAL_ACTIVITY_FIELDS = (
    "los_no",
    "status",
    "executive",
    "bank",
    "company",
    "district",
    "city",
    "applicant",
    "mobile",
    "receive_date",
    "address",
    "branch",
    "loan_type",
    "product_type",
    "remarks",
    "landmark",
)


def _activity_value(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _case_activity(
    case_id: int,
    activity_type: str,
    current_user: User,
    field_name: str | None = None,
    old_value=None,
    new_value=None,
) -> CaseActivity:
    return CaseActivity(
        case_id=case_id,
        activity_type=activity_type,
        field_name=field_name,
        old_value=_activity_value(old_value),
        new_value=_activity_value(new_value),
        performed_by_user_id=current_user.id,
        performed_by_name=current_user.full_name,
    )


def _validate_case_dimensions(db: Session, data: dict) -> None:
    company_id, district_id = data.get("company_id"), data.get("district_id")
    if company_id is not None:
        company = db.get(Company, company_id)
        if company is None or not company.is_active: raise HTTPException(status_code=422, detail="Active company not found")
        data["company"] = company.name
    if district_id is not None:
        district = db.get(District, district_id)
        if district is None or not district.is_active: raise HTTPException(status_code=422, detail="Active Rajasthan district not found")
        data["district"] = district.name
    if data.get("bank"):
        bank = db.scalar(select(Bank).where(Bank.name == data["bank"]))
        if bank is None:
            raise HTTPException(status_code=422, detail="Bank not found")

app = FastAPI(
    title="JANGID ASSOCIATE CRM",
    version="1.0.0"
)


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    logger.exception("Unhandled exception while processing request", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.middleware("http")
async def limit_request_body_size(request: Request, call_next):
    if request.method != "GET":
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                body_size = int(content_length)
            except ValueError:
                pass
            else:
                if body_size > MAX_REQUEST_BODY_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large"},
                    )
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }
    for header, value in security_headers.items():
        if header not in response.headers:
            response.headers[header] = value
    return response


FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"


def _get_allowed_cors_origins() -> list[str]:
    configured = os.getenv("CORS_ALLOW_ORIGINS", "")
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def _resolve_frontend_file(relative_path: str) -> Path | None:
    """Resolve a file path under frontend dist and prevent path traversal."""
    if not FRONTEND_DIST_DIR.exists():
        return None

    requested = relative_path.lstrip("/")
    candidate = (FRONTEND_DIST_DIR / requested).resolve()

    try:
        candidate.relative_to(FRONTEND_DIST_DIR.resolve())
    except ValueError:
        return None

    if candidate.is_file():
        return candidate

    return None

allowed_cors_origins = _get_allowed_cors_origins()
if allowed_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(payout_rates_router)
app.include_router(payout_rates_bulk_router)
app.include_router(masters_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(notifications_router)
app.include_router(auth_router, prefix="/api")
app.include_router(billing_router, prefix="/api", include_in_schema=False)
app.include_router(payout_rates_router, prefix="/api", include_in_schema=False)
app.include_router(payout_rates_bulk_router, prefix="/api", include_in_schema=False)
app.include_router(masters_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(notifications_router, prefix="/api", include_in_schema=False)
app.include_router(follow_ups_router)
app.include_router(follow_ups_router, prefix="/api", include_in_schema=False)

if (FRONTEND_DIST_DIR / "assets").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST_DIR / "assets"),
        name="frontend-assets",
    )


@app.get("/")
def root():
    if FRONTEND_INDEX_FILE.exists():
        return FileResponse(FRONTEND_INDEX_FILE)

    return {
        "message": "JANGID Associate CRM API Running"
    }


@app.get("/db-test")
def db_test(_: User = Depends(get_current_active_user)):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))

        return {
            "status": "success",
            "database": result.scalar()
        }


@app.get("/cases", response_model=list[CaseResponse])
@app.get("/api/cases", response_model=list[CaseResponse], include_in_schema=False)
def get_cases(
    request: Request,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    accepts_html = "text/html" in request.headers.get("accept", "")
    if FRONTEND_INDEX_FILE.exists() and accepts_html:
        return FileResponse(FRONTEND_INDEX_FILE)

    stmt = select(Case).order_by(Case.id.asc())
    return db.scalars(stmt).all()


@app.get("/cases/{id}", response_model=CaseResponse)
@app.get("/api/cases/{id}", response_model=CaseResponse, include_in_schema=False)
def get_case(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    case = db.get(Case, id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found"
        )
    return case


@app.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
@app.post(
    "/api/cases",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_case(
    case: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    case_data = case.model_dump()
    _validate_case_dimensions(db, case_data)
    if case_data.get("status") in {"Positive", "Negative"}:
        case_data["closed_date"] = date.today()
    new_case = Case(**case_data)

    try:
        db.add(new_case)
        db.flush()
        db.add(_case_activity(new_case.id, "CASE_CREATED", current_user))
        db.add_all(
            _case_activity(
                new_case.id,
                "FIELD_UPDATED",
                current_user,
                field_name=field,
                new_value=value,
            )
            for field in INITIAL_ACTIVITY_FIELDS
            if (value := getattr(new_case, field)) is not None
            and (not isinstance(value, str) or value.strip())
        )
        db.commit()
        db.refresh(new_case)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Case number already exists"
        )
    except Exception:
        db.rollback()
        raise

    return new_case


@app.put("/cases/{id}", response_model=CaseResponse)
@app.put("/api/cases/{id}", response_model=CaseResponse, include_in_schema=False)
def update_case(
    id: int,
    case_update: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    existing_case = db.get(Case, id)
    if existing_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found"
        )

    update_data = case_update.model_dump(exclude_unset=True)
    dimension_data = {"company_id": update_data.get("company_id", existing_case.company_id),
        "district_id": update_data.get("district_id", existing_case.district_id),
        "bank": update_data.get("bank", existing_case.bank)}
    _validate_case_dimensions(db, dimension_data)
    if "company_id" in update_data: update_data["company"] = dimension_data.get("company")
    if "district_id" in update_data: update_data["district"] = dimension_data.get("district")
    updated_status = update_data.get("status", existing_case.status)
    if updated_status in {"Positive", "Negative"}:
        if existing_case.closed_date is not None:
            update_data["closed_date"] = existing_case.closed_date
        elif update_data.get("closed_date") is None:
            update_data["closed_date"] = date.today()
    else:
        update_data["closed_date"] = None

    activities = []
    for field, value in update_data.items():
        old_value = getattr(existing_case, field)
        if old_value != value:
            activities.append(
                _case_activity(
                    existing_case.id,
                    ACTIVITY_TYPES_BY_FIELD.get(field, "FIELD_UPDATED"),
                    current_user,
                    field_name=field,
                    old_value=old_value,
                    new_value=value,
                )
            )
            setattr(existing_case, field, value)

    try:
        db.add_all(activities)
        db.commit()
        db.refresh(existing_case)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Case number already exists"
        )
    except Exception:
        db.rollback()
        raise

    return existing_case


@app.get("/cases/{id}/activity", response_model=list[CaseActivityResponse])
@app.get(
    "/api/cases/{id}/activity",
    response_model=list[CaseActivityResponse],
    include_in_schema=False,
)
def get_case_activity(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    if db.get(Case, id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found",
        )

    stmt = (
        select(CaseActivity)
        .where(CaseActivity.case_id == id)
        .order_by(CaseActivity.performed_at.desc(), CaseActivity.id.desc())
    )
    return db.scalars(stmt).all()


@app.delete("/cases/{id}", response_model=MessageResponse)
@app.delete("/api/cases/{id}", response_model=MessageResponse, include_in_schema=False)
def delete_case(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    existing_case = db.get(Case, id)
    if existing_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found"
        )

    db.delete(existing_case)
    db.commit()

    return {"message": f"Case with id {id} deleted successfully"}


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_spa_fallback(full_path: str, request: Request):
    frontend_file = _resolve_frontend_file(full_path)
    if frontend_file is not None:
        return FileResponse(frontend_file)

    accepts_html = "text/html" in request.headers.get("accept", "")
    if FRONTEND_INDEX_FILE.exists() and accepts_html:
        return FileResponse(FRONTEND_INDEX_FILE)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    
