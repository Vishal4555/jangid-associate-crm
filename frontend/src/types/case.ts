export type CaseStatus = "Pending" | "Positive" | "Negative";

export interface Case {
  id: number;

  case_no: string;
  receive_date: string;

  bank: string;
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
}

export type CaseStatusFilter = "All" | CaseStatus;

export interface CaseFormPayload {
  case_no: string;
  receive_date?: string;
  bank?: string;
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
}

export interface DeleteCaseResponse {
  message: string;
}