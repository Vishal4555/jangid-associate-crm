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
