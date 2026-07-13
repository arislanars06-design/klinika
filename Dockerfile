# syntax=docker/dockerfile:1.6
# ---- Clinic LOR — web layer container ----------------------------------------
# Multi-stage build: keep the runtime image lean, drop compilers after install.

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Copy pyproject first for better layer caching.
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY templates/ ./templates/

# Install only the deps the web layer actually needs (skip PySide6 — the web
# app never boots a Qt window). This keeps the image ~4x smaller.
RUN pip install --upgrade pip && \
    pip wheel --no-deps --wheel-dir=/wheels \
        "SQLAlchemy>=2.0" "alembic>=1.13" \
        "python-docx>=1.1" "docxtpl>=0.16" \
        "pydantic>=2.5" "pydantic-settings>=2.1" "python-dateutil>=2.8" \
        "loguru>=0.7" \
        "fastapi>=0.111" "uvicorn[standard]>=0.29" "jinja2>=3.1" \
        "python-multipart>=0.0.9" "itsdangerous>=2.1" \
        "matplotlib>=3.8"

# ---- Runtime -----------------------------------------------------------------

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CLINIC_DATA_DIR=/data \
    CLINIC_WEB_HOST=0.0.0.0 \
    CLINIC_WEB_PORT=8000

# Small runtime deps required by python-docx/docxtpl and lxml wheels.
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends libxml2 libxslt1.1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install pre-built wheels and the app source
COPY --from=builder /wheels /wheels
COPY --from=builder /build /app
RUN pip install --no-cache-dir /wheels/*.whl && \
    pip install --no-cache-dir --no-deps -e . && \
    rm -rf /wheels

# Volumes: sqlite db + template + backups all live under /data.
RUN mkdir -p /data/backups
VOLUME ["/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/login').read()" || exit 1

CMD ["python", "-m", "clinic.web.main"]
