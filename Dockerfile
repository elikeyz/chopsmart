# =========================
# Stage 1: Build MCP
# =========================
FROM node:20-bullseye AS mcp-builder

WORKDIR /mcp-opennutrition

# Install build tools for native modules
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy MCP project
COPY mcp-opennutrition/package*.json ./
RUN npm ci

COPY mcp-opennutrition/ ./

RUN mkdir -p ./data \
  && curl -L \
  -o ./data/opennutrition-dataset-2025.1.zip \
  https://raw.githubusercontent.com/deadletterq/mcp-opennutrition/main/data/opennutrition-dataset-2025.1.zip

# Build native deps + project
RUN npm rebuild better-sqlite3
RUN npm run build

# =========================
# Stage 2: FastAPI backend
# =========================
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY backend/pyproject.toml backend/uv.lock ./

RUN uv sync --frozen --no-install-project

COPY backend/*.py ./

COPY --from=mcp-builder /mcp-opennutrition/ ./mcp-opennutrition/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
