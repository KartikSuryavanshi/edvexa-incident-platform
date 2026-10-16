from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Incident, IncidentEvent, Service, TelemetrySample


def analyze_incident(db: Session, incident: Incident) -> dict:
    service = db.get(Service, incident.service_id)
    telemetry = db.scalar(
        select(TelemetrySample).where(TelemetrySample.service_id == incident.service_id).order_by(TelemetrySample.observed_at.desc())
    )
    event_count = db.scalar(select(IncidentEvent).where(IncidentEvent.incident_id == incident.id).order_by(IncidentEvent.created_at.desc()))
    facts = [f"Incident status is {incident.status} with severity {incident.severity}."]
    if service:
        facts.append(f"Affected service is {service.name} in the {service.environment} environment.")
    if telemetry:
        facts.extend([
            f"Latest latency is {telemetry.latency_ms:.0f} ms.",
            f"Latest error rate is {telemetry.error_rate:.1%}.",
            f"Latest availability is {telemetry.availability:.2%}.",
        ])
    if event_count:
        facts.append("Incident event history is available for correlation.")
    hypotheses = [f"The observed {incident.severity} condition is consistent with the telemetry threshold breach recorded for this incident."]
    return {
        "incident_id": incident.id,
        "provider": "deterministic-mock",
        "summary": incident.description,
        "observed_facts": facts,
        "hypotheses": hypotheses,
        "diagnostic_steps": ["Review recent telemetry for a sustained breach.", "Inspect the incident event timeline for correlated actions."],
        "recommendations": ["Use an approved simulated recovery action only after operator review."],
        "confidence": 0.72 if telemetry else 0.35,
        "limitations": ["No external logs, traces, or infrastructure signals are available in local demo mode."],
    }
