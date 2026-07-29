import axios from "axios";

import {
  clearStoredToken,
  getStoredToken,
  notifyAuthSessionCleared,
} from "../services/authStorage";

function resolveApiBaseUrl(): string {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

  if (!configuredBaseUrl) {
    // Single-server deployment: call API on the same origin.
    return "";
  }

  return configuredBaseUrl;
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
      clearStoredToken();
      notifyAuthSessionCleared("unauthorized");
    }

    return Promise.reject(error);
  },
);

export default API;