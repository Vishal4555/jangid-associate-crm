from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_cases: int = 0
    pending_cases: int = 0
    positive_cases: int = 0
    negative_cases: int = 0
    today_cases: int = 0
    this_month_cases: int = 0
