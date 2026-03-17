# ── Backend ──────────────────────────────────────────────
FROM python:3.12-slim AS backend
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# ── Frontend ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --silent
COPY frontend/ .
RUN npm run build

# ── Production Image ─────────────────────────────────────
FROM python:3.12-slim AS production
WORKDIR /app

# Install Node.js for Next.js server
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Backend
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY backend/ /app/backend/

# Frontend (built)
COPY --from=frontend-build /app/frontend/.next /app/frontend/.next
COPY --from=frontend-build /app/frontend/node_modules /app/frontend/node_modules
COPY --from=frontend-build /app/frontend/package.json /app/frontend/package.json
COPY --from=frontend-build /app/frontend/public /app/frontend/public

# Startup script
COPY docker-start.sh /app/docker-start.sh
RUN chmod +x /app/docker-start.sh

ENV USE_MEMORY_DB=true
EXPOSE 8000 3000

CMD ["/app/docker-start.sh"]
