"""
Muressons Global Command — Stakeholder Power-Interest Grid (Mendelow's Matrix)
Master data dictionary and evaluation logic for the Round 1 minigame.

2×2 Salience Grid:
  Y-axis: Power / Influence  (Low → High)
  X-axis: Interest in Muressons  (Low → High)

Quadrant Mapping:
  Top-Right    (High Power / High Interest) → "Manage Closely"
  Bottom-Right (Low Power / High Interest)  → "Keep Informed"
  Top-Left     (High Power / Low Interest)  → "Keep Satisfied"
  Bottom-Left  (Low Power / Low Interest)   → "Monitor"
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════
#  MASTER DATA DICTIONARY (Task 1)
# ═══════════════════════════════════════════════════════════════

STAKEHOLDERS = [
    # Q1 — Manage Closely (High Power / High Interest)
    {
        "id": "activist_fund",
        "name": "FutureFirst Activist Fund",
        "icon": "🦅",
        "description": "Aggressive activist investor demanding ESG accountability and board seats.",
        "correct_quadrant": "manage_closely",
    },
    {
        "id": "eu_regulators",
        "name": "EU Regulators",
        "icon": "🏛️",
        "description": "European regulators enforcing CSRD, supply chain due diligence, and carbon disclosure.",
        "correct_quadrant": "manage_closely",
    },

    # Q2 — Keep Informed (Low Power / High Interest)
    {
        "id": "local_communities",
        "name": "Deccan Plateau Local Communities",
        "icon": "🏘️",
        "description": "Communities near Muressons manufacturing facilities affected by water extraction and emissions.",
        "correct_quadrant": "keep_informed",
    },
    {
        "id": "tier3_miners",
        "name": "Tier-3 Mine Workers",
        "icon": "⛏️",
        "description": "Small-scale mineral suppliers deep in the value chain. Highly interested but low market power.",
        "correct_quadrant": "keep_informed",
    },
    {
        "id": "factory_employees",
        "name": "Factory Floor Employees",
        "icon": "👷",
        "description": "Frontline workers across manufacturing BUs. Directly impacted by decisions but limited influence.",
        "correct_quadrant": "keep_informed",
    },

    # Q3 — Keep Satisfied (High Power / Low Interest)
    {
        "id": "syndicate_banks",
        "name": "Institutional Syndicate Banks",
        "icon": "🏦",
        "description": "Major banks providing revolving credit facilities. Care about credit risk, not daily operations.",
        "correct_quadrant": "keep_satisfied",
    },
    {
        "id": "national_gov",
        "name": "National Government Tax Authority",
        "icon": "🏛️",
        "description": "Government tax authority with regulatory power but limited operational interest.",
        "correct_quadrant": "keep_satisfied",
    },

    # Q4 — Monitor (Low Power / Low Interest)
    {
        "id": "cafeteria_vendors",
        "name": "Corporate Cafeteria Vendors",
        "icon": "🍽️",
        "description": "Small catering suppliers with minimal influence on corporate strategy.",
        "correct_quadrant": "monitor",
    },
    {
        "id": "gen_public",
        "name": "General Public",
        "icon": "👥",
        "description": "The broad public. Low direct power and generally low awareness of corporate ESG.",
        "correct_quadrant": "monitor",
    },
    {
        "id": "local_media",
        "name": "Local Media",
        "icon": "📰",
        "description": "Regional media covering local business stories. Limited reach and influence.",
        "correct_quadrant": "monitor",
    },
]

# Quick lookup: stakeholder_id → correct_quadrant
MASTER_MAP: dict[str, str] = {s["id"]: s["correct_quadrant"] for s in STAKEHOLDERS}

# Valid quadrant IDs
VALID_QUADRANTS = {"manage_closely", "keep_satisfied", "keep_informed", "monitor"}

# Win condition
ACCURACY_THRESHOLD = 0.80  # 80% = 8/10 correct
BONUS_POINTS = 1000


# ═══════════════════════════════════════════════════════════════
#  EVALUATION LOGIC (Task 3)
# ═══════════════════════════════════════════════════════════════

def evaluate_stakeholder_map(submission: dict[str, str]) -> dict[str, Any]:
    """
    Compare a player's stakeholder→quadrant mapping against the master.

    Args:
        submission: dict of {stakeholder_id: quadrant_id}

    Returns:
        dict with accuracy_percentage, passed, points_awarded,
        details (per-stakeholder feedback), and the master mapping.
    """
    correct_count = 0
    details = []

    for stakeholder in STAKEHOLDERS:
        sid = stakeholder["id"]
        player_quadrant = submission.get(sid, "")
        correct_quadrant = stakeholder["correct_quadrant"]
        is_correct = player_quadrant == correct_quadrant

        if is_correct:
            correct_count += 1

        details.append({
            "id": sid,
            "name": stakeholder["name"],
            "player_quadrant": player_quadrant,
            "correct_quadrant": correct_quadrant,
            "is_correct": is_correct,
        })

    total = len(STAKEHOLDERS)
    accuracy = correct_count / total if total > 0 else 0
    passed = accuracy >= ACCURACY_THRESHOLD

    return {
        "accuracy_percentage": round(accuracy * 100, 1),
        "correct_count": correct_count,
        "total_count": total,
        "passed": passed,
        "points_awarded": BONUS_POINTS if passed else 0,
        "details": details,
        "master_mapping": MASTER_MAP,
    }


def get_stakeholder_list() -> list[dict]:
    """Return stakeholders WITHOUT the correct_quadrant (for the frontend bank)."""
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "icon": s["icon"],
            "description": s["description"],
        }
        for s in STAKEHOLDERS
    ]


def get_master_config() -> dict:
    """Return the full master config for God Mode admin view."""
    return {
        "stakeholders": STAKEHOLDERS,
        "quadrants": {
            "manage_closely": {"label": "Manage Closely", "position": "top_right", "power": "high", "interest": "high"},
            "keep_informed": {"label": "Keep Informed", "position": "bottom_right", "power": "low", "interest": "high"},
            "keep_satisfied": {"label": "Keep Satisfied", "position": "top_left", "power": "high", "interest": "low"},
            "monitor": {"label": "Monitor", "position": "bottom_left", "power": "low", "interest": "low"},
        },
        "threshold": ACCURACY_THRESHOLD,
        "bonus_points": BONUS_POINTS,
    }
