import API from "../api/caseApi";
import {apiErrorMessage,normalizePreview} from "./caseImportNormalization";

export type ImportState="VALID"|"WARNING"|"ERROR"|"IMPORTED";
export interface ImportIssue{field:string;entered_value:string|null;message:string;suggested_value?:string|null;suggested_id?:number|null;confidence?:string|null}
export interface ImportRow{row_number:number;data:Record<string,string>;state:ImportState;intended_action:string;errors:ImportIssue[];warnings:ImportIssue[]}
export interface ImportSummary{total_rows:number;valid_rows:number;warning_rows:number;error_rows:number;imported_rows:number;new_applications:number;new_visits_existing_application:number}
export interface MasterOption{id:number;name:string}
export interface ImportOptions{companies:MasterOption[];banks_by_company:Record<string,MasterOption[]>;executives:MasterOption[];districts:MasterOption[];loan_types:MasterOption[];visit_types:string[];statuses:string[]}
export interface ImportPreview{import_token:string;filename:string;uploaded_at:string;expires_at:string;summary:ImportSummary;rows:ImportRow[];options:ImportOptions}
export interface CommitResult{success:boolean;imported_rows:number;created_applications:number;created_visits:number;added_to_existing_applications:number;failed_rows:{row_number:number;errors:ImportIssue[]}[];remaining_rows:number}
export interface ImportError{row:number;field:string;value:string|null;message:string}
export interface ImportResult{success:boolean;created_applications:number;created_visits:number;updated_existing_applications:number;errors:ImportError[]}

export async function downloadCaseTemplate(){const response=await API.get("/cases/import/template",{responseType:"blob"});const url=URL.createObjectURL(response.data);const a=document.createElement("a");a.href=url;a.download="case_import_template.xlsx";a.click();URL.revokeObjectURL(url)}
export async function previewCases(file:File){const data=new FormData();data.append("file",file);try{return normalizePreview((await API.post("/cases/import/preview",data)).data)}catch(error){throw new Error(`Import preview failed: ${apiErrorMessage(error,"Unable to validate this Excel file.")}`)}}
export async function resumeCaseImport(){try{return normalizePreview((await API.get("/cases/import/resume")).data)}catch(error){const status=(error as {response?:{status?:number}})?.response?.status;if(status===404)return null;throw new Error(`Import preview failed: ${apiErrorMessage(error,"Unable to resume the last import.")}`)}}
export async function commitCaseImport(importToken:string,rows:ImportRow[]){try{const data=(await API.post<CommitResult>("/cases/import/commit",{import_token:importToken,rows:rows.map(row=>({row_number:row.row_number,resolved_data:row.data}))})).data;if(!data||typeof data.imported_rows!=="number"||!Array.isArray(data.failed_rows))throw new Error("Malformed commit response");return data}catch(error){throw new Error(`Import failed: ${apiErrorMessage(error,"The selected rows could not be imported.")}`)}}
