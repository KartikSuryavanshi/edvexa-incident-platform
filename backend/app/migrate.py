"""Safely bridge databases created before Alembic was introduced.

Fresh databases are left untouched here and are created by ``alembic upgrade head``.
An existing unversioned database is stamped only when its public table/column
fingerprint exactly matches a known migration boundary.
"""

import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.core.database import engine

logger = logging.getLogger(__name__)

BASELINE_SCHEMAS = {
    "0001_initial": {
        "services": {"id", "name", "environment", "status", "created_at"},
        "telemetry_samples": {"id", "service_id", "latency_ms", "error_rate", "availability", "observed_at"},
        "incidents": {"id", "service_id", "fingerprint", "title", "severity", "status", "opened_at", "updated_at"},
        "incident_events": {"id", "incident_id", "event_type", "message", "actor", "created_at"},
        "recovery_actions": {"id", "incident_id", "action_type", "idempotency_key", "status", "attempts", "created_at"},
        "analysis_results": {"id", "incident_id", "provider", "payload", "created_at"},
    },
    "0002_incident_engine": {
        "services": {"id", "name", "environment", "status", "created_at"},
        "telemetry_samples": {"id", "service_id", "latency_ms", "error_rate", "availability", "observed_at"},
        "incidents": {"id", "service_id", "fingerprint", "deduplication_key", "title", "description", "severity", "status", "opened_at", "updated_at"},
        "incident_events": {"id", "incident_id", "event_type", "message", "actor", "metadata", "created_at"},
        "recovery_actions": {"id", "incident_id", "action_type", "idempotency_key", "status", "attempts", "created_at"},
        "analysis_results": {"id", "incident_id", "provider", "payload", "created_at"},
        "health_checks": {"id", "service_id", "name", "check_type", "endpoint", "enabled", "created_at"},
    },
    "0003_recovery_tracking": {
        "services": {"id", "name", "environment", "status", "created_at"},
        "telemetry_samples": {"id", "service_id", "latency_ms", "error_rate", "availability", "observed_at"},
        "incidents": {"id", "service_id", "fingerprint", "deduplication_key", "title", "description", "severity", "status", "opened_at", "updated_at"},
        "incident_events": {"id", "incident_id", "event_type", "message", "actor", "metadata", "created_at"},
        "recovery_actions": {"id", "incident_id", "action_type", "idempotency_key", "status", "attempts", "last_error", "duration_ms", "approved_at", "created_at"},
        "analysis_results": {"id", "incident_id", "provider", "payload", "created_at"},
        "health_checks": {"id", "service_id", "name", "check_type", "endpoint", "enabled", "created_at"},
    },
    "0004_telemetry_resources": {
        "services": {"id", "name", "environment", "status", "created_at"},
        "telemetry_samples": {"id", "service_id", "latency_ms", "error_rate", "availability", "cpu_usage", "memory_usage", "request_volume", "heartbeat_ok", "observed_at"},
        "incidents": {"id", "service_id", "fingerprint", "deduplication_key", "title", "description", "severity", "status", "opened_at", "updated_at"},
        "incident_events": {"id", "incident_id", "event_type", "message", "actor", "metadata", "created_at"},
        "recovery_actions": {"id", "incident_id", "action_type", "idempotency_key", "status", "attempts", "last_error", "duration_ms", "approved_at", "created_at"},
        "analysis_results": {"id", "incident_id", "provider", "payload", "created_at"},
        "health_checks": {"id", "service_id", "name", "check_type", "endpoint", "enabled", "created_at"},
    },
    "0005_incident_assignment": {
        "services": {"id", "name", "environment", "status", "owner_team", "created_at"},
        "telemetry_samples": {"id", "service_id", "latency_ms", "error_rate", "availability", "cpu_usage", "memory_usage", "request_volume", "heartbeat_ok", "observed_at"},
        "incidents": {"id", "service_id", "fingerprint", "deduplication_key", "title", "description", "assigned_to", "severity", "status", "opened_at", "updated_at"},
        "incident_events": {"id", "incident_id", "event_type", "message", "actor", "metadata", "created_at"},
        "recovery_actions": {"id", "incident_id", "action_type", "idempotency_key", "status", "attempts", "last_error", "duration_ms", "approved_at", "created_at"},
        "analysis_results": {"id", "incident_id", "provider", "payload", "created_at"},
        "health_checks": {"id", "service_id", "name", "check_type", "endpoint", "enabled", "created_at"},
    },
}

# A previous development startup used ``Base.metadata.create_all()`` while
# the incident-engine migration was still pending. It created health_checks
# from the newer model but not the three 0002 columns. This exact fingerprint
# is safe to reconcile by stamping 0001 and letting 0002 add its missing
# columns; unknown partial schemas remain rejected.
LEGACY_PARTIAL_SCHEMAS = {
    "legacy_0001_plus_health_checks": {
        **BASELINE_SCHEMAS["0001_initial"],
        "health_checks": BASELINE_SCHEMAS["0002_incident_engine"]["health_checks"],
    },
}


def classify_schema(table_columns: dict[str, set[str]]) -> str | None:
    for revision, expected in reversed(list(BASELINE_SCHEMAS.items())):
        if table_columns == expected:
            return revision
    for fingerprint, expected in LEGACY_PARTIAL_SCHEMAS.items():
        if table_columns == expected:
            return fingerprint
    return None


def ensure_baseline():
    with engine.connect() as connection:
        inspector = inspect(connection)
        schema = "public" if connection.dialect.name == "postgresql" else None
        tables = set(inspector.get_table_names(schema=schema))
        if "alembic_version" in tables:
            version_rows = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
            if len(version_rows) > 1:
                raise RuntimeError("Found multiple Alembic revisions; refusing to alter the database.")
            if version_rows:
                return
            # A failed first migration can leave the version table present but
            # empty after creating some application tables. Treat it as an
            # unversioned schema and validate it below instead of allowing
            # `alembic upgrade` to replay the initial migration blindly.
            tables.remove("alembic_version")
        if not tables:
            logger.info("No existing schema detected; Alembic will create a fresh database.")
            return
        table_columns = {
            table: {column["name"] for column in inspector.get_columns(table, schema=schema)}
            for table in tables
        }
    revision = classify_schema(table_columns)
    if revision is None:
        raise RuntimeError(
            "Found an unversioned PostgreSQL schema that does not exactly match a known "
            "Edvexa migration boundary; refusing to stamp or alter it."
        )
    stamp_revision = revision
    if revision in LEGACY_PARTIAL_SCHEMAS:
        stamp_revision = "0001_initial"
        logger.warning(
            "Existing schema matches recognized partial state %s; stamping %s so Alembic can reconcile it.",
            revision,
            stamp_revision,
        )
    else:
        logger.warning("Existing schema matches %s; stamping only that explicit baseline before upgrade.", revision)
    alembic_config = Config("alembic.ini")
    command.stamp(alembic_config, stamp_revision)


if __name__ == "__main__":
    ensure_baseline()
