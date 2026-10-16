FROM python:3.12-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=300 \
  PIP_RETRIES=10

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app ./app
COPY alembic.ini .
COPY alembic ./alembic

CMD ["sh", "-c", "python -m app.migrate && alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

EXPOSE 8000
