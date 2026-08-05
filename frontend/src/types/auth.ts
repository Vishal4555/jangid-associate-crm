export type AuthRole = "Admin" | "Manager" | "Executive";

export interface AuthUser {
  id: number;
  full_name: string;
  username: string;
  email: string;
  mobile: string | null;
  role: AuthRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  executive_id: number | null;
  executive_name: string | null;
  permissions: string[];
}

export interface Permission { id:number; code:string; name:string; description:string; module:string; is_active:boolean }

export interface LoginCredentials {
  usernameOrEmail: string;
  password: string;
  rememberMe: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export type UserPayload = {
  full_name: string;
  username: string;
  email: string;
  mobile?: string;
  password?: string;
  role: AuthRole;
  is_active?: boolean;
  executive_id?: number | null;
};

export type ProfilePayload = Pick<UserPayload, "full_name" | "email">;
