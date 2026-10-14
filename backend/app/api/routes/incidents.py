from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import Incident
from app.schemas.service import IncidentEventRead, IncidentRead, IncidentTransitionRequest, PaginatedIncidents
from app.services.lifecycle import get_incident_events, transition_incident

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=PaginatedIncidents)
def list_incidents(
    offset: int = 0,
    limit: int = 20,
    service_id: int | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
):
    if offset < 0 or not 1 <= limit <= 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="offset must be >= 0 and limit must be between 1 and 100")
    query = select(Incident)
    count_query = select(func.count()).select_from(Incident)
    if service_id is not None:
        query = query.where(Incident.service_id == service_id)
        count_query = count_query.where(Incident.service_id == service_id)
    if status_filter is not None:
        query = query.where(Incident.status == status_filter)
        count_query = count_query.where(Incident.status == status_filter)
    items = db.scalars(query.order_by(Incident.updated_at.desc()).offset(offset).limit(limit)).all()
    return {"items": items, "offset": offset, "limit": limit, "total": db.scalar(count_query) or 0}


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.get("/{incident_id}/events", response_model=list[IncidentEventRead])
def incident_events(incident_id: int, db: Session = Depends(get_db)):
    return get_incident_events(db, incident_id)


@router.post("/{incident_id}/transition", response_model=IncidentRead)
def transition(
    incident_id: int,
    payload: IncidentTransitionRequest,
    x_actor: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    try:
        incident = transition_incident(db, incident_id, payload.status, payload.message, x_actor or "operator")
        db.commit()
        db.refresh(incident)
        return incident
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
