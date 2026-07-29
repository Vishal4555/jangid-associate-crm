from pathlib import Path
import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.db.base

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.masters import router as masters_router
from app.api.users import router as users_router
from app.db.database import Base, engine, get_db
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate, MessageResponse

app = FastAPI(
    title="JANGID ASSOCIATE CRM",
    version="1.0.0"
)

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
app.include_router(masters_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(auth_router, prefix="/api")
app.include_router(masters_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(users_router, prefix="/api")

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
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))

        return {
            "status": "success",
            "database": result.scalar()
        }


@app.get("/cases", response_model=list[CaseResponse])
@app.get("/api/cases", response_model=list[CaseResponse], include_in_schema=False)
def get_cases(request: Request, db: Session = Depends(get_db)):
    accepts_html = "text/html" in request.headers.get("accept", "")
    if FRONTEND_INDEX_FILE.exists() and accepts_html:
        return FileResponse(FRONTEND_INDEX_FILE)

    stmt = select(Case).order_by(Case.id.asc())
    return db.scalars(stmt).all()


@app.get("/cases/{id}", response_model=CaseResponse)
@app.get("/api/cases/{id}", response_model=CaseResponse, include_in_schema=False)
def get_case(id: int, db: Session = Depends(get_db)):
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
def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    new_case = Case(**case.model_dump())

    try:
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Case number already exists"
        )

    return new_case


@app.put("/cases/{id}", response_model=CaseResponse)
@app.put("/api/cases/{id}", response_model=CaseResponse, include_in_schema=False)
def update_case(id: int, case_update: CaseUpdate, db: Session = Depends(get_db)):
    existing_case = db.get(Case, id)
    if existing_case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found"
        )

    update_data = case_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_case, field, value)

    try:
        db.commit()
        db.refresh(existing_case)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Case number already exists"
        )

    return existing_case


@app.delete("/cases/{id}", response_model=MessageResponse)
@app.delete("/api/cases/{id}", response_model=MessageResponse, include_in_schema=False)
def delete_case(id: int, db: Session = Depends(get_db)):
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
    
