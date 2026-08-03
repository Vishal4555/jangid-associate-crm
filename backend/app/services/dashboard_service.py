from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.case import Case
from app.schemas.dashboard import (
    BankPerformanceResponse,
    CityPerformanceResponse,
    DashboardPerformanceResponse,
    DashboardSummaryResponse,
    ExecutivePerformanceResponse,
    PerformanceSummaryResponse,
)


PENDING_CONDITION = or_(
    Case.status == "Pending",
    Case.status.is_(None),
    func.trim(func.coalesce(Case.status, "")) == "",
)
CLOSED_CONDITION = Case.status.in_(["Positive", "Negative"])
TAT_CONDITION = and_(
    CLOSED_CONDITION,
    Case.receive_date.is_not(None),
    Case.closed_date.is_not(None),
)
TAT_DAYS = Case.closed_date - Case.receive_date
TAT_VALUE = case((TAT_CONDITION, TAT_DAYS), else_=None)


def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
    today = date.today()
    month_start = today.replace(day=1)

    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    summary_query = select(
        func.count(Case.id).label("total_cases"),
        func.sum(case((PENDING_CONDITION, 1), else_=0)).label("pending_cases"),
        func.sum(case((Case.status == "Positive", 1), else_=0)).label("positive_cases"),
        func.sum(case((Case.status == "Negative", 1), else_=0)).label("negative_cases"),
        func.sum(case((Case.receive_date == today, 1), else_=0)).label("today_cases"),
        func.sum(
            case(
                (
                    and_(
                        Case.receive_date >= month_start,
                        Case.receive_date < next_month_start,
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("this_month_cases"),
    )

    row = db.execute(summary_query).one()

    return DashboardSummaryResponse(
        total_cases=row.total_cases or 0,
        pending_cases=row.pending_cases or 0,
        positive_cases=row.positive_cases or 0,
        negative_cases=row.negative_cases or 0,
        today_cases=row.today_cases or 0,
        this_month_cases=row.this_month_cases or 0,
    )


def _metrics():
    return (
        func.count(Case.id).label("total_cases"),
        func.sum(case((PENDING_CONDITION, 1), else_=0)).label("pending"),
        func.sum(case((Case.status == "Positive", 1), else_=0)).label("positive"),
        func.sum(case((Case.status == "Negative", 1), else_=0)).label("negative"),
        func.sum(case((CLOSED_CONDITION, 1), else_=0)).label("closed"),
        func.avg(TAT_VALUE).label("average_tat"),
        func.min(TAT_VALUE).label("fastest_tat"),
        func.max(TAT_VALUE).label("slowest_tat"),
    )


def _filters(
    from_date: date | None,
    to_date: date | None,
    executive: str | None,
    city: str | None,
    bank: str | None,
):
    conditions = []
    if from_date is not None:
        conditions.append(Case.receive_date >= from_date)
    if to_date is not None:
        conditions.append(Case.receive_date <= to_date)
    if executive:
        conditions.append(Case.executive == executive)
    if city:
        conditions.append(Case.city == city)
    if bank:
        conditions.append(Case.bank == bank)
    return conditions


def _rounded(value) -> float | None:
    return round(float(value), 2) if value is not None else None


def _group_performance(db: Session, field, conditions) -> list:
    label = func.coalesce(func.nullif(func.trim(field), ""), "Unassigned").label("name")
    query = select(label, *_metrics()).where(*conditions).group_by(label).order_by(label)
    return db.execute(query).all()


def get_dashboard_performance(
    db: Session,
    from_date: date | None = None,
    to_date: date | None = None,
    executive: str | None = None,
    city: str | None = None,
    bank: str | None = None,
) -> DashboardPerformanceResponse:
    conditions = _filters(from_date, to_date, executive, city, bank)
    summary_row = db.execute(select(*_metrics()).where(*conditions)).one()
    executive_rows = _group_performance(db, Case.executive, conditions)
    city_rows = _group_performance(db, Case.city, conditions)
    bank_rows = _group_performance(db, Case.bank, conditions)

    return DashboardPerformanceResponse(
        summary=PerformanceSummaryResponse(
            total_cases=summary_row.total_cases or 0,
            pending_cases=summary_row.pending or 0,
            positive_cases=summary_row.positive or 0,
            negative_cases=summary_row.negative or 0,
            closed_cases=summary_row.closed or 0,
            average_tat=_rounded(summary_row.average_tat),
        ),
        executives=[
            ExecutivePerformanceResponse(
                executive_name=row.name,
                total_cases=row.total_cases or 0,
                pending=row.pending or 0,
                positive=row.positive or 0,
                negative=row.negative or 0,
                closed=row.closed or 0,
                average_tat=_rounded(row.average_tat),
                fastest_tat=row.fastest_tat,
                slowest_tat=row.slowest_tat,
            )
            for row in executive_rows
        ],
        cities=[
            CityPerformanceResponse(
                city=row.name,
                total_cases=row.total_cases or 0,
                pending=row.pending or 0,
                positive=row.positive or 0,
                negative=row.negative or 0,
                average_tat=_rounded(row.average_tat),
            )
            for row in city_rows
        ],
        banks=[
            BankPerformanceResponse(
                bank=row.name,
                total_cases=row.total_cases or 0,
                pending=row.pending or 0,
                positive=row.positive or 0,
                negative=row.negative or 0,
                average_tat=_rounded(row.average_tat),
            )
            for row in bank_rows
        ],
    )
