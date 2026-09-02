# Muressons Simulation — Model Card

**Version:** 2026-09-02 (launch-audit fixes F-01/F-02/F-03 applied — see AUDIT_Independent_Review_2026-09-01.md §8 and the change log at the end of this card; previous version 2026-09-01, post engine-excellence campaign)
**Scope:** the core-game economic model (all paradigms), its stochastic systems, and terminal valuation.
**Companion documents:** SIMULATION_CONTEXT.md (mechanics reference; its Canonical Option
Economics table is generated from config), SPEC_Pillar_Revenue_Impacts.md (the evidence
discipline this card extends), BALANCE_REPORT_BASELINE.md (empirical behaviour under
scripted strategies).

## 1. What this model is

A 10-round (5 simulated years; 6-month rounds) ESG business simulation for teaching
sustainability strategy. It is a **pedagogical model, not a forecasting model**: several
parameters are deliberately compressed or amplified so that consequences that take a
decade in reality arrive inside one course. This card records, for each load-bearing
economic parameter: the shipped value, the real-world benchmark, and an explicit verdict —
`realistic`, `stylized` (compressed timescale or amplified coupling, direction faithful),
or `pedagogical` (exaggerated to guarantee a teaching moment). Numbers below are the
config defaults; facilitators can override several per cohort.

## 2. Parameter review

### 2.1 Carbon pricing

| Parameter | Shipped | Benchmark | Verdict |
|---|---|---|---|
| Operating carbon fee (`global_carbon_fee` / `ECONOMIC_CARBON_PRICE_BASE`) | $40–50/tCO2e | EU ETS EUA ≈ €70/t (Apr 2026); first CBAM certificate €75.36/t; CDP median disclosed internal price ≈ $25/t (Europe/Asia avg ≈ $28) | `realistic` — sits between the internal-price median and the EUA market price |
| Terminal / shadow carbon price (`FINANCIAL_SHADOW_CARBON_PRICE`, R10 tax + CAROIC) | $250/t | US EPA social cost of carbon central estimate $190/t (2020$, 2% discount rate); Citi forecasts EUA €145/t by 2030, €200/t by 2035; Audi's internal price $200/t | `stylized` — a defensible high-ambition SCC; models the "carbon liability comes due" thesis at exit |
| Carbon price growth | +5%/round (~10%/yr) | Linear Reduction Factor tightening 4.4%/yr from 2028; consensus 2030 forecasts imply ~10–15%/yr appreciation | `realistic` |
| CBAM surcharge (`CBAM_SURCHARGE_RATE`) | $100/tCO2e × the group's total Scope 1+2 tCO2e, charged to treasury in rounds 3 and 7 when average CI > 40 and Scope 1+2 CI > 40 × 0.35 (was $100,000/t — a 1,000× data-entry error in `simulation_config.json`/`.xlsx`, F-03: ≈ 900 t at seed emissions made each hit an $81–120M treasury wipe-out, measured on Postgres; at $100/t the same hit is ≈ $90k); `config.py` clamps any value above $5,000/t back to the default and logs a warning, because deployed volumes load their own copy of the config | EU CBAM certificate price tracks the EUA weekly average, ≈ €70–75/t (2026); Citi €145/t by 2030 | `realistic` — set at the upper end of the 2026–2030 corridor so the levy is visible without dominating the P&L |

### 2.2 Valuation

| Parameter | Shipped | Benchmark | Verdict |
|---|---|---|---|
| Exit multiple (`TV_EXIT_MULTIPLE_*`) | Gordon growth `(1+g)/(WACC−g)`, g = 2%, clamped 6–18× EV/EBITDA. **Measured after F-02:** a team at the 5% ratchet floor sits ON the 18× ceiling; WACC must exceed ≈7.7% before the multiple moves, 12× corresponds to WACC ≈ 10.5%, and 6× to ≥ 19%. (Before F-02 the water-dependency unit bug pinned WACC at 20% for every team, so **every** team received the 6× floor and the coupling was inert.) The 12× "fixed fallback" applies only when no WACC is available. | 2026 sector multiples: household products ≈ 13.7×, pharma ≈ 18.6×, electronics ≈ 25.9×, application software ≈ 31.8× | `realistic` at the ceiling for the default mix, but **the ceiling binds for most healthy teams**, so the WACC→multiple coupling only bites once ESG premia lift WACC past ≈7.7%. Recalibration candidate: a lower ceiling (≈14×) or a higher g-adjusted base would restore a gradient among healthy teams. Open design decision, recorded here, not changed by the audit. |
| Regenerative Multiple M_R | clamp [0.0, 2.05]; components per calculate_mr; pinned ceilings 1.93 (legacy) / 2.02 (pillar) | ESG valuation premia in the literature run ~10–30% of EV, not ±100% | `pedagogical` — deliberately amplified so ESG strategy dominates the leaderboard; the model's central teaching lever |
| Cost of capital | base 5% (`cost_of_capital` seed), persisted as a stock in `active_event_flags.base_cost_of_capital`; per-regime macro modifier (−1% … +2%) applied as a LEVEL each round (no longer compounding as a flow); ESG-adjusted WACC = base + carbon premium + governance premium − SLO discount + nature premium (`water_dependency`/100 × (1 − transparency/100) × 0.02), clamped 3–20%; regulatory ratchet floor never falls unless avg investment ≥ 20% (−0.5%/round). **Measured trajectory (balance runner, pure_B): 5.2% → 8.0% over ten rounds.** | Real corporate WACC ≈ 7–11%/yr | `realistic` in level (the previous card's "≈20%/period" described the F-02 bug, not the design); `stylized` in the ratchet, which is the model's "reputation for risk is sticky" lever. Cost of capital reaches treasury only through NCD interest (a BU stock), the negative-treasury debt service and the exit multiple — it is not a treasury flow. |
| CapEx financing (changed 2026-09-02, F-05) | CapEx **leaves the treasury**. The tranche inside the allowance (20% of treasury, `FINANCIAL_FREE_CSF_PCT`, floored at `CSF_POOL_FLOOR`) is paid in cash this round; the excess is drawn as a term loan (`capex_loan_balance`, a stock in `active_event_flags`) at 12% (`FINANCIAL_DEFAULT_LOAN_RATE`), with interest on the opening balance and **straight-line principal repayment over the remaining rounds** (bullet at R10). Both appear on the balance sheet (`capex_term_loan`, inside covenant `total_debt`) and in the terminal net debt. Before this, CapEx principal was never a treasury outflow and the loan was interest-only forever — a team could allocate $30M a round for free. | BBB corporate lending ≈ 5–7%; principal amortises | `realistic` in structure; 12% is `stylized`-high (round compression, §3.2). The amortisation means late-game CapEx is repaid fast — a 10% treasury allowance keeps the pure_B bot solvent with $52M at R10 (balance report). |
| Insolvency floor | −$500M + $200M × ESG investment ratio (`FINANCIAL_TREASURY_FLOOR`), evented as Insolvency Floor Relief | Real firms enter administration far earlier | `pedagogical` — keeps failed teams playing to R10 while still ranking them last |

### 2.3 ESG–finance couplings

| Parameter | Shipped | Benchmark | Verdict |
|---|---|---|---|
| NCD → cost of debt (`NCD_INTEREST_COEFFICIENT`) | +1bp per NCD unit, compounding (NCD 500 ⇒ +5pts) | Corporate-bond studies find ESG-quartile spreads of tens of bps, not hundreds | `pedagogical` — amplified ~10× so natural-capital neglect becomes a visible debt spiral within 10 rounds; direction supported by the cost-of-debt literature |
| NCD → OPEX penalty (`NCD_OPEX_PENALTY_PER_UNIT`, F-10) | $1,000 per NCD index unit per BU per round (× tipping hostility), capped at 50% of BU revenue (75% once tipped); was `ncd × 50,000 / 1e6` = 5 cents per unit, i.e. inert. The NCD thresholds (`NCD_*`, 5,000 / 1,000) are on the index's actual scale. Charged as a per-round flow (see the flow-penalty row). | No market benchmark — natural-capital liabilities are not priced | `pedagogical` — sized so a neglected BU (NCD ≈ 3,000) pays ≈ $3M a round, visible but not fatal |
| Synergy OPEX saving (`SYNERGY_MAX_REDUCTION_PER_ROUND`, F-06) | OPEX × (1 − 0.06 × captured), captured = min(1, √ratio × dampening × synergy); i.e. **at most −6% OPEX per round** from synergy. Before, the reduction was unbounded in the synergy multiplier and could compound past 20%/round. | Operating-synergy programmes deliver low single-digit % of cost base per year | `realistic` |
| Flow penalties and cash (rulings A/C + F-04/F-04b) | Supply-chain contagion surcharge, DSO deferral, talent retention premium, NCD OPEX penalty, supplier defection and green-premium squeeze are **per-round flows**: they hit this round's P&L and treasury and are reversed from the persisted BU base before the tick ends, so nothing compounds. Where the penalty is assessed after gross profit is banked (talent, NCD, defection, squeeze) the engine charges treasury directly and events it (`post_csf_flow_adjustments_cash`, waterfall "Flow surcharges after gross profit") — until 2026-09-02 those four reached no cash at all under the transient rule, and multi-toggle and legacy trajectories had become identical. Inflation scales recorded transients so the reversal is exact. | — | `stylized` — the *mechanics* are accounting, the magnitudes inherit the verdicts of their own rows |
| Governance → cash conversion | revenue × (1 − gov_risk/500), charged to the ROUND as realized-cash drag (ruling A, 2026-09-01 — previously eroded `revenue_base` permanently, the diagnosed death-spiral driver) | DSO/working-capital drag rises with weak governance; supported directionally | `stylized` |
| Inflation symmetry (`INFLATION_REVENUE_PASSTHROUGH`) | revenue inflates at 80% of cost inflation (ruling B, 2026-09-01) — inflation is margin pressure, no longer a one-sided death tax | firms with pricing power pass through most input inflation; 70–100% pass-through observed in recent inflation episodes | `realistic` |
| Greenwash check (`GREENWASH_*`) | claim-tagged options vs 15% avg investment; −15 SLO/BU (full), half for moderate | ESMA fund-naming rules, FTC Green Guides enforcement | `stylized` — enforcement probability is 1.0 when triggered (real enforcement is sporadic); threshold is invented but directionally right |
| Dividend ratchet | cut >20% ⇒ −5 reputation | Dividend-signalling literature: cuts reliably produce negative abnormal returns | `realistic` in direction, invented magnitude |

### 2.4 Stochastic systems (all cohort-seeded, GAME-4)

| Parameter | Shipped | Benchmark | Verdict |
|---|---|---|---|
| R5 cyclone (`CYCLONE_PROB_BASE`, `PHYSICAL_VAR_DAMAGE_BASE`) | 75% probability (90% climate-tipped), $12M base damage | Annual Cat-4+ landfall probability for any single facility is a few percent at most | `pedagogical` — compressed so that ~three quarters of cohorts experience the physical-risk lesson; damage magnitude (~7% of group revenue) is in the plausible range for an uninsured direct hit |
| R9 strike | 50% base when avg SLO < 50; burnout adds up to +20pts; cap 95%; zeroes round revenue | BLS: ~30 major US work stoppages/yr economy-wide — striking is rare in absolute terms | `pedagogical` — conditional framing ("IF you finish 9 rounds with SLO<50") makes 50% defensible as a teaching device, not a base rate |
| Black swans | per-event 2–2.3%/round, 1-round cooldown, treasury hits ~5–8% of treasury | Idiosyncratic tail-event rates are unknowable at this granularity | `stylized` |
| CapEx overrun | >$3M ⇒ 25% chance of +15% | Megaproject literature (Flyvbjerg): cost overruns hit ~2/3 of projects, mean ≈ +30–60% | `realistic-conservative` |

### 2.5 Terminal pathway modifiers (verified against `ending_pathways.py`, 2026-09-01)

Climate Black Swan: +0.30 Climate Leader (avg CI<25, ramped), +0.20 Adaptation Premium,
+0.15 Carbon Transition (CI −40% vs R1), −0.40 Carbon Denial, −0.20 Shadow Board.
Stakeholder Revolt: +0.35 / +0.15 Employee Champion / +0.15 Community Trust / −0.50.
Regulatory Shutdown: +0.30 Regulatory Exemplar (ethics>7, no scandals) — doc figures in
SIMULATION_CONTEXT §6 match the shipped code. Cross-pathway difficulty coefficients
(1.00–1.20) are asserted design weights, not empirical estimates.

### 2.6 Reputation (changed 2026-09-02, F-01)

`group_reputation` is now a **derived** figure: the mean of the BU `reputation_score`
stock minus the live-crisis contagion dip, which is normalised so that a crisis of
severity 0 subtracts exactly 0 (the raw sigmoid at severity 0 used to shave ≈5.9 points
off the group figure every round with nothing wrong — the "phantom reputation drift"
that pushed every quiet team toward the 25-point brain-drain threshold by R6). Every
between-tick write to `group_reputation` (side tracks, agents, black swans, dividend
ratchet, emissions breach) is folded into the BU stock on the next tick through a
stamp-and-carry reconciliation (`_group_rep_derived` in `active_event_flags`), so no
shock is lost and none is double-counted. The contagion midpoint (severity 30) still
costs ≈16 points and a severity-100 crisis ≈50. Verdict: `stylized` — direction and
magnitudes as before, minus the artefact.

## 3. Known limitations

1. **CapEx financing** (§2.2): resolved 2026-09-02 (F-05) — CapEx debits treasury and
   the excess amortises. The remaining simplification is a single 12% rate that does not
   move with the ESG-adjusted WACC.
2. **Round compression**: one round = 6 months, but several rates (WACC, inflation
   5%/round, NCD compounding) behave closer to annual rates, an intentional 2× speed-up.
3. **Pillar-mode balance is unmeasured headlessly**: the router owns pillar impact
   application, so BALANCE_REPORT covers legacy_abc only.
4. **Difficulty (recalibrated 2026-09-01)**: the pre-ruling economy bankrupted every
   scripted strategy AND every real alpha team by R4–R7 (see
   CALIBRATION_DIAGNOSIS_2026-09-01.md). After rulings A+B+C (flow-not-stock
   penalties, 80% inflation pass-through) the balance report shows the intended
   gradient: disciplined ESG solvent and winning, extraction/neglect still failing.
   **Re-measured 2026-09-02 after phase 3 (F-04…F-13):** aggressive_green $891M,
   M_R 1.43, SAFE_HAVEN; balanced $415M / 1.03; pure_B $148M / 0.92, all solvent;
   pure_A, pure_C, extractive bankrupt R7. With the F2 continuous-pressure toggle ON
   the same disciplined bot reaches only M_R 1.03 and $572M — the reason F-11 turned
   the default OFF (a facilitator opts in per cohort). Note that the balance runner
   (`dry_run.py`) had been passing `crisis_severity=40` into every round — a permanent
   crisis production never had (the client sent 0; only the R4 crisis round is 40) —
   which drove group reputation to 0 by R4 in every scripted run. It now uses the
   same server-derived parameters as the router (F-07), so the report measures the
   deployed game.
   Watch item: greenwash checks use a RELATIVE investment ratio, so healthier
   treasuries raise the absolute investment needed to avoid scandal — monitor
   greenwash frequency in the next cohort's telemetry.
5. **M_R amplification** dominates terminal spread by design; instructors should present
   TV rankings as strategy quality, not market realism.
7. **Terminal values moved twice on 2026-09-02** (BALANCE_REPORT_BASELINE.md): first
   ≈2× when the exit multiple came off the 6× floor every team used to receive (F-02:
   aggressive_green $250M → $557M), then again with phase 3 (CapEx amortisation, the
   flow-penalty cash pass-through, the synergy cap, the balance runner's severity fix:
   aggressive_green $891M, balanced $415M, pure_B $148M; failed strategies clamp to
   $0). Solvency ordering is unchanged. Any scoring rubric or facilitator material
   that quotes absolute terminal-value bands must be re-read against the new baseline.
6. Magnitudes marked `pedagogical` above are teaching devices; the model card verdict —
   not the narrative text — is the honest label.

## 4. Evidence sources

- EUA spot ≈ €70/t and CBAM €75.36/t (Apr 2026); Citi €145/t 2030 forecast: https://www.homaio.com/post/2030-eua-price-predictions-expert-analysis-of-3-scenarios
- CDP median internal carbon price ≈ $25/t (Europe/Asia avg $28; Audi $200/t): https://trellis.net/article/how-start-using-internal-carbon-price/ and the CDP 2021 carbon-price report: https://cdn.cdp.net/cdp-production/cms/reports/documents/000/005/651/original/CDP_Global_Carbon_Price_report_2021.pdf
- US EPA social cost of greenhouse gases, central $190/t (2020$): https://www.epa.gov/system/files/documents/2023-12/epa_scghg_2023_report_final.pdf
- 2026 EV/EBITDA multiples by industry: https://eqvista.com/ebitda-multiples-by-industry/
- ESG performance and cost of debt (corporate bond evidence): https://www.sciencedirect.com/science/article/pii/S105752192500184X
- BLS Major Work Stoppages (annual): https://www.bls.gov/news.release/wkstp.htm
- NOAA hurricane climatology: https://www.aoml.noaa.gov/hrd-faq/

Maintained with the same discipline as SPEC_Pillar_Revenue_Impacts.md: change a parameter,
update its row and verdict in the same commit.

## 5. Change log

- **2026-09-02 (launch audit, AUDIT_Independent_Review_2026-09-01.md §8):** F-01
  reputation derived from the BU stock with a zero-baseline contagion (§2.6); F-02
  water dependency passed to the ESG-WACC as a 0–1 fraction, cost-of-capital base kept
  as a stock, exit-multiple coupling live for the first time (§2.2); F-03 CBAM
  surcharge $100,000/t → $100/t with a poison-value guard (§2.1). Golden traces
  (`backend/tests/golden/*.json`), the treasury-waterfall fingerprints and
  BALANCE_REPORT_BASELINE.md were rebaselined in the same change.
- **2026-09-02 (launch audit phase 3, §8 items 9–18):** F-04 four more penalties made
  per-round flows and F-04b cash pass-through for post-gross-profit transients (§2.3);
  F-05 CapEx debits treasury, excess amortises as a term loan (§2.2, §3.1); F-06 synergy
  OPEX saving capped at 6%/round (§2.3); F-07 crisis severity, imitation decay and the
  emergency-credit flag derived server-side (and in `dry_run.py`); F-08 stakeholder
  fatigue acts on each BU's reputation gain (it never fired before); F-09 the
  positional option_a/option_c CI bonus removed (options carry their configured
  deltas); F-10 NCD OPEX penalty in real dollars, SDG 6/14 thresholds on the 0–100
  scale (§2.3); F-11 F2 continuous NPC pressure default OFF (§3.4); F-12 one
  terminal-value formula (EBITDA floor and M_SDG on both paths); F-13 `ci_baseline_r1`
  stamped so the SBTi pathway has a baseline; F-41 the stakeholder-sentiment engine's
  missing functions implemented (it had raised ImportError, swallowed, on every commit).
  Goldens, fingerprints and BALANCE_REPORT_BASELINE.md rebaselined again.
