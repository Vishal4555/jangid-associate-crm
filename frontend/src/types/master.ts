export type MasterKey =
  | "banks"
  | "branches"
  | "executives"
  | "loan-types"
  | "product-types"
  | "companies"
  | "company-banks"
  | "districts";

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

export interface Company { id:number; name:string; code:string|null; source_type:"WhatsApp"|"Email"|"Both"|"Other"; contact_person:string|null; email:string|null; mobile:string|null; is_active:boolean; remarks:string|null; created_at:string; updated_at:string }
export interface CompanyBank { id:number; company_id:number; company_name:string; bank_id:number; bank_name:string; is_active:boolean; remarks:string|null; created_at:string; updated_at:string }
export interface District { id:number; name:string; state:string; is_active:boolean }

export type MasterRecord = Bank | Branch | Executive | LoanType | ProductType | Company | CompanyBank | District;

export type MasterRecordMap = {
  banks: Bank;
  branches: Branch;
  executives: Executive;
  "loan-types": LoanType;
  "product-types": ProductType;
  companies: Company;
  "company-banks": CompanyBank;
  districts: District;
};

export type MasterPageResponseMap = {
  banks: PageResponse<Bank>;
  branches: PageResponse<Branch>;
  executives: PageResponse<Executive>;
  "loan-types": PageResponse<LoanType>;
  "product-types": PageResponse<ProductType>;
  companies: PageResponse<Company>;
  "company-banks": PageResponse<CompanyBank>;
  districts: PageResponse<District>;
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
  companies: { name:string; code?:string; source_type:"WhatsApp"|"Email"|"Both"|"Other"; contact_person?:string; email?:string; mobile?:string; is_active:boolean; remarks?:string };
  "company-banks": { company_id:number; bank_id:number; is_active:boolean; remarks?:string };
  districts: { name:string; state:string; is_active:boolean };
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
  companies: { name:string; code:string; source_type:"WhatsApp"|"Email"|"Both"|"Other"; contact_person:string; email:string; mobile:string; is_active:boolean; remarks:string };
  "company-banks": { company_id:string; bank_id:string; is_active:boolean; remarks:string };
  districts: { name:string; state:string; is_active:boolean };
};

export interface MasterListParams {
  search?: string;
  page?: number;
  pageSize?: number;
  all?: boolean;
  bankId?: number;
  companyId?: number;
  statusFilter?: "Active" | "Inactive";
  activeOnly?: boolean;
}
