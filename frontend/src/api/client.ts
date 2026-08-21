import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

const ACCESS_TOKEN_KEY = "fawnic_access_token";
const REFRESH_TOKEN_KEY = "fawnic_refresh_token";

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  },
  setAccess: (access: string) => localStorage.setItem(ACCESS_TOKEN_KEY, access),
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};

export const apiClient = axios.create({ baseURL: BASE_URL });

apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = tokenStorage.getRefresh();
  if (!refresh) throw new Error("No refresh token available");

  const response = await axios.post(`${BASE_URL}/auth/token/refresh/`, { refresh });
  const access = response.data.access as string;
  tokenStorage.setAccess(access);
  return access;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        refreshPromise ??= refreshAccessToken();
        const access = await refreshPromise;
        refreshPromise = null;
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        refreshPromise = null;
        tokenStorage.clear();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

export function extractErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { error?: string; detail?: unknown } | undefined;
    if (data?.error && typeof data.error === "string") return data.error;
    if (typeof data?.detail === "string") return data.detail;
  }
  return fallback;
}

/** Maps DRF's {field: [messages]} validation error shape to a flat field->message record for inline form errors. */
export function extractFieldErrors(error: unknown): Record<string, string> {
  if (!axios.isAxiosError(error)) return {};
  const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
  if (!detail || typeof detail !== "object" || Array.isArray(detail)) return {};

  const fieldErrors: Record<string, string> = {};
  for (const [key, value] of Object.entries(detail as Record<string, unknown>)) {
    if (Array.isArray(value) && typeof value[0] === "string") {
      fieldErrors[key] = value[0];
    } else if (typeof value === "string") {
      fieldErrors[key] = value;
    }
  }
  return fieldErrors;
}
