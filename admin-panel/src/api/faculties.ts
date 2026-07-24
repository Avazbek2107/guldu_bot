import { apiClient } from "./client";
import type { FacultyOut, OrgUnitType } from "../types";

export async function listFaculties(unitType?: OrgUnitType): Promise<FacultyOut[]> {
  const { data } = await apiClient.get<FacultyOut[]>("/faculties", { params: { unit_type: unitType } });
  return data;
}

export async function createFaculty(name: string, unitType: OrgUnitType = "faculty"): Promise<FacultyOut> {
  const { data } = await apiClient.post<FacultyOut>("/faculties", { name, unit_type: unitType });
  return data;
}

export async function updateFaculty(id: number, name: string): Promise<FacultyOut> {
  const { data } = await apiClient.patch<FacultyOut>(`/faculties/${id}`, { name });
  return data;
}
