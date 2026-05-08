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


# ═══════════════════════════════════════════════════════════════
#  MIDDLEWARE INTERCEPT CONTROLLER
#  Intercepts the state-transition loop BEFORE values are
#  finalized in global_state.  Applies custom modifier functions
#  representing sudden, exogenous policy shifts.
#
#  Called from round_logic.run_new_engines() BEFORE the sandbox
#  effects are applied, so it can inject or modify regulations
#  on-the-fly based on current state conditions.
# ═══════════════════════════════════════════════════════════════

# ── Exogenous Event Registry ─────────────────────────────────

EXOGENOUS_EVENTS: dict[str, dict] = {
    "carbon_minsky_moment": {
        "name": "The Carbon Minsky Moment",
        "description": (
            "High Natural Capital Debt combined with sandbox carbon taxation "
            "creates a compounding interest spiral that makes debt unmanageable, "
            "forcing immediate divestment or turnaround mode."
        ),
        "trigger_rounds": [7, 8, 9],
        "trigger_conditions": {
            "min_ncd_threshold": 200,
            "requires_sandbox_tax": True,
        },
        "effects": {
            "ncd_interest_rate_bps_increase": 200,
            "treasury_pct_hit": -0.05,
            "reputation_delta": -8,
            "forced_divestment_mode": True,
        },
        "theory": (
            "Carney (2015): 'Tragedy of the Horizon' — financial assets become "
            "stranded when climate externalities are suddenly priced in."
        ),
        "icon": "💥",
        "severity": "critical",
    },
    "csddd_enforcement": {
        "name": "CSDDD Enforcement Action",
        "description": (
            "Corporate Sustainability Due Diligence Directive enforcement. "
            "A whistleblower triggers a €30M+ fine or operational suspension "
            "for the worst-performing Business Unit."
        ),
        "trigger_rounds": [7, 8, 9],
        "trigger_conditions": {
            "max_reputation_threshold": 40,
            "whistleblower_probability": 0.6,
        },
        "effects": {
            "fine_amount": 30_000_000,
            "worst_bu_suspension_rounds": 1,
            "governance_risk_delta": 15,
            "reputation_delta": -12,
        },
        "theory": (
            "EU CS3D (2024): Mandatory human-rights and environmental due "
            "diligence with civil liability for non-compliance."
        ),
        "icon": "⚖️",
        "severity": "critical",
    },
    "polycentric_water_shock": {
        "name": "Polycentric Water Shock",
        "description": (
            "Community activists (Megha Patrike) obtain a court injunction "
            "blocking facility access due to critical water stress, "
            "increasing OPEX by 15%."
        ),
        "trigger_rounds": [8],
        "trigger_conditions": {
            "min_water_stress": 0.6,
            "requires_community_agent": True,
        },
        "effects": {
            "opex_pct_increase": 0.15,
            "social_license_delta": -15,
            "reputation_delta": -10,
            "facility_injunction": True,
            "legal_costs": 5_000_000,
        },
        "theory": (
            "Coase (1960): When property rights over common-pool resources "
            "(water) are legally contested, operational friction increases. "
            "Ostrom (2009): Polycentric governance allows local actors to "
            "enforce resource boundaries."
        ),
        "icon": "🌊",
        "severity": "critical",
    },
}


def calc_pigouvian_penalty_per_bu(
    bu: dict,
    tax_rate_per_ton: float,
) -> tuple[float, dict]:
    """
    Pigouvian Penalty (Expert Tier):
      Penalty = BU_Carbon_Emissions × Custom_Tax_Rate_Per_Ton

    Carbon emissions proxy = carbon_intensity × revenue_base / 1_000_000
    (tonnes CO2e estimated from CI score and revenue scale).
    """
    ci = bu.get("carbon_intensity", 50)
    revenue = bu.get("revenue_base", 0)
    # Proxy: CI × revenue / 1M → estimated tonnes CO2e
    estimated_tonnes = round(ci * revenue / 1_000_000, 2)
    penalty = round(estimated_tonnes * tax_rate_per_ton, 2)

    return penalty, {
        "bu_id": bu.get("bu_id", "unknown"),
        "carbon_intensity": ci,
        "estimated_tonnes_co2e": estimated_tonnes,
        "tax_rate_per_ton": tax_rate_per_ton,
        "penalty": penalty,
        "formula": "Penalty = BU_Carbon_Emissions × Tax_Rate_Per_Ton",
        "theory": "Pigou (1920): Direct levy on 'bads' to internalise externalities.",
    }


def check_carbon_minsky_moment(
    bu: dict,
    ncd_threshold: float = 200,
    bps_increase: int = 200,
) -> tuple[bool, dict]:
    """
    Carbon Minsky Moment trigger:
    If BU's Natural Capital Debt exceeds threshold, increase the
    NCD interest rate by an additional `bps_increase` basis points.

    Carney (2015): Once NCD spirals past a critical threshold,
    compounding interest makes the debt unmanageable.
    """
    ncd = bu.get("natural_capital_debt", 0)
    triggered = ncd > ncd_threshold
    rate_increase = bps_increase / 10_000 if triggered else 0.0

    return triggered, {
        "bu_id": bu.get("bu_id", "unknown"),
        "natural_capital_debt": ncd,
        "threshold": ncd_threshold,
        "triggered": triggered,
        "interest_rate_increase": rate_increase,
        "bps_increase": bps_increase if triggered else 0,
        "theory": (
            "Carbon Minsky Moment: NCD exceeds critical threshold → "
            "compounding interest spiral. Carney (2015)."
        ),
    }


def calc_coasian_friction(
    bu: dict,
    water_stress: float,
    legal_dispute_active: bool = False,
) -> tuple[float, dict]:
    """
    Coasian Property Rights friction:
    When stakeholders claim property rights over common-pool resources
    (e.g., water), legal costs and operational friction increase.

    Friction = base_friction × (1 + water_dependency × water_stress)
    If legal_dispute_active: friction doubles (court costs, delays).
    """
    water_dep = bu.get("water_dependency", 0.3)
    base_friction = 0.02  # 2% baseline operational friction
    friction = base_friction * (1 + water_dep * water_stress)
    if legal_dispute_active:
        friction *= 2.0
    friction = round(min(friction, 0.20), 4)  # Cap at 20%

    opex_increase = round(bu.get("opex_base", 0) * friction, 2)

    return opex_increase, {
        "bu_id": bu.get("bu_id", "unknown"),
        "water_dependency": water_dep,
        "water_stress": water_stress,
        "legal_dispute_active": legal_dispute_active,
        "friction_rate": friction,
        "opex_increase": opex_increase,
        "theory": "Coase (1960): Property rights disputes increase transaction costs.",
    }


def calc_polycentric_burden(
    bu: dict,
    event_config: dict,
) -> tuple[float, dict]:
    """
    Polycentric Governance (Ostrom 2009):
    Asymmetrical regulatory burden based on BU industrial footprint.
    High-CI BUs face carbon-weighted burdens.
    High water-dependency BUs face water-weighted burdens.
    """
    ci = bu.get("carbon_intensity", 50)
    water_dep = bu.get("water_dependency", 0.3)
    revenue = bu.get("revenue_base", 0)

    # Carbon-weighted burden: 0-5% of revenue based on CI
    carbon_weight = min(ci / 100, 1.0) * 0.05
    # Water-weighted burden: 0-3% of revenue based on water dependency
    water_weight = min(water_dep, 1.0) * 0.03

    total_burden_rate = round(carbon_weight + water_weight, 4)
    burden_cost = round(revenue * total_burden_rate, 2)

    return burden_cost, {
        "bu_id": bu.get("bu_id", "unknown"),
        "carbon_weight": round(carbon_weight, 4),
        "water_weight": round(water_weight, 4),
        "total_burden_rate": total_burden_rate,
        "burden_cost": burden_cost,
        "theory": (
            "Ostrom (2009): Polycentric governance allows asymmetric "
            "regulation matched to local industrial/geographic footprint."
        ),
    }


# ═══════════════════════════════════════════════════════════════
#  MIDDLEWARE INTERCEPT — called before values finalize
# ═══════════════════════════════════════════════════════════════

def intercept_state_transition(
    sandbox_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> dict:
    """
    Regulatory Sandbox Middleware Intercept.

    Called BEFORE sandbox effects are applied and BEFORE values
    are finalized in global_state.  Evaluates exogenous event
    trigger conditions and injects crisis modifiers.

    Returns diagnostics dict with all intercepted actions.
    """
    if not sandbox_state.get("sandbox_mode"):
        return {}

    diag: dict[str, Any] = {
        "intercept_round": round_number,
        "pigouvian_penalties": [],
        "minsky_triggers": [],
        "coasian_frictions": [],
        "polycentric_burdens": [],
        "exogenous_events_fired": [],
    }

    # ── 1. Per-BU Pigouvian Penalty ──────────────────────────
    active_carbon_tax = None
    for reg in sandbox_state.get("active_regulations", []):
        if reg["instrument_id"] == "carbon_tax":
            active_carbon_tax = reg
            break

    if active_carbon_tax:
        rate = active_carbon_tax["parameters"].get("rate_per_tonne", 50)
        rounds_active = max(0, round_number - active_carbon_tax.get("activated_round", round_number))
        escalation = active_carbon_tax["parameters"].get("annual_escalation_pct", 5) / 100
        current_rate = rate * (1 + escalation) ** rounds_active

        for bu in bus:
            penalty, pen_diag = calc_pigouvian_penalty_per_bu(bu, current_rate)
            diag["pigouvian_penalties"].append(pen_diag)

            # Apply penalty to BU OPEX (not treasury — this is a direct cost)
            bu["opex_base"] = round(bu["opex_base"] + penalty, 2)

            # ── 2. Carbon Minsky Moment check ────────────────
            triggered, minsky_diag = check_carbon_minsky_moment(
                bu,
                ncd_threshold=sandbox_state.get("minsky_ncd_threshold", 200),
                bps_increase=sandbox_state.get("minsky_bps_increase", 200),
            )
            diag["minsky_triggers"].append(minsky_diag)

            if triggered:
                # Increase NCD interest accrual for this BU
                ncd = bu.get("natural_capital_debt", 0)
                rate_bump = minsky_diag["interest_rate_increase"]
                extra_interest = round(ncd * rate_bump, 2)
                bu["natural_capital_debt"] = round(ncd + extra_interest, 2)

    # ── 3. Coasian Property Rights Friction ──────────────────
    bio = gs.get("biodiversity_state", {})
    water_stress = bio.get("water_stress_index", 0.4)
    legal_dispute = sandbox_state.get("coasian_legal_dispute_active", False)

    if water_stress > 0.4 or legal_dispute:
        for bu in bus:
            cost, coase_diag = calc_coasian_friction(bu, water_stress, legal_dispute)
            diag["coasian_frictions"].append(coase_diag)
            if cost > 0:
                bu["opex_base"] = round(bu["opex_base"] + cost, 2)

    # ── 4. Polycentric Asymmetric Burdens ────────────────────
    if len(sandbox_state.get("active_regulations", [])) >= 2:
        for bu in bus:
            burden, poly_diag = calc_polycentric_burden(bu, {})
            diag["polycentric_burdens"].append(poly_diag)
            gs["corporate_treasury"] = round(
                gs.get("corporate_treasury", 0) - burden, 2
            )

    # ── 5. Exogenous Event Evaluation (R7-R9) ────────────────
    for event_id, event_cfg in EXOGENOUS_EVENTS.items():
        if round_number not in event_cfg["trigger_rounds"]:
            continue
        # Skip if already fired this session
        fired_key = f"exogenous_{event_id}_fired"
        if sandbox_state.get(fired_key):
            continue

        fired = _evaluate_exogenous_trigger(
            event_id, event_cfg, sandbox_state, gs, bus, events, round_number
        )
        if fired:
            diag["exogenous_events_fired"].append(fired)
            sandbox_state[fired_key] = round_number

    # Persist diagnostics
    sandbox_state.setdefault("intercept_log", []).append(diag)
    return diag


def _evaluate_exogenous_trigger(
    event_id: str,
    event_cfg: dict,
    sandbox_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> dict | None:
    """Evaluate whether an exogenous event's trigger conditions are met."""
    conds = event_cfg["trigger_conditions"]
    effects = event_cfg["effects"]

    if event_id == "carbon_minsky_moment":
        # Requires sandbox carbon tax active + any BU NCD > threshold
        has_tax = any(
            r["instrument_id"] == "carbon_tax"
            for r in sandbox_state.get("active_regulations", [])
        )
        if not has_tax and conds.get("requires_sandbox_tax"):
            return None
        threshold = conds.get("min_ncd_threshold", 200)
        breaching_bus = [
            bu for bu in bus
            if bu.get("natural_capital_debt", 0) > threshold
        ]
        if not breaching_bus:
            return None

        # Fire: apply compounding interest spike + treasury hit
        for bu in breaching_bus:
            ncd = bu.get("natural_capital_debt", 0)
            rate_bump = effects["ncd_interest_rate_bps_increase"] / 10_000
            bu["natural_capital_debt"] = round(ncd * (1 + rate_bump), 2)

        treasury_hit = round(
            gs.get("corporate_treasury", 0) * abs(effects.get("treasury_pct_hit", 0)), 2
        )
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - treasury_hit, 2)
        gs["group_reputation"] = max(0, round(
            gs.get("group_reputation", 50) + effects.get("reputation_delta", 0), 2
        ))

        # Surface as crisis event
        events.setdefault("custom_black_swans", []).append({
            "title": f"{event_cfg['icon']} {event_cfg['name']}",
            "narrative": event_cfg["description"],
            "icon": event_cfg["icon"],
            "severity": event_cfg["severity"],
        })
        return {
            "event_id": event_id,
            "name": event_cfg["name"],
            "round": round_number,
            "treasury_hit": treasury_hit,
            "breaching_bus": [bu["bu_id"] for bu in breaching_bus],
            "theory": event_cfg["theory"],
        }

    elif event_id == "csddd_enforcement":
        rep = gs.get("group_reputation", 50)
        if rep > conds.get("max_reputation_threshold", 40):
            return None
        import random
        if random.random() > conds.get("whistleblower_probability", 0.6):
            return None

        fine = effects.get("fine_amount", 30_000_000)
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - fine, 2)
        gs["group_reputation"] = max(0, round(
            gs.get("group_reputation", 50) + effects.get("reputation_delta", 0), 2
        ))
        # Worst BU gets governance risk spike
        worst_bu = min(bus, key=lambda b: b.get("social_license_score", 50))
        worst_bu["governance_risk_score"] = min(100, round(
            worst_bu.get("governance_risk_score", 20) + effects.get("governance_risk_delta", 0), 2
        ))

        events.setdefault("custom_black_swans", []).append({
            "title": f"{event_cfg['icon']} {event_cfg['name']}",
            "narrative": event_cfg["description"],
            "icon": event_cfg["icon"],
            "severity": event_cfg["severity"],
        })
        return {
            "event_id": event_id,
            "name": event_cfg["name"],
            "round": round_number,
            "fine": fine,
            "worst_bu": worst_bu.get("bu_id", "unknown"),
            "theory": event_cfg["theory"],
        }

    elif event_id == "polycentric_water_shock":
        bio = gs.get("biodiversity_state", {})
        water_stress = bio.get("water_stress_index", 0.4)
        if water_stress < conds.get("min_water_stress", 0.6):
            return None

        # Apply: +15% OPEX across all BUs
        for bu in bus:
            bu["opex_base"] = round(
                bu["opex_base"] * (1 + effects.get("opex_pct_increase", 0.15)), 2
            )
            bu["social_license_score"] = max(0, round(
                bu.get("social_license_score", 50) + effects.get("social_license_delta", 0), 2
            ))
        gs["group_reputation"] = max(0, round(
            gs.get("group_reputation", 50) + effects.get("reputation_delta", 0), 2
        ))
        legal = effects.get("legal_costs", 5_000_000)
        gs["corporate_treasury"] = round(gs["corporate_treasury"] - legal, 2)

        # Activate Coasian legal dispute flag for subsequent rounds
        sandbox_state["coasian_legal_dispute_active"] = True

        events.setdefault("custom_black_swans", []).append({
            "title": f"{event_cfg['icon']} {event_cfg['name']}",
            "narrative": event_cfg["description"],
            "icon": event_cfg["icon"],
            "severity": event_cfg["severity"],
        })
        return {
            "event_id": event_id,
            "name": event_cfg["name"],
            "round": round_number,
            "water_stress": water_stress,
            "legal_costs": legal,
            "theory": event_cfg["theory"],
        }

    return None


# ═══════════════════════════════════════════════════════════════
#  AGENT CROSS-WIRING
#  When sandbox shocks push autonomous agent tolerance below
#  their 'triggered' threshold, execute cascade chain immediately.
# ═══════════════════════════════════════════════════════════════

def crosswire_sandbox_to_agents(
    sandbox_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> dict:
    """
    Cross-wire sandbox injections to autonomous stakeholder agents.
    Checks if sandbox-induced state changes push any agent below
    their trigger thresholds.

    Agent mapping:
      - Eleanor Carson (the_regulator): governance_risk > 55 → 4% revenue fine
      - Marcus Chen-Hoffmann (the_institutional_investor): EBITDA < 0 → 8% treasury hit
      - Megha Patrike (the_community_activist): water stress → cascade

    Returns diagnostics of any agent triggers fired.
    """
    if not sandbox_state.get("sandbox_mode"):
        return {}

    diag: dict[str, Any] = {"agent_crosswire_triggers": []}

    # Read autonomous agent state
    aa = gs.get("autonomous_agents", {})
    if not aa.get("agents"):
        return diag

    # ── Eleanor Carson: Governance Risk breach ───────────────
    avg_gov = sum(bu.get("governance_risk_score", 20) for bu in bus) / max(len(bus), 1)
    regulator = aa["agents"].get("the_regulator", {})
    if (
        avg_gov > 55
        and regulator.get("triggered_round") is None
        and regulator.get("tolerance", 75) > 0
    ):
        # Push tolerance below triggered threshold
        regulator["tolerance"] = max(0, regulator["tolerance"] - 20)
        total_revenue = sum(bu.get("revenue_base", 0) for bu in bus)
        fine = round(total_revenue * 0.04, 2)
        gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0) - fine, 2)
        diag["agent_crosswire_triggers"].append({
            "agent": "the_regulator",
            "name": "Commissioner Eleanor Carson",
            "trigger": f"Governance Risk ({avg_gov:.1f}) > 55",
            "action": "4% revenue fine",
            "fine": fine,
            "new_tolerance": regulator["tolerance"],
        })
        events.setdefault("custom_black_swans", []).append({
            "title": "🏛️ REGULATORY FINE — Eleanor Carson",
            "narrative": (
                f"Commissioner Carson imposes emergency 4% revenue fine "
                f"(${fine:,.0f}) due to governance risk breach ({avg_gov:.1f}/100). "
                f"'Persistent governance failures will not be tolerated.'"
            ),
            "icon": "🏛️",
            "severity": "critical",
        })

        # ── CASCADE MULTIPLIER: Regulator → Journalist ──────────
        # When a regulatory probe fires, leaked subpoena documents
        # reduce the Journalist's tolerance — simulating a real-world
        # regulatory probe leaking to the press (domino effect).
        journalist = aa["agents"].get("the_journalist", {})
        if (
            journalist.get("triggered_round") is None
            and journalist.get("tolerance", 72) > 0
        ):
            old_tol = journalist.get("tolerance", 72)
            journalist["tolerance"] = max(0, old_tol - 10)
            diag["agent_crosswire_triggers"].append({
                "agent": "the_journalist",
                "name": "Jay Buffet (Cascade Multiplier)",
                "trigger": "Carson regulatory probe leaked to press",
                "action": "Tolerance −10 (Regulatory Leak → Media Amplification)",
                "old_tolerance": old_tol,
                "new_tolerance": journalist["tolerance"],
                "cascade_source": "the_regulator",
                "theory": (
                    "Cascade Multiplier — Herman & Chomsky (1988): "
                    "regulatory probes generate headline material, "
                    "creating a reinforcing feedback loop."
                ),
            })
            events.setdefault("custom_black_swans", []).append({
                "title": "📰 REGULATORY LEAK — Press Cascade",
                "narrative": (
                    f"Leaked subpoena documents from Commissioner Carson's investigation "
                    f"reach Jay Buffet's desk. Buffet begins drafting a 3-part exposé. "
                    f"Journalist tolerance drops from {old_tol} → {journalist['tolerance']}. "
                    f"'When the regulator knocks, the press follows.'"
                ),
                "icon": "📰",
                "severity": "warning",
            })

    # ── Marcus Chen-Hoffmann: Negative EBITDA ────────────────
    ebitda = sum(bu.get("revenue_base", 0) - bu.get("opex_base", 0) for bu in bus)
    investor = aa["agents"].get("the_institutional_investor", {})
    if (
        ebitda < 0
        and investor.get("triggered_round") is None
        and investor.get("tolerance", 80) > 0
    ):
        investor["tolerance"] = max(0, investor["tolerance"] - 25)
        treasury_hit = round(gs.get("corporate_treasury", 0) * 0.08, 2)
        gs["corporate_treasury"] = round(gs.get("corporate_treasury", 0) - treasury_hit, 2)
        diag["agent_crosswire_triggers"].append({
            "agent": "the_institutional_investor",
            "name": "Marcus Chen-Hoffmann",
            "trigger": f"EBITDA negative (${ebitda:,.0f})",
            "action": "Divestment fire sale — 8% treasury hit",
            "treasury_hit": treasury_hit,
            "new_tolerance": investor["tolerance"],
        })
        events.setdefault("custom_black_swans", []).append({
            "title": "📉 DIVESTMENT FIRE SALE — Marcus Chen-Hoffmann",
            "narrative": (
                f"Nordic Pension Alliance triggers full divestment. "
                f"'EBITDA is negative (${ebitda:,.0f}). We can no longer "
                f"justify this allocation.' Treasury hit: ${treasury_hit:,.0f}."
            ),
            "icon": "📉",
            "severity": "critical",
        })

    # Persist updated agent state
    gs["autonomous_agents"] = aa
    return diag


# ═══════════════════════════════════════════════════════════════
#  GOD MODE: TRIGGER EXOGENOUS EVENT MANUALLY
# ═══════════════════════════════════════════════════════════════

def trigger_exogenous_event(
    event_id: str,
    sandbox_state: dict,
    gs: dict,
    bus: list[dict],
    events: dict,
    round_number: int,
) -> dict:
    """
    Facilitator 'God Mode' — manually trigger an exogenous event
    regardless of whether conditions are met.
    """
    event_cfg = EXOGENOUS_EVENTS.get(event_id)
    if not event_cfg:
        return {"error": f"Unknown exogenous event: {event_id}"}

    # Force-fire the event (bypass condition checks)
    sandbox_state["sandbox_mode"] = True
    fired_key = f"exogenous_{event_id}_fired"

    if sandbox_state.get(fired_key):
        return {
            "error": f"Event '{event_id}' already fired in R{sandbox_state[fired_key]}",
            "already_fired_round": sandbox_state[fired_key],
        }

    result = _evaluate_exogenous_trigger(
        event_id, event_cfg, sandbox_state, gs, bus, events, round_number
    )

    if not result:
        # Force-apply effects directly since conditions weren't met
        efx = event_cfg["effects"]
        if efx.get("fine_amount"):
            gs["corporate_treasury"] = round(
                gs["corporate_treasury"] - efx["fine_amount"], 2
            )
        if efx.get("treasury_pct_hit"):
            hit = round(gs["corporate_treasury"] * abs(efx["treasury_pct_hit"]), 2)
            gs["corporate_treasury"] = round(gs["corporate_treasury"] - hit, 2)
        if efx.get("reputation_delta"):
            gs["group_reputation"] = max(0, round(
                gs.get("group_reputation", 50) + efx["reputation_delta"], 2
            ))
        if efx.get("opex_pct_increase"):
            for bu in bus:
                bu["opex_base"] = round(
                    bu["opex_base"] * (1 + efx["opex_pct_increase"]), 2
                )
        events.setdefault("custom_black_swans", []).append({
            "title": f"{event_cfg['icon']} {event_cfg['name']} (FORCED)",
            "narrative": event_cfg["description"],
            "icon": event_cfg["icon"],
            "severity": event_cfg["severity"],
        })
        result = {
            "event_id": event_id,
            "name": event_cfg["name"],
            "round": round_number,
            "forced": True,
            "theory": event_cfg["theory"],
        }

    sandbox_state[fired_key] = round_number
    return result
