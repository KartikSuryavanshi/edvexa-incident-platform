import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import CurrentUser, current_user
from app.db.models import Incident

router = APIRouter(prefix="/events", tags=["events"])


async def incident_stream(service_id: int | None):
    last_seen: datetime | None = None
    while True:
        with SessionLocal() as db:
            query = select(Incident).order_by(Incident.updated_at.desc()).limit(1)
            if service_id is not None:
                query = query.where(Incident.service_id == service_id)
            incident = db.scalar(query)
            if incident and (last_seen is None or incident.updated_at > last_seen):
                last_seen = incident.updated_at
                payload = {"id": incident.id, "status": incident.status, "severity": incident.severity, "updated_at": incident.updated_at.isoformat()}
                yield f"event: incident\ndata: {json.dumps(payload)}\n\n"
            else:
                yield ": keepalive\n\n"
        await asyncio.sleep(2)


@router.get("/stream")
async def stream(service_id: int | None = Query(default=None, ge=1), user: CurrentUser = Depends(current_user)):
    return StreamingResponse(incident_stream(service_id), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
