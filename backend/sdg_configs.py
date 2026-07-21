"""
Muressons Global Corporation — SDG Configs (top-level adapter)
==============================================================

ARCHITECTURAL NOTE
------------------
This module is a *dependency-injection adapter*, not a data source.

The canonical SDG round configurations live in:
    side_tracks/corporate_sdg/configs.py

engine.py and router.py import from this top-level ``sdg_configs`` namespace
(e.g. ``from sdg_configs import get_sdg_round_config``).  Rather than
duplicating data, this module re-exports from the canonical location and adds
``get_sdg_interlinkage_matrix()``, which is called only during the UN-SDG
paradigm's process_tick loop in engine.py.

Keeping data in one place prevents drift: any change to SDG_ROUND_CONFIGS in
side_tracks/corporate_sdg/configs.py is immediately visible here.
"""

from __future__ import annotations
from typing import Any

# ── Re-export canonical round configs ────────────────────────────────────────
# These are the functions engine.py and router.py import from this namespace.
from side_tracks.corporate_sdg.configs import (   # noqa: F401  (re-export)
    get_sdg_round_config,
    get_sdg_round_options,
    SDG_ROUND_CONFIGS,
    SDG_POINTS_MAP,
)


# ── SDG Cluster Interlinkage Matrix ───────────────────────────────────────────
# Used by engine.py (process_tick, UN-SDG paradigm) to compute cross-cluster
# spillover effects each round.
#
# Key: (source_cluster, target_cluster)  — both are BU state dict keys.
# Value: multiplier applied as:
#     spillover_delta[target] += multiplier * (source_value / 100.0)
#
# The engine then scales: actual_spillover = clip(delta * 10, -5, +5)
# and applies: new_value = clip(old + spillover - decay, 0, 100)
#
# Matrix design rationale (UN SDG interlinkages, 2019 Global Assessment):
#   SDG 6 (Clean Water) → SDG 3 (Good Health):      strong positive
#   SDG 4 (Quality Education) → SDG 8 (Decent Work): positive
#   SDG 8 (Decent Work / Sustainable Growth) → SDG 10 (Reduced Inequalities): positive
#   SDG 12 (Responsible Consumption) → SDG 13 (Climate Action): positive
#   SDG 16 (Governance / Peace) → all clusters:     positive (institutional quality)
#   SDG 17 (Partnerships) → SDG 1 (Basic Needs):   positive (aid effectiveness)
#   SDG 1 (Basic Needs) ↔ SDG 10 (Human Capital):  bidirectional positive
#   Governance fragility → Basic Needs:              negative spillover
#
# Cluster-to-SDG mapping used in the UN-SDG paradigm BU state:
#   basic_needs      → SDG 1, 2, 3, 6
#   human_capital    → SDG 4, 5, 8, 10
#   sustainable_growth → SDG 7, 8, 9, 11
#   planet           → SDG 12, 13, 14, 15
#   governance       → SDG 16
#   partnerships     → SDG 17

_INTERLINKAGE_MATRIX: dict[tuple[str, str], float] = {
    # ── Positive spillovers ───────────────────────────────────────────────────
    # Basic Needs ↔ Human Capital (SDG 1-4 bidirectional linkage)
    ("basic_needs",       "human_capital"):      0.25,
    ("human_capital",     "basic_needs"):        0.20,

    # Human Capital → Sustainable Growth (education/skills → economic output)
    ("human_capital",     "sustainable_growth"): 0.20,

    # Partnerships → Basic Needs (aid effectiveness, SDG 17→1)
    ("partnerships",      "basic_needs"):        0.15,

    # Governance → Sustainable Growth (institutional quality → investment)
    ("governance",        "sustainable_growth"): 0.20,

    # Governance → Human Capital (strong institutions enable education)
    ("governance",        "human_capital"):      0.10,

    # Governance → Partnerships (credible governance attracts partners)
    ("governance",        "partnerships"):       0.15,

    # Sustainable Growth → Planet (economic growth enables green investment)
    ("sustainable_growth","planet"):             0.10,

    # Partnerships → Governance (multilateral accountability)
    ("partnerships",      "governance"):         0.10,

    # Planet → Basic Needs (clean environment → clean water / food security)
    ("planet",            "basic_needs"):        0.10,

    # ── Negative spillovers (trade-off tensions) ──────────────────────────────
    # Sustainable Growth → Basic Needs negative (rapid industrialisation displaces)
    # Only active when sustainable_growth is very high and basic_needs is low;
    # keep as a small drag rather than a hard rule — the engine clips to ±5.
    ("sustainable_growth","basic_needs"):        -0.05,

    # Planet → Sustainable Growth negative (environmental compliance costs)
    ("planet",            "sustainable_growth"): -0.08,
}


def get_sdg_interlinkage_matrix() -> dict[tuple[str, str], float]:
    """
    Return the SDG cluster interlinkage matrix used by process_tick.

    Returns a dict keyed by (source_cluster, target_cluster) tuples where
    each value is a float multiplier.  The engine applies these as:

        spillover_delta[target] += multiplier * (source_value / 100.0)
        actual_spillover = clip(spillover_delta[target] * 10, -5.0, +5.0)
        new_value = clip(old_value + actual_spillover - decay, 0, 100)

    Returning a new dict each call prevents callers from mutating the module-
    level constant (defensive copy is cheap — the matrix is small and static).
    """
    return dict(_INTERLINKAGE_MATRIX)
