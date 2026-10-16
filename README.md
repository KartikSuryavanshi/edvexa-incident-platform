# Edvexa Reliability Operations Console

Edvexa is a local, cloud-native service reliability and incident response demonstration. It simulates service telemetry, evaluates configurable health thresholds, creates and deduplicates incidents, preserves an auditable lifecycle, provides safe simulated remediation, and exposes deterministic offline incident analysis.

## Architecture

```mermaid
flowchart LR
  UI[React + TypeScript dashboard] --> API[FastAPI REST + SSE]
  API --> MON[Monitoring and incident services]
  MON --> DB[(PostgreSQL)]
  API --> AI[Deterministic analysis adapter]
  API --> REC[Approval-gated simulated recovery]
  API --> MET[Prometheus-compatible metrics]
```

The backend owns all state changes. Telemetry is explicitly simulated; recovery writes a healthy simulated sample and an audit event but never invokes shells, cloud APIs, Kubernetes, or Docker control-plane commands. PostgreSQL is the runtime database, and Alembic migrations are applied before seed data.

## Features

- Deterministic healthy, degraded, and unhealthy telemetry scenarios.
- Configurable threshold evaluation for latency, error rate, availability, and heartbeat health, with CPU, memory, and request-volume history.
- Stable active-incident deduplication with new incidents after recovery.
- Incident states: `open`, `acknowledged`, `investigating`, `resolved`, `reopened`, and `closed`.
- Persistent incident event timelines and transition validation.
- Approval-gated simulated recovery with idempotency keys and outcome tracking.
- Offline structured incident analysis with observed facts, hypotheses, recommendations, confidence, and limitations.
- Service, telemetry, incident, recovery, readiness, metrics, and SSE endpoints.
- React dashboard with live incident feed, service simulation, incident timeline, evidence, analysis, and recovery controls.
- Local bearer-token roles: `viewer` can inspect, while `operator` and `admin` can ingest telemetry, transition incidents, and approve simulated recovery.

## Run locally with Docker Compose

Prerequisites: Docker Desktop (or Docker Engine with Compose) and Git.

```bash
cp .env.example .env
# Replace every generate-* value with locally generated random values.
docker compose up --build
```

Open the dashboard at <http://localhost:5173>. The API and OpenAPI docs are at <http://localhost:8000/docs>. Stop the stack with `docker compose down`; add `-v` only when intentionally deleting the local PostgreSQL volume.

The backend startup sequence validates any legacy unversioned schema, runs `alembic upgrade head`, performs an idempotent seed, and then starts Uvicorn. A database with an empty `alembic_version` table is never blindly replayed: it is stamped only when its tables and columns exactly match a known migration boundary. Unknown schemas fail fast for manual review.

The bootstrap also recognizes one verified legacy development shape: the six `0001_initial` tables plus `health_checks`, created by an earlier `create_all()` startup before the incident-engine columns were migrated. It stamps only `0001_initial`; the idempotent `0002_incident_engine` migration adds its missing columns and preserves the existing `health_checks` table. Any other partial or extra-column shape is rejected without modification.

Compose requires tokens in `.env`; the example values are placeholders only. Keep the Vercel deployment read-only with a viewer token. Never put an operator or admin token in a public frontend build because Vite embeds `VITE_*` values into browser JavaScript.

## Manual backend development

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
export DATABASE_URL="postgresql+psycopg://$POSTGRES_USER:$POSTGRES_PASSWORD@localhost:5432/$POSTGRES_DB"
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

For isolated unit tests, the existing fixture uses an in-memory SQLite database. Production and Compose configuration remain PostgreSQL-backed.

## Demo walkthrough

1. Start Compose and open the dashboard.
2. Click **Simulate** for a service; this submits a deterministic degraded sample.
3. Open the incident to inspect measured latency, error rate, availability, and the event timeline.
4. Click **Analyze evidence** to receive the deterministic local analysis.
5. Request recovery, then approve the simulated action. The recovery records an outcome and submits a healthy sample; it does not change real infrastructure.
6. Repeat the same simulation before recovery to observe one incident with a `signal_observed` audit event rather than duplicates.

## API examples

```bash
export EDVEXA_TOKEN="$OPERATOR_TOKEN"
curl -H "Authorization: Bearer $EDVEXA_TOKEN" http://localhost:8000/api/services
curl -X POST http://localhost:8000/api/services/1/telemetry/simulate \
  -H "Authorization: Bearer $EDVEXA_TOKEN" -H 'content-type: application/json' -d '{"scenario":"unhealthy","count":2}'
curl -H "Authorization: Bearer $EDVEXA_TOKEN" 'http://localhost:8000/api/incidents?status_filter=open&limit=20'
curl -X POST -H "Authorization: Bearer $EDVEXA_TOKEN" http://localhost:8000/api/incidents/1/analysis
curl -X POST http://localhost:8000/api/incidents/1/recovery \
  -H "Authorization: Bearer $EDVEXA_TOKEN" -H 'content-type: application/json' \
  -d '{"action_type":"restart_simulated","idempotency_key":"demo-incident-1","approved":true}'
curl -N -H "Authorization: Bearer $EDVEXA_TOKEN" http://localhost:8000/api/events/stream
```

## Testing and observability

```bash
./.venv/bin/pytest backend -q --capture=no
cd frontend
npm install
npm test
npm run typecheck
npm run build
npm audit --omit=dev --audit-level=high
cd ..
docker compose config
docker compose exec backend alembic current
docker compose exec backend pytest -q
```

The backend verification currently passes with `13 passed`. The frontend verification passes with `2` Vitest tests, a clean typecheck, a successful Vite production build, and `npm audit --omit=dev --audit-level=high` reporting no production vulnerabilities. Docker and PostgreSQL integration checks require a local Docker engine and are listed separately because they cannot be simulated by the SQLite unit-test fixture.

The API exposes `/api/live` for process liveness, `/api/ready` for database readiness, and `/api/metrics` for simple Prometheus text metrics. The dashboard consumes the API URL from `VITE_API_URL`; the default browser-visible value is `http://localhost:8000/api`.

## Security and limitations

Inputs are validated with Pydantic, query sizes are bounded, SQLAlchemy parameterized queries are used, CORS is configured explicitly, role-protected state changes use bearer tokens, idempotency keys protect simulated actions, and AI output is informational only. The browser SSE client uses the explicitly documented `access_token` query parameter because native `EventSource` cannot set headers; use HTTPS and a short-lived token for any non-demo deployment. This MVP does not include distributed SSE, real logs/traces, real infrastructure integrations, or a hosted model provider. Those are deliberate boundaries for a safe local screening demonstration.

## Project layout

- `backend/app/api/routes/` — HTTP and SSE endpoints.
- `backend/app/services/` — monitoring, lifecycle, analysis, and simulated recovery logic.
- `backend/app/db/` — SQLAlchemy models and session configuration.
- `backend/alembic/` — ordered PostgreSQL schema migrations.
- `frontend/src/` — typed React dashboard and API client.
- `docker-compose.yml` — PostgreSQL, API, and dashboard services.
