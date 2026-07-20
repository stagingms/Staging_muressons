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

# Install Node.js + curl (curl needed for backend health-check in startup)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Backend
COPY --from=backend /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY backend/ /app/backend/

# Seed data (db/seed_round1.json etc.)
COPY db/ /app/db/

# Frontend (built)
COPY --from=frontend-build /app/frontend/.next /app/frontend/.next
COPY --from=frontend-build /app/frontend/node_modules /app/frontend/node_modules
COPY --from=frontend-build /app/frontend/package.json /app/frontend/package.json
COPY --from=frontend-build /app/frontend/public /app/frontend/public

# Startup script
COPY docker-start.sh /app/docker-start.sh
RUN chmod +x /app/docker-start.sh

# Railway injects PORT env at runtime; default to 3000
# SEC-2: do NOT bake USE_MEMORY_DB=true into the production image. The store is
# selected at deploy time:
#   • Production: set USE_MEMORY_DB=false + DATABASE_URL (PostgreSQL).
#   • Local/offline: set USE_MEMORY_DB=true with DEBUG=true (or
#     ALLOW_MEMORY_DB_IN_PROD=true for an intentional non-durable run).
# main.py refuses to boot on the in-memory store when DEBUG=false unless the
# override is set, so an accidental memory-DB production deploy fails loudly
# instead of silently losing sessions.
ENV PORT=3000
ENV USE_MEMORY_DB=false
ENV MURESSONS_DATA_DIR=/data
ENV JWT_SECRET=0f8cfdfc1dd5c1bcbbc72623ef0a8b1921f1703291b326f2f1eb6b73756c3db5
ENV JWT_EXPIRY_HOURS=8
ENV MASTER_PASSWORD=w6eAsGMKm3ODQ8wHWRbezPsh
ENV PROJECT_ADMIN_PASSWORD=El0gVvsBv8XZNMCcdtwWKS5r
ENV TRUSTED_PROXY_IPS=127.0.0.1,::1,10.0.0.0/8,100.64.0.0/10

RUN mkdir -p /data && chmod 777 /data
EXPOSE 3000

CMD ["/app/docker-start.sh"]
