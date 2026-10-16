export type Service = { id: number; name: string; environment: string; status: string; created_at: string };
export type Telemetry = { id: number; service_id: number; latency_ms: number; error_rate: number; availability: number; observed_at: string };
export type Incident = { id: number; service_id: number; title: string; description: string; severity: string; status: string; updated_at: string };
export type IncidentEvent = { id: number; event_type: string; message: string; actor: string; event_metadata: Record<string, unknown>; created_at: string };
export type Analysis = { summary: string; observed_facts: string[]; hypotheses: string[]; recommendations: string[]; confidence: number; limitations: string[] };
