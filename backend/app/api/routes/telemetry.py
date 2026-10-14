from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import Service, TelemetrySample
from app.schemas.service import TelemetryCreate, TelemetryRead, TelemetrySimulationRequest
from app.services.monitoring import ingest_telemetry, make_simulated_sample

router = APIRouter(prefix="/services/{service_id}/telemetry", tags=["telemetry"])


def get_service(db: Session, service_id: int) -> Service:
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return service


@router.post("", response_model=TelemetryRead, status_code=status.HTTP_201_CREATED)
def ingest(service_id: int, payload: TelemetryCreate, db: Session = Depends(get_db)):
    service = get_service(db, service_id)
    sample = TelemetrySample(service_id=service_id, **payload.model_dump(exclude_none=True))
    try:
        sample, _, _ = ingest_telemetry(db, service, sample)
        db.commit()
        db.refresh(sample)
        return sample
    except Exception:
        db.rollback()
        raise


@router.post("/simulate", response_model=list[TelemetryRead], status_code=status.HTTP_201_CREATED)
def simulate(service_id: int, payload: TelemetrySimulationRequest, db: Session = Depends(get_db)):
    service = get_service(db, service_id)
    samples = []
    try:
        for sequence in range(payload.count):
            sample = make_simulated_sample(service_id, payload.scenario, sequence)
            sample, _, _ = ingest_telemetry(db, service, sample)
            samples.append(sample)
        db.commit()
        for sample in samples:
            db.refresh(sample)
        return samples
    except Exception:
        db.rollback()
        raise
