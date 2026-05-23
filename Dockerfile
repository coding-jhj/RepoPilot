FROM node:20-slim AS web-build

WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV REPOPILOT_LLM_PROVIDER=fake
ENV REPOPILOT_WORKSPACE_ROOT=/tmp/repopilot-workspaces
ENV REPOPILOT_FRONTEND_STATIC_DIR=/app/apps/web/out
ENV REPOPILOT_MAX_FILES_INDEXED=120
ENV REPOPILOT_MAX_FILE_BYTES=120000
ENV REPOPILOT_CLONE_TIMEOUT_SECONDS=45

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api ./apps/api
COPY --from=web-build /app/apps/web/out ./apps/web/out

WORKDIR /app/apps/api
RUN pip install --no-cache-dir -e .

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
