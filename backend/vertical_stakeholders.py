"""
Muressons — Vertical-Specific Stakeholder Sets
Industry-appropriate stakeholders for BU substitution verticals.
Same quadrant distribution as default: 2×MC, 3×KI, 2×KS, 2×MON, 1×AMB
"""
from __future__ import annotations
from typing import Any

# ═══════════════════════════════════════════════════════════════
#  TECHNOLOGY VERTICAL STAKEHOLDERS
# ═══════════════════════════════════════════════════════════════

TECHNOLOGY_STAKEHOLDERS = [
    # Q1 — Manage Closely (High Power / High Interest)
    {
        "id": "data_protection_authority",
        "name": "EU Data Protection Authority",
        "icon": "🏛️",
        "description": (
            "Issued a formal inquiry into your cloud platform's cross-border data transfers "
            "following Schrems III. Scheduled a mandatory compliance audit of the Frankfurt "
            "data centre for Q3. Fined a peer company €20M for GDPR violations last year."
        ),
        "correct_quadrant": "manage_closely",
        "urgency": "high", "legitimacy": "high",
        "urgency_rationale": "Formal inquiry with Q3 audit deadline. Regulatory clock is ticking.",
        "intel_dossier": [
            "📰 Politico EU: 'DPA signals tougher enforcement of AI Act for hyperscaler platforms'",
            "📰 FT: 'EU regulator fines CloudCorp €20M for inadequate data localisation'",
            "📰 Reuters: 'Muressons Technology added to priority review list for 2025 AI Act compliance'",
        ],
        "engagement_tactics": [
            {"id": "proactive_dpia", "label": "Submit voluntary Data Protection Impact Assessment ahead of deadline", "correct": True,
             "rationale": "Demonstrates good faith, may reduce penalty severity if gaps remain."},
            {"id": "lobby_delay", "label": "Hire Brussels lobbyists to delay enforcement timeline", "correct": False,
             "rationale": "Regulatory capture attempt — reputational disaster if leaked."},
            {"id": "wait_findings", "label": "Wait for audit and respond only to specific findings", "correct": False,
             "rationale": "Reactive posture invites maximum penalty exposure."},
        ],
    },
    {
        "id": "activist_tech_fund",
        "name": "TechEthics Activist Fund",
        "icon": "🦅",
        "description": (
            "Filed 2 shareholder resolutions demanding AI ethics disclosure and energy transparency. "
            "Currently building a 6% blocking stake and publicly threatening a board challenge "
            "at the next AGM over data centre carbon emissions."
        ),
        "correct_quadrant": "manage_closely",
        "urgency": "high", "legitimacy": "high",
        "urgency_rationale": "Active proxy fight with AGM deadline in 90 days.",
        "intel_dossier": [
            "📰 FT: 'TechEthics acquires 4.8% Muressons stake, signals intent to force AI governance vote'",
            "📰 Bloomberg: 'Activist fund proxy materials demand 2 independent AI ethics directors'",
            "📰 Reuters: 'TechEthics hires ex-IEEE ethics board chair as strategic advisor'",
        ],
        "engagement_tactics": [
            {"id": "ethics_board", "label": "Offer board seats to fund nominees on AI Ethics Committee", "correct": True,
             "rationale": "Co-opts the activist into governance, converting adversary to partner."},
            {"id": "buyback", "label": "Launch share buyback to dilute their stake", "correct": False,
             "rationale": "Defensive financial engineering — signals fear, not engagement."},
            {"id": "public_letter", "label": "Publish open letter rejecting their demands", "correct": False,
             "rationale": "Confrontational stance that mobilises other investors against management."},
        ],
    },
    # Q2 — Keep Informed (Low Power / High Interest)
    {
        "id": "open_source_community",
        "name": "Open Source Developer Community",
        "icon": "👩‍💻",
        "description": (
            "A coalition of 5,000 open-source contributors has published an open letter "
            "demanding Muressons release its foundational AI model weights. Internal "
            "developer satisfaction survey shows 45% support the open-source movement."
        ),
        "correct_quadrant": "keep_informed",
        "urgency": "medium", "legitimacy": "high",
        "urgency_rationale": "Growing internal sympathy creates latent talent flight risk.",
        "intel_dossier": [
            "📰 Hacker News: 'Open letter to Muressons: Release the weights — 5K signatures'",
            "📰 The Verge: 'Developer community threatens fork of Muressons SDK over licensing dispute'",
            "📰 Internal Pulse: '45% of engineers support open-sourcing foundational models'",
        ],
    },
    {
        "id": "gig_workers",
        "name": "Platform Gig Workers",
        "icon": "📱",
        "description": (
            "Contracted content moderators in the Philippines report 14-hour shifts reviewing "
            "harmful content without mental health support. An ILO observer has flagged the site. "
            "Workers are organising through an informal digital union."
        ),
        "correct_quadrant": "keep_informed",
        "urgency": "medium", "legitimacy": "high",
        "urgency_rationale": "ILO flag creates latent exposure. High moral legitimacy.",
        "intel_dossier": [
            "📰 Guardian: 'Content moderators at tech firms report PTSD at epidemic levels'",
            "📰 BBC: 'ILO observer flags safety violations at Philippines outsourcing hub'",
            "📰 Rest of World: 'Gig workers organise first digital union in Southeast Asia'",
        ],
    },
    {
        "id": "tech_employees",
        "name": "Engineering Workforce",
        "icon": "👷",
        "description": (
            "Senior engineers submitted a formal grievance about mandatory on-call rotations "
            "and AI-generated performance reviews. Internal pulse survey shows 58% 'dissatisfied'. "
            "LinkedIn profiles with 'open to work' badges increased 22% this quarter."
        ),
        "correct_quadrant": "keep_informed",
        "urgency": "medium", "legitimacy": "high",
        "urgency_rationale": "Rising attrition signals and collective grievance filed.",
        "intel_dossier": [
            "📰 Internal Memo: 'Q3 pulse survey — 58% dissatisfaction, highest in 4 years'",
            "📰 Blind App: 'Muressons engineers report burnout at 2× industry average'",
            "📰 HR Brief: 'Formal grievance filed re: AI-generated performance reviews'",
        ],
    },
    # Q3 — Keep Satisfied (High Power / Low Interest)
    {
        "id": "cloud_enterprise_clients",
        "name": "Enterprise Cloud Clients",
        "icon": "🏢",
        "description": (
            "Top 10 enterprise clients (representing 40% of ARR) sent routine contract "
            "renewal letters. No flags raised. Their procurement teams published a sector "
            "note on vendor ESG compliance but did not mention Muressons specifically."
        ),
        "correct_quadrant": "keep_satisfied",
        "urgency": "low", "legitimacy": "high",
        "urgency_rationale": "No contract breach imminent. Routine engagement sufficient.",
        "intel_dossier": [
            "📰 CIO Magazine: 'Enterprise clients tighten ESG clauses in cloud vendor contracts'",
            "📰 Internal Sales: 'Annual contract review — all SLAs met. Next review Q2 2026'",
            "📰 Gartner: 'Cloud vendor ESG ratings — Muressons rated 'neutral' in latest MQ'",
        ],
    },
    {
        "id": "sovereign_wealth_fund",
        "name": "Sovereign Wealth Fund Investors",
        "icon": "🏦",
        "description": (
            "Hold $1.8B in long-term equity positions with ESG covenant triggers. "
            "Sent a routine annual review letter — no flags raised. Their responsible "
            "investment team published a tech sector note last month but did not flag Muressons."
        ),
        "correct_quadrant": "keep_satisfied",
        "urgency": "low", "legitimacy": "high",
        "urgency_rationale": "No covenant breach imminent. Routine engagement sufficient.",
        "intel_dossier": [
            "📰 FT: 'Sovereign funds tighten ESG screening for tech holdings'",
            "📰 Internal IR: 'Annual SWF review — all covenants met. Next review Q2 2026'",
            "📰 PRI Report: 'Tech sector rated 'developing' on responsible AI governance'",
        ],
    },
    # Q4 — Monitor (Low Power / Low Interest)
    {
        "id": "campus_food_vendors",
        "name": "Campus Food Service Vendors",
        "icon": "🍽️",
        "description": (
            "Renewed their annual catering contract last month without negotiation. "
            "Serve approximately 1,200 meals/day across 2 tech campuses. "
            "Have never attended a supplier engagement session."
        ),
        "correct_quadrant": "monitor",
        "urgency": "low", "legitimacy": "low",
        "urgency_rationale": "No claims, no engagement, no influence pathway.",
        "intel_dossier": [
            "📰 Procurement Log: 'Campus food contract auto-renewed — $1.8M annual'",
            "📰 No external media coverage",
            "📰 Supplier Survey: 'Food vendors did not respond to annual ESG questionnaire'",
        ],
    },
    {
        "id": "tech_general_public",
        "name": "General Public",
        "icon": "👥",
        "description": (
            "Consumer awareness survey shows 6% unaided brand awareness for Muressons Technology. "
            "No trending social media mentions this period. A B2B cloud/AI platform, Muressons "
            "products are rarely used directly by end consumers."
        ),
        "correct_quadrant": "monitor",
        "urgency": "low", "legitimacy": "low",
        "urgency_rationale": "Negligible brand awareness. B2B model limits public salience.",
        "intel_dossier": [
            "📰 Brand Tracker Q3: '6% unaided awareness — unchanged from Q2'",
            "📰 Social Listening: '18 mentions on Twitter/X this month (vs. 120K for Google)'",
            "📰 No consumer-facing product incidents on record",
        ],
    },
    # AMBIGUOUS STAKEHOLDER — accepts 2 quadrants
    {
        "id": "tech_journalist",
        "name": "AI Ethics Investigative Journalist",
        "icon": "📰",
        "description": (
            "A well-connected investigative reporter at a major tech publication has been "
            "requesting interviews with the CTO about AI model training data. Published 3 "
            "articles about competitor AI ethics failures last month. Has 120K followers on "
            "X/Twitter and a track record of stories triggering congressional hearings."
        ),
        "correct_quadrant": "monitor",
        "alternate_quadrant": "keep_informed",
        "alternate_rationale": (
            "Reasonable case for 'Keep Informed': their track record of triggering "
            "congressional hearings means a negative story could rapidly escalate. "
            "Proactive engagement could convert them into an ally. Mitchell et al. (1997) "
            "would classify this stakeholder as having latent power activated by urgency."
        ),
        "urgency": "medium", "legitimacy": "medium",
        "urgency_rationale": "No immediate deadline, but investigative interest creates latent exposure.",
        "intel_dossier": [
            "📰 Press Office: 'Interview request from S. Chen, Wired — 4th request this quarter'",
            "📰 Media Monitor: 'S. Chen's AI bias investigation syndicated to NYT (reach: 8M)'",
            "📰 X/Twitter: 'Reporter's thread on tech worker exploitation got 25K engagements'",
        ],
    },
]

# Technology salience migrations (equivalent to default R4/R6/R9 shifts)
TECHNOLOGY_SALIENCE_MIGRATIONS = [
    {
        "round": 4, "stakeholder": "tech_general_public",
        "from_quadrant": "monitor", "to_quadrant": "manage_closely",
        "condition_flags": [],
        "narrative": (
            "The AI training data scandal went viral. Public awareness of Muressons "
            "surged from 6% to 58% in 48 hours. #DeleteMuressons is trending globally."
        ),
        "theory_note": "Mitchell et al. (1997): Dormant stakeholders acquire URGENCY through crisis events.",
    },
    {
        "round": 4, "stakeholder": "tech_journalist",
        "from_quadrant": "monitor", "to_quadrant": "manage_closely",
        "condition_flags": [],
        "narrative": (
            "The AI ethics journalist broke the story internationally. Their investigation "
            "triggered a congressional hearing request. They control the narrative."
        ),
        "theory_note": "Ackermann & Eden (2011): Media stakeholders have 'latent power' activated by crisis.",
    },
    {
        "round": 4, "stakeholder": "campus_food_vendors",
        "from_quadrant": "monitor", "to_quadrant": "keep_informed",
        "condition_flags": [],
        "narrative": (
            "Campus food vendors report declining foot traffic as engineers work remotely "
            "to avoid media scrutiny at the office."
        ),
        "theory_note": "Freeman (2010): Even peripheral stakeholders are affected by systemic crises.",
    },
    {
        "round": 6, "stakeholder": "open_source_community",
        "from_quadrant": "keep_informed", "to_quadrant": "manage_closely",
        "condition_flags": [],
        "narrative": (
            "The open-source community has partnered with the EFF to file an antitrust "
            "complaint. They now have legal representation and media amplification."
        ),
        "theory_note": "Mitchell et al. (1997): Communities acquired POWER through NGO alliance.",
    },
    {
        "round": 6, "stakeholder": "sovereign_wealth_fund",
        "from_quadrant": "keep_satisfied", "to_quadrant": "manage_closely",
        "condition_flags": ["data_centre_blindspot"],
        "narrative": (
            "Sovereign wealth funds' ESG desk flagged Muressons for review after the "
            "R4 scandal. Divestment is now on the table."
        ),
        "theory_note": "Mendelow (1991): 'Keep Satisfied' shifts to 'Manage Closely' when interest activates.",
    },
    {
        "round": 9, "stakeholder": "tech_employees",
        "from_quadrant": "keep_informed", "to_quadrant": "manage_closely",
        "condition_flags": [],
        "narrative": (
            "Engineers have voted to authorise a work-to-rule action. Senior talent "
            "attrition hit 35%. Their collective bargaining power has transformed."
        ),
        "theory_note": "Mitchell et al. (1997): Workers acquired POWER through collective action.",
    },
    {
        "round": 9, "stakeholder": "gig_workers",
        "from_quadrant": "keep_informed", "to_quadrant": "manage_closely",
        "condition_flags": [],
        "narrative": (
            "The ILO investigation escalated to formal enforcement. EU Platform Work "
            "Directive gives gig workers legal standing to claim against Muressons."
        ),
        "theory_note": "EU Platform Work Directive gave these stakeholders regulatory-backed POWER.",
    },
]


# ═══════════════════════════════════════════════════════════════
#  REGISTRY — maps vertical IDs to their stakeholder data
# ═══════════════════════════════════════════════════════════════

# Import verticals from the verticals package
from verticals import (
    OIL_GAS_STAKEHOLDERS, OIL_GAS_SALIENCE_MIGRATIONS,
    BANKING_FS_STAKEHOLDERS, BANKING_FS_SALIENCE_MIGRATIONS,
    RETAIL_FMCG_STAKEHOLDERS, RETAIL_FMCG_SALIENCE_MIGRATIONS,
    AGRICULTURE_STAKEHOLDERS, AGRICULTURE_SALIENCE_MIGRATIONS,
)

VERTICAL_STAKEHOLDER_SETS = {
    "technology": TECHNOLOGY_STAKEHOLDERS,
    "oil_gas": OIL_GAS_STAKEHOLDERS,
    "banking_financial_services": BANKING_FS_STAKEHOLDERS,
    "retail_fmcg": RETAIL_FMCG_STAKEHOLDERS,
    "agriculture": AGRICULTURE_STAKEHOLDERS,
}

VERTICAL_SALIENCE_MIGRATIONS = {
    "technology": TECHNOLOGY_SALIENCE_MIGRATIONS,
    "oil_gas": OIL_GAS_SALIENCE_MIGRATIONS,
    "banking_financial_services": BANKING_FS_SALIENCE_MIGRATIONS,
    "retail_fmcg": RETAIL_FMCG_SALIENCE_MIGRATIONS,
    "agriculture": AGRICULTURE_SALIENCE_MIGRATIONS,
}


def get_stakeholders_for_vertical(vertical_id: str) -> list[dict] | None:
    """Return the stakeholder set for a vertical, or None if not yet authored."""
    return VERTICAL_STAKEHOLDER_SETS.get(vertical_id)


def get_migrations_for_vertical(vertical_id: str) -> list[dict]:
    """Return salience migrations for a vertical, or empty list."""
    return VERTICAL_SALIENCE_MIGRATIONS.get(vertical_id, [])

