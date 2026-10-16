from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import CurrentUser, current_user, require_role
from app.db.models import AnalysisResult, Incident, RecoveryAction, utcnow
from app.schemas.operations import AnalysisRead, RecoveryRead
from app.schemas.operations import RecoveryRequest
from app.services.analysis import analyze_incident
from app.services.recovery import execute_recovery

router = APIRouter(prefix="/incidents", tags=["operations"])


def incident_or_404(db: Session, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post("/{incident_id}/analysis", response_model=AnalysisRead)
def analysis(incident_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(current_user)):
    incident = incident_or_404(db, incident_id)
    payload = analyze_incident(db, incident)
    db.add(AnalysisResult(incident_id=incident.id, provider=payload["provider"], payload=payload))
    db.commit()
    return payload


@router.post("/{incident_id}/recovery", response_model=RecoveryRead)
def recovery(incident_id: int, request: RecoveryRequest, db: Session = Depends(get_db), user: CurrentUser = Depends(require_role("operator", "admin"))):
    incident = incident_or_404(db, incident_id)
    try:
        action = execute_recovery(db, incident, request.action_type, request.idempotency_key, request.approved)
        db.commit()
        db.refresh(action)
        return action
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get("/{incident_id}/recovery", response_model=list[RecoveryRead])
def recovery_history(incident_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(current_user)):
    incident_or_404(db, incident_id)
    return db.scalars(select(RecoveryAction).where(RecoveryAction.incident_id == incident_id).order_by(RecoveryAction.created_at.desc())).all()
