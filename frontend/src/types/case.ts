export type CaseStatus = "Pending" | "Positive" | "Negative";
export type VisitType = "Residence" | "Office" | "Permanent" | "Business" | "Other";

export interface CaseVisit {
  id: number; case_id: number; visit_type: VisitType; address: string | null;
  district_id: number | null; district: string | null; city: string | null;
  landmark: string | null; executive: string | null; status: CaseStatus;
  negative_reason: string | null; receive_date: string | null; closed_date: string | null;
  remarks: string | null; next_follow_up_at: string | null; follow_up_note: string | null;
  tat_days: number | null; created_at: string; updated_at: string;
}

export type CaseVisitPayload = Omit<CaseVisit, "id" | "case_id" | "closed_date" | "tat_days" | "created_at" | "updated_at">;

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
  visit_type?: VisitType;
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
