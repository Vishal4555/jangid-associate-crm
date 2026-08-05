from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.database import get_db
from app.models.case import Case
from app.models.case_activity import CaseActivity
from app.models.case_visit import CaseVisit
from app.models.master import District
from app.models.user import User
from app.schemas.case import MessageResponse
from app.schemas.case_visit import CaseVisitCreate, CaseVisitResponse, CaseVisitUpdate

router = APIRouter(prefix="/cases/{case_id}/visits", tags=["case visits"])


def _case(db: Session, case_id: int) -> Case:
    item = db.get(Case, case_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Case with id {case_id} not found")
    return item


def _visit(db: Session, case_id: int, visit_id: int) -> CaseVisit:
    item = db.scalar(select(CaseVisit).where(CaseVisit.id == visit_id, CaseVisit.case_id == case_id))
    if item is None:
        raise HTTPException(status_code=404, detail=f"Visit with id {visit_id} not found for case {case_id}")
    return item


def _dimensions(db: Session, data: dict) -> None:
    if "district_id" not in data:
        return
    district_id = data.get("district_id")
    if district_id is None:
        data["district"] = None
        return
    district = db.get(District, district_id)
    if district is None or not district.is_active:
        raise HTTPException(status_code=422, detail="Active Rajasthan district not found")
    data["district"] = district.name


def _activity(case_id: int, kind: str, user: User, visit: CaseVisit, field=None, old=None, new=None):
    return CaseActivity(case_id=case_id, activity_type=kind, field_name=field,
        old_value=None if old is None else str(old), new_value=None if new is None else str(new),
        performed_by_user_id=user.id, performed_by_name=user.full_name,
        remarks=f"Visit #{visit.id} ({visit.visit_type})")


@router.get("", response_model=list[CaseVisitResponse])
def list_visits(case_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    _case(db, case_id)
    return db.scalars(select(CaseVisit).where(CaseVisit.case_id == case_id).order_by(CaseVisit.id)).all()


@router.post("", response_model=CaseVisitResponse, status_code=status.HTTP_201_CREATED)
def create_visit(case_id: int, payload: CaseVisitCreate, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    _case(db, case_id)
    data = payload.model_dump()
    _dimensions(db, data)
    data["closed_date"] = date.today() if data["status"] in {"Positive", "Negative"} else None
    visit = CaseVisit(case_id=case_id, created_by_user_id=user.id, updated_by_user_id=user.id, **data)
    try:
        db.add(visit); db.flush(); db.add(_activity(case_id, "VISIT_CREATED", user, visit)); db.commit(); db.refresh(visit)
    except Exception:
        db.rollback(); raise
    return visit


@router.get("/{visit_id}", response_model=CaseVisitResponse)
def get_visit(case_id: int, visit_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_active_user)):
    _case(db, case_id)
    return _visit(db, case_id, visit_id)


@router.put("/{visit_id}", response_model=CaseVisitResponse)
def update_visit(case_id: int, visit_id: int, payload: CaseVisitUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    _case(db, case_id); visit = _visit(db, case_id, visit_id)
    data = payload.model_dump(exclude_unset=True); _dimensions(db, data)
    old_status = visit.status
    new_status = data.get("status", old_status)
    if new_status == "Pending": data["closed_date"] = None
    elif old_status == "Pending" and new_status in {"Positive", "Negative"}: data["closed_date"] = date.today()
    activities = []
    for field, value in data.items():
        old = getattr(visit, field)
        if old != value:
            kind = "VISIT_STATUS_CHANGED" if field == "status" else "VISIT_EXECUTIVE_CHANGED" if field == "executive" else "VISIT_UPDATED"
            activities.append(_activity(case_id, kind, user, visit, field, old, value)); setattr(visit, field, value)
    visit.updated_by_user_id = user.id
    try:
        db.add_all(activities); db.commit(); db.refresh(visit)
    except Exception:
        db.rollback(); raise
    return visit


@router.delete("/{visit_id}", response_model=MessageResponse)
def delete_visit(case_id: int, visit_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    _case(db, case_id); visit = _visit(db, case_id, visit_id)
    activity = _activity(case_id, "VISIT_DELETED", user, visit)
    db.delete(visit); db.add(activity); db.commit()
    return {"message": f"Visit with id {visit_id} deleted successfully"}
