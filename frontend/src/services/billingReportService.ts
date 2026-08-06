import API from "../api/caseApi";
import type { CompanyBillingReport, ExecutivePerformanceReport } from "../types/billingReport";
export const getCompanyBillingReport = async (params:Record<string,string|number>) => (await API.get<CompanyBillingReport>("/billing/reports/company",{params})).data;
export const getExecutivePerformanceReport = async (params:Record<string,string|number>) => (await API.get<ExecutivePerformanceReport>("/billing/reports/executive",{params})).data;
