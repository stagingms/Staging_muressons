# Claims Register Re-execution — M-class rows
Repo: muressons-sim  |  HEAD verified: 0ad1246  |  Backend: backend/
Method: every verdict traced to code read at this commit. Option `flags_set`
entries are written as LIST ELEMENTS under active_event_flags["r{N}_flags"]
(round_logic.py:3769-3773); flag_utils.collect_all_flags (flag_utils.py:22-55)
DOES union those list elements, so a consumer routed through
_collect_all_flags CAN see them, but a consumer doing flags.get("x") or
"x" in active_event_flags on an option flag cannot.

## M-001 — CORRECTED
CLAIM AS PRINTED: Natural Capital Debt raises the cost of debt by 0.0001 per unit — one basis point per unit of NCD.
FINDING: The 0.0001/unit coefficient is real, but it prices the NCD ACCRUAL rate, not the firm's cost of debt: rate = corporate_cost_of_capital + NCD x 0.0001, and that rate is charged against the NCD stock itself (NCD compounds). NCD does not appear anywhere in calc_esg_adjusted_wacc, so it never reaches WACC or the exit multiple; the resulting per-BU `interest_rates` dict is written to events only (engine.py:3485) and read by nothing.
EVIDENCE: backend/config.py:348 `NCD_INTEREST_COEFFICIENT: float = float(_nat_cap.get("interest_coefficient", 0.0001))` (simulation_config.json confirms 0.0001); backend/engine.py:623 `return round(base_rate + (natural_capital_debt * NCD_INTEREST_COEFFICIENT), 6)`; backend/engine.py:3446-3451 `rate = calc_natural_capital_interest(corporate_cost_of_capital, old_ncd)` / `debt_charge = round(old_ncd * rate, 2)` / `new_ncd = round(old_ncd + debt_charge, 2)`; backend/systemic_risk_engine.py:31-36 (WACC terms: carbon, governance, SLO, nature — no NCD term).
CORRECTED CLAIM: Natural Capital Debt adds one basis point per unit to the interest rate charged on the NCD stock itself (rate = cost of capital + NCD x 0.0001), so NCD compounds against itself; it does not enter the ESG-adjusted WACC or the exit multiple.

## M-002 — CORRECTED
CLAIM AS PRINTED: Synergy engine: New_OPEX = Old_OPEX x (1 - sqrt(ratio) x 0.7 x Synergy).
FINDING: The uncapped form was replaced by F-06. The sqrt curve survives but is now a fraction captured of a hard per-round ceiling.
EVIDENCE: backend/engine.py:602-604 `captured = max(0.0, min(1.0, math.sqrt(ratio) * SYNERGY_DAMPENING_FACTOR * max(0.0, synergy_multiplier)))` / `factor = 1.0 - SYNERGY_MAX_REDUCTION_PER_ROUND * captured`; config.py:335 dampening 0.7, config.py:344 max_reduction_per_round 0.06 (both confirmed in simulation_config.json).
CORRECTED CLAIM: captured = min(1, sqrt(ratio) x 0.7 x Synergy); New_OPEX = Old_OPEX x (1 - 0.06 x captured) — i.e. at most a 6% OPEX cut per round. (See M-090, which states the current form correctly.)

## M-003 — CORRECTED
CLAIM AS PRINTED: VRIO advantage decays 2% per round unless reinvested; starts at 0.80.
FINDING: The 0.80 start is right; the decay rate is 5%, not 2%. It is config-driven (`engine_parameters.imitation_decay.default_rate`) and simulation_config.json ships 0.05.
EVIDENCE: backend/bu_profiles.py:468 `"vrio_advantage": 0.80`; backend/engine.py:634 `return round(advantage_current * (1.0 - imitation_decay_rate), 4)`; backend/config.py:740-742 `_IMITATION_DECAY_DEFAULT: float = 0.05` / `DEFAULT_IMITATION_DECAY_RATE = float(_imit.get("default_rate", _IMITATION_DECAY_DEFAULT))`; simulation_config.json `engine_parameters.imitation_decay = {"default_rate": 0.05}`.
CORRECTED CLAIM: VRIO advantage starts at 0.80 and decays 5% per round (config-driven, `imitation_decay.default_rate`, 0.05 as shipped) unless reinvested.

## M-004 — CONFIRMED
CLAIM AS PRINTED: Business units more than 15% above average revenue cannibalise overlapping units.
FINDING: Exact. The aggressor test is strict (`<= avg x 1.15` skips), and only BUs with a non-zero entry in the _MARKET_OVERLAP matrix are victims; the penalty is victim_revenue x 0.03 x overlap.
EVIDENCE: backend/engine.py:962 `if aggressor_rev <= avg_rev * CANNIBALIZATION_AGGRESSOR_MULT: continue`; config.py:409-410 base_rate 0.03, aggressor_threshold_multiplier 1.15.

## M-005 — CONFIRMED
CLAIM AS PRINTED: SUPERSEDED — see M-005a to M-005f. The documented "accuracy >=90% unlocks a $2M treasury bonus" is NOT implemented in router.py. Do not print. [Code awards 1,000 bonus points at >=80% full-quadrant accuracy.]
FINDING: True at this commit, and the config now says so explicitly. There is no $2M treasury bonus and no 90% key anywhere.
EVIDENCE: backend/round_configs.py:124-133 special_rules comment "the keys that used to sit here (accuracy_threshold: 90 and a $2M accuracy_bonus_amount treasury bonus) described a mechanic that never existed" plus `"accuracy_threshold_pct": 80, "accuracy_bonus_points": 1000`; backend/router.py:4889-4892 `accuracy_bonus = int(_r2_rules.get("accuracy_bonus_points", 1000)); global_state["bonus_score"] = ... + accuracy_bonus`.

## M-005a — CORRECTED
CLAIM AS PRINTED: Round 2 materiality budget is $15,000,000 and is released in proportion to Q1 recall: allocated = 15,000,000 x (|submitted Q1 ∩ true Q1| / |true Q1|). With six true Q1 issues each miss costs $2,500,000.
FINDING: Budget and recall formula are exact. The "six true Q1 issues / $2,500,000 a miss" arithmetic is wrong for the shipped default dictionary, which has FIVE Q1 issues — so each miss withholds $3,000,000. (Superseded on semantics by M-047: it is a ring-fenced release, not a cost.)
EVIDENCE: backend/round2_csrd.py:358 `"total_materiality_budget": 15_000_000`; backend/router.py:4803-4806 `correct_q1_count = len(q1_submission.intersection(q1_target_issue_ids))` / `m_acc = correct_q1_count / len(q1_target_issue_ids)` / `allocated_budget = int(total_budget * m_acc)`; the active default dictionary (backend/db/materiality_config.json, 8 issues) classifies 5 q1 / 2 q2 / 1 q3 / 0 q4 under round2_csrd.correct_quadrant_v2.
CORRECTED CLAIM: The Round 2 materiality budget is $15,000,000, released in proportion to Q1 recall; against the shipped default dictionary's FIVE Q1 issues each missed issue withholds $3,000,000.

## M-005b — CONFIRMED
CLAIM AS PRINTED: CFO precision gate: any issue placed in Q1 that is not genuinely doubly material causes outright rejection of the submission. A force override is available at a cost of -10 group reputation and sets cfo_override_used_r2.
FINDING: Exact, including the -10 and the flag name.
EVIDENCE: backend/router.py:4782-4797 `invalid_q1_issues = q1_submission - q1_target_issue_ids` ... `global_state["group_reputation"] = max(0, ... - 10)` / `global_state["cfo_override_used_r2"] = True` / else `raise HTTPException(status_code=400, ...)`.

## M-005c — CORRECTED
CLAIM AS PRINTED: Full-quadrant accuracy at or above 80% awards 1,000 bonus points. Ambiguous issues placed in an adjacent quadrant score 0.5 credit. materiality_aligned is set when accuracy >= 80% AND the governance choice is not Option C.
FINDING: First two sentences exact. The third is wrong post-F-1: the flag is now tiered and materiality_aligned requires Option A specifically; Option B at >=80% yields materiality_partial (+0.05), not materiality_aligned.
EVIDENCE: backend/router.py:4859-4862 (0.5 adjacent credit for is_ambiguous); backend/round_logic.py:3604-3612 `if choice == "option_c": tier = "materiality_ignored"` / `elif acc_ok and choice == "option_a": tier = "materiality_aligned"` / `elif acc_ok and choice == "option_b": tier = "materiality_partial"`.
CORRECTED CLAIM: Accuracy >=80% awards 1,000 bonus points and adjacent placements of ambiguous issues score 0.5 credit; materiality_aligned requires accuracy >=80% AND Option A, Option B at the same accuracy yields materiality_partial, and Option C yields materiality_ignored regardless.

## M-005d — CORRECTED
CLAIM AS PRINTED: A separate $1,000,000 Q2 disclosure budget is released pro rata: 1,000,000 x (correctly placed Q2 issues carrying disclosure_required / 4).
FINDING: The $1,000,000 and the pro-rata shape are right; the fixed denominator of 4 was replaced. The denominator is now the count of disclosure-carrying Q2 issues in the ACTIVE dictionary — two on the shipped default — and the ratio is capped at 1.0.
EVIDENCE: backend/router.py:4907-4914 `active_q2_disclosure = sum(1 for i in all_issues if i.get("disclosure_required") and _correct_quadrant_v2(i) == "q2")` / `max_q2 = max(active_q2_disclosure or len(Q2_DISCLOSURE_ISSUES), 1)` / `disclosure_allocated = int(disclosure_budget * min(1.0, q2_disclosure_correct / max_q2))`; backend/round2_csrd.py:364 `"disclosure_investment_budget": 1_000_000`.
CORRECTED CLAIM: A separate $1,000,000 Q2 disclosure budget is released pro rata against the disclosure-carrying Q2 issues in the ACTIVE dictionary (two on the shipped default, so each correct Q2 placement releases $500,000), capped at the full amount, and is credited into the same ring-fenced fund.

## M-005e — CORRECTED
CLAIM AS PRINTED: Round 2 governance Option C (CEO-only sign-off) applies a 40% clawback to the already-allocated materiality budget, +10 governance risk and -5 reputation, and blocks materiality_aligned regardless of matrix accuracy.
FINDING: All four elements are live at this commit. The one correction is the base and direction: the clawback is 40% of the RELEASED amount, taken from the restricted fund first with any shortfall charged to treasury, so it always reduces the position (it no longer reduces a debit).
EVIDENCE: backend/round_logic.py:3641-3652 `pct = float(cfg_opts.get("option_c", {}).get("budget_clawback_pct", 0.40))` / `clawback = round(released * pct, 2)` / `taken = min(clawback, fund)` / `gs["corporate_treasury"] = ... - shortfall`; backend/round_configs.py:193 `"budget_clawback_pct": 0.40`; round_configs.py:194 impacts `reputation: -5, governance_risk_delta: +10`; round_logic.py:3605 Option C forces materiality_ignored.
CORRECTED CLAIM: Round 2 Option C claws back 40% of the RELEASED materiality fund (restricted fund first, any shortfall charged to treasury), applies +10 governance risk and -5 reputation, and forces materiality_ignored regardless of matrix accuracy.

## M-005f — CONFIRMED
CLAIM AS PRINTED: materiality_aligned pays +0.10 on the Regenerative Multiple at the Round 10 terminal valuation.
FINDING: Confirmed — see M-048 evidence; the tier table pays aligned +0.10 / partial +0.05 / ignored 0.
EVIDENCE: backend/round_logic.py:3625-3627 tier message "materiality_aligned → +0.10 M_R at terminal valuation"; M_R component table verified in terminal_valuation.py (see M-048).

## M-006 — CONFIRMED
CLAIM AS PRINTED: tCO2e = CI x revenue / 1,000,000. Group carbon intensity is revenue-weighted: sum(CI x rev) / sum(rev).
FINDING: Both halves exact.
EVIDENCE: backend/engine.py:3517-3522 `sum(bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1_000_000 for bu in ctx.new_bus)`; backend/engine.py:154-168 calc_revenue_weighted_avg_ci `Σ(CI_i × Rev_i) / Σ(Rev_i)` (falls back to a simple mean only when total revenue is 0).

## M-007 — CORRECTED
CLAIM AS PRINTED: Carbon price base $50/tonne escalating 5% a year; $350 under Regulatory Shutdown; $750 under Climate Black Swan.
FINDING: $50 and 5% match the live config, but the escalation compounds PER ROUND, not per year (exponent is round_number - 1). The $350/$750 figures are pathway overrides on a DIFFERENT price — the terminal shadow carbon price (standard $250) — not on the $50 economic fee. There are four carbon prices in total (see M-077/M-087).
EVIDENCE: simulation_config.json `economic_parameters.carbon_price_base = 50`, `carbon_price_growth_rate = 0.05`; backend/config.py:184-185; backend/engine.py:3933 `fee_per_ton = round(base_fee * (1 + ECONOMIC_CARBON_PRICE_GROWTH) ** (current_global.get("round_number", 1) - 1), 2)`; backend/ending_pathways.py:458 `"carbon_tax_per_ton": 350` (Regulatory Shutdown), :169 `750` (Climate Black Swan), :263 and :360 `250` (standard); backend/config.py:195 FINANCIAL_SHADOW_CARBON_PRICE 250.0.
CORRECTED CLAIM: The economic carbon fee is $50/tonne escalating 5% PER ROUND; separately, the terminal shadow carbon price is $250/tonne, overridden to $350 under Regulatory Shutdown and $750 under Climate Black Swan.

## M-008 — CORRECTED
CLAIM AS PRINTED: Greenwashing engine: a green option (A or C) backed by less than 15% investment ratio costs 15 group reputation points and sets auditor tolerance to Hostile. Moderate options use a 10% threshold.
FINDING: Three errors. (1) Classification is config-driven via each option's `green_claim` key, not positional A/C — claim_level None means the option is never checked. (2) The penalty is 15 SOCIAL LICENCE points on every BU, not group reputation (moderate = 7.5). (3) Nothing in this engine touches auditor tolerance; the "auditor tolerance set to Hostile" text belongs to the BRSR side track's R4 self-assessment branch. The 15%/~10% thresholds are right, and there is now an absolute escape: total CapEx >= $3,000,000 cancels the scandal outright.
EVIDENCE: backend/engine.py:1233-1245 `if claim_level not in ("full", "moderate"): return False, 0.0` ... `if total_capex >= GREENWASH_ABS_CAPEX_FLOOR: return False, 0.0` ... `moderate_threshold = green_investment_threshold * GREENWASH_MODERATE_THRESHOLD_SCALE`; backend/engine.py:4261-4263 `bu["social_license_score"] = max(0.0, round(bu["social_license_score"] - greenwash_penalty, 2))`; config.py:474-478 (threshold 0.15, slo_penalty 15.0, moderate scale 0.67, penalty scale 0.5), config.py:694 GREENWASH_ABS_CAPEX_FLOOR 3,000,000; backend/brsr_controller.py:363-365 (the Hostile-auditor text).
CORRECTED CLAIM: An option whose config carries green_claim="full" backed by under 15% of the CSF pool costs 15 social licence points on every business unit; green_claim="moderate" uses ~10% and costs 7.5; either claim is cancelled outright by total CapEx of $3,000,000 or more.

## M-009 — CORRECTED
CLAIM AS PRINTED: Round 5 cyclone: base damage $12M applied if the stochastic roll exceeds 0.75. actual_damage = base x (1 - resilience_factor). Factors: 0.85 hard engineering, 0.60 nature-based, 0.00 insurance only. Protection is active from R7 — a two-round delay.
FINDING: All numbers correct, but the roll condition is INVERTED: damage strikes when roll < 0.75, i.e. 75% of the time, not 25%. The threshold also escalates with the climate tipping tier (+0.05 warning / +0.10 stressed / +0.15 tipped, capped 0.95). And the multiplier used in the damage line is `active_resilience_factor` from events, which is zero in R5 itself — the R5 option's own factor is queued as a two-round pending_capex project, so the R5 cyclone is never mitigated by the R5 choice.
EVIDENCE: backend/round_configs.py:333-335 `"stochastic_event": True, "base_damage": 12_000_000, "stochastic_threshold": 0.75`; option resilience_factor 0.85 / 0.60 / 0.0 at round_configs.py:353, 373, 393; backend/impact_engine.py:124 `if roll < threshold:` then :125 `actual_damage = round(base_damage * (1 - effective_resilience), 2)`; impact_engine.py:120-121 `active_resilience_factor = events.get("active_resilience_factor", 0.0)`; impact_engine.py:155-160 project queued with `"rounds_remaining": 2`; engine.py:2371-2373 decrement-then-fire.
CORRECTED CLAIM: The Round 5 cyclone strikes when the stochastic roll falls BELOW 0.75 (a 75% chance, raised up to 0.95 by the climate tipping tier), doing $12M x (1 - active resilience); the option's own resilience factor (0.85 hard engineering / 0.60 nature-based / 0.00 insurance) is a two-round pending CapEx project that only becomes active in R7, so it cannot reduce the R5 damage.

## M-010 — CONFIRMED
CLAIM AS PRINTED: Round 7 Option C sets synergy_unlock: +0.30 synergy multiplier and +0.15 M_R at terminal valuation. OPEX savings are captured separately in EBITDA, so the premium is not double-counted.
FINDING: Exact, including the double-count reasoning, which the code states in the same words. Note the premium is gated: it needs synergy_multiplier >= 0.80 (now a ±0.05 linear ramp, not a cliff), and the flag reaches calculate_mr only because flag_utils.collect_all_flags unions the r7_flags list.
EVIDENCE: backend/round_configs.py:525-529 option_c "Waste-to-Energy Partnership", `"flags_set": ["waste_to_energy", "synergy_unlock"]`, `"synergy_multiplier_boost": 0.30`; backend/terminal_valuation.py:218-224 `# STRAT-010: Reduced from +0.30 → +0.15` / `b = round(0.15 * synergy_frac, 4)` with the comment "Synergy OPEX savings already flow through terminal_ebitda"; terminal_valuation.py:216 ramp gate at 0.80. (The round_configs.py:529 inline comment "harmonised to match M_R +0.30" is stale.)

## M-011 — CORRECTED
CLAIM AS PRINTED: Instability Discount: -0.40 M_R when average social licence falls below 75.
FINDING: The -0.40 magnitude and the 75 threshold are right, but the cliff was replaced by a linear ramp (GAME-2): the penalty is 0 at SLO 80, -0.20 at 75, and the full -0.40 only at SLO 70 or below.
EVIDENCE: backend/terminal_valuation.py:266-269 `_slo_frac = _ramp_fraction(avg_slo, 75.0, _MR_RAMP_BAND_KPI, "below")` / `b = round(-0.40 * _slo_frac, 4)`; terminal_valuation.py:88 `_MR_RAMP_BAND_KPI: float = 10.0`; terminal_valuation.py:92-104 _ramp_fraction docstring ("1.0 at threshold-band/2, 0.0 at threshold+band/2").
CORRECTED CLAIM: The Instability Discount ramps linearly from 0 at average social licence 80 to the full -0.40 M_R at 70, passing through -0.20 at the nominal 75 threshold.

## M-012 — CORRECTED
CLAIM AS PRINTED: Contagion engine: Group_Rep = Avg_Rep - 50 x sigmoid((severity - 30) / 15).
FINDING: This is the pre-F-01 form. The dip is now NORMALISED so that zero severity produces zero dip; the raw sigmoid was 0.119 at severity 0 and silently removed ~6 reputation points every quiet round.
EVIDENCE: backend/engine.py:477-491 `baseline_input = (0.0 - midpoint) / safe_steepness` ... `normalised = max(0.0, (sigmoid_value - baseline_sigmoid) / (1.0 - baseline_sigmoid))` / `rep_drop = max_drop * normalised`; config.py:291/294/297 max_drop 50.0, midpoint 30.0, steepness 15.0.
CORRECTED CLAIM: Group_Rep = Avg_Rep - 50 x (sigma(s) - sigma(0)) / (1 - sigma(0)), where sigma(s) = 1/(1 + e^-((s - 30)/15)) — the normalisation makes zero severity mean zero dip.

## M-013 — CONFIRMED
CLAIM AS PRINTED: Stakeholder fatigue: efficiency = 1 / (1 + 0.3 x crisis_count).
FINDING: Formula and factor exact. (Its point of application changed — see M-091 — but the ratio is as printed.)
EVIDENCE: backend/engine.py:993-994 `efficiency = 1.0 / (1.0 + fatigue_factor * crisis_count_lifetime)`; config.py:424 STAKEHOLDER_FATIGUE_FACTOR 0.3; applied at engine.py:3369-3376.

## M-014 — CONFIRMED
CLAIM AS PRINTED: Burnout drifts +6 per round naturally; the OPEX penalty is quadratic above an index of 20.
FINDING: Both exact. Penalty rate = (burnout - 20)^2 x 0.000028125, i.e. 0% at 20 rising to ~18% at 100.
EVIDENCE: backend/config.py:356-359 natural_drift 6.0, opex_threshold 20.0, opex_penalty_coeff 0.000028125; backend/engine.py:676-681 `penalty_rate = round(((new_burnout - BURNOUT_OPEX_THRESHOLD) ** 2) * BURNOUT_OPEX_PENALTY_COEFF, 4)`. (Note engine.py:660 docstring still says "burnout > 40 → +0.3% OPEX" — stale text above live code.)

## M-015 — CONFIRMED
CLAIM AS PRINTED: Just Transition scaling factor = min(1.5, 1.0 + HR_investment_rounds x 0.10). The multiplier therefore caps at five funded HR rounds.
FINDING: Exact. Note it applies only when community_fund or managed_transition is held.
EVIDENCE: backend/terminal_valuation.py:240-241 `if hr_investment_rounds > 0 and (flags.get("community_fund") or flags.get("managed_transition")): jt_scaling = round(min(1.5, 1.0 + hr_investment_rounds * 0.10), 2)`; hr_investment_rounds counted at flag_utils.py:58-63 from `hr_invested_r{N}` keys.

## M-016 — CORRECTED
CLAIM AS PRINTED: Difficulty tiers: probability multiplier 0.5 / 1.0 / 1.5; impact multiplier 0.7 / 1.0 / 1.3; treasury floors -$500M / -$200M / -$50M.
FINDING: The two multiplier rows are exact. The per-tier treasury floors NO LONGER EXIST — treasury_floor was one of four keys removed from DIFFICULTY_TIERS as unread; there is one global floor of -$500,000,000. The tiers were also re-keyed foundation/advanced/expert and gained npc_max_fine ($6M/$12M/$25M) and covenant_trigger_ratio (4.5/3.5/2.5).
EVIDENCE: backend/black_swan_registry.py:41-43 "The four keys no code read (treasury_floor, bailout_amount, natural_decay_rate, and the never-consulted npc_max_fine) are gone or wired"; black_swan_registry.py:44-66 DIFFICULTY_TIERS; backend/config.py:224 `FINANCIAL_TREASURY_FLOOR = float(_financial.get("treasury_floor", -500_000_000))`, simulation_config.json financial_parameters.treasury_floor -500000000.
CORRECTED CLAIM: Difficulty tiers (foundation / advanced / expert) set probability multiplier 0.5 / 1.0 / 1.5, impact multiplier 0.7 / 1.0 / 1.3, regulator fine cap $6M / $12M / $25M and covenant trigger ratio 4.5x / 3.5x / 2.5x; the treasury floor is a single global -$500M, not per tier.

## M-017 — CORRECTED
CLAIM AS PRINTED: Macro interest rate cycle modifies WACC: R1-R2 easing -1%, R3-R5 neutral 0%, R6-R8 tightening +2%, R9-R10 crisis premium +3%.
FINDING: The first two bands are exact; the last two are overstated. Tightening is +1% (not +2%) and the crisis premium is +1.5% in R9 and +2.0% in R10 (not a flat +3%). The modifier is applied to the corporate cost of capital before the ESG-WACC adjustment.
EVIDENCE: backend/engine.py:1254-1263 `_MACRO_RATE_CYCLES = {1: -0.010, 2: -0.010, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.010, 7: 0.010, 8: 0.010, 9: 0.015, 10: 0.020}`; applied at engine.py:3437-3441.
CORRECTED CLAIM: Macro interest rate cycle: R1-R2 easing -1.0%, R3-R5 neutral 0%, R6-R8 tightening +1.0%, R9 crisis +1.5% and R10 crisis +2.0%, applied to the corporate cost of capital before the ESG-WACC adjustment.

## M-018 — CORRECTED
CLAIM AS PRINTED: EV = (Terminal EBITDA + Green Fund) x Exit Multiple x M_R x M_SDG. Equity = EV - Net Debt. 100,000,000 shares; $50.00 IPO reference price.
FINDING: The formula and the $50.00 reference are right, with two qualifications: the Green Fund is added ONLY in Advanced Climate mode, and EBITDA is floored at 0 before entering the formula. The share count is 6,500,000, not 100,000,000 — the code comment saying "100 million shares" is stale text above a config-driven constant.
EVIDENCE: backend/terminal_valuation.py:530-536 `base = ebitda + (green_fund_balance if is_advanced_climate else 0)` / `tv = round(base * effective_multiple * mr * m_sdg, 2)`; :522-524 `ebitda = max(EBITDA_FLOOR, raw_ebitda)`; backend/config.py:828-829 `TV_SHARES_OUTSTANDING: int = int(_tv.get("shares_outstanding", 6_500_000))`, `TV_IPO_PRICE = float(_tv.get("ipo_price_per_share", 50.0))`; simulation_config.json terminal_valuation.shares_outstanding = 6500000 (db/simulation_config.json agrees); terminal_valuation.py:33 comment "# 100 million shares (IPO anchor)" is stale.
CORRECTED CLAIM: EV = (Terminal EBITDA, floored at zero, + Green Fund in Advanced Climate mode only) x Exit Multiple x M_R x M_SDG; Equity = EV - Net Debt; 6,500,000 shares outstanding at a $50.00 IPO reference price.

## M-019 — CONFIRMED
CLAIM AS PRINTED: Exit multiple: fixed 12.0x by default, or WACC-linked as (1 + g) / (WACC - g) with g = 2%, floor 6.0x and ceiling 18.0x.
FINDING: Exact. WACC <= g is a guarded degenerate case that snaps to the ceiling.
EVIDENCE: backend/terminal_valuation.py:481 `exit_multiple=12.0` default; :339-346 `if wacc <= growth_rate: multiple = ceiling` else `multiple = (1.0 + growth_rate) / (wacc - growth_rate)` / `multiple = round(max(floor, min(ceiling, multiple)), 2)`; simulation_config.json long_run_growth 0.02, exit_multiple_floor 6.0, exit_multiple_ceiling 18.0.

## M-020 — CONFIRMED
CLAIM AS PRINTED: M_SDG = 1.0 + (SDG Impact Score / 100) x 0.25, giving a range of 0.97 to 1.26.
FINDING: Exact, formula and stated range (score range -11 to 105).
EVIDENCE: backend/terminal_valuation.py:368 `m_sdg = round(1.0 + (sdg_impact_score / 100.0) * 0.25, 4)`; docstring :360-366 "Range: -11 (all Option C) to 105 (all Option A). M_SDG range: 0.97 to 1.26."

## M-021 — REFUTED (code exists but is unreachable)
CLAIM AS PRINTED: Adaptive crisis severity scales up to x1.3 for strong performers and down to x0.8 for strugglers, with a further +5% per round escalation after Round 5.
FINDING: The arithmetic exists exactly as printed, but the value it returns is never fed back into the tick. The call is made AFTER the scripted severity has already been applied, and the result is stored only as an underscore-prefixed diagnostic with `applied: False`. It also only runs for round_number > 5. Nothing the player sees changes.
EVIDENCE: backend/branching_engine.py:243-251 `adaptive_mult = 1.0 + (perf_index - 70) / 100  # Up to 1.3x` / `adaptive_mult = 0.8 + (perf_index / 100)` / `round_mult = 1.0 + (round_number - 5) * 0.05`; backend/branching_engine.py:205-212 "the value calc_adaptive_crisis_severity returns have NO consumer in the tick"; backend/round_logic.py:1292-1294 `sev_diag["applied"] = False` / `sev_diag["adjusted_severity_not_applied"] = adj_severity` / `extra["_adaptive_crisis_severity_diagnostic"] = sev_diag`.

## M-022 — CONFIRMED
CLAIM AS PRINTED: Side-track round windows and prerequisites are as defined in the track classes in backend/side_tracks/*/track.py, which are the source of truth.
FINDING: The six track classes each expose num_rounds, available_window and cross_track_prerequisites as properties; all values quoted in M-023 to M-028 were read from them at this commit.
EVIDENCE: backend/side_tracks/{supply_chain,ethics_sustainability,stakeholder_management,sustainability_reporting,corporate_sdg,brsr_ngrbc}/track.py.

## M-023 — CONFIRMED
CLAIM AS PRINTED: Supply Chain side track: 7 rounds, available window R3-R8, no cross-track prerequisites.
EVIDENCE: backend/side_tracks/supply_chain/track.py:54-55 `return 7`; :58-59 `return (3, 8)  # Can be started after main R3, must complete before R8`; :74-75 `return []  # Supply Chain has no prerequisites; it enriches Ethics track`.

## M-024 — CONFIRMED
CLAIM AS PRINTED: Ethics & Sustainability side track: 5 rounds, available window R2-R7, prerequisite: supply_chain.
EVIDENCE: backend/side_tracks/ethics_sustainability/track.py:48-49 `return 5`; :52-53 `return (2, 7)`; :66-67 `return ["supply_chain"]  # SC track enriches modern slavery context`.

## M-025 — CONFIRMED
CLAIM AS PRINTED: Stakeholder Management side track: 4 rounds, available window R1-R6, no prerequisites.
EVIDENCE: backend/side_tracks/stakeholder_management/track.py:31 `def num_rounds(self) -> int: return 4`; :33 `def available_window(self) -> tuple[int, int]: return (1, 6)`; :45 `def cross_track_prerequisites(self) -> list[str]: return []`.

## M-026 — CONFIRMED
CLAIM AS PRINTED: Sustainability Reporting side track: 5 rounds, available window R2-R8, prerequisite: ethics_sustainability.
EVIDENCE: backend/side_tracks/sustainability_reporting/track.py:32 `return 5`; :34 `return (2, 8)`; :47-48 `return ["ethics_sustainability"]`.

## M-027 — CONFIRMED
CLAIM AS PRINTED: Corporate SDG Deep Track: 5 rounds, available window R1-R8, no prerequisites.
EVIDENCE: backend/side_tracks/corporate_sdg/track.py:94-95 `return 5`; :98-100 `return (1, 8)  # Independently triggerable from R1 through R8`; :113-114 `return []  # No prerequisites`.

## M-028 — CONFIRMED
CLAIM AS PRINTED: BRSR NGRBC Deep Dive: num_rounds = 10, available window R2-R8, prerequisites: sustainability_reporting AND ethics_sustainability.
FINDING: Exact, and the full chain supply_chain -> ethics_sustainability -> sustainability_reporting -> brsr_ngrbc follows from M-024 and M-026.
EVIDENCE: backend/side_tracks/brsr_ngrbc/track.py:25 `def num_rounds(self) -> int: return 10`; :27 `return (2, 8)`; :40-41 `return ["sustainability_reporting", "ethics_sustainability"]`.

## M-029 — CORRECTED
CLAIM AS PRINTED: The default Round 2 issue library contains twenty issues: six Q1, four Q2, four Q3, six Q4. Each carries severity, likelihood, time horizon and an ESRS topic reference.
FINDING: The 20-issue 6/4/4/6 set is round2_csrd.CSRD_ISSUES and its counts and Q1 membership are exact — but it is NOT the default scoring library (M-045: the scored dictionary is the 8-issue materiality_db.DEFAULT_CONFIG / db/materiality_config.json, 5 Q1 / 2 Q2 / 1 Q3 / 0 Q4). Two further errors of detail: five of the six Q4 issues carry NO esrs_reference at all (paper_recycling, plastic_straws, exec_travel, ergonomic_chairs, led_bulbs), and TWO issues have a long time horizon (scope3_carbon Q1 and employee_volunteering Q2), not one.
EVIDENCE: backend/round2_csrd.py CSRD_ISSUES — 20 ids parsed, correct_quadrant counts 6/4/4/6, Q1 = water_scarcity, e_waste, tier3_labor, ai_bias, scope3_carbon, plastic_packaging; time_horizon values 15 short / 3 medium / 2 long; esrs_reference absent on the five Q4 ids listed. Scoring path: backend/router.py:4671-4683 -> materiality_packs.resolve_session_bu_config / mat_db.get_current_config.
CORRECTED CLAIM: The 20-issue CSRD_ISSUES teaching set (6 Q1 / 4 Q2 / 4 Q3 / 6 Q4) is display material, not the scoring dictionary; each issue carries severity, likelihood and a time horizon, but five Q4 issues carry no ESRS reference, and two issues (scope3_carbon, employee_volunteering) have a long time horizon.

## M-030 — CORRECTED
CLAIM AS PRINTED: The engine classifies an axis as material at a severity x likelihood product at or above 12 out of 25.
FINDING: ESRS_MAT_THRESHOLD = 12 exists and is used exactly that way — but only when ALL FOUR dual-axis scores are present. No shipped dictionary carries them, so on every shipped path the categorical labels govern and the 12/25 product is never the operative rule.
EVIDENCE: backend/round2_csrd.py:501 `ESRS_MAT_THRESHOLD = 12  # out of 25 (5x5)`; :512-522 `if _has_dual_axis_scores(issue): ... return product >= ESRS_MAT_THRESHOLD` / `# Legacy single-pair severity_score/likelihood_score is NOT sufficient ... return issue.get("financial_impact" if axis == "fin" else "societal_impact") == "high"`.
CORRECTED CLAIM: The threshold of 12 out of 25 applies only to dictionaries carrying all four dual-axis scores; on every shipped dictionary an axis is material when its categorical label (financial_impact / societal_impact) is "high".

## M-031 — CONFIRMED
CLAIM AS PRINTED: Stakeholder panels: four groups (investors, own workforce, NGOs/communities, subject-matter experts) at $750,000 each; or per issue at $250,000 for the first four and $500,000 thereafter, maximum eight.
FINDING: Exact, including the tier break at 4 and the cap at 8; all four groups cost $3.0m as the note says.
EVIDENCE: backend/round2_csrd.py:381-384 `"base_fee_per_issue_usd": 250_000, "extended_fee_per_issue_usd": 500_000, "min_issues": 1, "max_issues": 8, "tier_break": 4`; :396/406/417/428 `"fee_usd": 750_000` for investors / workers / ngos / experts; pricing applied at backend/router.py:4756-4778.

## M-032 — CORRECTED
CLAIM AS PRINTED: Panel biases are deterministic: investors push social Q2 issues to Q3; NGOs push financial Q3 issues to Q2; own workforce pushes social issues from Q2/Q4 to Q1; subject-matter experts return the correct quadrant every time.
FINDING: The four bias rules are coded exactly as printed — but each biased rule is gated on the issue id appearing in _SOCIAL_ISSUE_IDS or _FINANCIAL_ISSUE_IDS, and those sets contain only CSRD_ISSUES ids (tier3_labor, ai_bias, living_wage, employee_volunteering, philanthropy / semi_prices, software_competitor, currency_exchange, eu_tax). None of them appears in the shipped scoring dictionary. So on the default dictionary ALL FOUR panels return the correct quadrant for every issue and are indistinguishable from the expert panel — the expert panel's dominance is not a $750k edge, it is a tie, and the biases the chapter teaches are never observable on the default path.
EVIDENCE: backend/round2_csrd.py:469-482 `_PANEL_GROUP_BIASES` and the two id sets, with the comment "(must match IDs in CSRD_ISSUES)"; :567-591 each non-"accurate" branch is `if ... and iid in _SOCIAL_ISSUE_IDS` / `iid in _FINANCIAL_ISSUE_IDS` else `issue_recs[group] = cq`; default dictionary ids at backend/materiality_db.py:222-264.
CORRECTED CLAIM: The four panel bias rules are coded as described but fire only for issue ids in the CSRD_ISSUES teaching set; against the shipped scoring dictionary every panel — including the three biased ones — returns the correct quadrant, so all four are equally accurate.

## M-033 — CORRECTED
CLAIM AS PRINTED: ESRS assurance readiness indicator: four signals (Q1 recall >= 80%, governance not Option C, at least one Q2 issue disclosed, ambiguous issues handled) produce a 0-4 star rating. It has no valuation effect. [DEFECT: no shipped issue carries is_ambiguous, so the maximum in the default game is three stars.]
FINDING: The four signals and the 0-4 range are exact, and assurance_stars has no consumer outside the debrief payload (no valuation effect). The DEFECT is no longer true: the shipped default dictionary carries one is_ambiguous issue (biodiversity_financial_risk), so the fourth signal is earnable and four stars is attainable.
EVIDENCE: backend/router.py:4960-4971 the four signals and `assurance_stars = sum(_assurance_signals.values())`; backend/materiality_db.py:262-264 `"id": "biodiversity_financial_risk" ... "is_ambiguous": True`; router.py:4859-4862 correct placement gives credit 1.0 so `is_ambiguous and credit >= 0.5` is satisfiable; grep for assurance_stars shows consumers only at router.py:5010 and round_logic.py:3673 (debrief payloads).
CORRECTED CLAIM: The assurance readiness indicator scores four signals into 0-4 stars with no valuation effect; all four, including the ambiguous-issue signal, are earnable on the shipped default dictionary.

## M-034 — REFUTED (no such code)
CLAIM AS PRINTED: A latent branch in _mat_axis_is_high classifies BOTH axes from the same severity x likelihood product whenever numeric severity_score and likelihood_score are present. No shipped configuration populates those fields.
FINDING: That branch was removed by F-6. mat_axis_is_high now takes the numeric path only when all FOUR of impact_severity_score, impact_likelihood_score, financial_magnitude_score, financial_likelihood_score are present, and the legacy single pair is explicitly ignored. The described trap for customisers cannot be triggered by populating severity_score/likelihood_score.
EVIDENCE: backend/round2_csrd.py:512-522 (see M-030); round2_csrd.py:485-499 comment "applying one product to each axis forces every issue onto the Q1/Q4 diagonal and makes Q2 and Q3 unreachable (that defect shipped) ... Numeric scoring is therefore used ONLY when all four axis-specific fields are present."

## M-035 — CONFIRMED (with a reachability caveat)
CLAIM AS PRINTED: The Round 2 tier-3 labour issue carries screen text stating the EU due diligence directive "enters force 2025 — civil liability exposure for parent company".
FINDING: The sentence exists verbatim in the tier3_labor issue's hover_description: "EU CSDDD enters force 2025 — civil liability exposure for parent company." CAVEAT: it lives in round2_csrd.CSRD_ISSUES, which is not the dictionary the Round 2 endpoints resolve (M-045). CSRD_ISSUES is imported into router.py at line 53 but that name is not used anywhere else in router.py; only the derived Q2_DISCLOSURE_ISSUES is read (as a fallback denominator), and ELECTRONICS_SENSITIVE_ISSUES is defined and never used. So the wrong-in-two-ways sentence is in the shipped source, but I could not establish that it renders to a student on the default path.
EVIDENCE: backend/round2_csrd.py, CSRD_ISSUES["tier3_labor"]["hover_description"]: "Independent audits flagged 14-hour shifts and withheld wages at 3 tier-3 suppliers in Southeast Asia. EU CSDDD enters force 2025 — civil liability exposure for parent company. Severity: HIGH (fundamental rights). Time horizon: SHORT-MEDIUM. ESRS S2 mandatory."; backend/router.py:53 (import) and :4906 (a comment) are the only occurrences of the name in the router; round2_csrd.py:448-459 the two derived subsets.

## M-036 — CORRECTED
CLAIM AS PRINTED: Round 2 Option C consequences and the board-oversight signal are all gated on global_state["r2_governance_choice"], which is READ twice in router.py and WRITTEN nowhere. The clawback never fires, the block never fires, and the governance signal is awarded unconditionally.
FINDING: Repaired. r2_governance_choice is now WRITTEN by the Round 2 post-tick handler on every commit, and the clawback, the tier block and the governance_board signal are all computed there from the live choice.
EVIDENCE: backend/round_logic.py:3572 `gs["r2_governance_choice"] = choice`; :3641-3652 clawback; :3604-3612 tier block; :3667 `signals["governance_board"] = (choice != "option_c")  # ESRS 1 §1.51`.
CORRECTED CLAIM: r2_governance_choice is written by _post_r2_materiality at end-of-round commit, and the Option C clawback, the materiality tier block and the board-oversight assurance signal all fire from it.

## M-037 — CONFIRMED
CLAIM AS PRINTED: The 1,000-point accuracy bonus is added to global_state["bonus_score"], surfaced in admin/leaderboard views and marked facilitator-adjustable in replay.py. It does not appear in terminal_valuation.py or ending_pathways.py.
FINDING: Exact. bonus_score has no reader in either valuation module.
EVIDENCE: backend/router.py:4890-4892 `global_state["bonus_score"] = global_state.get("bonus_score", 0) + accuracy_bonus`; backend/replay.py:84 `"bonus_score",  # facilitator-adjustable at any time`; backend/admin_router.py:6130 and :6555 read it; grep for bonus_score in terminal_valuation.py and ending_pathways.py returns nothing.

## M-038 — CORRECTED
CLAIM AS PRINTED: Round 2 Option A impacts carry BOTH treasury -2,500,000 and revenue_delta -2,500,000, plus reputation +5, governance_risk -5, carbon_intensity -3, social_license +5, natural_capital_debt -3, and an Advanced Climate NCD forgiveness multiplier of 1.25.
FINDING: Every element is right EXCEPT the double charge: revenue_delta is now 0. F-7 removed it explicitly, on the reasoning that revenue_delta is applied per business unit and revenue_base persists, so a group-sized figure cost $12.5m of permanent revenue for an option priced at $2.5m. Option A now costs $2.5m of cash and nothing else.
EVIDENCE: backend/round_configs.py:152-168 `"treasury": -2_500_000, "reputation": +5, "governance_risk_delta": -5, "carbon_intensity_delta": -3, ... "revenue_delta": 0, "social_license_delta": +5, "natural_capital_debt_delta": -3` with the F-7 comment "WAS -2_500_000"; :151 `"ac_bonus": {"ncd_forgiveness_multiplier": 1.25, ...}`.
CORRECTED CLAIM: Round 2 Option A carries treasury -2,500,000, revenue_delta 0, reputation +5, governance_risk -5, carbon_intensity -3, social_license +5, natural_capital_debt -3 and an Advanced Climate NCD forgiveness multiplier of 1.25 — the revenue double charge was removed.

## M-039 — REFUTED (no such code)
CLAIM AS PRINTED: materiality_aligned has TWO independent write paths and either alone grants the +0.10; router.py sets a boolean key and pops it otherwise, while _apply_option_flags writes active_event_flags["r2_flags"]=["materiality_aligned"] when Option A was chosen.
FINDING: Both writers are gone. Round 2's option configs no longer declare any tier flag in flags_set (Option A declares full_materiality_alignment, B materiality_exceptions, C ceo_only_signoff — all marked "choice marker with no consumer"), and router.submit_materiality_matrix explicitly does not set the tier flags. _post_r2_materiality is the single writer and sets all three explicitly True/False, never popping, so a stale value cannot survive.
EVIDENCE: backend/round_configs.py:143-148 and :188-190 the F-2 comments; backend/router.py:4944-4946 "Materiality tier flags — NOT set here (F-2)"; backend/round_logic.py:3613-3616 `for f in ("materiality_aligned", "materiality_partial", "materiality_ignored"): flags[f] = (f == tier)` with the comment "Explicit False, never pop".

## M-040 — REFUTED (no such code)
CLAIM AS PRINTED: The Round 2 materiality budget is a pure treasury DEBIT with no downstream consumer; corporate_treasury -= allocated_budget; q2_disclosure_budget_unlocked is likewise stored with no consumer.
FINDING: Inverted by F-3 and superseded by M-047. There is no treasury debit for the release; the amount becomes materiality_restricted_fund, and the Q2 disclosure allocation is credited into the same fund.
EVIDENCE: backend/router.py:4925-4935 the F-3 comment "The old behaviour debited treasury by the released amount and nothing ever consumed it" and `fund_balance = float(allocated_budget + disclosure_allocated)` / `global_state["materiality_restricted_fund"] = fund_balance`.

## M-041 — REFUTED (no such code)
CLAIM AS PRINTED: _POST_TICK_MAP in round_logic.py registers post-round handlers for rounds 1, 3, 4, 5, 6, 7, 8, 9 and 10. There is no handler for round 2.
FINDING: Round 2 has a registered handler at this commit. All ten rounds are covered.
EVIDENCE: backend/round_logic.py:3685-3696 `_POST_TICK_MAP = {1: _post_r1_foundations, 2: _post_r2_materiality, 3: ..., 10: _post_r10_grand_finale}`.

## M-042 — REFUTED (no such code)
CLAIM AS PRINTED: Round 2 scores the same issue by TWO different rules; _correct_quadrant_v2 uses severity_score x likelihood_score >= 12 applied to BOTH axes, and materiality_db.DEFAULT_CONFIG populates numeric scores on all 8 issues, so the numeric branch is LIVE on the default path.
FINDING: Superseded by M-050. There is now ONE classifier: q1_target_issue_ids is derived from correct_quadrant_v2, the same function that drives full-quadrant accuracy, and the legacy single-pair numeric branch was deleted. On DEFAULT_CONFIG the two former rules cannot disagree because there is only one.
EVIDENCE: backend/router.py:4728-4737 `q1_target_issue_ids = {issue["id"] for issue in all_issues if correct_quadrant_v2(issue) == "q1"}` with the F-6 follow-up comment "capital release and full-quadrant accuracy can no longer drift apart"; backend/round2_csrd.py:512-522.

## M-043 — CORRECTED
CLAIM AS PRINTED: round_logic._apply_common_impacts applies revenue_delta to EVERY business unit in a loop and mutates revenue_base, a persistent field. Round 2 Option A carries revenue_delta -2,500,000, so against the default five-unit group it removes $12,500,000 of revenue base permanently.
FINDING: The mechanism is exactly as described and still live. The instance is not: R2 Option A's revenue_delta is now 0 (F-7), so the $12.5m permanent loss no longer occurs.
EVIDENCE: backend/round_logic.py:1646-1651 `rev_delta = impacts.get("revenue_delta", 0)` / `for bu in bus: bu["revenue_base"] = max(0, round(old_rev + rev_delta, 2))`; backend/round_configs.py:166 `"revenue_delta": 0`.
CORRECTED CLAIM: _apply_common_impacts still applies revenue_delta per business unit into the persistent revenue_base, but Round 2 Option A's revenue_delta is now 0, so the option costs $2.5m of cash and no permanent revenue.

## M-044 — CORRECTED
CLAIM AS PRINTED: Sweep of every revenue_delta across the ten rounds: 25 options carry one ... Two outliers: R2 option_a at -2,500,000 (group -12.5m) and R10 option_c Divest at -2,000,000 (group -10.0m).
FINDING: Only ONE outlier remains. R2 option_a is now 0; every other revenue_delta in round_configs.py sits in the ±$100k-$1.2m per-unit band; R10 option_c Divest at -2,000,000 is the sole exception and is explicitly allow-listed in the per-unit sanity sweep.
EVIDENCE: backend/round_configs.py revenue_delta values: +500k, -200k, 0 (R2 a), 0 (R2 b), +400k (R2 c), -800k, +300k, +100k, -500k, 0, -1,000k, -600k, +500k, +800k, -200k, +1,000k, +600k, +400k, +700k, -400k, +300k, -1,200k, +600k, +400k, +1,000k, -500k, -2,000k (R10 c); the R10 entry carries the comment at :776-778 "-2M PER UNIT = -$10M group (13.2%) ... Allow-listed in tests/test_r2_materiality_audit.py".
CORRECTED CLAIM: Across the ten rounds every revenue_delta now sits in a coherent per-unit band of $100k-$1.2m except one: R10 option_c Divest at -2,000,000 per unit (group -$10.0m), which is allow-listed pending a design ruling.

## M-045 — CONFIRMED
CLAIM AS PRINTED: The dictionary a session scores against resolves through the same path that renders the display: a per-BU/cohort override, else an industry pack, else materiality_db.DEFAULT_CONFIG (8 issues). The 20-issue CSRD_ISSUES set in round2_csrd.py is NOT a scoring dictionary.
FINDING: Exact. DEFAULT_CONFIG is 8 issues classifying 5 Q1 / 2 Q2 / 1 Q3 / 0 Q4, and both Q2 issues carry disclosure_required.
EVIDENCE: backend/router.py:4671-4683 (bu_id -> resolve_session_bu_config; else materiality_dictionary_override; else mat_db.get_current_config); backend/materiality_packs.py:186-221 resolve_session_bu_config docstring "the DISPLAY endpoint can resolve identically"; backend/materiality_db.py:219-266 DEFAULT_CONFIG (8 issues; supply_chain_labor_risk and biodiversity_financial_risk carry disclosure_required True).

## M-046 — CONFIRMED
CLAIM AS PRINTED: The default dictionary contains no Q4 issue. Industry packs vary: electronics 3/3/3/1; consumer goods 5/2/1/2; retail FMCG 1/4/1/4; oil & gas 5/2/3/0; pharma 4/5/1/0; software 4/3/3/0; technology 4/5/1/0; agriculture 4/6/0/0; banking 4/3/3/0. materiality_config_healthcare.json is empty.
FINDING: Every figure matches, computed from the shipped JSON dictionaries under correct_quadrant_v2's categorical rule.
EVIDENCE: backend/db/materiality_config.json 8 issues -> 5/2/1/0; materiality_config_electronics.json 3/3/3/1; _consumer_goods 5/2/1/2; _retail_fmcg 1/4/1/4; _oil_gas 5/2/3/0; _pharma 4/5/1/0; _software 4/3/3/0; _technology 4/5/1/0; _agriculture 4/6/0/0; _banking_financial_services 4/3/3/0; _healthcare 0 issues (78 bytes).

## M-047 — CONFIRMED
CLAIM AS PRINTED: The Round 2 release is a RING-FENCED FUND, not a treasury debit. released = $15,000,000 x (Q1 found / |Q1 targets|) becomes materiality_restricted_fund ... The $1,000,000 Q2 disclosure budget is credited into the same fund, pro rata against the ACTIVE dictionary disclosure-carrying Q2 issues. With five Q1 targets each miss withholds $3,000,000.
FINDING: Exact on every element, including the five-target arithmetic.
EVIDENCE: backend/router.py:4803-4806 release formula; :4907-4914 active-dictionary Q2 denominator; :4925-4935 the F-3 ring-fence comment and `global_state["materiality_restricted_fund"] = fund_balance`; :4934 `materiality_fund_released`; five Q1 targets on the shipped default dictionary (M-046 evidence).

## M-048 — CONFIRMED
CLAIM AS PRINTED: The governance premium is tiered: >=80% AND Option A -> materiality_aligned +0.10 M_R; >=80% AND Option B -> materiality_partial +0.05; Option C or accuracy <80% -> materiality_ignored, 0. _post_r2_materiality (registered at _POST_TICK_MAP[2]) is the sole writer; the three flags are set explicitly True/False, never popped. The 80% threshold is read from special_rules.accuracy_threshold_pct.
FINDING: Exact on every clause.
EVIDENCE: backend/round_logic.py:3598-3616 (threshold read at :3601-3602 `_rules = (get_round_config(2) or {}).get("special_rules", {})` / `_threshold = float(_rules.get("accuracy_threshold_pct", 80))`; tier ladder :3604-3612; explicit True/False :3613-3616); backend/terminal_valuation.py:198-206 (+0.10 / +0.05); _POST_TICK_MAP[2] at round_logic.py:3687; test_flag_tiering_matrix in tests/test_r2_materiality_audit.py:347-361 pins all nine combinations.

## M-049 — CONFIRMED
CLAIM AS PRINTED: Option C clawback: 40% of the RELEASED amount, taken from the restricted fund first with any shortfall charged to treasury, so it always reduces the team position. Plus governance risk +10 and reputation -5. Round 3 green bond pricing on the R2 posture: aligned -$500,000, partial -$250,000, ignored +$1,000,000.
FINDING: Exact on every clause, including the Round 3 green bond pricing table, which is gated on R3 Option B (the Green Bond option) and reads the R2 tier through _collect_all_flags.
EVIDENCE: backend/round_logic.py:3641-3652 (clawback: released x pct, restricted fund first, treasury shortfall); backend/round_configs.py:193 `"budget_clawback_pct": 0.40`; :194 option_c impacts `reputation: -5, governance_risk_delta: +10`; backend/round_logic.py:2249-2280 `if choice == "option_b":` / `if "materiality_aligned" in r2_flags: discount = 500_000` / `elif "materiality_partial" in r2_flags: discount = 250_000` / `elif "materiality_ignored" in r2_flags: premium = 1_000_000; treasury_cost += premium`.

## M-050 — CONFIRMED
CLAIM AS PRINTED: round2_csrd.correct_quadrant_v2 is the round ONE classifier, used for q1_target_issue_ids, full-quadrant scoring, Q2 disclosure and panel recommendations. mat_axis_is_high uses numeric scoring ONLY when all four of impact_severity_score, impact_likelihood_score, financial_magnitude_score, financial_likelihood_score are present; otherwise the categorical labels govern. Legacy single-pair severity_score/likelihood_score is deliberately ignored.
FINDING: Exact on every clause; the post-repair DEFAULT_CONFIG distribution of 5 q1 / 2 q2 / 1 q3 is reproduced.
EVIDENCE: backend/round2_csrd.py:512-535; backend/router.py:4735-4737 (q1 targets), :4850 (`correct_q = _correct_quadrant_v2(issue)`), :4909-4911 (Q2 disclosure), backend/round2_csrd.py:564 (panel recommendations fall back to correct_quadrant_v2).

## M-051 — CORRECTED
CLAIM AS PRINTED: Seven defects ... repaired on 31 August 2026 across twelve commits on branch fix/r2-materiality-audit, pinned by a 38-test regression suite (tests/test_r2_materiality_audit.py). Full backend suite 2087 passed; frontend jest 1099 passed. Structural cause: Round 2 was the only round of ten with no post-tick handler.
FINDING: The suite exists and the structural claim is confirmed by the code (the R2 handler docstring says so in the same terms). Two numbers do not hold at this commit: the suite has 27 test functions expanding to 40 parametrised cases (parametrize decorators of 4, 9 and 3 at lines 164, 360, 402), not 38; and no branch named fix/r2-materiality-audit exists in this clone. The "2087 passed / 1099 passed" run totals are UNVERIFIABLE without executing the suites, which this audit does not do.
EVIDENCE: backend/tests/test_r2_materiality_audit.py (27 `def test_` definitions; parametrize at :164, :360, :402); backend/round_logic.py:3541-3560 _post_r2_materiality docstring ("F-1 structural fix ... this handler is the single point in the round where BOTH inputs exist"); `git branch -a` lists no r2-materiality branch.
CORRECTED CLAIM: The Round 2 repair is pinned by tests/test_r2_materiality_audit.py — 27 test functions expanding to 40 parametrised cases — and the structural cause stands: Round 2 was the only round of ten with no post-tick handler, so four specification sources drifted with no arbiter. (Do not print the branch name or the suite-wide pass totals; neither is checkable from the repository.)

## M-052 — REFUTED (no such code)
CLAIM AS PRINTED: just_transition_passed is computed from three conditions, two of which read flags that are never written (just_transition_fund, worker_retraining). It reduces to choice in ("option_a","option_c"). Round 9 Option B, Managed Transition, FAILS the test while earning +0.12 M_R.
FINDING: The expression was rewritten (B-1). It is now `"managed_transition" in all_flags or "community_fund" in all_flags`, read through _collect_all_flags — so R9 Option B (Managed Transition) and Option C (Community Investment Fund) PASS and Option A (Immediate Closure) fails. The two mechanics now agree; the dead flags are gone. The tail claim is confirmed: just_transition_passed is worth 6 points on the social ESG dimension.
EVIDENCE: backend/round_logic.py:3431-3444 (B-1 comment and `extra["just_transition_passed"] = ("managed_transition" in all_flags or "community_fund" in all_flags)`); backend/round_configs.py R9 flags_set — option_a `["immediate_closure"]`, option_b `["managed_transition"]`, option_c `["community_fund"]`; backend/admin_shared.py:861 `"just_transition_passed": 6`.

## M-053 — CORRECTED
CLAIM AS PRINTED: ending_pathways.py ~735 awards +0.20 M_R for "Supply Chain Transparency" on scope_3_transparency OR full_remediation. scope_3_transparency is never written; the bonus is reachable only by the remediation route.
FINDING: The bonus and its two-flag condition are exact (now at ending_pathways.py:754-757). The defect is repaired: scope_3_transparency IS written — B-2 wired it to Round 3 supply-chain visibility of 80% or more (Option A's direct supplier audit). Both routes now exist.
EVIDENCE: backend/ending_pathways.py:754-757 `if "scope_3_transparency" in all_flags or "full_remediation" in all_flags: mr_delta += 0.20`; backend/round_logic.py:2352-2358 the B-2 comment and `if scope3_completeness >= 80: gs.setdefault("active_event_flags", {})["scope_3_transparency"] = True`; full_remediation still set at ending_pathways.py:480.
CORRECTED CLAIM: The +0.20 "Supply Chain Transparency" premium is awarded on scope_3_transparency OR full_remediation, and both are now writable — scope_3_transparency by Round 3 supply-chain data completeness of 80% or more.

## M-054 — CORRECTED
CLAIM AS PRINTED: admin_router.py ~9925 reads retraining_succeeded for a facilitator display; nothing writes it. Its sibling nbs_succeeded IS written at impact_engine.py ~167.
FINDING: Repaired. retraining_succeeded is now written alongside nbs_succeeded in the same module, and the code comment records the fix in the claim's own terms.
EVIDENCE: backend/impact_engine.py:381-384 "the facilitator dashboard (admin_router) reads retraining_succeeded exactly as it reads nbs_succeeded, but only the NBS half ..." / `gs.setdefault("active_event_flags", {})["retraining_succeeded"] = retrain_succeeded`; nbs_succeeded at impact_engine.py:198; readers at admin_router.py:10238 and :10253.

## M-055 — REFUTED (no such code)
CLAIM AS PRINTED: Four of fourteen special_rules keys are never read outside their own definition: electronics_blindspot_doubles_crisis, low_social_license_strike_trigger, regulatory_friction_enabled, stochastic_event.
FINDING: All four now have live readers. The treatment the note said had not been applied elsewhere has been applied to exactly these keys.
EVIDENCE: electronics_blindspot_doubles_crisis read at backend/round_logic.py:227-228; low_social_license_strike_trigger at backend/impact_engine.py:302 `_strike_on = bool(_r9_rules.get("low_social_license_strike_trigger", True))`; regulatory_friction_enabled at impact_engine.py:301; stochastic_event at impact_engine.py:113 `stochastic_enabled = bool(special.get("stochastic_event", True))`.

## M-056 — CORRECTED
CLAIM AS PRINTED: ai_monetised is declared in Round 6 option_a flags_set AND written as a direct boolean at round_logic.py ~1843, both under the same condition. [Extend the dual-form guard rather than fixing the instance.]
FINDING: The boolean write no longer exists in round_logic.py — ai_monetised is now declared only in flags_set (legacy R6 option_a and the R6 operations pillar), and its live consumer reads it through _collect_all_flags. The recommended remedy was also actioned: a generalised dual-form guard now exists as a test, with ai_monetised and supply_chain_fragile as its two allow-list entries; the latter is a NEW instance with DISAGREEING writers.
EVIDENCE: grep for ai_monetised across backend/*.py finds declarations at round_configs.py (R6 option_a flags_set) and pillar_configs.py:801, a read at round_logic.py:2196 `if "ai_monetised" not in all_flags`, and no boolean write; backend/tests/test_engine_invariants.py:330-343 DUAL_FORM_ALLOWLIST and :346-360 test_no_flag_is_both_config_declared_and_boolean_written.
CORRECTED CLAIM: ai_monetised is declared only in Round 6 Option A's flags_set and read through _collect_all_flags; a generalised dual-form guard now exists as a regression test, whose allow-list records one remaining risky case — supply_chain_fragile, written by two writers under DIFFERENT conditions in the supply-chain side track.

## M-057 — CORRECTED
CLAIM AS PRINTED: Audit B clean results: (a) money scaling ... no new outliers beyond the three allow-listed; (b) 168 state keys written, none never read; (c) Shadow Board flags planet_expendable, shareholder_alienated and governance_fragility are all live, written via the data-driven REJECTION_FLAGS path.
FINDING: (c) CONFIRMED exactly — all three are written as top-level booleans through REJECTION_FLAGS. (a) the R10 Divest 13.2% allow-list entry is present in the config comment. (b) is NOT true as printed at this commit: at least two keys are written and read by nothing, both deliberately allow-listed — divest_all and carbon_price_noise_pct.
EVIDENCE: backend/shadow_board_audit.py:121-160 REJECTION_FLAGS with flag_name shareholder_alienated / planet_expendable / governance_fragility, written at :252 `flags[flag_info["flag_name"]] = True`; backend/round_configs.py:776-778 the 13.2% allow-list comment; backend/tests/test_engine_invariants.py:32-38 `ALLOWLISTED_UNAPPLIED = {... "divest_all": "pending design ruling — deliberately unconsumed"}` and :447-448 `ALLOWLISTED_UNCONSUMED_NOISE_FIELDS = {"carbon_price_noise_pct": ...}`.
CORRECTED CLAIM: The Shadow Board flags planet_expendable, shareholder_alienated and governance_fragility are all live top-level booleans written by the data-driven REJECTION_FLAGS path; the "no state key is written and never read" result now carries two deliberate exceptions, divest_all and carbon_price_noise_pct, both allow-listed by regression test.

## M-058 — REFUTED (no such code)
CLAIM AS PRINTED: social_license_delta from round option impacts is NEVER APPLIED in legacy_abc mode for Rounds 1, 2, 3, 7 and 10. _apply_common_impacts generically applies only carbon_intensity_delta, contagion_spike, governance_risk_delta, reputation and revenue_delta.
FINDING: Repaired by C-1. _apply_common_impacts now applies social_license_delta generically for EVERY round, guarded by social_license_applied_rN so a handler that applies it itself is not double-counted; the identical R1/R2/R3/R7/R10 set is named in the fix comment as the rounds that were dead.
EVIDENCE: backend/round_logic.py:1670-1688 the C-1 comment ("R1, R2, R3, R7 and R10 promised social_license_delta in config and never applied it") and `sl_delta = impacts.get("social_license_delta", impacts.get("social_license", 0))` / `for bu in bus: bu["social_license_score"] = ...` / `extra[f"social_license_applied_r{round_number}"] = sl_delta`.

## M-059 — REFUTED (no such code)
CLAIM AS PRINTED: natural_capital_debt_delta is never applied for Rounds 2, 4 and 10. Applied only by the R3, R5, R7 and R8 handlers.
FINDING: Repaired by C-2, in the same pass and the same shape as M-058. _apply_common_impacts now applies natural_capital_debt_delta generically with a natural_capital_debt_applied_rN guard.
EVIDENCE: backend/round_logic.py:1690-1699 the C-2 comment ("R2, R4 and R10 configured it with no applier anywhere") and `ncd_delta = impacts.get("natural_capital_debt_delta", 0)` / `bu["natural_capital_debt"] = max(0.0, round(... + ncd_delta, 2))`. NOTE for the chapter: the row's NOTE chain "NCD raises cost of debt at 1bp/unit -> WACC -> exit multiple" is not in the code — see M-001; NCD has no term in calc_esg_adjusted_wacc.

## M-060 — REFUTED (no such code)
CLAIM AS PRINTED: The R4 social-media velocity amplifier computes velocity_multiplier = 1.0 + 0.1 x (round_number - 3), but _post_r4_contagion is registered only at _POST_TICK_MAP[4], so the multiplier is always 1.10; the escalation is unreachable. Also contains a redundant expression.
FINDING: Repaired by C-3. The amplifier was lifted out of the R4 handler into its own function called from post_tick for every round, so it escalates as designed (1.1x at R4 to 1.7x at R10). round_number is now a parameter, so the redundant expression is gone. It amplifies only while group reputation is below 60.
EVIDENCE: backend/round_logic.py:2153-2168 the C-3 comment ("this used to live inside _post_r4_contagion, where round_number was always 4") / `velocity_multiplier = round(1.0 + 0.1 * (round_number - 3), 2)` / `if current_rep < 60:`; called unconditionally at round_logic.py:676 `_apply_social_media_velocity(round_number, global_state, extra_events)`.

## M-061 — CORRECTED
CLAIM AS PRINTED: Impact-key naming is split: social_license_delta vs social_license; reputation vs reputation_delta. Only four of the twenty-five impact keys are applied generically by _apply_common_impacts; the rest are per-handler.
FINDING: The split spellings still exist, but C-4 made them survivable: the canonical key is read first and the alias honoured as a fallback in the same expression. And SIX keys, not four, are now applied generically — carbon_intensity_delta, revenue_delta, governance_risk_delta, reputation (alias reputation_delta), social_license_delta (alias social_license) and natural_capital_debt_delta.
EVIDENCE: backend/round_logic.py:1636-1699; the alias reads at :1666 `impacts.get("reputation", impacts.get("reputation_delta", 0))` and :1683 `impacts.get("social_license_delta", impacts.get("social_license", 0))`, each with the C-4 comment "canonical ... alias is honoured for ONE release".
CORRECTED CLAIM: Impact-key spellings are still split (social_license_delta / social_license, reputation / reputation_delta), but each canonical key is now read with its alias as a fallback, and six keys — carbon intensity, revenue, governance risk, reputation, social licence and natural capital debt — are applied generically by _apply_common_impacts.

## M-062 — CORRECTED
CLAIM AS PRINTED: Verified clean: reputation IS applied for every round; Round 5 carries no social_license_delta in config; Pillar mode applies SLO via router.py ~2497, so M-058 is legacy-mode only.
FINDING: All three sub-claims still hold in substance, but the last is out of date twice over: the pillar-mode SLO applier is at router.py:8069-8073 (revenue-weighted and scaled by pillar effectiveness), and the legacy gap M-058 describes has since been closed generically, so there is no longer a legacy-only exposure to scope.
EVIDENCE: backend/round_logic.py:1666-1671 (reputation applied generically with a per-round guard); no social_license_delta appears in the Round 5 option configs (round_configs.py R5 block); backend/router.py:8069-8073 `sl_delta = round(agg_impacts.get("social_license_delta", 0) * effectiveness, 2)` / `bu["social_license_score"] = max(0, min(100, round(bu["social_license_score"] + proportional_sl, 2)))`.
CORRECTED CLAIM: Reputation is applied every round; Round 5 carries no social_license_delta; pillar mode applies social licence at router.py:8069-8073, revenue-weighted and scaled by pillar effectiveness — and the legacy-mode social-licence gap is itself now closed (M-058).

## M-063 — CORRECTED
CLAIM AS PRINTED: Round 2 is the only round whose option treasury is never charged ... R2 option_a treasury is -2,500,000. OPTION A IS FREE.
FINDING: Repaired by C-5. The Round 2 post-tick handler now charges the chosen option's impacts["treasury"], in legacy mode, before the Option C clawback, and stamps option_treasury_applied_r2. Option A is no longer free.
EVIDENCE: backend/round_logic.py:3574-3594 the C-5 comment ("Every other round charges its chosen option's impacts['treasury']; R2 never did") and `_r2_treasury = ((_r2_opts.get(choice) or {}).get("impacts") or {}).get("treasury", 0)` / `_apply_treasury_with_green_fund(...)` / `extra["option_treasury_applied_r2"] = _r2_treasury`; round_configs.py:161 `"treasury": -2_500_000`.
CORRECTED CLAIM: Every round including Round 2 now charges its chosen option's treasury impact; _post_r2_materiality applies R2 Option A's -$2,500,000 in legacy mode, before the Option C clawback.

## M-064 — CONFIRMED
CLAIM AS PRINTED: Round 10 Option C (Divest) sets impacts["divest_all"]=True and nothing outside that config ever reads it. Siblings spinoff_weakest_bu and synergy_wipe are handled.
FINDING: Exact in substance; line numbers have moved (config at round_configs.py:773, siblings handled at round_logic.py:2764 and :2777). The inertness is now a recorded design ruling with an allow-list entry, not an oversight. IMPORTANT for the chapter: the NOTE's "THREE of Round 10 Option C's five modelled consequences do nothing" is NO LONGER TRUE — the -12 social licence (M-058) and the +8 NCD (M-059) are both applied now, so divest_all is the only inert one.
EVIDENCE: backend/round_configs.py:767-773 the C-6 comment "divest_all has NO consumer — by design ruling it stays declared but inert until its mechanics are specified (allow-listed in tests/test_engine_invariants.py)"; backend/round_logic.py:2764 `if impacts.get("spinoff_weakest_bu"):`, :2777 `if impacts.get("synergy_wipe"):`; backend/tests/test_engine_invariants.py:38.

## M-065 — CORRECTED
CLAIM AS PRINTED: Of 20 distinct impact keys ... Only four keys have unapplied rounds: social_license_delta [1,2,3,7,10], natural_capital_debt_delta [2,4,10], treasury [2], divest_all [10].
FINDING: Three of the four have been repaired since (C-1, C-2, C-5). Only divest_all [10] remains unapplied, and it is a recorded design ruling.
EVIDENCE: see M-058 (round_logic.py:1670-1688), M-059 (:1690-1699), M-063 (:3574-3594) and M-064 (round_configs.py:767-773).
CORRECTED CLAIM: Of the impact keys used across the ten rounds, exactly one now has an unapplied round: divest_all in R10, deliberately inert by design ruling. social_license_delta, natural_capital_debt_delta and treasury are all applied in every round that declares them.

## M-066 — CORRECTED
CLAIM AS PRINTED: Social licence is an explicit per-BU stock bounded 0-100. Writers: round option impacts (guarded social_license_applied_rN); pillar aggregates; greenwash scandal -15/BU full or -7.5 moderate RECURRING; natural decay/growth (investment ratio <15% -> -4%/round, 15-30% flat, >=30% -> +3/round); black swans; triggered agent events (strike -20, expose -12, divestment -10); F2 continuous NPC pressure.
FINDING: The stock, its bounds and the first three writer families are exact. Two errors. (1) The decay ladder omits the middle tier: >=30% (or total CapEx >= $3m) grows +3 to +10, >=20% grows +1, >=15% or a minimum absolute spend is flat, below that is 4% decay — so there IS an unconditional inflow below 15% is still false, but the growth bar is 20%, not 30%. (2) The three triggered-agent figures are mis-assigned: the coordinated strike is social_license_delta -12 (not -20), the -20 belongs to the community activist's blockade, the journalist's exposé is -10 social licence and -20 reputation, and the institutional divestment carries NO social licence term at all (treasury -8%, reputation -15, cost of capital +0.02).
EVIDENCE: backend/engine.py:826-848 apply_natural_decay (four tiers); config.py:600-601, 641-643, 668 (growth_abs_capex 3,000,000; mid_growth 1.0; ratios 0.15 / 0.20 / 0.30; min_abs_capex 100,000); backend/autonomous_agents.py triggered_event effects blocks — regulator (treasury -4%, rep -12, gov -8, opex +6%), gen-Z strike (burnout +20, opex +15%, rep -8, SLO -12), institutional investor (treasury -8%, rep -15, cost of capital +0.02), community activist (SLO -20, rep -10, opex +10%, treasury -$3,000,000), journalist (rep -20, treasury -3%, SLO -10, gov +10).
CORRECTED CLAIM: Social licence is a per-BU stock bounded 0-100, written by round option impacts (guarded social_license_applied_rN), pillar aggregates, the greenwash scandal (-15/BU full, -7.5 moderate, recurring), natural decay/growth (>=30% of the pool or >=$3m total CapEx grows +3 to +10, >=20% grows +1, >=15% or a minimum absolute spend is flat, below that decays 4%/round), black swans, triggered agent events (community blockade -20, gen-Z strike -12, journalist exposé -10; institutional divestment costs treasury and reputation, not licence) and F2 continuous NPC pressure.

## M-067 — CORRECTED
CLAIM AS PRINTED: Five autonomous agents ... default ON. Tolerance stock starts 65-80, decays 8-15 per violation round x severity, recovers only 2-3 per clean round (1.5x after two consecutive). Stages dormant -> watching -> agitated -> hostile -> triggered. TRIGGERED IS PERMANENT and fires one-shot: shutdown order fine 4% of revenue; coordinated strike SLO -20; expose -12; divestment -10.
FINDING: Five agents, the named roster, the 65-80 opening tolerance, the five stages, the absorbing triggered state and the 1.5x recovery bonus after two consecutive clean rounds are all exact, and the engine is on by default. Three rate/consequence errors: base decay is 6-10 per violation round (not 8-15) before the (1 + severity), interference and shadow-board multipliers; base recovery is 2-5 per clean round (not 2-3); and the four one-shot figures are mis-assigned exactly as in M-066 — the regulator's fine is 4% of TREASURY (the narrative text says revenue; the effect key is treasury_pct_hit -0.04), the strike is SLO -12, the exposé is reputation -20 / SLO -10, and the divestment is treasury -8% / reputation -15.
EVIDENCE: backend/autonomous_agents.py:41-42, 88-89, 136-137, 184-185, 232-233 (patience_decay_rate 8/10/6/7/9; recovery_rate 3/5/2/4/4); :40, 87, 135, 183, 231 initial_tolerance 75/70/80/65/72; :559-566 `base_decay = profile["patience_decay_rate"] * (1 + severity)` x interference x shadow-board; :578-586 `recovery *= 1.5` when recovery_counter >= 2; :530-531 and :344-346 `triggered_round is not None` guards (absorbing); :700-702 `gs.get("corporate_treasury", 0) * abs(effects["treasury_pct_hit"])`; effects blocks as listed in M-066; gate at backend/round_logic.py:1206 `if _toggles.get("npc_stakeholders_enabled", True)` with the default True at pedagogical_engine.py:696.
CORRECTED CLAIM: Five autonomous agents, default ON, open with a tolerance stock of 65-80, lose 6-10 per violation round before severity, interference and shadow-board multipliers, and recover 2-5 per clean round (1.5x after two consecutive). Stages run dormant to triggered, triggered is permanent, and the one-shot consequences are: regulatory shutdown 4% of treasury plus -12 reputation; gen-Z strike -12 social licence, +20 burnout, +15% OPEX; community blockade -20 social licence and -$3m; journalist exposé -20 reputation and -10 social licence; institutional divestment -8% of treasury, -15 reputation and +2pp cost of capital.

## M-068 — CORRECTED
CLAIM AS PRINTED: Four named NPCs carry Mitchell/Agle/Wood salience profiles and four tiers; hostile+ drains -5 reputation/round (-3 legal), regulator enforcement draws a seeded $5-25M fine. With stakeholder_memory_enabled (F1, default ON) satisfaction integrates into a trust stock with gain_rate < loss_rate, and betrayal flags (deny-and-deflect, greenwashing, materiality_ignored) subtract a scar AND cap recovery. Staging limiter: a tier may worsen by at most one level per round; de-escalation is never rate-limited.
FINDING: Four named NPCs (activist_investor, regulator, community_leader, journalist) with Mitchell power/legitimacy/urgency profiles, the -5 / -3 reputation drain, F1 default ON, gain_rate 0.25 < loss_rate 0.55, the betrayal scar with a recovery ceiling, and the staging limiter (worsen at most one tier per round, de-escalation unlimited) are all exact. Two corrections. (1) The regulator's fine is no longer the raw $5-25M draw: FIN-09 caps it at the lesser of the draw, the difficulty tier's npc_max_fine ($6M/$12M/$25M) and 4% of trailing annual revenue. (2) Of the three named betrayal flags only the greenwashing family can actually fire: detect_betrayal scans this tick's events for keys whose value is True (plus an events["flags_set"] list that nothing in the core tick writes), and greenwashing_scandal / greenwashing_detected ARE written that way — but deny_and_deflect exists only as a list element inside rN_flags, and materiality_ignored is written into active_event_flags, not into the tick's events, so neither reaches the scar.
EVIDENCE: backend/npc_stakeholders.py:40-46 _BETRAYAL_FLAGS; :50-56 `active = {k for k, v in events.items() if v is True}` / `active |= {str(x) for x in (events.get("flags_set") or [])}`; deny_and_deflect written only at backend/round_configs.py:312 and pillar_configs.py:515 (flags_set lists); materiality_ignored written at round_logic.py:3613-3616 into gs["active_event_flags"]; greenwashing_scandal / greenwashing_detected written at engine.py:4261 and :4275 into ctx.events; npc_stakeholders.py:703 `rep_hit = -5 if action_result["action"] in ("hostile", "adversarial") else -3`; :710-725 the FIN-09 fine cap; :541-553 the one-tier-per-round limiter; config.py:432-433 TRUST_GAIN_RATE 0.25 / TRUST_LOSS_RATE 0.55.
CORRECTED CLAIM: Four named NPCs carry Mitchell salience profiles; hostile+ drains -5 reputation per round (-3 legal); regulator enforcement draws a seeded $5-25M fine capped at the lesser of the tier's fine ceiling and 4% of trailing annual revenue. With F1 on, satisfaction integrates into a trust stock that rises at 0.25 and falls at 0.55, and a greenwashing betrayal this round subtracts a scar and caps recovery — but deny_and_deflect (a list-held option flag) and materiality_ignored (written to the flag bag, not to the tick's events) cannot reach the betrayal detector. A tier may worsen by at most one level per round; de-escalation is never rate-limited.

## M-069 — CORRECTED
CLAIM AS PRINTED: Negotiation Rooms: $250,000 entry fee charged win or lose; max 2 meetings per round; 6 dialogue turns; server-validated concession whitelist — remediation fund $2.0m/+12 tolerance, governance audit $1.5m/+10, wellbeing $1.0m/+10, transparency pact $0.5m/+8, public apology $0/+4 and -2 reputation. Repeat price ladder (1.0, 1.5, 2.0) per agent; live broken-promise scar adds 25%. DE-ESCALATION IS CAPPED AT THE AGENT WATCHING THRESHOLD.
FINDING: Every price, rate and cap is exact. One omission: the whitelist has SIX entries, not five — the claim leaves out dividend_signal (Dividend Commitment Signal, $500,000 / +8 tolerance, the institutional investor).
EVIDENCE: backend/negotiation.py:35-40 `MEETING_FEE = 250_000`, `MAX_MEETINGS_PER_ROUND = 2`, `MAX_TURNS = 6`, `REPEAT_PRICE_LADDER = (1.0, 1.5, 2.0)`, `SCAR_SURCHARGE = 0.25`; :47-91 CONCESSION_CATALOG (six entries, costs and tolerance values as listed); :313 `cap = profile["escalation_thresholds"]["watching"]`.
CORRECTED CLAIM: ... the whitelist has six concessions: remediation fund $2.0m/+12, governance audit $1.5m/+10, wellbeing $1.0m/+10, transparency pact $0.5m/+8, dividend commitment signal $0.5m/+8, and public apology $0/+4 with -2 reputation.

## M-070 — CONFIRMED
CLAIM AS PRINTED: F5 promise ledger (stakeholder_engagement.py, default ON): one engagement action per round — town hall (goodwill, NO promise), public pledge, or private commitment. The latter two register on the ledger and are judged at maturity: kept pays trust, broken triggers the F1 betrayal scar plus a reputation penalty. Negotiation deals register on the same ledger.
FINDING: Exact on every clause.
EVIDENCE: backend/stakeholder_engagement.py:28-30 `"town_hall": {"creates_promise": False}, "public_pledge": {"creates_promise": True}, "private_commitment": {"creates_promise": True}`; :7-8 "kept ones pay a trust / SLO / reputation dividend; broken ones fire the F1 betrayal scar and a reputation ding"; :55-57 scar constants shared with F1; backend/negotiation.py:13 "resolve_agent_promises judges (tagged source='negotiation')"; toggle default at pedagogical_engine.py:726 `"stakeholder_engagement_enabled": True`; router.py:3166 passes "the round's optional engagement action" (singular).

## M-071 — CORRECTED
CLAIM AS PRINTED: Round 1 stakeholder map: >=80% placement accuracy earns a reputation bonus and gates the R2 materiality path; <60% takes a treasury penalty. Ten stakeholders acquire persistent attitude scores updated by a flag->delta rule table; salience can migrate quadrants on round events. Round 9 strike: below avg SLO 50 base probability 50%, burnout adds min(0.20, (avg_burnout-50)/100*0.40), cap 95%; a strike zeroes ALL BU revenue with a minimum penalty of max($1M, 5% of treasury).
FINDING: The R9 strike arithmetic is exact, including the Ch 8 worked example (burnout 58 -> +3.2pp -> 53.2%), and the ten-stakeholder attitude table is real and now persists. Three corrections on the R1 half. (1) There is NO reputation bonus at >=80% — there is a reputation PENALTY of -3 below 80%; what >=80% earns is leaderboard points (1,000 at 80%, 2,000 at 90%, 3,000 at 100%). (2) The R1 result does not gate the R2 materiality path: correct "manage closely" placements only add issue ids to stakeholder_boosted_issues, which the code describes as a frontend confirmation badge. (3) The R9 strike fires only when the round's option carries strike_risk (R9 Option A, Immediate Closure) or the pillar flag immediate_closure; and it charges treasury the greater of the floor and total group revenue rather than zeroing revenue_base.
EVIDENCE: backend/stakeholder_map.py:511-513 `passed = accuracy >= 0.80` / `reputation_penalty = FAILURE_REPUTATION_PENALTY if not passed else 0` / `treasury_penalty = POOR_ANALYSIS_TREASURY_PENALTY if accuracy < 0.60 else 0`; :566-572 SCORING_TIERS (1.00/3000, 0.90/2000, 0.80/1000), FAILURE_REPUTATION_PENALTY -3, POOR_ANALYSIS_TREASURY_PENALTY -500,000; STAKEHOLDERS list length 10; backend/router.py:4703-4726 the stakeholder_boost_map with the comment "so the frontend can show a confirmation badge"; backend/stakeholder_sentiment.py:23-27 FLAG_SENTIMENT_RULES; backend/impact_engine.py:290-295 (strike_risk gate), :321-341 (0.50 base, burnout boost, 0.95 cap), :345-356 (`MINIMUM_STRIKE_PENALTY = max(1_000_000, treasury * 0.05)` / `revenue_lost = max(MINIMUM_STRIKE_PENALTY, sum(revenue_base))`).
CORRECTED CLAIM: The Round 1 stakeholder map pays leaderboard points at >=80% accuracy (1,000 / 2,000 / 3,000) and takes -3 reputation below 80% and -$500,000 below 60%; its only carry into Round 2 is a display badge on linked issues. Ten stakeholders hold persistent attitude scores updated by a flag-to-delta table. The Round 9 strike fires only under Immediate Closure: below average social licence 50 the base probability is 50%, burnout above 50 adds min(0.20, (avg_burnout-50)/100*0.40) up to a 95% cap, and a strike charges treasury the greater of total group revenue and max($1M, 5% of treasury).

## M-072 — CORRECTED
CLAIM AS PRINTED: Five stakeholder toggles are default ON in DEFAULT_PEDAGOGICAL_TOGGLES as deployed: F1, F2, F5, F3, F4. F6 is opt-in. Negotiation rooms default ON at platform level, per-facilitator capability default-granted and explicitly revocable.
FINDING: FOUR are ON, not five. stakeholder_slo_feedback_enabled (F2) ships False — reversed by F-11 on 2 September 2026 (see M-083). F1, F5, F3, F4 are True and F6 is False. The negotiation clauses hold, with one internal inconsistency worth knowing: the platform default and the capability check both default to granted, but one facilitator-creation path stores `req.negotiation_rooms_enabled is True` under a comment reading "opt-in, default OFF".
EVIDENCE: backend/pedagogical_engine.py:719-729 (memory True, slo_feedback False, engagement True, coalitions True, uncertainty True, intel_ui False); admin_router.py:1449-1454 the same six with F2 described as "OFF by default (F-11 ...)"; admin_shared.py:298 `"negotiation_rooms_enabled": True`; admin_shared.py:901-907 facilitator_negotiation_granted "DEFAULT-GRANTED, explicitly revocable"; admin_router.py:2102 the conflicting comment.
CORRECTED CLAIM: Four stakeholder toggles ship ON (F1 memory, F3 coalitions, F4 uncertain thresholds, F5 promises) and two ship OFF (F2 licence feedback, F6 intel rail); negotiation rooms are on at platform level with a default-granted, revocable per-facilitator capability, and per-cohort pedagogical_overrides can still disable any of them.

## M-073 — CORRECTED
CLAIM AS PRINTED: apply_natural_decay gains a middle growth tier (investment ratio >=20% -> +1/round) and an absolute-capex escape into the full growth tier at NATURAL_DECAY_GROWTH_ABS_CAPEX = $3,000,000. The greenwash bar is now max(relative ratio, GREENWASH_ABS_CAPEX_FLOOR = $3,000,000 average per BU).
FINDING: Both mechanisms are exactly as described and config-backed. One error: the greenwash absolute floor is measured on TOTAL group CapEx, not an average per BU — greenwash_backing sums capex_allocated across the decisions and the check is `total_capex >= GREENWASH_ABS_CAPEX_FLOOR`.
EVIDENCE: backend/engine.py:827-839 (absolute escape and the +1.0 middle tier); config.py:600-601 growth_abs_capex 3,000,000 / mid_growth 1.0; config.py:642 mid_ratio 0.20; backend/engine.py:1183-1200 greenwash_backing "the TEAM'S share of the CSF pool ... and the team's total CapEx"; :1236 `if total_capex >= GREENWASH_ABS_CAPEX_FLOOR: return False, 0.0`.
CORRECTED CLAIM: apply_natural_decay gains a middle growth tier (ratio >=20% -> +1/round) and an absolute-capex escape into the full growth tier at $3,000,000; the greenwash bar is max(relative pool share, $3,000,000 of TOTAL group CapEx).

## M-074 — CONFIRMED
CLAIM AS PRINTED: The sentiment heat-map / NPC bridge runs at NPC_SENTIMENT_BRIDGE_BASELINE = 0.15 even with trust memory off, so the two surfaces can never fully diverge. A real bug was fixed in the same pass: the working sentiment list was read from a top-level key nothing persisted, so attitude scores silently re-initialised every round and the bridge could never fire.
FINDING: Both halves exact, and the code records the defect in the same terms.
EVIDENCE: backend/config.py:695 `NPC_SENTIMENT_BRIDGE_BASELINE = float(_trust.get("sentiment_bridge_baseline", 0.15))`; backend/npc_stakeholders.py:159-162 `_bridge_weight_baseline()` "Low always-on bridge weight used when F1 memory is off (EVAL rec 5)"; backend/engine.py:4765-4772 "the working list was only ever read from a TOP-LEVEL key that nothing persists, so attitudes silently re-initialised every round and the F1 bridge could never fire in production" with the round-trip read through active_event_flags.

## M-075 — CONFIRMED
CLAIM AS PRINTED: Staged escalation is live: a named NPC tier may worsen by at most one level per round (determine_npc_action); a standing start counts as cooperative, so Round 1 caps at one step past tier 0. De-escalation is never rate-limited. The 12 sm_ side-track outcome flags now grant one-shot trust/tolerance credits or debits via SM_TRACK_CREDITS.
FINDING: Exact, including the count of twelve sm_ flags.
EVIDENCE: backend/npc_stakeholders.py:541-553 "A relationship may WORSEN by at most one tier per round ... a standing start (no prior tier) counts as cooperative — so Round 1 can reach at most one step past tier 0 ... De-escalation" / `_cap = (0 if _prev_tier is None else _prev_tier) + 1`; :761-800 SM_TRACK_CREDITS with exactly twelve sm_ keys (sm_esg_gold_standard, sm_transparency_champion, sm_community_partnership, sm_investor_focus, sm_issb_aligned, sm_voluntary_commitments, sm_structured_response, sm_gap_closure, sm_rating_challenge, sm_defensive_crisis, sm_media_hostile, sm_legal_escalation) and :791 "One-shot application".

## M-076 — CORRECTED
CLAIM AS PRINTED: The engine carries seven independent facilitator switches set before Round 1 (trust memory, licence feedback, coalitions, uncertain thresholds, promise ledger, negotiation rooms, intel rail). Six ship ON, one OFF. They describe 2^7 = 128 distinct configurations.
FINDING: Seven switches and 128 configurations are right. The split is now FIVE on and TWO off: F2 licence feedback was reversed to OFF by F-11 (M-083), joining F6 the intel rail.
EVIDENCE: backend/pedagogical_engine.py:719-729; backend/admin_shared.py:298 and :901-907 (negotiation rooms).
CORRECTED CLAIM: The engine carries seven independent facilitator switches set before Round 1; five ship ON (trust memory, coalitions, uncertain thresholds, promise ledger, negotiation rooms) and two ship OFF (licence feedback, intel rail). They describe 2^7 = 128 distinct configurations, and leaderboards are comparable only within one.

## M-077 — CORRECTED
CLAIM AS PRINTED: There are THREE carbon prices in the engine: economic carbon fee (base $40, escalating 15% PER ROUND); shadow carbon price $250/tonne; pathway overrides $250 standard / $350 Regulatory Shutdown / $750 Climate.
FINDING: The code FALLBACKS are $40 and 15%, but the shipped config overrides both: simulation_config.json sets carbon_price_base 50 and carbon_price_growth_rate 0.05. The escalation is per round, as claimed. The shadow price and pathway overrides are exact. And there are FOUR prices, not three — CBAM at $100/tonne (M-087).
EVIDENCE: backend/config.py:184-185 `ECONOMIC_CARBON_PRICE_BASE = float(_economic_params.get("carbon_price_base", 40.0))` / `..._GROWTH = float(_economic_params.get("carbon_price_growth_rate", 0.15))`; simulation_config.json `"carbon_price_base": 50, "carbon_price_growth_rate": 0.05`; backend/engine.py:3933 `base_fee * (1 + ECONOMIC_CARBON_PRICE_GROWTH) ** (round_number - 1)`; config.py:195 shadow 250.0; ending_pathways.py:169/263/360/458; config.py:506-508 CBAM_SURCHARGE_RATE 100.
CORRECTED CLAIM: There are FOUR carbon prices in the engine: the economic carbon fee (shipped config $50, escalating 5% PER ROUND — the code fallbacks of $40 and 15% are overridden); the shadow carbon price $250/tonne used for the terminal carbon charge; the pathway overrides $250 standard / $350 Regulatory Shutdown / $750 Climate Black Swan; and the CBAM border levy at $100/tonne.

## M-078 — CONFIRMED
CLAIM AS PRINTED: Terminal carbon cost = group tCO2e x shadow price ($250/t). For the default four-unit configuration (pharma, electronics, consumer_goods, software) at opening intensities that is 2,424 tCO2e = approx $0.61m, about 3% of a $20m terminal EBITDA; a 31% intensity cut is worth approx $0.19m.
FINDING: Reproduced exactly from the shipped BU profiles: 18.0m x 35 + 16.5m x 72 + 10.5m x 48 + 8.5m x 12, all over 1e6, gives 630 + 1,188 + 504 + 102 = 2,424 tCO2e; at $250 that is $606,000; 3.0% of $20m; a 31% cut is $187,860.
EVIDENCE: backend/bu_profiles.py BU_PROFILES — pharma rev 18,000,000 CI 35; electronics 16,500,000 CI 72; consumer_goods 10,500,000 CI 48; software 8,500,000 CI 12; backend/terminal_valuation.py:516-517 `tco2e = round(sum(bu.get("carbon_intensity", 0) * bu["revenue_base"] / 1e6 for bu in bus), 1)` / `cc = round(tco2e * carbon_tax_per_ton, 2)`; config.py:195 shadow price 250.0.

## M-079 — REFUTED (no such code)
CLAIM AS PRINTED: Share count remains 100,000,000 (TV_SHARES_OUTSTANDING). At a $50.00 opening reference this implies approx $5bn equity value against $17.0m opening EBITDA, about 294x. UNCHANGED since first reported.
FINDING: TV_SHARES_OUTSTANDING is 6,500,000, in both the code fallback and both shipped config copies. The $50.00 reference is right and the $17.0m opening EBITDA is right (the four-unit gross profit is 53.5m - 36.5m), but the implied opening equity is $325m, about 19x EBITDA, not $5bn / 294x. The "100 million shares" text survives only as a stale comment above the constant.
EVIDENCE: backend/config.py:828 `TV_SHARES_OUTSTANDING: int = int(_tv.get("shares_outstanding", 6_500_000))`; simulation_config.json and db/simulation_config.json both `"shares_outstanding": 6500000`; backend/terminal_valuation.py:33 `SHARES_OUTSTANDING: int = TV_SHARES_OUTSTANDING   # 100 million shares (IPO anchor)` — comment only; :398 docstring "Fixed at 100M for this simulation" — comment only; :410 `raw_price_per_share = round(equity_value / max(1, shares_outstanding), 4)`.

## M-080 — REFUTED (no such code)
CLAIM AS PRINTED: just_transition_passed is TRUE for Round 9 option_a (Immediate Closure) and option_c (Community Fund) and FALSE for option_b (Managed Transition), because both named flags in the expression are dead reads. Two mechanics, opposite views. BLOCKS Chapter 9.
FINDING: The expression was replaced (B-1). It is now true for Option B (managed_transition) and Option C (community_fund) and FALSE for Option A (Immediate Closure), which is the view the M_R bonus already took. The two mechanics agree and the block on Chapter 9 is lifted.
EVIDENCE: backend/round_logic.py:3431-3444 (see M-052 for the full quotation); terminal_valuation.py:240-248 (+0.18 x jt_scaling for community_fund, +0.12 x jt_scaling for managed_transition); admin_shared.py:861 `"just_transition_passed": 6`.

## M-081 — CONFIRMED
CLAIM AS PRINTED: The engine computes a carbon price noise band of +/-7% per round (MACRO_NOISE_CARBON_BAND) and stores it as carbon_price_noise_pct. No code path outside tests and a pedagogical display list appears to consume it. [MARKED TRIANGLE — do not quote until engineering confirms.]
FINDING: Confirmed, and engineering has since confirmed it in the code itself. The triangle can be removed. The band is +/-7%, the draw is stored into events["macro_noise"], and a documented forcing experiment (+0.07 vs -0.07 with the seed held) found ZERO differing fields across four strategies and ten-round games.
EVIDENCE: backend/config.py:562 `MACRO_NOISE_CARBON_BAND = float(_noise.get("carbon_price_band", 0.07))`; backend/engine.py:1434 `carbon_price_pct = round(rng.uniform(-MACRO_NOISE_CARBON_BAND, MACRO_NOISE_CARBON_BAND), 4)`; :1399-1412 "carbon_price_noise_pct REACHES NO PRICE (launch-readiness review 2026-09-03) ... ZERO fields differ, and terminal value, final treasury and M_R are bit-identical"; pinned by backend/tests/test_engine_invariants.py:447-448 ALLOWLISTED_UNCONSUMED_NOISE_FIELDS.

## M-082 — CONFIRMED
CLAIM AS PRINTED: Negotiation routes /accept and /walk-out were NOT registered on the server at 81c23f9 — only /open and /say. Both routes exist at a81b753. negotiation.py itself is BYTE-IDENTICAL across the two commits.
FINDING: All three assertions verified directly from git objects.
EVIDENCE: `git show 81c23f9:backend/router.py` registers only `/negotiation/open` (line 3422) and `/negotiation/say` (3447) — zero matches for accept or walk-out; at HEAD router.py:4136/4161/4210/4236 registers all four; `git show 81c23f9:backend/negotiation.py` and `git show a81b753:backend/negotiation.py` share md5 c25aacd13c2f9984dd42a190b72bfa0c. (At 0ad1246 negotiation.py differs from a81b753 by one change only: a null-guard on group_reputation in accept_concession, audit F-03 — no price or rate moved.)

## M-083 — CONFIRMED
CLAIM AS PRINTED: stakeholder_slo_feedback_enabled (F2) ships FALSE at a81b753 (was True at d105dc2). Measured reason: with it on, a balanced all-B team average SLO fell 53.8 to 0.0 by round 5 and no scripted strategy reached the top two archetypes. Four toggles ship on, two off.
FINDING: Exact, including the measured figures, which the code comment records verbatim. Of the six stakeholder toggles, four ship on and two off.
EVIDENCE: backend/pedagogical_engine.py:720-725 "F-11 (launch audit 2026-09-01, owner ruling 2026-09-02): F2 is OFF by default again. With it on, a balanced all-B team's average SLO fell 53.8 -> 0.0 by round 5 ... and no scripted strategy could reach the top two archetypes." / `"stakeholder_slo_feedback_enabled": False`.

## M-084 — CONFIRMED
CLAIM AS PRINTED: The stakeholder-sentiment engine had NEVER run in production. engine.py imports initialise_sentiment and update_stakeholder_sentiment inside a try block; stakeholder_sentiment.py at 81c23f9 defines NEITHER. The ImportError was swallowed. Both functions are defined at a81b753 (lines 338, 343).
FINDING: Verified from git objects, including the line numbers, which are unchanged at HEAD.
EVIDENCE: `git show 81c23f9:backend/stakeholder_sentiment.py` contains zero definitions of either function; a81b753 and HEAD contain both; backend/stakeholder_sentiment.py:338 `def initialise_sentiment(...)` and :343 `def update_stakeholder_sentiment(`; backend/engine.py:4756-4757 `try:` / `from stakeholder_sentiment import update_stakeholder_sentiment, initialise_sentiment`.

## M-085 — CONFIRMED
CLAIM AS PRINTED: The exit multiple was pinned at its 6.00x floor for EVERY team on every build until a81b753. water_dependency (0-100 index) was passed to a parameter expecting a 0-1 fraction, producing a ~+76pp nature premium that held WACC at its 20% cap from round 1. (1+0.02)/(0.20-0.02) = 5.67x, clamped to the 6.0 floor.
FINDING: The repair is present and the code records the defect in the claim's own terms, including the seed mean and the 20% cap. The arithmetic checks: 1.02/0.18 = 5.667, below the 6.0 floor.
EVIDENCE: backend/engine.py:3684-3691 "F-02 (launch audit 2026-09-01): water_dependency is on a 0-100 scale but calc_esg_adjusted_wacc's biodiversity_dependency is a 0-1 fraction ... Passing the raw mean (seed 54.25) produced a +76-point 'premium' that pinned WACC at the 20% cap from round 1 for every team — and, through the Gordon growth multiple, the 6x exit-multiple floor for every team." / `_avg_water = max(0.0, min(1.0, sum(...) / n_bu / 100.0))`; systemic_risk_engine.py:34 `nature_premium = max(0, biodiversity_dependency * (1 - supply_chain_transparency / 100) * 0.02)`; :37 `min(0.20, adjusted)`; terminal_valuation.py:344-346 and simulation_config.json floor 6.0.

## M-086 — CORRECTED
CLAIM AS PRINTED: CapEx now leaves the treasury: the tranche inside the allowance (20% of positive treasury, floored at $5,000,000) is paid in cash; the excess is drawn as a term loan at 12%, interest on the opening balance, straight-line amortisation with a bullet at R10, carried inside covenant total_debt and R10 net debt.
FINDING: Everything is exact except the $5,000,000 floor, which belongs to a DIFFERENT quantity. The CapEx equity allowance is `max(0.0, base_treasury x 0.20)` with no floor; the $5,000,000 is CSF_POOL_FLOOR, the floor on the investable CSF pool (`max(treasury x 0.20, $5,000,000)`). A round-10 draw is additionally priced and settled within the round, so no debt outlives the game.
EVIDENCE: backend/engine.py:2989 `free_csf_limit = max(0.0, base_treasury * FINANCIAL_FREE_CSF_PCT)`; :3093-3111 loan opening / repayment / interest and the FIN-13 R10 bullet settlement; config.py:201 free_csf_pct 0.20, :215 default_loan_rate 0.12, :205-206 CSF_POOL_TREASURY_FRACTION 0.20 and CSF_POOL_FLOOR 5,000,000 with the comment "Corporate Sustainability Fund investable pool = max(treasury * fraction, floor)"; backend/balance_sheet.py:757-761 mirrors capex_loan_balance into non_current_liabilities.capex_term_loan.
CORRECTED CLAIM: CapEx leaves the treasury: the tranche inside the allowance (20% of positive treasury, no floor) is paid in cash; the excess is drawn as a term loan at 12%, interest on the opening balance, straight-line amortisation with a bullet at R10, carried inside covenant total debt and R10 net debt. (The $5,000,000 floor applies to the investable CSF pool, not the CapEx allowance.)

## M-087 — CORRECTED
CLAIM AS PRINTED: Terminal carbon cost uses a FLAT shadow price of $250/tonne. For group revenue $61.0m at CI 31 (1,891 tCO2e) that is $472,750, about 2.4% of a $20m terminal EBITDA; the no-action case at CI 45.3 is $690,825, so the five-year programme is worth $218,075 on this line. A fourth carbon price now exists: CBAM at $100/tonne.
FINDING: $250/tonne and CBAM $100/tonne are exact, and the arithmetic is internally consistent. "FLAT" is not: four paths move the terminal price off $250 — advanced_climate raises it to max(250, peak internal AC fee); a God Mode override replaces it; R10 Option C's carbon_tax_triple sets 750; and the ending pathways override to 350 or 750. The $61.0m / CI 31 / CI 45.3 figures are simulated terminal outcomes, not code constants, and were not independently reproduced.
EVIDENCE: backend/config.py:195 FINANCIAL_SHADOW_CARBON_PRICE 250.0; :506-508 CBAM_SURCHARGE_RATE default 100.0, simulation_config.json surcharge_rate 100; backend/round_logic.py:394-398 `if decision_paradigm_g == "advanced_climate" and _peak_ac_fee > 0: carbon_tax_per_ton = max(250.0, round(_peak_ac_fee, 2))`; :2696-2697 God Mode override; :2816-2817 `carbon_tax_per_ton = 750`; ending_pathways.py:169/458.
CORRECTED CLAIM: The terminal carbon cost is group tCO2e x a $250/tonne shadow price by default, raised by the advanced-climate peak internal fee, a facilitator override, R10 Option C's carbon-tax triple, or an ending pathway (to $350 or $750); a fourth carbon price exists as the CBAM border levy at $100/tonne.

## M-088 — CORRECTED
CLAIM AS PRINTED: VRIO/imitation decay is CONFIG-DRIVEN and the sources disagree. Code fallback 0.05; repo simulation_config.json 0.05; the data-volume copy at db/simulation_config.json reads 0.10 ... This key has NO sanity clamp; CBAM and NCD neighbours do.
FINDING: The config-driven mechanism and the code fallback of 0.05 are exact, and F-07 did move authority to the server. Two things have changed. (1) The two config copies AGREE at this commit: db/simulation_config.json also reads 0.05. (2) The key now HAS a sanity clamp of the same shape as its CBAM neighbour: anything above 0.08 is rejected back to 0.05 with a logged reason, so a stale 0.10 volume can no longer double the rate.
EVIDENCE: backend/config.py:740-746 `_IMITATION_DECAY_DEFAULT: float = 0.05` / `_IMITATION_DECAY_SANITY_MAX: float = 0.08` / `if DEFAULT_IMITATION_DECAY_RATE > _IMITATION_DECAY_SANITY_MAX: _clamp(... "exceeds the 0.08 sanity ceiling (stale pre-F-07 value)")`; simulation_config.json and db/simulation_config.json both `engine_parameters.imitation_decay = {"default_rate": 0.05}`; backend/engine.py:632-634 calc_vrio_decay.
CORRECTED CLAIM: The VRIO/imitation decay rate is config-driven with a code fallback of 0.05, both shipped config copies now read 0.05, and the key has gained a 0.08 sanity clamp that rejects a stale value back to 0.05 — so the doubling risk described before is closed. (Chapter 1's 5% trajectory is the live one: 0.80 unattended reaches 0.50 by round 10.)

## M-089 — CONFIRMED
CLAIM AS PRINTED: calc_contagion was not normalised at its zero point: at crisis severity 0 it returned 49.04 against a BU mean of 55.0, a -5.96 drop per tick in every quiet round. At a81b753 severity 0 returns exactly 55.00.
FINDING: Confirmed by reading the normalisation, which the code documents with the same 0.119 baseline sigmoid. At severity 0 the normalised fraction is exactly 0, so the group figure equals the BU mean; the raw sigmoid at severity 0 with midpoint 30 / steepness 15 is 1/(1+e^2) = 0.1192, and 55.0 - 50 x 0.1192 = 49.04.
EVIDENCE: backend/engine.py:477-491 "F-01 ... The raw sigmoid is 0.119 at severity 0 (with the default midpoint 30 / steepness 15), which silently removed ~6 reputation points from every team every round — a constant haircut, not contagion." / `normalised = max(0.0, (sigmoid_value - baseline_sigmoid) / (1.0 - baseline_sigmoid))`.

## M-090 — CONFIRMED
CLAIM AS PRINTED: Synergy OPEX reduction is now capped: captured = min(1, sqrt(ratio) x 0.7 x synergy); New_OPEX = Old_OPEX x (1 - 0.06 x captured). At 100% ratio the reduction is -4.2% (-$504K on $12M), not -70%.
FINDING: Exact, and the worked example checks: at ratio 1.0 with synergy 1.0, captured = 0.7 and the reduction is 0.06 x 0.7 = 4.2%, i.e. $504,000 on $12,000,000. (The FEATURE-2 docstring records the previous uncapped behaviour in the same terms.)
EVIDENCE: backend/engine.py:583-607 `captured = max(0.0, min(1.0, math.sqrt(ratio) * SYNERGY_DAMPENING_FACTOR * max(0.0, synergy_multiplier)))` / `factor = 1.0 - SYNERGY_MAX_REDUCTION_PER_ROUND * captured`, with the comment "the previous form took -35% of OPEX per round at a 25% ratio and compounded to the floor by round 4-5"; config.py:335 and :344 (0.7 and 0.06, both confirmed in simulation_config.json).

## M-091 — CONFIRMED
CLAIM AS PRINTED: The stakeholder fatigue engine never fired: it compared the derived group reputation figure with the BU mean, a gap that is identically <= 0 by construction. Zero of 24 probe combinations triggered it. It now dampens each BU reputation GAIN against its value at tick start, before contagion; losses are never dampened.
FINDING: Every clause is confirmed by the code, which records the defect and the probe count in the same terms. The probe count itself is quoted from the change log, as the row's own [reported] marking says, and was not re-run.
EVIDENCE: backend/engine.py:3354-3382 "F-08 ... the derived figure is the mean minus a non-negative contagion dip, so the 'recovery gap' was identically zero and the mechanic never fired (0 of 24 probe combinations). It now acts where recovery actually happens: on this tick's GAIN in each BU's reputation stock relative to what the BU carried into the tick. Losses are never dampened. Runs BEFORE contagion" / `_gain = bu["reputation_score"] - _start` / `if _gain > 0: _kept = calc_stakeholder_fatigue(_gain, crisis_count)`; calc_contagion called immediately after at :3385.

---

# APPENDIX — Verdict summary at 0ad1246

Totals: 97 M-class rows. CONFIRMED 40 (one, M-035, with a reachability caveat) | CORRECTED 44 | REFUTED 13 | UNVERIFIABLE 0.

## Every row that is NOT confirmed
M-001 | CORRECTED | 1bp/unit prices the NCD accrual rate, not cost of debt; NCD never reaches WACC.
M-002 | CORRECTED | Uncapped form superseded; reduction is 6% per round times captured.
M-003 | CORRECTED | Decay is 5% per round, not 2%; start 0.80 is right.
M-005a | CORRECTED | Default dictionary has five Q1 issues, so each miss withholds $3.0m not $2.5m.
M-005c | CORRECTED | materiality_aligned now needs Option A; Option B yields materiality_partial.
M-005d | CORRECTED | Q2 denominator is the active dictionary's disclosure Q2 count (two), not a fixed four.
M-005e | CORRECTED | Clawback is 40% of the RELEASED fund, treasury charged for any shortfall.
M-007 | CORRECTED | $50/5% escalates per ROUND; $350/$750 override the $250 shadow price, not the fee.
M-008 | CORRECTED | Config-driven green_claim, not A/C; penalty is social licence not reputation; no auditor tolerance.
M-009 | CORRECTED | Cyclone strikes when roll is BELOW 0.75; R5 choice cannot mitigate R5 damage.
M-011 | CORRECTED | -0.40 now ramps linearly from SLO 80 to 70, not a cliff at 75.
M-012 | CORRECTED | Sigmoid is normalised so severity 0 gives zero dip.
M-016 | CORRECTED | Per-tier treasury floors removed; one global -$500M. Tiers gained fine cap and covenant ratio.
M-017 | CORRECTED | Tightening is +1% not +2%; crisis is +1.5% R9 and +2.0% R10, not +3%.
M-018 | CORRECTED | 6,500,000 shares not 100,000,000; Green Fund only in Advanced Climate; EBITDA floored at 0.
M-021 | REFUTED (unreachable) | Computed after severity is applied and stored only as a diagnostic with applied=False.
M-029 | CORRECTED | Not the scoring library; five Q4 issues carry no ESRS reference; two long horizons not one.
M-030 | CORRECTED | The 12/25 product applies only to four-score dictionaries; no shipped one qualifies.
M-032 | CORRECTED | Bias rules key off CSRD_ISSUES ids, so all four panels are equally accurate on the default dictionary.
M-033 | CORRECTED | One shipped issue now carries is_ambiguous, so four stars is attainable.
M-034 | REFUTED (no such code) | The single-pair numeric branch was deleted; four dual-axis scores are now required.
M-036 | CORRECTED | r2_governance_choice is now written; clawback, tier block and governance signal all fire.
M-038 | CORRECTED | Option A revenue_delta is now 0; the double charge was removed.
M-039 | REFUTED (no such code) | Both old writers gone; _post_r2_materiality is the sole writer, sets True/False.
M-040 | REFUTED (no such code) | Release is a ring-fenced fund, not a treasury debit.
M-041 | REFUTED (no such code) | _POST_TICK_MAP[2] = _post_r2_materiality exists; all ten rounds covered.
M-042 | REFUTED (no such code) | One classifier now drives targets and scoring; the two rules cannot disagree.
M-043 | CORRECTED | Mechanism still live, but R2 Option A's revenue_delta is 0, so no $12.5m loss.
M-044 | CORRECTED | Only one outlier remains (R10 Divest -2.0m); R2 Option A is no longer one.
M-051 | CORRECTED | Suite is 27 defs / 40 parametrised cases, not 38; the named branch no longer exists.
M-052 | REFUTED (no such code) | Expression rewritten; Option B and C pass, Option A fails; the two mechanics agree.
M-053 | CORRECTED | scope_3_transparency is now written at R3 completeness >= 80; both routes exist.
M-054 | CORRECTED | retraining_succeeded is now written alongside nbs_succeeded.
M-055 | REFUTED (no such code) | All four special_rules keys now have live readers.
M-056 | CORRECTED | The boolean write is gone; a generalised dual-form guard test now exists.
M-057 | CORRECTED | "No key written-and-never-read" now has two allow-listed exceptions: divest_all, carbon_price_noise_pct.
M-058 | REFUTED (no such code) | social_license_delta is now applied generically for every round.
M-059 | REFUTED (no such code) | natural_capital_debt_delta is now applied generically for every round.
M-060 | REFUTED (no such code) | Amplifier moved to post_tick; it escalates 1.1x at R4 to 1.7x at R10.
M-061 | CORRECTED | Six keys are now generic, not four; aliases are read as fallbacks.
M-062 | CORRECTED | Pillar SLO applier is router.py:8069, effectiveness-scaled; the legacy gap is itself closed.
M-063 | CORRECTED | R2 option treasury is now charged in post-tick; Option A is not free.
M-065 | CORRECTED | Only divest_all remains unapplied; the other three keys were repaired.
M-066 | CORRECTED | Decay ladder omits the 20% middle tier; the three agent SLO figures are mis-assigned.
M-067 | CORRECTED | Decay 6-10 and recovery 2-5, not 8-15 and 2-3; four triggered figures mis-assigned.
M-068 | CORRECTED | Regulator fine is now capped; only greenwashing betrayal flags can actually reach the scar.
M-069 | CORRECTED | Whitelist has six concessions; dividend_signal $0.5m/+8 is omitted.
M-071 | CORRECTED | No reputation bonus at 80% (a -3 penalty below it); no R2 gate; strike needs Immediate Closure.
M-072 | CORRECTED | Four toggles ship ON, not five: F2 licence feedback ships FALSE.
M-073 | CORRECTED | Greenwash absolute floor is $3m of TOTAL group CapEx, not an average per BU.
M-076 | CORRECTED | Five switches ship ON and two OFF, not six and one.
M-077 | CORRECTED | Shipped config is $50 / 5%, not $40 / 15%; there are four carbon prices, not three.
M-079 | REFUTED (no such code) | Share count is 6,500,000, so implied equity is ~$325m at ~19x, not $5bn at 294x.
M-080 | REFUTED (no such code) | The expression was replaced; the two mechanics now agree. Chapter 9 is unblocked.
M-086 | CORRECTED | The CapEx allowance has no $5m floor; that floor belongs to the CSF investable pool.
M-087 | CORRECTED | The terminal price is not flat: four paths move it off $250.
M-088 | CORRECTED | Both config copies now read 0.05 and the key gained a 0.08 sanity clamp.

## NOT FOUND / UNCERTAIN
1. M-051's run totals ("backend suite 2087 passed; frontend jest 1099 passed"). Not checkable without executing the suites. For reference, backend/tests/*.py carries 2081 `def test_` definitions across 201 files, before parametrisation.
2. M-035's reachability. The sentence is in the source verbatim, but CSRD_ISSUES is imported into router.py and its name is never used again there, so I could not establish that the string renders to a student on the default path.
3. M-087's $61.0m revenue / CI 31 / CI 45.3 terminal figures. These are simulated end-of-game outcomes, not code constants; the arithmetic is internally consistent at $250/tonne but was not independently reproduced.
4. M-091's "zero of 24 probe combinations". The row itself marks this [reported]; the code states the same result but the probe was not re-run.
5. M-021, M-032, M-068 depend on reachability arguments rather than on absent code. Each is documented with the read shape and the write shape so an engineer can re-check.
6. Two internal inconsistencies noticed in passing that no register row covers, and that a facilitator-facing chapter may want to name: (a) admin_router.py:2102 stores the negotiation-rooms capability under a comment reading "opt-in, default OFF" while both the request model default and admin_shared.facilitator_negotiation_granted default it ON; (b) the BRSR side track writes `greenwash_detected` (brsr_controller.py:357) while the main engine writes `greenwashing_detected` (engine.py:4275) — the two spellings are not the same key.
7. Stale comments found sitting above live code, each of which would mislead a reader quoting the source: terminal_valuation.py:33 and :398 ("100 million shares"); engine.py:660 ("burnout > 40 → +0.3% OPEX"); round_configs.py:529 ("harmonised to match M_R +0.30"); terminal_valuation.py:156 and :209 (naming R7 option_c "Resist & Integrate" when round_configs titles it "Waste-to-Energy Partnership"); npc_stakeholders.py:26 and :649 ("stakeholder_memory_enabled ... defaults OFF" — it ships True).

---

# PHASE 5 RE-EXECUTION — 2026-09-08

Basis: the working tree of `fix/audit-remediation-wave3-20260906` after Phases 0–5
(the register above was traced against `0ad1246`). Method: every `backend/*.py:LINE`
citation in the 99 rows above was matched against a whitespace-normalised view of
the current file, so a statement the register joined onto one line still matches
when the source spans several, and `...` is matched as an elision. Then every row
whose CLAIM touches a mechanic Phase 5 moved was re-read by hand against both rule
sets. `backend/tests/calibration_sweep.py` and
`docs/verification/phase5_recalibration.md` carry the measurements cited below.

**Every claim below is now potentially TWO claims**, because a session records the
rule set it is graded under (`rules._rules_version`). Rows that changed are stated
for both. `2026.09` is every session played to date and every unstamped record;
`2026.10` is every session created from 2026-09-08.

## Mechanical citation status, all 99 rows

| | rows | meaning |
|---|---|---|
| EXACT | 18 | every cited fragment is still at the cited line |
| MOVED | 45 | every fragment is still in its file, at a different line — code moved beneath it, the claim did not |
| NEEDS RE-READ | 34 | at least one fragment is no longer findable as quoted |
| no EVIDENCE line | 2 | section headers, not claims |

The 34 include a known class of false positive: the register sometimes quotes a
config path (`engine_parameters.imitation_decay = {...}`), a bare number, or a
shell command inside backticks, none of which is Python source. They are listed by
`python3 backend/tests/register_check.py --human`.

**The 45 MOVED rows are not re-stamped here.** A line number that has drifted is a
citation defect, not a claim defect, and rewriting 45 rows' worth of numbers
mechanically into a verification document is exactly the kind of edit that should
be reviewed rather than generated. They are enumerated by
`python3 backend/tests/register_check.py --moves`, which lists only the
unambiguous single-destination moves.

## How wide the cut-over reaches — measured, not enumerated

The twelve rows below were found by searching claim TEXT for the names of the
switched mechanics. That is a weak instrument and this section says so; two
stronger ones were built afterwards, and the second changes how the rest of this
register should be re-executed.

**By code location** — `python3 backend/tests/register_check.py --versioned`.
It finds the fifteen `rule_on` / `rule_value` sites in the backend, resolves every
fragment quoted in this register to its CURRENT line (the citations are stamped
against `0ad1246`, so the numbers here cannot be tested directly), and reports
which rows cite code inside a rule-gated function. Result: **one row, M-068**,
which was already re-executed below. Wording cannot evade this check — but it only
catches rows citing the gate itself, and M-020 and M-085 below are
version-dependent because the values flowing INTO them changed, not because their
function is gated.

**By measurement** — `python3 backend/tests/calibration_sweep.py surface`.
It compares every scalar key in the closing global state, flag bag and aggregated
business units across paired games. Over 150 pairs, of **440 distinct quantities**:
142 differ in value at least once, 45 exist under one rule set only, **169 are
affected**, and 271 were not observed to differ. The chain runs
`supply_chain_transparency` → the nature premium → `cost_of_capital` →
`exit_multiple_wacc_used` → `terminal_value`, `equity_value`, `price_per_share`,
and on into treasury, EBITDA, opex, emissions, carbon cost and the per-BU figures.

**The rule this gives the register.** A row is version-dependent if its claim
quotes a quantity on the affected list — NOT if its claim happens to name a
switch. About 38% of the model's closing state is affected, including numbers
whose claims mention no switched mechanic at all. Run the tool with `--safe` for
the complement; treat "not observed to differ in 150 games" as evidence, not
proof.

## Rows whose CLAIM Phase 5 touched — re-executed

Twelve of the 99 rows name a quantity, flag or mechanic that Phase 5 moved. Three
changed. Nine did not. **This is a floor, not a ceiling** — see the rule above.

### M-020 — SUPERSEDED under 2026.10 (was CONFIRMED)

CLAIM AS PRINTED: M_SDG = 1.0 + (SDG Impact Score / 100) × 0.25, giving a range of
0.97 to 1.26.

FINDING: Correct and unchanged under **2026.09**. Under **2026.10** the formula
gained a neutral point and the input quantity changed, so both the input and the
range are different. `calculate_sdg_multiplier` is now
`1.0 + ((score − neutral) / 100) × coeff`; at `neutral=0` — the default, and what
2026.09 passes — it is bit-identical to the printed form. Under 2026.10 the score
is `engine.calc_sdg_impact`'s `sdg_index` with the Corporate SDG side track folded
in, and `neutral` is `config.SDG_INDEX_NEUTRAL = 73.5`. The neutral point is what
makes the change safe: the index sits near 73.5 for a team that has done nothing,
so anchoring at zero would have handed every session a ~22% terminal-value uplift
for standing still.

EVIDENCE: `backend/terminal_valuation.py:417-447` `calculate_sdg_multiplier(...)`
/ `:442` `m_sdg = round(1.0 + ((sdg_impact_score - neutral) / 100.0) * k, 4)`;
`backend/config.py:766-777` `SDG_INDEX_NEUTRAL = 73.5`, `SDG_MULTIPLIER_COEFF = 0.25`;
`backend/rules.py` `SWITCHES["sdg_single_quantity"]`.

MEASURED, 3,300 games: under 2026.09 M_SDG takes exactly ONE value, 1.0000, in
every game — the Corporate SDG side track is inactive on sampled paths, so the
multiplier is inert. Under 2026.10 it takes 636 distinct values spanning
0.8965 to 1.0757 (p05/p50/p95 = 0.9317 / 1.0015 / 1.0587, swans off).

CORRECTED CLAIM (2026.09): unchanged from the register above.
CORRECTED CLAIM (2026.10): M_SDG = 1.0 + ((SDG Index − 73.5) / 100) × 0.25, where
the SDG Index is the engine's own index with the side track folded in. Measured
range over 3,300 games: 0.8965 to 1.0757.

### M-068 — CORRECTED AGAIN (two errors, one of them in the register's own terms)

CLAIM AS RE-EXECUTED AT `0ad1246`: *"Of the three named betrayal flags only the
greenwashing family can actually fire … deny_and_deflect exists only as a list
element inside rN_flags, and materiality_ignored is written into
active_event_flags, not into the tick's events, so neither reaches the scar."*

FINDING: Both halves need correcting, and the first was wrong at `0ad1246` too.

**(1) `materiality_ignored` DOES reach the scar, under both rule sets.** The
register's reasoning — written into `active_event_flags`, therefore not in the
tick's `events` — does not hold, because `new_global["active_event_flags"]` and
the `events` bag are ONE object (`engine.py:4472`, `:4905`). `detect_betrayal`'s
first line, `active = {k for k, v in events.items() if v is True}`, therefore sees
it. Measured on path `all_c`, attributing each detection to its container: the
scar fires at R2 on `materiality_ignored` under 2026.09 as well as 2026.10. This
is a correction to the register, not to the code.

**(2) `deny_and_deflect` reaches the scar under 2026.10 only.** Phase 4 gated the
list-element read behind `rules.SWITCHES["npc_betrayal_reads_option_flags"]`; the
2026.09 branch is preserved bug-for-bug. Measured on `all_c`: the scar fires at R4
under 2026.10 and not under 2026.09.

**(3) A third fire, at R10, was a defect and is gone.** Until 2026-09-08 the R10
finale parked its re-run record under a bare key on the flag bag, so
`collect_all_flags` handed the whole game's flag history back to `detect_betrayal`
and one R4 decision produced two scars. Appendix B "Shape F";
`phase5_recalibration.md` §5.2.

EVIDENCE: `backend/npc_stakeholders.py:56-73` `detect_betrayal`, with `:70`
`active |= set(collect_all_flags(events))` (2026.10) and `:72`
`active |= {str(x) for x in (events.get("flags_set") or [])}` (2026.09);
`backend/autonomous_agents.py` carries the same function verbatim and
`tests/test_flag_rule_switches.py` asserts the two copies still agree;
`backend/flag_utils.py` `FINALE_INPUTS_KEY`;
`backend/tests/test_finale_record_is_storage.py::test_one_decision_raises_one_betrayal`
pins the R2-and-R4-only cadence.

MEASURED: the switch is the only one of the nine that moves a graded number —
mean ΔM_R −0.0129, worst −0.4250, mean ΔTV −1.88% over 120 specs; 6 of 120 runs
lose more than 0.05 of M_R.

CORRECTED CLAIM (2026.09): of the three named betrayal flags, the greenwashing
family and `materiality_ignored` fire; `deny_and_deflect` does not, because it
exists only as a list element inside `rN_flags` and the 2026.09 reader looks for a
top-level key or an `events["flags_set"]` list that nothing writes.
CORRECTED CLAIM (2026.10): all three fire, each exactly once, in the round the
flag is set. Everything else in M-068 — the four NPCs, the salience profiles, the
−5/−3 drain, the FIN-09 fine cap, gain_rate 0.25 < loss_rate 0.55, the recovery
ceiling and the staging limiter — is unchanged and still exact.

### M-085 — EXTENDED (still CONFIRMED; its input is no longer a constant)

CLAIM AS PRINTED: the exit multiple was pinned at its 6.00× floor for every team
until `a81b753`, because `water_dependency` (0–100) was passed to a parameter
expecting a 0–1 fraction.

FINDING: The repair and the arithmetic are exact and unchanged. What Phase 5 adds
is that the OTHER input to the same term has changed. The nature premium is

```
nature_premium = max(0, biodiversity_dependency × (1 − supply_chain_transparency/100) × 0.02)
```

and `supply_chain_transparency` was **constant at 40.0 in all 3,300 baseline
games** (§4.1 of the delta report): the score's read was the Shape-C defect, so
six of its eight boosts never applied. Under 2026.10 it is a real distribution
with a mean of 24.05, so `(1 − SCT/100)` rises from a fixed 0.60 to a mean 0.76
and the nature premium — hence WACC, hence the Gordon-growth exit multiple —
moves for every team.

MEASURED, 3,300 paired games: mean ΔSCT −15.95, mean ΔWACC +0.00168. The nature
premium alone predicts +0.00173 from the seed's mean water dependency (0.5425),
i.e. essentially all of it. Exit multiples sitting at the 18× cap fall from 617 to
529 (−14%).

EVIDENCE: `backend/systemic_risk_engine.py:37` the nature-premium line;
`:101` `calc_supply_chain_transparency`; `backend/engine.py:3712`
`_avg_water = max(0.0, min(1.0, ...))`; `backend/rules.py`
`KNOBS["sct_entropy_per_round"]` (−3.0 → −1.0) and
`SWITCHES["sct_flag_boosts_live"]` / `["sct_boosts_apply_once"]`.

ADDED CLAIM: Supply-chain transparency is not a display KPI. It is an input to the
ESG-adjusted WACC through the nature premium, so the Phase 5 recalibration of that
score moves the exit multiple — the one place in the model where a "soft" score
reaches the valuation without passing through M_R.

### Re-executed and UNCHANGED

| Row | Why it was re-read | Outcome |
|---|---|---|
| M-005f | `materiality_aligned` +0.10 M_R | Unchanged. Tier message now at `round_logic.py:3708-3710`; the +0.10 / +0.05 / 0 table is untouched by Phase 5. |
| M-018 | the terminal-value formula carries M_SDG | Formula unchanged (`terminal_valuation.py:605`). The M_SDG *input* changed — see M-020. The share count is not an open item: 6,500,000 in code and in the manuscript since 4 September (Ch 14 §14.5.2, Ch 18 §18.2.8, both Student Manuals), so the discrepancy this row reported at `0ad1246` is closed. |
| M-029 | Round 2 issue library | Unchanged; not a Phase 5 surface. Line drift only. |
| M-033 | assurance stars, `is_ambiguous` | Unchanged; matched only on the word "biodiversity". |
| M-045 | which dictionary a session scores against | Unchanged. |
| M-053 | the +0.20 Supply Chain Transparency M_R premium | Unchanged. This premium reads the `scope_3_transparency` / `full_remediation` FLAGS in `ending_pathways.py`; it is unrelated to the `supply_chain_transparency` SCORE recalibrated in §4.1, despite the shared name. Worth stating, because the two are easy to conflate. |
| M-069 | negotiation concessions | Unchanged. |
| M-070 | the promise ledger fires the F1 betrayal scar | Claim unchanged. Note the scar's TRIGGER set widened under 2026.10 (M-068); the ledger's own behaviour did not. |
| M-083 | toggle defaults, archetype reachability | Unchanged. The measured SLO collapse it records is a 2026.09 measurement and Phase 5 did not re-run it. |

## What remains open

Exit condition 3 — *"a register with no row still stamped against the old commit"* —
is **not met**. What is done: the twelve rows whose claims Phase 5 could have
moved are re-executed above, against both rule sets, with measurements. What is
not done, and is not a line-number refresh:

1. **45 rows carry drifted citations.** Mechanical, enumerated, reviewable.
2. **34 rows have at least one citation that no longer resolves as quoted** and
   need a human re-read. Some are false positives of the checker; the rest are
   real drift from Phases 0–4.
3. **Every row is now potentially two claims.** The register's contract was
   written when there was one rule set. A row needs a 2026.09 and a 2026.10
   statement if it quotes any of the 169 affected quantities — which is the rule
   the section above establishes, and is far broader than "names a switch".
   Twelve rows are done. The remainder should be swept against the affected list,
   not against the switch names; the code-location check is already clean, so
   what is left is the quantity sweep and the re-reads it produces.

Until those are closed, the header stamp at the top of this document stands as
written — `HEAD verified: 0ad1246` — because moving it would assert a re-execution
that has not happened.
