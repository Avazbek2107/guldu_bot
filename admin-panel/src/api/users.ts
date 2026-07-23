import { apiClient } from "./client";
import type { UserOut, UserRole } from "../types";

export interface UserCreatePayload {
  username: string;
  password: string;
  full_name: string;
  phone: string;
  role: UserRole;
  faculty_id: number | null;
  telegram_id?: number | null;
}

export interface UserUpdatePayload {
  full_name?: string;
  phone?: string;
  faculty_id?: number | null;
  password?: string;
  telegram_id?: number | null;
}

export async function listUsers(params?: { role?: UserRole; faculty_id?: number }): Promise<UserOut[]> {
  const { data } = await apiClient.get<UserOut[]>("/users", { params });
  return data;
}

export async function createUser(payload: UserCreatePayload): Promise<UserOut> {
  const { data } = await apiClient.post<UserOut>("/users", payload);
  return data;
}

export async function updateUser(id: number, payload: UserUpdatePayload): Promise<UserOut> {
  const { data } = await apiClient.patch<UserOut>(`/users/${id}`, payload);
  return data;
}

export async function blockUser(id: number): Promise<UserOut> {
  const { data } = await apiClient.post<UserOut>(`/users/${id}/block`);
  return data;
}

export async function unblockUser(id: number): Promise<UserOut> {
  const { data } = await apiClient.post<UserOut>(`/users/${id}/unblock`);
  return data;
}

export async function deleteUser(id: number): Promise<void> {
  await apiClient.delete(`/users/${id}`);
}
