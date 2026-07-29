from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from app.models.case import Case
from app.schemas.dashboard import DashboardSummaryResponse


def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
    today = date.today()
    month_start = today.replace(day=1)

    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    pending_condition = or_(
        Case.status == "Pending",
        Case.status.is_(None),
        func.trim(func.coalesce(Case.status, "")) == "",
    )

    summary_query = select(
        func.count(Case.id).label("total_cases"),
        func.sum(case((pending_condition, 1), else_=0)).label("pending_cases"),
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
