import API from "../api/caseApi";

import type { AuthUser, LoginCredentials, LoginResponse } from "../types/auth";

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