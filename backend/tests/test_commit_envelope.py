"""4.8 — a committed round records what was actually submitted.

WHAT WAS WRONG
    decision_audit_log has always had a `metadata` JSONB column and NOTHING
    ever wrote to it. Eight scalar fields survived a commit; everything else a
    team submitted was discarded the moment the request object went out of
    scope:

        pillar_decisions       the {energy, operations, supply_chain,
                               offsetting} split — an ENGINE INPUT
        investment_ratio       as actually used (recomputed server-side by
                               TECH-2/COR-1, so the value the client sent is
                               not the value that scored)
        dividends_paid         moves the treasury
        emergency_credit_used  takes a loan at +2%
        force_override_cfo     overrides a CFO refusal
        engagement_action      the F5 dialogic action
        player_id              WHO decided — Postgres dropped it while the
                               memory backend kept it, a silent parity gap

    Every one changes the numbers. So a round could not be reconstructed from
    its own audit trail: you could see a team chose option_b and spent $4M, but
    not how they split it, whether they took the loan, or whether a refusal was
    overridden. An audit log that looks complete and is not — the same class of
    defect as R10-2.

WHY FOUR WRITE SITES MATTER
    Rounds 1-9 persist through insert_next_round; round 10 goes through
    log_decisions. Patching one and not the other is exactly how R10-2 happened
    — the graded finale silently behaving differently from every other round.
    test_all_four_write_sites_persist_metadata pins all of them.
"""

from __future__ import annotations

import asyncio
import re
import sys
import uuid
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))


def _unique(name: str) -> str:
    return f"{name}-{uuid.uuid4().hex[:8]}"


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            import database as _db
            if getattr(_db, "_pool", None) is not None:
                loop.run_until_complete(_db.close_pool())
        except Exception:
            pass
        loop.close()


# ── 1. Every write site persists it ────────────────────────────────────────

def test_all_four_write_sites_persist_metadata():
    """R10-2 was one unpatched write site. This makes that shape of mistake
    fail loudly instead of hiding until a finale is graded."""
    pg = (_BACKEND_DIR / "database.py").read_text(encoding="utf-8")
    inserts = re.findall(r"INSERT INTO decision_audit_log\s*\(([^)]*)\)", pg)
    assert len(inserts) == 2, f"expected 2 Postgres write sites, found {len(inserts)}"
    for cols in inserts:
        assert "metadata" in cols, f"a write site drops the envelope: {cols!r}"

    mem = (_BACKEND_DIR / "database_memory.py").read_text(encoding="utf-8")
    appends = mem.count("_decision_log.append({")
    assert appends == 2, f"expected 2 memory write sites, found {appends}"
    # Count only inside the append blocks — the READ path legitimately carries
    # the same key, so a naive whole-file count would drift as readers change.
    write_blocks = [mem[i:i + 900] for i in
                    [m.start() for m in re.finditer(r"_decision_log\.append\(\{", mem)]]
    # Indentation differs between the two sites; match on the assignment, not
    # on a whitespace-exact line.
    assert all(re.search(r'"metadata":\s*dec\.get\("metadata"\)', b) for b in write_blocks), (
        "a memory write site drops the envelope"
    )


def test_the_envelope_survives_a_round_trip():
    import database as db
    out = _run(db.create_session(cohort_name=_unique("ENV"), facilitator_id="god_mode"))
    sid = out.get("session_id") or out.get("id")

    envelope = {
        "schema": 1,
        "player_id": "MUR-042",
        "investment_ratio": 0.37,
        "pillar_decisions": {"energy": 40, "operations": 30,
                             "supply_chain": 20, "offsetting": 10},
        "turn": {"dividends_paid": 250000.0, "emergency_credit_used": True,
                 "force_override_cfo": True, "engagement_action": None,
                 "imitation_decay_rate": 0.05, "expected_round": 1},
    }
    n = _run(db.log_decisions(sid, 1, [{
        "bu_id": "pharma", "decision_node_id": "r1_pharma", "choice_selected": "option_b",
        "capex_allocated": 4_000_000, "time_to_decision_seconds": 91,
        "team_consensus": None, "metadata": envelope,
    }]))
    assert n == 1

    rows = _run(db.fetch_decision_log(sid)) if hasattr(db, "fetch_decision_log") \
        else _run(db.fetch_round_history(sid))
    assert rows, "nothing came back from the audit trail"

    import json

    def _walk(rows):
        """fetch_round_history nests decisions under each round; fetch_all_decisions
        returns them flat. Accept either rather than pinning one reader's shape."""
        for r in rows:
            yield r
            for d in (r.get("decisions") or []):
                yield d

    found = None
    for r in _walk(rows):
        md = r.get("metadata")
        if isinstance(md, str):
            md = json.loads(md)
        if md and md.get("player_id") == "MUR-042":
            found = md
            break
    assert found, (
        "the commit envelope did not survive persistence — pillar splits, "
        "dividends and the CFO override are gone, which is the pre-4.8 state"
    )
    assert found["pillar_decisions"]["energy"] == 40
    assert found["turn"]["emergency_credit_used"] is True
    assert found["turn"]["force_override_cfo"] is True
    assert found["investment_ratio"] == 0.37


def test_a_decision_without_an_envelope_still_writes():
    """Backwards compatibility: older callers and internal auto-commits pass no
    metadata. They must not start failing."""
    import database as db
    out = _run(db.create_session(cohort_name=_unique("ENV-bare"), facilitator_id="god_mode"))
    sid = out.get("session_id") or out.get("id")
    n = _run(db.log_decisions(sid, 1, [{
        "bu_id": "pharma", "decision_node_id": "r1", "choice_selected": "option_a",
        "capex_allocated": 1, "time_to_decision_seconds": 0, "team_consensus": None,
    }]))
    assert n == 1


# ── 2. The router actually builds it ───────────────────────────────────────

def test_the_router_builds_the_envelope_after_the_engine_runs():
    """investment_ratio is RECOMPUTED server-side (TECH-2/COR-1). If the
    envelope were built from the raw request, it would record the advisory
    value the client sent — a number that never scored anything — and a reader
    would take it for the real one. Confidently wrong beats absent only in the
    sense that it is worse.
    """
    src = (_BACKEND_DIR / "router.py").read_text(encoding="utf-8")
    build = src.index("_turn_envelope = {")
    raw = src.index("decisions_raw = [d.model_dump()")
    persist = src.index("await db.insert_next_round(")
    assert raw < build < persist, (
        "the envelope must be built AFTER the engine has run and BEFORE "
        "persistence, or it records advisory values rather than effective ones"
    )
    for field in ("dividends_paid", "emergency_credit_used", "force_override_cfo",
                  "engagement_action", "pillar_decisions", "player_id"):
        assert field in src[build:build + 2000], f"{field} missing from the envelope"
