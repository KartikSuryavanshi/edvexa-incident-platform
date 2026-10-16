from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.events import router as events_router
from app.api.routes.operations import router as operations_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.services import router as services_router
from app.api.routes.telemetry import router as telemetry_router
from app.core.config import settings

app = FastAPI(title="Edvexa Incident Platform", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Idempotency-Key"],
)
app.include_router(health_router, prefix="/api")
app.include_router(services_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(operations_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
