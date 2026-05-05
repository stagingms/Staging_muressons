"""
Muressons Global Corporation — Stakeholder Power-Interest Grid (Mendelow's Matrix)
Master data dictionary and evaluation logic for the Round 1 minigame.

2×2 Salience Grid:
  Y-axis: Power / Influence  (Low → High)
  X-axis: Interest in Muressons  (Low → High)

Quadrant Mapping:
  Top-Right    (High Power / High Interest) → "Manage Closely"
  Bottom-Right (Low Power / High Interest)  → "Keep Informed"
  Top-Left     (High Power / Low Interest)  → "Keep Satisfied"
  Bottom-Left  (Low Power / Low Interest)   → "Monitor"

Enhanced with:
  - C4:  Graduated scoring (3000/2000/1000/0 + reputation/treasury penalties)
  - C6:  Behavioural evidence descriptions (analytical, not classificatory)
  - C8:  Engagement tactics for "Manage Closely" stakeholders
  - C12: Treasury penalty for poor analysis (<60%)
  - C13: Mitchell et al. (1997) urgency + legitimacy badges
  - C15: Intelligence dossier (news clippings per stakeholder)
  - C17: Ambiguous stakeholder with dual-quadrant acceptance
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════
#  MASTER DATA DICTIONARY
#  Descriptions are BEHAVIOURAL evidence (C6) — players must
#  infer Power and Interest from what stakeholders DO, not labels.
# ═══════════════════════════════════════════════════════════════

STAKEHOLDERS = [
    # Q1 — Manage Closely (High Power / High Interest)
    {
        "id": "activist_fund",
        "name": "FutureFirst Activist Fund",
        "icon": "🦅",
        "description": (
            "Filed 3 shareholder resolutions last period demanding climate risk disclosure. "
            "Currently building a 7% blocking stake and publicly threatening a board challenge "
            "at the next AGM."
        ),
        "correct_quadrant": "manage_closely",
        "urgency": "high",
        "legitimacy": "high",
        "urgency_rationale": "Active proxy fight with AGM deadline in 90 days. Cannot be deferred.",
        "intel_dossier": [
            "📰 FT: 'FutureFirst acquires 5.2% Muressons stake, signals intent to force ESG vote'",
            "📰 Reuters: 'Activist fund hires ex-ISSB chair as strategic advisor for Muressons campaign'",
            "📰 Bloomberg: 'FutureFirst proxy materials demand 3 independent climate directors'",
        ],
        "engagement_tactics": [
            {"id": "board_seats", "label": "Offer 2 board seats to fund nominees", "correct": True,
             "rationale": "Co-opts the activist into governance, converting adversary to partner."},
            {"id": "buyback", "label": "Launch share buyback to dilute their stake", "correct": False,
             "rationale": "Defensive financial engineering — signals fear, not engagement. Escalates conflict."},
            {"id": "public_letter", "label": "Publish open letter rejecting their demands", "correct": False,
             "rationale": "Confrontational stance that mobilises other institutional investors against management."},
        ],
    },
    {
        "id": "eu_regulators",
        "name": "EU Regulators",
        "icon": "🏛️",
        "description": (
            "Issued a formal compliance notice last month citing gaps in CSRD transition planning. "
            "Scheduled a mandatory site inspection of the Düsseldorf facility for Q3. "
            "Fined a peer company €15M for similar deficiencies last year."
        ),
        "correct_quadrant": "manage_closely",
        "urgency": "high",
        "legitimacy": "high",
        "urgency_rationale": "Formal compliance notice with Q3 inspection deadline. Regulatory clock is ticking.",
        "intel_dossier": [
            "📰 Politico EU: 'Brussels signals tougher enforcement of CSRD Article 8 for multinational conglomerates'",
            "📰 FT: 'EU regulator fines ChemCorp €15M for incomplete Scope 3 disclosure — precedent for sector'",
            "📰 Reuters: 'DG FISMA adds Muressons to priority review list for 2025 CSRD assurance cycle'",
        ],
        "engagement_tactics": [
            {"id": "proactive_report", "label": "Submit voluntary pre-compliance ESRS report ahead of deadline", "correct": True,
             "rationale": "Demonstrates good faith, may reduce penalty severity if gaps remain."},
            {"id": "lobby", "label": "Hire Brussels lobbyists to delay enforcement timeline", "correct": False,
             "rationale": "Regulatory capture attempt — reputational disaster if leaked to press."},
            {"id": "min_compliance", "label": "Wait for inspection and respond only to specific findings", "correct": False,
             "rationale": "Reactive posture invites maximum penalty exposure."},
        ],
    },

    # Q2 — Keep Informed (Low Power / High Interest)
    {
        "id": "local_communities",
        "name": "Deccan Plateau Local Communities",
        "icon": "🏘️",
        "description": (
            "Organised a 200-person peaceful protest outside the Pune facility last week over "
            "groundwater depletion. Filed a Right to Water petition with the state tribunal. "
            "Local panchayat leaders are actively seeking media coverage."
        ),
        "correct_quadrant": "keep_informed",
        "urgency": "high",
        "legitimacy": "high",
        "urgency_rationale": "Active legal petition and escalating protests. High urgency but limited market power.",
        "intel_dossier": [
            "📰 Times of India: 'Villagers block tanker access to Muressons Pune plant over water rights'",
            "📰 Scroll.in: 'Deccan groundwater levels drop 40% near industrial corridor — NGO report'",
            "📰 NDTV: 'State tribunal accepts community petition against corporate water extraction'",
        ],
    },
    {
        "id": "tier3_miners",
        "name": "Tier-3 Mine Workers",
        "icon": "⛏️",
        "description": (
            "A leaked WhatsApp group reveals cobalt miners in the DRC supply chain working "
            "14-hour shifts without PPE. An ILO observer has flagged the site. Workers are "
            "organising through an informal union but have no direct contract with Muressons."
        ),
        "correct_quadrant": "keep_informed",
        "urgency": "medium",
        "legitimacy": "high",
        "urgency_rationale": "ILO flag creates latent exposure. No immediate deadline but high moral legitimacy.",
        "intel_dossier": [
            "📰 Guardian: 'Cobalt supply chains still rife with child labour despite industry pledges'",
            "📰 BBC Africa: 'ILO observer flags safety violations at DRC mine linked to European tech supply chains'",
            "📰 Supply Chain Dive: 'Tier-3 visibility remains blind spot for 78% of FTSE 100 companies'",
        ],
    },
    {
        "id": "factory_employees",
        "name": "Factory Floor Employees",
        "icon": "👷",
        "description": (
            "Shop stewards submitted a formal grievance about mandatory overtime ahead of the "
            "Q4 production push. Internal pulse survey shows 62% of line workers 'dissatisfied' "
            "with management communication. Union membership has risen 15% this year."
        ),
        "correct_quadrant": "keep_informed",
        "urgency": "medium",
        "legitimacy": "high",
        "urgency_rationale": "Rising union membership signals latent collective action capability.",
        "intel_dossier": [
            "📰 Internal Memo: 'Q3 pulse survey — 62% dissatisfaction rate, highest in 5 years'",
            "📰 Manufacturing Today: 'Union membership surges across European manufacturing sector'",
            "📰 HR Brief: 'Shop steward grievance filed re: mandatory overtime — formal response due in 14 days'",
        ],
    },

    # Q3 — Keep Satisfied (High Power / Low Interest)
    {
        "id": "syndicate_banks",
        "name": "Institutional Syndicate Banks",
        "icon": "🏦",
        "description": (
            "Hold €2.1B in revolving credit facilities with covenant triggers at 3.5× "
            "net debt/EBITDA. Sent a routine annual review letter — no flags raised. "
            "Their ESG desk published a sector note last month but did not mention Muressons."
        ),
        "correct_quadrant": "keep_satisfied",
        "urgency": "low",
        "legitimacy": "high",
        "urgency_rationale": "No covenant breach imminent. Routine engagement sufficient.",
        "intel_dossier": [
            "📰 Euromoney: 'Syndicate banks tighten ESG covenants for new facilities — existing deals grandfathered'",
            "📰 Internal Finance: 'Annual credit review — all covenants met. Next review Q2 2026'",
            "📰 Banking Times: 'JPM/HSBC ESG desk rates industrials sector 'neutral' — no Muressons mention'",
        ],
    },
    {
        "id": "national_gov",
        "name": "National Government Tax Authority",
        "icon": "🏛️",
        "description": (
            "Conducted a standard transfer pricing audit of the Singapore subsidiary last year "
            "with no adverse findings. New carbon border adjustment regulations are in draft "
            "stage — earliest implementation is 18 months away. No direct correspondence this period."
        ),
        "correct_quadrant": "keep_satisfied",
        "urgency": "low",
        "legitimacy": "high",
        "urgency_rationale": "No active investigation. CBAM is 18+ months from enforcement.",
        "intel_dossier": [
            "📰 Tax Journal: 'Transfer pricing audit of Muressons Singapore — no adjustments required'",
            "📰 Reuters: 'CBAM Phase 2 draft regulations published — 18-month implementation timeline'",
            "📰 Gov Gazette: 'Corporate tax compliance dashboard — Muressons rated Green (fully compliant)'",
        ],
    },

    # Q4 — Monitor (Low Power / Low Interest)
    {
        "id": "cafeteria_vendors",
        "name": "Corporate Cafeteria Vendors",
        "icon": "🍽️",
        "description": (
            "Renewed their annual catering contract last month without negotiation. "
            "Serve approximately 800 meals/day across 3 campus locations. "
            "Have never attended a supplier engagement session or raised any concerns."
        ),
        "correct_quadrant": "monitor",
        "urgency": "low",
        "legitimacy": "low",
        "urgency_rationale": "No claims, no engagement, no influence pathway.",
        "intel_dossier": [
            "📰 Procurement Log: 'Cafeteria contract auto-renewed — $1.2M annual, no change'",
            "📰 No external media coverage",
            "📰 Supplier Survey: 'Cafeteria vendors did not respond to annual ESG questionnaire'",
        ],
    },
    {
        "id": "gen_public",
        "name": "General Public",
        "icon": "👥",
        "description": (
            "A consumer sentiment survey shows 4% unaided brand awareness for Muressons. "
            "No trending social media mentions this period. A B2B conglomerate, Muressons "
            "products are rarely purchased directly by end consumers."
        ),
        "correct_quadrant": "monitor",
        "urgency": "low",
        "legitimacy": "low",
        "urgency_rationale": "Negligible brand awareness. B2B model limits public salience.",
        "intel_dossier": [
            "📰 Brand Tracker Q3: '4% unaided awareness — unchanged from Q2'",
            "📰 Social Listening: '12 mentions of Muressons on Twitter/X this month (vs. 45K for Apple)'",
            "📰 No consumer-facing product recalls or public complaints on record",
        ],
    },

    # C17: AMBIGUOUS STAKEHOLDER — accepts 2 quadrants
    {
        "id": "local_media",
        "name": "Regional Business Journalist",
        "icon": "📰",
        "description": (
            "A well-connected investigative reporter at the regional business daily has been "
            "requesting interviews with the Head of Sustainability. Published 2 articles about "
            "competitor ESG practices last month. Has 85K followers on X/Twitter and a track "
            "record of stories being picked up by national outlets."
        ),
        "correct_quadrant": "monitor",
        "alternate_quadrant": "keep_informed",
        "alternate_rationale": (
            "Reasonable case for 'Keep Informed': their track record of national syndication "
            "means a negative story could rapidly escalate. Proactive engagement (background "
            "briefings, exclusives) could convert them into an ally. Mitchell et al. (1997) "
            "would classify this stakeholder as having latent power activated by urgency — "
            "a crisis event would instantly shift them to 'Manage Closely'."
        ),
        "urgency": "medium",
        "legitimacy": "medium",
        "urgency_rationale": "No immediate deadline, but investigative interest creates latent exposure.",
        "intel_dossier": [
            "📰 Press Office: 'Interview request from J. Mehta, Deccan Herald Business — 3rd request this period'",
            "📰 Media Monitor: 'J. Mehta's competitor ESG article syndicated to Economic Times (reach: 2.1M)'",
            "📰 X/Twitter: 'Reporter's thread on greenwashing in Indian manufacturing got 12K engagements'",
        ],
    },
]

# Quick lookup: stakeholder_id → correct_quadrant
MASTER_MAP: dict[str, str] = {s["id"]: s["correct_quadrant"] for s in STAKEHOLDERS}

# ═══════════════════════════════════════════════════════════════
#  VERTICAL-AWARE HELPERS
#  When BU substitutions are active, we can serve the vertical's
#  stakeholder set instead of the default Muressons set.
# ═══════════════════════════════════════════════════════════════


def _resolve_active_vertical(global_state: dict) -> str | None:
    """
    If the session has any BU substitutions, return the first
    vertical ID found (used to select alternate stakeholder data).
    Returns None for default sessions.
    """
    subs = global_state.get("bu_substitutions", {})
    if not subs:
        return None
    # Return the first substitution vertical_id
    from bu_profiles import DEFAULT_SLOTS
    for slot in DEFAULT_SLOTS:
        v_id = subs.get(slot)
        if v_id and v_id != slot:
            return v_id
    return None


def get_stakeholders_for_session(global_state: dict) -> list[dict]:
    """Return the appropriate stakeholder set for a session (vertical or default)."""
    v_id = _resolve_active_vertical(global_state)
    if v_id:
        from vertical_stakeholders import get_stakeholders_for_vertical
        vertical_data = get_stakeholders_for_vertical(v_id)
        if vertical_data:
            return vertical_data
    return STAKEHOLDERS


def get_master_map_for_session(global_state: dict) -> dict[str, str]:
    """Return the stakeholder_id→quadrant mapping for the active session context."""
    stakeholders = get_stakeholders_for_session(global_state)
    return {s["id"]: s["correct_quadrant"] for s in stakeholders}


def evaluate_stakeholder_map_for_session(
    submission: dict[str, str], global_state: dict
) -> dict[str, Any]:
    """
    Session-aware evaluation: uses vertical stakeholders if substitutions are active.
    Falls back to the default Muressons evaluation otherwise.
    """
    stakeholders = get_stakeholders_for_session(global_state)
    if stakeholders is STAKEHOLDERS:
        # Default path — use existing function
        return evaluate_stakeholder_map(submission)
    # Vertical path — run evaluation against the vertical set
    return _evaluate_against(submission, stakeholders)


def _evaluate_against(submission: dict[str, str], stakeholders: list[dict]) -> dict[str, Any]:
    """Generic evaluator parameterised by a stakeholder set."""
    correct_count = 0
    details = []
    master_map = {}

    for stakeholder in stakeholders:
        sid = stakeholder["id"]
        player_quadrant = submission.get(sid, "")
        correct_quadrant = stakeholder["correct_quadrant"]
        alternate = stakeholder.get("alternate_quadrant")
        master_map[sid] = correct_quadrant

        is_correct = (player_quadrant == correct_quadrant) or (
            alternate and player_quadrant == alternate
        )
        if is_correct:
            correct_count += 1

        details.append({
            "id": sid,
            "name": stakeholder["name"],
            "player_quadrant": player_quadrant,
            "correct_quadrant": correct_quadrant,
            "alternate_quadrant": alternate,
            "alternate_rationale": stakeholder.get("alternate_rationale", ""),
            "is_correct": is_correct,
        })

    total = len(stakeholders)
    accuracy = correct_count / total if total > 0 else 0

    points_awarded = 0
    scoring_tier = "Below Threshold"
    for threshold, points, label in SCORING_TIERS:
        if accuracy >= threshold:
            points_awarded = points
            scoring_tier = label
            break

    passed = accuracy >= 0.80
    reputation_penalty = FAILURE_REPUTATION_PENALTY if not passed else 0
    treasury_penalty = POOR_ANALYSIS_TREASURY_PENALTY if accuracy < 0.60 else 0

    urgency_debrief = [
        {
            "id": s["id"], "name": s["name"],
            "urgency": s.get("urgency", "low"),
            "legitimacy": s.get("legitimacy", "low"),
            "urgency_rationale": s.get("urgency_rationale", ""),
        }
        for s in stakeholders
    ]

    engagement_tactics = []
    for s in stakeholders:
        if s["correct_quadrant"] == "manage_closely" and s.get("engagement_tactics"):
            engagement_tactics.append({
                "stakeholder_id": s["id"],
                "stakeholder_name": s["name"],
                "tactics": [
                    {"id": t["id"], "label": t["label"], "correct": t["correct"], "rationale": t["rationale"]}
                    for t in s["engagement_tactics"]
                ],
            })

    return {
        "accuracy_percentage": round(accuracy * 100, 1),
        "correct_count": correct_count,
        "total_count": total,
        "passed": passed,
        "points_awarded": points_awarded,
        "scoring_tier": scoring_tier,
        "reputation_penalty": reputation_penalty,
        "treasury_penalty": treasury_penalty,
        "details": details,
        "master_mapping": master_map,
        "urgency_debrief": urgency_debrief,
        "engagement_tactics": engagement_tactics,
    }


ALTERNATE_MAP: dict[str, str] = {
    s["id"]: s["alternate_quadrant"]
    for s in STAKEHOLDERS
    if s.get("alternate_quadrant")
}

# Valid quadrant IDs
VALID_QUADRANTS = {"manage_closely", "keep_satisfied", "keep_informed", "monitor"}

# ═══════════════════════════════════════════════════════════════
#  SCORING (C4: Graduated tiers + C12: Treasury penalty)
# ═══════════════════════════════════════════════════════════════

SCORING_TIERS = [
    (1.00, 3000, "Perfect Alignment"),
    (0.90, 2000, "Strong Alignment"),
    (0.80, 1000, "Adequate Alignment"),
]
FAILURE_REPUTATION_PENALTY = -3    # Rep penalty if <80%
POOR_ANALYSIS_TREASURY_PENALTY = -500_000  # $500K wasted consulting if <60%


# ═══════════════════════════════════════════════════════════════
#  EVALUATION LOGIC
# ═══════════════════════════════════════════════════════════════

def evaluate_stakeholder_map(submission: dict[str, str]) -> dict[str, Any]:
    """
    Compare a player's stakeholder→quadrant mapping against the master.
    C4:  Graduated scoring with reputation/treasury penalties.
    C13: Urgency debrief returned post-submission.
    C17: Ambiguous stakeholders accept alternate quadrant as correct.
    """
    correct_count = 0
    details = []

    for stakeholder in STAKEHOLDERS:
        sid = stakeholder["id"]
        player_quadrant = submission.get(sid, "")
        correct_quadrant = stakeholder["correct_quadrant"]
        alternate = stakeholder.get("alternate_quadrant")

        # C17: Accept alternate quadrant
        is_correct = (player_quadrant == correct_quadrant) or (
            alternate and player_quadrant == alternate
        )

        if is_correct:
            correct_count += 1

        details.append({
            "id": sid,
            "name": stakeholder["name"],
            "player_quadrant": player_quadrant,
            "correct_quadrant": correct_quadrant,
            "alternate_quadrant": alternate,
            "alternate_rationale": stakeholder.get("alternate_rationale", ""),
            "is_correct": is_correct,
        })

    total = len(STAKEHOLDERS)
    accuracy = correct_count / total if total > 0 else 0

    # C4: Graduated scoring
    points_awarded = 0
    scoring_tier = "Below Threshold"
    for threshold, points, label in SCORING_TIERS:
        if accuracy >= threshold:
            points_awarded = points
            scoring_tier = label
            break

    passed = accuracy >= 0.80

    # C4: Reputation penalty for <80%
    reputation_penalty = FAILURE_REPUTATION_PENALTY if not passed else 0

    # C12: Treasury penalty for <60%
    treasury_penalty = POOR_ANALYSIS_TREASURY_PENALTY if accuracy < 0.60 else 0

    # C13: Urgency debrief (Mitchell et al. 1997)
    urgency_debrief = [
        {
            "id": s["id"],
            "name": s["name"],
            "urgency": s.get("urgency", "low"),
            "legitimacy": s.get("legitimacy", "low"),
            "urgency_rationale": s.get("urgency_rationale", ""),
        }
        for s in STAKEHOLDERS
    ]

    # C8: Engagement tactics for Manage Closely stakeholders
    engagement_tactics = []
    for s in STAKEHOLDERS:
        if s["correct_quadrant"] == "manage_closely" and s.get("engagement_tactics"):
            engagement_tactics.append({
                "stakeholder_id": s["id"],
                "stakeholder_name": s["name"],
                "tactics": [
                    {"id": t["id"], "label": t["label"], "correct": t["correct"], "rationale": t["rationale"]}
                    for t in s["engagement_tactics"]
                ],
            })

    return {
        "accuracy_percentage": round(accuracy * 100, 1),
        "correct_count": correct_count,
        "total_count": total,
        "passed": passed,
        "points_awarded": points_awarded,
        "scoring_tier": scoring_tier,
        "reputation_penalty": reputation_penalty,
        "treasury_penalty": treasury_penalty,
        "details": details,
        "master_mapping": MASTER_MAP,
        "urgency_debrief": urgency_debrief,
        "engagement_tactics": engagement_tactics,
    }


def get_stakeholder_list() -> list[dict]:
    """Return stakeholders WITHOUT correct_quadrant (for the frontend bank).
    C15: Includes intel_dossier for pre-classification analysis."""
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "icon": s["icon"],
            "description": s["description"],
            "intel_dossier": s.get("intel_dossier", []),
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
        "scoring_tiers": [
            {"threshold": t[0], "points": t[1], "label": t[2]} for t in SCORING_TIERS
        ],
        "failure_reputation_penalty": FAILURE_REPUTATION_PENALTY,
        "poor_analysis_treasury_penalty": POOR_ANALYSIS_TREASURY_PENALTY,
    }


# ═══════════════════════════════════════════════════════════════
#  C7: DYNAMIC SALIENCE MIGRATION (Ackermann & Eden 2011)
#
#  Stakeholder power/interest is NOT static. Crisis events,
#  regulatory actions, and market signals shift salience over
#  time. Each migration rule specifies:
#    - round: which round triggers the check
#    - stakeholder: who moves
#    - from_quadrant → to_quadrant: the shift
#    - condition: a lambda on global_state flags that must be True
#    - narrative: why it happened (shown to player)
#    - theory_note: academic reference for the facilitator
# ═══════════════════════════════════════════════════════════════

SALIENCE_MIGRATIONS: list[dict[str, Any]] = [
    # ── Round 4: Contagion Crisis ──────────────────────────────
    # The crisis event makes previously low-salience stakeholders
    # suddenly high-interest or high-power.
    {
        "round": 4,
        "stakeholder": "gen_public",
        "from_quadrant": "monitor",
        "to_quadrant": "manage_closely",
        "condition_flags": [],  # always triggers in R4
        "narrative": (
            "The supply chain scandal went viral on social media. "
            "General public awareness of Muressons surged from 4% to 62% "
            "in 48 hours. Consumer boycott threats are now credible."
        ),
        "theory_note": (
            "Mitchell et al. (1997): Dormant stakeholders acquire URGENCY "
            "through crisis events, shifting from latent to definitive salience."
        ),
    },
    {
        "round": 4,
        "stakeholder": "local_media",
        "from_quadrant": "monitor",
        "to_quadrant": "manage_closely",
        "condition_flags": [],  # always triggers in R4
        "narrative": (
            "The regional business journalist broke the story nationally. "
            "Their investigation is now syndicated across 3 major outlets. "
            "They hold the power to control the narrative."
        ),
        "theory_note": (
            "Ackermann & Eden (2011): Media stakeholders have 'latent power' — "
            "dormant until activated by a crisis. Once activated, they become "
            "context setters who shape all other stakeholder responses."
        ),
    },
    {
        "round": 4,
        "stakeholder": "cafeteria_vendors",
        "from_quadrant": "monitor",
        "to_quadrant": "keep_informed",
        "condition_flags": [],  # always triggers in R4
        "narrative": (
            "Cafeteria staff are reporting declining foot traffic as employees "
            "work from home to avoid media scrutiny at the office. Their "
            "commercial interest in Muressons has increased."
        ),
        "theory_note": (
            "Freeman (2010): Even peripheral stakeholders are affected by "
            "systemic crises. Their interest shifts, even if power remains low."
        ),
    },

    # ── Round 6: NGO Campaign / Regulatory Escalation ─────────
    {
        "round": 6,
        "stakeholder": "local_communities",
        "from_quadrant": "keep_informed",
        "to_quadrant": "manage_closely",
        "condition_flags": [],  # always triggers in R6
        "narrative": (
            "An international NGO has adopted the Deccan water rights case. "
            "The community now has legal representation, media amplification, "
            "and a credible threat of operational injunction."
        ),
        "theory_note": (
            "Mitchell et al. (1997): Communities acquired POWER through "
            "NGO alliance — shifting from dependent to definitive stakeholder. "
            "This is the classic 'coalition formation' salience shift."
        ),
    },
    {
        "round": 6,
        "stakeholder": "syndicate_banks",
        "from_quadrant": "keep_satisfied",
        "to_quadrant": "manage_closely",
        "condition_flags": ["electronics_blindspot"],
        "narrative": (
            "The syndicate banks' ESG desk has flagged Muressons for review "
            "after the R4 scandal. Covenant renegotiation is now on the table. "
            "Their interest has shifted from passive to active."
        ),
        "theory_note": (
            "Mendelow (1991): 'Keep Satisfied' stakeholders shift to 'Manage "
            "Closely' when an event activates their latent interest. The "
            "electronics blindspot failure was that activating event."
        ),
    },

    # ── Round 9: Labour Crisis / Just Transition ──────────────
    {
        "round": 9,
        "stakeholder": "factory_employees",
        "from_quadrant": "keep_informed",
        "to_quadrant": "manage_closely",
        "condition_flags": [],  # always triggers in R9
        "narrative": (
            "Factory workers have voted to authorise a strike. Union membership "
            "is now at 78%. Their collective bargaining power has transformed "
            "them from a voice to hear into a force to manage."
        ),
        "theory_note": (
            "Mitchell et al. (1997): Workers acquired POWER through unionisation. "
            "Combined with their existing high LEGITIMACY and newly activated "
            "URGENCY (strike deadline), they are now definitive stakeholders."
        ),
    },
    {
        "round": 9,
        "stakeholder": "tier3_miners",
        "from_quadrant": "keep_informed",
        "to_quadrant": "manage_closely",
        "condition_flags": [],  # always triggers in R9
        "narrative": (
            "The ILO investigation has escalated to a formal enforcement action. "
            "Supply chain due diligence legislation (EU CS3D) now gives "
            "Tier-3 workers legal standing to claim against Muressons directly."
        ),
        "theory_note": (
            "Legitimacy alone was insufficient for power. EU CS3D gave "
            "these stakeholders regulatory-backed POWER, transforming them "
            "from dependent to definitive (Mitchell et al. 1997)."
        ),
    },
]


def get_migrations_for_round(round_number: int) -> list[dict]:
    """Return all migration rules that trigger at the given round."""
    return [m for m in SALIENCE_MIGRATIONS if m["round"] == round_number]


def apply_salience_migrations(
    round_number: int,
    global_state: dict,
) -> list[dict[str, Any]]:
    """
    Check and apply salience migrations for the current round.

    Reads from global_state["stakeholder_salience_current"] (initialised from
    the R1 master map if absent) and writes back the updated salience map.

    Returns a list of migration events that fired (for display in the cockpit).
    """
    # Initialise current salience from R1 master if not yet set
    if "stakeholder_salience_current" not in global_state:
        global_state["stakeholder_salience_current"] = dict(MASTER_MAP)

    current = global_state["stakeholder_salience_current"]
    all_flags = set()
    flags_dict = global_state.get("active_event_flags", {})
    if isinstance(flags_dict, dict):
        for k, v in flags_dict.items():
            if isinstance(v, list):
                # Only add hashable items (skip nested dicts)
                for item in v:
                    if isinstance(item, str):
                        all_flags.add(item)
            elif isinstance(v, str):
                all_flags.add(v)
            elif isinstance(v, bool) and v:
                pass  # flag presence is the key itself
            # Skip dict/int/float values — they aren't flag identifiers
        all_flags.update(flags_dict.keys())

    migrations_fired = []
    history_key = "salience_migration_history"
    if history_key not in global_state:
        global_state[history_key] = []

    for rule in get_migrations_for_round(round_number):
        sid = rule["stakeholder"]
        # Skip if already migrated to this quadrant
        if current.get(sid) == rule["to_quadrant"]:
            continue

        # Check condition flags (empty = unconditional)
        if rule["condition_flags"]:
            if not all(f in all_flags for f in rule["condition_flags"]):
                continue

        # Apply migration
        old_quadrant = current.get(sid, rule["from_quadrant"])
        current[sid] = rule["to_quadrant"]

        stakeholder_data = next((s for s in STAKEHOLDERS if s["id"] == sid), None)
        event = {
            "stakeholder_id": sid,
            "stakeholder_name": stakeholder_data["name"] if stakeholder_data else sid,
            "stakeholder_icon": stakeholder_data["icon"] if stakeholder_data else "•",
            "from_quadrant": old_quadrant,
            "to_quadrant": rule["to_quadrant"],
            "round": round_number,
            "narrative": rule["narrative"],
            "theory_note": rule["theory_note"],
        }
        migrations_fired.append(event)
        global_state[history_key].append(event)

    global_state["stakeholder_salience_current"] = current
    return migrations_fired

