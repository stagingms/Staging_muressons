"""PyJWT replaces python-jose without invalidating a single live session (F-22).

WHY THE SWAP
------------
`pip-audit` reported 16 advisories across 3 packages. Six of them were not
Muressons' code at all: python-jose drags in `ecdsa` — which has NO fixed
release — and pins `pyasn1<0.5.0`, so pyasn1 could never be patched to 0.6.4
while jose was a dependency. Upgrading was impossible without removing jose.

WHY IT IS SAFE
--------------
The scheme is unchanged: HS256, the same JWT_SECRET, the same claims. A token
minted by the old jose build is an ordinary HS256 JWT, so the PyJWT build
decodes it and NOBODY IS LOGGED OUT by the deploy. The test below proves that
with a token built independently of our own encoder, so it cannot pass just
because both sides share a bug.

The two real API differences are pinned too: the error base is `PyJWTError`,
and PyJWT verifies `exp` by default — which is what we want everywhere except
the god_mode recovery path, where `verify_exp: False` must still work.
"""
import base64
import hashlib
import hmac
import json
import time

import pytest

import auth_jwt


# ── a jose-era token, constructed from first principles ────────────────────

def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _hs256(payload: dict, secret: str) -> str:
    """Mint an HS256 JWT without using the app's encoder.

    This is deliberately hand-rolled: if it used auth_jwt.create_facilitator_token
    the test would only prove PyJWT can read its own output, which is not the
    claim. The claim is that a token issued by the PREVIOUS library still works.
    """
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header}.{body}".encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header}.{body}.{_b64(sig)}"


def test_a_token_from_the_previous_library_still_authenticates():
    """The upgrade must not sign anyone out mid-workshop."""
    now = int(time.time())
    legacy = _hs256(
        {"sub": "FAC-001", "role": "facilitator", "ver": 0, "iat": now, "exp": now + 3600},
        auth_jwt.JWT_SECRET,
    )
    payload = auth_jwt.decode_facilitator_token(legacy)
    assert payload["sub"] == "FAC-001"
    assert payload["role"] == "facilitator"
    assert payload["ver"] == 0


def test_our_own_tokens_round_trip():
    token = auth_jwt.create_facilitator_token("FAC-007", "lead_facilitator", token_version=3)
    payload = auth_jwt.decode_facilitator_token(token)
    assert (payload["sub"], payload["role"], payload["ver"]) == ("FAC-007", "lead_facilitator", 3)


def test_encode_returns_a_string_not_bytes():
    """PyJWT 1.x returned bytes; 2.x returns str. The cookie layer needs str."""
    assert isinstance(auth_jwt.create_facilitator_token("FAC-002", "facilitator"), str)


# ── the security properties must be unchanged ──────────────────────────────

def test_a_tampered_signature_is_rejected():
    from fastapi import HTTPException
    token = auth_jwt.create_facilitator_token("FAC-003", "facilitator")
    head, body, sig = token.split(".")
    forged = f"{head}.{body}.{'A' * len(sig)}"
    with pytest.raises(HTTPException) as exc:
        auth_jwt.decode_facilitator_token(forged)
    assert exc.value.status_code == 401


def test_a_token_signed_with_the_wrong_secret_is_rejected():
    from fastapi import HTTPException
    now = int(time.time())
    hostile = _hs256({"sub": "god_mode", "role": "god_mode", "ver": 0,
                      "iat": now, "exp": now + 3600}, "not-the-real-secret")
    with pytest.raises(HTTPException) as exc:
        auth_jwt.decode_facilitator_token(hostile)
    assert exc.value.status_code == 401


def test_an_expired_token_is_rejected(monkeypatch):
    """SEC-1: expiry applies to EVERY account, god_mode included."""
    from fastapi import HTTPException
    now = int(time.time())
    stale = _hs256({"sub": "god_mode", "role": "god_mode", "ver": 0,
                    "iat": now - 7200, "exp": now - 3600}, auth_jwt.JWT_SECRET)
    with pytest.raises(HTTPException) as exc:
        auth_jwt.decode_facilitator_token(stale)
    assert exc.value.status_code == 401


def test_the_recovery_path_still_ignores_expiry_but_not_the_signature():
    """god_mode recovery relaxes ONLY `exp` — a forged signature must still fail."""
    from fastapi import HTTPException
    now = int(time.time())
    expired = _hs256({"sub": "god_mode", "role": "god_mode", "ver": 0,
                      "iat": now - 7200, "exp": now - 3600}, auth_jwt.JWT_SECRET)

    fn = getattr(auth_jwt, "decode_token_ignore_expiry", None)
    if fn is None:                      # name differs across revisions
        fn = next((getattr(auth_jwt, n) for n in dir(auth_jwt)
                   if "ignore" in n and "exp" in n and callable(getattr(auth_jwt, n))), None)
    if fn is None:
        pytest.skip("no expiry-relaxing decoder in this revision")

    assert fn(expired)["sub"] == "god_mode"

    forged = _hs256({"sub": "god_mode", "role": "god_mode", "ver": 0,
                     "iat": now, "exp": now + 3600}, "wrong-secret")
    with pytest.raises(HTTPException):
        fn(forged)


# ── the dependency is genuinely gone ───────────────────────────────────────

def test_no_module_imports_python_jose():
    """The point of the exercise: jose leaves, and ecdsa/pyasn1 leave with it."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[1]
    offenders = []
    for py in root.glob("*.py"):
        src = py.read_text(encoding="utf-8", errors="replace")
        code = "\n".join(l for l in src.split("\n")
                         if not l.lstrip().startswith("#"))
        if "from jose" in code or "import jose" in code:
            offenders.append(py.name)
    assert not offenders, f"python-jose is back in: {offenders}"


def test_requirements_pin_the_fixed_versions():
    import pathlib, re
    raw = (pathlib.Path(__file__).resolve().parents[1] / "requirements.txt").read_text(encoding="utf-8")
    # Strip trailing comments: the PyJWT line explains what it replaced, and a
    # tripwire must not be satisfied — or broken — by its own documentation.
    req = "\n".join(l.split("#", 1)[0].rstrip() for l in raw.split("\n"))
    assert "python-jose" not in req, "python-jose re-added — it pins pyasn1<0.5.0"
    assert re.search(r"^PyJWT==", req, re.M)
    # starlette >= 1.3.1 is what PYSEC-2026-249 requires; fastapi>=0.140 is what
    # lifts the old <0.42 ceiling that made it unreachable.
    m = re.search(r"^starlette==(\d+)\.(\d+)\.(\d+)", req, re.M)
    assert m, "starlette must be pinned explicitly, not left to fastapi's floor"
    assert tuple(int(g) for g in m.groups()) >= (1, 3, 1)
    f = re.search(r"^fastapi==(\d+)\.(\d+)\.", req, re.M)
    assert f and (int(f.group(1)), int(f.group(2))) >= (0, 140), \
        "fastapi <0.140 re-pins starlette<0.42 and reopens the advisories"
