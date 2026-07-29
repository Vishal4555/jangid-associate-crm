export type AuthRole = "Admin" | "Manager" | "Executive";

export interface AuthUser {
  id: number;
  full_name: string;
  username: string;
  email: string;
  role: AuthRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  usernameOrEmail: string;
  password: string;
  rememberMe: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}