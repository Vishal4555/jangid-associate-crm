import logging
from datetime import date, datetime
from pathlib import Path
import os
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import and_, delete, exists, func, or_, select, text
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
from app.api.users import me_router as user_company_me_router, router as users_router
from app.api.permissions import router as permissions_router
from app.api.case_visits import list_router as case_visit_list_router, router as case_visits_router
from app.api.case_import import router as case_import_router
from app.core.security import get_current_active_user, has_permission, require_any_permission, require_permission
from app.core.company_scope import assert_company_access, assigned_company_ids
from app.db.database import Base, engine, get_db
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.case_activity import CaseActivity
from app.models.billing import Billing
from app.models.billing_month import BankMonthlyBillingSnapshot, BillingMonth
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


def _normalized_identity(value: str | None) -> str:
    return " ".join((value or "").strip().casefold().split())


def _generated_case_no() -> str:
    return f"JA-{uuid4().hex[:12].upper()}"


def _executive_name(user: User) -> str:
    if user.role != "Executive" or user.executive is None:
        raise HTTPException(status_code=403, detail="Executive account is not linked to an Executive Master record")
    return user.executive.full_name


def _case_visible_to(case_id: int, user: User):
    conditions = []
    company_ids = assigned_company_ids(user)
    if company_ids is not None: conditions.append(Case.company_id.in_(company_ids))
    if user.role == "Executive" and not has_permission(user, "cases.view_all"):
        name = _executive_name(user)
        conditions.append(or_(Case.executive == name, exists(select(CaseVisit.id).where(CaseVisit.case_id == case_id, CaseVisit.executive == name))))
    return and_(*conditions) if conditions else True


def _assert_parent_compatible(existing: Case, data: dict) -> None:
    checks = (
        ("Company", existing.company, data.get("company")),
        ("Bank / Finance Company", existing.bank, data.get("bank")),
        ("Applicant", existing.applicant, data.get("applicant")),
    )
    for label, old, new in checks:
        if _normalized_identity(old) != _normalized_identity(new):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"LOS / Application No already exists with a different {label}.",
            )

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
app.include_router(user_company_me_router)
app.include_router(permissions_router)
app.include_router(notifications_router)
app.include_router(case_visits_router)
app.include_router(case_visit_list_router)
app.include_router(case_import_router)
app.include_router(auth_router, prefix="/api")
app.include_router(billing_router, prefix="/api", include_in_schema=False)
app.include_router(payout_rates_router, prefix="/api", include_in_schema=False)
app.include_router(payout_rates_bulk_router, prefix="/api", include_in_schema=False)
app.include_router(masters_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(user_company_me_router, prefix="/api")
app.include_router(permissions_router, prefix="/api")
app.include_router(notifications_router, prefix="/api", include_in_schema=False)
app.include_router(case_visits_router, prefix="/api", include_in_schema=False)
app.include_router(case_visit_list_router, prefix="/api", include_in_schema=False)
app.include_router(case_import_router, prefix="/api", include_in_schema=False)
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
    current_user: User = Depends(require_permission("cases.view")),
):
    accepts_html = "text/html" in request.headers.get("accept", "")
    if FRONTEND_INDEX_FILE.exists() and accepts_html:
        return FileResponse(FRONTEND_INDEX_FILE)

    stmt = select(Case).order_by(Case.id.asc())
    stmt = stmt.where(_case_visible_to(Case.id, current_user))
    return db.scalars(stmt).all()


@app.get("/cases/{id}", response_model=CaseResponse)
@app.get("/api/cases/{id}", response_model=CaseResponse, include_in_schema=False)
def get_case(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cases.view")),
):
    case = db.scalar(select(Case).where(Case.id == id, _case_visible_to(Case.id, current_user)))
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
    current_user: User = Depends(require_permission("cases.create")),
):
    case_data = case.model_dump()
    visit_type = case_data.pop("visit_type", "Residence")
    # case_no supplied by older clients is deliberately ignored for this workflow.
    case_data.pop("case_no", None)
    case_data["los_no"] = (case_data.get("los_no") or "").strip()
    assert_company_access(current_user, case_data.get("company_id"), write=True)
    if not case_data["los_no"]:
        raise HTTPException(status_code=422, detail="LOS / Application No is required")
    _validate_case_dimensions(db, case_data)
    if case_data.get("status") in {"Positive", "Negative"}:
        case_data["closed_date"] = date.today()
    mobile_visit_count = db.scalar(select(func.count(CaseVisit.id)).join(Case).where(Case.mobile == case_data.get("mobile"))) or 0 if case_data.get("mobile") else 0

    try:
        candidates = db.scalars(select(Case).where(
            func.lower(func.trim(Case.los_no)) == case_data["los_no"].casefold(),
            Case.company_id == case_data.get("company_id"),
            func.lower(func.trim(Case.bank)) == _normalized_identity(case_data.get("bank")),
        ).with_for_update()).all()
        matches = [item for item in candidates if _normalized_identity(item.applicant) == _normalized_identity(case_data.get("applicant"))]
        if len(matches) > 1:
            raise HTTPException(status_code=409, detail="Multiple parent cases already use this LOS / Application No; resolve the data before adding a visit.")
        if matches:
            new_case = matches[0]
            result_message = "New visit added to existing application."
        else:
            parent_fields = {key: value for key, value in case_data.items() if key in Case.__table__.columns.keys()}
            new_case = Case(case_no=_generated_case_no(), **parent_fields)
            db.add(new_case)
            db.flush()
            db.add(_case_activity(new_case.id, "CASE_CREATED", current_user))
            db.add_all(
                _case_activity(new_case.id, "FIELD_UPDATED", current_user, field_name=field, new_value=value)
                for field in INITIAL_ACTIVITY_FIELDS
                if (value := getattr(new_case, field)) is not None
                and (not isinstance(value, str) or value.strip())
            )
            result_message = "New application and first visit created."
        first_visit = CaseVisit(
            case_id=new_case.id,
            visit_type=visit_type,
            address=case_data.get("address"),
            district_id=case_data.get("district_id"),
            district=case_data.get("district"),
            city=case_data.get("city"),
            landmark=case_data.get("landmark"),
            executive=case_data.get("executive"),
            status=case_data.get("status") or "Pending",
            negative_reason=case_data.get("negative_reason"),
            receive_date=case_data.get("receive_date"),
            closed_date=case_data.get("closed_date"),
            remarks=case_data.get("remarks"),
            next_follow_up_at=case_data.get("next_follow_up_at"),
            follow_up_note=case_data.get("follow_up_note"),
            created_by_user_id=current_user.id,
            updated_by_user_id=current_user.id,
        )
        db.add(first_visit)
        db.flush()
        db.add(CaseActivity(case_id=new_case.id, activity_type="VISIT_CREATED",
            performed_by_user_id=current_user.id, performed_by_name=current_user.full_name,
            remarks=f"Visit #{first_visit.id} ({first_visit.visit_type})"))
        db.commit()
        db.refresh(new_case)
        new_case.message = result_message + (f" Mobile already exists in {mobile_visit_count} visits." if mobile_visit_count else "")
    except HTTPException:
        db.rollback()
        raise
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
    current_user: User = Depends(require_any_permission("cases.edit", "cases.edit_assigned")),
):
    if current_user.role == "Executive" and not has_permission(current_user, "cases.edit"):
        raise HTTPException(status_code=403, detail="Executives can update only permitted fields on assigned visits")
    existing_case = db.scalar(select(Case).where(Case.id == id, _case_visible_to(Case.id, current_user)))
    if existing_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found"
        )

    update_data = case_update.model_dump(exclude_unset=True)
    if "company_id" in update_data: assert_company_access(current_user, update_data.get("company_id"), write=True)
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
    current_user: User = Depends(require_permission("cases.view")),
):
    if db.scalar(select(Case.id).where(Case.id == id, _case_visible_to(Case.id, current_user))) is None:
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
    current_user: User = Depends(require_permission("cases.delete")),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin may delete a case",
        )

    existing_case = db.get(Case, id)
    if existing_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found"
        )

    protected_message = (
        "This case is part of finalized billing or payment history and cannot be deleted."
    )
    has_billing_history = db.scalar(
        select(Billing.id).where(Billing.case_id == id).limit(1)
    ) is not None
    has_finalized_snapshot = db.scalar(
        select(BankMonthlyBillingSnapshot.id)
        .join(BillingMonth, BillingMonth.id == BankMonthlyBillingSnapshot.billing_month_id)
        .where(
            BankMonthlyBillingSnapshot.case_id == id,
            BillingMonth.status == "FINALIZED",
        )
        .limit(1)
    ) is not None
    if has_billing_history or has_finalized_snapshot:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=protected_message)

    try:
        # These rows are operational and may be removed with an otherwise
        # unreferenced case. The transaction is committed only after the parent.
        db.execute(delete(CaseActivity).where(CaseActivity.case_id == id))
        db.execute(delete(CaseVisit).where(CaseVisit.case_id == id))
        db.delete(existing_case)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.info("Case %s deletion blocked by an immutable dependency", id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=protected_message,
        ) from exc

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
    
