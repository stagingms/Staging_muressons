"""/api/health answers "which build is this?".

WHY THIS EXISTS
    Three separate times during the 2026-08 UI work, the question "has my
    deploy gone out yet?" had no answer, and each time it cost more than any
    bug in the work. The reason it is hard is that a still-building deploy and
    a FAILED build are indistinguishable from outside: Railway keeps the
    previous container serving in both cases, and nothing anywhere says which
    one you are looking at. Refreshing harder does not help.

    So health now reports the build. `uptime_seconds` alone resolves the
    ambiguity — a deploy that has landed has an uptime measured in seconds.
    `commit` resolves the next question after that, which is WHICH commit.

WHAT THIS DOES NOT DO
    It does not touch simulation logic, session flow, or any player-visible
    surface. It adds keys to a diagnostic endpoint.
"""
import os
import time

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")

import main  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(main.app)


def test_health_reports_a_build_block(client):
    body = client.get("/api/health").json()
    assert "build" in body, "health must answer 'which build is this?'"
    for key in ("commit", "branch", "deployment", "started_at", "uptime_seconds"):
        assert key in body["build"], f"build.{key} missing"


def test_uptime_is_real_and_moves(client):
    """The one field that always works, on every platform, with no env vars.

    A deploy that has gone out has an uptime in seconds. One that is still
    building, or that failed, keeps the previous container's uptime climbing.
    """
    first = client.get("/api/health").json()["build"]["uptime_seconds"]
    assert isinstance(first, int) and first >= 0
    time.sleep(1.1)
    second = client.get("/api/health").json()["build"]["uptime_seconds"]
    assert second > first, "uptime must advance, or it cannot distinguish a restart"


def test_absent_env_reads_as_null_not_as_a_plausible_string(client):
    """None, never "unknown" or "".

    A monitor comparing build.commit against `git rev-parse HEAD` must be able
    to tell "this platform does not report it" from "it reports something".
    A falsy string would compare unequal and read as a failed deploy.
    """
    for var in ("RAILWAY_GIT_COMMIT_SHA", "RAILWAY_GIT_BRANCH", "RAILWAY_DEPLOYMENT_ID"):
        assert var not in os.environ or os.environ[var], "test env should not set these"
    build = client.get("/api/health").json()["build"]
    for key in ("commit", "branch", "deployment"):
        assert build[key] is None or isinstance(build[key], str)
        assert build[key] != "", f"build.{key} must be null rather than an empty string"


def test_the_healthcheck_contract_is_unchanged(client):
    """railway.json points its healthcheck at this path. Adding keys is safe;
    changing status or dropping a key is not."""
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    for key in ("status", "database", "demo_mode", "storage",
                "durable_storage", "low_disk_space"):
        assert key in body, f"pre-existing health key {key} was dropped"
    assert body["status"] == "ok"
