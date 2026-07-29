"""Every session-scoped MUTATING endpoint must bind the caller to the session.

SEC-AUDIT-2026-07-29. A route audit found 17 mutating handlers under
/api/simulations/{session_id}/... declared as:

    async def board_vote(session_id: str, body: dict):

with no `request` parameter. Without `request` there is nothing to read a
cookie or X-Player-Id from, so NO ownership check could run — not because
someone removed it, but because the handler could not physically perform one.

This was not theoretical. Proven end to end against a victim session:

    anonymous POST /api/simulations/{victim}/board-vote  ->  200
    victim's group_reputation and corporate_treasury both changed.

Classroom impact: session ids are exposed constantly — projected on a screen,
in a browser URL bar, in a screen-share, in a support screenshot. Anyone
holding one could vote in another team's boardroom, run their supply-chain
audits, activate regulatory instruments, or submit their CEO interview.

The failure mode this file guards is SILENT: a new endpoint written in the
same shape compiles, passes its own unit tests, and is wide open. Only a check
on the SIGNATURE catches it, which is what this does.

`join_session` is the deliberate exception — it authenticates with player_id +
password, which is how a player gets a session in the first place.
"""
import pathlib
import re

import pytest

ROUTER = pathlib.Path(__file__).resolve().parents[1] / "router.py"
SRC = ROUTER.read_text(encoding="utf-8")
LINES = SRC.split("\n")

# Authenticates by credential, not by prior session ownership.
EXEMPT = {"join_session"}

MUTATING = ("post", "patch", "put", "delete")


def _session_scoped_mutating_handlers():
    """Yield (name, path, lineno, signature) for mutating routes whose path
    carries {session_id}."""
    out = []
    for i, line in enumerate(LINES):
        m = re.match(r"@router\.(%s)\(" % "|".join(MUTATING), line)
        if not m:
            continue
        path = ""
        for p in range(i, min(i + 5, len(LINES))):
            pm = re.search(r'"(/[^"]*)"', LINES[p])
            if pm:
                path = pm.group(1)
                break
        if "{session_id}" not in path:
            continue
        for j in range(i, min(i + 16, len(LINES))):
            if LINES[j].lstrip().startswith("async def "):
                k = j
                sig = []
                while k < len(LINES) and not LINES[k].rstrip().endswith(":"):
                    sig.append(LINES[k])
                    k += 1
                sig.append(LINES[k] if k < len(LINES) else "")
                joined = " ".join(s.strip() for s in sig)
                name = re.search(r"async def (\w+)", joined).group(1)
                out.append((name, path, j + 1, joined))
                break
    return out


HANDLERS = _session_scoped_mutating_handlers()


def test_the_scan_actually_finds_handlers():
    """A regex that silently matches nothing would make every test below
    vacuously pass — the exact way a tripwire rots."""
    assert len(HANDLERS) >= 15, f"expected the audit's ~17 handlers, found {len(HANDLERS)}"


@pytest.mark.parametrize(
    "name,path,lineno,sig",
    [h for h in HANDLERS if h[0] not in EXEMPT],
    ids=[h[0] for h in HANDLERS if h[0] not in EXEMPT],
)
def test_handler_can_identify_its_caller(name, path, lineno, sig):
    """It must accept `request`, or it cannot check anything at all."""
    assert "request: Request" in sig, (
        f"{name} ({path}, router.py:{lineno}) takes no `request`, so no cookie "
        "and no X-Player-Id can be read: this endpoint is unauthenticated by "
        "construction. Add `request: Request` and call "
        "_assert_player_owns_session(request, session_id)."
    )


@pytest.mark.parametrize(
    "name,path,lineno,sig",
    [h for h in HANDLERS if h[0] not in EXEMPT],
    ids=[h[0] for h in HANDLERS if h[0] not in EXEMPT],
)
def test_handler_actually_asserts_ownership(name, path, lineno, sig):
    """Accepting `request` is not enough — the check must be called."""
    body = "\n".join(LINES[lineno - 1: lineno + 60])
    guarded = (
        "_assert_player_owns_session" in body
        or "_assert_session_ownership" in body
        or "require_facilitator" in sig
        or "require_sim_manager" in sig
        or "require_super_admin" in sig
    )
    assert guarded, (
        f"{name} ({path}, router.py:{lineno}) never binds the caller to the "
        "session. Any holder of a session id can invoke it."
    )


def test_exempt_list_stays_small_and_justified():
    """Exemptions are how this rots quietly. Each one needs a reason in the
    module docstring; keep the list short enough to audit by eye."""
    assert len(EXEMPT) <= 2, "too many exemptions — justify each in the docstring"
    for name in EXEMPT:
        assert name in SRC, f"exempt handler {name} no longer exists — drop it"
