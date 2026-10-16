from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecoveryRequest(BaseModel):
    action_type: str = Field(pattern="^(restart_simulated|scale_simulated|retry_job_simulated)$")
    idempotency_key: str = Field(min_length=8, max_length=128)
    approved: bool = False


class RecoveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    action_type: str
    idempotency_key: str
    status: str
    attempts: int
    last_error: str | None
    duration_ms: int | None
    approved_at: datetime | None
    created_at: datetime

class AnalysisRead(BaseModel):
    incident_id: int
    provider: str
    summary: str
    observed_facts: list[str]
    hypotheses: list[str]
    diagnostic_steps: list[str]
    recommendations: list[str]
    confidence: float
    limitations: list[str]


class MetricsRead(BaseModel):
    content: str
    content_type: str = "text/plain; version=0.0.4"
