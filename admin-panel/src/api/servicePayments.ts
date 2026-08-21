import { apiClient } from "./client";
import type { ServicePaymentOut } from "../types";

export interface ServicePaymentPayload {
  name: string;
  category: string;
  due_date: string;
  responsible_person?: string | null;
  notes?: string | null;
}

export async function listServicePayments(): Promise<ServicePaymentOut[]> {
  const { data } = await apiClient.get<ServicePaymentOut[]>("/service-payments");
  return data;
}

export async function createServicePayment(payload: ServicePaymentPayload): Promise<ServicePaymentOut> {
  const { data } = await apiClient.post<ServicePaymentOut>("/service-payments", payload);
  return data;
}

export async function updateServicePayment(
  id: number,
  payload: Partial<ServicePaymentPayload>,
): Promise<ServicePaymentOut> {
  const { data } = await apiClient.patch<ServicePaymentOut>(`/service-payments/${id}`, payload);
  return data;
}

export async function deleteServicePayment(id: number): Promise<void> {
  await apiClient.delete(`/service-payments/${id}`);
}
