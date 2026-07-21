"""
Muressons — Stakeholder Management Round Configs (4 rounds)
"""

STAKEHOLDER_ROUND_CONFIGS: dict = {
    1: {
        "title": "Stakeholder Salience Mapping",
        "crisis_title": "🎯 Board Demands Stakeholder Strategy",
        "crisis_narrative": (
            "The board has mandated a formal stakeholder engagement strategy "
            "following a bruising AGM where activist shareholders secured 38% "
            "support for a climate resolution. Institutional investors (representing "
            "55% of shares) are demanding structured engagement. How do you "
            "approach your stakeholder landscape?"
        ),
        "options": {
            "option_a": {
                "title": "Dynamic Salience Framework",
                "description": (
                    "Implement Mitchell, Agle & Wood's salience model with periodic "
                    "reassessment. Map all stakeholder groups by power, legitimacy, "
                    "and urgency. Establish formal engagement channels with top-tier "
                    "stakeholders and publish a Stakeholder Engagement Policy."
                ),
                "impacts": {"treasury": -3_000_000, "reputation": 8, "governance_risk_delta": -5, "social_license_delta": 6},
                "flags_set": ["sm_dynamic_salience", "sm_engagement_policy"],
            },
            "option_b": {
                "title": "Investor-Focused Prioritisation",
                "description": (
                    "Focus engagement resources on institutional investors and "
                    "proxy advisors. Strengthen ESG disclosures, host investor "
                    "roadshows, and establish a Sustainability Advisory Panel "
                    "with 3 independent ESG experts."
                ),
                "impacts": {"treasury": -1_500_000, "reputation": 4, "governance_risk_delta": -2},
                "flags_set": ["sm_investor_focus"],
            },
            "option_c": {
                "title": "Reactive Engagement",
                "description": (
                    "Maintain current ad-hoc engagement approach. Respond to "
                    "stakeholder inquiries as they arise. Allocate resources "
                    "only when issues escalate to board level."
                ),
                "impacts": {"treasury": 0, "reputation": -4, "governance_risk_delta": 3},
                "flags_set": ["sm_reactive_approach"],
            },
        },
    },
    2: {
        "title": "Investor Relations & ESG Disclosure",
        "crisis_title": "📊 ESG Rating Downgrade Threat",
        "crisis_narrative": (
            "MSCI has placed your ESG rating on 'negative watch' due to "
            "governance concerns and disclosure gaps. Sustainalytics has flagged "
            "an 'unmanaged risk' in your environmental pillar. If downgraded, "
            "you'll be excluded from $12B in ESG index-tracking funds. The clock "
            "is ticking — rating reviews are in 60 days."
        ),
        "options": {
            "option_a": {
                "title": "Comprehensive ESG Reporting Overhaul",
                "description": (
                    "Adopt GRI Universal Standards, align with ISSB (IFRS S1/S2), "
                    "publish a standalone Sustainability Report with KPIs, "
                    "get limited assurance from Big 4, and proactively brief "
                    "all rating agencies."
                ),
                "impacts": {"treasury": -4_000_000, "reputation": 10, "governance_risk_delta": -8},
                "flags_set": ["sm_esg_gold_standard", "sm_issb_aligned"],
            },
            "option_b": {
                "title": "Targeted Gap Closure",
                "description": (
                    "Address the specific gaps flagged by MSCI and Sustainalytics. "
                    "Publish a governance improvement roadmap and enhanced climate "
                    "disclosures. Host a direct engagement call with rating analysts."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": 5, "governance_risk_delta": -4},
                "flags_set": ["sm_gap_closure"],
            },
            "option_c": {
                "title": "Challenge the Methodology",
                "description": (
                    "Dispute the rating methodology, argue peer comparison "
                    "inconsistencies, and lobby for sector-specific scoring. "
                    "Minimise disclosure changes."
                ),
                "impacts": {"treasury": -500_000, "reputation": -6, "governance_risk_delta": 4},
                "flags_set": ["sm_rating_challenge"],
            },
        },
    },
    3: {
        "title": "Community Engagement & Social License",
        "crisis_title": "🏘️ Community Opposition to Expansion",
        "crisis_narrative": (
            "Your planned $50M facility expansion faces organised community "
            "opposition. A local coalition cites water pollution concerns, "
            "traffic congestion, and gentrification. The planning commission "
            "hearing is in 30 days. Social media campaigns have attracted "
            "national attention with #NotInOurBackyard trending."
        ),
        "options": {
            "option_a": {
                "title": "Co-Design & Community Benefit Agreement",
                "description": (
                    "Establish a Community Liaison Committee, co-design a "
                    "Community Benefit Agreement (CBA) with binding commitments "
                    "on employment, environmental monitoring, and revenue sharing. "
                    "Fund an independent Environmental Impact Assessment."
                ),
                "impacts": {"treasury": -5_000_000, "reputation": 12, "social_license_delta": 15},
                "flags_set": ["sm_community_partnership", "sm_cba_signed"],
            },
            "option_b": {
                "title": "Voluntary Commitments Package",
                "description": (
                    "Offer voluntary environmental pledges, a $1M community "
                    "development fund, and periodic town halls. Modify the "
                    "expansion design to address key concerns."
                ),
                "impacts": {"treasury": -2_500_000, "reputation": 5, "social_license_delta": 6},
                "flags_set": ["sm_voluntary_commitments"],
            },
            "option_c": {
                "title": "Expedited Approval Process",
                "description": (
                    "Engage lobbyists to fast-track planning approval, use "
                    "legal mechanisms to limit objections, and proceed with "
                    "the original design. Minimise community engagement."
                ),
                "impacts": {"treasury": -1_000_000, "reputation": -8, "social_license_delta": -8, "governance_risk_delta": 6},
                "flags_set": ["sm_community_overridden", "sm_legal_escalation"],
            },
        },
    },
    4: {
        "title": "Crisis Communication & Media Strategy",
        "crisis_title": "📰 Multi-Front Reputational Crisis",
        "crisis_narrative": (
            "A perfect storm: an employee whistleblower alleges safety violations, "
            "a product recall affects 200,000 units, and an investigative podcast "
            "series exposes executive compensation during layoffs. Your stock price "
            "drops 8% in pre-market trading. All stakeholder groups are demanding "
            "immediate responses."
        ),
        "special_rules": {
            "engagement_policy_bonus": {
                "condition": "sm_engagement_policy",
                "effect": "Established channels reduce crisis escalation by 20%",
            },
            "reactive_penalty": {
                "condition": "sm_reactive_approach",
                "effect": "No crisis playbook — media narrative spirals 25% faster",
            },
        },
        "options": {
            "option_a": {
                "title": "Radical Transparency & CEO Leadership",
                "description": (
                    "CEO issues video statement within 4 hours, acknowledges "
                    "failures, announces independent investigation, suspends "
                    "executive bonuses, and invites stakeholder representatives "
                    "to a 'Reset Summit' within 14 days."
                ),
                "impacts": {"treasury": -3_000_000, "reputation": 15, "social_license_delta": 10, "governance_risk_delta": -6},
                "flags_set": ["sm_crisis_leader", "sm_transparency_champion"],
            },
            "option_b": {
                "title": "Structured Response Protocol",
                "description": (
                    "Activate crisis management team, issue holding statements, "
                    "brief key investors directly, address each issue sequentially "
                    "over 7 days, and commission external reviews."
                ),
                "impacts": {"treasury": -1_500_000, "reputation": 5, "governance_risk_delta": -2},
                "flags_set": ["sm_structured_response"],
            },
            "option_c": {
                "title": "Legal & PR Defence",
                "description": (
                    "Retain crisis PR firm, issue legal threats to podcast, "
                    "challenge whistleblower credibility, and frame recall as "
                    "'precautionary'. Focus on stock price recovery."
                ),
                "impacts": {"treasury": -2_000_000, "reputation": -10, "governance_risk_delta": 8, "social_license_delta": -5},
                "flags_set": ["sm_defensive_crisis", "sm_media_hostile"],
            },
        },
    },
}
