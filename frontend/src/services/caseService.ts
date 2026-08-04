import API from "../api/caseApi";
import { emitCasesChanged } from "./caseChangeEvents";
import type {
  Case,
  CaseActivity,
  CaseFormPayload,
  DeleteCaseResponse,
} from "../types/case";

export type CaseApiResponse = {
  id: number;
  case_no: string;
  los_no: string | null;
  receive_date: string | null;
  closed_date: string | null;
  bank: string | null;
  company_id: number | null;
  company: string | null;
  district_id: number | null;
  district: string | null;
  branch: string | null;
  loan_type: string | null;
  applicant: string | null;
  product_type: string | null;
  address: string | null;
  city: string | null;
  mobile: string | null;
  executive: string | null;
  status: string | null;
  negative_reason: string | null;
  landmark: string | null;
  remarks: string | null;
  next_follow_up_at: string | null;
  follow_up_note: string | null;
};

export function mapCaseResponse(data: CaseApiResponse): Case {
  return {
    id: data.id,
    case_no: data.case_no,
    los_no: data.los_no ?? "",
    receive_date: data.receive_date ?? "",
    closed_date: data.closed_date ?? "",
    bank: data.bank ?? "",
    company_id: data.company_id,
    company: data.company ?? "",
    district_id: data.district_id,
    district: data.district ?? "",
    branch: data.branch ?? "",
    loan_type: data.loan_type ?? "",
    applicant: data.applicant ?? "",
    product_type: data.product_type ?? "",
    address: data.address ?? "",
    city: data.city ?? "",
    mobile: data.mobile ?? "",
    executive: data.executive ?? "",
    status:
      data.status === "Positive" || data.status === "Negative"
        ? data.status
        : "Pending",
    negative_reason: data.negative_reason ?? "",
    landmark: data.landmark ?? "",
    remarks: data.remarks ?? "",
    next_follow_up_at: data.next_follow_up_at ?? "",
    follow_up_note: data.follow_up_note ?? "",
  };
}

function cleanPayload(payload: CaseFormPayload): CaseFormPayload {
  const entries = Object.entries(payload).map(([key, value]) => {
    if (typeof value === "string") {
      const trimmed = value.trim();
      if (key === "next_follow_up_at" || key === "follow_up_note" || key === "los_no") {
        return [key, trimmed === "" ? null : trimmed];
      }
      return [key, trimmed === "" ? undefined : trimmed];
    }
    return [key, value];
  });

  return Object.fromEntries(entries);
}

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
      : "Something went wrong while processing your request.";

  return new Error(message);
}

export const getCases = async (): Promise<Case[]> => {
  try {
    const response = await API.get<CaseApiResponse[]>("/cases");
    return Array.isArray(response.data) ? response.data.map(mapCaseResponse) : [];
  } catch (error) {
    throw toErrorMessage(error);
  }
};

export const getCaseById = async (id: number): Promise<Case> => {
  try {
    const response = await API.get<CaseApiResponse>(`/cases/${id}`);
    return mapCaseResponse(response.data);
  } catch (error) {
    throw toErrorMessage(error);
  }
};

export const getCaseActivity = async (id: number): Promise<CaseActivity[]> => {
  try {
    const response = await API.get<CaseActivity[]>(`/cases/${id}/activity`);
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    throw toErrorMessage(error);
  }
};

export const createCase = async (data: CaseFormPayload): Promise<Case> => {
  try {
    const response = await API.post<CaseApiResponse>("/cases", cleanPayload(data));
    const createdCase = mapCaseResponse(response.data);
    emitCasesChanged();
    return createdCase;
  } catch (error) {
    throw toErrorMessage(error);
  }
};

export const updateCase = async (
  id: number,
  data: CaseFormPayload,
): Promise<Case> => {
  try {
    const response = await API.put<CaseApiResponse>(`/cases/${id}`, cleanPayload(data));
    const updatedCase = mapCaseResponse(response.data);
    emitCasesChanged();
    return updatedCase;
  } catch (error) {
    throw toErrorMessage(error);
  }
};

export const deleteCase = async (id: number): Promise<DeleteCaseResponse> => {
  try {
    const response = await API.delete<DeleteCaseResponse>(`/cases/${id}`);
    emitCasesChanged();
    return response.data;
  } catch (error) {
    throw toErrorMessage(error);
  }
};
