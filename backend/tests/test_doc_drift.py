"""Documentation drift — audit 2026-09-04 SOC-8, CFG-09, OPS-7, FIN-14, VAL-11d/e · WP-28.

Pins the in-repo text to the shipped numbers so the next recalibration cannot
leave a facilitator surface describing the previous version.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("USE_MEMORY_DB", "true")

REPO = Path(__file__).resolve().parent.parent.parent


def _read(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def test_natural_decay_docs_describe_the_shipped_tiers():
    from config import (NATURAL_DECAY_NO_DECAY_RATIO, NATURAL_DECAY_MID_RATIO,
                        NATURAL_DECAY_GROWTH_RATIO, NATURAL_DECAY_MIN_ABS_CAPEX, NATURAL_DECAY_FACTOR)
    assert (NATURAL_DECAY_NO_DECAY_RATIO, NATURAL_DECAY_MID_RATIO, NATURAL_DECAY_GROWTH_RATIO) == (0.15, 0.20, 0.30)
    assert NATURAL_DECAY_MIN_ABS_CAPEX == 100_000 and NATURAL_DECAY_FACTOR == 0.96
    import engine, inspect
    doc = inspect.getsource(engine.apply_natural_decay)
    assert "0.10 / 0.25 / 0.50, config-driven" not in doc and "BU's OWN investment ratio" in doc
    excel = _read("backend/config_excel.py")
    for stale in ("(default 0.10)", "(default 0.25)", "(default 0.50)", "(default 500,000)"):
        assert stale not in excel, stale
    assert "(default 0.15)" in excel and "(default 100,000)" in excel
    glossary = _read("frontend/app/components/TechnicalGlossary.js")
    assert "0.98" not in glossary and "8-point SLO penalty" not in glossary and "+0.35" not in glossary
    assert "0.96" in glossary and "15-point" in glossary


def test_glossary_and_teleprompter_state_what_the_code_does():
    analytics = _read("backend/admin_analytics.py")
    assert "principal never debits treasury" not in analytics and "repaid straight-line" in analytics
    tele = _read("backend/admin_teleprompter.py")
    assert "R6 is the earliest round a trigger can fire" not in tele and "R4 is the earliest round" in tele
    assert "shows EXACTLY how treasury moved" not in tele and "FIN-06" in tele
    sidebar = _read("frontend/app/config/sidebarConfig.js")
    assert "the cohort shell untouched" in sidebar
    registry = _read("frontend/app/components/PlayerRegistry.js")
    assert "A new random password will be generated" not in registry and "ID@123" in registry


def test_init_sql_carries_the_purge_bypass_the_boot_copy_has():
    sql = _read("db/init.sql")
    assert "current_setting('muressons.allow_purge', true) = 'on'" in sql
    assert sql.index("allow_purge") < sql.index("Immutability violation: DELETE")


def test_published_mr_ceilings_come_from_one_table():
    from terminal_valuation import (MR_PUBLISHED_CEILINGS, MR_CEILING_BY_PARADIGM, max_achievable_mr_for,
                                    calculate_mr)
    assert MR_PUBLISHED_CEILINGS == {"base": 1.93, "jt_scaled": 2.02, "brsr": 1.98}
    assert MR_CEILING_BY_PARADIGM["multi_toggles"] == 2.02 and MR_CEILING_BY_PARADIGM["legacy_abc"] == 1.93
    assert max_achievable_mr_for({}, 0) == 1.93
    assert max_achievable_mr_for({}, 3) == 2.02
    assert max_achievable_mr_for({"brsr_net_positive_dividend": 0.05}, 0) == 1.98
    assert calculate_mr({}, 50, 0, 50, 1.0, 0)["max_achievable_mr"] == 1.93
    assert calculate_mr({}, 50, 0, 50, 1.0, 5)["max_achievable_mr"] == 2.02
    from admin_router import _PARADIGM_NORMALIZATION
    assert {k: v["max_mr"] for k, v in _PARADIGM_NORMALIZATION.items()} == {
        "legacy_abc": 1.93, "multi_toggles": 2.02, "advanced_climate": 1.93, "healthcare": 1.93, "brsr_ngrbc": 1.98}
    assert "2.33" not in _read("backend/consequence_dna_api.py")


def test_context_docs_name_the_live_mechanics():
    ctx = _read("SIMULATION_CONTEXT.md")
    assert "Scores decay toward baseline when uninvested" not in ctx and "on its OWN investment ratio" in ctx
    assert "reputation GAIN since the previous tick" in ctx
    card = _read("MODEL_CARD.md")
    assert "audit SOC-3" in card and "pre-reconciliation stock" in card
    deploy = _read("DEPLOYMENT_CHECKLIST.md")
    assert "MURESSONS_MULTIWORKER_VERIFIED=true" in deploy and "scale_preflight.py" in deploy
