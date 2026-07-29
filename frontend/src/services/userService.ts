import API from "../api/caseApi";
import type { AuthUser, UserPayload } from "../types/auth";

export async function listUsers(search?: string): Promise<AuthUser[]> {
  const response = await API.get<AuthUser[]>("/users", { params: search ? { search } : undefined });
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

export async function deleteUser(id: number): Promise<void> {
  await API.delete(`/users/${id}`);
}
