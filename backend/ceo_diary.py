"""
Muressons Global Corporation — CEO Diary Narrative Engine
Template-driven narrative generator that produces 2-sentence
"CEO diary entries" after each round based on choices and outcomes.
"""

from __future__ import annotations
from typing import Any


# ═══════════════════════════════════════════════════════════════
#  NARRATIVE FRAGMENTS — keyed by (round, option, event_flag)
# ═══════════════════════════════════════════════════════════════

# Each entry: (opening_sentence, closing_sentence)
# Opening = player's agency. Closing = consequence/emotion.

_ROUND_NARRATIVES: dict[int, dict[str, tuple[str, str]]] = {
    1: {
        "option_a": (
            "I decided to keep the ESG audit light — a surface-level scan that wouldn't disrupt operations.",
            "The CFO was relieved, but something in the Electronics division's numbers didn't add up. I hope it's nothing.",
        ),
        "option_b": (
            "I commissioned the full forensic audit. $3M well spent — or so I told the board.",
            "The auditors uncovered uncomfortable truths across every division. Better to know now than learn later from a regulator.",
        ),
        "option_c": (
            "We chose a phased approach — audit Pharma and Consumer Goods now, defer the tech divisions.",
            "A reasonable compromise, though I can't shake the feeling we're kicking the can down the road on Electronics.",
        ),
        "_default": (
            "The board mandated our first ESG assessment. Whatever we found, it would set the tone for everything that followed.",
            "At least now we have a baseline. The real question is what we do with it.",
        ),
    },
    2: {
        "option_a": (
            "Full materiality alignment. Every dollar tied to genuine impact. The CFO called it 'idealistic'.",
            "The CSRD compliance team was thrilled. The investors... they're watching to see if principle translates to returns.",
        ),
        "option_b": (
            "We allowed strategic exceptions to the materiality framework. Pragmatic, I told myself.",
            "The board approved, but I noticed the governance committee exchanged glances. We're walking a fine line.",
        ),
        "option_c": (
            "I overruled the materiality framework entirely. Business as usual prevails.",
            "The CFO clawed back 40% of the allocated budget. Markets don't reward half-measures, but neither does regulatory exposure.",
        ),
        "_default": (
            "The Double Materiality Matrix forced us to confront what truly matters — financially and socially.",
            "CSRD reporting is no longer optional. We either lead the disclosure, or we get dragged through it.",
        ),
    },
    3: {
        "option_a": (
            "We ripped out our supply chain overnight. New low-carbon suppliers, new risks, new costs.",
            "The disruption was real — but so was the 15-point drop in carbon intensity. Bold moves have bold consequences.",
        ),
        "option_b": (
            "The green bond was issued at a premium. The market believed in our transition story — for now.",
            "Natural capital debt is falling, but slowly. The bond investors expect periodic progress reports.",
        ),
        "option_c": (
            "Carbon offsets. The easy path. The analysts called it 'kicking the can down the road'.",
            "The reputation hit was immediate. Our own employees started asking uncomfortable questions at the town hall.",
        ),
        "_default": (
            "Scope 3 emissions dominated the board agenda for the first time. Supply chain decarbonisation is now unavoidable.",
            "The regulators are circling. Every supplier contract is now an ESG liability.",
        ),
    },
    4: {
        "option_a": (
            "When the Electronics scandal broke, I chose full transparency. We opened our factories to journalists.",
            "It cost $6M and dominated headlines for a week. But when the cameras left, our reputation was stronger than before the crisis.",
        ),
        "option_b": (
            "We hired the best crisis PR firm money could buy. They contained the narrative, if not the truth.",
            "The media moved on, but the root cause festers. Factory workers know the truth hasn't changed.",
        ),
        "option_c": (
            "Deny and deflect. The playbook of a previous era. I hoped it would still work.",
            "It didn't. The contagion spread to every division. I can feel the board's confidence eroding.",
        ),
        "_default": (
            "A supply chain scandal tested everything we'd built. The contagion engine doesn't discriminate.",
            "Reputation, it turns out, is the most fragile asset on the balance sheet.",
        ),
    },
    5: {
        "option_a": (
            "I signed off on the $8M hard engineering defence. Flood walls and reinforced infrastructure.",
            "The construction team says two rounds until completion. Meanwhile, we pray the cyclone holds off. The carbon cost of all that concrete keeps me awake.",
        ),
        "option_b": (
            "Mangrove restoration. Nature as infrastructure. The environmentalists loved it; the CFO was sceptical.",
            "If the ecosystem establishes properly, we'll have protection AND reduced natural capital debt. That's a big 'if'.",
        ),
        "option_c": (
            "Insurance only. No physical adaptation. The cheapest option, and the riskiest.",
            "When — not if — the next cyclone hits, there will be nothing between it and our manufacturing corridor.",
        ),
        "_default": (
            "A Category 4 cyclone bore down on our primary corridor. Climate risk became very, very physical.",
            "The era of theoretical sustainability is over. The weather doesn't care about our annual report.",
        ),
    },
    6: {
        "option_a": (
            "We monetised the biased AI. Revenue surged. Ethics took a back seat.",
            "The short-term numbers are spectacular. The long-term reputational bomb is ticking. I can hear it.",
        ),
        "option_b": (
            "I shut down the AI tool, hired an ethics board, and committed to a full model retrain.",
            "$8M and six months of disruption. But every employee knows we chose principle over profit. That matters.",
        ),
        "option_c": (
            "A quiet patch. Fix the algorithm, say nothing. The tech team assured me nobody would notice.",
            "Nobody noticed — yet. But if it leaks, the cover-up will be worse than the crime. I've seen this movie before.",
        ),
        "_default": (
            "Our AI recruitment tool was found to systematically discriminate. The question wasn't 'did it happen' — it was 'what do we do now'.",
            "Algorithmic ethics isn't a tech problem. It's a leadership problem.",
        ),
    },
    7: {
        "option_a": (
            "Full circular redesign. Every product engineered for disassembly and reuse.",
            "$10M is a lot of money. But when the EU fines are $15M for non-compliance, it starts to look like a bargain.",
        ),
        "option_b": (
            "Extended Producer Responsibility programs. Take-back schemes and recycling partnerships.",
            "The compliance team is satisfied. The innovation team says we're doing the minimum. They're both right.",
        ),
        "option_c": (
            "Waste-to-energy. A bridge between environmental ambition and economic reality.",
            "The synergy multiplier jumped. Cross-BU collaboration is finally paying off. The board is smiling — for once.",
        ),
        "_default": (
            "EU circular economy regulations caught us with 60% waste diversion targets. The clock is ticking.",
            "Linear take-make-waste is dying. The only question is whether we transition or get transitioned.",
        ),
    },
    8: {
        "option_a": (
            "Water efficiency upgrades across all BUs. Equal allocation, equal sacrifice.",
            "The equity of the approach earned us community trust. But at $12M, equity doesn't come cheap.",
        ),
        "option_b": (
            "I prioritised Electronics — our highest-margin division. Pharma and Consumer Goods took the water cuts.",
            "The social licence hit was devastating. Community trust in the 'left behind' divisions has cratered.",
        ),
        "option_c": (
            "A $30M desalination plant. The biggest single investment in company history.",
            "The construction delay means no benefit for two rounds. But when it comes online, we'll never face a water crisis again. I hope.",
        ),
        "_default": (
            "The drought exposed a truth we'd been avoiding: our business model is built on water scarcity.",
            "Blue stress isn't a future risk. It's a present reality.",
        ),
    },
    9: {
        "option_a": (
            "Immediate factory closure. 2,000 jobs gone. The efficiency gain was immediate.",
            "The community protests are growing louder. If social licence was already low, this might trigger a strike.",
        ),
        "option_b": (
            "A managed transition. Two years of retraining, severance, and community engagement.",
            "$12M for human dignity. The board asked if we could quantify the ROI. Some things can't be put on a spreadsheet.",
        ),
        "option_c": (
            "$20M into a community investment fund. Green jobs, skills training, economic diversification.",
            "The local mayor called me personally to say thank you. That felt more real than any analyst rating.",
        ),
        "_default": (
            "Decarbonisation has a human cost. 2,000 families are waiting to learn their fate.",
            "Just Transition isn't a buzzword. It's a moral obligation.",
        ),
    },
    10: {
        "option_a": (
            "We fought the activist. Integration prevails. Synergy is our weapon.",
            "Three years of strategy crystallised into this moment. We kept the group together — but can we keep them at bay forever?",
        ),
        "option_b": (
            "The weakest BU was spun off. A painful amputation to save the body.",
            "The market reacted positively. The employees of the spun-off division... less so.",
        ),
        "option_c": (
            "Full divestiture. Everything must go. Maximum cash extraction.",
            "The treasury is flush. The company is a shell. Was this victory, or surrender?",
        ),
        "_default": (
            "An activist consortium forced the board's hand. The final chapter of Muressons is being written.",
            "Terminal valuation. Three years of decisions, distilled into a single number. I wonder if it tells the whole story.",
        ),
    },
}

# ── Event-conditional overlays ──────────────────────────────────
# If a specific event flag is present, append additional context
_EVENT_OVERLAYS: dict[str, str] = {
    "greenwashing_scandal": " The greenwashing scandal made every promise ring hollow.",
    "tipping_point_reached": " The climate tipping point changed everything. There's no going back.",
    "insolvency_active": " Credit downgrade. The CFO's face said it all.",
    "talent_penalty_applied": " Our best people are leaving. Brain drain is real.",
    "technology_lockin_penalty": " We're locked in. Diversification isn't an option anymore.",
    "stakeholder_fatigue_applied": " Stakeholder fatigue is setting in. Another crisis, another apology.",
    "strike_triggered": " The strike paralysed operations. Revenue zeroed for the period.",
    "divestment_pressure_active": " Institutional investors are demanding a credible decarbonisation pathway — or they walk.",
    "cbam_surcharge_applied": " The EU border carbon adjustment hit our import costs hard.",
    "loss_damage_levy_applied": " We're now contributing to the UN Loss & Damage Fund. The cost of inaction made real.",
}


def generate_ceo_diary(
    round_number: int,
    choice_selected: str,
    events: dict[str, Any],
) -> dict[str, str]:
    """
    Generate a 2-sentence CEO diary entry for the completed round.

    Returns {entry, round_label, mood}.
    """
    round_narratives = _ROUND_NARRATIVES.get(round_number, {})

    # Get the narrative for the selected choice, or fall back to default
    if choice_selected and choice_selected in round_narratives:
        opening, closing = round_narratives[choice_selected]
    else:
        opening, closing = round_narratives.get("_default", (
            f"Round {round_number} presented challenges I hadn't anticipated.",
            "Every decision in this role has consequences that ripple further than I can see.",
        ))

    # Check for event overlays to add emotional depth
    overlay = ""
    for flag, addon in _EVENT_OVERLAYS.items():
        if events.get(flag):
            overlay = addon
            break  # Only add one overlay per entry

    entry = f"{opening} {closing}{overlay}"

    # Determine emotional mood from events
    treasury_delta = events.get("internal_carbon_fee_deducted", 0) or 0
    rep = events.get("group_reputation", 50)
    if events.get("greenwashing_scandal") or events.get("insolvency_active"):
        mood = "distressed"
    elif events.get("tipping_point_reached") or events.get("strike_triggered"):
        mood = "anxious"
    elif rep and rep > 70:
        mood = "confident"
    elif rep and rep < 30:
        mood = "desperate"
    else:
        mood = "contemplative"

    round_labels = {
        1: "Foundations", 2: "Double Materiality", 3: "Scope 3 Emissions",
        4: "Contagion", 5: "Climate", 6: "AI Bias",
        7: "Circularity", 8: "Blue Stress", 9: "Just Transition",
        10: "Grand Finale",
    }

    return {
        "entry": entry,
        "round_label": round_labels.get(round_number, f"Round {round_number}"),
        "mood": mood,
        "round_number": round_number,
    }
