import API from "../api/caseApi";
import type { BillingDashboard, MonthStatus, MonthlyBillingResponse, PaymentRegisterPayload } from "../types/monthlyBilling";

function errorMessage(error: unknown) {
  const value = error as { response?: { data?: { detail?: string } } };
  return new Error(value.response?.data?.detail || "Unable to generate monthly billing.");
}
export async function finalizeMonth(month:string, notes?:string) { return (await API.post<MonthStatus>("/billing/month-finalize",{month,notes})).data; }
export async function reopenMonth(month:string, reason:string) { return (await API.post<MonthStatus>("/billing/month-reopen",{month,reason})).data; }
export async function regenerateMonth(month:string) { return (await API.post<MonthStatus>("/billing/month-regenerate",{month,confirm:true})).data; }
export async function getBillingDashboard(month:string) { return (await API.get<BillingDashboard>("/billing/dashboard",{params:{month}})).data; }
export async function getMonthlyBilling(month: string, filters: Record<string, string> = {}) {
  try { return (await API.get<MonthlyBillingResponse>("/billing/monthly", { params: { month, ...filters } })).data; }
  catch (error) { throw errorMessage(error); }
}
export async function savePaymentRegister(payload: PaymentRegisterPayload) {
  try { return (await API.post("/billing/monthly/payment-register", payload)).data; }
  catch (error) { throw errorMessage(error); }
}
