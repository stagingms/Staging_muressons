# Muressons Global Corporation — Architecture Blueprint

> **Purpose**: This document is the canonical reference for adding new logic modules to the Muressons simulation.
> Every new mechanic **must** complete this blueprint before any code is merged, to prevent logical drift and maintain simulation integrity.

---

## How to Use This Document

1. **Copy the Module Blueprint Template** (Section 2) into a new section below.
2. **Fill in all fields** before writing any code.
3. **Register the module** in the Module Registry (Section 3).
4. **Add edge-case tests** to `backend/validation_logic.py`.
5. **Commit `blueprint.md`** alongside the implementation PR.

---

## 1. Module Blueprint Template

Use the following structure for **every new logic module** added to the simulation:

| Section | Description |
|---|---|
| **System Goal** | Define the purpose of the new mechanic — what player behaviour or real-world system does it model? |
| **Logical Invariants** | Conditions that must remain true at all times (e.g., sum of assets = sum of liabilities + equity; scores clamped to [0, 100]). |
| **Data Dependencies** | Parameters pulled from `simulation_config.json` via `backend/config.py`, and any BU-state fields that must be present in the game state dict. |
| **Edge Cases** | Extreme or degenerate inputs to be tested in `backend/validation_logic.py` (e.g., empty BU list, zero revenue, `round_number` out of range). |

### Template (copy and fill in)

```
### Module: <Module Name>

**File**: `backend/<filename>.py`
**Added in**: Round / Version <X>
**Author**: <initials or team>

#### System Goal
<!-- What real-world mechanic does this module simulate?
     What player decision does it respond to? -->

#### Logical Invariants
<!-- List each invariant as a bullet:
  - Scores are clamped to [0, 100]
  - Sum of scope_1 + scope_2 + scope_3 ratios == 1.0 for every BU
  - CSF must equal gross_profit - dividends_paid exactly
-->

#### Data Dependencies
<!-- From simulation_config.json (loaded in backend/config.py):
  - SIM_ROUNDS, SIM_INITIAL_BUDGET
  - ECONOMIC_CARBON_PRICE_BASE, ECONOMIC_CARBON_PRICE_GROWTH
  - CONSTRAINT_MAX_CARBON_EMISSIONS, CONSTRAINT_MIN_LIQUIDITY_RATIO

  From game state dict (bu_states list):
  - bu_id, revenue_base, opex_base, carbon_intensity, reputation_score, ...
-->

#### Edge Cases
<!-- List test scenarios for backend/validation_logic.py:
  - Empty BU list (len == 0) → must return neutral/zero value, not raise
  - All revenues == 0 → fallback to simple mean (see calc_csf, _calc_rw_avg_ci)
  - crisis_severity < 0 → clamp to 0 before sigmoid
  - investment_ratio > 1.0 → clamp to 1.0
  - round_number outside [1, SIM_ROUNDS] → fallback to 0.0 modifier
-->
```

---

## 2. Registered Modules

Each module that has shipped is documented here in full. Modules are grouped by engine layer.

---

### 2.1 Carbon Accounting Helpers
**File**: [`backend/engine.py`](backend/engine.py) — top of file  
**Functions**: `get_scope_ratios`, `calc_revenue_weighted_avg_ci`, `apply_ci_delta_to_bus`

| Section | Detail |
|---|---|
| **System Goal** | Centralise all GHG Protocol Scope 1/2/3 calculations to ensure consistent carbon intensity accounting across all BUs and verticals. Replaces prior per-function scope estimates. |
| **Logical Invariants** | `scope_1 + scope_2 + scope_3 == 1.0` for every BU entry in `_ALL_BU_SCOPE_RATIOS`. Revenue-weighted avg CI falls back to simple mean when total revenue is zero. `carbon_intensity` is always `>= 0.0` after a delta is applied. |
| **Data Dependencies** | `ECONOMIC_CARBON_PRICE_BASE`, `ECONOMIC_CARBON_PRICE_GROWTH` from `config.py`; `bu_id`, `carbon_intensity`, `revenue_base` from `bu_states`. |
| **Edge Cases** | Empty `bus` list → return `_DEFAULT_SCOPE_RATIOS`; unknown `bu_id` → fallback to `_DEFAULT_SCOPE_RATIOS`; all revenues zero → simple arithmetic mean; negative `ci_delta` with `scope3_weighted` routing on low-Scope3 BU → verify `factor = 0.5 + 0.20 = 0.70`. |

---

### 2.2 Corporate Strategic Fund (CSF)
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_csf`

| Section | Detail |
|---|---|
| **System Goal** | Compute net cash added to the corporate treasury each round: `CSF = Σ(Revenue_Base − OPEX_Base) − Dividends_Paid`. |
| **Logical Invariants** | CSF may be negative (deficit round). The result must equal gross_profit minus dividends exactly (no rounding on the subtraction). |
| **Data Dependencies** | `revenue_base`, `opex_base` from every BU state dict; `dividends_paid` from player decision payload. |
| **Edge Cases** | Empty BU list → `gross_profit = 0`; `dividends_paid` larger than gross profit → negative CSF is valid; floating-point: sum then subtract to preserve precision. |

---

### 2.3 Contagion Engine (Sigmoid Model)
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_contagion`

| Section | Detail |
|---|---|
| **System Goal** | Model crisis propagation via an S-curve so that low-severity events have minimal reputation impact, mid-range events cause rapid erosion, and high-severity events plateau. `Group_Rep = Avg_Rep − 50 × sigmoid((severity − 30) / 15)`. |
| **Logical Invariants** | Output clamped to `[0, 100]`. `crisis_severity` is floored at `0` before the sigmoid (no negative severity). Empty `bu_states` returns `50.0`. |
| **Data Dependencies** | `reputation_score` per BU; `crisis_severity` from `black_swan_registry.py` or round event payload. |
| **Edge Cases** | `crisis_severity = 0` → minimal damage; `crisis_severity = 100` → near-maximum damage; empty `bu_states` → `50.0`; `crisis_severity < 0` → clamp to `0`. |

---

### 2.4 Synergy Engine (Diminishing Returns)
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_synergy_opex`

| Section | Detail |
|---|---|
| **System Goal** | Model efficiency gains from cross-BU investment with a square-root curve so early dollars yield outsized returns and later dollars face diminishing marginal efficiency. `New_OPEX = Old_OPEX × (1 − sqrt(ratio) × 0.7 × Synergy_Multiplier)`. |
| **Logical Invariants** | `investment_ratio` clamped to `[0.0, 1.0]`. Result (new OPEX) is always `>= 0.0`. |
| **Data Dependencies** | `opex_base` from BU state; `investment_ratio` and `synergy_multiplier` from round decisions / `round_configs.py`. |
| **Edge Cases** | `investment_ratio = 0` → no change; `investment_ratio = 1` → maximum reduction; `synergy_multiplier > 1.0` → verify OPEX doesn't go negative; `old_opex = 0` → return `0`. |

---

### 2.5 Natural Capital Cost of Debt
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_natural_capital_interest`

| Section | Detail |
|---|---|
| **System Goal** | Add a surcharge to the base interest rate proportional to the firm's Natural Capital Debt (NCD): `rate = base_rate + NCD × 0.0001`. Calibrated so NCD=500 → ~10 % and NCD=1000 → ~15 %. |
| **Logical Invariants** | `natural_capital_debt` floored at `0` (no negative surcharge). Returned rate floored at `base_rate`. |
| **Data Dependencies** | `base_rate` from `round_configs.py`; `natural_capital_debt` accumulated in game state. |
| **Edge Cases** | `NCD = 0` → rate equals `base_rate`; `NCD < 0` → clamp to `0`; extreme NCD (e.g., 10 000) → verify rate doesn't overflow. |

---

### 2.6 Burnout Accumulation Engine
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_burnout_accumulation`

| Section | Detail |
|---|---|
| **System Goal** | Track staff fatigue across 6-month rounds. Applies HR-driven delta plus a natural drift of `+6.0/round` when no HR investment is made. OPEX penalty activates at burnout > 20 (quadratic curve; max ~18 % penalty at 100). |
| **Logical Invariants** | `new_burnout` clamped to `[0, 100]`. `opex_penalty_rate` is always `>= 0`. `critical_burnout` flag is set when `new_burnout > 70`. |
| **Data Dependencies** | `staff_burnout_index` per BU from game state; `burnout_delta` from HR pillar decision; `natural_drift` defaults to `6.0` (set to `0` when HR was invested this round). |
| **Edge Cases** | Burnout at `100` with positive delta → stays at `100`; burnout at `0` with negative delta → stays at `0`; `natural_drift = 0` when HR is invested; `burnout = 20` → `opex_penalty_rate = 0` (boundary check). |

---

### 2.7 Workforce Readiness Engine
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_workforce_readiness`

| Section | Detail |
|---|---|
| **System Goal** | Track aggregate workforce competence across rounds. High HR investment: `+16`; medium: `+8`; no investment: `−10` (skills atrophy). Affects strategic pillar effectiveness and terminal valuation synergy bonus. |
| **Logical Invariants** | `new_readiness` clamped to `[0, 100]`. `low_readiness_penalty` flag when `< 40`. `high_readiness_bonus` flag when `> 75`. |
| **Data Dependencies** | `workforce_readiness` from game state (starts at `50`); `hr_quality_tier` from HR pillar decision (`"high"`, `"medium"`, `"none"`). |
| **Edge Cases** | Starting readiness `0` + `"none"` tier → stays at `0`; starting readiness `100` + `"high"` tier → stays at `100`; unknown tier string → treated as `"none"` (−10 delta). |

---

### 2.8 Revenue Cannibalization Engine
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_revenue_cannibalization`

| Section | Detail |
|---|---|
| **System Goal** | Model intra-group market overlap: BUs with revenue >15 % above group average cannibalize overlapping BUs proportional to the `_MARKET_OVERLAP` matrix. |
| **Logical Invariants** | A BU cannot cannibalize itself. Cannibalization amounts are always `>= 0`. Penalty is additive across multiple aggressors. |
| **Data Dependencies** | `bu_id`, `revenue_base` from `bu_states`; `_MARKET_OVERLAP` matrix in `engine.py`; `rate` defaults to `0.03`. |
| **Edge Cases** | Single-BU game → no pairs → return `{}`; all revenues equal → no aggressor; unknown BU pair → overlap defaults to `0.0`; `rate = 0` → no penalties. |

---

### 2.9 Stakeholder Fatigue Engine
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_stakeholder_fatigue`

| Section | Detail |
|---|---|
| **System Goal** | Diminish trust recovery efficiency after repeated crises. `efficiency = 1 / (1 + 0.3 × crisis_count)`. Ensures stakeholders become harder to appease the more crises occur. |
| **Logical Invariants** | `efficiency` is always `> 0` (asymptote, never reaches 0). Effective recovery is always `<= recovery_amount`. |
| **Data Dependencies** | `crisis_count_lifetime` accumulated in game state; `recovery_amount` from stakeholder recovery decision; `fatigue_factor = 0.3` (configurable). |
| **Edge Cases** | `crisis_count = 0` → full recovery; `recovery_amount = 0` → return `0`; large `crisis_count` (e.g., 100) → very small but non-zero effective recovery. |

---

### 2.10 ESG Greenwashing Risk Engine
**File**: [`backend/engine.py`](backend/engine.py) — functions `calc_greenwashing_risk`, `check_bu_greenwash_scandal`

| Section | Detail |
|---|---|
| **System Goal** | Detect hypocrisy when players select high-impact green options (A/C) without backing them with sufficient investment ratios (`>= 15 %`). Triggers reputation penalty (`−15`) and sets auditor tolerance to Hostile. |
| **Logical Invariants** | Scandal can only trigger on `option_a` or `option_c` (not neutral options). Penalty is fixed at `15.0` for group-level; `7.5` for moderate choices. |
| **Data Dependencies** | `choice` string from player decision; `investment_ratio` per BU or per decision; `green_investment_threshold = 0.15` from `engine.py`. |
| **Edge Cases** | Empty `decisions` list → `avg_ratio = 0` → scandal triggers if green option selected; `choice = "option_b"` → lenient 10 % threshold; all ratios `>= 0.15` → no scandal; `choice` not in any known set → return `(False, 0.0)`. |

---

### 2.11 Macro Interest Rate Environment
**File**: [`backend/engine.py`](backend/engine.py) — function `calc_macro_rate_environment`

| Section | Detail |
|---|---|
| **System Goal** | Model central bank policy cycles across the 10-round simulation: easing (R1–R2), neutral (R3–R5), tightening (R6–R8), and crisis premium (R9–R10). Returns a Cost-of-Capital modifier and descriptive regime label. |
| **Logical Invariants** | Rate modifier is a finite float for all valid `round_number` values. Unknown round falls back to `0.0` modifier. |
| **Data Dependencies** | `round_number` from game state; `_MACRO_RATE_CYCLES` dict in `engine.py`; `SIM_ROUNDS` from `config.py`. |
| **Edge Cases** | `round_number = 0` → not in dict → returns `0.0` modifier; `round_number > SIM_ROUNDS` → returns `0.0` modifier; negative round → same fallback. |

---

## 3. Module Registry

Quick-reference table of all shipped logic modules.

| # | Module Name | File | Primary Function(s) | Config Keys Used |
|---|---|---|---|---|
| 1 | Carbon Accounting Helpers | `engine.py` | `get_scope_ratios`, `calc_revenue_weighted_avg_ci`, `apply_ci_delta_to_bus` | `ECONOMIC_CARBON_PRICE_BASE`, `ECONOMIC_CARBON_PRICE_GROWTH` |
| 2 | Corporate Strategic Fund | `engine.py` | `calc_csf` | `SIM_INITIAL_BUDGET` |
| 3 | Contagion Engine | `engine.py` | `calc_contagion` | — |
| 4 | Synergy Engine | `engine.py` | `calc_synergy_opex` | — |
| 5 | Natural Capital Cost of Debt | `engine.py` | `calc_natural_capital_interest` | — |
| 6 | VRIO Decay | `engine.py` | `calc_vrio_decay` | — |
| 7 | Burnout Accumulation | `engine.py` | `calc_burnout_accumulation` | — |
| 8 | Workforce Readiness | `engine.py` | `calc_workforce_readiness` | — |
| 9 | Talent Brain-Drain | `engine.py` | `calc_talent_braindrain` | — |
| 10 | Strike Probability | `engine.py` | `calc_strike_probability` | — |
| 11 | Natural Decay | `engine.py` | `apply_natural_decay` | — |
| 12 | Macroeconomic Inflation | `engine.py` | `calc_inflation` | — |
| 13 | Execution Overrun Risk | `engine.py` | `calc_overrun_risk` | — |
| 14 | Technical Debt | `engine.py` | `calc_technical_debt` | — |
| 15 | Revenue Cannibalization | `engine.py` | `calc_revenue_cannibalization` | — |
| 16 | Stakeholder Fatigue | `engine.py` | `calc_stakeholder_fatigue` | — |
| 17 | Supply Chain Contagion | `engine.py` | `calc_supply_chain_contagion` | — |
| 18 | Competitor Pressure | `engine.py` | `calc_competitor_pressure` | — |
| 19 | Cash Conversion | `engine.py` | `calc_cash_conversion` | — |
| 20 | Dividend Ratchet | `engine.py` | `calc_dividend_ratchet` | — |
| 21 | Talent Allocation Pressure | `engine.py` | `calc_talent_allocation_pressure` | — |
| 22 | Technology Lock-In | `engine.py` | `calc_technology_lockin` | — |
| 23 | ESG Greenwashing Risk | `engine.py` | `calc_greenwashing_risk`, `check_bu_greenwash_scandal` | — |
| 24 | Macro Interest Rate | `engine.py` | `calc_macro_rate_environment` | `SIM_ROUNDS` |
| 25 | Biodiversity Engine | `biodiversity_engine.py` | _(see file)_ | — |
| 26 | Balance Sheet Engine | `balance_sheet.py` | _(see file)_ | `CONSTRAINT_MIN_LIQUIDITY_RATIO` |
| 27 | Systemic Risk Engine | `systemic_risk_engine.py` | _(see file)_ | `CONSTRAINT_MAX_CARBON_EMISSIONS` |
| 28 | Terminal Valuation | `terminal_valuation.py` | _(see file)_ | `ECONOMIC_CIRCULAR_ECONOMY_BONUS` |
| 29 | Regulatory Sandbox | `regulatory_sandbox.py` | _(see file)_ | — |
| 30 | Black Swan Registry | `black_swan_registry.py` | _(see file)_ | — |

---

## 4. Simulation Config Reference

All tuneable parameters live in [`simulation_config.json`](simulation_config.json) and are loaded into typed constants by [`backend/config.py`](backend/config.py).

| JSON Path | Config Constant | Default | Description |
|---|---|---|---|
| `simulation_settings.rounds` | `SIM_ROUNDS` | `10` | Total number of 6-month simulation rounds |
| `simulation_settings.agents` | `SIM_AGENTS` | `5` | Number of player/BU profiles |
| `simulation_settings.initial_budget` | `SIM_INITIAL_BUDGET` | `50 000 000` | Starting Corporate Strategic Fund (USD) |
| `economic_parameters.carbon_price_base` | `ECONOMIC_CARBON_PRICE_BASE` | `40.0` | Base carbon price (USD / tCO₂e) |
| `economic_parameters.carbon_price_growth_rate` | `ECONOMIC_CARBON_PRICE_GROWTH` | `0.15` | Annual carbon price escalation rate |
| `economic_parameters.circular_economy_efficiency_bonus` | `ECONOMIC_CIRCULAR_ECONOMY_BONUS` | `0.15` | OPEX bonus from circular economy decisions |
| `constraints.max_carbon_emissions` | `CONSTRAINT_MAX_CARBON_EMISSIONS` | `5 000.0` | Group-wide emissions cap (tCO₂e) |
| `constraints.min_liquidity_ratio` | `CONSTRAINT_MIN_LIQUIDITY_RATIO` | `0.2` | Minimum cash / assets ratio before penalty |

> **Rule**: Never hardcode any value from the table above directly in engine logic. Always import the constant from `config.py`.

---

## 5. Validation Checklist

Before merging any new logic module, verify:

- [ ] Blueprint entry completed in Section 2 above (all four fields filled)
- [ ] Module added to the registry table in Section 3
- [ ] New `simulation_config.json` keys documented in Section 4 (if any)
- [ ] Edge-case tests added to `backend/validation_logic.py`
- [ ] All invariants asserted in the test (clamping, sign correctness, empty-list guards)
- [ ] No magic numbers — all tuneable values sourced from `config.py`
- [ ] `blueprint.md` committed in the same PR as the implementation

---

*Last updated: 2026-05-28 | Maintained by the Muressons simulation engineering team.*
