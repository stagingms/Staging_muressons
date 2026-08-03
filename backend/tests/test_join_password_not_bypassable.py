"""SEC-2026-08-02 — the join password check must not be skippable from the wire.

THE BUG THIS PINS
    `POST /public/sessions/{id}/join` was declared as

        async def join_session(session_id, req: JoinSessionRequest,
                               _bypass_password: bool = False)

    FastAPI binds a non-path, non-Pydantic scalar with a default as a QUERY
    parameter, and a leading underscore is not filtered. So

        POST /api/simulations/public/sessions/<cohort>/join?_bypass_password=true
        {"player_id": "MUR-004", "password": ""}

    skipped the bcrypt check entirely, leaving only validate_player_id — which
    is membership, not authentication. Player ids are not secret (they are
    printed on handouts, and GET /api/admin/cohort-pulse/{id} returns them
    unauthenticated), so this was a password-free takeover of any student seat.

    A source comment asserted the parameter "cannot come from an HTTP body".
    That was true and irrelevant: it came from the query string.

THE FIX
    The implementation moved to `_join_session_impl`, which has NO route and a
    KEYWORD-ONLY `bypass_password`. The public `join_session` is a thin wrapper
    that always passes False. The bypass is now unreachable from the wire by
    construction, not by convention.

WHY THE TESTS BELOW ARE SHAPED THIS WAY
    test_join_route_has_no_query_parameters is the load-bearing one: it asks
    FASTAPI what it decided the public surface is, rather than reading the
    signature and inferring. Any future scalar added to `join_session` — with
    any name, underscore or not — fails it. That generalises past this one bug.

    The observer path (player_login -> _join_session_impl(bypass_password=True),
    after the team view code has been verified against team_view_password) is
    the ONE legitimate use, and deleting the parameter instead of hiding it
    would break every observer seat. test_impl_still_accepts_the_bypass and the
    existing test_team_seats.py cover that direction.
"""

import inspect
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

import router  # noqa: E402
from router import JoinSessionRequest  # noqa: E402  (defined in router, not models)

_JOIN_PATH = "/api/simulations/public/sessions/{session_id}/join"


def _join_route():
    for r in router.router.routes:
        if getattr(r, "path", None) == _JOIN_PATH and "POST" in getattr(r, "methods", ()):
            return r
    raise AssertionError(f"join route not found; paths = {[getattr(r, 'path', None) for r in router.router.routes][:20]}")


# ── The load-bearing test ────────────────────────────────────────────────────

def test_join_route_has_no_query_parameters():
    """Ask FastAPI what the public surface is, not the signature.

    A scalar parameter with a default becomes a query parameter no matter what
    it is called. This fails for `_bypass_password`, `bypass_password`,
    `bypass`, or anything else someone adds later.
    """
    query_names = [p.name for p in _join_route().dependant.query_params]
    assert query_names == [], (
        f"join_session exposes query parameter(s) {query_names}. Scalar "
        "parameters with defaults are part of the PUBLIC API. If one of them "
        "influences an authorisation decision, it is an auth bypass — move it "
        "to a keyword-only argument of _join_session_impl instead."
    )


def test_join_route_takes_only_the_path_id_and_the_body():
    sig = inspect.signature(router.join_session)
    assert list(sig.parameters) == ["session_id", "req"]


# ── The bypass is not expressible on the public callable ─────────────────────

def test_public_join_rejects_a_bypass_argument():
    body = JoinSessionRequest(player_id="MUR-004", password="")
    with pytest.raises(TypeError):
        inspect.signature(router.join_session).bind("sid", body, bypass_password=True)
    with pytest.raises(TypeError):
        inspect.signature(router.join_session).bind("sid", body, _bypass_password=True)


# ── The one legitimate caller must keep working ──────────────────────────────

def test_impl_still_accepts_the_bypass_as_keyword_only():
    """player_login needs this for observer seats. Keep it reachable in-process
    and unreachable from the wire."""
    sig = inspect.signature(router._join_session_impl)
    p = sig.parameters["bypass_password"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY, (
        "bypass_password must be keyword-only — a positional/default parameter "
        "is what FastAPI would expose if this function were ever given a route."
    )
    assert p.default is False, "the bypass must default to OFF"

    body = JoinSessionRequest(player_id="MUR-004", password="")
    sig.bind("sid", body, bypass_password=True)          # observer path: must bind
    with pytest.raises(TypeError):
        sig.bind("sid", body, True)                      # never positionally


def test_impl_is_not_routed():
    paths = [getattr(r, "endpoint", None) for r in router.router.routes]
    assert router._join_session_impl not in paths, (
        "_join_session_impl must never be given a route — its keyword-only "
        "bypass would become a query parameter again."
    )
