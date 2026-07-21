"""
SEC-2 regression tests — the session-cookie Secure flag must be decoupled
from DEBUG so a stray DEBUG=true cannot silently downgrade auth cookies to
plaintext HTTP.

These are pure-function tests over auth_jwt.cookie_secure_enabled(); they do
not require the app or a live server.
"""

import importlib
import os

import pytest


def _reload_auth():
    import auth_jwt
    return importlib.reload(auth_jwt)


@pytest.fixture(autouse=True)
def _clean_env():
    """Snapshot and restore the two env vars this behaviour depends on."""
    saved = {k: os.environ.get(k) for k in ("COOKIE_SECURE", "DEBUG")}
    for k in ("COOKIE_SECURE", "DEBUG"):
        os.environ.pop(k, None)
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_prod_default_is_secure():
    """DEBUG=false and COOKIE_SECURE unset → Secure ON (production default)."""
    os.environ["DEBUG"] = "false"
    assert _reload_auth().cookie_secure_enabled() is True


def test_dev_default_is_insecure():
    """DEBUG=true and COOKIE_SECURE unset → Secure OFF (local dev over HTTP)."""
    os.environ["DEBUG"] = "true"
    assert _reload_auth().cookie_secure_enabled() is False


def test_explicit_true_overrides_debug():
    """COOKIE_SECURE=true forces Secure even when DEBUG=true."""
    os.environ["DEBUG"] = "true"
    os.environ["COOKIE_SECURE"] = "true"
    assert _reload_auth().cookie_secure_enabled() is True


def test_explicit_false_allows_insecure():
    """COOKIE_SECURE=false allows plaintext even when DEBUG=false (LAN workshop)."""
    os.environ["DEBUG"] = "false"
    os.environ["COOKIE_SECURE"] = "false"
    assert _reload_auth().cookie_secure_enabled() is False


@pytest.mark.parametrize("truthy", ["true", "1", "yes", "TRUE", "Yes"])
def test_truthy_aliases(truthy):
    os.environ["COOKIE_SECURE"] = truthy
    assert _reload_auth().cookie_secure_enabled() is True


@pytest.mark.parametrize("falsy", ["false", "0", "no", "FALSE", "No"])
def test_falsy_aliases(falsy):
    os.environ["DEBUG"] = "false"
    os.environ["COOKIE_SECURE"] = falsy
    assert _reload_auth().cookie_secure_enabled() is False


def test_set_session_cookie_honours_flag():
    """set_session_cookie must stamp Secure according to cookie_secure_enabled()."""
    os.environ["DEBUG"] = "false"
    os.environ["COOKIE_SECURE"] = "true"
    auth = _reload_auth()

    from starlette.responses import Response
    resp = Response()
    auth.set_session_cookie(resp, "dummy.jwt.token")
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert "Secure" in set_cookie_header
    assert "HttpOnly" in set_cookie_header
    assert "SameSite=strict" in set_cookie_header.replace(" ", "").replace("samesite", "SameSite")
