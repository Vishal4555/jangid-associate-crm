export interface DashboardSummary {
  total_cases: number;
  pending_cases: number;
  positive_cases: number;
  negative_cases: number;
  today_cases: number;
  this_month_cases: number;
}

export interface PerformanceSummary {
  total_cases: number;
  pending_cases: number;
  positive_cases: number;
  negative_cases: number;
  closed_cases: number;
  average_tat: number | null;
}

export interface ExecutivePerformance {
  executive_name: string;
  total_cases: number;
  pending: number;
  positive: number;
  negative: number;
  closed: number;
  average_tat: number | null;
  fastest_tat: number | null;
  slowest_tat: number | null;
}

export interface CityPerformance {
  city: string;
  total_cases: number;
  pending: number;
  positive: number;
  negative: number;
  average_tat: number | null;
}

export interface BankPerformance {
  bank: string;
  total_cases: number;
  pending: number;
  positive: number;
  negative: number;
  average_tat: number | null;
}

export interface DashboardPerformance {
  summary: PerformanceSummary;
  executives: ExecutivePerformance[];
  cities: CityPerformance[];
  banks: BankPerformance[];
}

export interface PerformanceFilters {
  from_date?: string;
  to_date?: string;
  executive?: string;
  city?: string;
  bank?: string;
}
