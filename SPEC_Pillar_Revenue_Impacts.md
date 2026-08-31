# SPEC — Revenue Impacts for Pillar Options (v2, realism-reviewed)
**Date:** 2026-08-31 · **Branch:** `fix/pillar-impact-ownership` · **Status:** v2 IMPLEMENTED — wired into pillar_configs.py + router; validation trajectory in §7
**Motivation:** the pillar-ownership repair removed the leaked legacy `revenue_delta` that was
accidentally the only decision-driven revenue lever in pillar mode (§9 of
AUDIT_FULLCOURSE_RESPONSE_2026-08-31.md). v1 proposed values by internal calibration only;
v2 re-rates each against published business evidence. Changed cells show v1 struck through.

## 1. Semantics (unchanged from v1)

- `revenue_delta` is **per-BU, flat**, matching the legacy convention; router-aggregated,
  **effectiveness-scaled**, floored at 0, applied in `_apply_pillar_aggregate_impacts`.
- **R1–R9 only** — R10's mapped ending owns its own revenue by design ruling.
- Reading the numbers: BU revenue_base runs ≈ $10–15M, so **+100K ≈ 0.8% of BU revenue**
  (that column below assumes $12M). Because a `revenue_base` change PERSISTS and compounds
  through every remaining round, each value must be read as a **recurring run-rate change**,
  not a one-off — which is why transient effects are rated small.

## 2. Realism benchmarks used

| Effect class | Real-world evidence | Implication for values |
|---|---|---|
| Green/sustainability demand | NYU Stern CSB × Circana Sustainable Market Share Index: sustainability-marketed products hold >25% of US CPG share and grow roughly twice as fast as conventional, contributing ~30% of category growth from a much smaller base | Green-positioning uplift of **+0.4–2%/yr** of revenue is defensible; anything larger is not, for a diversified industrial group |
| Boycotts & scandals | Boycott research (Northwestern/King; Wharton) finds most boycotts move sales <1% — reputational/stock damage dominates — but *severe, sustained* branded scandals hit affected lines 5–25% (VW, Bud Light class) | Routine negligence ≈ −0.5–1%; an active in-story crisis mishandled (R4 Deny) justifies **−3–4%**; everyday "no action" options should NOT carry big revenue penalties |
| Supply-chain disruption | Economist Impact / Coupa / Interos-class studies: disruption costs average ~6–10% of revenue in severe years; ~$16M/yr for large firms | An abrupt supplier switch is a real disruption: **−2–3%** short-term, not −1% |
| Circular revenue | Philips reports ~20–25% of sales as circular revenue (multi-year build); Caterpillar Reman is a multi-billion line (~7% of group) | A flagship circular launch at **+2–3%** in its first year is realistic; adjacent circular plays 0.5–1.5% |
| Cost-side programmes | Lean, automation, energy efficiency, offshoring, people analytics primarily move **cost**, not revenue | Their revenue values are trimmed to small "capacity-release" proxies (see §5 note 1) |
| Avoided-loss overlaps | The engine already models cyclone damage (R5), water stress (R8) and strikes (R9) as separate penalty channels | Resilience/continuity options keep revenue ≈ 0–0.8% to avoid double-counting the same protection |

## 3. The table (rev = proposed revenue_delta $/BU; struck value = v1 where changed; % = share of $12M BU revenue)

### Round 1 — ESG Foundation Strategy
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale (realism-reviewed) |
|---|---|---:|---:|---:|---:|---:|---|
| energy | renewable_ppa | −2.0M | −8 | 0 | **+100K** | 0.8% | RE100-class B2B customers require green suppliers — retention, not premium |
| energy | fossil_status_quo | 0 | +2 | 0 | **0** | — | — |
| energy | solar_capex | −4.0M | −12 | 0 | ~~+150K~~ **+100K** | 0.8% | Energy is cost-side; revenue only via green-qualification wins |
| operations | lean_process | −1.5M | 0 | 0 | ~~+150K~~ **+100K** | 0.8% | Lean is mostly cost; capacity release converts partially |
| operations | digital_twin | −3.0M | 0 | 0 | ~~+250K~~ **+150K** | 1.2% | Digital uplift of 3–5% is multi-year; year-one ≈ 1% |
| operations | no_change | 0 | 0 | 0 | **0** | — | — |
| supply_chain | audit_suppliers | −2.5M | 0 | +3 | **0** | — | Risk play — pays via R4 severity |
| supply_chain | tier1_only | −0.5M | 0 | 0 | **0** | — | — |
| supply_chain | defer | 0 | 0 | 0 | **0** | — | Governance is the price |
| offsetting | nature_based | −2.0M | 0 | 0 | **0** | — | NCD channel |
| offsetting | carbon_credits | −1.0M | 0 | 0 | **0** | — | — |
| offsetting | no_offsetting | 0 | 0 | 0 | **0** | — | NCD +3 is the price |
| human_resources | dei_training | −2.0M | 0 | +4 | **0** | — | Burnout/SLO channel |
| human_resources | leadership_dev | −1.5M | 0 | 0 | **0** | — | — |
| human_resources | no_hr_action | 0 | 0 | −1 | **0** | — | — |

### Round 2 — Double Materiality Investment
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale |
|---|---|---:|---:|---:|---:|---:|---|
| energy | green_tariff | −1.5M | −6 | 0 | **+50K** | 0.4% | Modest green premium — in NYU Stern band |
| energy | efficiency_upgrades | −2.5M | −4 | 0 | ~~+150K~~ **+100K** | 0.8% | Cost-side proxy, trimmed |
| energy | baseline | 0 | 0 | 0 | **0** | — | — |
| operations | materiality_board | −2.0M | 0 | 0 | **0** | — | Governance channel |
| operations | compliance_minimum | −0.5M | 0 | 0 | **0** | — | — |
| operations | ignore_framework | 0 | 0 | 0 | **0** | — | Governance +10 is the price |
| supply_chain | blockchain_trace | −3.5M | 0 | +5 | ~~+200K~~ **+100K** | 0.8% | Traceability premium applies only to covered SKUs — blended <1% |
| supply_chain | annual_report | −0.8M | 0 | 0 | **0** | — | — |
| supply_chain | no_transparency | 0 | 0 | 0 | **0** | — | — |
| offsetting | community_fund | −3.0M | 0 | +8 | ~~+100K~~ **+50K** | 0.4% | Licence-to-grow is real but slow-burn |
| offsetting | employee_program | −1.5M | 0 | +3 | **0** | — | — |
| offsetting | no_mitigation | 0 | 0 | −2 | **0** | — | — |
| human_resources | people_analytics | −2.5M | 0 | 0 | ~~+100K~~ **0** | — | Pure cost-side — see §5 note 1 |
| human_resources | engagement_survey | −0.5M | 0 | +2 | **0** | — | — |
| human_resources | no_hr_action | 0 | 0 | 0 | **0** | — | — |

### Round 3 — Scope 3 Decarbonisation
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale |
|---|---|---:|---:|---:|---:|---:|---|
| energy | electrification | −5.0M | −15 | 0 | ~~+250K~~ **+200K** | 1.7% | Low-carbon procurement access (green-steel-class premiums on niche volumes) |
| energy | hybrid_transition | −2.0M | −6 | 0 | **+100K** | 0.8% | Partial qualification |
| energy | status_quo | 0 | +3 | 0 | **−100K** | −0.8% | CDP-style buyer requirements delisting carbon-intensive SKUs |
| operations | closed_loop | −4.0M | 0 | 0 | **+250K** | 2.1% | Recovered-material sales — first-year circular line |
| operations | waste_reduction | −1.5M | 0 | 0 | ~~+100K~~ **+50K** | 0.4% | Mostly yield/cost |
| operations | no_change | 0 | 0 | 0 | **0** | — | NCD +5 is the price |
| supply_chain | rapid_switch | −4.0M | −12 | 0 | ~~−150K~~ **−300K** | −2.5% | Disruption studies: severe-year costs run 6–10% of revenue; a forced switch is −2–3% short-term |
| supply_chain | green_bond | −2.0M | −6 | 0 | ~~+100K~~ **0** | — | A financing instrument moves cost of capital, not demand — NCD −10 already rewards it |
| supply_chain | offset_defer | −1.0M | 0 | 0 | **0** | — | — |
| offsetting | science_based | −3.0M | −8 | 0 | ~~+100K~~ **+50K** | 0.4% | SBTi is B2B qualification, weak direct-demand evidence |
| offsetting | voluntary_offsets | −1.5M | 0 | 0 | **0** | — | — |
| offsetting | greenwash_risk | −0.2M | 0 | 0 | **0** | — | Greenwash engine is the price |
| human_resources | green_academy | −3.0M | 0 | +5 | **0** | — | Pays via readiness/synergy R7 |
| human_resources | safety_compliance | −0.5M | 0 | 0 | **0** | — | — |
| human_resources | no_hr_action | 0 | 0 | −2 | **0** | — | — |

### Round 4 — Reputation Crisis Response (active scandal — larger swings are evidence-consistent)
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale |
|---|---|---:|---:|---:|---:|---:|---|
| energy | green_pivot | −3.0M | −10 | 0 | ~~+150K~~ **+100K** | 0.8% | Counter-narrative demand is transient; trimmed for persistence |
| energy | maintain | 0 | 0 | 0 | **0** | — | — |
| energy | cost_cutting | +1.5M | +5 | 0 | **−200K** | −1.7% | Quality erosion mid-crisis |
| operations | full_transparency | −2.0M | 0 | +5 | **+200K** | 1.7% | Demand recovery vs the declining counterfactual |
| operations | pr_containment | −1.5M | 0 | −2 | **0** | — | — |
| operations | deny | 0 | 0 | −10 | **−400K** | −3.3% | Severe-scandal band (VW/Bud Light class hits 5–25% on affected lines; −3.3% blended is conservative-realistic) |
| supply_chain | remediate_all | −5.0M | 0 | +10 | **+250K** | 2.1% | Retailer delistings reversed |
| supply_chain | targeted_fix | −1.5M | 0 | +3 | **+100K** | 0.8% | Partial recovery |
| supply_chain | ignore | 0 | 0 | −5 | **−200K** | −1.7% | B2B contract losses during an active scandal |
| offsetting | stakeholder_fund | −4.0M | 0 | +8 | ~~+100K~~ **+50K** | 0.4% | Goodwill converts slowly |
| offsetting | ngo_partnership | −1.0M | 0 | +3 | **+50K** | 0.4% | Credibility halo |
| offsetting | no_action | 0 | 0 | 0 | **−100K** | −0.8% | Lingering scandal drag — most boycotts move sales <1% |
| human_resources | crisis_counselling | −1.5M | 0 | +4 | **0** | — | Burnout channel |
| human_resources | overtime_push | +0.5M | 0 | −4 | **0** | — | Burnout +12 is the price |
| human_resources | no_hr_action | 0 | 0 | −2 | **0** | — | — |

### Round 5 — Climate Resilience (avoided-loss round — the cyclone engine already charges damage)
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale |
|---|---|---:|---:|---:|---:|---:|---|
| energy | microgrids | −4.0M | 0 | 0 | ~~+100K~~ **+50K** | 0.4% | Uptime revenue kept minimal — cyclone damage is the main channel |
| energy | generator_backup | −1.0M | +3 | 0 | ~~+50K~~ **0** | — | Same overlap; CI +3 already prices it |
| energy | no_backup | 0 | 0 | 0 | **0** | — | Cyclone damage is the price |
| operations | hard_engineering | −8.0M | 0 | 0 | **0** | — | Resilience-factor channel |
| operations | nature_based | −5.0M | 0 | 0 | **0** | — | Resilience + NCD channel |
| operations | insurance_only | −2.0M | 0 | 0 | **0** | — | — |
| supply_chain | diversify | −3.0M | 0 | 0 | **+100K** | 0.8% | Order continuity — customers reward reliable suppliers |
| supply_chain | nearshore | −2.0M | −3 | 0 | **+50K** | 0.4% | Lead-time edge |
| supply_chain | accept_risk | 0 | 0 | 0 | **0** | — | — |
| offsetting | adaptation_fund | −3.0M | 0 | +6 | **0** | — | SLO/burnout channel |
| offsetting | parametric_insurance | −1.5M | 0 | 0 | **0** | — | — |
| offsetting | no_adaptation | 0 | 0 | 0 | **0** | — | — |
| human_resources | emergency_team | −2.0M | 0 | +5 | **0** | — | — |
| human_resources | basic_ppe | −0.5M | 0 | +1 | **0** | — | — |
| human_resources | no_hr_action | 0 | 0 | −3 | **0** | — | — |

### Round 6 — AI Ethics & Technology
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale |
|---|---|---:|---:|---:|---:|---:|---|
| energy | green_data_centers | −4.0M | −10 | 0 | ~~+150K~~ **+100K** | 0.8% | Capacity headroom only converts if compute-constrained |
| energy | efficiency_optimize | −1.5M | −4 | 0 | ~~+100K~~ **+50K** | 0.4% | Cost-side proxy |
| energy | no_change | 0 | 0 | 0 | **0** | — | — |
| operations | ethical_overhaul | −8.0M | 0 | +15 | **+100K** | 0.8% | Trust → adoption; the M_R flag is the real prize |
| operations | quiet_patch | −1.0M | 0 | 0 | **0** | — | Governance +10 is the price |
| operations | monetise | 0 | 0 | 0 | **+400K** | 3.3% | THE temptation — software AI monetisation of 5–15% is documented; legacy config gave +10M on one BU, so this is conservative. Rep −20 + ai_monetised costs follow |
| supply_chain | ai_supply_optimize | −3.0M | 0 | 0 | ~~+250K~~ **+150K** | 1.2% | Fill-rate/availability gains ≈ 1%, rest is cost |
| supply_chain | manual_oversight | −1.0M | 0 | +3 | **0** | — | — |
| supply_chain | automate_fully | −0.5M | 0 | 0 | ~~+150K~~ **+50K** | 0.4% | Automation is cost-side; governance +8 stays the real price |
| offsetting | digital_inclusion | −2.5M | 0 | +8 | **+50K** | 0.4% | New-market seeding |
| offsetting | scholarship_program | −1.0M | 0 | +4 | **0** | — | — |
| offsetting | no_social_invest | 0 | 0 | −2 | **0** | — | — |
| human_resources | responsible_ai_training | −2.5M | 0 | +5 | ~~+100K~~ **+50K** | 0.4% | Deployment velocity, safely |
| human_resources | ai_upskilling | −0.8M | 0 | 0 | ~~+100K~~ **+50K** | 0.4% | Productivity is mostly cost-side |
| human_resources | no_hr_action | 0 | 0 | −2 | **0** | — | — |

### Round 7 — Circular Economy Transition (best-evidenced revenue round)
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale |
|---|---|---:|---:|---:|---:|---:|---|
| energy | waste_to_energy | −6.0M | −8 | 0 | ~~+200K~~ **+150K** | 1.2% | Energy sales — modest at industrial scale |
| energy | heat_recovery | −2.5M | −4 | 0 | ~~+100K~~ **+50K** | 0.4% | Cost-side proxy |
| energy | no_change | 0 | 0 | 0 | **0** | — | — |
| operations | full_circular | −10.0M | 0 | 0 | **+350K** | 2.9% | First-year flagship circular line — Philips-class programmes reach 20–25% of sales over years; 3% year one is realistic |
| operations | epr | −5.0M | 0 | 0 | ~~+150K~~ **+100K** | 0.8% | EPR is compliance-dominant; take-back service revenue is small |
| operations | minimum_compliance | −1.0M | 0 | 0 | **0** | — | — |
| supply_chain | reverse_logistics | −4.0M | 0 | 0 | **+150K** | 1.2% | Recovered-material margin (Cat-Reman-class economics) |
| supply_chain | material_passport | −2.0M | 0 | 0 | ~~+100K~~ **+50K** | 0.4% | Premium positioning, niche coverage |
| supply_chain | linear_model | 0 | 0 | 0 | **0** | — | NCD +5 is the price |
| offsetting | biodiversity_fund | −3.0M | 0 | 0 | **0** | — | NCD channel |
| offsetting | regenerative_ag | −2.0M | 0 | 0 | **+50K** | 0.4% | Agri premium |
| offsetting | no_nature | 0 | 0 | 0 | **0** | — | — |
| human_resources | circular_reskilling | −3.5M | 0 | +6 | ~~+100K~~ **+50K** | 0.4% | Execution capacity — synergy modifier already rewards this |
| human_resources | cross_training | −1.0M | 0 | 0 | ~~+50K~~ **0** | — | Cost-side |
| human_resources | no_hr_action | 0 | 0 | −2 | **0** | — | — |

### Round 8 — Water Scarcity Response (licence round — real cases are lumpy, engine already models stress)
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale |
|---|---|---:|---:|---:|---:|---:|---|
| energy | dry_cooling | −5.0M | 0 | 0 | **+50K** | 0.4% | Continuity under stress |
| energy | water_recycling | −3.0M | 0 | 0 | ~~+100K~~ **+50K** | 0.4% | Overlaps water-stress engine — kept minimal |
| energy | no_water_action | 0 | 0 | 0 | **0** | — | Water-stress engine is the price |
| operations | equitable | −12.0M | 0 | +5 | **+100K** | 0.8% | All lines keep running |
| operations | prioritize_electronics | −4.0M | 0 | 0 | **+150K** | 1.2% | Flagship line protected — SLO severe-drop is the price elsewhere |
| operations | desalination | −30.0M | 0 | 0 | **0** | — | Deferred NCD −30 and payback revenue already modelled |
| supply_chain | water_footprint_audit | −2.0M | 0 | 0 | **0** | — | — |
| supply_chain | water_efficient_suppliers | −3.0M | 0 | 0 | **+50K** | 0.4% | Supply continuity |
| supply_chain | no_supply_change | 0 | 0 | 0 | **0** | — | — |
| offsetting | watershed_restore | −4.0M | 0 | +5 | **+50K** | 0.4% | Basin licence |
| offsetting | community_water | −2.0M | 0 | +8 | **+100K** | 0.8% | Community-backed operations (real licence failures — Tuticorin-class — are total shutdowns; the marginal value stays small and the SLO engine carries the catastrophe) |
| offsetting | no_stewardship | 0 | 0 | −3 | **−100K** | −0.8% | Community friction |
| human_resources | water_steward_training | −2.0M | 0 | +4 | **+50K** | 0.4% | Efficient operations |
| human_resources | shift_rotation | −0.7M | 0 | 0 | **0** | — | — |
| human_resources | no_hr_action | 0 | 0 | 0 | **0** | — | — |

### Round 9 — Just Transition Strategy
| Area | Option | Cost | CI | SLO | rev v2 | % | Rationale |
|---|---|---:|---:|---:|---:|---:|---|
| energy | green_reskilling | −5.0M | 0 | +10 | **+150K** | 1.2% | Productive redeployment |
| energy | partial_retraining | −2.0M | 0 | +4 | **+50K** | 0.4% | Partial capability retention |
| energy | no_retraining | −0.5M | 0 | −8 | **−100K** | −0.8% | Capability loss |
| operations | managed_transition | −12.0M | 0 | +10 | **+100K** | 0.8% | Orderly wind-down protects order book |
| operations | immediate_closure | +5.0M | 0 | −20 | **−400K** | −3.3% | Abrupt closure disrupts delivery and order book; note the strike engine can stack a further probabilistic revenue-zeroing — deliberate double jeopardy, flagged |
| operations | automation_pivot | −8.0M | 0 | −5 | ~~+250K~~ **+150K** | 1.2% | Automation is mostly cost-side; capacity release converts partially |
| supply_chain | local_ecosystem | −3.0M | 0 | +6 | **+100K** | 0.8% | Local demand loyalty |
| supply_chain | cooperative_model | −2.0M | 0 | +8 | **+50K** | 0.4% | Stable partners |
| supply_chain | offshore | +2.0M | 0 | −10 | ~~+200K~~ **+100K** | 0.8% | Offshoring is margin, not demand; small revenue proxy + the +2M cash inflow keeps the temptation |
| offsetting | community_fund | −20.0M | 0 | +18 | **+100K** | 0.8% | Licence-to-operate dividend |
| offsetting | transition_bonds | −5.0M | 0 | +6 | **+50K** | 0.4% | — |
| offsetting | no_community | 0 | 0 | −5 | **−100K** | −0.8% | Community boycott drag |
| human_resources | full_severance_redeploy | −6.0M | 0 | +10 | **+100K** | 0.8% | Retention → delivery |
| human_resources | statutory_minimum | −1.0M | 0 | −3 | **0** | — | — |
| human_resources | no_hr_action | 0 | 0 | −8 | **−100K** | −0.8% | Attrition hits delivery |

### Round 10 — Year 5 Corporate Destiny
All fifteen R10 pillar options: **rev = n/a** — the mapped A/B/C ending's full impact set
(including its `revenue_delta`) is the single source, by the 2026-08-31 ruling.

## 4. Strategy sanity sums, v2 (per BU per round, effectiveness = 1.0)

| Round | Virtuous picks | v1 | Negligent picks | v1 |
|---|---:|---:|---:|---:|
| R1 | +250K | +400K | 0 | 0 |
| R2 | +250K | +550K | 0 | 0 |
| R3 | +500K | +700K | −100K | −100K |
| R4 | +600K | +700K | −900K | −900K |
| R5 | +150K | +200K | 0 | 0 |
| R6 | +450K | +650K | +450K | +550K |
| R7 | +750K | +850K | 0 | 0 |
| R8 | +350K | +400K | −100K | −100K |
| R9 | +550K | +600K | −600K | −500K |
| **Cumulative** | **≈ +3.85M/BU** | +5.0M | **≈ −1.25M/BU** | −1.05M |

Net effect of the review: the virtuous run-rate comes down ~23% (v1 over-credited
cost-side programmes as revenue), the negligent path gets slightly harsher, and the
biggest single swings stay where the evidence is strongest — the R4 crisis, the R7
circular launch, and the R6 temptation.

## 5. Cross-cutting realism notes

1. **Cost-side effects modelled as revenue (deliberate proxy).** Lean, automation,
   energy efficiency, offshoring and analytics really move OPEX, not demand. v2 trims
   them to small capacity-release proxies. The more faithful model is an `opex_delta`
   pillar key applied alongside revenue in `_apply_pillar_aggregate_impacts` — recommended
   as a follow-up if the teaching goal includes cost-structure strategy; rows marked
   "cost-side" above would migrate there at roughly 2–3× the revenue-proxy magnitude.
2. **Persistence.** revenue_base deltas persist and compound; every value is a run-rate
   change. Transient effects (crisis counter-narratives, goodwill) are rated small for
   exactly this reason.
3. **No double-counting of avoided losses.** R5/R8/R9 already carry cyclone damage, the
   water-stress engine and the strike engine; their options keep revenue ≈ 0–1.2%.
4. **The R6 temptation is calibrated, not accidental.** Monetise (+3.3%, zero cost) beats
   every virtuous R6 combination on immediate revenue — matching real AI-monetisation
   economics — and the config already charges it: rep −20, `ai_monetised` → $3M EU AI Act
   cost + governance +5 from R7, and black-swan probability +8%.

## 6. Implementation checklist (unchanged from v1)

1. Add the v2 `revenue_delta` values to `pillar_configs.py` (R1–R9 only).
2. Add a revenue block to `router._apply_pillar_aggregate_impacts` (effectiveness-scaled,
   flat per BU, floor at 0), mirroring the SLO block.
3. Extend `tests/test_pillar_impact_ownership.py` for the revenue block's scaling.
4. Re-run the pillar-game harness and record the trajectory next to the §9 numbers.
5. Rebaseline multi_toggles goldens if any tighten. Cohort-boundary shipping.

## 7. Validation trajectory (implemented)

Same 10-round pillar policy and seed as the §9 baselines in
AUDIT_FULLCOURSE_RESPONSE_2026-08-31.md:

| Variant | Closing treasury | Terminal value | M_R |
|---|---:|---:|---:|
| Pre-fix (leaky legacy stacking) | +$53.6M | +$65.7M | 1.58 |
| Ownership fix, no revenue lever | −$137.5M | −$214.1M | 1.58 |
| **Ownership fix + SPEC v2 revenue** | **+$13.8M** | **+$61.1M** | **1.58** |

Terminal value lands within 7% of what the leaky engine produced — pillar-cohort
difficulty is comparable to what the last thirty cohorts experienced — while the
cash game is deliberately tighter (+$13.8M vs +$53.6M closing treasury) and every
dollar now comes from designed, evidence-rated levers instead of the accident.
Implementation notes: revenue is applied LAST in `_apply_pillar_aggregate_impacts`
so the revenue-weighted deltas keep the round's incoming distribution as their
basis; R7's waste_to_energy × full_circular mutual exclusivity correctly reverses
one side's revenue along with its other impacts (covered by test).
