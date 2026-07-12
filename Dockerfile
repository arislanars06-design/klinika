# Multi-stage Dockerfile for the Klinika LOR web app.
# Stage 1 installs deps into a slim virtualenv, stage 2 copies it into a
# fresh base image so we don't ship build tools.

FROM python:3.11-slim AS build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src ./src
COPY templates ./templates
RUN pip install --no-deps -e .

# ---------- runtime ----------
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CLINIC_DATA_DIR=/data

WORKDIR /app
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /app /app

RUN mkdir -p /data/backups /data/logs && \
    useradd --system --uid 1000 clinic && chown -R clinic /app /data
USER clinic

EXPOSE 8000
VOLUME ["/data", "/app/templates"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD \
    python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz').read()" || exit 1

CMD ["python", "-m", "clinic.main", "--host", "0.0.0.0"]
