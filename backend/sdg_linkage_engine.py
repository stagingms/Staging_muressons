"""
Muressons Global Corporation — BU-SDG Linkage Engine

Maps each Business Unit to its principal UN Sustainable Development Goals
and calculates per-BU SDG alignment scores from live game metrics.

Principled Prioritization Framework:
  💊 Pharma:    SDG 3 (Health) & SDG 6 (Water)
  ⚡ Electronics: SDG 8 (Decent Work) & SDG 12 (Responsible Production)
  🛒 Consumer:  SDG 12 (Circularity) & SDG 15 (Life on Land)
  💻 Software:  SDG 9 (Innovation) & SDG 10 (Reduced Inequalities)

Linkage Rules:
  - Pharma:     Water dependency → operational continuity
  - Electronics: Carbon intensity → 'Carbon Retribution' damage multiplier
  - Consumer:   Biodiversity loss → NCD interest rate spiral
  - Software:   AI bias → 'Truth Premium' valuation uplift
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════
#  SDG-BU MATERIALITY MAP
# ═══════════════════════════════════════════════════════════════

# Official UN SDG color palette
SDG_COLORS = {
    3: "#4C9F38",   # Good Health
    6: "#26BDE2",   # Clean Water
    8: "#A21942",   # Decent Work
    9: "#FD6925",   # Industry & Innovation
    10: "#DD1367",  # Reduced Inequalities
    12: "#BF8B2E",  # Responsible Production
    15: "#56C02B",  # Life on Land
}

SDG_BU_MATERIALITY = {
    "pharma": {
        "sdgs": [
            {
                "sdg": 3, "label": "Good Health & Well-being", "icon": "💊",
                "metric_key": "social_license_score",
                "weight": 0.6,
                "scoring": "higher_is_better",
                "description": "Patient access, drug safety, and equitable healthcare delivery",
            },
            {
                "sdg": 6, "label": "Clean Water & Sanitation", "icon": "💧",
                "metric_key": "water_dependency_score",
                "weight": 0.4,
                "scoring": "lower_is_better",
                "description": "Water dependency links directly to operational continuity",
            },
        ],
        "linkage_rule": "Water dependency scores drive operational continuity multiplier",
        "color": "#4C9F38",
    },
    "electronics": {
        "sdgs": [
            {
                "sdg": 8, "label": "Decent Work & Economic Growth", "icon": "⚡",
                "metric_key": "staff_burnout_index",
                "weight": 0.5,
                "scoring": "lower_is_better",
                "description": "Supply chain labor conditions and workforce wellbeing",
            },
            {
                "sdg": 12, "label": "Responsible Consumption & Production", "icon": "♻️",
                "metric_key": "carbon_intensity",
                "weight": 0.5,
                "scoring": "lower_is_better",
                "description": "Carbon intensity feeds the 'Carbon Retribution' damage multiplier",
            },
        ],
        "linkage_rule": "Carbon intensity drives 'Carbon Retribution' damage multiplier",
        "color": "#A21942",
    },
    "consumer_goods": {
        "sdgs": [
            {
                "sdg": 12, "label": "Responsible Consumption & Production", "icon": "🛒",
                "metric_key": "natural_capital_debt",
                "weight": 0.5,
                "scoring": "lower_is_better",
                "description": "Circularity metrics and waste reduction",
            },
            {
                "sdg": 15, "label": "Life on Land", "icon": "🌿",
                "metric_key": "biodiversity_score",
                "weight": 0.5,
                "scoring": "higher_is_better",
                "description": "Biodiversity loss drives NCD interest rate spirals",
            },
        ],
        "linkage_rule": "Biodiversity loss drives Natural Capital Debt interest rate spirals",
        "color": "#56C02B",
    },
    "software": {
        "sdgs": [
            {
                "sdg": 9, "label": "Industry, Innovation & Infrastructure", "icon": "💻",
                "metric_key": "workforce_readiness",
                "weight": 0.5,
                "scoring": "higher_is_better",
                "description": "Innovation capacity and digital infrastructure resilience",
            },
            {
                "sdg": 10, "label": "Reduced Inequalities", "icon": "⚖️",
                "metric_key": "ai_bias_score",
                "weight": 0.5,
                "scoring": "lower_is_better",
                "description": "AI bias drives the 'Truth Premium' valuation uplift",
            },
        ],
        "linkage_rule": "AI bias inversely drives 'Truth Premium' valuation uplift",
        "color": "#FD6925",
    },
}


# ═══════════════════════════════════════════════════════════════
#  METRIC NORMALIZATION
# ═══════════════════════════════════════════════════════════════

# Expected metric ranges for normalization (0-100 scoring)
_METRIC_RANGES = {
    "social_license_score":    {"min": 0, "max": 100, "default": 50},
    "water_dependency_score":  {"min": 0, "max": 100, "default": 50},
    "staff_burnout_index":     {"min": 0, "max": 100, "default": 25},
    "carbon_intensity":        {"min": 0, "max": 100, "default": 50},
    "natural_capital_debt":    {"min": 0, "max": 500_000, "default": 50_000},
    "biodiversity_score":      {"min": 0, "max": 100, "default": 50},
    "workforce_readiness":     {"min": 0, "max": 100, "default": 50},
    "ai_bias_score":           {"min": 0, "max": 100, "default": 50},
}


def _normalize_metric(value: float, key: str, scoring: str) -> float:
    """
    Normalize a raw metric value to a 0-100 SDG alignment score.
    higher_is_better: score = normalized value
    lower_is_better:  score = 100 - normalized value
    """
    mr = _METRIC_RANGES.get(key, {"min": 0, "max": 100, "default": 50})
    mn, mx = mr["min"], mr["max"]
    if mx == mn:
        return 50.0
    normalized = max(0.0, min(100.0, ((value - mn) / (mx - mn)) * 100.0))
    if scoring == "lower_is_better":
        normalized = 100.0 - normalized
    return round(normalized, 2)


# ═══════════════════════════════════════════════════════════════
#  CORE CALCULATIONS
# ═══════════════════════════════════════════════════════════════

def calc_bu_sdg_alignment(
    bu_state: dict,
    bu_id: str,
    global_state: dict | None = None,
) -> dict[str, Any]:
    """
    Calculate per-BU SDG alignment score from mapped metrics.

    Returns:
        {
            "bu_id": str,
            "sdg_score": float (0-100),
            "sdg_details": [{sdg, label, icon, raw_value, normalized, weight, contribution}],
            "material_sdgs": [3, 6],
            "linkage_rule": str,
            "gaps": [{sdg, label, score, threshold, gap_magnitude}],
        }
    """
    materiality = SDG_BU_MATERIALITY.get(bu_id)
    if not materiality:
        return {
            "bu_id": bu_id,
            "sdg_score": 50.0,
            "sdg_details": [],
            "material_sdgs": [],
            "linkage_rule": "No SDG mapping defined for this BU",
            "gaps": [],
        }

    details = []
    weighted_score = 0.0

    for sdg_def in materiality["sdgs"]:
        key = sdg_def["metric_key"]
        weight = sdg_def["weight"]
        scoring = sdg_def["scoring"]

        # Extract metric: try BU state first, then global state
        raw_value = bu_state.get(key)
        if raw_value is None and global_state:
            raw_value = global_state.get(key)
        if raw_value is None:
            # Special case: biodiversity comes from nested state
            if key == "biodiversity_score" and global_state:
                bio = global_state.get("biodiversity_state", {})
                raw_value = bio.get("biodiversity_health_index", 50)
            elif key == "water_dependency_score" and global_state:
                bio = global_state.get("biodiversity_state", {})
                raw_value = bio.get("water_stress_index", 0.5) * 100
            elif key == "ai_bias_score":
                # AI bias: derive from governance risk for Software BU
                raw_value = bu_state.get("governance_risk_score", 30)
            else:
                raw_value = _METRIC_RANGES.get(key, {}).get("default", 50)

        normalized = _normalize_metric(raw_value, key, scoring)
        contribution = round(normalized * weight, 2)
        weighted_score += contribution

        details.append({
            "sdg": sdg_def["sdg"],
            "label": sdg_def["label"],
            "icon": sdg_def["icon"],
            "description": sdg_def["description"],
            "metric_key": key,
            "raw_value": round(raw_value, 2) if isinstance(raw_value, float) else raw_value,
            "normalized_score": normalized,
            "weight": weight,
            "contribution": contribution,
            "color": SDG_COLORS.get(sdg_def["sdg"], "#888"),
        })

    # Identify gaps (SDGs scoring below 40)
    gaps = []
    for d in details:
        if d["normalized_score"] < 40:
            gaps.append({
                "sdg": d["sdg"],
                "label": d["label"],
                "score": d["normalized_score"],
                "threshold": 40,
                "gap_magnitude": round(40 - d["normalized_score"], 2),
            })

    return {
        "bu_id": bu_id,
        "sdg_score": round(weighted_score, 2),
        "sdg_details": details,
        "material_sdgs": [d["sdg"] for d in details],
        "linkage_rule": materiality["linkage_rule"],
        "color": materiality["color"],
        "gaps": gaps,
    }


def calc_group_sdg_score(
    bu_states: list[dict],
    global_state: dict | None = None,
) -> dict[str, Any]:
    """
    Calculate weighted group-level SDG alignment score across all BUs.

    Returns:
        {
            "group_sdg_score": float (0-100),
            "bu_scores": {bu_id: {sdg_score, sdg_details, ...}},
            "sdg_heatmap": {sdg_num: average_score},
            "material_gaps": [{bu_id, sdg, label, score}],
        }
    """
    bu_scores = {}
    sdg_scores_map: dict[int, list[float]] = {}

    for bu in bu_states:
        bu_id = bu.get("bu_id", "unknown")
        result = calc_bu_sdg_alignment(bu, bu_id, global_state)
        bu_scores[bu_id] = result

        for d in result["sdg_details"]:
            sdg_scores_map.setdefault(d["sdg"], []).append(d["normalized_score"])

    # Group-level score: average of all BU SDG scores
    all_scores = [v["sdg_score"] for v in bu_scores.values() if v["sdg_details"]]
    group_score = round(sum(all_scores) / max(len(all_scores), 1), 2)

    # SDG heatmap: average score per SDG across all BUs
    sdg_heatmap = {}
    for sdg_num, scores in sdg_scores_map.items():
        sdg_heatmap[sdg_num] = round(sum(scores) / len(scores), 2)

    # Aggregate material gaps
    material_gaps = []
    for bu_id, result in bu_scores.items():
        for gap in result.get("gaps", []):
            material_gaps.append({"bu_id": bu_id, **gap})

    return {
        "group_sdg_score": group_score,
        "bu_scores": bu_scores,
        "sdg_heatmap": sdg_heatmap,
        "material_gaps": material_gaps,
        "gap_count": len(material_gaps),
    }


def evaluate_sdg_materiality_gaps(
    bu_states: list[dict],
    global_state: dict | None = None,
) -> list[dict]:
    """
    Identify BUs with critical SDG underperformance (score < 30).
    Returns list of alerts for the executive cockpit.
    """
    group = calc_group_sdg_score(bu_states, global_state)
    alerts = []

    for gap in group["material_gaps"]:
        if gap["score"] < 30:
            alerts.append({
                "severity": "critical",
                "bu_id": gap["bu_id"],
                "sdg": gap["sdg"],
                "label": gap["label"],
                "score": gap["score"],
                "message": (
                    f"⚠️ Critical SDG gap: {gap['bu_id']} scores {gap['score']}/100 "
                    f"on SDG {gap['sdg']} ({gap['label']}). "
                    f"Gap magnitude: {gap['gap_magnitude']} points below threshold."
                ),
            })

    return alerts


def get_sdg_dashboard_data(
    bu_states: list[dict],
    global_state: dict | None = None,
) -> dict[str, Any]:
    """
    JSON payload for the frontend SDG Alignment Radar visualization.
    """
    group = calc_group_sdg_score(bu_states, global_state)
    alerts = evaluate_sdg_materiality_gaps(bu_states, global_state)

    return {
        "group_sdg_score": group["group_sdg_score"],
        "bu_scores": group["bu_scores"],
        "sdg_heatmap": group["sdg_heatmap"],
        "sdg_colors": SDG_COLORS,
        "materiality_map": {
            bu_id: {
                "sdgs": [s["sdg"] for s in mat["sdgs"]],
                "linkage_rule": mat["linkage_rule"],
                "color": mat["color"],
            }
            for bu_id, mat in SDG_BU_MATERIALITY.items()
        },
        "alerts": alerts,
        "gap_count": group["gap_count"],
    }


