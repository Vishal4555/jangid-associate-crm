import API from "../api/caseApi";

import type { AuthUser, LoginCredentials, LoginResponse, ProfilePayload } from "../types/auth";

export async function loginWithPassword(
  credentials: Omit<LoginCredentials, "rememberMe">,
): Promise<LoginResponse> {
  const response = await API.post<LoginResponse>("/auth/login", {
    username: credentials.usernameOrEmail,
    password: credentials.password,
  });

  return response.data;
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const response = await API.get<AuthUser>("/auth/me");
  return response.data;
}

export async function updateCurrentUser(payload: ProfilePayload): Promise<AuthUser> {
  const response = await API.put<AuthUser>("/auth/me", payload);
  return response.data;
}
export async function logoutCurrentSession():Promise<void>{await API.post("/auth/logout")}
