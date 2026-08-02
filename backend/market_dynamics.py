"""
Muressons Global Corporation — Cross-Player Market Dynamics (SE-5)
Shared market environment for multiplayer sessions: industry
reputation, talent pool, competitive carbon pricing, and market
share dynamics.

Theory base:
  - Porter (1980): Competitive Strategy — Five Forces
  - Schelling (1960): Strategy of Conflict — game theory
  - Akerlof (1970): Market for Lemons — information asymmetry
  - Spence (1973): Signaling theory

Architecture:
  Pure-function module. Maintains a shared market state across
  all players in a cohort session. Updated after each round when
  all players have committed.
"""

from __future__ import annotations
from typing import Any
import math


# ═══════════════════════════════════════════════════════════════
#  SHARED MARKET STATE
# ═══════════════════════════════════════════════════════════════

def create_initial_market_state(n_players: int) -> dict[str, Any]:
    """Create the shared market state for a multiplayer session."""
    return {
        "industry_reputation_index": 50.0,  # Average of all player reputations
        "industry_carbon_intensity": 55.0,  # Average CI across all players
        "talent_pool": {
            "available_green_talent": 100,   # Shared pool of sustainability specialists
            "available_tech_talent": 150,    # Shared pool of tech specialists
            "available_operations_talent": 200,
            "talent_cost_multiplier": 1.0,  # Increases as pool shrinks
        },
        "market_share": {},  # player_id -> share (0-1, sums to 1)
        "carbon_permit_price": 45.0,  # $/tCO2e
        "carbon_permit_supply": 1000,  # Total permits available
        "esg_benchmark_index": 50.0,  # Industry ESG benchmark
        "regulatory_pressure": 30.0,  # 0-100, increases over rounds
        "consumer_sentiment_esg": 40.0,  # 0-100, consumer ESG awareness
        "investor_engagement_level": 50.0,
        "market_events": [],
        "market_history": [],
    }


# ═══════════════════════════════════════════════════════════════
#  MARKET DYNAMICS ENGINE
# ═══════════════════════════════════════════════════════════════

def update_industry_reputation(
    market_state: dict,
    player_reputations: dict[str, float],
) -> dict:
    """
    Industry reputation = weighted average of all player reputations.
    A single bad actor drags down the whole industry (Akerlof 1970).
    """
    reps = list(player_reputations.values())
    if not reps:
        return {"industry_reputation": market_state["industry_reputation_index"]}

    avg_rep = sum(reps) / len(reps)
    min_rep = min(reps)

    # Industry effect: bad actors drag average down disproportionately
    # "Lemons" effect: worst performer has outsized negative impact
    lemons_weight = 0.3
    industry_rep = round(
        avg_rep * (1 - lemons_weight) + min_rep * lemons_weight, 2
    )
    market_state["industry_reputation_index"] = max(0, min(100, industry_rep))

    return {
        "industry_reputation": industry_rep,
        "average_reputation": round(avg_rep, 2),
        "worst_performer_rep": round(min_rep, 2),
        "lemons_effect": round(avg_rep - industry_rep, 2),
        "message": (
            f"📊 Industry reputation index: {industry_rep:.0f}/100. "
            + (
                f"Lemons effect: worst performer ({min_rep:.0f}) is dragging "
                f"industry average down by {avg_rep - industry_rep:.1f} points."
                if avg_rep - industry_rep > 3
                else "Industry reputation is stable."
            )
        ),
    }


def process_talent_competition(
    market_state: dict,
    player_talent_demands: dict[str, dict],
) -> dict:
    """
    Shared talent pool mechanics.
    Players compete for scarce green/tech/ops talent.
    High demand drives up talent costs for everyone (Porter's rivalry).
    """
    pool = market_state["talent_pool"]
    diagnostics: dict[str, Any] = {"allocations": {}}

    # Aggregate demand across all players
    total_demand = {"green": 0, "tech": 0, "operations": 0}
    for player_id, demand in player_talent_demands.items():
        total_demand["green"] += demand.get("green_talent", 0)
        total_demand["tech"] += demand.get("tech_talent", 0)
        total_demand["operations"] += demand.get("operations_talent", 0)

    # Calculate scarcity multipliers
    for talent_type, total in total_demand.items():
        supply_key = f"available_{talent_type}_talent"
        supply = pool.get(supply_key, 100)
        if supply > 0:
            demand_ratio = total / supply
            # Price increases exponentially with scarcity
            cost_mult = max(1.0, 1.0 + 0.5 * (demand_ratio - 0.5) ** 2)
        else:
            cost_mult = 3.0  # Severe scarcity

        diagnostics[f"{talent_type}_demand_ratio"] = round(total / max(supply, 1), 3)
        diagnostics[f"{talent_type}_cost_multiplier"] = round(cost_mult, 3)

    # Allocate talent proportionally (first-come-first-served is unfair)
    for player_id, demand in player_talent_demands.items():
        allocation = {}
        for talent_type in ["green", "tech", "operations"]:
            requested = demand.get(f"{talent_type}_talent", 0)
            supply_key = f"available_{talent_type}_talent"
            total_requested = total_demand.get(talent_type, 0)
            supply = pool.get(supply_key, 100)

            if total_requested > 0 and supply > 0:
                share = requested / total_requested
                allocated = min(requested, round(supply * share))
            else:
                allocated = 0

            allocation[talent_type] = allocated

        diagnostics["allocations"][player_id] = allocation

    # Update pool (talent replenishes partially each round)
    pool["available_green_talent"] = max(
        50, pool["available_green_talent"] - total_demand["green"] + 20
    )
    pool["available_tech_talent"] = max(
        75, pool["available_tech_talent"] - total_demand["tech"] + 30
    )
    pool["available_operations_talent"] = max(
        100, pool["available_operations_talent"] - total_demand["operations"] + 40
    )

    # Overall talent cost multiplier
    avg_scarcity = sum(
        diagnostics.get(f"{t}_cost_multiplier", 1.0) for t in ["green", "tech", "operations"]
    ) / 3
    pool["talent_cost_multiplier"] = round(avg_scarcity, 3)

    return diagnostics


def update_carbon_market(
    market_state: dict,
    player_emissions: dict[str, float],
    round_number: int,
) -> dict:
    """
    Shared carbon permit market.
    Supply decreases each round (declining cap).
    Demand from all players drives price.
    """
    supply = market_state["carbon_permit_supply"]
    current_price = market_state["carbon_permit_price"]

    # Supply decreases 4.2% per round (EU ETS linear reduction factor)
    supply = round(supply * 0.958, 0)
    market_state["carbon_permit_supply"] = supply

    # Total demand
    total_emissions = sum(player_emissions.values())

    if supply > 0:
        scarcity = total_emissions / supply
        # Price follows scarcity curve
        new_price = round(current_price * (1 + 0.3 * (scarcity - 0.8)), 2)
        new_price = max(10, min(500, new_price))
    else:
        new_price = 500  # Maximum

    market_state["carbon_permit_price"] = new_price

    return {
        "permit_price": new_price,
        "price_change": round(new_price - current_price, 2),
        "total_emissions": round(total_emissions, 2),
        "supply_remaining": supply,
        "scarcity_ratio": round(total_emissions / max(supply, 1), 3),
        "message": (
            f"🏭 Carbon permit price: ${new_price:.0f}/tCO2e "
            f"({'↑' if new_price > current_price else '↓'} "
            f"${abs(new_price - current_price):.0f}). "
            f"Supply: {supply:.0f} permits remaining."
        ),
    }


def calculate_market_share(
    player_data: dict[str, dict],
) -> dict:
    """
    Calculate relative market share based on revenue, reputation, and ESG score.
    Uses Spence (1973) signaling: ESG performance signals quality to market.
    """
    if not player_data:
        return {}

    shares = {}
    total_score = 0

    for player_id, data in player_data.items():
        revenue = data.get("total_revenue", 0)
        reputation = data.get("reputation", 50)
        esg_score = data.get("esg_score", 50)

        # Composite market power score
        score = (
            revenue * 0.5
            + reputation * 10_000 * 0.3
            + esg_score * 10_000 * 0.2
        )
        shares[player_id] = score
        total_score += score

    # Normalise to 0-1
    if total_score > 0:
        for pid in shares:
            shares[pid] = round(shares[pid] / total_score, 4)

    return shares


def process_market_tick(
    market_state: dict,
    all_player_states: dict[str, dict],
    round_number: int,
) -> tuple[dict, dict]:
    """
    Process all market dynamics for this round.
    Called after all players have committed their turns.
    """
    diagnostics: dict[str, Any] = {}

    # 1. Industry reputation (Akerlof lemons effect)
    player_reps = {
        pid: ps.get("group_reputation", 50)
        for pid, ps in all_player_states.items()
    }
    rep_diag = update_industry_reputation(market_state, player_reps)
    diagnostics["industry_reputation"] = rep_diag

    # 2. Carbon market
    player_emissions = {}
    for pid, ps in all_player_states.items():
        bus = ps.get("bu_states", [])
        avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
        player_emissions[pid] = avg_ci * len(bus)
    carbon_diag = update_carbon_market(market_state, player_emissions, round_number)
    diagnostics["carbon_market"] = carbon_diag

    # 3. Market share
    player_data = {}
    for pid, ps in all_player_states.items():
        bus = ps.get("bu_states", [])
        total_rev = sum(bu.get("revenue_base", 0) for bu in bus)
        player_data[pid] = {
            "total_revenue": total_rev,
            "reputation": ps.get("group_reputation", 50),
            "esg_score": ps.get("group_reputation", 50),  # Proxy
        }
    market_state["market_share"] = calculate_market_share(player_data)
    diagnostics["market_shares"] = market_state["market_share"]

    # 4. Regulatory pressure increases over time
    market_state["regulatory_pressure"] = min(
        100, market_state["regulatory_pressure"] + round_number * 1.5
    )

    # 5. Consumer ESG sentiment
    market_state["consumer_sentiment_esg"] = min(
        100, market_state["consumer_sentiment_esg"] + 3  # Growing trend
    )

    # History
    market_state["market_history"].append({
        "round": round_number,
        "industry_rep": market_state["industry_reputation_index"],
        "carbon_price": market_state["carbon_permit_price"],
        "regulatory_pressure": market_state["regulatory_pressure"],
        "consumer_esg": market_state["consumer_sentiment_esg"],
    })

    return market_state, diagnostics
