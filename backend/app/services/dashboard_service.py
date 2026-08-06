from __future__ import annotations

from datetime import date

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.schemas.dashboard import (
    BankPerformanceResponse, CityPerformanceResponse, DashboardPerformanceResponse,
    DashboardSummaryResponse, ExecutivePerformanceResponse,
    ExecutivePendingAgeingResponse, CityPendingAgeingResponse, PendingAgeingResponse,
    PendingAgeingSummaryResponse, PerformanceSummaryResponse,
)


PENDING_CONDITION = CaseVisit.status == "Pending"
CLOSED_CONDITION = CaseVisit.status.in_(["Positive", "Negative"])
TAT_CONDITION = and_(CLOSED_CONDITION, CaseVisit.receive_date.is_not(None), CaseVisit.closed_date.is_not(None))
TAT_DAYS = CaseVisit.closed_date - CaseVisit.receive_date
TAT_VALUE = case((TAT_CONDITION, TAT_DAYS), else_=None)
PENDING_AGE_DAYS = func.current_date() - CaseVisit.receive_date


def _base_query(*columns):
    return select(*columns).select_from(CaseVisit).join(Case, Case.id == CaseVisit.case_id)


def _scope_conditions(executive_scope: str | None, company_ids: set[int] | None):
    conditions = []
    if executive_scope is not None:
        conditions.append(CaseVisit.executive == executive_scope)
    if company_ids is not None:
        conditions.append(Case.company_id.in_(company_ids))
    return conditions


def get_dashboard_summary(db: Session, executive_scope: str | None = None, company_ids: set[int] | None = None) -> DashboardSummaryResponse:
    today = date.today()
    month_start = today.replace(day=1)
    next_month_start = (month_start.replace(year=month_start.year + 1, month=1)
                        if month_start.month == 12 else month_start.replace(month=month_start.month + 1))
    row = db.execute(_base_query(
        func.count(CaseVisit.id).label("total_cases"),
        func.sum(case((PENDING_CONDITION, 1), else_=0)).label("pending_cases"),
        func.sum(case((CaseVisit.status == "Positive", 1), else_=0)).label("positive_cases"),
        func.sum(case((CaseVisit.status == "Negative", 1), else_=0)).label("negative_cases"),
        func.sum(case((CaseVisit.receive_date == today, 1), else_=0)).label("today_cases"),
        func.sum(case((and_(CaseVisit.receive_date >= month_start, CaseVisit.receive_date < next_month_start), 1), else_=0)).label("this_month_cases"),
    ).where(*_scope_conditions(executive_scope, company_ids))).one()
    return DashboardSummaryResponse(**{name: getattr(row, name) or 0 for name in (
        "total_cases", "pending_cases", "positive_cases", "negative_cases", "today_cases", "this_month_cases")})


def _metrics():
    return (
        func.count(CaseVisit.id).label("total_cases"),
        func.sum(case((PENDING_CONDITION, 1), else_=0)).label("pending"),
        func.sum(case((CaseVisit.status == "Positive", 1), else_=0)).label("positive"),
        func.sum(case((CaseVisit.status == "Negative", 1), else_=0)).label("negative"),
        func.sum(case((CLOSED_CONDITION, 1), else_=0)).label("closed"),
        func.avg(TAT_VALUE).label("average_tat"), func.min(TAT_VALUE).label("fastest_tat"), func.max(TAT_VALUE).label("slowest_tat"),
    )


def _filters(from_date, to_date, executive, city, bank):
    conditions = []
    if from_date is not None: conditions.append(CaseVisit.receive_date >= from_date)
    if to_date is not None: conditions.append(CaseVisit.receive_date <= to_date)
    if executive: conditions.append(CaseVisit.executive == executive)
    if city: conditions.append(CaseVisit.city == city)
    if bank: conditions.append(Case.bank == bank)
    return conditions


def _rounded(value):
    return round(float(value), 2) if value is not None else None


def _group_performance(db, field, conditions):
    label = func.coalesce(func.nullif(func.trim(field), ""), "Unassigned").label("name")
    return db.execute(_base_query(label, *_metrics()).where(*conditions).group_by(label).order_by(label)).all()


def get_dashboard_performance(db: Session, from_date=None, to_date=None, executive=None, city=None, bank=None,
                              company_ids=None, executive_scope=None) -> DashboardPerformanceResponse:
    conditions = _filters(from_date, to_date, executive, city, bank) + _scope_conditions(executive_scope, company_ids)
    summary = db.execute(_base_query(*_metrics()).where(*conditions)).one()
    executives = _group_performance(db, CaseVisit.executive, conditions)
    cities = _group_performance(db, CaseVisit.city, conditions)
    banks = _group_performance(db, Case.bank, conditions)
    return DashboardPerformanceResponse(
        summary=PerformanceSummaryResponse(total_cases=summary.total_cases or 0, pending_cases=summary.pending or 0,
            positive_cases=summary.positive or 0, negative_cases=summary.negative or 0, closed_cases=summary.closed or 0,
            average_tat=_rounded(summary.average_tat)),
        executives=[ExecutivePerformanceResponse(executive_name=r.name, total_cases=r.total_cases or 0,
            pending=r.pending or 0, positive=r.positive or 0, negative=r.negative or 0, closed=r.closed or 0,
            average_tat=_rounded(r.average_tat), fastest_tat=r.fastest_tat, slowest_tat=r.slowest_tat) for r in executives],
        cities=[CityPerformanceResponse(city=r.name, total_cases=r.total_cases or 0, pending=r.pending or 0,
            positive=r.positive or 0, negative=r.negative or 0, average_tat=_rounded(r.average_tat)) for r in cities],
        banks=[BankPerformanceResponse(bank=r.name, total_cases=r.total_cases or 0, pending=r.pending or 0,
            positive=r.positive or 0, negative=r.negative or 0, average_tat=_rounded(r.average_tat)) for r in banks],
    )


def _ageing_metrics():
    dated = CaseVisit.receive_date.is_not(None)
    return (func.count(CaseVisit.id).label("total_pending"),
        func.sum(case((and_(dated, PENDING_AGE_DAYS.between(0, 2)), 1), else_=0)).label("zero_to_two"),
        func.sum(case((and_(dated, PENDING_AGE_DAYS.between(3, 5)), 1), else_=0)).label("three_to_five"),
        func.sum(case((and_(dated, PENDING_AGE_DAYS.between(6, 10)), 1), else_=0)).label("six_to_ten"),
        func.sum(case((and_(dated, PENDING_AGE_DAYS >= 11), 1), else_=0)).label("eleven_plus"))


def _ageing_values(row):
    return {key: getattr(row, key) or 0 for key in ("total_pending", "zero_to_two", "three_to_five", "six_to_ten", "eleven_plus")}


def _group_pending_ageing(db, field, scope):
    label = func.coalesce(func.nullif(func.trim(field), ""), "Unassigned").label("name")
    query = (_base_query(label, *_ageing_metrics()).where(PENDING_CONDITION, *scope).group_by(label)
             .order_by(func.sum(case((and_(CaseVisit.receive_date.is_not(None), PENDING_AGE_DAYS >= 11), 1), else_=0)).desc(),
                       func.count(CaseVisit.id).desc()))
    return db.execute(query).all()


def get_pending_ageing(db: Session, executive_scope=None, company_ids=None) -> PendingAgeingResponse:
    scope = _scope_conditions(executive_scope, company_ids)
    summary = db.execute(_base_query(*_ageing_metrics()).where(PENDING_CONDITION, *scope)).one()
    executives = _group_pending_ageing(db, CaseVisit.executive, scope)
    cities = _group_pending_ageing(db, CaseVisit.city, scope)
    return PendingAgeingResponse(summary=PendingAgeingSummaryResponse(**_ageing_values(summary)),
        executives=[ExecutivePendingAgeingResponse(executive=r.name, **_ageing_values(r)) for r in executives],
        cities=[CityPendingAgeingResponse(city=r.name, **_ageing_values(r)) for r in cities])
