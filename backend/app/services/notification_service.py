from datetime import datetime, time, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.case import Case
from app.schemas.notification import NotificationResponse
from app.services.dashboard_service import PENDING_CONDITION


SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def get_notifications(db: Session, executive_scope: str | None = None) -> list[NotificationResponse]:
    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    tomorrow_start = today_start + timedelta(days=1)
    old_pending_cutoff = now.date() - timedelta(days=6)

    query = (
        select(Case)
        .where(
            or_(
                Case.next_follow_up_at < tomorrow_start,
                and_(
                    PENDING_CONDITION,
                    Case.receive_date.is_not(None),
                    Case.receive_date <= old_pending_cutoff,
                ),
            )
        )
    )
    if executive_scope is not None: query = query.where(Case.executive == executive_scope)
    cases = db.scalars(query).all()
    notifications: list[NotificationResponse] = []

    for case_item in cases:
        if case_item.next_follow_up_at is not None and case_item.next_follow_up_at < now:
            notifications.append(
                NotificationResponse(
                    id=f"overdue-follow-up-{case_item.id}-{case_item.next_follow_up_at.isoformat()}",
                    type="OVERDUE_FOLLOW_UP",
                    title="Overdue Follow-up",
                    message="This case has a follow-up that is past due.",
                    case_id=case_item.id,
                    case_no=case_item.case_no,
                    los_no=case_item.los_no,
                    applicant=case_item.applicant,
                    executive=case_item.executive,
                    due_at=case_item.next_follow_up_at.isoformat(),
                    severity="warning",
                )
            )
        elif case_item.next_follow_up_at is not None and case_item.next_follow_up_at < tomorrow_start:
            notifications.append(
                NotificationResponse(
                    id=f"today-follow-up-{case_item.id}-{case_item.next_follow_up_at.isoformat()}",
                    type="TODAY_FOLLOW_UP",
                    title="Today's Follow-up",
                    message="This case has a follow-up scheduled today.",
                    case_id=case_item.id,
                    case_no=case_item.case_no,
                    los_no=case_item.los_no,
                    applicant=case_item.applicant,
                    executive=case_item.executive,
                    due_at=case_item.next_follow_up_at.isoformat(),
                    severity="info",
                )
            )

        if (
            case_item.receive_date is not None
            and case_item.receive_date <= old_pending_cutoff
            and (case_item.status is None or not case_item.status.strip() or case_item.status == "Pending")
        ):
            age_days = (now.date() - case_item.receive_date).days
            notifications.append(
                NotificationResponse(
                    id=f"old-pending-case-{case_item.id}",
                    type="OLD_PENDING_CASE",
                    title="Old Pending Case",
                    message=f"This pending case has been open for {age_days} days.",
                    case_id=case_item.id,
                    case_no=case_item.case_no,
                    los_no=case_item.los_no,
                    applicant=case_item.applicant,
                    executive=case_item.executive,
                    occurred_at=case_item.receive_date.isoformat(),
                    severity="critical" if age_days >= 11 else "warning",
                )
            )

    notifications.sort(
        key=lambda item: (
            SEVERITY_ORDER[item.severity],
            item.due_at or item.occurred_at or "",
        )
    )
    return notifications[:50]
