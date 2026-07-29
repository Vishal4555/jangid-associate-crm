import API from "../api/caseApi";
import type { DashboardSummary } from "../types/dashboard";

const EMPTY_SUMMARY: DashboardSummary = {
  total_cases: 0,
  pending_cases: 0,
  positive_cases: 0,
  negative_cases: 0,
  today_cases: 0,
  this_month_cases: 0,
};

function toErrorMessage(error: unknown): Error {
  const message =
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    typeof error.response === "object" &&
    error.response !== null &&
    "data" in error.response &&
    typeof error.response.data === "object" &&
    error.response.data !== null &&
    "detail" in error.response.data &&
    typeof error.response.data.detail === "string"
      ? error.response.data.detail
      : "Unable to load dashboard summary.";

  return new Error(message);
}

export const getEmptyDashboardSummary = (): DashboardSummary => ({ ...EMPTY_SUMMARY });

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  try {
    const response = await API.get<DashboardSummary>("/dashboard/summary");

    return {
      total_cases: response.data.total_cases ?? 0,
      pending_cases: response.data.pending_cases ?? 0,
      positive_cases: response.data.positive_cases ?? 0,
      negative_cases: response.data.negative_cases ?? 0,
      today_cases: response.data.today_cases ?? 0,
      this_month_cases: response.data.this_month_cases ?? 0,
    };
  } catch (error) {
    throw toErrorMessage(error);
  }
};
