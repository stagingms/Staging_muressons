"""
rate_limit.py — IP rate limiting (audit #17, extracted verbatim from admin_router).

This is a behaviour-preserving extraction: the sliding-window counter, the
trusted-proxy IP resolution, and the restart-surviving ban persistence were moved
here unchanged from admin_router.py to shrink that ~10k-line god-file. admin_router
re-exports `_check_rate_limit` (and the rest) so every existing import — including
`from admin_router import _check_rate_limit` in router.py — keeps working.
"""

from __future__ import annotations

import collections
import json
import os
import time

from fastapi import HTTPException, Request

# ── HIGH-009 / SECURITY-HIGH-003: Rate limiter with trusted-proxy allowlist ──
# Sliding-window counter: at most _RATE_LIMIT_MAX attempts per IP per window.
_RATE_LIMIT_MAX = 10          # max attempts  (login / brute-force paths)
_RATE_LIMIT_WINDOW = 60       # seconds

# Admin action paths (already authenticated) use a much higher limit so
# legitimate super-admin clicks don't trigger the brute-force guard.
_ADMIN_ACTION_RATE_MAX = 120  # 120 actions per window is plenty for real use
_ADMIN_ACTION_PREFIXES = frozenset({"fac_reset_pw", "role_change"})

# QA-2026-07-16 #7: prefixes that get a GENEROUS per-IP ceiling because a whole
# classroom of players typically shares ONE public IP (venue/campus NAT). The
# tight 10/min brute-force cap would lock the room out at "everyone log in now".
# Per-ACCOUNT brute-force protection is applied separately (identity= below).
_HIGH_IP_LIMIT_PREFIXES = frozenset({"player_login"})
_HIGH_IP_LIMIT_MAX = 300      # per IP per window — fits a large NATed cohort

# deque of timestamps per IP key (monotonic — in-process only)
_rate_buckets: dict[str, collections.deque] = {}

# LOW-002: Persist ban state across server restarts so a restart cannot be used
# to bypass an active rate-limit ban.  The file stores wall-clock UNIX expiry
# timestamps keyed by "<prefix>:<ip>" so entries are portable across restarts.
# QA-2026-07-16 #3: routed through the durable data dir (MURESSONS_DATA_DIR)
# so bans survive a Railway REDEPLOY, not just a same-container restart.
from runtime_paths import data_file as _data_file
_RATE_BAN_FILE = str(_data_file("rate_bans.json"))
# { "login:1.2.3.4": 1735000000.0, ... }  — wall-clock UNIX expiry seconds
_persistent_bans: dict[str, float] = {}


def _load_persistent_bans() -> None:
    """LOW-002: Restore IP ban state from disk; discard already-expired entries."""
    global _persistent_bans
    try:
        if os.path.exists(_RATE_BAN_FILE):
            with open(_RATE_BAN_FILE, "r", encoding="utf-8") as _f:
                raw: dict = json.load(_f)
            now_wall = time.time()
            _persistent_bans = {k: v for k, v in raw.items() if isinstance(v, (int, float)) and v > now_wall}
    except Exception:
        _persistent_bans = {}


def _save_persistent_bans() -> None:
    """LOW-002: Flush current ban state to disk atomically."""
    try:
        os.makedirs(os.path.dirname(_RATE_BAN_FILE), exist_ok=True)
        _tmp = _RATE_BAN_FILE + ".tmp"
        with open(_tmp, "w", encoding="utf-8") as _f:
            json.dump(_persistent_bans, _f)
        os.replace(_tmp, _RATE_BAN_FILE)
    except Exception as exc:
        # Non-fatal — in-memory bans still apply for this process lifetime — but
        # recorded (F-36) so a full volume is visible in /api/health.
        try:
            from admin_shared import record_persistence_failure
            record_persistence_failure("rate_bans", exc, _RATE_BAN_FILE)
        except Exception:  # pragma: no cover
            pass


_load_persistent_bans()
# Clear any stale admin-action bans that were incorrectly persisted with the
# tight login limit — they will not be recreated unless the higher admin limit
# is also exceeded.
for _ban_key in list(_persistent_bans.keys()):
    if any(_ban_key.startswith(p + ":") for p in _ADMIN_ACTION_PREFIXES):
        del _persistent_bans[_ban_key]
_save_persistent_bans()

# SECURITY-HIGH-003: Only trust X-Forwarded-For / X-Real-IP when the direct
# TCP connection originates from a known proxy / load-balancer.  Accepting
# these headers from arbitrary clients allows an attacker to spoof a new IP
# on every request and bypass the rate limit entirely.
#
# Set TRUSTED_PROXY_IPS to a comma-separated list of your proxy IPs or CIDRs.
# Defaults to localhost only (safe for direct-access deployments).
#
# BUG-2026-07-19: this list DOCUMENTED CIDR support but compared by exact
# string (`direct_ip in frozenset`), so a range like 10.0.0.0/8 matched
# nothing. On a PaaS the app sits behind an edge proxy whose internal address
# is not knowable in advance, so operators reach for a range — and got silent
# no-op trust. X-Forwarded-For was then discarded and EVERY request resolved to
# the same proxy address, collapsing a whole cohort into one rate-limit bucket:
# one student mistyping their password could 429 the entire room. Entries are
# now parsed once into exact addresses plus real networks.
#
# Railway / Render / Fly.io: add the platform's edge range, e.g.
#   TRUSTED_PROXY_IPS=127.0.0.1,::1,10.0.0.0/8,100.64.0.0/10
# Trusting a PRIVATE range is safe here because a client cannot choose the
# source address of the TCP connection the platform makes to your container.
# Never add a public range you do not control — that would let anyone on it
# spoof X-Forwarded-For and bypass rate limiting entirely.
_TRUSTED_PROXY_RAW: tuple[str, ...] = tuple(
    ip.strip()
    for ip in os.getenv("TRUSTED_PROXY_IPS", "127.0.0.1,::1").split(",")
    if ip.strip()
)


def _parse_trusted(entries):
    """Split raw entries into (exact-address set, network list).

    Unparseable entries are kept as exact strings rather than dropped: the old
    behaviour was exact-string matching, and silently discarding a malformed
    entry would be a security-relevant surprise in the other direction.
    """
    import ipaddress
    exact, nets = set(), []
    for raw in entries:
        try:
            if "/" in raw:
                nets.append(ipaddress.ip_network(raw, strict=False))
            else:
                exact.add(str(ipaddress.ip_address(raw)))
        except ValueError:
            exact.add(raw)
    return frozenset(exact), tuple(nets)


_TRUSTED_EXACT, _TRUSTED_NETS = _parse_trusted(_TRUSTED_PROXY_RAW)

# Kept for backwards compatibility: existing code and tests import this name.
_TRUSTED_PROXY_IPS: frozenset[str] = _TRUSTED_EXACT


def _is_trusted_proxy(ip: str) -> bool:
    if ip in _TRUSTED_EXACT:
        return True
    if not _TRUSTED_NETS:
        return False
    try:
        import ipaddress
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _TRUSTED_NETS)


def _resolve_client_ip(request: Request) -> str:
    """Return the real client IP, honouring proxy headers only from trusted sources."""
    direct_ip = request.client.host if request.client else "unknown"
    if _is_trusted_proxy(direct_ip):
        # Trust X-Forwarded-For only when the direct connection is a known proxy
        xff = request.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()
        xri = request.headers.get("X-Real-IP", "")
        if xri:
            return xri.strip()
    # Untrusted direct connection — use the socket IP, ignore spoofable headers
    return direct_ip


def _check_rate_limit(request: Request, key_prefix: str = "login", identity: str = None) -> None:
    """Raise HTTP 429 if the caller exceeds the rate limit for this prefix.

    LOW-002: Bans triggered in this process are written to disk so they survive
    server restarts.  On each call we first check the persisted ban dict (using
    wall-clock time), then fall through to the in-memory sliding window.

    QA-2026-07-16 #7: when ``identity`` is supplied (e.g. a player_id) the bucket
    is keyed by that identity instead of the source IP, so brute-force protection
    is scoped to the individual account being targeted rather than shared across
    every player behind one NAT. Callers typically pair a per-identity check
    (tight cap) with a per-IP check under a HIGH_IP ceiling.
    """
    ip = _resolve_client_ip(request)
    subject = identity.strip().upper() if identity else ip
    key = f"{key_prefix}:{subject}"

    # Resolve the effective cap for this bucket.
    if identity is not None:
        # Per-account brute-force guard — tight cap on one player_id.
        effective_max = _RATE_LIMIT_MAX
    elif key_prefix in _ADMIN_ACTION_PREFIXES:
        effective_max = _ADMIN_ACTION_RATE_MAX
    elif key_prefix in _HIGH_IP_LIMIT_PREFIXES:
        # Per-IP ceiling generous enough for a whole NATed classroom.
        effective_max = _HIGH_IP_LIMIT_MAX
    else:
        effective_max = _RATE_LIMIT_MAX

    # LOW-002: Check persisted ban (wall-clock, survives restart)
    now_wall = time.time()
    if key in _persistent_bans:
        ban_expiry = _persistent_bans[key]
        if ban_expiry > now_wall:
            remaining = max(1, int(ban_expiry - now_wall))
            raise HTTPException(
                status_code=429,
                detail=f"Too many attempts. Please wait {remaining} seconds.",
            )
        # Ban has expired — remove stale entry
        del _persistent_bans[key]

    # In-process sliding-window check (monotonic timestamps)
    now = time.monotonic()
    if key not in _rate_buckets:
        _rate_buckets[key] = collections.deque()
    bucket = _rate_buckets[key]
    # Evict timestamps outside the sliding window
    while bucket and bucket[0] < now - _RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= effective_max:
        # LOW-002: Persist this ban so a restart doesn't reset it
        _persistent_bans[key] = now_wall + _RATE_LIMIT_WINDOW
        _save_persistent_bans()
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Please wait {_RATE_LIMIT_WINDOW} seconds.",
        )
    bucket.append(now)
    # L-4 fix: Periodic cleanup of stale bucket keys to prevent unbounded dict growth.
    # The previous `if not bucket` check was dead code (bucket always non-empty after append).
    # Now we sweep every ~100 calls to prune empty deques from expired sessions.
    if len(_rate_buckets) > 50 and hash(key) % 100 == 0:
        stale_keys = [k for k, v in _rate_buckets.items() if not v]
        for k in stale_keys:
            del _rate_buckets[k]
