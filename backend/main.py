"""
Muressons Global Corporation — FastAPI Application Entry Point

Automatically detects whether PostgreSQL is available.
If not, falls back to an in-memory database for zero-dependency deployment.
"""

import os
import sys

# Force UTF-8 output on Windows to avoid UnicodeEncodeError with emoji/special chars
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
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

# ── SEC-2: Production durability guard ─────────────────────────
# The in-memory store loses ALL live sessions on restart/redeploy/crash.
# That is acceptable for local dev (DEBUG=true) but catastrophic for a
# graded, multi-hour workshop. In production (DEBUG=false) we refuse to
# boot on the in-memory store unless the operator explicitly opts in via
# ALLOW_MEMORY_DB_IN_PROD=true (documented escape hatch for single-laptop
# offline workshops).
_allow_memory_in_prod = os.getenv("ALLOW_MEMORY_DB_IN_PROD", "").lower() in ("true", "1", "yes")


def _refuse_memory_db_in_prod() -> None:
    """Hard-fail at startup if memory DB would silently be used in production."""
    if DEBUG or _allow_memory_in_prod:
        if not DEBUG and _allow_memory_in_prod:
            print(
                "\n"
                "╔══════════════════════════════════════════════════════════╗\n"
                "║  SEC-2 WARNING — In-memory DB running in PRODUCTION.       ║\n"
                "║  ALL sessions, decisions and scores are LOST on restart.  ║\n"
                "║  Override active: ALLOW_MEMORY_DB_IN_PROD=true             ║\n"
                "║  Use only for single-laptop / offline workshops.          ║\n"
                "╚══════════════════════════════════════════════════════════╝"
            )
        return
    # Production + memory DB + no override → refuse to start.
    print(
        "\n"
        "╔══════════════════════════════════════════════════════════╗\n"
        "║  SEC-2 FATAL — Refusing to start on the in-memory store    ║\n"
        "║  in production (DEBUG=false).                              ║\n"
        "║  • Configure PostgreSQL: set USE_MEMORY_DB=false and a     ║\n"
        "║    valid DATABASE_URL.                                     ║\n"
        "║  • Or, for an intentional single-laptop offline workshop,  ║\n"
        "║    set ALLOW_MEMORY_DB_IN_PROD=true (data is NOT durable). ║\n"
        "╚══════════════════════════════════════════════════════════╝"
    )
    sys.exit(1)


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

# SEC-6: production fail-fast — a prod boot must have a configured JWT secret.
# Without it auth_jwt generates an ephemeral per-process secret, silently
# invalidating every session on each restart. Fail loudly instead.
if not DEBUG and not os.getenv("JWT_SECRET", ""):
    print(
        "\n"
        "╔══════════════════════════════════════════════════════════╗\n"
        "║  SEC-6 FATAL — JWT_SECRET is not set in production.        ║\n"
        "║  Generate one and set it before starting:                 ║\n"
        "║     openssl rand -hex 32                                  ║\n"
        "╚══════════════════════════════════════════════════════════╝"
    )
    sys.exit(1)

# SEC-4: warn loudly if the MASTER_PASSWORD break-glass bypass is armed in prod.
if not DEBUG and os.getenv("MASTER_PASSWORD", ""):
    print(
        "\n"
        "╔══════════════════════════════════════════════════════════╗\n"
        "║  SEC-4 WARNING — MASTER_PASSWORD bypass is ARMED in       ║\n"
        "║  production. It overrides every player/facilitator login. ║\n"
        "║  Enable only for a recovery window, then unset it.        ║\n"
        "║  All uses are recorded in db/admin_audit.jsonl.          ║\n"
        "╚══════════════════════════════════════════════════════════╝"
    )

if _use_memory:
    _refuse_memory_db_in_prod()  # SEC-2: hard-fail in prod unless overridden
    print("[MEMORY] In-memory mode (forced via USE_MEMORY_DB)")
    import database_memory as db
elif _is_postgres_available():
    import database as db
    print("[POSTGRES] PostgreSQL mode")
else:
    # SEC-2: a silent fallback to memory in production is the most dangerous
    # path (operator believes Postgres is in use). Guard it the same way.
    _refuse_memory_db_in_prod()
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

    # REC-1a: Startup banner warning for memory mode
    _is_memory_db = _use_memory or getattr(db, "__name__", "") == "database_memory"
    if _is_memory_db:
        print("\n" + "=" * 70)
        print("  [!] RUNNING IN MEMORY MODE")
        print("  Data will be lost on server restart.")
        print("  For classroom sessions, set USE_MEMORY_DB=false")
        print("  and configure DATABASE_URL for PostgreSQL.")
        print("=" * 70 + "\n")

    # Sync and seed missing cohort sessions for facilitators (e.g. if initial seeding failed)
    try:
        from admin_shared import _facilitator_registry
        from datetime import datetime, timezone
        sessions = await db.fetch_all_sessions()
        for fac in _facilitator_registry:
            if fac.get("deleted_at"):
                continue
            fac_id = fac.get("facilitator_id")
            if not fac_id or fac_id in ("god_mode", "FAC-EMERGENCY"):
                continue
            # Count top-level sessions for this facilitator
            fac_sessions = [s for s in sessions if s.get("facilitator_id") == fac_id]
            if not fac_sessions:
                print(f"[startup] Seeding missing Alpha Cohort for facilitator {fac_id}")
                try:
                    await db.create_session(
                        cohort_name=f"{fac.get('name', 'Facilitator')}'s Alpha Cohort ({fac_id})",
                        facilitator_id=fac_id,
                        decision_paradigm=fac.get("decision_paradigm", "legacy_abc") or "legacy_abc",
                        experience_level="standard",
                        created_by="system_startup",
                        created_when=datetime.now(timezone.utc).date().isoformat()
                    )
                except Exception as ex:
                    print(f"[startup] Failed to seed cohort for {fac_id}: {ex}")
    except Exception as e:
        print(f"[startup] Failed to sync/seed missing cohorts: {e}")

    yield
    await db.close_pool()


# LOW-004: Decouple Swagger / ReDoc from DEBUG so production deployments can
# keep verbose logging (DEBUG=true) without accidentally exposing the API
# explorer.  Set DOCS_ENABLED=true explicitly when you need the docs UI.
# By default, docs are only available when DEBUG=true (local / staging).
_docs_enabled = (
    os.getenv("DOCS_ENABLED", "").lower() in ("true", "1", "yes")
    or DEBUG
)
_docs_url    = "/docs"         if _docs_enabled else None
_redoc_url   = "/redoc"        if _docs_enabled else None
_openapi_url = "/openapi.json" if _docs_enabled else None

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
