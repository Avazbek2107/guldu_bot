import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const MUTATING_METHODS = new Set(["post", "put", "patch", "delete"]);

// Populated by AuthContext after login/session-restore. The JWT itself lives in an
// httpOnly cookie the browser attaches automatically; this token only proves the
// request originated from our own page (CSRF double-submit defense).
export const csrfState = { token: null as string | null };

export const apiClient = axios.create({ baseURL: API_BASE_URL, withCredentials: true });

apiClient.interceptors.request.use((config) => {
  if (csrfState.token && config.method && MUTATING_METHODS.has(config.method.toLowerCase())) {
    config.headers["X-CSRF-Token"] = csrfState.token;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      csrfState.token = null;
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export async function downloadBlob(
  url: string,
  params: Record<string, unknown> | undefined,
  filename: string,
): Promise<void> {
  const response = await apiClient.get(url, { params, responseType: "blob" });
  const blobUrl = URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(blobUrl);
}

export async function downloadTicketPdf(ticketId: number, filename: string): Promise<void> {
  await downloadBlob(`/tickets/${ticketId}/pdf`, undefined, filename);
}

export function resolveAssetUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export function extractErrorDetail(err: unknown): string | undefined {
  return (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
}
