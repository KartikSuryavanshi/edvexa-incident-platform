from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    check_type: str
    endpoint: str | None
    enabled: bool


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    environment: str
    status: str
    created_at: datetime
    health_checks: list[HealthCheckRead] = []


class ServiceHealthRead(BaseModel):
    service: ServiceRead
    state: str
    reason: str
    latest_telemetry: "TelemetryRead | None" = None


class TelemetryCreate(BaseModel):
    latency_ms: float = Field(ge=0, le=120_000)
    error_rate: float = Field(ge=0, le=1)
    availability: float = Field(ge=0, le=1)
    observed_at: datetime | None = None


class TelemetryRead(TelemetryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    observed_at: datetime


ServiceHealthRead.model_rebuild()


class TelemetrySimulationRequest(BaseModel):
    scenario: str = Field(default="healthy", pattern="^(healthy|degraded|unhealthy)$")
    count: int = Field(default=1, ge=1, le=20)


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    fingerprint: str
    title: str
    description: str
    severity: str
    status: str
    opened_at: datetime
    updated_at: datetime


class IncidentTransitionRequest(BaseModel):
    status: str = Field(pattern="^(acknowledged|investigating|resolved|reopened)$")
    message: str | None = Field(default=None, max_length=500)


class IncidentEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    event_type: str
    message: str
    actor: str
    event_metadata: dict
    created_at: datetime


class PaginatedIncidents(BaseModel):
    items: list[IncidentRead]
    offset: int
    limit: int
    total: int
