"""
Muressons Global Corporation — Dynamic Case Injection (SE-8)
LLM-generated real-world case briefs contextual to the player's
current state, replacing static case parallels with adaptive content.

Theory base:
  - Baldwin & Ford (1988): Transfer of training
  - Kolb (1984): Experiential learning cycle
  - Schön (1983): Reflective practice

Architecture:
  Hybrid module. Contains deterministic case selection logic
  AND prompt templates for LLM-generated contextual briefs.
  Falls back to curated case bank if LLM is unavailable.
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════
#  CONTEXTUAL CASE BANK
#  Cases organised by situation type, not by round.
#  The engine selects the most relevant case based on player state.
# ═══════════════════════════════════════════════════════════════

CONTEXTUAL_CASES = {
    "high_carbon_intensity": [
        {
            "id": "orsted_transformation",
            "company": "Ørsted",
            "title": "From DONG Energy to Ørsted: The Total Business Model Transformation",
            "year": "2017-2023",
            "situation": (
                "Danish state oil/gas company DONG Energy had carbon intensity "
                "among the highest in European utilities. Facing stranded asset "
                "risk and regulatory pressure, they made the radical decision to "
                "divest ALL fossil fuel assets and pivot to offshore wind."
            ),
            "outcome": (
                "Market cap grew from $15B to $60B. Became world's largest offshore "
                "wind developer. Share price tripled despite divesting profitable assets."
            ),
            "lesson": "Radical decarbonisation can be a value creation strategy, not just risk mitigation.",
            "theory": "Teece (2007): Dynamic Capabilities — sensing, seizing, transforming.",
            "relevance_threshold": {"carbon_intensity_above": 55},
        },
        {
            "id": "heidelberg_carbon_capture",
            "company": "HeidelbergCement (Heidelberg Materials)",
            "title": "Hard-to-Abate Sector: Carbon Capture as Transition Strategy",
            "year": "2020-2025",
            "situation": (
                "Cement production is responsible for 8% of global CO2. Unlike "
                "energy, cement cannot simply switch fuel sources. Heidelberg invested "
                "€1.5B in carbon capture technology at its Brevik plant in Norway."
            ),
            "outcome": (
                "First commercial-scale CCS facility in cement industry. Capturing "
                "400,000 tonnes CO2/year. Positioned as first-mover in hard-to-abate "
                "sector decarbonisation."
            ),
            "lesson": "When operational change isn't enough, technological innovation becomes the leverage point.",
            "theory": "Meadows (2008): LP10 — changing the physical structure of the system.",
            "relevance_threshold": {"carbon_intensity_above": 70},
        },
    ],
    "low_reputation": [
        {
            "id": "vw_dieselgate_recovery",
            "company": "Volkswagen",
            "title": "Dieselgate to Electric: VW's Long Road to Reputational Recovery",
            "year": "2015-2024",
            "situation": (
                "VW's emissions cheating scandal destroyed $30B in market value "
                "overnight. Criminal prosecutions, €31B in fines and settlements. "
                "The deepest corporate trust crisis in European history."
            ),
            "outcome": (
                "VW committed €89B to electrification. Launched ID. series. "
                "But reputation recovery is still incomplete — trust takes "
                "years to rebuild, not quarters."
            ),
            "lesson": "Reputational damage follows a sigmoid curve: fast to destroy, slow to rebuild.",
            "theory": "Contagion sigmoid model: the simulation's own engine mirrors VW's experience.",
            "relevance_threshold": {"reputation_below": 40},
        },
        {
            "id": "bp_beyond_petroleum",
            "company": "BP",
            "title": "The Perils of 'Beyond Petroleum': Greenwashing Before the Term Existed",
            "year": "2000-2010",
            "situation": (
                "BP rebranded as 'Beyond Petroleum' in 2000, spending $200M on "
                "marketing while maintaining the same fossil fuel business model. "
                "When Deepwater Horizon exploded in 2010, the gap between brand "
                "promise and operational reality became catastrophic."
            ),
            "outcome": (
                "$65B in total costs. CEO forced to resign. The 'Beyond Petroleum' "
                "campaign is now the textbook definition of corporate greenwashing."
            ),
            "lesson": "Branding without operational transformation is the highest-risk strategy.",
            "theory": "Greenwashing engine: SLO penalty = f(gap between claims and performance).",
            "relevance_threshold": {"reputation_below": 35},
        },
    ],
    "high_burnout": [
        {
            "id": "amazon_warehouse",
            "company": "Amazon",
            "title": "The Human Cost of Efficiency: Amazon's Warehouse Labour Crisis",
            "year": "2020-2023",
            "situation": (
                "Amazon's warehouse injury rate was 2x the industry average. "
                "Annual turnover exceeded 150%. The JFK8 Staten Island facility "
                "voted to unionise in 2022 — the first Amazon union in US history."
            ),
            "outcome": (
                "Labour costs increased $1B+ from wage increases and safety "
                "improvements. But operational efficiency dropped 15% during "
                "the transition. The 'move fast' culture hit human capital limits."
            ),
            "lesson": "Workforce burnout is a hidden liability that compounds until it becomes a visible crisis.",
            "theory": "Senge (1990): 'Limits to Growth' archetype — growth hits human constraint.",
            "relevance_threshold": {"burnout_above": 55},
        },
    ],
    "strong_esg_performance": [
        {
            "id": "patagonia_purpose",
            "company": "Patagonia",
            "title": "Earth Is Now Our Only Shareholder: Purpose as Business Model",
            "year": "2022",
            "situation": (
                "Founder Yvon Chouinard transferred 100% of company ownership "
                "to a climate trust. Revenue had grown to $1.5B/year precisely "
                "because customers trusted the brand's authenticity."
            ),
            "outcome": (
                "Revenue continues to grow post-transfer. Brand value increased "
                "30%. Patagonia proved that purpose-driven business creates "
                "sustainable competitive advantage."
            ),
            "lesson": "When paradigm (LP2) aligns with goals (LP3) and rules (LP5), the system is self-reinforcing.",
            "theory": "Meadows (2008): Alignment across multiple leverage points creates systemic resilience.",
            "relevance_threshold": {"reputation_above": 75},
        },
    ],
    "stakeholder_conflict": [
        {
            "id": "danone_activism",
            "company": "Danone",
            "title": "The CEO Who Was Too Green: Faber's Ouster and the Limits of ESG Leadership",
            "year": "2021",
            "situation": (
                "Danone CEO Emmanuel Faber championed 'Entreprise à Mission' — "
                "legally binding the company to social and environmental goals. "
                "When margins declined during COVID, activist investors Artisan "
                "Partners and Bluebell Capital orchestrated his removal."
            ),
            "outcome": (
                "Faber was fired. Successor partially reversed the mission. "
                "Danone's share price initially rose but long-term ESG "
                "credibility was severely damaged."
            ),
            "lesson": "ESG leadership without shareholder coalition is fragile. Build the coalition BEFORE you need it.",
            "theory": "Organisational politics (SI-5): Coalition-building is a prerequisite for transformation.",
            "relevance_threshold": {"slo_below": 45},
        },
    ],
    "financial_distress": [
        {
            "id": "gm_bankruptcy",
            "company": "General Motors",
            "title": "Chapter 11 and Rebirth: GM's Structured Crisis Recovery",
            "year": "2009-2014",
            "situation": (
                "GM filed for Chapter 11 bankruptcy during the 2008 crisis. "
                "$50B government bailout. Shed brands (Pontiac, Saturn, Hummer). "
                "Emerged leaner with focus on EVs and autonomous vehicles."
            ),
            "outcome": (
                "GM returned to profitability within 2 years. Repaid government "
                "loans. Now investing $35B in EVs through 2025."
            ),
            "lesson": "Structured crisis (turnaround arc) can create a stronger company if managed strategically.",
            "theory": "Turnaround arc: the simulation's 3-act distress model mirrors GM's actual recovery.",
            "relevance_threshold": {"treasury_below": 5_000_000},
        },
    ],
}


# ═══════════════════════════════════════════════════════════════
#  DYNAMIC CASE SELECTION
# ═══════════════════════════════════════════════════════════════

def select_contextual_cases(
    gs: dict,
    bus: list[dict],
    round_number: int,
    max_cases: int = 2,
) -> list[dict]:
    """
    Select the most relevant cases based on current player state.
    Returns up to max_cases cases that match the player's situation.
    """
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)
    rep = gs.get("group_reputation", 50)
    treasury = gs.get("corporate_treasury", 0)

    matched = []

    for situation, cases in CONTEXTUAL_CASES.items():
        for case in cases:
            threshold = case.get("relevance_threshold", {})
            relevant = False

            if "carbon_intensity_above" in threshold and avg_ci > threshold["carbon_intensity_above"]:
                relevant = True
            if "reputation_below" in threshold and rep < threshold["reputation_below"]:
                relevant = True
            if "reputation_above" in threshold and rep > threshold["reputation_above"]:
                relevant = True
            if "burnout_above" in threshold and avg_burnout > threshold["burnout_above"]:
                relevant = True
            if "slo_below" in threshold and avg_slo < threshold["slo_below"]:
                relevant = True
            if "treasury_below" in threshold and treasury < threshold["treasury_below"]:
                relevant = True

            if relevant:
                matched.append({
                    "situation": situation,
                    **case,
                    "relevance_score": _calc_relevance_score(case, gs, bus),
                })

    # Sort by relevance and return top N
    matched.sort(key=lambda c: c.get("relevance_score", 0), reverse=True)
    return matched[:max_cases]


def _calc_relevance_score(
    case: dict,
    gs: dict,
    bus: list[dict],
) -> float:
    """Calculate how relevant a case is to the current player state."""
    score = 0.0
    threshold = case.get("relevance_threshold", {})

    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
    rep = gs.get("group_reputation", 50)
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)

    if "carbon_intensity_above" in threshold:
        excess = avg_ci - threshold["carbon_intensity_above"]
        if excess > 0:
            score += excess * 2

    if "reputation_below" in threshold:
        deficit = threshold["reputation_below"] - rep
        if deficit > 0:
            score += deficit * 2

    if "burnout_above" in threshold:
        excess = avg_burnout - threshold["burnout_above"]
        if excess > 0:
            score += excess * 1.5

    return round(score, 2)


# ═══════════════════════════════════════════════════════════════
#  LLM PROMPT FOR CONTEXTUAL CASE GENERATION
# ═══════════════════════════════════════════════════════════════

def get_dynamic_case_prompt(
    gs: dict,
    bus: list[dict],
    round_number: int,
    round_theme: str,
) -> str:
    """
    Generate a prompt for LLM to create a custom case study
    relevant to the player's current situation.
    """
    avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
    avg_slo = sum(bu.get("social_license_score", 50) for bu in bus) / max(len(bus), 1)
    rep = gs.get("group_reputation", 50)
    treasury = gs.get("corporate_treasury", 0)
    avg_burnout = sum(bu.get("staff_burnout_index", 0) for bu in bus) / max(len(bus), 1)

    return f"""Generate a real-world corporate case study that is relevant to the following simulation state.
The case should be factual (a real company and real events), not fictional.

SIMULATION CONTEXT:
- Round: {round_number}/10 (Theme: {round_theme})
- Group Reputation: {rep}/100
- Carbon Intensity: {avg_ci:.0f}
- Social Licence: {avg_slo:.0f}/100
- Treasury: ${treasury:,.0f}
- Workforce Burnout: {avg_burnout:.0f}/100

FORMAT (JSON):
{{
  "company": "Company Name",
  "title": "Brief case title",
  "year": "Year(s)",
  "situation": "2-3 sentence description of the challenge they faced",
  "outcome": "2-3 sentence description of what happened",
  "lesson": "1 sentence transferable lesson for the student",
  "theory": "Academic theory this case illustrates"
}}

Select a case that DIRECTLY parallels the student's current challenges.
If reputation is low, choose a reputational recovery case.
If carbon intensity is high, choose a decarbonisation case.
Focus on Fortune 500 / FTSE 100 companies for credibility."""
