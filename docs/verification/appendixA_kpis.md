# Appendix A — KPI and Formula Reference

Source repo: `muressons-sim`, git HEAD `0ad1246`.
All paths below are relative to the repo root. Backend paths are under `backend/`,
frontend paths under `frontend/`.

Every formula is quoted verbatim from source. Where a docstring disagrees with the
executable code, BOTH are reported and the discrepancy is listed in
"Discrepancies and duplicate definitions" at the end. Nothing here is inferred.

## Canonical state containers

The two authoritative KPI dicts are the Pydantic response models in `backend/models.py`:

- **Group / global state** — `class GlobalStateOut` (`backend/models.py:119`).
  Required fields: `corporate_treasury`, `group_reputation`, `synergy_multiplier`,
  `cost_of_capital`. Optional: `active_event_flags`, `historical_ebitda`,
  `tco2e_emissions`, `vrio_advantage`, `vrio_capabilities`, `green_transition_fund`,
  `tipping_point_active`, `pending_capex_projects`, `bonus_score`, `inflation_index`,
  `competitor_ebitda`, `political_capital`, `community_trust_score`,
  `global_emissions_intensity`, `cfo_austerity_active`, `regulatory_ratchet_baseline`,
  `balance_sheet`, plus cohort/pacing/quiz plumbing fields that are not KPIs.
- **Per-business-unit state** — `class BUStateOut` (`backend/models.py:192`).
  Fields: `bu_id`, `name`, `revenue_base`, `opex_base`, `natural_capital_debt`,
  `social_license_score`, `reputation_score`, `governance_risk_score`,
  `water_dependency`, `carbon_intensity`, `risk_factors`, `patient_outcomes_score`,
  `staff_burnout_index`, `bed_capacity_utilization`, `supplier_defection_active`,
  `green_premium_squeeze`.

The next-round global state is assembled by `_assemble_global_state`
(`backend/engine.py:4884`), which the docstring describes as "a pure data-assembly
step — no calculations here".

Frontend display labels and units come from the canonical catalog
`frontend/app/utils/kpiFormats.js:25-35` (`KPI` object), described in its own header
comment (line 2) as "single source of truth for KPI labels + formatting (audit #14)".

---

# 1. FINANCIAL

## 1.1 `corporate_treasury`

1. **Name in code:** `corporate_treasury` (global state); `ctx.new_treasury` inside the tick.
2. **Definition:** Group cash balance carried between rounds.
3. **Range / units:** Currency (dollars in all narrative strings). Floored, not clamped
   to zero — see the treasury floor below. Config floor default
   `FINANCIAL_TREASURY_FLOOR = -500_000_000` (`backend/config.py:224`).
4. **Formula (exact, as written):**
   - Base flow, `backend/engine.py:3155`:
     `ctx.new_treasury = round(base_treasury + csf - equity_capex - loan_repayment - total_interest + emergency_credit_drawn, 2)`
   - `csf` comes from `calc_csf` (`backend/engine.py:397`), called at `backend/engine.py:2978`
     as `csf = calc_csf(ctx.new_bus, clamped_dividends)`:
     ```
     gross_profit = sum(bu["revenue_base"] - bu["opex_base"] for bu in bu_states)
     return gross_profit - dividends_paid
     ```
     (`backend/engine.py:402-403`; docstring at 398-401 states
     `CSF = Σ(Revenue_Base - OPEX_Base) - Dividends_Paid`.)
   - Dynamic floor, `backend/engine.py:4416-4417`:
     `_final_floor = FINANCIAL_TREASURY_FLOOR + (_avg_inv_final * 200_000_000)`
     then `ctx.events["treasury_floor_effective"] = round(_final_floor, 2)`, applied at
     `backend/engine.py:4422`: `ctx.new_treasury = max(ctx.new_treasury, _final_floor)`.
     An earlier debt-service gate applies the same shape at `backend/engine.py:3579,3584`.
5. **What drives it:** every cash event in the tick. Confirmed writers:
   revenue/opex through `csf` (`backend/engine.py:2978`); negative-treasury debt service
   (`backend/engine.py:3572`); pending-project revenue generation (`backend/engine.py:3272`);
   CBAM surcharge (`backend/engine.py:3812`); carbon offset purchase (`backend/engine.py:3977`);
   round carbon fee (`backend/engine.py:4002`); loss-and-damage levy
   (`backend/engine.py:4075`, `4086`); UN SDG carbon retribution levy
   (`backend/engine.py:4134`); bailout (`backend/engine.py:4320`); regulatory ratchet fine
   (`backend/engine.py:4652`); covenant surcharge in the balance-sheet engine
   (`backend/balance_sheet.py:948`).
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:25`
   (`corporate_treasury: { label: 'Treasury', unit: '$', format: _money, goodDirection: +1 }`);
   also `frontend/app/components/AchievementBadges.js`, `AIAdvisor.js`, `AnnualReport.js`.
7. **Group:** financial.

## 1.2 `revenue_base` (per BU)

1. **Name in code:** `revenue_base` (`backend/models.py:195`).
2. **Definition:** A business unit's annualised revenue base, the driver of EBITDA,
   carbon tonnage and the treasury.
3. **Range / units:** Currency; floored at 0 (`backend/engine.py:4747`:
   `bu["revenue_base"] = max(0.0, bu.get("revenue_base", 0.0))`). Seed values are
   per-profile, e.g. 18_000_000 / 16_500_000 / 10_500_000 (`backend/bu_profiles.py:36,52,68`).
4. **Formula:** no single formula — a stock mutated by option impacts. Documented
   multiplicative writers:
   - Supplier defection, `backend/engine.py:4687`:
     `bu["revenue_base"] = round(bu["revenue_base"] * SUPPLIER_DEFECTION_REV_MULT, 2)`
   - Green premium squeeze, `backend/engine.py:4706-4708`:
     `penalty_pct = (60 - bu["social_license_score"]) * 0.005`;
     `penalty_val = round(bu["revenue_base"] * penalty_pct, 2)`;
     `bu["revenue_base"] -= penalty_val`
   - Boundary rounding, `backend/engine.py:4399`: `bu["revenue_base"] = round(bu["revenue_base"], 2)`
5. **What drives it:** the supply-chain pillar choice combined with investment ratio
   (`backend/engine.py:4682` — gate is `supply_chain_choice in ["audit_suppliers",
   "strict_mandates", "living_wage_mandate"] and inv_ratio < SUPPLIER_DEFECTION_INV_THRESHOLD`);
   the green-premium gate `inv_ratio > 0.25 and bu.get("social_license_score", 50) < 60`
   (`backend/engine.py:4705`); revenue cannibalisation (`backend/engine.py:939`).
6. **Displayed:** yes — `frontend/app/components/AnnualReport.js`,
   `frontend/app/components/EBITDAWaterfall.js`, `frontend/app/briefings/resolver.js`.
7. **Group:** financial.

## 1.3 `opex_base` (per BU)

1. **Name in code:** `opex_base` (`backend/models.py:196`).
2. **Definition:** A business unit's operating cost base.
3. **Range / units:** Currency; floored at 0 (`backend/engine.py:4748`). Synergy
   reductions floor at 35% of first-seen opex — `SYNERGY_OPEX_FLOOR_FRACTION = 0.35`
   (`backend/engine.py:570`), enforced by `synergy_opex_floor` (`backend/engine.py:573`).
4. **Formulas (each an exact quote):**
   - Synergy reduction, `calc_synergy_opex` (`backend/engine.py:584`), body at 603-607:
     ```
     ratio = max(0.0, min(1.0, investment_ratio))
     captured = max(0.0, min(1.0, math.sqrt(ratio) * SYNERGY_DAMPENING_FACTOR * max(0.0, synergy_multiplier)))
     factor = 1.0 - SYNERGY_MAX_REDUCTION_PER_ROUND * captured
     return max(0.0, round(old_opex * factor, 2))
     ```
     Docstring form (`backend/engine.py:594-595`):
     `captured = min(1, sqrt(ratio) × dampening × synergy_multiplier)`;
     `New_OPEX = Old_OPEX × (1 − SYNERGY_MAX_REDUCTION_PER_ROUND × captured)`.
     Constants: `SYNERGY_DAMPENING_FACTOR = 0.7` (`backend/config.py:335`),
     `SYNERGY_MAX_REDUCTION_PER_ROUND = 0.06` (`backend/config.py:344`).
   - Inflation, `calc_inflation` (`backend/engine.py:852`), body at 865:
     `return round(opex * (1.0 + inflation_index), 2)`
     (docstring `New_OPEX = OPEX * (1 + inflation_index)`, default 0.05, line 862).
   - Technical debt, `calc_technical_debt` (`backend/engine.py:895`), body at 910:
     `return round(opex * (1.0 + penalty_rate), 2), True` when
     `consecutive_zero_rounds >= penalty_threshold` (line 909).
   - Talent brain-drain, `calc_talent_braindrain` (`backend/engine.py:744`), body 761-768:
     ```
     penalty = 1.0 + max(0.0, (BRAINDRAIN_REPUTATION_THRESHOLD - group_reputation) / 100.0) * BRAINDRAIN_PENALTY_MULTIPLIER
     if burnout_index > BRAINDRAIN_BURNOUT_THRESHOLD:
         penalty += ((burnout_index - BRAINDRAIN_BURNOUT_THRESHOLD) / 100.0) * BRAINDRAIN_BURNOUT_OVERHEAD
     penalty = min(penalty, BRAINDRAIN_PENALTY_CAP)
     new_opex = round(opex_base * penalty, 2)
     ```
     Constants (`backend/config.py:373-381`): reputation threshold 65.0, penalty
     multiplier 1.5, burnout threshold 50.0, burnout overhead 2.0, penalty cap 1.30.
   - Burnout OPEX penalty, applied at `backend/round_logic.py:1956-1958`:
     `penalty_amount = round(bu["opex_base"] * penalty_rate, 2)`;
     `bu["opex_base"] = round(bu["opex_base"] + penalty_amount, 2)`,
     where `penalty_rate` is from `calc_burnout_accumulation` — see 3.3.
   - Employer-brand OPEX penalty, `backend/engine.py:3715-3719`:
     `eb_opex_multiplier = round(((EMPLOYER_BRAND_PENALTY_THRESHOLD - _eb) / EMPLOYER_BRAND_PENALTY_THRESHOLD) * EMPLOYER_BRAND_MAX_PENALTY_RATE, 4)`
     then `penalty = round(bu_opex * eb_opex_multiplier, 2)`;
     `bu["opex_base"] = round(bu_opex + penalty, 2)`.
   - Supplier defection, `backend/engine.py:4686`:
     `bu["opex_base"] = round(bu["opex_base"] * SUPPLIER_DEFECTION_OPEX_MULT, 2)`
5. **What drives it:** investment ratio + synergy multiplier (synergy);
   `inflation_index` (inflation); consecutive zero-investment rounds (technical debt);
   `group_reputation` and `staff_burnout_index` (brain drain); burnout above threshold;
   employer brand below `EMPLOYER_BRAND_PENALTY_THRESHOLD`; supply-chain mandate
   without funding.
6. **Displayed:** yes — `frontend/app/components/AnnualReport.js`,
   `EBITDAWaterfall.js`, `ebitdaWaterfallModel.js`.
7. **Group:** financial.

## 1.4 `historical_ebitda`

1. **Name in code:** `historical_ebitda` (`backend/models.py:125`; `ctx.historical_ebitda`
   `backend/engine.py:2501`).
2. **Definition:** Group EBITDA for the round — gross profit summed across BUs.
3. **Range / units:** Currency; unbounded (can go negative).
4. **Formula:** `backend/engine.py:3514-3516`:
   ```
   ctx.historical_ebitda = round(
       sum(bu["revenue_base"] - bu["opex_base"] for bu in ctx.new_bus), 2
   )
   ```
   A second, byte-different writer exists in `backend/router.py:3290-3292`:
   `new_global["historical_ebitda"] = round(sum((bu.get("revenue_base") or 0) - (bu.get("opex_base") or 0) for bu in new_bus), 2)`
   (same arithmetic, None-tolerant accessors).
5. **What drives it:** every `revenue_base` and `opex_base` writer (see 1.2, 1.3).
   Consumed by CAROIC (`backend/engine.py:3560`), competitor pressure
   (`backend/engine.py:4443`) and the balance sheet.
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:26`
   (`label: 'EBITDA', unit: '$'`); `frontend/app/components/AnnualReport.js`,
   `EBITDAWaterfall.js`.
7. **Group:** financial.

## 1.5 `cost_of_capital` / ESG-adjusted WACC

1. **Name in code:** `cost_of_capital` (global state, `backend/models.py:122`);
   `ctx.corporate_cost_of_capital` in the tick; `esg_wacc` / `adjusted_wacc` in the
   systemic-risk engine.
2. **Definition:** Group weighted average cost of capital, adjusted for ESG risk.
3. **Range / units:** Fraction (not percent). Clamped `[0.03, 0.20]` in code
   (`backend/systemic_risk_engine.py:39`). The docstring at line 29 says
   "Ranges: WACC 3%-15% (base 5%, ±10% ESG swing)" — see discrepancies.
4. **Formula:** `calc_esg_adjusted_wacc` (`backend/systemic_risk_engine.py:19`),
   body at 31-39:
   ```
   carbon_premium = max(0, (carbon_intensity_avg - 40) * 0.0008)
   gov_premium = max(0, (governance_risk_avg - 25) * 0.0006)
   slo_discount = max(0, (social_license_avg - 50) * 0.0003)
   nature_premium = max(0, biodiversity_dependency * (1 - supply_chain_transparency / 100) * 0.02)

   adjusted = base_wacc + carbon_premium + gov_premium - slo_discount + nature_premium
   adjusted = round(max(0.03, min(0.20, adjusted)), 4)
   ```
   Docstring form (line 28):
   `ESG-Adjusted WACC = Base + Carbon_Premium + Gov_Premium - SLO_Discount + Nature_Premium`.
5. **What drives it:**
   - Macro rate cycle, `backend/engine.py:3437-3439`:
     `corporate_cost_of_capital = round(corporate_cost_of_capital + macro_rate.get("coc_modifier", 0.0), 4)`.
     Cycle table `_MACRO_RATE_CYCLES` (`backend/engine.py:1252-1262`): R1-2 −0.010,
     R3-5 0.0, R6-8 +0.010, R9 +0.015, R10 +0.020.
   - ESG adjustment applied at `backend/engine.py:3698`: `ctx.corporate_cost_of_capital = esg_wacc`,
     gated on the `systemic_risk_enabled` toggle (`backend/engine.py:3694`).
   - Stranded-asset surcharge, `backend/engine.py:3749`:
     `ctx.corporate_cost_of_capital = round(ctx.corporate_cost_of_capital + STRANDED_ASSET_COC_SURCHARGE, 4)`
     (`STRANDED_ASSET_COC_SURCHARGE = 0.015`, `backend/config.py:578`), fired only when
     `ctx.decision_paradigm == "advanced_climate"` and some BU exceeds
     `STRANDED_ASSET_CI_THRESHOLD` (`backend/engine.py:3746-3747`).
   - SBTi surcharge, `backend/engine.py:3886`.
   - Historical maximum ratchet, `backend/engine.py:4363`:
     `ctx.corporate_cost_of_capital = historical_coc_max`.
   - Financial tipping point, `backend/round_logic.py:867`:
     `global_state["cost_of_capital"] = round(coc + pen["borrowing_premium_once"], 4)`
     (`borrowing_premium_once: 0.04`, `backend/systemic_risk_engine.py:181`).
   - Inputs to the ESG formula: revenue-weighted average carbon intensity
     (`avg_ci`), average `governance_risk_score`, average `social_license_score`,
     average `water_dependency` rescaled to a 0-1 fraction
     (`backend/engine.py:3690-3691`:
     `_avg_water = max(0.0, min(1.0, sum(bu.get("water_dependency", 0) for bu in ctx.new_bus) / n_bu / 100.0))`),
     and `supply_chain_transparency` (default 30, `backend/engine.py:3692`).
6. **Displayed:** yes — `frontend/app/components/AnnualReport.js`,
   `CohortComparison.js`, `CohortPulse.js`.
7. **Group:** financial (driven by environmental, social and governance inputs).

## 1.6 `synergy_multiplier` / VRIO decay

1. **Name in code:** `synergy_multiplier` (`backend/models.py:121`); `new_synergy` in the tick.
2. **Definition:** VRIO advantage multiplier; gates the M_R synergy premium and
   scales the synergy OPEX reduction.
3. **Range / units:** Dimensionless multiplier, 1.0 at start per the `calculate_mr`
   docstring (`backend/terminal_valuation.py:145`). No hard clamp found in `calc_vrio_decay`.
4. **Formula:** `calc_vrio_decay` (`backend/engine.py:627`), body at 634:
   `return round(advantage_current * (1.0 - imitation_decay_rate), 4)`
   (docstring: `Advantage_next = Advantage_current * (1 - Imitation_Decay_Rate)`, line 632).
   Effective decay rate, `backend/engine.py:3496-3497`:
   ```
   _effective_decay = ctx.imitation_decay_rate * max(0.2, 1.0 - _avg_invest_syn)
   new_synergy = calc_vrio_decay(ctx.pre_tick_synergy, _effective_decay)
   ```
   Project boost added after decay, `backend/engine.py:3500`:
   `new_synergy = round(new_synergy + _proj_delta.synergy_boost_total, 4)`.
5. **What drives it:** the pre-austerity average investment ratio
   (`_pre_austerity_avg_invest`, `backend/engine.py:3494`); completed CapEx projects
   (`synergy_boost_total`); R7 `option_c` "Resist & Integrate" sets the `synergy_unlock`
   flag per the `calculate_mr` docstring (`backend/terminal_valuation.py:145-146`).
6. **Displayed:** yes — `frontend/app/components/AnnualReport.js`, `DebriefReport.js`,
   `ExecutiveCockpit.js`.
7. **Group:** financial.

## 1.7 `vrio_capabilities`

1. **Name in code:** `vrio_capabilities` (`backend/models.py:127`; `ctx.vrio_capabilities`
   `backend/engine.py:2503`).
2. **Definition:** Four-axis VRIO scorecard derived from group averages.
3. **Range / units:** Each axis clamped 0-100, rounded to 1dp.
4. **Formula:** `backend/engine.py:4390-4395`:
   ```
   ctx.vrio_capabilities = {
       "value":         round(max(0, min(100, avg_sl)), 1),
       "rarity":        round(max(0, min(100, 100 - avg_ci_v)), 1),
       "imitability":   round(max(0, min(100, ctx.new_synergy * 100)), 1),
       "organization":  round(max(0, min(100, 100 - avg_gr)), 1),
   }
   ```
   Inputs at `backend/engine.py:4387-4389`:
   `avg_sl = sum(bu.get("social_license_score", 50) for bu in ctx.new_bus) / n`;
   `avg_gr = sum(bu.get("governance_risk_score", 20) for bu in ctx.new_bus) / n`;
   `avg_ci_v = _calc_rw_avg_ci(ctx.new_bus)`.
5. **What drives it:** social licence, governance risk, revenue-weighted carbon
   intensity, and the synergy multiplier.
6. **Displayed:** `vrio_advantage` appears in
   `frontend/app/components/SustainabilityBalancedScorecard.js`. The declared model
   field `vrio_advantage` (`backend/models.py:126`) is **not written** by
   `_assemble_global_state` (which writes only `vrio_capabilities`,
   `backend/engine.py:4909`) — see the special lists.
7. **Group:** governance / composite.

## 1.8 `inflation_index`

1. **Name in code:** `inflation_index` (`backend/models.py:178`, default `0.025`);
   `ctx.new_inflation_index`.
2. **Definition:** Per-round OPEX inflation rate.
3. **Range / units:** Fraction per round. `calc_inflation`'s docstring says
   "Default inflation_index = 0.05 (5% per 6-month period, ~10% annualized)"
   (`backend/engine.py:863`) while the model default is `0.025`
   (`backend/models.py:178`) — see discrepancies.
4. **Formula (drift):** `backend/engine.py:4187`:
   `ctx.new_inflation_index = round(ctx.new_inflation_index + 0.010, 4)`
   when `hostility_multiplier > 5` (`backend/engine.py:4186`, reading
   `market_hostility_index` default 5 at line 4185).
5. **What drives it:** the `market_hostility_index` event flag.
6. **Displayed:** yes — `frontend/app/components/consequenceCatalog.js`, `EngineEventsPanel.js`.
7. **Group:** financial.

## 1.9 `competitor_ebitda` and `relative_market_advantage`

1. **Names in code:** `competitor_ebitda` (`backend/models.py:179`),
   `relative_market_advantage` (event flag).
2. **Definition:** NPC competitor EBITDA and the player's EBITDA relative to it.
3. **Range / units:** Currency; ratio (4dp).
4. **Formula:** `calc_competitor_pressure` (`backend/engine.py:1024`), body 1036-1041:
   ```
   new_competitor = round(competitor_ebitda * (1.0 + competitor_growth_rate), 2)
   if new_competitor > 0:
       relative = round(player_ebitda / new_competitor, 4)
   else:
       relative = 1.0
   ```
   Call site `backend/engine.py:4443`.
5. **What drives it:** `COMPETITOR_GROWTH_RATE` and the player's `historical_ebitda`.
   A warning event fires when `relative_advantage < 1.0` (`backend/engine.py:4447`).
6. **Displayed:** yes — `competitor_ebitda` in
   `frontend/app/components/CompetitorIntelligence.js`; `relative_market_advantage` in
   `frontend/app/components/consequenceCatalog.js`, `FrontPageReveal.js`.
7. **Group:** financial.

## 1.10 `terminal_value` (Enterprise Value)

1. **Name in code:** `terminal_value` / `tv` (`backend/terminal_valuation.py:537`).
2. **Definition:** Exit enterprise value of the group at the end of play.
3. **Range / units:** Currency. EBITDA floored at `EBITDA_FLOOR = 0.0`
   (`backend/terminal_valuation.py:478`) before entering the formula.
4. **Formula:** `calculate_terminal_value` (`backend/terminal_valuation.py:481`),
   body at 513-537:
   ```
   gross = sum(bu["revenue_base"] - bu["opex_base"] for bu in bus)
   total_revenue = sum(bu["revenue_base"] for bu in bus)
   tco2e = round(sum(bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1e6 for bu in bus), 1)
   cc = round(tco2e * carbon_tax_per_ton, 2)
   raw_ebitda: float = round(gross - cc, 2)
   ebitda_floored: bool = raw_ebitda < EBITDA_FLOOR
   ebitda: float = max(EBITDA_FLOOR, raw_ebitda)
   mr = round(max(MR_FLOOR, min(MR_CEILING, mr)), 4)
   base = ebitda + (green_fund_balance if is_advanced_climate else 0)
   ...
   tv = round(base * effective_multiple * mr * m_sdg, 2)
   ```
   Docstring form (`backend/terminal_valuation.py:493-496`):
   ```
   Terminal_EBITDA = Σ(Rev − OPEX) − (Carbon_Tons × Carbon_Tax)
   TV (EV)         = (EBITDA + Green_Fund) × Exit_Multiple × M_R × M_SDG
   Equity_Value    = TV − Net_Debt
   Price/Share     = Equity_Value / SHARES_OUTSTANDING
   ```
5. **What drives it:** all BU revenue/opex; `carbon_intensity` (through `tco2e`);
   `carbon_tax_per_ton` (default `FINANCIAL_SHADOW_CARBON_PRICE = 250.0`,
   `backend/config.py:195`); `green_transition_fund` when
   `is_advanced_climate`; `M_R`; `M_SDG`; the exit multiple (fixed 12.0 default or
   dynamic Gordon-Growth when `use_dynamic_multiple=True`, `backend/terminal_valuation.py:533`).
6. **Displayed:** yes — `frontend/app/admin/trading-floor/page.js`,
   `frontend/app/components/consequenceCatalog.js`.
7. **Group:** composite (financial headline).

## 1.11 `exit_multiple` (Gordon Growth)

1. **Name in code:** `exit_multiple` (`backend/terminal_valuation.py:349`).
2. **Definition:** EV/EBITDA exit multiple derived from WACC and long-run growth.
3. **Range / units:** Multiple (×), clamped to
   `[TV_EXIT_MULTIPLE_FLOOR=6.0, TV_EXIT_MULTIPLE_CEILING=18.0]`
   (`backend/config.py:831-832`), rounded to 2dp.
4. **Formula:** `calculate_dynamic_exit_multiple` (`backend/terminal_valuation.py:319`),
   body 337-345:
   ```
   if wacc <= growth_rate:
       multiple = ceiling
       basis = "wacc_below_growth_rate_ceiling_applied"
   else:
       multiple = (1.0 + growth_rate) / (wacc - growth_rate)

   multiple = round(max(floor, min(ceiling, multiple)), 2)
   ```
   Docstring form (line 328): `Exit_Multiple = (1 + g) / (WACC − g)`.
   Defaults: `wacc = FINANCIAL_WACC_LENDER_THRESHOLD = 0.08` (`backend/config.py:227`),
   `growth_rate = TV_LONG_RUN_GROWTH = 0.02` (`backend/config.py:830`).
   `wacc_penalty_active` flag: `wacc > FINANCIAL_WACC_LENDER_THRESHOLD + 0.01` (line 354).
5. **What drives it:** `cost_of_capital` / ESG-adjusted WACC.
6. **Displayed:** yes — `frontend/app/admin/trading-floor/page.js`,
   `frontend/app/components/AnnualReport.js`.
7. **Group:** financial.

## 1.12 Equity bridge — `equity_value`, `price_per_share`, `net_debt`, `ev_over_revenue`, `price_to_book`, `share_price_change_pct`

1. **Names in code:** `equity_value`, `price_per_share`, `price_per_share_raw`,
   `equity_wiped_out`, `net_debt`, `ev_over_revenue`, `price_to_book`,
   `share_price_change_pct`, `share_price_vs_ipo`, `ev_revenue_signal`, `pb_signal`
   (`backend/terminal_valuation.py:443-471`).
2. **Definition:** Bridge from enterprise value to equity value and per-share price,
   plus market multiples.
3. **Range / units:** Currency; `price_per_share` floored at
   `SHARE_PRICE_FLOOR = 1.0` (`backend/terminal_valuation.py:43`).
   `shares_outstanding` default `TV_SHARES_OUTSTANDING = 6_500_000`
   (`backend/config.py:828`) — the code comments say 100M, see discrepancies.
   `IPO_PRICE_PER_SHARE = TV_IPO_PRICE = 50.0` (`backend/config.py:829`).
4. **Formula:** `calculate_equity_bridge` (`backend/terminal_valuation.py:377`),
   body 405-424:
   ```
   equity_value = round(enterprise_value - net_debt, 2)
   raw_price_per_share = round(equity_value / max(1, shares_outstanding), 4)
   price_per_share = max(SHARE_PRICE_FLOOR, raw_price_per_share)
   equity_wiped_out = equity_value < 0
   ipo_price = IPO_PRICE_PER_SHARE

   ev_over_revenue = round(enterprise_value / total_revenue, 2) if total_revenue > 0 else None
   price_to_book = round(equity_value / book_equity, 2) if book_equity > 0 else None

   ev_rev_benchmark = 2.5
   pb_benchmark = 1.5
   sp_change_pct = round((price_per_share - ipo_price) / ipo_price * 100, 1) if ipo_price > 0 else 0
   ```
   Docstring form (lines 388-395):
   `Equity_Value = Enterprise_Value − Net_Debt`;
   `Price_Per_Share = Equity_Value / Shares_Outstanding`;
   `EV/Revenue = Enterprise_Value / Total_Revenue`;
   `Price/Book = Equity_Value / Book_Equity (net assets)`.
   Signal bands, lines 428-432 and 436-440: premium when
   `ev_over_revenue > ev_rev_benchmark * 1.2`, fair when `>= ev_rev_benchmark * 0.8`,
   else discount; same 1.2 / 0.8 shape for price-to-book with `below_book` as the low tier.
5. **What drives it:** `terminal_value`; `net_debt` computed in
   `_equity_and_solvency` (`backend/round_logic.py:310`), body 326-338:
   ```
   total_financial_debt = (
       _ncl.get("revolving_credit_facility", 50_000_000)
       + _ncl.get("green_bonds_outstanding", 0.0)
       + max(_ncl.get("capex_term_loan", 0.0), _capex_loan)
       + _cl.get("short_term_debt", 0.0)
       + max(_cl.get("emergency_credit_line", 0.0), _ec_line)
   )
   treasury_cash = gs.get("corporate_treasury", 0.0)
   net_debt = round(total_financial_debt - treasury_cash, 2)
   ```
6. **Displayed:** `price_per_share` yes — `frontend/app/admin/trading-floor/page.js`,
   `frontend/app/components/consequenceCatalog.js`; `equity_value` yes —
   `frontend/app/components/consequenceCatalog.js`, `FrontPageReveal.js`;
   `ev_over_revenue` and `price_to_book` yes — `consequenceCatalog.js`;
   `stock_price` label in `frontend/app/utils/kpiFormats.js:27`.
   `share_price_change_pct` — **NOT FOUND** in `frontend/app`.
7. **Group:** financial.

## 1.13 `dmav` and `ncd_liability_usd`

1. **Names in code:** `dmav` (`backend/round_logic.py:355-356`),
   `ncd_liability_usd` and `total_ncd_points` (`backend/round_logic.py:349-351`).
2. **Definition:** DMAV is the solvency axis of the two-axis archetype matrix;
   `ncd_liability_usd` is the capitalised dollar price of accumulated natural-capital debt.
3. **Range / units:** Currency, rounded to 2dp.
4. **Formula:** `backend/round_logic.py:348-356`:
   ```
   _total_ncd_points = round(sum(max(0.0, float(b.get("natural_capital_debt", 0) or 0)) for b in bus), 2)
   _ncd_liability = round(_total_ncd_points * _NCD_PRICE * float(effective_exit_multiple), 2)
   ...
   _dmav = treasury_cash * mr - _ncd_liability
   extra["dmav"] = round(_dmav, 2)
   ```
   where `_NCD_PRICE` is `config.NCD_OPEX_PENALTY_PER_UNIT` (imported at
   `backend/round_logic.py:325`). Basis string at line 353:
   `"{points} NCD pts × ${price}/pt/round × {multiple}× exit multiple"`.
   Solvency gate, `backend/round_logic.py:370`:
   `"solvent": _dmav > 0 and equity_value >= 0`.
5. **What drives it:** `corporate_treasury`, `M_R`, total `natural_capital_debt`
   across BUs, and the effective exit multiple.
6. **Displayed:** `ncd_liability_usd` yes —
   `frontend/app/components/ArchetypeReveal.js`, `frontend/app/page.js`.
   `dmav` — **NOT FOUND** in `frontend/app`.
7. **Group:** composite.

## 1.14 `liquidity_ratio`

1. **Name in code:** `liquidity_ratio` (`backend/balance_sheet.py:922-923`).
2. **Definition:** Cash as a share of total assets.
3. **Range / units:** Fraction, 4dp. Minimum
   `CONSTRAINT_MIN_LIQUIDITY_RATIO = 0.2` (`backend/config.py:189`).
4. **Formula:** `backend/balance_sheet.py:922-923`:
   ```
   liquidity_ratio = round(cash / total_assets, 4) if total_assets > 0 else 0.0
   bs["liquidity_ratio"] = liquidity_ratio
   ```
5. **What drives it:** `cash_and_equivalents` (synced to `corporate_treasury`) and
   `total_assets`. Consequence at `backend/balance_sheet.py:924-926`: when below the
   minimum and covenant status is `green`, status is downgraded to `amber`.
6. **Displayed:** **NOT FOUND** in `frontend/app` (searched `liquidity_ratio`,
   `liquidityRatio`; `BalanceSheetModal.js` contains no `liquidity` match).
7. **Group:** financial.

## 1.15 Covenants — `covenant_status`, `net_debt_to_ebitda`, `debt_to_equity`

1. **Names in code:** `covenant_status`, `net_debt_to_ebitda`
   (`backend/balance_sheet.py:914-915`), `debt_to_equity`
   (`backend/balance_sheet.py:905-908`).
2. **Definition:** Lender covenant compliance state and the leverage ratios behind it.
3. **Range / units:** `covenant_status` ∈ {green, amber, red, breached};
   ratios are multiples (2dp); `debt_to_equity` is set to `99.0` when equity ≤ 0.
4. **Formulas:**
   - `debt_to_equity`, `backend/balance_sheet.py:905-908`:
     ```
     if total_equity > 0:
         bs["debt_to_equity"] = round(bs["total_liabilities"] / total_equity, 2)
     else:
         bs["debt_to_equity"] = 99.0
     ```
   - True EBITDA passed to the covenant check, `backend/balance_sheet.py:913`:
     `true_ebitda = round(gross_profit + total_depreciation, 2)`
   - `check_covenants` (`backend/balance_sheet.py:398`), body 421-452:
     ```
     total_debt = (
         bs["non_current_liabilities"]["revolving_credit_facility"]
         + bs["non_current_liabilities"]["green_bonds_outstanding"]
         + bs["non_current_liabilities"].get("capex_term_loan", 0.0)
         + bs["current_liabilities"]["short_term_debt"]
     )
     cash = bs["current_assets"]["cash_and_equivalents"]
     net_debt = total_debt - cash

     if ebitda <= 0:
         ratio = 99.0 if net_debt > 0 else 0.0
     else:
         ratio = round(net_debt / ebitda, 2)

     base_trigger = bs.get("covenant_trigger_ratio", 3.5)
     wacc_excess = max(0, esg_wacc - FINANCIAL_WACC_LENDER_THRESHOLD)
     wacc_tightening = round(wacc_excess * 25, 2)
     effective_trigger = round(max(2.0, base_trigger - wacc_tightening), 2)

     if ratio <= BS_COVENANT_GREEN_RATIO:
         status = "green"
     elif ratio <= effective_trigger:
         status = "amber"
     elif ratio <= effective_trigger + 1.0:
         status = "red"
     else:
         status = "breached"
     ```
     `BS_COVENANT_GREEN_RATIO = 2.5` (`backend/config.py:283`).
   - Treasury surcharge, `backend/balance_sheet.py:458-462`:
     ```
     if status == "red":
         surcharge = round(max(0, net_debt) * 0.02 / 2, 2)
     elif status == "breached":
         surcharge = round(max(0, net_debt) * 0.05 / 2, 2)
     ```
5. **What drives it:** total debt lines, `corporate_treasury` (as cash), true EBITDA,
   and the ESG-adjusted WACC (which tightens the trigger 0.25× per 1% of excess).
   Also downgraded by the liquidity ratio (see 1.14). Feeds the `financial` tipping
   dimension (`backend/systemic_risk_engine.py:155-159`).
6. **Displayed:** yes — `covenant_status` and `net_debt_to_ebitda` in
   `frontend/app/components/BalanceSheetModal.js` and `EngineEventsPanel.js`;
   `debt_to_equity` in `BalanceSheetModal.js` and `EngineWidgetsPanel.js`.
7. **Group:** financial / governance.

## 1.16 `brand_value`

1. **Name in code:** `brand_value` / `_brand_value_base` (`backend/balance_sheet.py:275`).
2. **Definition:** Intangible brand asset on the balance sheet.
3. **Range / units:** Currency; floored at `1_000_000` (`backend/balance_sheet.py:299`).
4. **Formula:** `calc_brand_value` (`backend/balance_sheet.py:275`), body 296-299:
   ```
   rep_factor = max(0.1, group_reputation / 50.0)
   slo_factor = max(0.1, math.sqrt(avg_slo / 50.0))
   new_brand = round(brand_base * rep_factor * slo_factor, 2)
   new_brand = max(1_000_000, new_brand)
   ```
   Docstring form (line 286): `Brand = Base × (Rep/50) × sqrt(SLO/50)`.
   Documented bounds (lines 288-292): Rep=100/SLO=100 → 2.83× base;
   Rep=50/SLO=50 → 1.00×; Rep=10/SLO=10 → 0.09×.
5. **What drives it:** `group_reputation` and average `social_license_score`.
   Computed against the stable opening base, never the prior period
   (docstring lines 281-284, `compounding_prevented: True` diagnostic at line 305).
6. **Displayed:** yes — `frontend/app/components/BalanceSheetModal.js`,
   `SustainabilityBalancedScorecard.js`.
7. **Group:** financial (driven by social).

---

# 2. ENVIRONMENTAL

## 2.1 `carbon_intensity` (per BU)

1. **Name in code:** `carbon_intensity` (`backend/models.py:202`, default 0).
2. **Definition:** Emissions intensity of a business unit.
3. **Range / units:** **tCO₂e per $1M revenue** — stated explicitly at
   `backend/bu_profiles.py:19-20`:
   `carbon_intensity : float  — tCO₂e per $1M revenue (I1: UNIT ANNOTATION)` /
   `Used in tonnage formula: tonnes = CI × revenue_base / 1_000_000`.
   Floored at 0, no upper clamp (`backend/engine.py:4752`:
   `bu["carbon_intensity"] = max(0.0, bu.get("carbon_intensity", 0.0))`).
   Seed values 35 / 72 / 48 (`backend/bu_profiles.py:38,54,70`).
4. **Formula:** a stock, changed by additive deltas. Writers:
   - `backend/round_logic.py:117`:
     `bu["carbon_intensity"] = max(0.0, round(bu.get("carbon_intensity", 0) + ci_delta, 2))`
   - `backend/round_logic.py:2313`:
     `bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) + ci_delta, 2))`
   - `backend/round_logic.py:2787` (halving):
     `bu["carbon_intensity"] = max(0, round(bu.get("carbon_intensity", 0) / 2, 2))`
   - `backend/round_logic.py:3527` (R5 hard-engineering pulse revert):
     `bu["carbon_intensity"] = max(0.0, round(bu.get("carbon_intensity", 0) + revert_delta, 2))`
   - Routed delta application, `apply_ci_delta_in_place` (`backend/engine.py:245`),
     body 266-268:
     ```
     for bu in bus:
         bu_id = bu.get("bu_id", "")
         if bu_id in result.new_carbon_intensities:
             bu["carbon_intensity"] = result.new_carbon_intensities[bu_id]
     ```
   - Clamps/rounding: `backend/engine.py:3649`, `3670`, `4405`, `4752`.
5. **What drives it:** decision option impacts carrying `ci_delta` (routed uniformly
   or by scope, `get_scope_ratios` `backend/engine.py:149`); the R5 hard-engineering
   pulse and its revert; circularity/decarbonisation options.
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:32`
   (`label: 'Carbon Intensity', unit: 'tCO₂e', goodDirection: -1`);
   `frontend/app/briefings/resolver.js`, `consequenceCatalog.js`, `ConsequencePreview.js`.
7. **Group:** environmental.

## 2.2 Revenue-weighted average carbon intensity (`avg_ci`)

1. **Name in code:** `calc_revenue_weighted_avg_ci`, aliased `_calc_rw_avg_ci`
   (`backend/engine.py:154`, alias at 176).
2. **Definition:** Group carbon intensity, weighted by revenue rather than a
   simple mean.
3. **Range / units:** tCO₂e per $1M revenue (docstring line 161:
   "Units: tCO₂e per $1M revenue (matches carbon_intensity field)").
4. **Formula:** `backend/engine.py:163-170`:
   ```
   total_rev = sum(bu.get("revenue_base", 0) for bu in bus)
   if total_rev <= 0:
       n = max(len(bus), 1)
       return sum(bu.get("carbon_intensity", 0) for bu in bus) / n
   return sum(
       bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) for bu in bus
   ) / total_rev
   ```
   Docstring form (line 160): `avg_CI = Σ(CI_i × Rev_i) / Σ(Rev_i)`.
5. **What drives it:** per-BU `carbon_intensity` and `revenue_base`.
   Consumed by the ESG-WACC carbon premium (`backend/engine.py:3681,3696`),
   VRIO rarity (`backend/engine.py:4389`), `global_emissions_intensity`
   (`backend/engine.py:4130,4182`) and the contagion risk index
   (`backend/engine.py:1901`).
6. **Displayed:** not as its own field name; surfaced via
   `global_emissions_intensity` (see 2.5).
7. **Group:** environmental.

## 2.3 `tco2e_emissions`

1. **Name in code:** `tco2e_emissions` (`backend/models.py:124`;
   `ctx.tco2e_emissions` `backend/engine.py:2502`).
2. **Definition:** Total absolute group emissions for the round.
3. **Range / units:** tCO₂e, rounded to 1dp.
4. **Formula:** `backend/engine.py:3517-3522`:
   ```
   ctx.tco2e_emissions = round(
       sum(
           bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1_000_000
           for bu in ctx.new_bus
       ), 1
   )
   ```
   Second writer, `backend/router.py:3293-3295`:
   `new_global["tco2e_emissions"] = round(sum((bu.get("carbon_intensity") or 0) * (bu.get("revenue_base") or 0) / 1_000_000 for bu in new_bus), 1)`
   Third, inside terminal valuation (`backend/terminal_valuation.py:515`):
   `tco2e = round(sum(bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1e6 for bu in bus), 1)`
5. **What drives it:** `carbon_intensity` and `revenue_base`.
   Consequence — emissions cap breach, `backend/engine.py:3530`:
   `if ctx.tco2e_emissions > CONSTRAINT_MAX_CARBON_EMISSIONS:` sets
   `emissions_limit_breached`, then deducts `EMISSIONS_BREACH_REP_PENALTY` (5.0,
   `backend/config.py:573`) from every BU's `reputation_score`
   (`backend/engine.py:3545`) and from `ctx.group_reputation`
   (`backend/engine.py:3546`).
   Also drives the carbon fee (`backend/engine.py:4001`), the retribution levy
   (`backend/engine.py:4133`) and the CAROIC carbon capital charge
   (`backend/engine.py:3562`).
6. **Displayed:** yes — `frontend/app/components/AchievementBadges.js`, `AIAdvisor.js`.
7. **Group:** environmental.

## 2.4 `absolute_emissions` (per BU)

1. **Name in code:** `absolute_emissions`.
2. **Definition:** Per-BU absolute emissions (the same tonnage formula at BU level).
3. **Range / units:** tCO₂e, 2dp.
4. **Formula:** `backend/engine.py:3525-3527`:
   ```
   bu["absolute_emissions"] = round(
       bu.get("carbon_intensity", 0) * bu.get("revenue_base", 0) / 1_000_000, 2
   )
   ```
   Duplicate writer, `backend/router.py:3297-3299` (identical arithmetic,
   None-tolerant accessors).
5. **What drives it:** `carbon_intensity` × `revenue_base`.
   Consumed by `backend/regional_reporting.py:238-243`.
6. **Displayed:** **NOT FOUND** in `frontend/app` (searched `absolute_emissions`,
   `absoluteEmissions`).
7. **Group:** environmental.

## 2.5 `global_emissions_intensity`

1. **Name in code:** `global_emissions_intensity` (`backend/models.py:183`).
2. **Definition:** Group-level revenue-weighted carbon intensity, published to the
   UN SDG Edition state.
3. **Range / units:** tCO₂e per $1M revenue, 2dp.
4. **Formula:** `backend/engine.py:4130-4131`:
   ```
   global_emissions = _calc_rw_avg_ci(ctx.new_bus)
   ctx.events["global_emissions_intensity"] = round(global_emissions, 2)
   ```
   Re-written at end of the SDG block, `backend/engine.py:4182`:
   `ctx.events["global_emissions_intensity"] = round(_calc_rw_avg_ci(ctx.new_bus), 2)`
5. **What drives it:** every `carbon_intensity` and `revenue_base` writer.
   Consequence, `backend/engine.py:4132-4134`:
   `if current_global["round_number"] <= 5 and global_emissions > 100:`
   `retribution_penalty = round(ctx.tco2e_emissions * 3.0 * 1000, 2)`;
   `ctx.new_treasury = round(ctx.new_treasury - retribution_penalty, 2)`.
   **Note:** `_assemble_global_state` writes the TOP-LEVEL key from the PREVIOUS
   state, not from this round's computation — `backend/engine.py:4922`:
   `"global_emissions_intensity": ctx.current_global.get("global_emissions_intensity", 0.0),`
   The freshly computed value reaches the client only through `active_event_flags`.
6. **Displayed:** yes — `frontend/app/components/consequenceCatalog.js`,
   `ExecutiveCockpit.js`.
7. **Group:** environmental.

## 2.6 `natural_capital_debt` (NCD, per BU)

1. **Name in code:** `natural_capital_debt` (`backend/models.py:197`, default 0).
2. **Definition:** Accumulated ecological debt stock for a BU; compounds at an
   interest rate that itself rises with the debt.
3. **Range / units:** Unit-less "points" in the engine — `backend/round_logic.py:353`
   prices them as `"{n} NCD pts × ${price}/pt/round"`. Clamped to
   `[0, NCD_HARD_CAP]` where `NCD_HARD_CAP = 5_000` (`backend/config.py:237`);
   warning at `NCD_WARN_THRESHOLD = 1_000` (`backend/config.py:241`).
   The frontend labels it as money — see discrepancies.
4. **Formulas:**
   - Interest rate, `calc_natural_capital_interest` (`backend/engine.py:611`),
     body 622-623:
     ```
     natural_capital_debt = max(0.0, natural_capital_debt)
     return round(base_rate + (natural_capital_debt * NCD_INTEREST_COEFFICIENT), 6)
     ```
     Docstring form (line 616): `Interest_Rate = Base_Rate + (Natural_Capital_Debt * 0.0001)`;
     calibration note (lines 618-619): "At NCD=100: rate ≈ 6.0%. At NCD=500: rate ≈ 10.0%.
     At NCD=1000: rate ≈ 15.0%." `NCD_INTEREST_COEFFICIENT = 0.0001` (`backend/config.py:348`).
   - Compounding, `backend/engine.py:3445-3451`:
     ```
     old_ncd    = bu.get("natural_capital_debt", 0)
     rate       = calc_natural_capital_interest(corporate_cost_of_capital, old_ncd)
     interest_rates[bu["bu_id"]] = rate
     debt_charge = round(old_ncd * rate, 2)
     new_ncd     = round(old_ncd + debt_charge, 2)
     bu["natural_capital_debt"] = min(new_ncd, NCD_HARD_CAP)
     ```
   - Investment-driven accumulation/reduction, `backend/engine.py:3470-3478`:
     ```
     if _bu_inv < 0.20:
         _ncd_accum = (0.20 - _bu_inv) * bu.get("carbon_intensity", 30) * 0.5
         bu["natural_capital_debt"] = min(
             bu["natural_capital_debt"] + _ncd_accum, NCD_HARD_CAP
         )
     elif _bu_inv >= 0.30:
         _ncd_reduction = (_bu_inv - 0.25) * 10
         bu["natural_capital_debt"] = max(0, bu["natural_capital_debt"] - _ncd_reduction)
     ```
   - Climate tipping-point mark-up: `ncd_stock_uplift_once: 0.50`
     (`backend/systemic_risk_engine.py:172`).
   - Forgiveness, `backend/engine.py:3793`:
     `bu["natural_capital_debt"] = max(0, round(old_ncd - forgiveness_per_bu, 2))`
5. **What drives it:** per-BU `investment_ratio`; `carbon_intensity` (the accumulation
   coefficient); `cost_of_capital` (the interest base); the climate tipping point.
   Consequences: credit-downgrade black swan at `NCD_WARN_THRESHOLD`
   (`backend/engine.py:3453-3465`); toxic OPEX penalty
   (`backend/engine.py:3823`: `ncd = max(0, bu.get("natural_capital_debt", 0))`);
   environmental provisions (see 2.7); `ncd_liability_usd` and DMAV (see 1.13);
   momentum score NCD term (see 5.5).
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:31`
   (`label: 'Natural Capital Debt', unit: '$', format: _money, goodDirection: -1`);
   `frontend/app/components/AnnualReport.js`, `ArchetypeReveal.js`, `ConsequencePreview.js`.
7. **Group:** environmental.

## 2.7 `environmental_provisions`

1. **Name in code:** `calc_environmental_provisions` (`backend/balance_sheet.py:364`).
2. **Definition:** IAS 37 environmental provision liability derived from NCD and
   active remediation obligations.
3. **Range / units:** Currency; floored at `min_provision`
   (`MIN_ENVIRONMENTAL_PROVISION`), 2dp.
4. **Formula:** `backend/balance_sheet.py:392-396`:
   ```
   ncd_provision   = ncd * BS_NCD_PROVISION_PER_UNIT
   event_provision = len(remediation_events) * BS_NCD_EVENT_PROVISION

   new_provision = ncd_provision + event_provision
   return round(max(min_provision, new_provision), 2)
   ```
   Docstring notes the old `max()` ratchet was removed so provisions can decrease
   (lines 366-372), citing IAS 37 §59.
5. **What drives it:** average NCD per BU and the count of active remediation events.
6. **Displayed:** yes — `frontend/app/components/BalanceSheetModal.js`,
   `SustainabilityBalancedScorecard.js`.
7. **Group:** environmental (balance-sheet liability).

## 2.8 `stranded_asset_exposure`

1. **Name in code:** `stranded_asset_exposure` (`backend/balance_sheet.py:311`).
2. **Definition:** Proportion of PPE at risk of climate-transition write-down.
   Docstring (line 320): "Based on Carbon Tracker Initiative methodology."
3. **Range / units:** Currency exposure; the underlying risk fraction is capped at 0.80.
4. **Formula:** `calc_stranded_assets` (`backend/balance_sheet.py:311`), body 322-348:
   ```
   ci_risk = min(0.5, carbon_intensity_avg / 200.0)

   pathway_modifiers = {
       "climate_black_swan": 0.20,
       "activist_ultimatum": 0.10,
       "regulatory_shutdown": 0.15,
       "hostile_takeover": 0.05,
       "stakeholder_revolt": 0.08,
   }
   pathway_risk = pathway_modifiers.get(ending_pathway, 0.10)

   tipping_modifiers = {
       "tipped": 0.15,
       "stressed": 0.10,
       "warning": 0.05,
       "none": 0.0,
   }
   tipping_risk = tipping_modifiers.get(tipping_tier, 0.0)

   total_risk = min(0.80, ci_risk + pathway_risk + tipping_risk)
   exposure = round(ppe * total_risk, 2)
   ```
   Risk-level bands (lines 353-357): critical > 0.40, high > 0.25, moderate > 0.10, else low.
5. **What drives it:** average carbon intensity, the ending pathway, and the
   systemic tipping tier. PPE comes from the balance sheet.
6. **Displayed:** yes — `frontend/app/components/BalanceSheetModal.js`,
   `consequenceCatalog.js`.
7. **Group:** environmental / financial.

## 2.9 `water_dependency` (per BU)

1. **Name in code:** `water_dependency` (`backend/models.py:201`, default 0).
2. **Definition:** A BU's dependence on water as a natural input.
3. **Range / units:** **0-100 scale** — stated at `backend/engine.py:2032`
   ("water_dependency is on a 0–100 scale (seed 12–82)") and
   `backend/engine.py:3684-3689` ("water_dependency is on a 0-100 scale but
   calc_esg_adjusted_wacc's biodiversity_dependency is a 0-1 fraction").
   Seed values 82 / 58 / 65 (`backend/bu_profiles.py:39,55,71`).
4. **Formula:** a stock changed additively — `backend/round_logic.py:2609-2612`:
   ```
   wd_delta = impacts.get("water_dependency_delta", 0)
   ...
       bu["water_dependency"] = max(0, round(bu.get("water_dependency", 0) + wd_delta, 2))
   ```
   Rescaled for WACC at `backend/engine.py:3690-3691`:
   `_avg_water = max(0.0, min(1.0, sum(bu.get("water_dependency", 0) for bu in ctx.new_bus) / n_bu / 100.0))`
5. **What drives it:** decision impacts carrying `water_dependency_delta`
   (the R8 blue-stress track, `backend/round_logic.py:2529` `_post_r8_blue_stress`).
   Consumed by the WACC nature premium and by SDG 6 and SDG 14 scoring
   (`backend/engine.py:2034,2042`).
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:33`
   (`label: 'Water Dependency', unit: '%', format: _pct, goodDirection: -1`);
   `frontend/app/briefings/data/standard.js`, `resolver.js`, `tokens.js`.
7. **Group:** environmental.

## 2.10 `green_transition_fund`

1. **Name in code:** `green_transition_fund` (`backend/models.py:131`);
   `ctx.new_green_fund_balance`.
2. **Definition:** Ring-fenced climate fund; added to EBITDA in terminal value under
   the advanced-climate paradigm.
3. **Range / units:** Currency, floored at 0 in the assembly
   (`backend/engine.py:4902`: `"green_transition_fund": max(0.0, ctx.new_green_fund_balance)`).
4. **Formula:** fed by the carbon fee, `backend/engine.py:4001-4002`:
   ```
   round_carbon_fee_total = round(ctx.tco2e_emissions * carbon_fee_per_ton, 2)
   ...
   ctx.new_treasury       = round(ctx.new_treasury - round_carbon_fee_total, 2)
   ```
   with the waterfall note at `backend/engine.py:4015`:
   `"${carbon_fee_per_ton}/tCO₂e × {tco2e}t = ${total} transferred to Green Fund."`
   Consumed in terminal value, `backend/terminal_valuation.py:529`:
   `base = ebitda + (green_fund_balance if is_advanced_climate else 0)`
5. **What drives it:** `tco2e_emissions` × the per-ton carbon fee (which escalates —
   `backend/engine.py:4010` narrates "Fee escalates {escalation_rate*100}% per ...").
6. **Displayed:** yes — `frontend/app/components/ExecutiveCockpit.js`, `InvestmentMatrix.js`.
7. **Group:** environmental / financial.

---

# 3. SOCIAL

## 3.1 `reputation_score` (per BU) and `group_reputation` (group)

1. **Names in code:** `reputation_score` (`backend/models.py:199`, default 50);
   `group_reputation` (`backend/models.py:120`; `ctx.group_reputation`).
2. **Definition:** Per-unit brand/reputation stock and the group-level reputation
   published each round.
3. **Range / units:** Score 0-100. BU clamp `backend/engine.py:4749`:
   `bu["reputation_score"] = max(0.0, min(100.0, bu.get("reputation_score", 50.0)))`.
   Group clamped to `[0.0, 100.0]` by `calc_contagion` (docstring line 443).
   Seed 55 (`backend/bu_profiles.py:45,61,77`); model default 50.
4. **Formula (group):** `calc_contagion` (`backend/engine.py:407`), called at
   `backend/engine.py:3385`: `ctx.group_reputation = calc_contagion(ctx.new_bus, ctx.crisis_severity)`.
   Docstring form (`backend/engine.py:419-421`):
   ```
   sigmoid_input = (crisis_severity − midpoint) / steepness
   sigmoid_value = 1 / (1 + e^(−sigmoid_input))
   group_rep     = avg_rep − max_drop × sigmoid_value
   ```
   Code, `backend/engine.py:455-470`:
   ```
   crisis_severity = max(0.0, crisis_severity)
   if not bu_states:
       return 50.0
   avg_rep: float = sum(bu["reputation_score"] for bu in bu_states) / len(bu_states)
   safe_steepness: float = steepness if steepness != 0.0 else 1.0
   sigmoid_input: float = (crisis_severity - midpoint) / safe_steepness
   ...
   sigmoid_value: float = 1.0 / (1.0 + math.exp(-sigmoid_input))
   ```
   Defaults: `CONTAGION_MAX_DROP = 50.0` (`backend/config.py:291`),
   `CONTAGION_MIDPOINT = 30.0` (`backend/config.py:294`),
   `CONTAGION_STEEPNESS = 15.0` (`backend/config.py:297`).
   Documented behaviour by severity tier (`backend/engine.py:423-426`):
   `< 15` drop ≤ 3.5 pts; `= 30` drop = 25 pts; `> 50` drop ≤ 44 pts.
   **Note** the docstring's tier table quotes a 25-point drop at the midpoint
   (i.e. `max_drop` of 50 × 0.5), consistent with the config default.
5. **Formula (BU stock reconciliation):** `reconcile_reputation_stock`
   (`backend/engine.py:526`), body 550-557:
   ```
   carry = round(persisted - reference, 4)
   if abs(carry) < 0.005:
       return 0.0
   for b in bus:
       cur = float(b.get("reputation_score", 50.0) or 0.0)
       b["reputation_score"] = round(max(0.0, min(100.0, cur + carry)), 2)
   return carry
   ```
   On the first tick `reference` is the mean of the BU stock
   (`backend/engine.py:543`: "seed BUs average 53.25 vs seed 50").
6. **Formula (natural decay):** `apply_natural_decay` (`backend/engine.py:790`),
   body 827-850:
   ```
   decay = NATURAL_DECAY_FACTOR  # ~0.96
   if capex_abs >= NATURAL_DECAY_GROWTH_ABS_CAPEX and investment_ratio < NATURAL_DECAY_GROWTH_RATIO:
       investment_ratio = NATURAL_DECAY_GROWTH_RATIO
   if investment_ratio >= NATURAL_DECAY_GROWTH_RATIO:
       slo_growth = 3.0 + (investment_ratio - NATURAL_DECAY_GROWTH_RATIO) * 10  # +3 to +10
       return (
           reputation,
           round(min(100.0, social_license + slo_growth), 2),
       )
   elif investment_ratio >= NATURAL_DECAY_MID_RATIO:
       return reputation, round(min(100.0, social_license + NATURAL_DECAY_MID_GROWTH), 2)
   elif investment_ratio >= NATURAL_DECAY_NO_DECAY_RATIO or invested:
       return reputation, social_license
   else:
       return (
           round(reputation * decay, 2),
           round(social_license * decay, 2),
       )
   ```
   Call site `backend/engine.py:3309`:
   `bu["reputation_score"], bu["social_license_score"] = apply_natural_decay(...)`.
   Constants: `NATURAL_DECAY_FACTOR = 0.96` (`backend/config.py:352`),
   `NATURAL_DECAY_NO_DECAY_RATIO = 0.15`, `NATURAL_DECAY_MID_RATIO = 0.20`,
   `NATURAL_DECAY_GROWTH_RATIO = 0.30` (`backend/config.py:641-643`),
   `NATURAL_DECAY_MID_GROWTH = 1.0` (`backend/config.py:601`),
   `NATURAL_DECAY_GROWTH_ABS_CAPEX = 3_000_000` (`backend/config.py:600`),
   `NATURAL_DECAY_MIN_ABS_CAPEX = 100_000` (`backend/config.py:668`).
7. **What drives it:** `crisis_severity` (group); per-BU investment ratio and
   absolute CapEx (decay tiers); the emissions cap breach penalty
   (`backend/engine.py:3545-3546`, −5.0 points); the climate tipping-point
   `reputation_ceiling: 60` (`backend/systemic_risk_engine.py:173`);
   greenwashing scandals. Consumes into: talent brain-drain OPEX
   (`backend/engine.py:761`), employer brand (`backend/engine.py:3711`),
   brand value (`backend/balance_sheet.py:296`), momentum
   (`backend/engine.py:1735`), contagion risk index (`backend/engine.py:1901`).
8. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:29`
   (`reputation_score: { label: 'Reputation', unit: 'score', goodDirection: +1 }`);
   `group_reputation` in `frontend/app/components/AchievementBadges.js`,
   `AIAdvisor.js`, `AnnualReport.js`; `reputation_score` in
   `frontend/app/components/TeamImpersonation.js`, `frontend/app/page.js`.
9. **Group:** social.

## 3.2 `social_license_score` (SLO, per BU)

1. **Name in code:** `social_license_score` (`backend/models.py:198`, default 50).
2. **Definition:** Community/stakeholder licence to operate for a BU.
3. **Range / units:** Score 0-100 (clamp `backend/engine.py:4750`).
   Seed 50 (`backend/bu_profiles.py:43,59,75`).
4. **Formula:** the decay/growth tiers of `apply_natural_decay`
   (`backend/engine.py:790`, quoted in full at 3.1 above) plus additive
   option deltas. Additional writers:
   - `backend/engine.py:4262` (greenwashing):
     `bu["social_license_score"] = max(0.0, round(bu["social_license_score"] - greenwash_penalty, 2))`
   - `backend/round_logic.py:860` (social tipping ceiling):
     `bu["social_license_score"] = float(pen["social_license_ceiling"])`
     (`social_license_ceiling: 50`, `backend/systemic_risk_engine.py:178`)
   - `backend/round_logic.py:2412`, `2633`:
     `bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + sl_delta, 2)))`
   - `backend/round_logic.py:1783`:
     `b["social_license_score"] = max(0, min(100, round(b["social_license_score"] + sl_boost, 2)))`
   - `backend/round_logic.py:2847`: `min(100, round(bu.get("social_license_score", 0) + 15, 2))`
   - `backend/round_logic.py:2860`: `max(0, round(bu.get("social_license_score", 0) + impacts["slo_all_penalty"], 2))`
5. **What drives it:** per-BU investment ratio and absolute CapEx (decay tiers);
   greenwashing scandal penalty (`calc_greenwashing_risk`, `backend/engine.py:1204`);
   the social tipping point; decision option `sl_delta` impacts;
   green-premium squeeze reads it (`backend/engine.py:4705`).
   Consumes into: strike probability, M_R instability discount, brand value,
   ESG-WACC SLO discount, VRIO "value" axis.
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:28`
   (`label: 'Social License', unit: 'score', goodDirection: +1`);
   `frontend/app/components/ESGLeadershipProfile.js`, `InvestmentMatrix.js`,
   `MasterVariableEditor.js`.
7. **Group:** social.

## 3.3 `staff_burnout_index` (per BU)

1. **Name in code:** `staff_burnout_index` (`backend/models.py:207`, `Optional[float] = None`).
2. **Definition:** Workforce burnout stock; lower is better.
3. **Range / units:** Score 0-100, clamped in the function
   (`backend/engine.py:665`) and again at `backend/engine.py:4753`.
4. **Formula:** `calc_burnout_accumulation` (`backend/engine.py:638`), body 664-686:
   ```
   new_burnout = current_burnout + burnout_delta + natural_drift
   new_burnout = round(max(0.0, min(100.0, new_burnout)), 2)
   ...
   if new_burnout > BURNOUT_OPEX_THRESHOLD:
       penalty_rate = round(((new_burnout - BURNOUT_OPEX_THRESHOLD) ** 2) * BURNOUT_OPEX_PENALTY_COEFF, 4)
       diagnostics["opex_penalty_rate"] = penalty_rate
   else:
       diagnostics["opex_penalty_rate"] = 0.0
   ```
   In-code comment on the curve (`backend/engine.py:680-681`):
   "Smooth quadratic curve: 0% at 20 -> 18% at 100".
   Constants: `BURNOUT_NATURAL_DRIFT = 6.0` (`backend/config.py:356`),
   `BURNOUT_OPEX_THRESHOLD = 20.0` (`backend/config.py:357`),
   `BURNOUT_CRITICAL_THRESHOLD = 70.0` (`backend/config.py:358`),
   `BURNOUT_OPEX_PENALTY_COEFF = 0.000028125` (`backend/config.py:359`).
   Docstring mechanics block (`backend/engine.py:657-661`) states different
   numbers — see discrepancies.
5. **What drives it:** the HR pillar choice's `burnout_delta` and the natural drift,
   applied per BU at `backend/round_logic.py:1947-1951`:
   ```
   new_burnout, diag = calc_burnout_accumulation(
       current, burnout_delta, natural_drift
   )
   bu["staff_burnout_index"] = new_burnout
   ```
   Consequences: OPEX penalty (`backend/round_logic.py:1956-1958`);
   governance-risk spike when critical, `backend/round_logic.py:1962-1966`:
   ```
   gov_spike = 3.0
   bu["governance_risk_score"] = min(
       100.0, round(bu.get("governance_risk_score", 20.0) + gov_spike, 2)
   )
   ```
   ; brain-drain OPEX overhead (`backend/engine.py:764`); the M_R
   Wellbeing bonus and the social tipping thresholds; employer brand.
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:34`
   (`label: 'Staff Burnout', unit: 'score', goodDirection: -1`);
   `frontend/app/components/ESGLeadershipProfile.js`, `ExecutiveCockpit.js`,
   `ReportsExport.js`.
7. **Group:** social.

## 3.4 `workforce_readiness`

1. **Name in code:** `workforce_readiness` (global; carried across the tick via
   `ENGINE_STATE_KEYS`, `backend/engine.py:4861`).
2. **Definition:** Group workforce competence stock.
3. **Range / units:** Score 0-100, starts at 50 (docstring `backend/engine.py:698`;
   default in `backend/round_logic.py:1972`: `gs.get("workforce_readiness", 50.0)`).
4. **Formula:** `calc_workforce_readiness` (`backend/engine.py:689`), body 715-729:
   ```
   if hr_quality_tier == "high":
       delta = READINESS_DELTA_HIGH
   elif hr_quality_tier == "medium":
       delta = READINESS_DELTA_MEDIUM
   elif hr_quality_tier == "no_lever":
       delta = 0.0
   else:
       delta = READINESS_DELTA_NONE

   new_readiness = round(max(0.0, min(100.0, current_readiness + delta)), 2)
   ```
   Constants: `READINESS_DELTA_HIGH = 16.0`, `READINESS_DELTA_MEDIUM = 8.0`,
   `READINESS_DELTA_NONE = -10.0`, `READINESS_LOW_THRESHOLD = 40.0`,
   `READINESS_HIGH_THRESHOLD = 75.0` (`backend/config.py:365-369`).
   Documented interdependencies (`backend/engine.py:711-713`):
   "readiness < 40: Strategic pillar effectiveness reduced by 20%";
   "readiness > 75: Synergy multiplier gets +0.05 bonus at terminal valuation".
5. **What drives it:** the HR quality tier and whether an HR lever exists
   (`backend/round_logic.py:1976-1980`):
   ```
   _hr_lever_available = (events.get("pillar_cost_applied") is not None) or bool(pillar_flags) or hr_choice is not None
   new_readiness, readiness_diag = calc_workforce_readiness(
       current_readiness, hr_invested, hr_quality if _hr_lever_available else "no_lever"
   )
   ```
   Consequence, `backend/round_logic.py:1986-1988`:
   `if new_readiness < 40.0: gs["pillar_effectiveness_modifier"] = 0.80  # 20% penalty`,
   else `1.0` (line 1995).
   Consumed by the M_R Workforce Excellence bonus (`backend/terminal_valuation.py:249-253`)
   and employer brand (`backend/engine.py:3711`).
6. **Displayed:** yes — `frontend/app/components/consequenceCatalog.js`, `ExecutiveCockpit.js`.
7. **Group:** social.

## 3.5 `employer_brand_score`

1. **Name in code:** `employer_brand_score` / `score`
   (`backend/systemic_risk_engine.py:98,120`).
2. **Definition:** Composite employer-attractiveness index; drives recruitment cost.
3. **Range / units:** 0-100, clamped and rounded to 1dp
   (`backend/systemic_risk_engine.py:112`).
4. **Formula:** `calc_employer_brand` (`backend/systemic_risk_engine.py:98`),
   body 107-118:
   ```
   score = (
       group_reputation * 0.4
       + (100 - avg_burnout) * 0.3
       + workforce_readiness * 0.3
   )
   score = round(max(0, min(100, score)), 1)

   recruitment_premium = 0.0
   if score < 40:
       recruitment_premium = round((40 - score) / 100 * 0.08, 4)
   ```
   Docstring form (line 104):
   `Employer Brand = Rep × 0.4 + (100 - Burnout) × 0.3 + Readiness × 0.3`.
   Talent-risk bands (lines 128-132): critical < 25, high < 40, moderate < 60, else healthy.
5. **What drives it:** `group_reputation`, average `staff_burnout_index`,
   `workforce_readiness`. Consequence, `backend/engine.py:3714-3723`:
   OPEX penalty on every BU when `_eb < EMPLOYER_BRAND_PENALTY_THRESHOLD` (40,
   `backend/config.py:705`), scaled by `EMPLOYER_BRAND_MAX_PENALTY_RATE` (0.08,
   `backend/config.py:706`).
6. **Displayed:** yes — `frontend/app/components/EngineEventsPanel.js`, `ExecutiveCockpit.js`.
7. **Group:** social (composite).

## 3.6 `strike_probabilities` / P_Strike

1. **Name in code:** `strike_probabilities` (event flag, `backend/engine.py:3511`);
   `calc_strike_probability` (`backend/engine.py:772`).
2. **Definition:** Per-BU probability of industrial action.
3. **Range / units:** Probability clamped to `[0.0, 1.0]`, 4dp.
   Warning bands `STRIKE_WARNING_THRESHOLD = 0.20`,
   `STRIKE_CRITICAL_THRESHOLD = 0.40` (`backend/config.py:780-781`).
4. **Formula:** `backend/engine.py:788-789`:
   ```
   p = base_risk + ((1.0 - (social_license / 100.0)) * STRIKE_SOCIAL_LICENSE_WEIGHT * coalition_multiplier)
   return max(0.0, min(1.0, round(p, 4)))
   ```
   Docstring form (line 777):
   `P_Strike = Base_Risk + ((1 - (Social_License / 100)) * 0.4 * coalition_multiplier)`.
   `STRIKE_SOCIAL_LICENSE_WEIGHT = 0.4` (`backend/config.py:401`).
   Call site, `backend/engine.py:3506-3510`:
   ```
   gov_risk  = bu.get("governance_risk_score", 0)
   base_risk = gov_risk / 100.0
   p         = calc_strike_probability(base_risk, bu["social_license_score"])
   strike_probs[bu["bu_id"]] = p
   ```
   Coalition variant in the forecast, `backend/engine.py:1946-1947`:
   `_coalition_mult = 1.0 + _coalition_pressure * COALITION_STRIKE_GAIN`
   (`COALITION_STRIKE_GAIN = 0.5`, defined twice — `backend/config.py:405` and `457`).
5. **What drives it:** `governance_risk_score` (the base risk),
   `social_license_score`, and NPC coalition pressure.
6. **Displayed:** yes — `frontend/app/components/consequenceCatalog.js`, `EngineEventsPanel.js`.
7. **Group:** social / governance.

## 3.7 `community_trust_score`

1. **Name in code:** `community_trust_score` (`backend/models.py:182`;
   `ctx.sdg_community_trust` `backend/engine.py:2507`, default 50.0).
2. **Definition:** UN SDG Edition community trust metric.
3. **Range / units:** Score, 2dp. Derived from 0-100 SDG cluster fields.
4. **Formula:** `backend/engine.py:4170-4171`:
   ```
   ctx.sdg_community_trust = round(avg_gov * 0.6 + avg_part * 0.4, 2)
   ctx.events["community_trust_score"]           = ctx.sdg_community_trust
   ```
   with inputs at `backend/engine.py:4159-4160`:
   `avg_gov  = sum(bu.get("governance", 0) for bu in ctx.new_bus) / max(len(ctx.new_bus), 1)`;
   `avg_part = sum(bu.get("partnerships", 0) for bu in ctx.new_bus) / max(len(ctx.new_bus), 1)`.
5. **What drives it:** the per-BU SDG cluster fields `governance` and `partnerships`
   (distinct from `governance_risk_score`). Only computed inside the UN SDG Edition block.
6. **Displayed:** yes — `frontend/app/components/consequenceCatalog.js`, `ExecutiveCockpit.js`.
7. **Group:** social.

## 3.8 `patient_outcomes_score` and `bed_capacity_utilization` (healthcare)

1. **Names in code:** `patient_outcomes_score` (`backend/models.py:206`,
   `Optional[float] = None`), `bed_capacity_utilization` (`backend/models.py:208`).
2. **Definition:** Healthcare-vertical BU quality and capacity metrics.
3. **Range / units:** NOT FOUND — no clamp or unit annotation located in
   `engine.py`, `round_logic.py` or `config.py`.
4. **Formula:** **NOT FOUND** — no assignment to `patient_outcomes_score` was found
   in `backend/engine.py`, `backend/round_logic.py`, `backend/config.py` or
   `backend/models.py` beyond the model declaration. The only related identifier
   found in the frontend is `patient_outcomes_billing_multiplier`
   (`frontend/app/components/consequenceCatalog.js:159`), which is a different key.
5. **What drives it:** NOT FOUND.
6. **Displayed:** `patient_outcomes_score` — **NOT FOUND** in `frontend/app`.
   `bed_capacity_utilization` — yes, `frontend/app/components/ExecutiveCockpit.js`.
7. **Group:** social.

---

# 4. GOVERNANCE

## 4.1 `governance_risk_score` (per BU)

1. **Name in code:** `governance_risk_score` (`backend/models.py:200`, default 0).
2. **Definition:** Governance/compliance risk stock for a BU. Higher is worse.
3. **Range / units:** Score 0-100 (clamp `backend/engine.py:3648`:
   `bu["governance_risk_score"] = max(0.0, min(100.0, bu.get("governance_risk_score", 20.0)))`;
   rounding `backend/engine.py:4404`). Model default 0, but every engine read
   defaults to 20 (e.g. `backend/engine.py:3682`, `4388`, `4389`).
   Seed values 15 / 20 / 10 (`backend/bu_profiles.py:44,60,76`).
4. **Formula:** a stock changed by additive deltas. Writers in `round_logic.py`:
   - `backend/round_logic.py:1657` — `bu["governance_risk_score"] = max(...)`
   - `backend/round_logic.py:1964-1966` (burnout critical spike, quoted at 3.3)
   - `backend/round_logic.py:2140` — `max(...)`
   - `backend/round_logic.py:2204` — `min(100, round(...))`
   - `backend/round_logic.py:2319` — `bu["governance_risk_score"] = min(100, bu["governance_risk_score"] + 10)`
   - `backend/round_logic.py:2419` — `max(0, min(100, round(bu["governance_risk_score"] + gov_delta, 2)))`
5. **What drives it:** decision option `gov_delta` impacts; critical burnout
   (+3.0 per BU, `backend/round_logic.py:1963`); the EU AI Act liability and
   AI-bias tracks (`_post_r6_ai_bias`, `backend/round_logic.py:2378`).
   Consequences: the ESG-WACC governance premium
   (`backend/systemic_risk_engine.py:32`); strike probability base risk
   (`backend/engine.py:3508`); VRIO "organization" axis
   (`backend/engine.py:4394`); the contagion risk index; SDG 11 and SDG 16
   (`backend/engine.py:2039,2044`); and the **regulatory ratchet fine**,
   `backend/engine.py:4649-4653`:
   ```
   regulatory_baseline = REG_RATCHET_BASELINE + (current_global["round_number"] // 2) * REG_RATCHET_ROUND_INCREMENT
   avg_gov_risk        = sum(bu.get("governance_risk_score", 0) for bu in ctx.new_bus) / max(len(ctx.new_bus), 1)
   if avg_gov_risk > regulatory_baseline:
       fine             = (avg_gov_risk - regulatory_baseline) * REG_RATCHET_FINE_PER_POINT
       ctx.new_treasury -= fine
   ```
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:30`
   (`label: 'Governance Risk', unit: 'score', goodDirection: -1`);
   `frontend/app/briefings/resolver.js`, `InvestmentMatrix.js`, `MasterVariableEditor.js`.
7. **Group:** governance.

## 4.2 `supply_chain_transparency`

1. **Name in code:** `supply_chain_transparency`
   (`backend/systemic_risk_engine.py:55`; event flag written at
   `backend/engine.py:3706`).
2. **Definition:** How much of the supply chain the group can see. Docstring
   (line 63): "Supply Chain Transparency Score (0-100). Starts at 30."
3. **Range / units:** Score clamped `[0, 100]`, 2dp
   (`backend/systemic_risk_engine.py:83`). Default/seed read is 30
   (`backend/engine.py:3692`).
4. **Formula:** `calc_supply_chain_transparency`
   (`backend/systemic_risk_engine.py:55`), body 68-83:
   ```
   delta = -3.0  # Natural entropy

   flag_boosts = {
       "deep_audit_completed": 20.0,
       "blockchain_traceability": 15.0,
       "materiality_aligned": 5.0,
       "supply_chain_disruption_risk": -10.0,
       "deny_and_deflect": -15.0,
       "remediation_active": 8.0,
       "circular_redesign": 5.0,
       "epr_program": 3.0,
   }

   applied_boosts = {}
   for flag, boost in flag_boosts.items():
       if flag in flags or flag in (flags.get("flags_set", []) if isinstance(flags.get("flags_set"), list) else []):
           delta += boost
           applied_boosts[flag] = boost

   new_score = round(max(0, min(100, current_score + delta)), 2)
   ```
   Docstring form (lines 64-66) says: "Improves via: deep audit (+20),
   blockchain (+15), materiality_aligned (+5). Degrades via: natural entropy
   (-3/round), scandal events (-25)". The `-25` scandal term is not in the
   `flag_boosts` table — see discrepancies.
5. **What drives it:** the eight named event flags above, plus the per-round
   −3.0 entropy. Consumed by the ESG-WACC nature premium
   (`backend/systemic_risk_engine.py:34`) and a black-swan probability modifier
   (`backend/black_swan_registry.py:277`:
   `{"metric": "supply_chain_transparency", "below": 40, "probability_add": 0.10}`).
6. **Displayed:** yes — `frontend/app/components/consequenceCatalog.js`,
   `TeamImpersonation.js`.
7. **Group:** governance.

## 4.3 `political_capital`

1. **Name in code:** `political_capital` (`backend/models.py:181`;
   `ctx.sdg_political_capital` `backend/engine.py:2506`, default 50.0).
2. **Definition:** UN SDG Edition political standing; gates the donor budget.
3. **Range / units:** Score, 2dp; derived from 0-100 SDG cluster fields.
4. **Formula:** `backend/engine.py:4161-4169`:
   ```
   ctx.sdg_political_capital = round((avg_gov + avg_part) / 2.0, 2)
   if ctx.sdg_political_capital < 30:
       budget_multiplier = 0.60
   elif ctx.sdg_political_capital < 50:
       budget_multiplier = 0.80
   else:
       budget_multiplier = round(1.0 + (ctx.sdg_political_capital - 50) / 200.0, 4)
   ctx.events["donor_fatigue_budget_multiplier"] = budget_multiplier
   ctx.events["political_capital_score"]         = ctx.sdg_political_capital
   ```
5. **What drives it:** the per-BU SDG cluster fields `governance` and
   `partnerships` (same inputs as `community_trust_score`, different weights).
6. **Displayed:** yes — `frontend/app/components/consequenceCatalog.js`, `ExecutiveCockpit.js`.
7. **Group:** governance.

## 4.4 `bonus_score`

1. **Name in code:** `bonus_score` (`backend/models.py:134`, `Optional[int] = 0`).
2. **Definition:** Accumulated learning/quiz/stakeholder-map bonus points.
3. **Range / units:** Integer points; no clamp found.
4. **Formula:** no engine formula — it is only ever incremented in the router.
   Writers:
   - `backend/router.py:4893`:
     `global_state["bonus_score"] = global_state.get("bonus_score", 0) + accuracy_bonus`
   - `backend/router.py:5200` (reversal):
     `gs["bonus_score"] = gs.get("bonus_score", 0) - float(_prev.get("points_awarded", 0) or 0)`
   - `backend/router.py:5205`:
     `gs["bonus_score"] = gs.get("bonus_score", 0) + result["points_awarded"]`
   - `backend/router.py:5384`: `gs["bonus_score"] = gs.get("bonus_score", 0) + points`
   - `backend/router.py:5431`: `gs["bonus_score"] = gs.get("bonus_score", 0) + incremental`
   - Initialised to 0 at `backend/router.py:6333`.
   The engine only carries it forward — `backend/engine.py:4910`:
   `"bonus_score": ctx.current_global.get("bonus_score", 0),`
5. **What drives it:** stakeholder-map accuracy, quiz results, and learning bonuses —
   all router-side, never the tick.
6. **Displayed:** yes — `frontend/app/components/GameOverSummary.js`,
   `LeaderboardMatrix.js`.
7. **Group:** governance (learning/meta).

---

# 5. COMPOSITE

## 5.1 `regenerative_multiple` (M_R)

1. **Name in code:** `mr` / `regenerative_multiple` / `mr_raw`
   (`backend/terminal_valuation.py:126`, return dict at 298-317).
2. **Definition:** ESG quality/risk modifier applied to terminal valuation.
   Docstring (line 128): "Regenerative Multiple (M_R) — ESG quality / risk
   modifier for terminal valuation."
3. **Range / units:** Dimensionless multiplier clamped to
   `[MR_FLOOR, MR_CEILING] = [0.0, 2.05]` (`backend/terminal_valuation.py:56-57`).
   Published reachable ceilings, `MR_PUBLISHED_CEILINGS`
   (`backend/terminal_valuation.py:63`):
   `{"base": 1.93, "jt_scaled": 2.02, "brsr": 1.98}`;
   `MR_CEILING_BY_PARADIGM` (line 64):
   `{"legacy_abc": 1.93, "advanced_climate": 1.93, "healthcare": 1.93,
     "multi_toggles": 2.02, "brsr_ngrbc": 1.98}`.
4. **Formula (full accumulation, exact):** `calculate_mr`
   (`backend/terminal_valuation.py:126`). Base at line 197: `mr = 1.0`. Terms:
   - `backend/terminal_valuation.py:199-200`: `if flags.get("materiality_aligned"): mr += 0.10`
   - `backend/terminal_valuation.py:201-206`: `elif flags.get("materiality_partial"): mr += 0.05`
   - Synergy premium, `backend/terminal_valuation.py:214-224`:
     ```
     synergy_flag_present: bool = bool(flags.get("synergy_unlock"))
     synergy_threshold_met: bool = synergy_multiplier >= 0.80
     synergy_frac: float = _ramp_fraction(synergy_multiplier, 0.80, _MR_RAMP_BAND_SYNERGY, "above") if synergy_flag_present else 0.0
     synergy_bonus_applied: bool = synergy_flag_present and synergy_frac > 0.0
     if synergy_bonus_applied:
         b = round(0.15 * synergy_frac, 4)
         mr += b
     ```
   - Resilience, `backend/terminal_valuation.py:233-235`:
     `if not flags.get("insurance_only") and not flags.get("electronics_water_priority") and not flags.get("civil_water_priority"): mr += 0.20`
   - Truth premium, line 236-238: `if flags.get("ethical_ai_overhaul"): mr += 0.15`
   - JT scaling, lines 239-241:
     `jt_scaling = 1.0`;
     `if hr_investment_rounds > 0 and (flags.get("community_fund") or flags.get("managed_transition")): jt_scaling = round(min(1.5, 1.0 + hr_investment_rounds * 0.10), 2)`
   - Community champion, lines 242-244: `b = round(0.18 * jt_scaling, 4); mr += b`
   - Just transition (elif), lines 245-247: `b = round(0.12 * jt_scaling, 4); mr += b`
   - Workforce excellence, lines 249-253:
     `_wf_frac = _ramp_fraction(workforce_readiness, 75.0, _MR_RAMP_BAND_KPI, "above")`;
     `b = round(0.10 * _wf_frac, 4); mr += b`
   - Wellbeing, lines 255-258:
     `_wb_frac = _ramp_fraction(avg_burnout, 20.0, _MR_RAMP_BAND_KPI, "below")`;
     `b = round(0.05 * _wb_frac, 4); mr += b`
   - Planet-expendable penalty, lines 259-261: `mr -= 0.20`
   - BRSR ESG alpha dividend, lines 263-266: `mr += brsr_div`
   - Instability discount, lines 268-271:
     `_slo_frac = _ramp_fraction(avg_slo, 75.0, _MR_RAMP_BAND_KPI, "below")`;
     `b = round(-0.40 * _slo_frac, 4); mr += b`
   - Pathway bonuses, lines 272-278: `mr += v` for each numeric value.
   - Clamp, lines 282-283:
     `raw_mr: float = round(mr, 4)`;
     `mr = round(max(MR_FLOOR, min(MR_CEILING, mr)), 4)`
   Ramp helper `_ramp_fraction` (`backend/terminal_valuation.py:92`), body 106-121:
   ```
   half = band / 2.0
   if band <= 0:
       if direction == "above":
           return 1.0 if value >= threshold else 0.0
       return 1.0 if value < threshold else 0.0
   if direction == "above":
       if value >= threshold + half:
           return 1.0
       if value <= threshold - half:
           return 0.0
       return (value - (threshold - half)) / band
   else:  # "below"
       if value <= threshold - half:
           return 1.0
       if value >= threshold + half:
           return 0.0
       return ((threshold + half) - value) / band
   ```
   Band widths (`backend/terminal_valuation.py:89-90`):
   `_MR_RAMP_BAND_KPI = 10.0` (±5 points around 0-100 KPI thresholds);
   `_MR_RAMP_BAND_SYNERGY = 0.10` (±0.05 around the 0.80 synergy gate).
   Documented arithmetic of the ceiling (`backend/terminal_valuation.py:293-294`):
   `1.0+0.10+0.15+0.20+0.15+0.18+0.10+0.05 = 1.93` without JT scaling;
   2.02 with it (community champion 0.18 × 1.5 = 0.27); 1.98 with the BRSR dividend.
   `max_achievable_mr_for` (`backend/terminal_valuation.py:70`), body 74-77:
   ```
   if hr_investment_rounds and hr_investment_rounds > 0:
       return MR_PUBLISHED_CEILINGS["jt_scaled"]
   if flags and flags.get("brsr_net_positive_dividend"):
       return MR_PUBLISHED_CEILINGS["brsr"]
   return MR_PUBLISHED_CEILINGS["base"]
   ```
   A second, defensive clamp exists in `calculate_terminal_value`
   (`backend/terminal_valuation.py:526-528`).
5. **What drives it:** the event flags `materiality_aligned`, `materiality_partial`,
   `synergy_unlock`, `insurance_only`, `electronics_water_priority`,
   `civil_water_priority`, `ethical_ai_overhaul`, `community_fund`,
   `managed_transition`, `planet_expendable`, `brsr_net_positive_dividend`;
   the KPIs `synergy_multiplier`, `workforce_readiness`, `avg_burnout`, `avg_slo`;
   `hr_investment_rounds` (counted from `hr_invested_r{N}` flags written at
   `backend/round_logic.py:1941-1942`); and `pathway_bonuses` from the ending pathway.
6. **Displayed:** yes — `frontend/app/utils/kpiFormats.js:35`
   (`regenerative_multiple: { label: 'Regenerative Multiple', unit: '×', goodDirection: +1 }`);
   `frontend/app/components/ArchetypeReveal.js`, `consequenceCatalog.js`.
7. **Group:** composite.

## 5.2 `sdg_multiplier` (M_SDG)

1. **Name in code:** `m_sdg` / `sdg_multiplier` (`backend/terminal_valuation.py:359`).
2. **Definition:** Terminal-value multiplier earned from the Corporate SDG Side Track.
3. **Range / units:** Dimensionless. Docstring (lines 364-366):
   "SDG Impact Score ... Range: -11 (all Option C) to 105 (all Option A).
   M_SDG range: 0.97 to 1.26. Sessions without the SDG Side Track default to
   score=0 → M_SDG=1.0 (neutral)." No clamp is applied in code.
4. **Formula:** `calculate_sdg_multiplier` (`backend/terminal_valuation.py:359`),
   body 368-373:
   ```
   m_sdg = round(1.0 + (sdg_impact_score / 100.0) * 0.25, 4)
   return {
       "m_sdg": m_sdg,
       "sdg_impact_score": sdg_impact_score,
       "sdg_track_active": sdg_impact_score != 0.0,
   }
   ```
   Docstring form (line 361): `M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25`.
5. **What drives it:** `sdg_impact_score`, accumulated by the Corporate SDG Side
   Track. Multiplies terminal value at `backend/terminal_valuation.py:537`.
6. **Displayed:** `m_sdg` yes — `frontend/app/components/FacilitatorTeleprompter.js`,
   `GameOverSummary.js`, `GodModeStatus.js`. The literal key `sdg_multiplier` —
   **NOT FOUND** in `frontend/app`. `sdg_impact_score` is displayed
   (`frontend/app/components/GameOverSummary.js:578,701`, `SDGAlignmentRadar.js:88`,
   `ShadowBoardAudit.js:30`).
7. **Group:** composite.

## 5.3 `caroic` (Carbon-Adjusted Return on Invested Capital)

1. **Name in code:** `caroic`, `caroic_pct`, `nopat`, `carbon_capital_charge`,
   `adjusted_capital`, `grade` (`backend/engine.py:2173`, return dict 2259-2270).
2. **Definition:** ROIC with a shadow carbon charge added to the capital base.
3. **Range / units:** `caroic` is a ratio (6dp); `caroic_pct` is a percentage (2dp).
   Grade bands from config: A+ ≥ 25, A ≥ 15, B ≥ 10, C ≥ 5, D ≥ 0, else F
   (`backend/config.py:758-761`, applied `backend/engine.py:2240-2255`).
4. **Formula:** `calc_caroic` (`backend/engine.py:2173`), body 2214-2236:
   ```
   tax_rate = max(0.0, min(1.0, tax_rate))
   nopat = ebitda * (1.0 - tax_rate)
   carbon_tonnage = max(0.0, carbon_tonnage)
   shadow_carbon_price = max(0.0, shadow_carbon_price)
   carbon_capital_charge = carbon_tonnage * shadow_carbon_price
   invested_capital_floored = max(0.0, invested_capital)
   adjusted_capital = invested_capital_floored + carbon_capital_charge

   if adjusted_capital <= 0:
       caroic = 0.0
   else:
       caroic = nopat / adjusted_capital

   caroic = round(caroic, 6)
   caroic_pct = round(caroic * 100, 2)
   ```
   Docstring form (`backend/engine.py:2181`):
   `CAROIC = EBITDA × (1 − Tax Rate) / (Invested Capital + (Carbon Tonnage × Shadow Carbon Price))`.
   Defaults: `tax_rate = FINANCIAL_CORPORATE_TAX_RATE = 0.25` (`backend/config.py:198`);
   `shadow_carbon_price = FINANCIAL_SHADOW_CARBON_PRICE = 250.0` (`backend/config.py:195`).
5. **What drives it:** call site `backend/engine.py:3554-3567`:
   ```
   _shadow_carbon_price = current_global.get("active_event_flags", {}).get(
       "carbon_tax_per_ton",
       current_global.get("active_event_flags", {}).get("shadow_carbon_price", FINANCIAL_SHADOW_CARBON_PRICE),
   )
   _ic_proxy    = max(0.0, sum(bu.get("revenue_base", 0) for bu in ctx.new_bus) * 0.5)
   caroic_result = calc_caroic(
       ebitda=ctx.historical_ebitda,
       invested_capital=_ic_proxy,
       carbon_tonnage=ctx.tco2e_emissions,
       tax_rate=FINANCIAL_CORPORATE_TAX_RATE,
       shadow_carbon_price=_shadow_carbon_price,
   )
   caroic_result["invested_capital_method"] = "revenue_proxy_0.5x"
   ctx.events["caroic"] = caroic_result
   ```
   So invested capital is **0.5 × total revenue**, not the treasury the
   docstring names — see discrepancies.
6. **Displayed:** yes — `caroic` in `frontend/app/components/KPIDashboard.js`,
   `consequenceCatalog.js`; `caroic_pct` in `KPIDashboard.js`,
   `SessionHealthDashboard.js`; `nopat` in `KPIDashboard.js`, `TechnicalGlossary.js`.
   Also exposed to the admin surface at `backend/admin_router.py:11439,11911-11912`.
7. **Group:** composite (financial × environmental).

## 5.4 `sdg_index` and `sdg_grade` (17-goal SDG Impact Report)

1. **Names in code:** `sdg_index`, `sdg_grade`, `sdg_scores`, `bonus_sdgs`,
   `total_sdgs_on_track` / `_at_risk` / `_off_track`
   (`backend/engine.py:2058`, return dict 2155-2172).
2. **Definition:** Maps BU variables onto all 17 UN SDGs, scoring each and
   aggregating. Docstring (line 2061): "Returns a score (0-100) per SDG and an
   aggregate SDG Index."
3. **Range / units:** Per-SDG raw score clamped `[0, 100]`; weighted score is
   `raw × weight`, capped at 100.0 after bonuses; `sdg_index` is 1dp.
   Status bands (line 2152): on_track ≥ 60.0, at_risk ≥ 30.0, else off_track.
4. **Formula:** `calc_sdg_impact` (`backend/engine.py:2058`).
   - Per-SDG base, `backend/engine.py:2091-2106`:
     ```
     avg_val: float = sum(bu.get(metric_key, 0) for bu in bus) / n

     if invert:
         if threshold == 0:
             raw_score: float = 100.0 if avg_val == 0 else max(0.0, 100.0 - avg_val)
         else:
             raw_score = max(0.0, min(100.0, (1.0 - avg_val / (threshold * 2)) * 100.0))
     else:
         if threshold == 0:
             raw_score = 100.0
         else:
             raw_score = max(0.0, min(100.0, (avg_val / threshold) * 100.0))

     base_weighted[sdg_num] = round(raw_score * weight, 1)
     ```
   - Flag bonuses, `backend/engine.py:2122-2124`:
     ```
     pre_bonus = base_weighted[sdg_num]
     base_weighted[sdg_num] = round(min(100.0, pre_bonus + bonus_pts), 1)
     ```
   - Aggregate, `backend/engine.py:2133-2135`:
     ```
     total_weight: float = sum(cfg["weight"] for cfg in _SDG_MAPPING.values())
     aggregate: float = round(
         sum(base_weighted.values()) / max(total_weight, 1.0), 1
     )
     ```
   - Grade, `backend/engine.py:2158-2164`:
     A+ ≥ `SDG_GRADE_A_PLUS` (80), A ≥ 70, B ≥ 55, C ≥ 40, D ≥ 25, else F
     (`backend/config.py:753-757`).
   Example mapping rows (`backend/engine.py:2034,2039,2040,2042,2043,2044`):
   ```
   6:  {"label": "Clean Water",             "metric": "water_dependency",     "weight": 1.0, "threshold": 40, "invert": True},
   11: {"label": "Sustainable Cities",       "metric": "governance_risk_score","weight": 0.5, "threshold": 25, "invert": True},
   12: {"label": "Responsible Consumption",  "metric": "natural_capital_debt", "weight": 0.8, "threshold": 3000, "invert": True},
   14: {"label": "Life Below Water",         "metric": "water_dependency",     "weight": 0.6, "threshold": 30, "invert": True},
   15: {"label": "Life on Land",            "metric": "natural_capital_debt", "weight": 0.7, "threshold": 2000, "invert": True},
   16: {"label": "Peace & Justice",         "metric": "governance_risk_score","weight": 0.8, "threshold": 20, "invert": True},
   ```
5. **What drives it:** every BU metric named in `_SDG_MAPPING`, plus the
   `_SDG_FLAG_BONUSES` table. Called once per tick at `backend/engine.py:4457`:
   `sdg_report = calc_sdg_impact(ctx.new_bus, ctx.events)` →
   `ctx.events["sdg_impact"] = sdg_report`.
6. **Displayed:** `sdg_index` — **NOT FOUND** in `frontend/app` (searched
   `sdg_index`, `sdgIndex`). `sdg_grade` yes —
   `frontend/app/components/GameOverSummary.js`. The `sdg_impact` container key is
   read by `frontend/app/components/SDGAlignmentRadar.js`, `GameOverSummary.js`,
   `ShadowBoardAudit.js`.
7. **Group:** composite.

## 5.5 `momentum_score`

1. **Name in code:** `momentum_score`, `trend`, `consecutive_high`, `comeback_kid`,
   `comeback_kid_mr_bonus` (`backend/engine.py:1712`, return dict 1776-1789).
2. **Definition:** Rate of improvement over a 3-round rolling window.
   Docstring (line 1718): "Rewards teams that are improving regardless of
   absolute position."
3. **Range / units:** 0-100, 1dp. Returns `50.0` with
   `trend: "insufficient_data"` when fewer than 2 history entries
   (`backend/engine.py:1723-1725`).
4. **Formula:** `backend/engine.py:1730-1751`:
   ```
   delta_velocity = (curr_treasury - prev_treasury) - (prev_treasury - prev2_treasury)
   ...
   delta_rep = curr_rep - prev_rep
   ...
   delta_ncd = prev_ncd - curr_ncd  # Positive = NCD is reducing (good)

   norm_velocity = max(-50, min(50, delta_velocity / max(abs(curr_treasury), 1) * MOMENTUM_TREASURY_NORM))
   norm_rep = max(-50, min(50, delta_rep * MOMENTUM_REP_MULTIPLIER))
   norm_ncd = max(-50, min(50, delta_ncd * MOMENTUM_NCD_MULTIPLIER))

   raw = 50 + (MOMENTUM_WEIGHT_TREASURY * norm_velocity + MOMENTUM_WEIGHT_REP * norm_rep + MOMENTUM_WEIGHT_NCD * norm_ncd)
   score = round(max(0, min(100, raw)), 1)
   ```
   Docstring form (line 1720):
   `Momentum = 0.4 × Δ(treasury_velocity) + 0.3 × Δ(reputation) + 0.3 × Δ(NCD_reduction)`.
   Constants (`backend/config.py:769-777`):
   `MOMENTUM_WEIGHT_TREASURY = 0.4`, `MOMENTUM_WEIGHT_REP = 0.3`,
   `MOMENTUM_WEIGHT_NCD = 0.3`, `MOMENTUM_HIGH_THRESHOLD = 70`,
   `MOMENTUM_COMEBACK_MR_BONUS = 0.05`, `MOMENTUM_TREASURY_NORM = 500`,
   `MOMENTUM_REP_MULTIPLIER = 5`, `MOMENTUM_NCD_MULTIPLIER = 10`.
   Comeback Kid gate, `backend/engine.py:1762-1766`:
   ```
   if score > MOMENTUM_HIGH_THRESHOLD:
       consecutive += 1

   comeback_kid = consecutive >= 2
   ```
   Trend bands, lines 1768-1775: accelerating ≥ 70, stable ≥ 50,
   decelerating ≥ 30, else declining.
5. **What drives it:** `corporate_treasury` (second difference),
   `group_reputation` (first difference) and the `ncd_transparency`
   event-flag NCD totals; call site `backend/engine.py:4468-4479`.
6. **Displayed:** `momentum` / `momentum_score` yes —
   `frontend/app/components/consequenceCatalog.js`, `PolicyWarRoom.js`;
   also `backend/admin_teleprompter.py:1708`.
   `comeback_kid` — **NOT FOUND** as that key in `frontend/app`
   (`comeback` appears in `ArchetypeReveal.js`, `TurnaroundConsole.js`,
   `TurnaroundPhaseChip.js`, which are turnaround components, not this flag).
7. **Group:** composite.

## 5.6 `contagion_risk_index`

1. **Name in code:** `contagion_risk_index` (`backend/engine.py:1902`,
   published at 2003).
2. **Definition:** Composite leading indicator of systemic fragility.
   In-code comment (line 1899): "Contagion Risk Index (composite leading indicator)";
   (line 1901): "Higher = more dangerous. Scale 0-100."
3. **Range / units:** 0-100, 1dp.
4. **Formula:** `backend/engine.py:1902-1907`:
   ```
   contagion_risk_index = round(min(100, max(0,
       (avg_gov_risk * CRI_WEIGHT_GOV_RISK) +
       ((100 - avg_slo) * CRI_WEIGHT_SLO_DEFICIT) +
       ((100 - avg_rep) * CRI_WEIGHT_REP_DEFICIT) +
       (avg_ci * CRI_WEIGHT_CARBON)
   )), 1)
   ```
   Weights (`backend/config.py:762-765`):
   `CRI_WEIGHT_GOV_RISK = 0.3`, `CRI_WEIGHT_SLO_DEFICIT = 0.3`,
   `CRI_WEIGHT_REP_DEFICIT = 0.2`, `CRI_WEIGHT_CARBON = 0.2`.
   Tier labels, `backend/engine.py:2005-2008`: 🟢 Low < `CRI_TIER_LOW` (25),
   🟡 Moderate < `CRI_TIER_MODERATE` (50), 🟠 High < `CRI_TIER_HIGH` (75)
   (`backend/config.py:766-768`). Warning threshold
   `CONTAGION_RISK_WARNING = 60` (`backend/config.py:782`).
   Inputs, `backend/engine.py:1894-1900`:
   `avg_rep`, `avg_slo`, `avg_gov_risk` are simple means;
   `avg_ci = _calc_rw_avg_ci(current_bus)` is revenue-weighted.
5. **What drives it:** governance risk, social licence, reputation and
   revenue-weighted carbon intensity. Consumed by the board-room reflection
   prompt (`backend/engine.py:4487`:
   `contagion_risk = forecast.get("contagion_risk_index", 0)`).
6. **Displayed:** **NOT FOUND** in `frontend/app` (searched
   `contagion_risk_index`, `contagion_risk`, `contagionRisk`).
7. **Group:** composite.

## 5.7 Systemic tipping points — `tipping_point_active`, `tipping_tier`, `systemic_tipping_state`

1. **Names in code:** `tipping_point_active` (`backend/models.py:132`),
   `tipping_tier`, `systemic_tipping_state`
   (`backend/engine.py:4904-4905`, `4938`).
2. **Definition:** Irreversibility gates across three dimensions —
   climate, social, financial.
3. **Range / units:** Tier ∈ {none, warning, stressed, tipped}.
4. **Thresholds:** `TIPPING_THRESHOLDS` (`backend/systemic_risk_engine.py:138-161`):
   ```
   "climate": {
       "warning":  {"carbon_intensity_avg": 65, "ehi_below": 45},
       "stressed": {"carbon_intensity_avg": 75, "ehi_below": 30},
       "tipped":   {"carbon_intensity_avg": 85, "ehi_below": 15},
   },
   "social": {
       "warning":  {"avg_slo_below": 35, "avg_burnout": 60},
       "stressed": {"avg_slo_below": 25, "avg_burnout": 75},
       "tipped":   {"avg_slo_below": 15, "avg_burnout": 90},
   },
   "financial": {
       "warning":  {"covenant_status": "amber"},
       "stressed": {"covenant_status": "red"},
       "tipped":   {"covenant_status": "breached"},
   },
   ```
5. **Penalties:** `IRREVERSIBILITY_PENALTIES`
   (`backend/systemic_risk_engine.py:170-186`):
   ```
   "climate_tipped": {
       "ncd_stock_uplift_once": 0.50,
       "reputation_ceiling": 60,
       ...
   },
   "social_tipped": {
       "opex_surcharge_once": 0.05,
       "social_license_ceiling": 50,
       ...
   },
   "financial_tipped": {
       "borrowing_premium_once": 0.04,
       "capex_cap_multiplier": 0.50,
       "dividend_suspended": True,
       ...
   },
   ```
   Applied by `apply_tipping_penalties` (`backend/round_logic.py:824`);
   cost-of-capital write at `backend/round_logic.py:867`;
   SLO ceiling write at `backend/round_logic.py:860`.
   In-code note (`backend/systemic_risk_engine.py:164-169`) records that two
   previously documented penalties — `strike_probability_floor` and
   `carbon_tax_multiplier` — "had no reader at all — they are gone from the table".
6. **What drives it:** revenue-weighted carbon intensity and the ecosystem health
   index (climate); average SLO and average burnout (social); `covenant_status`
   (financial).
7. **Displayed:** `tipping_point_active` is a declared model field
   (`backend/models.py:132`); the systemic tipping tier feeds
   `calc_stranded_assets` (`backend/balance_sheet.py:340-348`).
   Frontend display of the literal keys was not verified beyond
   `stranded_asset_exposure`.
8. **Group:** composite.

## 5.8 `greenwashing risk` (scandal gate)

1. **Name in code:** `calc_greenwashing_risk` (`backend/engine.py:1204`);
   `greenwash_backing` (`backend/engine.py:1183`);
   `resolve_green_claim` (`backend/engine.py:1157`).
2. **Definition:** Fires an SLO-destroying scandal when a green claim is not
   backed by spend.
3. **Range / units:** Returns `(scandal_triggered: bool, social_license_penalty: float)`.
4. **Formula:** `backend/engine.py:1231-1245`:
   ```
   if claim_level not in ("full", "moderate"):
       return False, 0.0
   pool_share, total_capex = greenwash_backing(decisions)
   if total_capex >= GREENWASH_ABS_CAPEX_FLOOR:
       return False, 0.0
   if claim_level == "full":
       if pool_share < green_investment_threshold:
           return True, penalty
   else:
       moderate_threshold = green_investment_threshold * GREENWASH_MODERATE_THRESHOLD_SCALE
       if pool_share < moderate_threshold:
           return True, round(penalty * GREENWASH_MODERATE_PENALTY_SCALE, 2)
   return False, 0.0
   ```
   Documented tiers (`backend/engine.py:1227-1229`):
   `"full" → 15% of the pool, full penalty (SDG-ORCH: 15.0)`;
   `"moderate" → ≈10% of the pool, half penalty`.
5. **What drives it:** the chosen option's configured `claim_level`, the team's
   share of the CSF pool and total CapEx. Applies the penalty to
   `social_license_score` at `backend/engine.py:4262`.
6. **Displayed:** not verified as a named KPI field; surfaced through
   `social_license_score` and event narratives.
7. **Group:** composite (governance × social).

---

# 6. COMPUTED BUT NEVER DISPLAYED

Each entry was computed in the backend and then searched for by its exact field
name across `frontend/app` (`*.js`, `*.jsx`), including camelCase variants.
"NOT FOUND" here means no match in `frontend/app`.

| KPI | Computed at | Consumed by (backend) | Search performed |
|---|---|---|---|
| `sdg_index` | `backend/engine.py:2133-2135` (aggregate), published `backend/engine.py:2157` | Nothing found — no backend reader outside its own return dict | `sdg_index`, `sdgIndex` → NOT FOUND |
| `contagion_risk_index` | `backend/engine.py:1902-1907` | `backend/engine.py:4487` (board-room reflection prompt) | `contagion_risk_index`, `contagion_risk`, `contagionRisk` → NOT FOUND |
| `liquidity_ratio` | `backend/balance_sheet.py:922-923`; snapshotted into `balance_sheet_history` at `backend/balance_sheet.py:1007` | `backend/balance_sheet.py:924-926` — downgrades a green covenant to amber | `liquidity_ratio`, `liquidityRatio`, `liquidity` in `BalanceSheetModal.js` → NOT FOUND |
| `absolute_emissions` (per BU) | `backend/engine.py:3525-3527`; duplicated at `backend/router.py:3297-3299` | `backend/regional_reporting.py:238-243` | `absolute_emissions`, `absoluteEmissions` → NOT FOUND |
| `dmav` | `backend/round_logic.py:355-356` | `backend/round_logic.py:370` (`solvent` gate); `solvency_gated_profile` `backend/round_logic.py:47` | `dmav` → NOT FOUND |
| `share_price_change_pct` | `backend/terminal_valuation.py:424`, returned at 452 | Nothing found | `share_price_change_pct` → NOT FOUND |
| `comeback_kid` / `comeback_kid_mr_bonus` | `backend/engine.py:1765`, returned 1785-1786 | Nothing found reading the flag back | `comeback_kid` → NOT FOUND (`comeback` matches only turnaround components) |
| `patient_outcomes_score` | **NOT FOUND** — declared only at `backend/models.py:206`; no writer located | Nothing found | `patient_outcomes_score`, `patientOutcomes` → NOT FOUND |
| `sdg_multiplier` (as that key) | `backend/terminal_valuation.py:369`, exported as `"sdg_multiplier"` at `backend/terminal_valuation.py:572` | `backend/terminal_valuation.py:537` (terminal value) | `sdg_multiplier` → NOT FOUND (the same number IS displayed under the key `m_sdg`) |

Notes on two near-misses that are **not** in this list:
- `vrio_advantage` is declared at `backend/models.py:126` and IS referenced in
  `frontend/app/components/SustainabilityBalancedScorecard.js` — but
  `_assemble_global_state` never writes it (it writes only `vrio_capabilities`,
  `backend/engine.py:4909`). This is the inverse defect: a **displayed field with
  no producer** in the tick assembly.
- `global_emissions_intensity` IS displayed, but the top-level state key carries the
  PREVIOUS round's value (`backend/engine.py:4922` reads
  `ctx.current_global.get(...)`), while the current round's value only reaches the
  client via `active_event_flags` (`backend/engine.py:4131`, `4182`).

---

# 7. DISPLAYED BUT NEVER CONSUMED BY ANOTHER CALCULATION

"Never consumed" = no backend reader was found that uses the value as an input to a
further calculation (as opposed to merely serialising it for the response).

| KPI | Displayed at | Producer | Evidence of no downstream consumer |
|---|---|---|---|
| `bonus_score` | `frontend/app/components/GameOverSummary.js`, `LeaderboardMatrix.js` | Router only — `backend/router.py:4893, 5205, 5384, 5431` | The engine only carries it forward verbatim (`backend/engine.py:4910`). No formula in `engine.py`, `round_logic.py`, `terminal_valuation.py` reads it. |
| `vrio_capabilities` (value / rarity / imitability / organization) | `frontend/app/components/SustainabilityBalancedScorecard.js` (via `vrio_advantage`) | `backend/engine.py:4390-4395` | Written into the assembled state (`backend/engine.py:4909`) and nothing else. The four axes are derived FROM other KPIs; no engine reader was found. |
| `relative_market_advantage` | `frontend/app/components/consequenceCatalog.js`, `FrontPageReveal.js` | `backend/engine.py:4443-4445` | Only reader found is the warning-string branch at `backend/engine.py:4446-4450`. The `calc_competitor_pressure` docstring (`backend/engine.py:1035`) says it "is used as a terminal multiplier modifier", but no such use was located in `terminal_valuation.py`. |
| `community_trust_score` | `frontend/app/components/consequenceCatalog.js`, `ExecutiveCockpit.js` | `backend/engine.py:4170-4171` | Written to state (`backend/engine.py:4921`) and to events. No formula reads it back. (Contrast `political_capital`, which DOES drive `donor_fatigue_budget_multiplier` at `backend/engine.py:4162-4168`.) |
| `momentum_score` | `frontend/app/components/consequenceCatalog.js`, `PolicyWarRoom.js`; `backend/admin_teleprompter.py:1708` | `backend/engine.py:1751` | Appended to `momentum_history` (`backend/engine.py:4478`) which feeds only the `consecutive_high` counter in the next call. `comeback_kid_mr_bonus` is returned but no reader applies it to M_R. |
| `bed_capacity_utilization` | `frontend/app/components/ExecutiveCockpit.js` | **NOT FOUND** — declared only at `backend/models.py:208` | No writer and no reader located in `engine.py`, `round_logic.py` or `config.py`. |
| `caroic` / `caroic_pct` | `frontend/app/components/KPIDashboard.js`, `SessionHealthDashboard.js`, `consequenceCatalog.js`; admin at `backend/admin_router.py:11911-11912` | `backend/engine.py:3559-3567` | Stored in `ctx.events["caroic"]`; no engine formula reads it back. It is a pure readout. |

---

# 8. NOT FOUND / UNCERTAIN

## 8.1 Looked for and could not pin down

- **`patient_outcomes_score` formula.** Declared `backend/models.py:206`. No
  assignment found in `backend/engine.py`, `backend/round_logic.py`,
  `backend/config.py` or `backend/bu_profiles.py`. **NOT FOUND.**
- **`bed_capacity_utilization` formula.** Declared `backend/models.py:208`.
  No assignment found in the searched files. **NOT FOUND.**
- **`vrio_advantage` producer.** Declared `backend/models.py:126`; read by
  `frontend/app/components/SustainabilityBalancedScorecard.js`; never written by
  `_assemble_global_state`. **NOT FOUND.**
- **`regulatory_ratchet_baseline` as a persisted KPI.** Declared
  `backend/models.py:186` (default 10.0), but the value used each round is
  recomputed locally at `backend/engine.py:4649` from `REG_RATCHET_BASELINE`
  and the round number; no writer of the model field was located.
- **`REG_RATCHET_BASELINE` / `REG_RATCHET_ROUND_INCREMENT` /
  `REG_RATCHET_FINE_PER_POINT` numeric defaults.** Referenced at
  `backend/engine.py:4649,4652` but their `config.py` definitions were not read;
  values **NOT VERIFIED**.
- **`NCD_OPEX_PENALTY_PER_UNIT` in the DMAV basis.** Value is
  `1_000` (`backend/config.py:246`), but the basis string describes it as
  "$/pt/round" (`backend/round_logic.py:353`) while it is applied once, multiplied
  by the exit multiple. The per-round semantics are asserted only in the string.
- **`ehi_below` (ecosystem health index)** appears in `TIPPING_THRESHOLDS`
  (`backend/systemic_risk_engine.py:140-142`) but the producing formula for `ehi`
  was not located in the files read. **NOT FOUND** in this pass.
- **`crisis_severity` formula.** `calc_contagion` consumes it
  (`backend/engine.py:408`) and `base_crisis_severity_for_round` exists at
  `backend/round_logic.py:127`, but its body was not read. **NOT VERIFIED.**
- **Frontend display of `tipping_point_active` / `tipping_tier`.** Not searched
  individually. **NOT VERIFIED.**

## 8.2 Same quantity, two different definitions or values

1. **`liquidity_ratio` — two incompatible formulas under one name and one
   threshold constant.**
   - `backend/balance_sheet.py:922`: `cash / total_assets`
   - `backend/tests/test_simulation_integrity.py:134` (`_derive_liquidity_ratio`,
     defined at line 130): `liquidity_ratio = EBITDA / Total_Revenue`, where
     `EBITDA = Σ(revenue - opex)` and `Revenue = Σ(revenue_base)`.
   Both are compared against `CONSTRAINT_MIN_LIQUIDITY_RATIO` (0.2,
   `backend/config.py:189`) — the balance sheet at line 924, the test at line 210.

2. **`SHARES_OUTSTANDING` — comments say 100M, config says 6.5M.**
   - `backend/terminal_valuation.py:33`: `SHARES_OUTSTANDING: int = TV_SHARES_OUTSTANDING   # 100 million shares (IPO anchor)`
   - `backend/terminal_valuation.py:10` (module docstring):
     "Per-share price: Equity Value / SHARES_OUTSTANDING (100M shares)"
   - `backend/terminal_valuation.py:400` (docstring):
     "shares_outstanding: Fixed at 100M for this simulation"
   - `backend/config.py:828`: `TV_SHARES_OUTSTANDING: int = int(_tv.get("shares_outstanding", 6_500_000))`
   The `bridge_note` string (`backend/terminal_valuation.py:462`) prints
   `{shares_outstanding//1_000_000}M shares`, which renders "6M" under the config default.

3. **ESG-adjusted WACC range — docstring vs code clamp.**
   - Docstring `backend/systemic_risk_engine.py:29`:
     "Ranges: WACC 3%-15% (base 5%, ±10% ESG swing)"
   - Code `backend/systemic_risk_engine.py:39`:
     `adjusted = round(max(0.03, min(0.20, adjusted)), 4)  # FIX-C: raised cap from 15% to 20%`

4. **CAROIC invested capital — docstring vs call site.**
   - Docstring `backend/engine.py:2191-2192`: "Total capital deployed (corporate
     treasury as proxy for total capital base)."
   - Call site `backend/engine.py:3558`:
     `_ic_proxy = max(0.0, sum(bu.get("revenue_base", 0) for bu in ctx.new_bus) * 0.5)`
     tagged `caroic_result["invested_capital_method"] = "revenue_proxy_0.5x"`
     (`backend/engine.py:3566`).

5. **Burnout OPEX penalty — docstring vs code.**
   - Docstring `backend/engine.py:659`: "OPEX penalty threshold: burnout > 40 →
     +0.3% OPEX per burnout point above 40" (a linear rule from 40).
   - Code `backend/engine.py:678-682`: quadratic from `BURNOUT_OPEX_THRESHOLD`
     (20.0): `penalty_rate = round(((new_burnout - BURNOUT_OPEX_THRESHOLD) ** 2) * BURNOUT_OPEX_PENALTY_COEFF, 4)`
     with the in-code comment "Smooth quadratic curve: 0% at 20 -> 18% at 100".
   - The call site's comment repeats the stale figure —
     `backend/round_logic.py:1954`: `# OPEX penalty when burnout > 40`.

6. **`inflation_index` default — model vs engine docstring.**
   - `backend/models.py:178`: `inflation_index: Optional[float] = 0.025`
   - `backend/engine.py:863`: "Default inflation_index = 0.05 (5% per 6-month
     period, ~10% annualized)"

7. **`COALITION_STRIKE_GAIN` defined twice in `config.py`.**
   - `backend/config.py:405`: `float(_strike.get("coalition_strike_gain", 0.5))`
   - `backend/config.py:457`: `float(_coal.get("strike_gain", 0.5))`
   Same default (0.5) but different config sections; the later binding (line 457)
   is the one in effect at import time.

8. **Supply-chain transparency scandal penalty documented but absent.**
   Docstring `backend/systemic_risk_engine.py:66` says "Degrades via: … scandal
   events (-25)", but no `-25` entry exists in the `flag_boosts` table
   (`backend/systemic_risk_engine.py:70-79`). The most negative entry is
   `"deny_and_deflect": -15.0`.

9. **`historical_ebitda`, `tco2e_emissions` and `absolute_emissions` each have two
   writers.** `backend/engine.py:3514, 3517, 3525` and
   `backend/router.py:3290, 3293, 3297`. The arithmetic matches; the router copies
   use `or 0` None-guards while the engine copies use `.get(key, 0)` /
   direct indexing. The router version runs after the tick and overwrites.

10. **`governance_risk_score` default disagreement.** The Pydantic model defaults
    it to `0` (`backend/models.py:200`), while every engine read defaults to `20`
    (`backend/engine.py:3682`, `4388`, `4389`, `4404`) and the SDG mapping treats
    20-25 as the neutral threshold (`backend/engine.py:2039`, `2044`).

11. **`natural_capital_debt` unit disagreement.** The engine treats it as
    unit-less points capped at 5000 (`backend/config.py:237`) and prices them
    explicitly at `backend/round_logic.py:353`, but the frontend catalog formats
    it as money — `frontend/app/utils/kpiFormats.js:31`:
    `unit: '$', format: _money`.

12. **`water_dependency` unit disagreement.** Backend comments state a 0-100 scale
    (`backend/engine.py:2032`, `3684-3689`) and it is divided by 100 before use as
    a fraction (`backend/engine.py:3691`); the frontend catalog formats it as a
    percentage — `frontend/app/utils/kpiFormats.js:33`: `unit: '%', format: _pct`.

13. **M_R ceiling comment history.** `backend/terminal_valuation.py:52-54` says
    "MR_CEILING : 2.05 — 10bp above the absolute documented maximum of 2.03
    (1.93 base max + 0.10 JT-scaling headroom)", while the note at
    `backend/terminal_valuation.py:295-299` records that "the 2.03 previously
    written here was wrong by 0.01" and pins 1.93 / 2.02 / 1.98. Both texts are
    present in the file at HEAD `0ad1246`.
