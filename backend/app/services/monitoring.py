from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Incident, IncidentEvent, Service, TelemetrySample, utcnow

DEGRADED_THRESHOLDS = {"latency_ms": 300.0, "error_rate": 0.05, "availability": 0.995}
UNHEALTHY_THRESHOLDS = {"latency_ms": 1000.0, "error_rate": 0.20, "availability": 0.95}
ACTIVE_STATUSES = {"open", "acknowledged", "investigating", "reopened"}


@dataclass(frozen=True)
class HealthEvaluation:
    state: str
    reason: str


def evaluate_health(sample: TelemetrySample) -> HealthEvaluation:
    unhealthy_reasons: list[str] = []
    degraded_reasons: list[str] = []
    if sample.latency_ms >= UNHEALTHY_THRESHOLDS["latency_ms"]:
        unhealthy_reasons.append(f"latency {sample.latency_ms:.0f}ms")
    elif sample.latency_ms >= DEGRADED_THRESHOLDS["latency_ms"]:
        degraded_reasons.append(f"latency {sample.latency_ms:.0f}ms")
    if sample.error_rate >= UNHEALTHY_THRESHOLDS["error_rate"]:
        unhealthy_reasons.append(f"error rate {sample.error_rate:.1%}")
    elif sample.error_rate >= DEGRADED_THRESHOLDS["error_rate"]:
        degraded_reasons.append(f"error rate {sample.error_rate:.1%}")
    if sample.availability < UNHEALTHY_THRESHOLDS["availability"]:
        unhealthy_reasons.append(f"availability {sample.availability:.2%}")
    elif sample.availability < DEGRADED_THRESHOLDS["availability"]:
        degraded_reasons.append(f"availability {sample.availability:.2%}")
    if unhealthy_reasons:
        return HealthEvaluation("unhealthy", ", ".join(unhealthy_reasons))
    if degraded_reasons:
        return HealthEvaluation("degraded", ", ".join(degraded_reasons))
    return HealthEvaluation("healthy", "all monitored signals are within thresholds")


def simulated_values(scenario: str) -> tuple[float, float, float]:
    return {
        "healthy": (80.0, 0.01, 0.999),
        "degraded": (450.0, 0.08, 0.985),
        "unhealthy": (1500.0, 0.30, 0.90),
    }[scenario]


def record_event(
    db: Session,
    incident_id: int,
    event_type: str,
    message: str,
    event_metadata: dict | None = None,
    actor: str = "system",
) -> IncidentEvent:
    event = IncidentEvent(
        incident_id=incident_id,
        event_type=event_type,
        message=message,
        actor=actor,
        event_metadata=event_metadata or {},
    )
    db.add(event)
    return event


def detect_incident(db: Session, service: Service, sample: TelemetrySample, evaluation: HealthEvaluation) -> Incident | None:
    service.status = evaluation.state
    if evaluation.state == "healthy":
        active = db.scalars(
            select(Incident).where(Incident.service_id == service.id, Incident.status.in_(ACTIVE_STATUSES))
        ).all()
        for incident in active:
            incident.status = "resolved"
            incident.updated_at = utcnow()
            record_event(db, incident.id, "auto_resolved", "Service health recovered", {"reason": evaluation.reason})
        return None

    deduplication_key = f"service:{service.id}:health:{evaluation.state}"
    active_incident = db.scalar(
        select(Incident)
        .where(Incident.deduplication_key == deduplication_key, Incident.status.in_(ACTIVE_STATUSES))
        .order_by(Incident.updated_at.desc())
    )
    telemetry_metadata = {
        "latency_ms": sample.latency_ms,
        "error_rate": sample.error_rate,
        "availability": sample.availability,
        "health_state": evaluation.state,
    }
    if active_incident:
        active_incident.updated_at = utcnow()
        record_event(db, active_incident.id, "signal_observed", "Repeated failure signal deduplicated", telemetry_metadata)
        return active_incident

    severity = "critical" if evaluation.state == "unhealthy" else "warning"
    incident = Incident(
        service_id=service.id,
        fingerprint=f"{deduplication_key}:{uuid4().hex[:12]}",
        deduplication_key=deduplication_key,
        title=f"{evaluation.state.title()} health for {service.name}",
        description=f"{service.name} is {evaluation.state}: {evaluation.reason}.",
        severity=severity,
        status="open",
    )
    db.add(incident)
    db.flush()
    record_event(db, incident.id, "incident_created", incident.description, telemetry_metadata)
    return incident


def ingest_telemetry(db: Session, service: Service, sample: TelemetrySample) -> tuple[TelemetrySample, HealthEvaluation, Incident | None]:
    evaluation = evaluate_health(sample)
    db.add(sample)
    db.flush()
    incident = detect_incident(db, service, sample, evaluation)
    return sample, evaluation, incident


def make_simulated_sample(service_id: int, scenario: str, sequence: int = 0) -> TelemetrySample:
    latency_ms, error_rate, availability = simulated_values(scenario)
    return TelemetrySample(
        service_id=service_id,
        latency_ms=latency_ms,
        error_rate=error_rate,
        availability=availability,
        observed_at=datetime.now(timezone.utc) + timedelta(microseconds=sequence),
    )
