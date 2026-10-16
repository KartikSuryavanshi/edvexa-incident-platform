from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Incident, IncidentEvent, utcnow
from app.services.monitoring import record_event

ALLOWED_TRANSITIONS = {
    "open": {"acknowledged", "investigating", "resolved"},
    "acknowledged": {"investigating", "resolved"},
    "investigating": {"resolved"},
    "resolved": {"reopened", "closed"},
    "reopened": {"acknowledged", "investigating", "resolved"},
}


def transition_incident(db: Session, incident_id: int, new_status: str, message: str | None, actor: str) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    if new_status not in ALLOWED_TRANSITIONS.get(incident.status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition incident from {incident.status} to {new_status}",
        )
    old_status = incident.status
    incident.status = new_status
    incident.updated_at = utcnow()
    record_event(
        db,
        incident.id,
        "lifecycle_transition",
        message or f"Incident transitioned from {old_status} to {new_status}",
        {"from_status": old_status, "to_status": new_status},
        actor,
    )
    return incident


def get_incident_events(db: Session, incident_id: int):
    if db.get(Incident, incident_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return db.scalars(
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(IncidentEvent.created_at.asc())
    ).all()
