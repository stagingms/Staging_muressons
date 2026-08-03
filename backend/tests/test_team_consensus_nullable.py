"""
TEAM-3 — team_consensus becomes honest (UX audit #7, 2026-08-02).

WHAT WAS WRONG
    `BUDecision.team_consensus` defaulted to `ConsensusLevel.majority` and the
    client hardcoded the same value on every commit, so the decision audit log
    asserted a majority decision for every round ever played — including solo
    play, including rounds the SERVER auto-committed while nobody was at the
    keyboard. The debrief question "how did your team decide?" was therefore
    answered from fiction.

WHAT THIS PINS
    1. The model no longer invents a value: an omitted consensus is None.
    2. `not_recorded` exists in the enum and is what auto-commit writes —
       "auto_default", the previous string, was not a member of the Postgres
       `consensus_level` type at all and would have violated it.
    3. Both stores agree (parity): a missing value persists as None, never as
       'majority'.
    4. The engine does not read the field, so changing it cannot move a single
       number in the simulation. This is the test that lets the change ship
       against a validated engine.
"""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("USE_MEMORY_DB", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("JWT_SECRET", "testsecret0123456789abcdefabcdef")

_BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

from models import BUDecision, ConsensusLevel  # noqa: E402


# ── 1. The model stops inventing a consensus ──────────────────────────────

def test_omitted_consensus_is_none_not_majority():
    d = BUDecision(
        bu_id="pharma", investment_ratio=0.25, capex_allocated=1_000_000,
        choice_selected="option_a", decision_node_id="round_1_pharma",
        time_to_decision_seconds=42,
    )
    assert d.team_consensus is None, (
        "An omitted consensus must stay absent. Defaulting to 'majority' is what "
        "put a fabricated answer in the graded audit log."
    )


@pytest.mark.parametrize("value", ["unanimous", "majority", "split", "facilitator_override", "not_recorded"])
def test_every_enum_member_is_accepted(value):
    d = BUDecision(
        bu_id="pharma", investment_ratio=0.1, capex_allocated=1,
        choice_selected="option_b", decision_node_id="n", time_to_decision_seconds=0,
        team_consensus=value,
    )
    assert d.team_consensus == ConsensusLevel(value)


# ── 2. not_recorded exists, auto_default never did ────────────────────────

def test_not_recorded_is_a_member():
    assert ConsensusLevel.not_recorded.value == "not_recorded"


def test_auto_default_is_rejected():
    """The old auto-commit path wrote "auto_default". It is not a member of the
    Postgres consensus_level type, so on a real database that write would have
    failed the enum constraint."""
    with pytest.raises(Exception):
        BUDecision(
            bu_id="pharma", investment_ratio=0.1, capex_allocated=1,
            choice_selected="option_b", decision_node_id="n",
            time_to_decision_seconds=0, team_consensus="auto_default",
        )


def test_auto_commit_paths_record_not_recorded():
    """Both auto-commit builders must write not_recorded — a server commit is
    the canonical 'no team answered' case."""
    router_src = (_BACKEND_DIR / "router.py").read_text(encoding="utf-8", errors="ignore")
    admin_src = (_BACKEND_DIR / "admin_router.py").read_text(encoding="utf-8", errors="ignore")
    assert 'team_consensus="not_recorded"' in router_src
    assert '"team_consensus": "not_recorded"' in admin_src
    assert '"auto_default"' not in router_src
    assert '"team_consensus": "auto_default"' not in admin_src


# ── 3. Store parity: no coercion on either side ───────────────────────────

def test_neither_store_coerces_a_missing_value_to_majority():
    pg = (_BACKEND_DIR / "database.py").read_text(encoding="utf-8", errors="ignore")
    mem = (_BACKEND_DIR / "database_memory.py").read_text(encoding="utf-8", errors="ignore")
    for name, src in (("database.py", pg), ("database_memory.py", mem)):
        assert 'dec.get("team_consensus", "majority")' not in src, (
            f"{name} still coerces a missing consensus to 'majority' — the exact "
            f"behaviour TEAM-3 removed."
        )


def test_schema_declares_the_column_nullable():
    """Both the init.sql schema and the auto-schema DDL in database.py must
    agree, or a fresh DB and a migrated DB diverge."""
    init_sql = (_BACKEND_DIR.parent / "db" / "init.sql").read_text(encoding="utf-8", errors="ignore")
    pg = (_BACKEND_DIR / "database.py").read_text(encoding="utf-8", errors="ignore")
    assert "'not_recorded'" in init_sql
    assert "team_consensus          consensus_level NOT NULL DEFAULT 'majority'" not in init_sql
    assert "team_consensus          consensus_level NOT NULL DEFAULT 'majority'" not in pg
    # The forward-only migration must be present for already-deployed databases.
    assert "ADD VALUE IF NOT EXISTS 'not_recorded'" in pg
    assert "ALTER COLUMN team_consensus DROP NOT NULL" in pg


# ── 4. The engine cannot see this field ───────────────────────────────────

def test_engine_never_reads_team_consensus():
    """The whole safety argument for this change: team_consensus is an audit
    field, never an engine input. If that stops being true, this fails and the
    change must be re-reviewed against the golden trace."""
    for fname in ("engine.py", "round_logic.py", "terminal_valuation.py"):
        src = (_BACKEND_DIR / fname).read_text(encoding="utf-8", errors="ignore")
        assert "team_consensus" not in src, (
            f"{fname} references team_consensus — it is no longer a pure audit "
            f"field, and changing its default could move simulation output."
        )
