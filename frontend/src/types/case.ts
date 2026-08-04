export type CaseStatus = "Pending" | "Positive" | "Negative";

export interface Case {
  id: number;

  case_no: string;
  los_no: string;
  receive_date: string;
  closed_date: string;

  bank: string;
  company_id: number | null;
  company: string;
  district_id: number | null;
  district: string;
  branch: string;
  loan_type: string;

  applicant: string;

  product_type: string;

  address: string;
  city: string;

  mobile: string;

  executive: string;

  status: CaseStatus;

  negative_reason: string;

  landmark: string;

  remarks: string;

  next_follow_up_at: string;

  follow_up_note: string;
}

export type CaseStatusFilter = "All" | CaseStatus;

export interface CaseFormPayload {
  case_no: string;
  los_no?: string | null;
  receive_date?: string;
  bank?: string;
  company_id?: number | null;
  company?: string;
  district_id?: number | null;
  district?: string;
  branch?: string;
  loan_type?: string;
  applicant?: string;
  product_type?: string;
  address?: string;
  city?: string;
  mobile?: string;
  executive?: string;
  status?: CaseStatus;
  negative_reason?: string;
  landmark?: string;
  remarks?: string;
  next_follow_up_at?: string | null;
  follow_up_note?: string | null;
}

export interface DeleteCaseResponse {
  message: string;
}

export interface CaseActivity {
  id: number;
  case_id: number;
  activity_type: string;
  field_name: string | null;
  old_value: string | null;
  new_value: string | null;
  performed_by_user_id: number | null;
  performed_by_name: string | null;
  performed_at: string;
  remarks: string | null;
}
