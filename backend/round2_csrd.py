"""
Muressons Global Corporation — Round 2 Data Dictionary
20 CSRD Materiality Issues configured for the Double Materiality Matrix

ESRS 1 Compliance:
  - Each issue carries severity/likelihood/time_horizon metadata
    reflecting the spectrum-based assessment required by ESRS 1 §1.51-1.61
  - Q2 issues flagged with disclosure_required=True (impact materiality alone
    triggers ESRS S1, S2, E1-E5 disclosure obligations)
  - Electronics issues flagged with electronics_sensitive=True for R1 blindspot
    intelligence modulation
"""

# ── Canonical CSRD Issues (used for scoring validation) ───────────────────────
# These are the 20 issues displayed in the default Muressons simulation.
# severity: scale of harm (ESRS 1 threshold) | likelihood: probability of occurrence
# time_horizon: short/medium/long (per ESRS 1 §1.8)
# disclosure_required: True if impact materiality alone triggers mandatory disclosure
# electronics_sensitive: True if R1 audit blindspot degrades description fidelity
CSRD_ISSUES = {
    # ── Quadrant 1 (High Fin/High Impact — Doubly Material) ──────────────────
    "water_scarcity": {
        "id": "water_scarcity",
        "title": "Water Scarcity in Deccan Plateau",
        "hover_description": (
            "Your Pharma BU draws 40M litres/yr from an over-exploited aquifer. "
            "Local agriculture communities depend on the same source. Severity: HIGH "
            "(irreversible ecosystem damage). Time horizon: SHORT (drought imminent). "
            "ESRS E3 disclosure mandatory."
        ),
        "blindspot_description": "Water risk indicator — insufficient audit data to assess severity.",
        "correct_quadrant": 1,
        "severity": "high", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS E3 (Water & Marine Resources)",
        "stakeholder_voice": "local_communities",  # R1 stakeholder map connection
    },
    "e_waste": {
        "id": "e_waste",
        "title": "E-Waste & Toxic Mineral Runoff",
        "hover_description": (
            "Electronics BU generates 1,200 tonnes/yr of unprocessed e-waste. "
            "Lead, cadmium, and mercury leaching into groundwater near factory sites. "
            "EU WEEE Directive Phase III enforcement begins 2026. Severity: HIGH. "
            "Time horizon: SHORT. ESRS E2 disclosure mandatory."
        ),
        "blindspot_description": "Impact unknown — insufficient audit data from Electronics BU.",
        "correct_quadrant": 1,
        "severity": "high", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": True,
        "esrs_reference": "ESRS E2 (Pollution) / WEEE Directive Phase III",
        "stakeholder_voice": None,
    },
    "tier3_labor": {
        "id": "tier3_labor",
        "title": "Tier-3 Supply Chain Labor Practices",
        "hover_description": (
            "Independent audits flagged 14-hour shifts and withheld wages at 3 tier-3 "
            "suppliers in Southeast Asia. EU CSDDD enters force 2025 — civil liability "
            "exposure for parent company. Severity: HIGH (fundamental rights). "
            "Time horizon: SHORT-MEDIUM. ESRS S2 mandatory."
        ),
        "blindspot_description": "Supply chain labour conditions — audit scope did not reach Tier-3.",
        "correct_quadrant": 1,
        "severity": "high", "likelihood": "medium", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": True,
        "esrs_reference": "ESRS S2 (Workers in Value Chain) / EU CSDDD",
        "stakeholder_voice": "suppliers",
    },
    "ai_bias": {
        "id": "ai_bias",
        "title": "AI Algorithmic Bias & Redlining",
        "hover_description": (
            "Software BU's recruitment AI systematically deprioritises candidates from "
            "postcodes with ethnic minority majorities. EU AI Act (High-Risk AI Systems) "
            "triggers fines up to €30M or 6% global revenue. Severity: HIGH. "
            "Time horizon: SHORT. ESRS S1 / EU AI Act mandatory."
        ),
        "blindspot_description": "AI system risk classification — data insufficient for impact assessment.",
        "correct_quadrant": 1,
        "severity": "high", "likelihood": "medium", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS S1 (Own Workforce) / EU AI Act Art. 9",
        "stakeholder_voice": "employees",
    },
    "scope3_carbon": {
        "id": "scope3_carbon",
        "title": "Scope 3 Carbon Emissions",
        "hover_description": (
            "Your supply chain generates 4× more CO₂ than direct operations. "
            "At $250/tCO₂ terminal carbon tax rate, current trajectory costs $18M at "
            "R10. SBTi 1.5°C pathway requires 4.2%/yr Scope 3 reduction. "
            "Time horizon: LONG but compounding. ESRS E1 mandatory."
        ),
        "blindspot_description": "Upstream emission profile — energy audit data unavailable.",
        "correct_quadrant": 1,
        "severity": "high", "likelihood": "high", "time_horizon": "long",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS E1 (Climate Change) / GHG Protocol Scope 3",
        "stakeholder_voice": None,
    },
    "plastic_packaging": {
        "id": "plastic_packaging",
        "title": "End-of-Life Plastic Packaging",
        "hover_description": (
            "Consumer Goods BU ships 4,200 tonnes of non-recyclable packaging/yr. "
            "EU Extended Producer Responsibility (EPR) levy of 15% on non-recyclable "
            "packaging takes effect 2025. Ocean microplastics create reputational and "
            "regulatory exposure. Severity: HIGH. Time horizon: SHORT. ESRS E5 mandatory."
        ),
        "blindspot_description": "Packaging waste stream composition — product lifecycle data missing.",
        "correct_quadrant": 1,
        # F-5: borderline — the financial axis hinges on the EPR levy's
        # enforcement timing; arguable Q1 vs Q2.
        "is_ambiguous": True,
        "severity": "medium", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS E5 (Resource Use & Circular Economy) / EU EPR",
        "stakeholder_voice": "local_communities",
    },

    # ── Quadrant 2 (Low Fin/High Impact) — Disclosure-Only Issues ────────────
    # These are ESRS-material from an impact perspective (mandatory disclosure under
    # ESRS S1, S2) but require DISCLOSURE INVESTMENT, not capex.
    "employee_volunteering": {
        "id": "employee_volunteering",
        "title": "Generic Employee Volunteering",
        "hover_description": (
            "Currently unstructured. While financially immaterial, ESRS S1 §65 requires "
            "disclosure of community engagement policies. Requires: data collection "
            "system (~$120K/yr) and assurance. No capex, but disclosure investment needed."
        ),
        "blindspot_description": "Community engagement data — employee survey not conducted.",
        "correct_quadrant": 2,
        "severity": "low", "likelihood": "low", "time_horizon": "long",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS S1 §65 (Community Engagement)",
        "disclosure_investment_usd": 120_000,
        "stakeholder_voice": "employees",
    },
    "philanthropy": {
        "id": "philanthropy",
        "title": "Corporate Philanthropy & Local Schools",
        "hover_description": (
            "Education donations create real community impact. Financially immaterial "
            "(<0.1% revenue) but ESRS S3 (Affected Communities) requires disclosure. "
            "Disclosure cost: $80K for data collection and social impact measurement."
        ),
        "blindspot_description": "Community investment data — insufficient documentation.",
        "correct_quadrant": 2,
        # F-5: borderline — real community impact but financially immaterial;
        # arguable Q2 vs Q4.
        "is_ambiguous": True,
        "severity": "medium", "likelihood": "high", "time_horizon": "medium",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS S3 (Affected Communities)",
        "disclosure_investment_usd": 80_000,
        "stakeholder_voice": "local_communities",
    },
    "open_source_ai": {
        "id": "open_source_ai",
        "title": "Open-Sourcing Proprietary AI for NGOs",
        "hover_description": (
            "Releasing AI tools to NGOs creates genuine positive impact on public services. "
            "Financially immaterial but generates social license value. ESRS G1 §37 "
            "requires disclosure of how products serve societal purposes. "
            "Disclosure cost: $60K for impact measurement."
        ),
        "blindspot_description": "AI social impact metrics — measurement framework not established.",
        "correct_quadrant": 2,
        "severity": "medium", "likelihood": "medium", "time_horizon": "medium",
        "disclosure_required": True, "electronics_sensitive": False,
        "esrs_reference": "ESRS G1 (Business Conduct) §37",
        "disclosure_investment_usd": 60_000,
        "stakeholder_voice": None,
    },
    "living_wage": {
        "id": "living_wage",
        "title": "Living Wage Standardization across Tier-4",
        "hover_description": (
            "Gap between minimum wage and living wage at Tier-4 suppliers affects ~8,000 "
            "workers. High societal severity (fundamental right to dignified living). "
            "ESRS S2 mandatory disclosure. Financial impact is low (indirect). "
            "Requires supplier engagement programme: $200K disclosure + stakeholder cost."
        ),
        "blindspot_description": "Tier-4 wage data — supply chain audit did not reach this depth.",
        "correct_quadrant": 2,
        # F-5: genuinely borderline — high societal severity, low/indirect
        # financial impact; arguable Q1 vs Q2. Earns half credit when placed
        # in an adjacent quadrant (assurance signal: ambiguous_handled).
        "is_ambiguous": True,
        "severity": "high", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": True, "electronics_sensitive": True,
        "esrs_reference": "ESRS S2 (Workers in Value Chain) — wage adequacy",
        "disclosure_investment_usd": 200_000,
        "stakeholder_voice": "suppliers",
    },

    # ── Quadrant 3 (High Fin/Low Impact) ─────────────────────────────────────
    "semi_prices": {
        "id": "semi_prices",
        "title": "Raw Semiconductor Price Volatility",
        "hover_description": (
            "Spot prices for NAND and DRAM have swung ±35% in 18 months. High financial "
            "risk to Electronics BU margin. Not a CSRD impact materiality issue — no "
            "significant environmental or social harm from price fluctuation. "
            "ESRS disclosure: financial risk only (ESRS 2 §SBM-3)."
        ),
        "blindspot_description": "Semiconductor supply exposure — Electronics BU audit data missing.",
        "correct_quadrant": 3,
        "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": True,
        "esrs_reference": "ESRS 2 §SBM-3 (Material Risks)",
        "stakeholder_voice": None,
    },
    "software_competitor": {
        "id": "software_competitor",
        "title": "Consumer Shift to Competitor Software",
        "hover_description": (
            "Three AI-native competitors have taken 12% market share in 18 months. "
            "High financial risk (revenue erosion). Low societal impact — purely competitive "
            "market dynamics. Not an ESRS impact materiality issue."
        ),
        "blindspot_description": "Market share data — competitive intelligence not included in audit.",
        "correct_quadrant": 3,
        "severity": "low", "likelihood": "medium", "time_horizon": "medium",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": "ESRS 2 §SBM-3 (Competitive Risk)",
        "stakeholder_voice": None,
    },
    "currency_exchange": {
        "id": "currency_exchange",
        "title": "Currency Exchange Rate Fluctuations",
        "hover_description": (
            "USD/EUR and USD/INR volatility creates ±8% revenue swing on international "
            "sales. Pure financial risk. No societal or environmental harm. "
            "Hedge via forward contracts. Not ESRS impact-material."
        ),
        "blindspot_description": "FX exposure — treasury data review needed.",
        "correct_quadrant": 3,
        "severity": "low", "likelihood": "medium", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": "ESRS 2 §SBM-3 (Financial Risk)",
        "stakeholder_voice": None,
    },
    "eu_tax": {
        "id": "eu_tax",
        "title": "Corporate Tax Rate Changes in EU",
        "hover_description": (
            "EU Pillar Two global minimum tax (15%) affects Muressons' Irish holding "
            "structure. Significant financial exposure: est. €4M additional tax liability. "
            "No environmental/social harm. Governance disclosure required under ESRS G1."
        ),
        "blindspot_description": "Tax structure exposure — group finance review required.",
        "correct_quadrant": 3,
        "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": "ESRS G1 §37 (Tax Transparency)",
        "stakeholder_voice": None,
    },

    # ── Quadrant 4 (Low Fin/Low Impact) ──────────────────────────────────────
    "paper_recycling": {
        "id": "paper_recycling",
        "title": "Office Paper Recycling at HQ",
        "hover_description": (
            "HQ recycles 4 tonnes of paper/yr. Negligible financial and environmental "
            "impact at group scale. Good practice but not CSRD-material. "
            "Not required for ESRS disclosure."
        ),
        "blindspot_description": "Office waste data — minor operational metric.",
        "correct_quadrant": 4,
        "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None,
        "stakeholder_voice": None,
    },
    "plastic_straws": {
        "id": "plastic_straws",
        "title": "Replacing Plastic Straws in Cafeteria",
        "hover_description": (
            "Estimated 12,000 single-use straws eliminated/yr. Positive optics but "
            "immaterial at group scale. Classic 'greenwashing distractor' — looks good, "
            "costs little, achieves little. Not ESRS-material."
        ),
        "blindspot_description": "Cafeteria waste — minor operational metric.",
        "correct_quadrant": 4,
        "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None,
        "stakeholder_voice": None,
    },
    "exec_travel": {
        "id": "exec_travel",
        "title": "Executive Travel Carbon Offsets",
        "hover_description": (
            "C-suite flights generate ~85 tCO₂/yr — <0.01% of total group emissions. "
            "Offsetting these is symbolic, not strategic. At $250/ton, this is $21,250/yr. "
            "Disclosure not required as not material. Allocating budget here is a "
            "governance red flag (optics over substance)."
        ),
        "blindspot_description": "Executive travel data — HR records required.",
        "correct_quadrant": 4,
        "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None,
        "stakeholder_voice": None,
    },
    "earth_day": {
        "id": "earth_day",
        "title": "Annual Earth Day Social Media Campaign",
        "hover_description": (
            "PR campaign generates goodwill but zero measurable ESG improvement. "
            "Risk: if Q1 issues are unaddressed, this campaign constitutes greenwashing "
            "under EU Green Claims Directive. Not ESRS-material."
        ),
        "blindspot_description": "PR spend data — marketing records needed.",
        "correct_quadrant": 4,
        "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": "EU Green Claims Directive (greenwashing risk if Q1 unresolved)",
        "stakeholder_voice": None,
    },
    "ergonomic_chairs": {
        "id": "ergonomic_chairs",
        "title": "Ergonomic Chairs for Developers",
        "hover_description": (
            "Improving workplace comfort is good HR practice. Financially negligible. "
            "No environmental impact. Not CSRD-material at group level. "
            "May qualify under ESRS S1 wellbeing disclosure — but not strategic capital."
        ),
        "blindspot_description": "Workplace ergonomics data — HR records needed.",
        "correct_quadrant": 4,
        "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None,
        "stakeholder_voice": None,
    },
    "led_bulbs": {
        "id": "led_bulbs",
        "title": "LED Bulb Swaps in Admin Offices",
        "hover_description": (
            "Saves ~8 tCO₂/yr and ~$4,000 in energy costs. Measurable but immaterial "
            "at group scale. Classic low-hanging fruit — fine to do, wrong to prioritise "
            "over Scope 3, e-waste, or water risk. Not ESRS-material."
        ),
        "blindspot_description": "Energy consumption data — utilities records needed.",
        "correct_quadrant": 4,
        "severity": "low", "likelihood": "high", "time_horizon": "short",
        "disclosure_required": False, "electronics_sensitive": False,
        "esrs_reference": None,
        "stakeholder_voice": None,
    },
}

ROUND_2_DEFAULT_CONFIG = {
    "round_2_config": {
        "total_materiality_budget": 15_000_000,
        # ── Disclosure Investment Sub-Budget ─────────────────────────────────
        # Q2 issues (High Impact/Low Financial) require mandatory ESRS disclosure
        # even without capex allocation. This budget covers:
        #   data collection systems, third-party assurance, stakeholder engagement
        # Separate from capex — not deducted from materiality_budget.
        "disclosure_investment_budget": 1_000_000,
        # ── Stakeholder Panel Survey — Multi-Group Model ─────────────────────
        # Each of the 4 ESRS §1.47 stakeholder groups can be commissioned
        # independently, once per Round 2. Fee: flat $750K per group.
        # Maximum total: $3M (all 4 groups).
        # Each group provides deterministic per-issue quadrant recommendations
        # based on its ESRS-aligned priority bias.
        "stakeholder_panel": {
            "enabled": True,
            "label": "Commission Stakeholder Panel Survey",
            "description": (
                "Engage independent stakeholder panels (Investors, Own Workforce, NGOs, "
                "Subject Matter Experts) to rate issues. Each group can be commissioned "
                "once per Round 2, revealing stakeholder-specific materiality perspectives "
                "modelled on ESRS 1 §1.47-1.50."
            ),
            # ── Legacy per-issue pricing (kept for backward compatibility) ────
            "base_fee_per_issue_usd": 250_000,
            "extended_fee_per_issue_usd": 500_000,
            "min_issues": 1,
            "max_issues": 8,
            "tier_break": 4,
            # ── Per-group panel config (multi-survey model) ───────────────────
            # Flat $750K per group; max $3M for all 4 groups.
            "groups": {
                "investors": {
                    "label": "\U0001f4b0 Investors",
                    "description": (
                        "Investors prioritise Q3 financial risks and transition risks (ESRS E1, G1). "
                        "They may underweight community and social impacts relative to NGOs."
                    ),
                    "esrs_ref": "ESRS \u00a71.47(a)",
                    "fee_usd": 750_000,
                    "color": "#6366f1",
                },
                "workers": {
                    "label": "\U0001f477 Own Workforce",
                    "description": (
                        "Own workforce focuses on S1 issues: fair wages, health & safety, "
                        "working conditions. Strong signal for internal impacts."
                    ),
                    "esrs_ref": "ESRS \u00a71.47(b)",
                    "fee_usd": 750_000,
                    "color": "#3b82f6",
                },
                "ngos": {
                    "label": "\U0001f30d NGOs / Communities",
                    "description": (
                        "NGOs and affected communities elevate Q2 environmental harms "
                        "(E3, E4, S2, S3). ESRS \u00a71.50: their views may conflict with investor "
                        "priorities \u2014 this tension is pedagogically important."
                    ),
                    "esrs_ref": "ESRS \u00a71.47(c)",
                    "fee_usd": 750_000,
                    "color": "#10b981",
                },
                "experts": {
                    "label": "\U0001f393 Subject Matter Experts",
                    "description": (
                        "Subject matter experts (academics, assurance providers) calibrate ESRS "
                        "topic mapping and materiality thresholds. They validate whether issues "
                        "are correctly classified under E1\u2013E5 and S1\u2013S4."
                    ),
                    "esrs_ref": "ESRS \u00a71.47(d)",
                    "fee_usd": 750_000,
                    "color": "#f59e0b",
                },
            },
        },
    }
}

# ── Q2 Disclosure Budget: Issues requiring disclosure investment ───────────────
# ── ESRS Assurance Readiness labels ──────────────────────────────────────────
# Shared by router.submit_materiality_matrix (provisional, at panel submit) and
# round_logic._post_r2_materiality (final, once the governance choice is known).
ASSURANCE_LABELS = {
    0: ("\u274c Not Assurance-Ready", "No board oversight, poor Q1 recall, and no Q2 disclosure. External assurance would be refused."),
    1: ("\u26a0\ufe0f Limited Readiness", "Partial compliance. Significant gaps remain before limited assurance is achievable."),
    2: ("\U0001f4cb Limited Assurance Pathway", "Meets minimum threshold for limited assurance under ISAE 3000. Requires improvement in governance and disclosure."),
    3: ("\u2705 Reasonable Assurance Candidate", "Strong recall and governance. Suitable for reasonable assurance with minor remediation of Q2 disclosure gaps."),
    4: ("\U0001f3c6 Exemplary ESRS Compliance", "Full board oversight, \u226580% Q1 recall, Q2 disclosure, and ambiguous issues handled correctly. Best-practice materiality process."),
}

Q2_DISCLOSURE_ISSUES = {
    iid: issue
    for iid, issue in CSRD_ISSUES.items()
    if issue.get("disclosure_required") and issue["correct_quadrant"] == 2
}

# ── Electronics-sensitive issues (affected by R1 blindspot flag) ──────────────
ELECTRONICS_SENSITIVE_ISSUES = {
    iid: issue
    for iid, issue in CSRD_ISSUES.items()
    if issue.get("electronics_sensitive")
}


# ── Panel Group Biases ─────────────────────────────────────────────────────────
# Deterministic perturbation rules per ESRS §1.47 stakeholder group.
# Bias keys:
#   "accurate"  → always returns the correct quadrant
#   "q3_push"   → social Q2 issues pushed to Q3 (investors underweigh community harm)
#   "q2_push"   → financial Q3 issues pushed to Q2 (NGOs surface community impact)
#   "s1_boost"  → workforce issues bumped to Q1 (workers amplify social priority)
_PANEL_GROUP_BIASES: dict[str, str] = {
    "investors": "q3_push",
    "workers":   "s1_boost",
    "ngos":      "q2_push",
    "experts":   "accurate",
}

# Issue sets for bias routing (must match IDs in CSRD_ISSUES)
_SOCIAL_ISSUE_IDS: set[str] = {
    "tier3_labor", "ai_bias", "living_wage", "employee_volunteering", "philanthropy"
}
_FINANCIAL_ISSUE_IDS: set[str] = {
    "semi_prices", "software_competitor", "currency_exchange", "eu_tax"
}


# ── Axis classification (F-6) ─────────────────────────────────────────────────
# ESRS 1 treats impact materiality and financial materiality as SEPARATE
# assessments: impact materiality is severity (scale, scope, irremediability)
# × likelihood of the impact; financial materiality is magnitude × likelihood
# of the financial effect. A single severity × likelihood product cannot
# express both: applying one product to each axis forces every issue onto the
# Q1/Q4 diagonal and makes Q2 and Q3 unreachable (that defect shipped —
# 3 of 8 DEFAULT_CONFIG issues were mis-scored, Q2/Q3 placements were marked
# wrong, and the Q2 disclosure budget could never unlock).
#
# Numeric scoring is therefore used ONLY when all four axis-specific fields
# are present. Otherwise the string labels govern — and the string labels are
# already the authority for q1_target_issue_ids, so this makes the round use
# ONE rule instead of two. No shipped dictionary carries the four dual-axis
# fields today, so every dictionary falls back to the string labels, while
# proper dual-axis scoring stays available for future configs.
ESRS_MAT_THRESHOLD = 12  # out of 25 (5x5)
_DUAL_AXIS_FIELDS = (
    "impact_severity_score", "impact_likelihood_score",
    "financial_magnitude_score", "financial_likelihood_score",
)


def _has_dual_axis_scores(issue: dict) -> bool:
    return all(issue.get(f) is not None for f in _DUAL_AXIS_FIELDS)


def mat_axis_is_high(issue: dict, axis: str) -> bool:
    """True if the given axis clears the ESRS significance threshold."""
    if _has_dual_axis_scores(issue):
        if axis == "fin":
            product = issue["financial_magnitude_score"] * issue["financial_likelihood_score"]
        else:
            product = issue["impact_severity_score"] * issue["impact_likelihood_score"]
        return product >= ESRS_MAT_THRESHOLD
    # Legacy single-pair severity_score/likelihood_score is NOT sufficient to
    # separate the axes and is deliberately ignored here.
    return issue.get("financial_impact" if axis == "fin" else "societal_impact") == "high"


def correct_quadrant_v2(issue: dict) -> str:
    """The round's ONE quadrant classifier (see mat_axis_is_high)."""
    h_fin = mat_axis_is_high(issue, "fin")
    h_imp = mat_axis_is_high(issue, "soc")
    if h_fin and h_imp:
        return "q1"
    if not h_fin and h_imp:
        return "q2"
    if h_fin and not h_imp:
        return "q3"
    return "q4"


def compute_panel_recommendations(issues: list[dict]) -> dict[str, dict[str, str]]:
    """
    Compute per-group quadrant recommendations for every issue.

    Returns:
        {
            "water_scarcity": {"investors": "q1", "workers": "q1", "ngos": "q1", "experts": "q1"},
            "semi_prices":    {"investors": "q3", "workers": "q4", "ngos": "q2", "experts": "q3"},
            ...
        }

    Bias rules (per group):
        experts  : always correct
        investors: Q2 social issues → Q3 (focus on financial risk, miss community harm)
        ngos     : Q3 financial issues → Q2 (surface community impact in financial risks)
        workers  : Social issues in Q2/Q4 → Q1 (amplify own-workforce materiality)
    """
    recs: dict[str, dict[str, str]] = {}

    for issue in issues:
        iid = issue.get("id", "")
        cq_num = issue.get("correct_quadrant")
        # Dictionaries without an explicit correct_quadrant (e.g. the 8-issue
        # materiality_db.DEFAULT_CONFIG) used to default EVERY issue to q4,
        # silently degrading all panel recommendations — experts included.
        # Fall back to the round's single classifier instead.
        cq = f"q{cq_num}" if cq_num is not None else correct_quadrant_v2(issue)
        issue_recs: dict[str, str] = {}

        for group, bias in _PANEL_GROUP_BIASES.items():
            if bias == "accurate":
                issue_recs[group] = cq

            elif bias == "q3_push":
                # Investors: community/social Q2 issues mis-classified as Q3
                if cq == "q2" and iid in _SOCIAL_ISSUE_IDS:
                    issue_recs[group] = "q3"
                else:
                    issue_recs[group] = cq

            elif bias == "q2_push":
                # NGOs: pure-financial Q3 issues get elevated to Q2
                if cq == "q3" and iid in _FINANCIAL_ISSUE_IDS:
                    issue_recs[group] = "q2"
                else:
                    issue_recs[group] = cq

            elif bias == "s1_boost":
                # Workers: workforce/social issues always recommended as Q1
                if iid in _SOCIAL_ISSUE_IDS and cq in ("q2", "q4"):
                    issue_recs[group] = "q1"
                else:
                    issue_recs[group] = cq

            else:
                issue_recs[group] = cq

        recs[iid] = issue_recs

    return recs
