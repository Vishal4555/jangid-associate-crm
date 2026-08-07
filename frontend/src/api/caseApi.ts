import axios from "axios";

import {
  clearStoredToken,
  getStoredToken,
  notifyAuthSessionCleared,
} from "../services/authStorage";

function resolveApiBaseUrl(): string {
  // Production requests must stay in the nginx-proxied API namespace.  Do not
  // consult the legacy VITE_API_BASE_URL variable: a stale value of "/" sends
  // requests to the SPA location, which returns index.html instead of JSON.
  const configuredBaseUrl = import.meta.env.VITE_API_URL?.trim() || "/api";
  return configuredBaseUrl.replace(/\/$/, "") || "/api";
}

const API = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: {
    "Content-Type": "application/json",
  },
});

API.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const revoked = error.response?.data?.detail === "SESSION_REVOKED";
      if (revoked) window.sessionStorage.setItem("session-ended-message", "This account was signed in from another browser.\nYour session has ended.");
      clearStoredToken();
      notifyAuthSessionCleared(revoked ? "session_revoked" : "unauthorized");
      if (revoked && window.location.pathname !== "/login") window.location.assign("/login");
    }

    return Promise.reject(error);
  },
);

export default API;
