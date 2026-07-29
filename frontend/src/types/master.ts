export type MasterKey =
  | "banks"
  | "branches"
  | "executives"
  | "loan-types"
  | "product-types";

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PageResponse<T> extends PaginationMeta {
  items: T[];
}

export interface Bank {
  id: number;
  name: string;
  code: string | null;
  created_at: string;
  updated_at: string;
}

export interface Branch {
  id: number;
  bank_id: number;
  bank_name: string;
  name: string;
  code: string | null;
  created_at: string;
  updated_at: string;
}

export interface Executive {
  id: number;
  full_name: string;
  email: string | null;
  mobile: string | null;
  status: "Active" | "Inactive";
  created_at: string;
  updated_at: string;
}

export interface LoanType {
  id: number;
  name: string;
  code: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductType {
  id: number;
  name: string;
  code: string | null;
  created_at: string;
  updated_at: string;
}

export type MasterRecord = Bank | Branch | Executive | LoanType | ProductType;

export type MasterRecordMap = {
  banks: Bank;
  branches: Branch;
  executives: Executive;
  "loan-types": LoanType;
  "product-types": ProductType;
};

export type MasterPageResponseMap = {
  banks: PageResponse<Bank>;
  branches: PageResponse<Branch>;
  executives: PageResponse<Executive>;
  "loan-types": PageResponse<LoanType>;
  "product-types": PageResponse<ProductType>;
};

export type MasterPayloadMap = {
  banks: { name: string; code?: string };
  branches: { bank_id: number; name: string; code?: string };
  executives: {
    full_name: string;
    email?: string;
    mobile?: string;
    status: "Active" | "Inactive";
  };
  "loan-types": { name: string; code?: string };
  "product-types": { name: string; code?: string };
};

export type MasterFormValuesMap = {
  banks: { name: string; code: string };
  branches: { bank_id: string; name: string; code: string };
  executives: {
    full_name: string;
    email: string;
    mobile: string;
    status: "Active" | "Inactive";
  };
  "loan-types": { name: string; code: string };
  "product-types": { name: string; code: string };
};

export interface MasterListParams {
  search?: string;
  page?: number;
  pageSize?: number;
  all?: boolean;
  bankId?: number;
  statusFilter?: "Active" | "Inactive";
  activeOnly?: boolean;
}
