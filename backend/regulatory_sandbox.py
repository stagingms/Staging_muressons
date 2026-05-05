"""
Muressons Global Corporation — Regulatory Sandbox Mode (SE-7)
Expert-tier mode where students design and test ESG regulations,
observing their systemic effects on the simulation.

Theory base:
  - Stigler (1971): Theory of Economic Regulation
  - Pigou (1920): Pigouvian taxation
  - Coase (1960): Property rights and externalities
  - Ostrom (2009): Polycentric governance

Architecture:
  Pure-function module. Players can create custom regulations
  that modify the simulation's rule engine in controlled ways.
  Available only in Expert difficulty tier.
"""

from __future__ import annotations
from typing import Any
import math


# ═══════════════════════════════════════════════════════════════
#  REGULATORY INSTRUMENTS
# ═══════════════════════════════════════════════════════════════

REGULATORY_INSTRUMENTS = {
    "carbon_tax": {
        "name": "Carbon Tax",
        "description": "Direct price on carbon emissions (Pigouvian tax)",
        "parameters": {
            "rate_per_tonne": {"min": 10, "max": 500, "default": 50, "unit": "$/tCO2e"},
            "annual_escalation_pct": {"min": 0, "max": 20, "default": 5, "unit": "%"},
            "border_adjustment": {"type": "bool", "default": True},
        },
        "effects": {
            "opex_increase_per_ci": 0.001,  # OPEX increase per unit carbon intensity × rate
            "innovation_incentive": 0.02,   # Revenue boost for low-CI BUs
            "revenue_impact_exporters": -0.03,  # Export competitiveness hit
        },
        "theory": "Pigou (1920): Internalising negative externalities via price signals.",
    },
    "emissions_trading": {
        "name": "Emissions Trading System (ETS)",
        "description": "Cap-and-trade with declining annual cap",
        "parameters": {
            "initial_cap_reduction_pct": {"min": 1, "max": 10, "default": 4.2, "unit": "%/year"},
            "free_allocation_pct": {"min": 0, "max": 100, "default": 50, "unit": "%"},
            "market_stability_reserve": {"type": "bool", "default": True},
        },
        "effects": {
            "permit_cost_base": 45,
            "volatility": 0.15,
            "windfall_profit_risk": True,
        },
        "theory": "Coase (1960): Property rights enable efficient allocation of pollution rights.",
    },
    "mandatory_disclosure": {
        "name": "Mandatory ESG Disclosure (CSRD-style)",
        "description": "Required sustainability reporting with assurance",
        "parameters": {
            "scope": {"options": ["limited", "reasonable"], "default": "limited"},
            "double_materiality": {"type": "bool", "default": True},
            "digital_taxonomy": {"type": "bool", "default": False},
        },
        "effects": {
            "governance_risk_reduction": -5,
            "compliance_cost": 500_000,
            "reputation_boost": 3,
            "transparency_effect": 0.15,  # Reduces information asymmetry
        },
        "theory": "Akerlof (1970): Reducing information asymmetry prevents market for lemons.",
    },
    "due_diligence": {
        "name": "Supply Chain Due Diligence (CS3D-style)",
        "description": "Mandatory human rights and environmental due diligence",
        "parameters": {
            "tiers_covered": {"min": 1, "max": 4, "default": 2, "unit": "tiers"},
            "liability_regime": {"options": ["civil", "administrative", "criminal"], "default": "civil"},
            "safe_harbour": {"type": "bool", "default": True},
        },
        "effects": {
            "compliance_cost_per_tier": 300_000,
            "supply_chain_risk_reduction": -0.10,
            "social_license_boost": 5,
            "operational_friction": 0.02,
        },
        "theory": "Ruggie (2011): UN Guiding Principles on Business and Human Rights.",
    },
    "nature_regulation": {
        "name": "Nature Restoration Law (EU NRL-style)",
        "description": "Binding targets for ecosystem restoration",
        "parameters": {
            "restoration_target_pct": {"min": 10, "max": 50, "default": 20, "unit": "% of degraded land"},
            "reporting_frequency": {"options": ["annual", "biennial"], "default": "annual"},
            "financial_penalty_per_hectare": {"min": 1000, "max": 50000, "default": 10000, "unit": "$/ha"},
        },
        "effects": {
            "habitat_restoration_mandate": True,
            "ehi_target_bonus": 5,
            "compliance_cost": 750_000,
        },
        "theory": "Dasgupta (2021): Nature as asset requiring regulatory protection.",
    },
    "just_transition_fund": {
        "name": "Just Transition Fund (mandatory contribution)",
        "description": "Mandatory corporate contributions to worker transition",
        "parameters": {
            "contribution_rate_pct": {"min": 0.5, "max": 5.0, "default": 1.0, "unit": "% of revenue"},
            "eligibility": {"options": ["all_workers", "displaced_only", "community"], "default": "displaced_only"},
        },
        "effects": {
            "treasury_cost_pct_revenue": 0.01,
            "social_license_boost": 8,
            "strike_probability_reduction": -0.15,
            "burnout_reduction": -5,
        },
        "theory": "ILO (2015): Guidelines for a Just Transition towards sustainable economies.",
    },
}


# ═══════════════════════════════════════════════════════════════
#  SANDBOX SIMULATION
# ═══════════════════════════════════════════════════════════════

def create_sandbox_state() -> dict[str, Any]:
    """Create initial regulatory sandbox state."""
    return {
        "active_regulations": [],
        "regulation_history": [],
        "regulatory_complexity_index": 0.0,  # 0-100
        "compliance_burden_total": 0.0,
        "regulatory_capture_risk": 0.0,  # Stigler (1971) warning
        "sandbox_mode": False,
        "audit_log": [],              # Per-round effect diagnostics
    }


# ═══════════════════════════════════════════════════════════════
#  DECAY FACTORS — Time-series attenuation per instrument
#  Grounded in regulatory economics literature:
#   - Learning-curve theory (Arrow 1962): compliance costs halve
#     as organisations build internal routines over ~2 years.
#   - Goodhart's Law: once a measure becomes a target, its
#     behavioural impact attenuates (social license signal decay).
#   - Declining free allocation schedules: ETS permits phase out,
#     increasing real permit cost pressure per round.
# ═══════════════════════════════════════════════════════════════

DECAY_FACTORS: dict[str, dict[str, float]] = {
    # carbon_tax: NO decay — escalation encoded directly in rate formula
    "carbon_tax": {},

    # Emissions Trading: free allocation phases out at 5%/round → rising
    # effective permit cost. Modelled as an ESCALATION not a decay.
    "emissions_trading": {
        "free_allocation_decay_per_round": 0.05,   # 5% less free allocation each round
        "permit_cost_escalation_per_round": 0.08,   # 8% permit price growth (supply tightens)
    },

    # Mandatory Disclosure: compliance cost halves by round 3 (learning curve).
    # Reputation boost also decays — market discounts repeated disclosures.
    "mandatory_disclosure": {
        "cost_decay_rate": 0.40,        # 40% cost reduction per round after first (Arrow 1962)
        "cost_floor_fraction": 0.20,    # minimum = 20% of initial (ongoing assurance costs)
        "rep_boost_decay_rate": 0.30,   # reputation benefit attenuates 30%/round
    },

    # Due Diligence: audit routines mature → per-tier costs fall 10%/round
    # but social license boost also decays as it becomes table-stakes.
    "due_diligence": {
        "cost_decay_rate": 0.10,        # 10% cost reduction per round
        "cost_floor_fraction": 0.50,    # minimum = 50% (permanent audit overhead)
        "slo_boost_decay_rate": 0.20,   # social license benefit decays 20%/round
    },

    # Nature Restoration: upfront investment yields permanence — cost decays
    # steeply as restoration areas are completed, then stabilises.
    "nature_regulation": {
        "cost_decay_rate": 0.15,        # 15% cost reduction per round
        "cost_floor_fraction": 0.30,    # minimum = 30% (ongoing monitoring)
        "ehi_bonus_escalation": 0.10,   # EHI bonus GROWS 10%/round (compounding restoration)
    },

    # Just Transition Fund: social license and strike probability effects decay
    # because: (a) goodwill has a half-life, (b) workers expect more over time.
    "just_transition_fund": {
        "slo_boost_decay_rate": 0.30,   # 30% decay in SLO boost per round
        "strike_reduction_decay_rate": 0.25,  # 25% decay in strike benefit per round
        "cost_pct_is_fixed": True,      # Treasury cost does NOT decay (legal obligation)
    },
}


def _decayed_value(initial: float, decay_rate: float, rounds_active: int,
                   floor_fraction: float = 0.0) -> float:
    """Apply exponential decay: value = initial × (1 - rate)^rounds, floored at initial × floor."""
    decayed = initial * ((1 - decay_rate) ** rounds_active)
    floor = initial * floor_fraction
    return max(floor, decayed)




def activate_regulation(
    sandbox_state: dict,
    instrument_id: str,
    custom_params: dict,
    round_number: int,
) -> dict:
    """
    Activate a regulatory instrument with custom parameters.
    Returns the regulation record and projected effects.
    """
    instrument = REGULATORY_INSTRUMENTS.get(instrument_id)
    if not instrument:
        return {"error": f"Unknown instrument: {instrument_id}"}

    # Merge custom params with defaults
    final_params = {}
    for param_name, param_config in instrument["parameters"].items():
        if param_name in custom_params:
            val = custom_params[param_name]
            # Validate bounds
            if "min" in param_config and isinstance(val, (int, float)):
                val = max(param_config["min"], min(param_config["max"], val))
            final_params[param_name] = val
        else:
            final_params[param_name] = param_config.get("default")

    regulation = {
        "instrument_id": instrument_id,
        "name": instrument["name"],
        "parameters": final_params,
        "activated_round": round_number,
        "effects": instrument["effects"],
        "theory": instrument["theory"],
    }

    sandbox_state["active_regulations"].append(regulation)
    sandbox_state["regulation_history"].append({
        "action": "activated",
        "instrument": instrument_id,
        "round": round_number,
        "params": final_params,
    })

    # Update complexity index
    sandbox_state["regulatory_complexity_index"] = min(
        100, len(sandbox_state["active_regulations"]) * 15
    )

    # Regulatory capture warning (Stigler 1971)
    if len(sandbox_state["active_regulations"]) > 4:
        sandbox_state["regulatory_capture_risk"] = min(
            100, (len(sandbox_state["active_regulations"]) - 4) * 20
        )

    return {
        "regulation": regulation,
        "complexity_index": sandbox_state["regulatory_complexity_index"],
        "capture_risk": sandbox_state["regulatory_capture_risk"],
        "message": (
            f"📋 Regulation activated: {instrument['name']}. "
            f"Regulatory complexity: {sandbox_state['regulatory_complexity_index']:.0f}/100."
        ),
        "capture_warning": (
            f"⚠️ REGULATORY CAPTURE RISK ({sandbox_state['regulatory_capture_risk']:.0f}%): "
            f"Stigler (1971) warns that excessive regulation complexity creates "
            f"opportunities for regulatory capture. Consider simplification."
            if sandbox_state["regulatory_capture_risk"] > 40
            else None
        ),
    }



def apply_sandbox_effects(
    sandbox_state: dict,
    gs: dict,
    bus: list[dict],
    round_number: int,
) -> dict:
    """
    Apply effects of all active regulations to the game state.
    Uses time-series decay (DECAY_FACTORS) so compliance costs and benefit
    signals attenuate realistically across rounds (Arrow 1962 learning curve,
    Goodhart's Law, ETS free-allocation phase-out schedule).
    Returns diagnostics of all regulatory effects applied.
    """
    if not sandbox_state.get("sandbox_mode") or not sandbox_state.get("active_regulations"):
        return {}

    diagnostics: dict[str, Any] = {"regulations_applied": [], "round": round_number}
    total_compliance_cost = 0.0

    for reg in sandbox_state["active_regulations"]:
        inst_id = reg["instrument_id"]
        effects = reg["effects"]
        params = reg["parameters"]
        rounds_active = max(0, round_number - reg.get("activated_round", round_number))
        df = DECAY_FACTORS.get(inst_id, {})
        reg_diag: dict[str, Any] = {
            "instrument": inst_id,
            "name": reg["name"],
            "rounds_active": rounds_active,
        }

        # ── Carbon Tax ──────────────────────────────────────────────
        if inst_id == "carbon_tax":
            rate = params.get("rate_per_tonne", 50)
            escalation = params.get("annual_escalation_pct", 5) / 100
            current_rate = rate * (1 + escalation) ** rounds_active
            avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
            tax_cost = round(avg_ci * current_rate * len(bus) * 100, 2)
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - tax_cost, 2)
            total_compliance_cost += tax_cost
            reg_diag["carbon_tax_paid"] = tax_cost
            reg_diag["current_rate"] = round(current_rate, 2)
            reg_diag["decay_note"] = f"Escalating at {escalation*100:.0f}%/round — Pigou (1920)."

        # ── Emissions Trading System ────────────────────────────────
        elif inst_id == "emissions_trading":
            base_permit = effects.get("permit_cost_base", 45)
            # Free allocation phases out (decaying) → effective permit cost escalates
            free_alloc_pct = max(0.0, params.get("free_allocation_pct", 50) / 100
                                 - df.get("free_allocation_decay_per_round", 0.05) * rounds_active)
            escalation = df.get("permit_cost_escalation_per_round", 0.08)
            permit_price = base_permit * (1 + escalation) ** rounds_active
            effective_cost = permit_price * (1 - free_alloc_pct)
            avg_ci = sum(bu.get("carbon_intensity", 50) for bu in bus) / max(len(bus), 1)
            ets_cost = round(avg_ci * effective_cost * len(bus) * 50, 2)
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - ets_cost, 2)
            total_compliance_cost += ets_cost
            reg_diag["ets_cost"] = ets_cost
            reg_diag["permit_price"] = round(permit_price, 2)
            reg_diag["free_alloc_pct"] = round(free_alloc_pct * 100, 1)
            reg_diag["decay_note"] = (
                f"Free allocation decayed to {free_alloc_pct*100:.1f}%; "
                f"permit price escalated to ${permit_price:.0f}/t — Coase (1960)."
            )

        # ── Mandatory Disclosure ────────────────────────────────────
        elif inst_id == "mandatory_disclosure":
            base_cost = effects.get("compliance_cost", 500_000)
            cost = round(_decayed_value(
                base_cost,
                df.get("cost_decay_rate", 0.40),
                rounds_active,
                df.get("cost_floor_fraction", 0.20),
            ), 2)
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - cost, 2)
            total_compliance_cost += cost

            # Governance risk reduction: constant (structural change, no decay)
            for bu in bus:
                bu["governance_risk_score"] = max(
                    0, round(bu.get("governance_risk_score", 20) + effects.get("governance_risk_reduction", 0), 2)
                )

            # Reputation boost decays (market discounts repeated disclosures)
            base_rep = effects.get("reputation_boost", 3)
            rep_boost = round(_decayed_value(base_rep, df.get("rep_boost_decay_rate", 0.30), rounds_active), 2)
            gs["group_reputation"] = min(100, round(gs.get("group_reputation", 50) + rep_boost, 2))

            reg_diag["compliance_cost"] = cost
            reg_diag["rep_boost_applied"] = rep_boost
            reg_diag["decay_note"] = (
                f"Cost decayed to ${cost:,.0f} (Arrow 1962 learning curve); "
                f"rep boost decayed to +{rep_boost:.1f}pts (Goodhart's Law)."
            )

        # ── Just Transition Fund ────────────────────────────────────
        elif inst_id == "just_transition_fund":
            total_rev = sum(bu.get("revenue_base", 0) for bu in bus)
            contribution = round(total_rev * params.get("contribution_rate_pct", 1.0) / 100, 2)
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - contribution, 2)
            total_compliance_cost += contribution

            # SLO boost decays (goodwill half-life)
            base_slo = effects.get("social_license_boost", 8) / 4
            slo_boost = round(_decayed_value(base_slo, df.get("slo_boost_decay_rate", 0.30), rounds_active), 2)
            # Burnout reduction: constant (structural wage improvement)
            burnout_red = effects.get("burnout_reduction", -5) / 4
            for bu in bus:
                bu["social_license_score"] = min(100, round(bu.get("social_license_score", 50) + slo_boost, 2))
                bu["staff_burnout_index"] = max(0, round(bu.get("staff_burnout_index", 0) + burnout_red, 2))

            reg_diag["contribution_paid"] = contribution
            reg_diag["slo_boost_applied"] = slo_boost
            reg_diag["decay_note"] = (
                f"SLO boost decayed to +{slo_boost:.2f}pts/BU — "
                f"goodwill half-life (ILO 2015). Contribution fixed at ${contribution:,.0f}."
            )

        # ── Due Diligence ───────────────────────────────────────────
        elif inst_id == "due_diligence":
            tiers = params.get("tiers_covered", 2)
            base_cost_per_tier = effects.get("compliance_cost_per_tier", 300_000)
            effective_cost_per_tier = _decayed_value(
                base_cost_per_tier,
                df.get("cost_decay_rate", 0.10),
                rounds_active,
                df.get("cost_floor_fraction", 0.50),
            )
            cost = round(effective_cost_per_tier * tiers, 2)
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - cost, 2)
            total_compliance_cost += cost

            # SLO boost decays (due diligence becomes table-stakes)
            base_slo = effects.get("social_license_boost", 5) / 4
            slo_boost = round(_decayed_value(base_slo, df.get("slo_boost_decay_rate", 0.20), rounds_active), 2)
            for bu in bus:
                bu["social_license_score"] = min(100, round(bu.get("social_license_score", 50) + slo_boost, 2))

            reg_diag["dd_cost"] = cost
            reg_diag["tiers_audited"] = tiers
            reg_diag["slo_boost_applied"] = slo_boost
            reg_diag["decay_note"] = (
                f"Per-tier cost decayed to ${effective_cost_per_tier:,.0f} "
                f"(audit routines mature); SLO boost decayed to +{slo_boost:.2f}pts — Ruggie (2011)."
            )

        # ── Nature Restoration Law ──────────────────────────────────
        elif inst_id == "nature_regulation":
            base_cost = effects.get("compliance_cost", 750_000)
            cost = round(_decayed_value(
                base_cost,
                df.get("cost_decay_rate", 0.15),
                rounds_active,
                df.get("cost_floor_fraction", 0.30),
            ), 2)
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - cost, 2)
            total_compliance_cost += cost

            # EHI bonus ESCALATES (compounding restoration investment)
            base_ehi = effects.get("ehi_target_bonus", 5)
            ehi_escalation = df.get("ehi_bonus_escalation", 0.10)
            ehi_bonus = round(base_ehi * (1 + ehi_escalation) ** rounds_active, 2)
            bio = gs.get("biodiversity_state", {})
            if bio:
                bio["ecosystem_health_index"] = min(
                    100, round(bio.get("ecosystem_health_index", 50) + ehi_bonus, 2)
                )
                gs["biodiversity_state"] = bio

            reg_diag["restoration_cost"] = cost
            reg_diag["ehi_bonus_applied"] = ehi_bonus
            reg_diag["decay_note"] = (
                f"Restoration cost decayed to ${cost:,.0f} (projects complete); "
                f"EHI bonus escalated to +{ehi_bonus:.1f}pts — Dasgupta (2021)."
            )

        diagnostics["regulations_applied"].append(reg_diag)

    sandbox_state["compliance_burden_total"] = round(
        sandbox_state.get("compliance_burden_total", 0) + total_compliance_cost, 2
    )
    diagnostics["total_compliance_cost_this_round"] = total_compliance_cost
    diagnostics["cumulative_compliance_burden"] = sandbox_state["compliance_burden_total"]

    # Persist this round's diagnostics to audit_log for facilitator visibility
    if "audit_log" not in sandbox_state:
        sandbox_state["audit_log"] = []
    sandbox_state["audit_log"].append(diagnostics)

    # Ostrom (2009): Polycentric governance insight
    if len(sandbox_state["active_regulations"]) >= 3:
        diagnostics["polycentric_governance_note"] = (
            "📚 Ostrom (2009): You're experiencing polycentric governance — "
            "multiple overlapping regulatory instruments. While complex, "
            "polycentric systems can be more resilient than single-instrument "
            "approaches if well-coordinated."
        )

    return diagnostics
