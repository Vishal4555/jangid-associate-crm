export type RateKind = "bank" | "executive";

export interface RateBase {
  id: number; city: string | null; loan_type: string | null; product_type: string | null;
  payout_rate: string; effective_from: string; effective_to: string | null; is_active: boolean;
  remarks: string | null; created_at: string; updated_at: string;
}
export interface BankRate extends RateBase { bank_id: number; bank_name: string; company_id:number|null; company_name:string|null; district_id:number|null; district_name:string|null; state: string | null }
export interface ExecutiveRate extends RateBase { executive_id: number; executive_name: string; bank_id: number | null; bank_name: string | null }
export type PayoutRate = BankRate | ExecutiveRate;
export interface RatePayload {
  bank_id?: number | null; executive_id?: number; state?: string | null; city?: string | null;
  company_id?:number|null; district_id?:number|null;
  loan_type?: string | null; product_type?: string | null; payout_rate: number; effective_from: string;
  effective_to?: string | null; is_active: boolean; remarks?: string | null;
}
export interface BankRateBulkPayload extends Omit<RatePayload,"bank_id"|"executive_id"> { company_id:number; bank_ids:number[]; district_id:number }
export interface BankRateBulkResult { created_count:number; failed_count:number; items:BankRate[]; errors:string[] }
export interface ImportRateRow {
  row_number: number; company?:string; bank?: string; district?:string; executive?: string; state?: string; city?: string; location?: string;
  loan_type?: string; product_type?: string; payout_rate?: number; effective_from?: string;
  effective_to?: string; active: boolean; remarks?: string;
}
export interface ImportResult { valid_count: number; invalid_count: number; imported_count: number; rows: { row_number: number; valid: boolean; errors: string[] }[] }
