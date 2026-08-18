import { apiClient, downloadBlob } from "./client";
import type { FacultyImportResult, FacultyOut, OrgUnitType } from "../types";

export async function listFaculties(
  unitType?: OrgUnitType,
  opts?: { parentId?: number; topLevel?: boolean },
): Promise<FacultyOut[]> {
  const { data } = await apiClient.get<FacultyOut[]>("/faculties", {
    params: { unit_type: unitType, parent_id: opts?.parentId, top_level: opts?.topLevel },
  });
  return data;
}

export async function createFaculty(
  name: string,
  unitType: OrgUnitType = "faculty",
  parentId?: number | null,
): Promise<FacultyOut> {
  const { data } = await apiClient.post<FacultyOut>("/faculties", {
    name,
    unit_type: unitType,
    parent_id: parentId ?? null,
  });
  return data;
}

export async function updateFaculty(id: number, name: string): Promise<FacultyOut> {
  const { data } = await apiClient.patch<FacultyOut>(`/faculties/${id}`, { name });
  return data;
}

export async function deleteFaculty(id: number): Promise<void> {
  await apiClient.delete(`/faculties/${id}`);
}

export async function exportFaculties(unitType: OrgUnitType): Promise<void> {
  const filename = unitType === "department" ? "bolimlar.xlsx" : "fakultetlar.xlsx";
  await downloadBlob("/faculties/export", { unit_type: unitType }, filename);
}

export async function importFaculties(unitType: OrgUnitType, file: File): Promise<FacultyImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<FacultyImportResult>("/faculties/import", formData, {
    params: { unit_type: unitType },
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
