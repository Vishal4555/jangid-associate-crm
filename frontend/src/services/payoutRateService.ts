import API from "../api/caseApi";
import type { ImportRateRow, ImportResult, PayoutRate, RateKind, RatePayload } from "../types/payoutRate";

function message(error: unknown) {
  const e = error as { response?: { data?: { detail?: string } } };
  return new Error(e.response?.data?.detail || "Unable to process payout rates.");
}
export async function listPayoutRates(kind: RateKind, search = "") {
  try { return (await API.get<PayoutRate[]>(`/billing/rates/${kind}`, { params: search ? { search } : {} })).data; }
  catch (error) { throw message(error); }
}
export async function savePayoutRate(kind: RateKind, payload: RatePayload, id?: number) {
  try { return (id ? await API.put<PayoutRate>(`/billing/rates/${kind}/${id}`, payload) : await API.post<PayoutRate>(`/billing/rates/${kind}`, payload)).data; }
  catch (error) { throw message(error); }
}
export async function importPayoutRates(kind: RateKind, rows: ImportRateRow[], confirm: boolean) {
  try { return (await API.post<ImportResult>(`/billing/rates/${kind}/import`, { rows, confirm })).data; }
  catch (error) { throw message(error); }
}
