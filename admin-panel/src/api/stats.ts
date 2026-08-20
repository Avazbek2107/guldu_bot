import { apiClient } from "./client";
import type { DashboardStats, MyDashboardStats } from "../types";

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/stats/dashboard");
  return data;
}

export async function fetchMyDashboardStats(): Promise<MyDashboardStats> {
  const { data } = await apiClient.get<MyDashboardStats>("/stats/me");
  return data;
}
