import { apiClient } from "./client";
import type { ProjectOut } from "../types";

export interface ProjectPayload {
  name: string;
  description?: string | null;
  status?: string;
  responsible_person?: string | null;
}

export async function listProjects(): Promise<ProjectOut[]> {
  const { data } = await apiClient.get<ProjectOut[]>("/projects");
  return data;
}

export async function createProject(payload: ProjectPayload): Promise<ProjectOut> {
  const { data } = await apiClient.post<ProjectOut>("/projects", payload);
  return data;
}

export async function updateProject(id: number, payload: Partial<ProjectPayload>): Promise<ProjectOut> {
  const { data } = await apiClient.patch<ProjectOut>(`/projects/${id}`, payload);
  return data;
}

export async function deleteProject(id: number): Promise<void> {
  await apiClient.delete(`/projects/${id}`);
}
