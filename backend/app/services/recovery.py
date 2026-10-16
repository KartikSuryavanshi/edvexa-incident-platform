from time import monotonic, sleep

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Incident, RecoveryAction, Service, utcnow
from app.services.monitoring import ingest_telemetry, make_simulated_sample, record_event

ALLOWED_ACTIONS = {"restart_simulated", "scale_simulated", "retry_job_simulated"}


def execute_recovery(db: Session, incident: Incident, action_type: str, idempotency_key: str, approved: bool) -> RecoveryAction:
    if action_type not in ALLOWED_ACTIONS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported simulated recovery action")
    existing = db.scalar(select(RecoveryAction).where(RecoveryAction.idempotency_key == idempotency_key))
    if existing is not None:
        if existing.incident_id != incident.id or existing.action_type != action_type:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Idempotency key is already used for another action")
        if existing.status in {"succeeded", "failed"} or not approved:
            return existing
        action = existing
    else:
        action = RecoveryAction(incident_id=incident.id, action_type=action_type, idempotency_key=idempotency_key)
        db.add(action)
        db.flush()
    if not approved:
        action.status = "pending_approval"
        record_event(db, incident.id, "recovery_requested", f"Simulated action {action_type} awaits approval", {"action_type": action_type})
        return action

    action.approved_at = action.approved_at or utcnow()
    action.status = "running"
    started = monotonic()
    service = db.get(Service, incident.service_id)
    succeeded = False
    for attempt in range(1, settings.recovery_max_attempts + 1):
        action.attempts += 1
        try:
            if service is None:
                raise RuntimeError("Affected service no longer exists")
            if action_type == "retry_job_simulated" and attempt == 1:
                raise RuntimeError("simulated transient job failure")
            # This intentionally records a healthy simulated measurement; it never calls infrastructure.
            sample = make_simulated_sample(service.id, "healthy", attempt)
            ingest_telemetry(db, service, sample)
            succeeded = True
            break
        except Exception as exc:
            action.last_error = str(exc)[:500]
            if attempt < settings.recovery_max_attempts:
                sleep(settings.recovery_backoff_seconds * (2 ** (attempt - 1)))
    action.status = "succeeded" if succeeded else "failed"
    action.duration_ms = int((monotonic() - started) * 1000)
    if succeeded:
        action.last_error = None
        record_event(db, incident.id, "recovery_succeeded", f"Simulated action {action_type} completed", {"action_id": action.id, "attempts": action.attempts})
    else:
        record_event(db, incident.id, "recovery_failed", "Simulated recovery failed after bounded retries", {"error": action.last_error, "attempts": action.attempts})
    return action
