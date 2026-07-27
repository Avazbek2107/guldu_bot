import { apiClient } from "./client";
import type { UserOut } from "../types";

export interface AuthResponse {
  csrf_token: string;
  user: UserOut;
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", { username, password });
  return data;
}

export async function fetchMe(): Promise<AuthResponse> {
  const { data } = await apiClient.get<AuthResponse>("/auth/me");
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export interface ProfileUpdatePayload {
  full_name?: string;
  username?: string;
  current_password?: string;
  new_password?: string;
}

export async function updateProfile(payload: ProfileUpdatePayload): Promise<AuthResponse> {
  const { data } = await apiClient.patch<AuthResponse>("/auth/me", payload);
  return data;
}

export async function uploadAvatar(file: File): Promise<AuthResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<AuthResponse>("/auth/me/avatar", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
