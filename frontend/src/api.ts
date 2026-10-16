import type { Analysis, Incident, IncidentEvent, Service, Telemetry } from "./types";

const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";
const token = import.meta.env.VITE_AUTH_TOKEN ?? "operator-demo";
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, { headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(options?.headers ?? {}) }, ...options });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail ?? `Request failed (${response.status})`);
  return response.json() as Promise<T>;
}
export const api = {
  services: () => request<Service[]>("/services"),
  telemetry: (id: number) => request<Telemetry[]>(`/services/${id}/telemetry?limit=12`),
  incidents: () => request<{ items: Incident[]; total: number }>("/incidents?limit=20"),
  events: (id: number) => request<IncidentEvent[]>(`/incidents/${id}/events`),
  simulate: (id: number, scenario: string) => request<Telemetry[]>(`/services/${id}/telemetry/simulate`, { method: "POST", body: JSON.stringify({ scenario }) }),
  transition: (id: number, next: string) => request<Incident>(`/incidents/${id}/transition`, { method: "POST", body: JSON.stringify({ status: next }) }),
  analysis: (id: number) => request<Analysis>(`/incidents/${id}/analysis`, { method: "POST" }),
  recovery: (id: number, approved: boolean) => request<{ status: string }>(`/incidents/${id}/recovery`, { method: "POST", body: JSON.stringify({ action_type: "restart_simulated", idempotency_key: `demo-${id}`, approved }) }),
};
