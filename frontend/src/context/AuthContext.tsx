import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  AUTH_SESSION_CLEARED_EVENT,
  clearRememberedUsername,
  clearStoredToken,
  getStoredToken,
  notifyAuthSessionCleared,
  setRememberedUsername,
  setStoredToken,
} from "../services/authStorage";
import { fetchCurrentUser, loginWithPassword, logoutCurrentSession } from "../services/authService";
import type { AuthUser, LoginCredentials } from "../types/auth";

type AuthContextValue = {
  currentUser: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<AuthUser>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(
    (reason: "logout" | "unauthorized" | "bootstrap") => {
      clearStoredToken();
      setCurrentUser(null);
      setIsLoading(false);
      notifyAuthSessionCleared(reason);
    },
    [],
  );

  useEffect(() => {
    const handleSessionCleared = () => {
      setCurrentUser(null);
      setIsLoading(false);
    };

    window.addEventListener(AUTH_SESSION_CLEARED_EVENT, handleSessionCleared);

    return () => {
      window.removeEventListener(AUTH_SESSION_CLEARED_EVENT, handleSessionCleared);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function restoreSession() {
      const token = getStoredToken();

      if (!token) {
        if (!cancelled) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const user = await fetchCurrentUser();

        if (!cancelled) {
          setCurrentUser(user);
        }
      } catch {
        if (!cancelled) {
          clearSession("bootstrap");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void restoreSession();

    return () => {
      cancelled = true;
    };
  }, [clearSession]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const response = await loginWithPassword(credentials);

      setStoredToken(response.access_token);

      if (credentials.rememberMe) {
        setRememberedUsername(credentials.usernameOrEmail);
      } else {
        clearRememberedUsername();
      }

      const user = await fetchCurrentUser();
      setCurrentUser(user);
      setIsLoading(false);

      return user;
    },
    [],
  );

  const logout = useCallback(async () => {
    try { await logoutCurrentSession(); } catch { /* local logout must still complete */ }
    clearSession("logout");
  }, [clearSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      currentUser,
      isAuthenticated: currentUser !== null,
      isLoading,
      login,
      logout,
    }),
    [currentUser, isLoading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
