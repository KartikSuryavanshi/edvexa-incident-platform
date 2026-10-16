from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.db.models import Incident, Service

router = APIRouter(tags=["observability"])


@router.get("/metrics", include_in_schema=False, response_class=PlainTextResponse)
def metrics(db: Session = Depends(get_db)):
    services = db.scalar(select(func.count()).select_from(Service)) or 0
    incidents = db.scalar(select(func.count()).select_from(Incident).where(Incident.status != "resolved")) or 0
    critical = db.scalar(select(func.count()).select_from(Incident).where(Incident.severity == "critical", Incident.status != "resolved")) or 0
    return f"edvexa_services_total {services}\nedvexa_open_incidents {incidents}\nedvexa_critical_incidents {critical}\n"
