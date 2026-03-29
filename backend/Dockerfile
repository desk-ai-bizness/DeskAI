FROM python:3.12-slim-bookworm AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

# Use uv to install the project with dev dependencies into the system Python
RUN uv pip install --system --no-cache -e ".[dev]"

# ---------------------------------------------------------------------------

FROM builder AS dev

RUN useradd --create-home deskai
USER deskai
WORKDIR /app

ENTRYPOINT ["bash"]
