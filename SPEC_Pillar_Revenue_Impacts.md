# SPEC — Revenue Impacts for Pillar Options
**Date:** 2026-08-31 · **Branch:** `fix/pillar-impact-ownership` · **Status:** PROPOSAL — awaiting design-owner sign-off
**Motivation:** the pillar-ownership repair removed the leaked legacy `revenue_delta` that was
accidentally the only decision-driven revenue lever in pillar mode (§9 of
AUDIT_FULLCOURSE_RESPONSE_2026-08-31.md). This spec proposes deliberate `revenue_delta`
values for every pillar option, shown alongside each option's existing CI and SLO scores.

## 1. Semantics (proposed)

- `revenue_delta` on a pillar option is **per-BU, flat**, matching the legacy convention.
- The router aggregates it by summation across chosen areas (exactly like every other pillar
  impact key) and applies it in `_apply_pillar_aggregate_impacts`, **scaled by workforce
  effectiveness** and floored at 0 revenue — one new ~6-line block mirroring the SLO block.
- **R1–R9 only.** Round 10's pillar aggregates are skipped by design ruling (the mapped
  ending's full impact set is the single R10 source), so R10 pillar options carry no
  revenue values — the ending's own `revenue_delta` governs.
- Because five areas stack per round, per-option values are set at roughly ⅕–¼ of legacy
  per-option scale, so a coherent strategy's round total lands in the legacy band
  (≈ ±$0.2–0.9M per BU per round).

## 2. Calibration targets

- A committed "virtuous" strategy earns **≈ +$400–850K/BU/round** (peaking in R3 and R7,
  the heavy-capex rounds) — cumulative ≈ +$5M/BU of revenue base by R10, ≈ +$25M group.
  This deliberately recovers only part of the ~$190M terminal-value inflation the leak
  provided: the rest of that inflation came from compounding leaked CI/reputation and is
  not meant to return.
- A negligent strategy loses revenue in the rounds where the story supports demand loss
  (crisis mishandling in R4, workforce/community rupture in R9), and R6 keeps a deliberate
  temptation: reckless AI monetisation is the single biggest revenue pick (+$400K) with the
  reputation/flag consequences already in config.
- Zero is the default: compliance, governance, offsetting and HR-wellbeing options keep
  their value in their own channels (governance→WACC, burnout→OPEX, SLO→Instability
  Discount) rather than double-paying through revenue.

## 3. The table (proposed `rev` = revenue_delta, $/BU; ci / slo unchanged, shown for context)

### Round 1 — ESG Foundation Strategy
| Area | Option | Cost | CI | SLO | **rev (proposed)** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | renewable_ppa | −2.0M | −8 | 0 | **+100K** | Green power premium on contracts |
| energy | fossil_status_quo | 0 | +2 | 0 | **0** | — |
| energy | solar_capex | −4.0M | −12 | 0 | **+150K** | Energy cost edge → pricing headroom |
| operations | lean_process | −1.5M | 0 | 0 | **+150K** | Throughput gain |
| operations | digital_twin | −3.0M | 0 | 0 | **+250K** | Uptime + faster product cycles |
| operations | no_change | 0 | 0 | 0 | **0** | — |
| supply_chain | audit_suppliers | −2.5M | 0 | +3 | **0** | Risk play — pays via R4 severity |
| supply_chain | tier1_only | −0.5M | 0 | 0 | **0** | — |
| supply_chain | defer | 0 | 0 | 0 | **0** | Penalty channel is governance |
| offsetting | nature_based | −2.0M | 0 | 0 | **0** | Pays via NCD |
| offsetting | carbon_credits | −1.0M | 0 | 0 | **0** | — |
| offsetting | no_offsetting | 0 | 0 | 0 | **0** | Penalty channel is NCD |
| human_resources | dei_training | −2.0M | 0 | +4 | **0** | Pays via burnout/SLO |
| human_resources | leadership_dev | −1.5M | 0 | 0 | **0** | — |
| human_resources | no_hr_action | 0 | 0 | −1 | **0** | — |

### Round 2 — Double Materiality Investment
| Area | Option | Cost | CI | SLO | **rev** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | green_tariff | −1.5M | −6 | 0 | **+50K** | Modest green premium |
| energy | efficiency_upgrades | −2.5M | −4 | 0 | **+150K** | Unit-cost edge |
| energy | baseline | 0 | 0 | 0 | **0** | — |
| operations | materiality_board | −2.0M | 0 | 0 | **0** | Governance channel |
| operations | compliance_minimum | −0.5M | 0 | 0 | **0** | — |
| operations | ignore_framework | 0 | 0 | 0 | **0** | Governance +10 is the price |
| supply_chain | blockchain_trace | −3.5M | 0 | +5 | **+200K** | Traceability premium (B2B) |
| supply_chain | annual_report | −0.8M | 0 | 0 | **0** | — |
| supply_chain | no_transparency | 0 | 0 | 0 | **0** | — |
| offsetting | community_fund | −3.0M | 0 | +8 | **+100K** | Licence-to-grow in local markets |
| offsetting | employee_program | −1.5M | 0 | +3 | **0** | — |
| offsetting | no_mitigation | 0 | 0 | −2 | **0** | — |
| human_resources | people_analytics | −2.5M | 0 | 0 | **+100K** | Productivity |
| human_resources | engagement_survey | −0.5M | 0 | +2 | **0** | — |
| human_resources | no_hr_action | 0 | 0 | 0 | **0** | — |

### Round 3 — Scope 3 Decarbonisation
| Area | Option | Cost | CI | SLO | **rev** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | electrification | −5.0M | −15 | 0 | **+250K** | Low-carbon product line access |
| energy | hybrid_transition | −2.0M | −6 | 0 | **+100K** | Partial premium |
| energy | status_quo | 0 | +3 | 0 | **−100K** | Carbon-intensive SKUs losing buyers |
| operations | closed_loop | −4.0M | 0 | 0 | **+250K** | Material recovery revenue |
| operations | waste_reduction | −1.5M | 0 | 0 | **+100K** | Yield gain |
| operations | no_change | 0 | 0 | 0 | **0** | NCD +5 is the price |
| supply_chain | rapid_switch | −4.0M | −12 | 0 | **−150K** | Short-term supply disruption |
| supply_chain | green_bond | −2.0M | −6 | 0 | **+100K** | Funded supplier upgrades hold volume |
| supply_chain | offset_defer | −1.0M | 0 | 0 | **0** | — |
| offsetting | science_based | −3.0M | −8 | 0 | **+100K** | SBTi brand pull |
| offsetting | voluntary_offsets | −1.5M | 0 | 0 | **0** | — |
| offsetting | greenwash_risk | −0.2M | 0 | 0 | **0** | Greenwash engine is the price |
| human_resources | green_academy | −3.0M | 0 | +5 | **0** | Pays via readiness/synergy R7 |
| human_resources | safety_compliance | −0.5M | 0 | 0 | **0** | — |
| human_resources | no_hr_action | 0 | 0 | −2 | **0** | — |

### Round 4 — Reputation Crisis Response
| Area | Option | Cost | CI | SLO | **rev** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | green_pivot | −3.0M | −10 | 0 | **+150K** | Counter-narrative demand |
| energy | maintain | 0 | 0 | 0 | **0** | — |
| energy | cost_cutting | +1.5M | +5 | 0 | **−200K** | Quality/demand erosion |
| operations | full_transparency | −2.0M | 0 | +5 | **+200K** | Demand recovery |
| operations | pr_containment | −1.5M | 0 | −2 | **0** | — |
| operations | deny | 0 | 0 | −10 | **−400K** | Boycott dynamics |
| supply_chain | remediate_all | −5.0M | 0 | +10 | **+250K** | Retailer delistings reversed |
| supply_chain | targeted_fix | −1.5M | 0 | +3 | **+100K** | Partial recovery |
| supply_chain | ignore | 0 | 0 | −5 | **−200K** | B2B contract losses |
| offsetting | stakeholder_fund | −4.0M | 0 | +8 | **+100K** | Goodwill demand |
| offsetting | ngo_partnership | −1.0M | 0 | +3 | **+50K** | Credibility halo |
| offsetting | no_action | 0 | 0 | 0 | **−100K** | Lingering scandal drag |
| human_resources | crisis_counselling | −1.5M | 0 | +4 | **0** | Burnout channel |
| human_resources | overtime_push | +0.5M | 0 | −4 | **0** | Burnout +12 is the price |
| human_resources | no_hr_action | 0 | 0 | −2 | **0** | — |

### Round 5 — Climate Resilience
| Area | Option | Cost | CI | SLO | **rev** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | microgrids | −4.0M | 0 | 0 | **+100K** | Uptime through outages |
| energy | generator_backup | −1.0M | +3 | 0 | **+50K** | Partial continuity |
| energy | no_backup | 0 | 0 | 0 | **0** | Cyclone damage is the price |
| operations | hard_engineering | −8.0M | 0 | 0 | **0** | Resilience factor channel |
| operations | nature_based | −5.0M | 0 | 0 | **0** | Resilience + NCD channel |
| operations | insurance_only | −2.0M | 0 | 0 | **0** | — |
| supply_chain | diversify | −3.0M | 0 | 0 | **+100K** | Order continuity |
| supply_chain | nearshore | −2.0M | −3 | 0 | **+50K** | Lead-time edge |
| supply_chain | accept_risk | 0 | 0 | 0 | **0** | — |
| offsetting | adaptation_fund | −3.0M | 0 | +6 | **0** | SLO/burnout channel |
| offsetting | parametric_insurance | −1.5M | 0 | 0 | **0** | — |
| offsetting | no_adaptation | 0 | 0 | 0 | **0** | — |
| human_resources | emergency_team | −2.0M | 0 | +5 | **0** | — |
| human_resources | basic_ppe | −0.5M | 0 | +1 | **0** | — |
| human_resources | no_hr_action | 0 | 0 | −3 | **0** | — |

### Round 6 — AI Ethics & Technology
| Area | Option | Cost | CI | SLO | **rev** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | green_data_centers | −4.0M | −10 | 0 | **+150K** | Compute capacity headroom |
| energy | efficiency_optimize | −1.5M | −4 | 0 | **+100K** | Cost edge |
| energy | no_change | 0 | 0 | 0 | **0** | — |
| operations | ethical_overhaul | −8.0M | 0 | +15 | **+100K** | Trust → adoption (M_R flag is the real prize) |
| operations | quiet_patch | −1.0M | 0 | 0 | **0** | Governance +10 is the price |
| operations | monetise | 0 | 0 | 0 | **+400K** | THE temptation — rep −20 and ai_monetised costs follow |
| supply_chain | ai_supply_optimize | −3.0M | 0 | 0 | **+250K** | Fulfilment speed |
| supply_chain | manual_oversight | −1.0M | 0 | +3 | **0** | — |
| supply_chain | automate_fully | −0.5M | 0 | 0 | **+150K** | Cheap gains, governance +8 price |
| offsetting | digital_inclusion | −2.5M | 0 | +8 | **+50K** | New-market seeding |
| offsetting | scholarship_program | −1.0M | 0 | +4 | **0** | — |
| offsetting | no_social_invest | 0 | 0 | −2 | **0** | — |
| human_resources | responsible_ai_training | −2.5M | 0 | +5 | **+100K** | Deployment velocity, safely |
| human_resources | ai_upskilling | −0.8M | 0 | 0 | **+100K** | Productivity |
| human_resources | no_hr_action | 0 | 0 | −2 | **0** | — |

### Round 7 — Circular Economy Transition
| Area | Option | Cost | CI | SLO | **rev** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | waste_to_energy | −6.0M | −8 | 0 | **+200K** | Energy sales |
| energy | heat_recovery | −2.5M | −4 | 0 | **+100K** | Cost edge |
| energy | no_change | 0 | 0 | 0 | **0** | — |
| operations | full_circular | −10.0M | 0 | 0 | **+350K** | Resale/refurb product lines |
| operations | epr | −5.0M | 0 | 0 | **+150K** | Take-back service revenue |
| operations | minimum_compliance | −1.0M | 0 | 0 | **0** | — |
| supply_chain | reverse_logistics | −4.0M | 0 | 0 | **+150K** | Recovered-material margin |
| supply_chain | material_passport | −2.0M | 0 | 0 | **+100K** | Premium positioning |
| supply_chain | linear_model | 0 | 0 | 0 | **0** | NCD +5 is the price |
| offsetting | biodiversity_fund | −3.0M | 0 | 0 | **0** | NCD channel |
| offsetting | regenerative_ag | −2.0M | 0 | 0 | **+50K** | Agri premium |
| offsetting | no_nature | 0 | 0 | 0 | **0** | — |
| human_resources | circular_reskilling | −3.5M | 0 | +6 | **+100K** | Execution capacity (synergy modifier too) |
| human_resources | cross_training | −1.0M | 0 | 0 | **+50K** | Flexibility |
| human_resources | no_hr_action | 0 | 0 | −2 | **0** | — |

### Round 8 — Water Scarcity Response
| Area | Option | Cost | CI | SLO | **rev** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | dry_cooling | −5.0M | 0 | 0 | **+50K** | Continuity under stress |
| energy | water_recycling | −3.0M | 0 | 0 | **+100K** | Continuity + cost edge |
| energy | no_water_action | 0 | 0 | 0 | **0** | Water-stress engine is the price |
| operations | equitable | −12.0M | 0 | +5 | **+100K** | All lines keep running |
| operations | prioritize_electronics | −4.0M | 0 | 0 | **+150K** | Flagship line protected — licence cost elsewhere |
| operations | desalination | −30.0M | 0 | 0 | **0** | Deferred NCD −30 is the payoff |
| supply_chain | water_footprint_audit | −2.0M | 0 | 0 | **0** | — |
| supply_chain | water_efficient_suppliers | −3.0M | 0 | 0 | **+50K** | Supply continuity |
| supply_chain | no_supply_change | 0 | 0 | 0 | **0** | — |
| offsetting | watershed_restore | −4.0M | 0 | +5 | **+50K** | Basin licence |
| offsetting | community_water | −2.0M | 0 | +8 | **+100K** | Community-backed operations |
| offsetting | no_stewardship | 0 | 0 | −3 | **−100K** | Community friction |
| human_resources | water_steward_training | −2.0M | 0 | +4 | **+50K** | Efficient operations |
| human_resources | shift_rotation | −0.7M | 0 | 0 | **0** | — |
| human_resources | no_hr_action | 0 | 0 | 0 | **0** | — |

### Round 9 — Just Transition Strategy
| Area | Option | Cost | CI | SLO | **rev** | Rationale |
|---|---|---:|---:|---:|---:|---|
| energy | green_reskilling | −5.0M | 0 | +10 | **+150K** | Productive redeployment |
| energy | partial_retraining | −2.0M | 0 | +4 | **+50K** | Partial capability retention |
| energy | no_retraining | −0.5M | 0 | −8 | **−100K** | Capability loss |
| operations | managed_transition | −12.0M | 0 | +10 | **+100K** | Orderly wind-down protects lines |
| operations | immediate_closure | +5.0M | 0 | −20 | **−400K** | Disruption (strike engine stacks) |
| operations | automation_pivot | −8.0M | 0 | −5 | **+250K** | Efficiency, at licence cost |
| supply_chain | local_ecosystem | −3.0M | 0 | +6 | **+100K** | Local demand loyalty |
| supply_chain | cooperative_model | −2.0M | 0 | +8 | **+50K** | Stable partners |
| supply_chain | offshore | +2.0M | 0 | −10 | **+200K** | Cheaper supply — SLO −10 is the price |
| offsetting | community_fund | −20.0M | 0 | +18 | **+100K** | Licence-to-operate dividend |
| offsetting | transition_bonds | −5.0M | 0 | +6 | **+50K** | — |
| offsetting | no_community | 0 | 0 | −5 | **−100K** | Community boycott drag |
| human_resources | full_severance_redeploy | −6.0M | 0 | +10 | **+100K** | Retention → delivery |
| human_resources | statutory_minimum | −1.0M | 0 | −3 | **0** | — |
| human_resources | no_hr_action | 0 | 0 | −8 | **−100K** | Attrition hits delivery |

### Round 10 — Year 5 Corporate Destiny
All fifteen R10 pillar options: **rev = n/a** — by the 2026-08-31 ruling, R10 pillar
aggregates are skipped and the mapped A/B/C ending's full impact set (including its
`revenue_delta`) is the single source.

## 4. Strategy sanity sums (per BU per round, effectiveness = 1.0)

| Round | Virtuous picks | Negligent picks |
|---|---:|---:|
| R1 | +400K | 0 |
| R2 | +550K | 0 |
| R3 | +700K | −100K |
| R4 | +700K | −900K |
| R5 | +200K | 0 |
| R6 | +650K | +550K (temptation round, by design) |
| R7 | +850K | 0 |
| R8 | +400K | −100K |
| R9 | +600K | −500K |
| **Cumulative** | **≈ +5.0M/BU** | **≈ −1.05M/BU** |

## 5. Implementation checklist (once signed off)

1. Add the `revenue_delta` values above to `pillar_configs.py` (R1–R9 only).
2. Add a revenue block to `router._apply_pillar_aggregate_impacts` (effectiveness-scaled,
   flat per BU, floor at 0), mirroring the SLO block.
3. Extend `tests/test_pillar_impact_ownership.py`: the helper unit test asserts the revenue
   block's scaling; the R1–R9 ownership tests already guarantee no double-application.
4. Re-run the pillar-game harness before/after and record the new trajectory next to the
   §9 numbers; expect closing treasury to recover into a legacy-comparable band while
   remaining below the leaky pre-fix figures.
5. Rebaseline any multi_toggles goldens that pin financials (test_treasury_waterfall
   residuals if they tighten later). Cohort-boundary shipping, as with the parent branch.
