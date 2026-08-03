from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_cases: int = 0
    pending_cases: int = 0
    positive_cases: int = 0
    negative_cases: int = 0
    today_cases: int = 0
    this_month_cases: int = 0


class PerformanceSummaryResponse(BaseModel):
    total_cases: int = 0
    pending_cases: int = 0
    positive_cases: int = 0
    negative_cases: int = 0
    closed_cases: int = 0
    average_tat: float | None = None


class ExecutivePerformanceResponse(BaseModel):
    executive_name: str
    total_cases: int = 0
    pending: int = 0
    positive: int = 0
    negative: int = 0
    closed: int = 0
    average_tat: float | None = None
    fastest_tat: int | None = None
    slowest_tat: int | None = None


class CityPerformanceResponse(BaseModel):
    city: str
    total_cases: int = 0
    pending: int = 0
    positive: int = 0
    negative: int = 0
    average_tat: float | None = None


class BankPerformanceResponse(BaseModel):
    bank: str
    total_cases: int = 0
    pending: int = 0
    positive: int = 0
    negative: int = 0
    average_tat: float | None = None


class DashboardPerformanceResponse(BaseModel):
    summary: PerformanceSummaryResponse
    executives: list[ExecutivePerformanceResponse]
    cities: list[CityPerformanceResponse]
    banks: list[BankPerformanceResponse]


class PendingAgeingSummaryResponse(BaseModel):
    total_pending: int = 0
    zero_to_two: int = 0
    three_to_five: int = 0
    six_to_ten: int = 0
    eleven_plus: int = 0


class ExecutivePendingAgeingResponse(PendingAgeingSummaryResponse):
    executive: str


class CityPendingAgeingResponse(PendingAgeingSummaryResponse):
    city: str


class PendingAgeingResponse(BaseModel):
    summary: PendingAgeingSummaryResponse
    executives: list[ExecutivePendingAgeingResponse]
    cities: list[CityPendingAgeingResponse]
