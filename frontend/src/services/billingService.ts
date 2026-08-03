import API from "../api/caseApi";
import type { BillingFilters, BillingPayload, BillingRecord, BulkCreateResponse, BulkPreviewFilters, BulkPreviewResponse } from "../types/billing";


function errorMessage(error: unknown): Error {
  const message = typeof error === "object" && error !== null && "response" in error && typeof error.response === "object" && error.response !== null && "data" in error.response && typeof error.response.data === "object" && error.response.data !== null && "detail" in error.response.data && typeof error.response.data.detail === "string" ? error.response.data.detail : "Unable to process billing request.";
  return new Error(message);
}

export async function previewBulkBilling(filters: BulkPreviewFilters): Promise<BulkPreviewResponse> {
  try { return (await API.post<BulkPreviewResponse>("/billing/bulk-preview", filters)).data; }
  catch (error) { throw errorMessage(error); }
}

export async function createBulkBilling(caseIds: number[]): Promise<BulkCreateResponse> {
  try { return (await API.post<BulkCreateResponse>("/billing/bulk-create", { case_ids: caseIds })).data; }
  catch (error) { throw errorMessage(error); }
}

export async function getBilling(filters: BillingFilters = {}): Promise<BillingRecord[]> {
  try {
    const response = await API.get<BillingRecord[]>("/billing", { params: filters });
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    throw errorMessage(error);
  }
}

export async function createBilling(payload: BillingPayload): Promise<BillingRecord> {
  try {
    return (await API.post<BillingRecord>("/billing", payload)).data;
  } catch (error) {
    throw errorMessage(error);
  }
}

export async function updateBilling(id: number, payload: BillingPayload): Promise<BillingRecord> {
  try {
    return (await API.put<BillingRecord>(`/billing/${id}`, payload)).data;
  } catch (error) {
    throw errorMessage(error);
  }
}
