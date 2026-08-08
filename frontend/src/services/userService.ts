import axios from 'axios';
import API from "../api/caseApi";
import type { AssignedCompaniesResponse, AuthUser, Permission, UserPayload } from "../types/auth";

export async function listUsers(filters: {search?: string; role?: string; is_active?: boolean} = {}): Promise<AuthUser[]> {
  const response = await API.get<AuthUser[]>("/users", { params: filters });
  return Array.isArray(response.data) ? response.data : [];
}

export async function createUser(payload: UserPayload): Promise<AuthUser> {
  const response = await API.post<AuthUser>("/users", payload);
  return response.data;
}

export async function updateUser(id: number, payload: Partial<UserPayload>): Promise<AuthUser> {
  const response = await API.put<AuthUser>(`/users/${id}`, payload);
  return response.data;
}

export async function resetUserPassword(id: number, password: string): Promise<void> {
  await API.post(`/users/${id}/reset-password`, { password });
}
export async function forceLogoutUser(id:number):Promise<void>{await API.post(`/users/${id}/force-logout`)}

export async function listPermissions(): Promise<Permission[]> { const response=await API.get<Permission[]>("/permissions"); return response.data; }
export async function getUserPermissions(id:number):Promise<string[]>{const response=await API.get<{permission_codes:string[]}>(`/users/${id}/permissions`);return response.data.permission_codes}
export async function updateUserPermissions(id:number,permission_codes:string[]):Promise<string[]>{const response=await API.put<{permission_codes:string[]}>(`/users/${id}/permissions`,{permission_codes});return response.data.permission_codes}
export async function getUserCompanies(id:number):Promise<AssignedCompaniesResponse>{const response=await API.get<AssignedCompaniesResponse>(`/users/${id}/companies`);return response.data}
export async function updateUserCompanies(id:number,company_ids:number[]):Promise<AssignedCompaniesResponse>{const response=await API.put<AssignedCompaniesResponse>(`/users/${id}/companies`,{company_ids});return response.data}
export async function getMyAssignedCompanies():Promise<AssignedCompaniesResponse>{const response=await API.get<AssignedCompaniesResponse>("/me/assigned-companies");return response.data}

export function userApiErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) return error instanceof Error ? error.message : 'Something went wrong';
  const detail: unknown = error.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return error.message;
  const labels: Record<string,string> = {full_name:'Full name',username:'Username',email:'Email',mobile:'Mobile',password:'Password',role:'Role',executive_id:'Executive linkage',company_ids:'Company assignments',permission_codes:'Permissions'};
  return detail.map((item: {loc?:unknown;msg?:unknown}) => {
    const loc = Array.isArray(item.loc) ? item.loc : [];
    const field = [...loc].reverse().find(value => typeof value === 'string' && value !== 'body');
    const label = typeof field === 'string' ? (labels[field] ?? field.replaceAll('_',' ')) : 'Request';
    const message = typeof item.msg === 'string' ? item.msg.replace(/^Value error,\s*/i, '') : 'Invalid value';
    return `${label} — ${message}`;
  }).join('\n');
}
