"""
Muressons Global Command — FastAPI Application Entry Point

Automatically detects whether PostgreSQL is available.
If not, falls back to an in-memory database for zero-dependency deployment.
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_TITLE, APP_VERSION, DEBUG

# ── Database Backend Selection ─────────────────────────────────
# Set USE_MEMORY_DB=true to force in-memory mode
# Otherwise, we try PostgreSQL and fall back automatically.

_use_memory = os.getenv("USE_MEMORY_DB", "").lower() in ("true", "1", "yes")

if _use_memory:
    print("[MEMORY] In-memory mode (forced via USE_MEMORY_DB)")
    import database_memory as db
else:
    try:
        import asyncpg  # noqa: F401 — just checking availability
        import database as db
        print("[POSTGRES] PostgreSQL mode")
    except Exception:
        print("[MEMORY] PostgreSQL unavailable -- using in-memory database")
        import database_memory as db

# Inject the selected db module into router/admin_router
sys.modules["database"] = db  # type: ignore

from router import router as simulation_router  # noqa: E402
from admin_router import admin_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database lifecycle."""
    await db.get_pool()
    yield
    await db.close_pool()


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
)

# FIX AUDIT-011: CORS — use explicit origins instead of wildcard + credentials.
# Set CORS_ORIGINS env var to a comma-separated list for production.
import os as _os
_cors_origins = _os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
_cors_origins = [o.strip() for o in _cors_origins if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(simulation_router)
app.include_router(admin_router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "database": "memory" if _use_memory or "database_memory" in str(type(db)) else "postgresql",
    }
