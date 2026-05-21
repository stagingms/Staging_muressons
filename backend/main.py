"""
Muressons Global Corporation — FastAPI Application Entry Point

Automatically detects whether PostgreSQL is available.
If not, falls back to an in-memory database for zero-dependency deployment.
"""

import os
import sys
from contextlib import asynccontextmanager

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

import socket
from urllib.parse import urlparse
from config import APP_TITLE, APP_VERSION, DEBUG, DATABASE_URL

# ── Database Backend Selection ─────────────────────────────────
# Set USE_MEMORY_DB=true to force in-memory mode
# Otherwise, we try PostgreSQL and fall back automatically.

_use_memory = os.getenv("USE_MEMORY_DB", "").lower() in ("true", "1", "yes")

def _is_postgres_available() -> bool:
    try:
        import asyncpg  # noqa: F401
        parsed = urlparse(DATABASE_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except Exception:
        return False

if _use_memory:
    print("[MEMORY] In-memory mode (forced via USE_MEMORY_DB)")
    import database_memory as db
elif _is_postgres_available():
    import database as db
    print("[POSTGRES] PostgreSQL mode")
else:
    print("[MEMORY] PostgreSQL unavailable -- using in-memory database")
    import database_memory as db

# Inject the selected db module into router/admin_router
sys.modules["database"] = db  # type: ignore

from router import router as simulation_router  # noqa: E402
from admin_router import admin_router  # noqa: E402
from admin_teleprompter import teleprompter_router  # noqa: E402  ARCH-002
from admin_resources import resources_router  # noqa: E402  ARCH-002
from admin_analytics import analytics_router  # noqa: E402  ARCH-002


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database lifecycle."""
    await db.get_pool()
    yield
    await db.close_pool()


# LOW-002: Hide interactive API docs in production to reduce attack surface.
_docs_url    = "/docs"    if DEBUG else None
_redoc_url   = "/redoc"   if DEBUG else None
_openapi_url = "/openapi.json" if DEBUG else None

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

# FIX AUDIT-011: CORS — use explicit origins instead of wildcard + credentials.
# Set CORS_ORIGINS env var to a comma-separated list for production.
# Railway auto-injects RAILWAY_PUBLIC_DOMAIN when a public domain is assigned.
import os as _os
_cors_origins = _os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
_cors_origins = [o.strip() for o in _cors_origins if o.strip()]

# Auto-detect Railway public domain
_railway_domain = _os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
if _railway_domain:
    _cors_origins.append(f"https://{_railway_domain}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HIGH-010: HTTP security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Limit referrer data leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Prevent browsers from exposing permissions unnecessarily
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        # Content-Security-Policy: tighten for API responses (no HTML rendered by backend)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        # HSTS: force HTTPS for 1 year in production
        if not DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Remove server banner
        if "server" in response.headers:
            del response.headers["server"]
        return response

app.add_middleware(SecurityHeadersMiddleware)

# LOW-009: Generic error handler — never expose internal tracebacks in production
@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception):
    if DEBUG:
        # In debug mode, let FastAPI's default handler show the traceback
        raise exc
    logging.exception("Unhandled server error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again."},
    )

# Mount routers
app.include_router(simulation_router)
app.include_router(admin_router)
app.include_router(teleprompter_router)  # ARCH-002: Extracted sub-router
app.include_router(resources_router)     # ARCH-002: Extracted sub-router
app.include_router(analytics_router)     # ARCH-002: Extracted sub-router


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "database": "memory" if _use_memory or "database_memory" in str(type(db)) else "postgresql",
    }
