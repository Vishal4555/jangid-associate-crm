import type {ImportIssue,ImportOptions,ImportPreview,ImportRow,ImportState,ImportSummary} from "./caseImportService";

const states=new Set<ImportState>(["VALID","WARNING","ERROR","IMPORTED"]);
const emptySummary:ImportSummary={total_rows:0,valid_rows:0,warning_rows:0,error_rows:0,imported_rows:0,new_applications:0,new_visits_existing_application:0};
const emptyOptions:ImportOptions={companies:[],banks_by_company:{},executives:[],districts:[],loan_types:[],visit_types:[],statuses:[]};
const record=(value:unknown):Record<string,unknown>=>value!==null&&typeof value==="object"&&!Array.isArray(value)?value as Record<string,unknown>:{};
const list=(value:unknown):unknown[]=>Array.isArray(value)?value:[];
const text=(value:unknown):string=>value===null||value===undefined?"":typeof value==="string"?value:typeof value==="number"||typeof value==="boolean"?String(value):JSON.stringify(value);
const integer=(value:unknown):number=>Number.isFinite(Number(value))?Number(value):0;
const masters=(value:unknown)=>list(value).map(item=>record(item)).filter(item=>integer(item.id)>0&&text(item.name)).map(item=>({id:integer(item.id),name:text(item.name)}));

export function normalizeIssue(value:unknown):ImportIssue{
 if(typeof value==="string")return{field:"row",entered_value:null,message:value};
 const item=record(value);return{field:text(item.field)||"row",entered_value:item.entered_value==null?null:text(item.entered_value),message:text(item.message)||"Validation issue",suggested_value:item.suggested_value==null?null:text(item.suggested_value),suggested_id:item.suggested_id==null?null:integer(item.suggested_id),confidence:item.confidence==null?null:text(item.confidence)};
}

export function normalizePreview(value:unknown):ImportPreview{
 const source=record(value),summary=record(source.summary),rawOptions=record(source.options),rawBanks=record(rawOptions.banks_by_company);
 const options:ImportOptions={...emptyOptions,companies:masters(rawOptions.companies),executives:masters(rawOptions.executives),districts:masters(rawOptions.districts),loan_types:masters(rawOptions.loan_types),visit_types:list(rawOptions.visit_types).map(text).filter(Boolean),statuses:list(rawOptions.statuses).map(text).filter(Boolean),banks_by_company:Object.fromEntries(Object.entries(rawBanks).map(([key,items])=>[key,masters(items)]))};
 const rows:ImportRow[]=list(source.rows).map((raw,index)=>{const row=record(raw),rawData=record(row.data),state=text(row.state) as ImportState;return{row_number:integer(row.row_number)||index+2,data:Object.fromEntries(Object.entries(rawData).map(([key,item])=>[key,text(item)])),state:states.has(state)?state:"ERROR",intended_action:text(row.intended_action)||"VALIDATION_REQUIRED",errors:list(row.errors).map(normalizeIssue),warnings:list(row.warnings).map(normalizeIssue)}});
 return{import_token:text(source.import_token),filename:text(source.filename),uploaded_at:text(source.uploaded_at),expires_at:text(source.expires_at),summary:{...emptySummary,total_rows:integer(summary.total_rows),valid_rows:integer(summary.valid_rows),warning_rows:integer(summary.warning_rows),error_rows:integer(summary.error_rows),imported_rows:integer(summary.imported_rows),new_applications:integer(summary.new_applications),new_visits_existing_application:integer(summary.new_visits_existing_application)},rows,options};
}

export function apiErrorMessage(error:unknown,fallback:string){
 const source=record(error),response=record(source.response),data=record(response.data),detail=data.detail;
 if(typeof detail==="string"&&detail.trim())return detail;
 if(Array.isArray(detail))return detail.map(item=>text(record(item).msg)||text(item)).filter(Boolean).join("; ")||fallback;
 if(detail&&typeof detail==="object")return text(detail)||fallback;
 return text(source.message)||fallback;
}
