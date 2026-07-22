import { apiClient } from "./client";
import type { UserOut } from "../types";

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserOut;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>("/auth/login", { username, password });
  return data;
}

export async function fetchMe(): Promise<UserOut> {
  const { data } = await apiClient.get<UserOut>("/auth/me");
  return data;
}
