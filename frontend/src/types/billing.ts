export type PaymentStatus = "Pending" | "Partially Paid" | "Paid" | "Cancelled";

export interface BillingRecord {
  id: number;
  case_id: number;
  case_no: string;
  applicant: string | null;
  bank: string | null;
  city: string | null;
  executive: string | null;
  bank_payout_amount: string;
  bank_paid_amount: string;
  bank_payment_status: PaymentStatus;
  bank_paid_date: string | null;
  bank_payment_reference: string | null;
  executive_payout_amount: string;
  executive_paid_amount: string;
  executive_payment_status: PaymentStatus;
  executive_paid_date: string | null;
  executive_payment_reference: string | null;
  gross_margin: string;
  bank_balance: string;
  executive_balance: string;
  expected_gross_margin: string;
  realized_cash_margin: string;
  remarks: string | null;
  created_at: string;
  updated_at: string;
}

export interface BillingPayload {
  case_id: number;
  bank_payout_amount: string;
  bank_paid_amount: string;
  bank_payment_status: PaymentStatus;
  bank_paid_date: string | null;
  bank_payment_reference: string | null;
  executive_payout_amount: string;
  executive_paid_amount: string;
  executive_payment_status: PaymentStatus;
  executive_paid_date: string | null;
  executive_payment_reference: string | null;
  remarks: string | null;
}

export interface BillingFilters {
  case_no?: string;
  bank?: string;
  executive?: string;
  city?: string;
  bank_payment_status?: PaymentStatus;
  executive_payment_status?: PaymentStatus;
  from_date?: string;
  to_date?: string;
}

export interface BulkPreviewFilters {
  case_ids?: number[]; receive_date_from?: string; receive_date_to?: string; bank?: string;
  city?: string; executive?: string; status?: string; only_without_billing?: boolean;
}
export type RateStatus = "MATCHED" | "MISSING" | "AMBIGUOUS";
export interface BulkPreviewRow {
  case_id: number; case_no: string; applicant: string | null; bank: string | null; city: string | null;
  location: string | null; executive: string | null; loan_type: string | null; product_type: string | null;
  bank_rate_status: RateStatus; bank_rate_id: number | null; bank_payout_amount: string | null;
  executive_rate_status: RateStatus; executive_rate_id: number | null; executive_payout_amount: string | null;
  expected_gross_margin: string | null; existing_billing: boolean; validation_errors: string[]; ready: boolean;
}
export interface BulkPreviewResponse {
  rows: BulkPreviewRow[];
  summary: { selected_cases: number; ready_cases: number; missing_bank_rates: number; missing_executive_rates: number; ambiguous_rates: number; existing_billing_records: number };
}
export interface BulkCreateResponse {
  created_count: number; skipped_count: number; error_count: number;
  results: { case_id: number; case_no: string | null; status: "CREATED" | "SKIPPED" | "ERROR"; billing_id: number | null; errors: string[] }[];
}
