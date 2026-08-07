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
