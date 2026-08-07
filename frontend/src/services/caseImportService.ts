import API from "../api/caseApi";
export interface ImportError {row:number;field:string;value:string|null;message:string}
export interface ImportResult {success:boolean;created_applications:number;created_visits:number;updated_existing_applications:number;errors:ImportError[]}
export async function downloadCaseTemplate(){const response=await API.get("/cases/import/template",{responseType:"blob"});const url=URL.createObjectURL(response.data);const a=document.createElement("a");a.href=url;a.download="case_import_template.xlsx";a.click();URL.revokeObjectURL(url)}
export async function importCases(file:File){const data=new FormData();data.append("file",file);return (await API.post<ImportResult>("/cases/import",data)).data}
