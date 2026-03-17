"""
Muressons Global Command — Engine Unit Tests
Run: pytest tests/test_engine.py -v
"""

import sys
import os
import math

# Allow imports from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import (
    calc_csf,
    calc_contagion,
    calc_synergy_opex,
    calc_natural_capital_interest,
    calc_vrio_decay,
    calc_talent_braindrain,
    calc_strike_probability,
    apply_natural_decay,
    process_tick,
)


# ── Fixtures ─────────────────────────────────────────────────────

SEED_BUS = [
    {
        "bu_id": "pharma",
        "revenue_base": 18_000_000,
        "opex_base": 11_500_000,
        "natural_capital_debt": 0,
        "social_license_score": 55,
        "reputation_score": 52,
        "governance_risk_score": 15,
        "water_dependency": 82,
        "carbon_intensity": 45,
        "risk_factors": {},
    },
    {
        "bu_id": "electronics",
        "revenue_base": 16_500_000,
        "opex_base": 10_800_000,
        "natural_capital_debt": 0,
        "social_license_score": 48,
        "reputation_score": 50,
        "governance_risk_score": 20,
        "water_dependency": 58,
        "carbon_intensity": 72,
        "risk_factors": {},
    },
    {
        "bu_id": "consumer_goods",
        "revenue_base": 10_500_000,
        "opex_base": 7_800_000,
        "natural_capital_debt": 0,
        "social_license_score": 52,
        "reputation_score": 53,
        "governance_risk_score": 10,
        "water_dependency": 65,
        "carbon_intensity": 38,
        "risk_factors": {},
    },
    {
        "bu_id": "software",
        "revenue_base": 8_500_000,
        "opex_base": 4_200_000,
        "natural_capital_debt": 0,
        "social_license_score": 60,
        "reputation_score": 58,
        "governance_risk_score": 8,
        "water_dependency": 12,
        "carbon_intensity": 28,
        "risk_factors": {},
    },
]

SEED_GLOBAL = {
    "round_number": 1,
    "corporate_treasury": 50_000_000,
    "group_reputation": 50,
    "synergy_multiplier": 1.0,
    "cost_of_capital": 0.05,
    "active_event_flags": {},
}


# ── 1. CSF ───────────────────────────────────────────────────────

class TestCSF:
    def test_basic(self):
        result = calc_csf(SEED_BUS, dividends_paid=0)
        expected = (18e6 - 11.5e6) + (16.5e6 - 10.8e6) + (10.5e6 - 7.8e6) + (8.5e6 - 4.2e6)
        assert result == expected

    def test_with_dividends(self):
        result = calc_csf(SEED_BUS, dividends_paid=5_000_000)
        expected = (18e6 - 11.5e6) + (16.5e6 - 10.8e6) + (10.5e6 - 7.8e6) + (8.5e6 - 4.2e6) - 5e6
        assert result == expected


# ── 2. Contagion Engine ─────────────────────────────────────────

class TestContagion:
    def test_no_crisis(self):
        result = calc_contagion(SEED_BUS, crisis_severity=0)
        avg = (52 + 50 + 53 + 58) / 4
        assert result == round(avg, 2)

    def test_with_crisis(self):
        result = calc_contagion(SEED_BUS, crisis_severity=50)
        avg = (52 + 50 + 53 + 58) / 4
        expected = round(avg - 50 * 0.4, 2)
        assert result == expected

    def test_clamp_floor(self):
        result = calc_contagion(SEED_BUS, crisis_severity=250)
        assert result == 0.0


# ── 3. Synergy Engine ──────────────────────────────────────────

class TestSynergy:
    def test_zero_investment(self):
        result = calc_synergy_opex(10_000_000, 0.0, 1.0)
        assert result == 10_000_000

    def test_full_investment(self):
        result = calc_synergy_opex(10_000_000, 1.0, 1.0)
        assert result == 0.0

    def test_partial(self):
        result = calc_synergy_opex(10_000_000, 0.5, 1.0)
        assert result == 5_000_000

    def test_clamp_ratio(self):
        result = calc_synergy_opex(10_000_000, 1.5, 1.0)
        assert result == 0.0  # clamped to 1.0


# ── 4. Natural Capital Interest ─────────────────────────────────

class TestNaturalCapitalInterest:
    def test_no_debt(self):
        result = calc_natural_capital_interest(0.05, 0)
        assert result == 0.05

    def test_with_debt(self):
        result = calc_natural_capital_interest(0.05, 100)
        assert result == round(0.05 + 100 * 0.0005, 6)


# ── 5. VRIO Decay ──────────────────────────────────────────────

class TestVRIODecay:
    def test_basic(self):
        result = calc_vrio_decay(1.0, 0.05)
        assert result == round(1.0 * 0.95, 4)

    def test_no_decay(self):
        result = calc_vrio_decay(1.0, 0.0)
        assert result == 1.0

    def test_full_decay(self):
        result = calc_vrio_decay(1.0, 1.0)
        assert result == 0.0


# ── 6. Talent Brain-Drain ──────────────────────────────────────

class TestTalentBrainDrain:
    def test_high_reputation_no_penalty(self):
        opex, penalty = calc_talent_braindrain(4_200_000, 70)
        assert penalty == 1.0
        assert opex == 4_200_000

    def test_low_reputation_penalty(self):
        opex, penalty = calc_talent_braindrain(4_200_000, 50)
        expected_penalty = 1.0 + max(0, (65 - 50) / 100) * 1.5
        assert penalty == round(expected_penalty, 4)
        assert opex == round(4_200_000 * expected_penalty, 2)


# ── 7. Strike Probability ──────────────────────────────────────

class TestStrikeProbability:
    def test_perfect_social_license(self):
        result = calc_strike_probability(0.0, 100)
        assert result == 0.0

    def test_zero_social_license(self):
        result = calc_strike_probability(0.0, 0)
        assert result == 0.4

    def test_with_base_risk(self):
        result = calc_strike_probability(0.2, 50)
        expected = round(0.2 + (1 - 0.5) * 0.4, 4)
        assert result == expected


# ── 8. Natural Decay ───────────────────────────────────────────

class TestNaturalDecay:
    def test_no_decay_when_invested(self):
        rep, sl = apply_natural_decay(50, 60, invested=True)
        assert rep == 50
        assert sl == 60

    def test_decay_when_not_invested(self):
        rep, sl = apply_natural_decay(50, 60, invested=False)
        assert rep == round(50 * 0.98, 2)
        assert sl == round(60 * 0.98, 2)


# ── Integration: process_tick ───────────────────────────────────

class TestProcessTick:
    def test_basic_tick_advances_round(self):
        decisions = [
            {"bu_id": "pharma", "investment_ratio": 0.1, "capex_allocated": 500_000},
            {"bu_id": "electronics", "investment_ratio": 0.05, "capex_allocated": 200_000},
            {"bu_id": "consumer_goods", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "software", "investment_ratio": 0.0, "capex_allocated": 1},
        ]
        result = process_tick(SEED_GLOBAL, SEED_BUS, decisions)

        assert result["global_state"]["round_number"] == 2
        assert len(result["bu_states"]) == 4
        assert "strike_probabilities" in result["events"]
        assert "talent_penalty_applied" in result["events"]

    def test_treasury_changes(self):
        decisions = [
            {"bu_id": "pharma", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "electronics", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "consumer_goods", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "software", "investment_ratio": 0.0, "capex_allocated": 1},
        ]
        result = process_tick(SEED_GLOBAL, SEED_BUS, decisions, dividends_paid=0)

        gross = sum(bu["revenue_base"] - bu["opex_base"] for bu in SEED_BUS)
        expected_treasury = 50_000_000 + gross
        assert result["global_state"]["corporate_treasury"] == expected_treasury

    def test_synergy_decay(self):
        decisions = [
            {"bu_id": "pharma", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "electronics", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "consumer_goods", "investment_ratio": 0.0, "capex_allocated": 1},
            {"bu_id": "software", "investment_ratio": 0.0, "capex_allocated": 1},
        ]
        result = process_tick(
            SEED_GLOBAL, SEED_BUS, decisions, imitation_decay_rate=0.05
        )
        assert result["global_state"]["synergy_multiplier"] == round(1.0 * 0.95, 4)
