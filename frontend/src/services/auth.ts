import axios from "axios";
import { apiClient, tokenStorage } from "../api/client";
import type { User } from "../types/models";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export const authService = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const { data } = await axios.post<LoginResponse>(`${BASE_URL}/auth/token/`, { username, password });
    tokenStorage.set(data.access, data.refresh);
    return data;
  },
  logout: () => {
    tokenStorage.clear();
  },
  me: async (): Promise<User> => {
    const { data } = await apiClient.get<User>("/auth/me/");
    return data;
  },
};
