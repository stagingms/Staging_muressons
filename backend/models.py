"""
Muressons Global Corporation — Pydantic Request / Response Models
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DecisionParadigm(str, Enum):
    legacy_abc = "legacy_abc"
    multi_toggles = "multi_toggles"
    # FIX AUDIT-021: Add missing paradigm to enum for Pydantic validation
    advanced_climate = "advanced_climate"
    healthcare = "healthcare"


# ── Enums ────────────────────────────────────────────────────────

class ConsensusLevel(str, Enum):
    unanimous = "unanimous"
    majority = "majority"
    split = "split"
    facilitator_override = "facilitator_override"


class MaterialityImpact(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class MaterialityCategory(str, Enum):
    economic = "economic"
    ecological = "ecological"
    social = "social"


# ── Materiality Config Models ────────────────────────────────────

class MaterialityIssue(BaseModel):
    id: str
    title: str
    hover_description: str
    category: str  # e.g., "ecological", "social", "economic"
    financial_impact: str  # "high", "medium", "low"
    societal_impact: str  # "high", "medium", "low"
    mitigation_cost_usd: int
    stakeholders_group: Optional[str] = ""
    stakeholders_subgroup: Optional[str] = ""
    nature_of_impact: Optional[str] = ""
    interdependency_1: Optional[str] = ""
    interdependency_2: Optional[str] = ""
    affected_bu_1: Optional[str] = ""
    affected_bu_2: Optional[str] = ""

class InterdependenceLink(BaseModel):
    id: str
    source_issue_id: str
    target_issue_id: str
    severity: int = Field(..., ge=1, le=5)  # 1 to 5
    description: str


class MaterialityConfig(BaseModel):
    consultant_fee_usd: int = 1500000
    issues: list[MaterialityIssue] = []
    interdependencies: list[InterdependenceLink] = []


# ── Materiality Submissions ───────────────────────────────────────

class MatrixSubmission(BaseModel):
    quadrant_1_top_right: list[str] = []
    quadrant_2_top_left: list[str] = []
    quadrant_3_bottom_right: list[str] = []
    quadrant_4_bottom_left: list[str] = []


class MaterialitySubmissionRequest(BaseModel):
    consultant_used: bool = False
    panel_issue_count: int = 4             # 1-8; tiered stakeholder panel pricing
    matrix_submission: MatrixSubmission
    force_override_cfo: bool = False
    bu_id: Optional[str] = None  # BU-specific dictionary for Strategic Pillars mode


class MaterialitySubmissionResponse(BaseModel):
    success: bool = True
    allocated_budget: int
    corporate_treasury: float
    message: str = "Success"
    debrief: Optional[dict] = None         # ESRS regulatory debrief card


# ── Config Models ────────────────────────────────────────────────

class ConsultantFeature(BaseModel):
    enabled: bool = True
    consultant_fee_usd: int = 1500000
    auto_solve_count: int = 5


class Round2Config(BaseModel):
    total_materiality_budget: int = 15000000
    consultant_feature: ConsultantFeature = Field(default_factory=ConsultantFeature)


# ── Shared Sub-Models ────────────────────────────────────────────

class GlobalStateOut(BaseModel):
    corporate_treasury: float
    group_reputation: float
    synergy_multiplier: float
    cost_of_capital: float
    active_event_flags: dict[str, Any] = {}
    historical_ebitda: Optional[float] = 0
    tco2e_emissions: Optional[float] = 0
    vrio_advantage: Optional[float] = 0
    vrio_capabilities: Optional[dict[str, Any]] = {}
    
    # FIX AUDIT-026: Tighten GlobalStateOut by explicitly defining fields
    # rather than allowing arbitrary extra fields.
    green_transition_fund: Optional[float] = 0.0
    tipping_point_active: Optional[bool] = False
    pending_capex_projects: Optional[list[dict]] = []
    bonus_score: Optional[int] = 0
    stakeholder_map_completed: Optional[bool] = False
    learning_bonuses_awarded: Optional[dict] = {}
    saved_allocations: Optional[dict] = {}
    saved_decision_choice: Optional[str] = None
    materiality_budget_allocated: Optional[list] = None
    materiality_bu_id: Optional[str] = None
    csrd_completed: Optional[bool] = False

    # Economic complexity engines
    inflation_index: Optional[float] = 0.025
    competitor_ebitda: Optional[float] = 0.0

    # UN SDG Edition metrics
    political_capital: Optional[float] = None
    community_trust_score: Optional[float] = None
    global_emissions_intensity: Optional[float] = None


class BUStateOut(BaseModel):
    bu_id: str
    name: str = ""
    revenue_base: float
    opex_base: float
    natural_capital_debt: float = 0
    social_license_score: float = 50
    reputation_score: float = 50
    governance_risk_score: float = 0
    water_dependency: float = 0
    carbon_intensity: float = 0
    risk_factors: dict[str, Any] = {}
    
    # Healthcare Mechanics
    patient_outcomes_score: Optional[float] = None
    staff_burnout_index: Optional[float] = None
    bed_capacity_utilization: Optional[float] = None


# ── POST /api/simulations/start ─────────────────────────────────

class StartSessionRequest(BaseModel):
    cohort_name: str = Field(..., min_length=1, max_length=120)
    facilitator_id: Optional[str] = None
    allowed_overrides: Optional[list[str]] = None
    allowed_swipes: Optional[list[str]] = None
    loan_interest_rate: float = Field(0.12, ge=0.0)
    decision_paradigm: str = "legacy_abc"  # 'legacy_abc' | 'multi_toggles'
    currency_symbol: Optional[str] = "$"   # Per-cohort display currency
    scenario_preset: Optional[str] = None  # Per-cohort engine preset id
    ending_pathway: Optional[str] = None   # Per-cohort ending pathway (R10 crisis)
    experience_level: Optional[str] = None  # Per-cohort unified preset (classroom/workshop/executive/chaos)
    difficulty_tier: Optional[str] = None   # Per-cohort visibility tier (foundation/advanced/expert)
    created_by: Optional[str] = None        # Who created this cohort
    created_when: Optional[str] = None      # When this cohort was created (YYYY-MM-DD)
    start_date: Optional[str] = None        # Cohort start date (YYYY-MM-DD) — game accessible from this date
    end_date: Optional[str] = None          # Cohort end date (YYYY-MM-DD) — game locked after this date


class StartSessionResponse(BaseModel):
    session_id: str
    round_number: int = 1
    global_state: GlobalStateOut
    business_units: list[BUStateOut]


# ── POST /api/simulations/{session_id}/commit-turn ──────────────

class BUDecision(BaseModel):
    bu_id: str
    investment_ratio: float = Field(0.0, ge=0.0, le=1.0)  # FIX VULN-002: was 1.5
    capex_allocated: float = Field(0.0, ge=0.0)  # Router enforces min $1
    choice_selected: str = ""
    decision_node_id: str = ""
    time_to_decision_seconds: int = Field(0, ge=0)
    team_consensus: ConsensusLevel = ConsensusLevel.majority
    pillar_decisions: Optional[dict] = None  # {energy, operations, supply_chain, offsetting}


class SaveDecisionsRequest(BaseModel):
    allocations: dict[str, float]
    decision_choice: Optional[str] = None


class CommitTurnRequest(BaseModel):
    dividends_paid: float = Field(0.0, ge=0.0)
    crisis_severity: float = Field(0.0, ge=0.0, le=100.0)
    imitation_decay_rate: float = Field(0.05, ge=0.0, le=1.0)
    decisions: list[BUDecision]
    force_override_cfo: bool = False
    # ITEM 1: Optimistic locking — client sends expected round
    expected_round: Optional[int] = None
    # Emergency credit line: +$1M at prevailing rate + 2%
    emergency_credit_used: bool = False


class CommitTurnResponse(BaseModel):
    session_id: str
    new_round_number: int
    global_state: GlobalStateOut
    business_units: list[BUStateOut]
    events: dict[str, Any] = {}


# ── GET /api/simulations/{session_id}/dashboard ─────────────────

class RoundSnapshot(BaseModel):
    round_number: int
    global_state: GlobalStateOut
    business_units: list[BUStateOut]


class DashboardResponse(BaseModel):
    session_id: str
    current_round: int
    global_state: GlobalStateOut
    business_units: list[BUStateOut]
    history: list[RoundSnapshot] = []
