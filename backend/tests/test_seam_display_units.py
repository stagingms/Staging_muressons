"""SEAM-15 (audit 2026-09-04, Wave 3) — carbon intensity on the display surfaces
is the group's tCO₂e per $M revenue (revenue-weighted, the figure the emissions
total is built from), not the arithmetic mean of the BU intensities; and the
benchmark badge names the static FTSE 100 reference table instead of "peers".

The audit's alpha team: mean 4.64 (a divested BU at $1M revenue and CI 0 pulled
it down) against an implied 420 t / $57.19M = 6.87 tCO₂e/$M, badged "99th
percentile — outperforming 75%+ of FTSE 100 peers".
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("USE_MEMORY_DB", "true")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmarks import get_benchmarks  # noqa: E402
from engine import calc_revenue_weighted_avg_ci  # noqa: E402

ALPHA = [
    {"bu_id": "pharma", "carbon_intensity": 8.0, "revenue_base": 30_000_000, "opex_base": 20_000_000,
     "governance_risk_score": 30, "social_license_score": 60, "water_dependency": 20, "natural_capital_debt": 5},
    {"bu_id": "electronics", "carbon_intensity": 6.0, "revenue_base": 20_000_000, "opex_base": 15_000_000,
     "governance_risk_score": 30, "social_license_score": 60, "water_dependency": 20, "natural_capital_debt": 5},
    {"bu_id": "consumer_goods", "carbon_intensity": 4.56, "revenue_base": 6_190_000, "opex_base": 5_000_000,
     "governance_risk_score": 30, "social_license_score": 60, "water_dependency": 20, "natural_capital_debt": 5},
    {"bu_id": "software", "carbon_intensity": 0.0, "revenue_base": 1_000_000, "opex_base": 900_000,   # divested
     "governance_risk_score": 30, "social_license_score": 60, "water_dependency": 20, "natural_capital_debt": 5},
]


def test_benchmark_intensity_is_emissions_over_revenue_not_the_bu_mean():
    mean = sum(b["carbon_intensity"] for b in ALPHA) / len(ALPHA)
    weighted = calc_revenue_weighted_avg_ci(ALPHA)
    assert mean < 5.0 < weighted, (mean, weighted)   # the divested BU flatters the mean
    out = get_benchmarks(ALPHA, {"corporate_treasury": 50e6})
    ci = out["benchmarks"]["carbon_intensity"] if "benchmarks" in out else out["carbon_intensity"]
    assert ci["your_value"] == round(weighted, 2)
    tonnes = sum(b["carbon_intensity"] * b["revenue_base"] / 1e6 for b in ALPHA)
    assert ci["your_value"] == round(tonnes / (sum(b["revenue_base"] for b in ALPHA) / 1e6), 2)


def test_the_badge_names_a_static_reference_table_not_peers():
    out = get_benchmarks(ALPHA, {"corporate_treasury": 50e6})
    rows = out["benchmarks"].values() if "benchmarks" in out else out.values()
    for row in rows:
        if isinstance(row, dict) and "insight" in row:
            assert "peers" not in row["insight"], row["insight"]
            assert "reference" in row["insight"]


def test_the_session_report_and_analytics_use_the_same_weighting():
    import inspect
    import admin_router, admin_analytics
    src = inspect.getsource(admin_router.get_session_report)
    assert "calc_revenue_weighted_avg_ci" in src
    assert 'sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)' not in src
    src2 = inspect.getsource(admin_analytics)
    assert "calc_revenue_weighted_avg_ci" in src2
