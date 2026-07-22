import { apiClient } from "./client";
import type { FacultyOut } from "../types";

export async function listFaculties(): Promise<FacultyOut[]> {
  const { data } = await apiClient.get<FacultyOut[]>("/faculties");
  return data;
}

export async function createFaculty(name: string): Promise<FacultyOut> {
  const { data } = await apiClient.post<FacultyOut>("/faculties", { name });
  return data;
}

export async function updateFaculty(id: number, name: string): Promise<FacultyOut> {
  const { data } = await apiClient.patch<FacultyOut>(`/faculties/${id}`, { name });
  return data;
}

export async function assignTechnician(
  facultyId: number,
  userId: number,
  role: "technician_main" | "technician_backup",
): Promise<void> {
  await apiClient.post(`/faculties/${facultyId}/technicians`, { user_id: userId, role });
}
