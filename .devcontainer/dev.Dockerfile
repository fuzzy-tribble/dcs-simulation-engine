# syntax=docker/dockerfile:1
FROM python:3.10.13-slim

# Install git + optional SSH client for GitHub/Bitbucket, plus minimal build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git openssh-client ca-certificates curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Keep it minimal; no compilers unless your deps need them.
ENV POETRY_VIRTUALENVS_CREATE=false \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Pin Poetry to stable 2.1.x
RUN pip install --no-cache-dir "poetry==2.1.4"

WORKDIR /app

# Cache-friendly deps layer
COPY pyproject.toml poetry.lock* ./

# Build-time flag: include dev deps when true
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then \
    poetry install --no-root --with dev; \
    else \
    poetry install --no-root --only main; \
    fi

# App code
COPY . .

# No default CMD/ENTRYPOINT — set per service in compose