import { apiClient, downloadBlob } from "./client";
import type { TicketCategory, TicketOut, TicketPriority, TicketStatus } from "../types";

export interface TicketFilters {
  faculty_id?: number;
  status?: TicketStatus;
  technician_id?: number;
  category?: TicketCategory;
  priority?: TicketPriority;
  date_from?: string;
  date_to?: string;
}

export async function listTickets(filters?: TicketFilters): Promise<TicketOut[]> {
  const { data } = await apiClient.get<TicketOut[]>("/tickets", { params: filters });
  return data;
}

export async function closeTicket(
  id: number,
  resolutionComment: string | null,
  inventoryItemId: number,
): Promise<TicketOut> {
  const { data } = await apiClient.patch<TicketOut>(`/tickets/${id}/close`, {
    resolution_comment: resolutionComment,
    inventory_item_id: inventoryItemId,
  });
  return data;
}

export async function reassignTicket(id: number, technicianId: number): Promise<TicketOut> {
  const { data } = await apiClient.patch<TicketOut>(`/tickets/${id}/reassign`, {
    technician_id: technicianId,
  });
  return data;
}

export async function exportTickets(filters: TicketFilters | undefined, format: "xlsx" | "pdf"): Promise<void> {
  const filename = `arizalar.${format}`;
  await downloadBlob("/tickets/export", { ...filters, format }, filename);
}
