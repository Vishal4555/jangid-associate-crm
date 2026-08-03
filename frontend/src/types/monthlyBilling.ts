export type MonthlyRateStatus = "MATCHED" | "MISSING" | "AMBIGUOUS";
export type RegisterStatus = "Pending" | "Partially Paid" | "Paid" | "Cancelled";
export interface MonthStatus { month:string; status:"DRAFT"|"FINALIZED"|"REOPENED"; revision_number:number; finalized_at:string|null; reopened_at:string|null; notes:string|null }
export interface ExecutiveMonthlyBilling {
  executive_id: number | null; executive: string; rate: string | null; rate_display: string;
  bank_counts: Record<string, number>; total_points: number; gross_payment: string | null;
  advance: string; net_payment: string | null; paid: string; balance: string | null;
  payment_status: RegisterStatus; rate_status: MonthlyRateStatus; register_id: number | null; is_finalized: boolean;
  payment_date?:string|null; payment_reference?:string|null; remarks?:string|null; snapshot_revision?:number|null;
}
export interface BankMonthlyBilling {
  case_id: number|null; date: string; bank: string | null; los_no: string | null; name: string | null;
  address: string | null; city: string | null; mobile: string | null; status: string;
  remark: string | null; rate: string | null; rate_status: MonthlyRateStatus;
}
export interface MonthlyBillingResponse {
  month: string; executive_billing: ExecutiveMonthlyBilling[]; bank_billing: BankMonthlyBilling[];
  summary: { total_cases: number; billable_cases: number; missing_executive_rates: number;
    missing_bank_rates: number; ambiguous_rates: number; total_executive_payment: string; total_bank_billing: string };
  month_status: MonthStatus;
}
export interface BankPayment { id:number; billing_month:string; bank:string; city:string; billed_amount:string; received_amount:string; balance_amount:string; status:RegisterStatus; payment_date:string|null; payment_reference:string|null; remarks:string|null; is_finalized:boolean }
export interface BillingDashboard { month:string; month_status:MonthStatus; total_bank_billing:string; bank_received:string; bank_outstanding:string; total_executive_payout:string; executive_paid:string; executive_outstanding:string; expected_gross_margin:string; realized_cash_margin:string; bank_summary:BankPayment[]; executive_summary:ExecutiveMonthlyBilling[] }
export interface PaymentRegisterPayload {
  billing_month: string; executive_id: number; advance_amount: number; paid_amount: number;
  payment_date?: string | null; payment_reference?: string | null; remarks?: string | null;
  finalize?: boolean; regenerate?: boolean;
}
