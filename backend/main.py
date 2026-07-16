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


def _assert_secure_cookies_in_prod() -> None:
    """SEC-2: In production (DEBUG=false) the session cookie MUST carry Secure.

    The Secure flag is now resolved by auth_jwt.cookie_secure_enabled()
    (COOKIE_SECURE env, falling back to `not DEBUG`), decoupled from DEBUG so a
    stray DEBUG=true no longer silently downgrades auth cookies to plaintext.
    This guard closes the remaining hole: a prod deployment that explicitly set
    COOKIE_SECURE=false (or left DEBUG=true) would still ship insecure cookies.
    We refuse to boot unless the operator has knowingly opted out for an
    HTTP-only LAN workshop via ALLOW_INSECURE_COOKIES=true.
    """
    if DEBUG:
        return  # local development - plaintext HTTP is expected
    try:
        from auth_jwt import cookie_secure_enabled
    except Exception:
        return  # auth module unavailable -> nothing to assert
    if cookie_secure_enabled():
        return
    allow_insecure = os.getenv("ALLOW_INSECURE_COOKIES", "").lower() in ("true", "1", "yes")
    if allow_insecure:
        print(
            "\n"
            "SEC-2 WARNING - Auth cookies are NOT Secure in PROD. "
            "Session tokens can be sent over plaintext HTTP and sniffed. "
            "Override active: ALLOW_INSECURE_COOKIES=true. "
            "Use only for an intentional HTTP-only LAN workshop."
        )
        return
    print(
        "\n"
        "SEC-2 FATAL - Insecure auth cookies in production. "
        "DEBUG=false but the session cookie Secure flag is OFF. "
        "Serve over HTTPS and set COOKIE_SECURE=true (or unset COOKIE_SECURE "
        "and DEBUG so it defaults to Secure). Or, for an intentional HTTP-only "
        "LAN workshop, set ALLOW_INSECURE_COOKIES=true (cookies are sniffable)."
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

# SEC-2: production fail-fast - auth cookies must be Secure (HTTPS-only) unless
# the operator explicitly opts out for an HTTP-only LAN workshop.
_assert_secure_cookies_in_prod()

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
elif not os.getenv("MASTER_PASSWORD", ""):
    # QA-2026-07-16 #1: there is no committed default any more. Unset ⇒ the
    # god_mode break-glass is disabled — the safe production posture. Local
    # testers who need god_mode set MASTER_PASSWORD in backend/.env.
    print("[SEC-4] MASTER_PASSWORD not set — god_mode break-glass DISABLED (safe default).")

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

# Fix #5: configure the shared coordination store to match the selected backend.
# In Postgres mode it externalizes live-run coordination state (round pacing,
# God-Mode freeze) so it survives restarts AND is shared across workers/replicas
# (the 500-user target — audit §1.1/§1.2). In memory mode it is a no-op and
# durability rides database_memory's JSON snapshot.
try:
    import coordination_store as _coordination_store
    _coord_backend = "postgres" if getattr(db, "__name__", "") == "database" else "memory"
    _coordination_store.configure(_coord_backend, pg_pool_getter=getattr(db, "get_pool", None))
except Exception as _cs_exc:  # pragma: no cover - defensive
    print(f"[coordination] configure skipped: {_cs_exc}")
    _coordination_store = None

# QA-2026-07-16 #10: configure cross-worker WebSocket fan-out (no-op in memory /
# single-worker mode). Wired to the ConnectionManager's local-only delivery sink.
try:
    import ws_fanout as _ws_fanout
    from admin_ws import manager as _ws_manager
    _ws_backend = "postgres" if getattr(db, "__name__", "") == "database" else "memory"
    _ws_fanout.configure(_ws_backend, pg_pool_getter=getattr(db, "get_pool", None),
                         local_deliver=_ws_manager.deliver_local)
except Exception as _wsf_exc:  # pragma: no cover - defensive
    print(f"[ws_fanout] configure skipped: {_wsf_exc}")
    _ws_fanout = None

from router import router as simulation_router  # noqa: E402
from admin_router import admin_router  # noqa: E402
from admin_teleprompter import teleprompter_router  # noqa: E402  ARCH-002
from admin_resources import resources_router  # noqa: E402  ARCH-002
from admin_analytics import analytics_router  # noqa: E402  ARCH-002
from admin_god_controls import god_router  # noqa: E402  audit #17 (extracted sub-router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the database lifecycle."""
    await db.get_pool()

    # Fix #5: prepare the shared coordination store — create its table (PG only),
    # rehydrate this worker's in-process pacing/freeze caches from the shared
    # state, and start the background refresher that keeps workers converged.
    if _coordination_store is not None:
        try:
            await _coordination_store.init_schema()
            await _coordination_store.rehydrate()
            await _coordination_store.start_background_refresh()
        except Exception as _cs_start_exc:
            print(f"[coordination] startup skipped (non-fatal): {_cs_start_exc}")

    # QA-2026-07-16 #10: start the cross-worker WS listener (no-op in memory mode).
    if _ws_fanout is not None:
        try:
            await _ws_fanout.start_listener()
        except Exception as _wsf_start_exc:
            print(f"[ws_fanout] listener start skipped (non-fatal): {_wsf_start_exc}")

    # audit #10: start the idle-session reaper — reaps expired solo sessions and
    # GCs the per-process commit-lock / timestamp / pacing dicts so they don't
    # grow unbounded over a long-running server.
    try:
        import session_reaper as _session_reaper
        await _session_reaper.start_reaper()
    except Exception as _reaper_exc:
        print(f"[reaper] startup skipped (non-fatal): {_reaper_exc}")
        _session_reaper = None

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
    try:
        import session_reaper as _sr
        await _sr.stop_reaper()
    except Exception:
        pass
    if _coordination_store is not None:
        try:
            await _coordination_store.stop_background_refresh()
        except Exception:
            pass
    if _ws_fanout is not None:
        try:
            await _ws_fanout.stop_listener()
        except Exception:
            pass
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

# audit #4: enumerate methods/headers instead of "*". The origin allowlist is the
# real control, but with allow_credentials=True it is good hygiene to only permit
# the verbs and request headers the app actually uses, rather than reflecting
# whatever an allowed origin asks for.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-Player-Id", "Authorization"],
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

# audit #16: structured logging + request/session correlation. Every log line
# emitted while handling a request is tagged with a request_id (echoed back as
# X-Request-Id) and, for /simulations/{id} routes, the session_id — so a live
# incident ("team X is stuck") can be traced across the logs. JSON in prod,
# human-readable in local dev (see logging_config).
import re as _re
import time as _time_mod
from logging_config import (
    configure_logging as _configure_logging,
    new_request_id as _new_request_id,
    set_request_context as _set_request_context,
    reset_request_context as _reset_request_context,
)

_configure_logging()
_access_logger = logging.getLogger("muressons.access")
_SESSION_ID_RE = _re.compile(r"/simulations/([0-9a-fA-F-]{8,})")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Outermost middleware: assign/propagate a request id, derive the session
    id from the path, and emit one structured access-log line per request."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-Id", "").strip() or _new_request_id()
        _match = _SESSION_ID_RE.search(request.url.path)
        _set_request_context(req_id, _match.group(1) if _match else "")
        _start = _time_mod.perf_counter()
        _status = 500
        try:
            response: Response = await call_next(request)
            _status = response.status_code
            response.headers["X-Request-Id"] = req_id
            return response
        finally:
            _dur_ms = round((_time_mod.perf_counter() - _start) * 1000, 1)
            _access_logger.info(
                "%s %s -> %s (%sms)", request.method, request.url.path, _status, _dur_ms
            )
            _reset_request_context()


# Added last → outermost, so the context is set for all inner handling.
app.add_middleware(RequestContextMiddleware)

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
app.include_router(god_router)           # audit #17: Extracted God-Mode controls sub-router


@app.get("/health", tags=["System"])
async def health_check():
    # BUGFIX: the old detection `"database_memory" in str(type(db))` was DEAD —
    # `db` is a module, so `str(type(db))` is "<class 'module'>" and never
    # matches. It reported "memory" ONLY when USE_MEMORY_DB was forced, and
    # crucially MISreported "postgresql" during a silent Postgres-unavailable
    # fallback (main.py imports database_memory but _use_memory stays False) —
    # hiding the exact data-loss risk the player "demo mode" banner exists to
    # warn about. Use the authoritative module-name check, same as lifespan().
    _memory = _use_memory or getattr(db, "__name__", "") == "database_memory"
    # demo_mode is TRUE only when ephemeral storage was chosen deliberately —
    # USE_MEMORY_DB explicitly set, or the documented prod opt-in. An incidental
    # dev fallback (Postgres just unreachable) is memory-backed but NOT "demo
    # mode", so the player banner stays off. This is safe: production can never
    # silently run o