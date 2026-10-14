from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.db.models import Service, TelemetrySample
from app.schemas.service import ServiceHealthRead, ServiceRead, TelemetryRead
from app.services.monitoring import evaluate_health

router = APIRouter(prefix="/services", tags=["services"])


def get_service_or_404(db: Session, service_id: int) -> Service:
    service = db.scalar(select(Service).options(selectinload(Service.health_checks)).where(Service.id == service_id))
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.get("", response_model=list[ServiceRead])
def list_services(db: Session = Depends(get_db)):
    return db.scalars(select(Service).options(selectinload(Service.health_checks)).order_by(Service.name)).all()


@router.get("/{service_id}/health", response_model=ServiceHealthRead)
def service_health(service_id: int, db: Session = Depends(get_db)):
    service = get_service_or_404(db, service_id)
    latest = db.scalar(
        select(TelemetrySample)
        .where(TelemetrySample.service_id == service_id)
        .order_by(TelemetrySample.observed_at.desc())
    )
    if latest is None:
        return {"service": service, "state": service.status, "reason": "no telemetry observed yet", "latest_telemetry": None}
    evaluation = evaluate_health(latest)
    return {"service": service, "state": evaluation.state, "reason": evaluation.reason, "latest_telemetry": latest}


@router.get("/{service_id}/telemetry", response_model=list[TelemetryRead])
def recent_telemetry(service_id: int, limit: int = 20, db: Session = Depends(get_db)):
    get_service_or_404(db, service_id)
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="limit must be between 1 and 100")
    return db.scalars(
        select(TelemetrySample)
        .where(TelemetrySample.service_id == service_id)
        .order_by(TelemetrySample.observed_at.desc())
        .limit(limit)
    ).all()
