"""
Muressons Global Command — ESG Industry Benchmarks
Static FTSE 100 ESG benchmark data for percentile comparisons.
Sources: MSCI ESG Ratings, Sustainalytics, CDP Climate Disclosure.
"""

from __future__ import annotations
from typing import Any
import bisect


# ═══════════════════════════════════════════════════════════════
#  FTSE 100 ESG BENCHMARK DISTRIBUTIONS
#  Each list represents sorted values at 10th, 20th, ... 90th percentile
#  Data approximated from public MSCI/Sustainalytics reports (2024-2025)
# ═══════════════════════════════════════════════════════════════

BENCHMARKS: dict[str, dict[str, Any]] = {
    "carbon_intensity": {
        "label": "Carbon Intensity (tCO2e/$M Revenue)",
        "unit": "tCO2e/$M",
        "direction": "lower_is_better",
        # P10=5, P20=12, P30=18, P40=25, P50=35, P60=45, P70=58, P80=75, P90=120
        "percentiles": [5, 12, 18, 25, 35, 45, 58, 75, 120],
        "industry_leaders": [
            {"company": "Software Co.", "value": 4, "note": "Cloud-native, 100% renewable energy"},
            {"company": "Financial Group", "value": 8, "note": "Scope 1+2 near-zero, Scope 3 dominant"},
        ],
        "industry_laggards": [
            {"company": "Mining Corp", "value": 180, "note": "Heavy industrial, Scope 1 dominant"},
            {"company": "Cement PLC", "value": 145, "note": "Process emissions, hard-to-abate sector"},
        ],
    },
    "governance_risk_score": {
        "label": "Governance Risk Score",
        "unit": "points",
        "direction": "lower_is_better",
        # P10=5, P20=10, P30=15, P40=20, P50=25, P60=32, P70=40, P80=52, P90=65
        "percentiles": [5, 10, 15, 20, 25, 32, 40, 52, 65],
        "industry_leaders": [
            {"company": "Governance Star PLC", "value": 3, "note": "Independent board, ESG committee"},
        ],
        "industry_laggards": [
            {"company": "Legacy Inc", "value": 72, "note": "Dual-class shares, no ESG oversight"},
        ],
    },
    "social_license_score": {
        "label": "Social License to Operate",
        "unit": "score",
        "direction": "higher_is_better",
        # P10=22, P20=30, P30=38, P40=45, P50=52, P60=60, P70=68, P80=76, P90=85
        "percentiles": [22, 30, 38, 45, 52, 60, 68, 76, 85],
        "industry_leaders": [
            {"company": "Community Corp", "value": 92, "note": "Just Transition pioneer, living wage"},
        ],
        "industry_laggards": [
            {"company": "Extraction Co", "value": 15, "note": "Multiple community conflicts, legal action"},
        ],
    },
    "ebitda_margin": {
        "label": "EBITDA Margin",
        "unit": "%",
        "direction": "higher_is_better",
        # P10=5, P20=8, P30=11, P40=14, P50=17, P60=21, P70=25, P80=30, P90=38
        "percentiles": [5, 8, 11, 14, 17, 21, 25, 30, 38],
        "industry_leaders": [
            {"company": "Tech Giant PLC", "value": 42, "note": "Platform model, low marginal cost"},
        ],
        "industry_laggards": [
            {"company": "Retail Chain", "value": 3, "note": "Thin margins, high competition"},
        ],
    },
    "water_dependency": {
        "label": "Water Dependency Index",
        "unit": "score",
        "direction": "lower_is_better",
        # P10=2, P20=5, P30=10, P40=15, P50=22, P60=30, P70=40, P80=55, P90=75
        "percentiles": [2, 5, 10, 15, 22, 30, 40, 55, 75],
        "industry_leaders": [
            {"company": "Digital Services", "value": 1, "note": "Air-cooled data centres"},
        ],
        "industry_laggards": [
            {"company": "Beverage Corp", "value": 85, "note": "Water-intensive production"},
        ],
    },
    "natural_capital_debt": {
        "label": "Natural Capital Debt",
        "unit": "units",
        "direction": "lower_is_better",
        # P10=0, P20=2, P30=5, P40=8, P50=12, P60=18, P70=28, P80=42, P90=65
        "percentiles": [0, 2, 5, 8, 12, 18, 28, 42, 65],
        "industry_leaders": [
            {"company": "Regenerative AgriCo", "value": 0, "note": "Net nature-positive certified"},
        ],
        "industry_laggards": [
            {"company": "Petrochem Group", "value": 95, "note": "Unaddressed legacy contamination"},
        ],
    },
}


def _calc_percentile(value: float, percentile_list: list[float], lower_is_better: bool) -> int:
    """
    Calculate the percentile rank of a value against a sorted distribution.
    percentile_list should contain 9 values (P10 through P90).
    Returns a percentile (0-100).
    """
    if not percentile_list:
        return 50
    # For lower_is_better: lower values = higher percentile (better)
    # For higher_is_better: higher values = higher percentile (better)
    if lower_is_better:
        # Invert: count how many percentiles the value is below
        pos = bisect.bisect_right(percentile_list, value)
        percentile = round((pos / len(percentile_list)) * 100)
        # Invert so lower = better percentile
        percentile = 100 - percentile + 10
    else:
        pos = bisect.bisect_left(percentile_list, value)
        percentile = round((pos / len(percentile_list)) * 100) + 10

    return max(1, min(99, percentile))


def get_benchmarks(
    bu_states: list[dict],
    global_state: dict,
) -> dict[str, Any]:
    """
    Compare current simulation metrics against FTSE 100 benchmarks.
    Returns percentile rankings and contextual insights.
    """
    n = len(bu_states) or 1
    avg_ci = sum(bu.get("carbon_intensity", 0) for bu in bu_states) / n
    avg_gov = sum(bu.get("governance_risk_score", 0) for bu in bu_states) / n
    avg_sl = sum(bu.get("social_license_score", 50) for bu in bu_states) / n
    avg_wd = sum(bu.get("water_dependency", 0) for bu in bu_states) / n
    avg_ncd = sum(bu.get("natural_capital_debt", 0) for bu in bu_states) / n

    total_rev = sum(bu["revenue_base"] for bu in bu_states)
    total_opex = sum(bu["opex_base"] for bu in bu_states)
    ebitda_margin = round(((total_rev - total_opex) / max(total_rev, 1)) * 100, 1)

    metrics = {
        "carbon_intensity": avg_ci,
        "governance_risk_score": avg_gov,
        "social_license_score": avg_sl,
        "ebitda_margin": ebitda_margin,
        "water_dependency": avg_wd,
        "natural_capital_debt": avg_ncd,
    }

    results: dict[str, dict] = {}
    for metric_id, value in metrics.items():
        benchmark = BENCHMARKS.get(metric_id)
        if not benchmark:
            continue
        lower_is_better = benchmark["direction"] == "lower_is_better"
        pctl = _calc_percentile(value, benchmark["percentiles"], lower_is_better)

        # Generate insight
        if pctl >= 75:
            insight = f"Top quartile — outperforming 75%+ of FTSE 100 peers"
            badge = "🏆"
        elif pctl >= 50:
            insight = f"Above median — performing better than most FTSE 100 peers"
            badge = "✅"
        elif pctl >= 25:
            insight = f"Below median — room for improvement vs FTSE 100 peers"
            badge = "⚠️"
        else:
            insight = f"Bottom quartile — significantly lagging FTSE 100 peers"
            badge = "🔴"

        results[metric_id] = {
            "label": benchmark["label"],
            "your_value": round(value, 2),
            "unit": benchmark["unit"],
            "percentile": pctl,
            "percentile_label": f"{pctl}th percentile",
            "badge": badge,
            "insight": insight,
            "industry_leaders": benchmark.get("industry_leaders", []),
            "direction": benchmark["direction"],
        }

    return {
        "benchmarks": results,
        "data_source": "FTSE 100 ESG Benchmarks (MSCI/Sustainalytics, 2024-2025)",
        "note": "Percentiles are approximate. Real-world distributions vary by sector.",
    }
