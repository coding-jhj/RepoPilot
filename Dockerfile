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
# Semantic retrieval ON in the live image. The MiniLM weights are baked at build
# time into a known cache dir so the first request pays no download and the
# runtime needs no network or writable home (it would otherwise silently fall
# back to keyword search). HF_HUB_OFFLINE pins the load to the baked copy.
ENV REPOPILOT_USE_EMBEDDINGS=true
ENV HF_HOME=/app/model_cache
ENV SENTENCE_TRANSFORMERS_HOME=/app/model_cache

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api ./apps/api
COPY --from=web-build /app/apps/web/out ./apps/web/out

WORKDIR /app/apps/api
RUN pip install --no-cache-dir -e ".[embeddings]"
# Prebake the all-MiniLM-L6-v2 weights into the image (downloads to HF_HOME).
# a+rwX so the runtime user can read them and write lock files even if the
# container does not run as root.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
    && chmod -R a+rwX /app/model_cache
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
