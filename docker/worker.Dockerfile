# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Builder stage — install Python dependencies into wheels
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------------------------------------------------------------------------
# Runtime stage — lean image for background worker processes
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

COPY api/ ./api/
COPY worker/ ./worker/
COPY scripts/ ./scripts/

USER app

# Default worker entrypoint runs the demo seed script in dry-run mode.
# Override this command in deployment manifests once a task-queue consumer
# (ingestion, embedding, evaluation jobs) is wired in.
CMD ["python", "scripts/run_worker.py"]
