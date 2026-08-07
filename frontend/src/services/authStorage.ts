const AUTH_TOKEN_KEY = "jangid-associate-crm.auth.token";
const REMEMBERED_USERNAME_KEY = "jangid-associate-crm.auth.username";
const AUTH_SESSION_CLEARED_EVENT = "jangid-associate-crm-auth-cleared";

export type AuthClearReason = "logout" | "unauthorized" | "bootstrap" | "session_revoked";

export function getStoredToken(): string | null {
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function getRememberedUsername(): string {
  return window.localStorage.getItem(REMEMBERED_USERNAME_KEY) ?? "";
}

export function setRememberedUsername(username: string): void {
  window.localStorage.setItem(REMEMBERED_USERNAME_KEY, username);
}

export function clearRememberedUsername(): void {
  window.localStorage.removeItem(REMEMBERED_USERNAME_KEY);
}

export function notifyAuthSessionCleared(reason: AuthClearReason): void {
  window.dispatchEvent(
    new CustomEvent(AUTH_SESSION_CLEARED_EVENT, {
      detail: { reason },
    }),
  );
}

export { AUTH_SESSION_CLEARED_EVENT };
