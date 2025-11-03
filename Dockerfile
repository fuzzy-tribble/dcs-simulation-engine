###
# Builder: export Poetry deps -> install into a venv (no dev deps)
###
FROM python:3.10.13-slim AS builder

ARG POETRY_VERSION=2.1.4

# Build tools only for wheel builds in this stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

# Poetry just for export
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Only dep files first for cache-friendly builds
COPY pyproject.toml poetry.lock* ./

# Export main (prod) deps and install into venv
RUN poetry export --only main --format requirements.txt --output /tmp/requirements.txt --without-hashes
RUN python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip \
    && /venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

###
# Runtime: minimal image with only the venv + app code
###
FROM python:3.10.13-slim

# Create non-root user
RUN useradd -m appuser

# Copy venv from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

# Cloud Run/GKE friendly defaults
ENV PORT=8080 \
    APP_TARGET=api \
    GAME=Explore

# Tiny entrypoint that chooses which script to run based on env
# Supports either scripts/ or script/ folder names.
RUN printf '%s\n' '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'script_path() {' \
    '  if [[ -f "scripts/$1" ]]; then echo "scripts/$1"; elif [[ -f "script/$1" ]]; then echo "script/$1"; else echo "$1"; fi' \
    '}' \
    'case "${APP_TARGET}" in' \
    '  widget)' \
    '    exec python "$(script_path run_widget.py)" --game "${GAME}"' \
    '    ;;' \
    '  api|*)' \
    '    exec python "$(script_path run_api.py)"' \
    '    ;;' \
    'esac' > /entrypoint.sh \
    && chmod +x /entrypoint.sh

USER appuser
EXPOSE 8080
ENTRYPOINT ["/entrypoint.sh"]