import { apiClient, downloadBlob } from "./client";
import type { InventoryImportResult, InventoryItemOut, RepairHistoryItem } from "../types";

export interface InventoryItemPayload {
  faculty_id: number;
  room?: string | null;
  inventory_number?: string | null;
  uzasbo?: string | null;
  inventory_type?: string | null;
  model?: string | null;
  status?: string;
  internet_connection?: string | null;
  mac_address?: string | null;
  responsible_person?: string | null;
  assigned_technician_id?: number | null;
}

export async function listInventory(facultyId?: number): Promise<InventoryItemOut[]> {
  const { data } = await apiClient.get<InventoryItemOut[]>("/inventory", { params: { faculty_id: facultyId } });
  return data;
}

export async function createInventoryItem(payload: InventoryItemPayload): Promise<InventoryItemOut> {
  const { data } = await apiClient.post<InventoryItemOut>("/inventory", payload);
  return data;
}

export async function updateInventoryItem(
  id: number,
  payload: Partial<InventoryItemPayload>,
): Promise<InventoryItemOut> {
  const { data } = await apiClient.patch<InventoryItemOut>(`/inventory/${id}`, payload);
  return data;
}

export async function deleteInventoryItem(id: number): Promise<void> {
  await apiClient.delete(`/inventory/${id}`);
}

export async function getInventoryHistory(id: number): Promise<RepairHistoryItem[]> {
  const { data } = await apiClient.get<RepairHistoryItem[]>(`/inventory/${id}/history`);
  return data;
}

export async function exportInventory(facultyId?: number): Promise<void> {
  await downloadBlob("/inventory/export", { faculty_id: facultyId }, "inventar.xlsx");
}

export async function importInventory(file: File): Promise<InventoryImportResult> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<InventoryImportResult>("/inventory/import", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
