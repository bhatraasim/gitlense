FROM python:3.12-slim

# install system deps
RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

# install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# copy code
COPY . .