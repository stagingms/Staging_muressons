# Muressons Global Corporation — Simulation Context Summary

> **Purpose**: This is the canonical, living reference document for the complete Muressons simulation.
> It covers the narrative world, all 10 main rounds, decision pillars, ending pathways, side tracks,
> business unit profiles, scoring mechanics, and supporting engine systems.
> Any AI assistant, new developer, or facilitator should read this file *first*.

---

## Table of Contents

1. [Simulation Overview](#1-simulation-overview)
2. [Business Units](#2-business-units)
3. [Game State KPIs](#3-game-state-kpis)
4. [Main Simulation — 10 Rounds](#4-main-simulation--10-rounds)
5. [Decision Pillars (Multi-Toggle Paradigm)](#5-decision-pillars-multi-toggle-paradigm)
6. [Ending Pathways (5 Alternate Ends)](#6-ending-pathways-5-alternate-ends)
7. [Side Tracks (6 Parallel Mini-Simulations)](#7-side-tracks-6-parallel-mini-simulations)
8. [Terminal Valuation & Archetypes](#8-terminal-valuation--archetypes)
9. [Stochastic Systems](#9-stochastic-systems)
10. [Black Swan Events](#10-black-swan-events)
11. [Flag Dependency Graph](#11-flag-dependency-graph)
12. [Core Engine Modules](#12-core-engine-modules)
13. [Simulation Config & Tuneable Parameters](#13-simulation-config--tuneable-parameters)
14. [Industry Verticals (BU Substitutions)](#14-industry-verticals-bu-substitutions)
15. [Role Hierarchy: God Mode → Facilitator → Player](#15-role-hierarchy-god-mode--facilitator--player)
16. [Runtime Dependency Map](#16-runtime-dependency-map)
17. [Codebase Provenance & Refactor Log](#17-codebase-provenance--refactor-log)

---

## 1. Simulation Overview

**Name**: Muressons Global Corporation  
**Format**: Multi-round ESG & sustainability strategy simulation for executive/MBA education  
**Duration**: 10 main rounds (each represents a 6-month decision period, spanning 5 years)  
**Paradigm**: Dual-track — main simulation runs sequentially, side tracks can be injected at any point  
**Starting Date**: Simulation opens at Year 0; R10 represents the Year 5 terminal-valuation moment  

### Core Learning Objectives
- Double materiality and CSRD/ESRS compliance decision-making  
- Scope 1/2/3 carbon accounting under real supply-chain pressure  
- Crisis management, stakeholder fatigue, and social licence to operate  
- Terminal valuation as a function of ESG quality (the Regenerative Multiple, M_R)  
- Trade-offs between short-term cash extraction and long-run enterprise value  

### Simulation Architecture
```
God Mode (platform admin)
  └── Facilitator (session designer)
        └── Player (team making decisions)
              ├── Main Simulation (10 rounds)
              │     ├── Round Crisis Decision (A/B/C)
              │     └── Pillar Decisions (5 areas × 3 options each)
              └── Side Tracks (1–6 parallel tracks, assigned by facilitator)
                    ├── Supply Chain
                    ├── Ethics & Sustainability
                    ├── Stakeholder Management
                    ├── Sustainability Reporting
                    ├── Corporate SDG Deep Track
                    └── BRSR NGRBC Deep Dive
```

---

## 2. Business Units

Muressons is a conglomerate with **4 active BU slots**. Each slot can be filled by a default BU or an industry vertical substitute. All values are initialised at session start.

### Default 4-Slot Lineup

| BU | Icon | Revenue (USD) | OPEX (USD) | Carbon Intensity (tCO₂e/\$M rev) | Water Dependency | Natural Capital Debt | Governance Risk |
|---|---|---|---|---|---|---|---|
| **Pharma** | 💊 | $18,000,000 | $12,000,000 | 35 | 82 | 120 | 15 |
| **Electronics** | ⚡ | $16,500,000 | $11,500,000 | 72 | 58 | 200 | 20 |
| **Consumer Goods** | 🛒 | $10,500,000 | $7,500,000 | 48 | 65 | 150 | 10 |
| **Software** | 💻 | $8,500,000 | $5,500,000 | 12 | 12 | 30 | 25 |

**All BUs start with:**  Social Licence Score = 50 · Reputation Score = 55 · Burnout Index = 10 · VRIO Advantage = 0.80

### Key BU Mechanics
- **Electronics** is the `blindspot` BU — Round 1 audit decisions determine whether `electronics_blindspot` flag is set, which doubles crisis severity in Round 4.
- **Carbon Intensity** is the primary emissions metric: `tonnes_CO₂e = CI × revenue / 1,000,000`.
- **Revenue-weighted group avg CI** = Σ(CI × rev) / Σrev — used for terminal valuation carbon tax.
- **Natural Capital Debt (NCD)** accumulates if green investments are not made; it raises the cost of debt.

---

## 3. Game State KPIs

| KPI | Scope | Range | Notes |
|---|---|---|---|
| `corporate_treasury` | Group | Starts $50M | Can go negative (crisis) |
| `group_reputation` | Group | 0–100 | S-curve contagion model |
| `synergy_multiplier` | Group | 0–2.0 | Diminishing-returns sqrt model |
| `cost_of_capital` / WACC | Group | 0.05–0.20+ | NCD and macro rate environment |
| `workforce_readiness` | Group | 0–100 | Starts 50; affects terminal valuation |
| `carbon_intensity` | Per BU | ≥0 | tCO₂e per $1M revenue |
| `social_license_score` (SLO) | Per BU | 0–100 | Stakeholder fatigue engine |
| `staff_burnout_index` | Per BU | 0–100 | OPEX quadratic penalty above 20 |
| `natural_capital_debt` | Per BU | ≥0 | Raises cost of debt by 0.01% per unit |
| `governance_risk_score` | Per BU | 0–100 | Greenwash probability, litigation risk |
| `vrio_advantage` | Per BU | 0–1.0 | Decays 2%/round unless reinvested |
| `sdg_impact_score` | Group | −11 to 105 | From Corporate SDG side track only |

---

## 4. Main Simulation — 10 Rounds

Each round has:
1. **A thematic crisis** with three strategic response options (A/B/C).
2. **Five pillar decisions** (Energy, Operations, Supply Chain, Offsetting, Human Resources) — each with 3 options.
3. **Post-round engine calculations** (see §12).
4. **Foreshadowing events** injected from Rounds 5–8 based on the chosen ending pathway (invisible to players).

---

### Round 1 — Foundations: ESG Baseline Assessment 📋

**Crisis**: Board-mandated ESG audit. Depth of audit sets the game's risk baseline.

| Option | Title | Treasury | Reputation | Key Effect |
|---|---|---|---|---|
| A | Surface-Level Scan | $0 | −2 | Sets `electronics_blindspot` (hidden risk; doubles R4 severity) |
| B | Deep Forensic Audit | −$3M | +5 | Sets `deep_audit_completed`; CI −5; SLO +5 |
| C | Phased Audit Rollout | −$1.5M | +2 | Sets `deferred_audit`; partial blind spots remain |

**Strategic Consequence**: Option A is the highest-risk short-term choice. `electronics_blindspot` is a "time bomb" flag that detonates in Round 4 (Contagion), doubling crisis severity from 40 to 80.

---

### Round 2 — Double Materiality: Materiality-Based Budget Allocation 📊

**Crisis**: CFO requires all investment proposals to align with the High Financial Impact / High ESG Impact quadrant per the Double Materiality framework (ESRS 1).

**Special Mechanics**:
- **Materiality Matrix (mid-round panel)**: players classify the issue library on the 2×2 double-materiality matrix. Impact materiality and financial materiality are assessed separately; one classifier (`round2_csrd.correct_quadrant_v2`, string labels unless a dictionary carries all four dual-axis scores) drives scoring, the CFO gate and capital release.
- **Capital Release → Restricted Fund**: $15M × Q1 recall is released into a ring-fenced fund (`materiality_restricted_fund`) — NOT a treasury debit. The fund pays ESG CapEx ahead of the loan/interest machinery (like the Advanced Climate green fund); capital for missed issues is never released. Q2 disclosure placements unlock up to a further $1M into the same fund.
- **Accuracy Bonus**: full-quadrant accuracy ≥ 80% earns +1,000 leaderboard points (`bonus_score`). There is **no** $2M treasury bonus and **no** 90% threshold — earlier versions of this document described a mechanic that never existed (audit finding F-4).
- **CFO Precision Gate**: a non-Q1 issue placed in Q1 is rejected (HTTP 400); forcing the override costs −10 group reputation.
- **CSRD/ESRS Climate Bonus**: Option A with Advanced Climate mode unlocks NCD forgiveness (+25%).
- **Governance reconciliation (post-tick)**: the matrix is scored mid-round, but the A/B/C choice arrives at commit — `round_logic._post_r2_materiality` is the single arbiter that combines the two, writes exactly one tier flag, applies the Option C clawback (40% of the released fund, shortfall charged to treasury) and finalises the assurance debrief.

<!-- BEGIN GENERATED: R2-MECHANICS (scripts/generate_r2_mechanics_table.py — do not edit by hand) -->

**Options** (economics from `round_configs.py`; `revenue_delta` is per business unit):

| Option | Title | Treasury | Revenue Δ/BU | Reputation | Governance posture |
|---|---|---|---|---|---|
| A | Full Materiality Alignment | −$2.5M | $0 | +5 | Board-committee oversight — eligible for `materiality_aligned` |
| B | Strategic Exceptions | $0 | $0 | +2 | Strategic exceptions — eligible for `materiality_partial` |
| C | CEO-Only Sign-Off (No Board Committee Oversight) | $0 | +$400K | -5 | ESRS 1 §1.51 breach — always `materiality_ignored`; 40% fund clawback |

**Governance premium — tiered** (accuracy is full-quadrant matrix accuracy; exactly one flag is written, by `round_logic._post_r2_materiality`):

| Matrix accuracy | Option | Flag | M_R at R10 | R3 Green Bond effect |
|---|---|---|---|---|
| < 80% | A | `materiality_ignored` | 0 | +$1M Green Bond risk premium |
| = 80% | A | `materiality_aligned` | +0.10 | −$500K Green Bond discount |
| > 80% | A | `materiality_aligned` | +0.10 | −$500K Green Bond discount |
| < 80% | B | `materiality_ignored` | 0 | +$1M Green Bond risk premium |
| = 80% | B | `materiality_partial` | +0.05 | −$250K Green Bond discount |
| > 80% | B | `materiality_partial` | +0.05 | −$250K Green Bond discount |
| < 80% | C | `materiality_ignored` | 0 | +$1M Green Bond risk premium |
| = 80% | C | `materiality_ignored` | 0 | +$1M Green Bond risk premium |
| > 80% | C | `materiality_ignored` | 0 | +$1M Green Bond risk premium |

<!-- END GENERATED: R2-MECHANICS -->

**Regulatory Context**: Option C represents a real ESRS 1 violation — the management body must oversee the materiality process. Institutional investors apply a risk premium. The tiering teaches that analysis and governance are separate obligations: doing the materiality work well (≥80%) does not excuse approving it badly (Option C voids the premium; Option B halves it).

---

### Round 3 — Scope 3: Supply Chain Decarbonisation 🏭

**Crisis**: Regulators signal mandatory Scope 3 disclosures. Supply chain carbon is 4× direct emissions.

| Option | Title | Treasury | Key Effect |
|---|---|---|---|
| A | Rapid Supplier Switch | −$4M | `early_decarboniser` flag; CI −15 (scope3-weighted routing); supply disruption risk |
| B | Green Bond Investment | −$2M | `green_bond_active`; NCD −15; CI −8 (scope3-weighted) |
| C | Offset & Defer | −$1M | `carbon_deferred`; NCD +5; Reputation −3 |

**Scope-Routing**: Options A and B use `scope3_weighted` CI routing — impacts are weighted by each BU's Scope 3 ratio, so Electronics and Consumer Goods absorb more of the CI reduction.

---

### Round 4 — Contagion: Reputation Crisis Cascade 🔥

**Crisis**: Labour-rights exposé in Electronics supply chain goes viral. The Contagion Engine propagates reputation damage using an S-curve sigmoid formula.

**Special Mechanics**:
- If `electronics_blindspot` is active: crisis severity doubles (40 → 80).
- If `deep_audit_completed` is active: severity halved.

| Option | Title | Treasury | Reputation | Key Effect |
|---|---|---|---|---|
| A | Full Transparency & Remediation | −$6M | +10 | `remediation_active`; SLO +8; Gov Risk −5 |
| B | Damage Control PR | −$2M | +2 | `pr_containment`; SLO −3; root cause unaddressed |
| C | Deny & Deflect | $0 | −15 | `deny_and_deflect`; SLO −10; Gov Risk +8; NCD +5 |

**Sigmoid Formula**: `Group_Rep = Avg_Rep − 50 × sigmoid((severity − 30) / 15)`

---

### Round 5 — Climate: Physical Climate Risk Event 🌪️

**Crisis**: Category 4 cyclone projected. Base damage $12M. A stochastic roll determines actual impact.

**Special Mechanics**:
- **Stochastic Event**: roll > 0.75 → full $12M damage applied.
- **Shadow Board** activates in Round 5 — a virtual board of 3 directors (Planet, People, Shareholder) each advocate their preferred option. Players may reject their advice, but each rejection sets a permanent penalty flag.

| Option | Title | Resilience Factor | Treasury | Key Effect |
|---|---|---|---|---|
| A | Hard Engineering Defence | 0.85 | −$8M | `hard_engineering`; NCD +10; CI +3 (2-round delay before protection) |
| B | Nature-Based Solutions | 0.60 | −$5M | `nature_based_resilience`; NCD −8; CI −6 (2-round delay) |
| C | Insurance Only | 0.00 | −$2M | `insurance_only`; **BLOCKS** +0.20 Resilience Bonus at terminal valuation |

**Shadow Board Flags** (set if player *rejects* director advice):
- Reject Planet director → `planet_expendable` → −0.20 M_R penalty  
- Reject Shareholder director → `shareholder_alienated` → −0.20 M_R (Hostile Takeover pathway)  
- Reject Governance director → `governance_fragility` → −0.25 M_R (Regulatory Shutdown pathway)  

---

### Round 6 — AI Bias: Algorithmic Ethics & Brand Risk 🤖

**Crisis**: Software BU's AI recruitment tool systematically discriminates. Story reaches mainstream media.

**Macro Context**: Rounds 6–8 enter the "interest rate tightening" phase — WACC increases, reducing the terminal exit multiple.

| Option | Title | Treasury | Key Effect |
|---|---|---|---|
| A | Monetise the Algorithm | +$10M (Software Rev) | `ai_monetised`; Reputation −20; SLO −15; EU AI Act costs from R7 |
| B | Ethical AI Overhaul | −$8M | `ethical_ai_overhaul`; +0.15 Truth Premium M_R; SLO +15 |
| C | Quiet Patch | −$1M | `quiet_patch`; Gov Risk +10; risk of future leak |

---

### Round 7 — Circularity: Circular Economy Transition ♻️

**Crisis**: EU circular economy regulations mandate 60% waste diversion. Non-compliance fine: $15M.

| Option | Title | Treasury | Key Effect |
|---|---|---|---|
| A | Full Circular Redesign | −$10M | `circular_redesign`; NCD −12; CI −8 (scope3-weighted); Rep +8 |
| B | Extended Producer Responsibility | −$5M | `epr_program`; NCD −6; CI −5 (scope3-weighted) |
| C | Waste-to-Energy Partnership | −$7M | `waste_to_energy` + `synergy_unlock`; Synergy boost +0.30; CI −6 (scope3-weighted) |

**Key**: Option C sets the `synergy_unlock` flag → +0.15 M_R Strategic Synergy Premium at terminal valuation (OPEX savings separately captured in EBITDA).

---

### Round 8 — Blue Stress: Water Scarcity Emergency 🌊

**Crisis**: Multi-year drought depletes watershed serving Pharma and Electronics. Government water rationing imminent.

| Option | Title | Treasury | Key Effect |
|---|---|---|---|
| A | Water Efficiency for All BUs | −$12M | `water_efficiency_all`; Water −20; CI −3; SLO +5 |
| B | Prioritise Electronics | −$4M | `electronics_water_priority`; **BLOCKS** +0.20 Resilience M_R; SLO −25 for Pharma/Consumer Goods |
| C | Desalination Mega-Project | −$30M | `desalination_built`; NCD −30; Water −40; generates $5M/round from R10 (3-round payback) |

**Macro Context**: Interest rate "crisis premium" enters in R9–R10 — WACC at highest point.

---

### Round 9 — Just Transition: Workforce & Community Justice ✊

**Crisis**: Decarbonisation requires closing 3 legacy factories. 2,000 jobs at risk.

**Special Mechanics**:
- If Social Licence < threshold: 50% chance of strike that zeros revenue.
- `regulatory_friction_enabled` — governance risk increases add OPEX drag.

| Option | Title | Treasury | Key Effect |
|---|---|---|---|
| A | Immediate Closure | +$5M | `immediate_closure`; SLO −20; Rep −15; 50% base strike chance if SLO low (strike_probability_override: 0.50; burnout adds up to +20pts) |
| B | Managed Transition | −$12M | `managed_transition`; SLO +10; Rep +8; +0.12 M_R Just Transition bonus (×JT scaling) |
| C | Community Investment Fund | −$20M | `community_fund`; SLO +18; Rep +12; +0.18 M_R Community Champion bonus (×JT scaling) |

**JT Scaling**: Both managed_transition and community_fund bonuses are multiplied by 1 + (HR_investment_rounds × 0.10), capped at 1.5×. Teams that consistently invested in HR earn a higher M_R bonus.

---

### Round 10 — Grand Finale: Activist Ultimatum 🏛️

**Default Crisis**: An activist consortium holds a blocking stake and demands strategic restructuring.

> **Note**: The actual R10 crisis and options are **pathway-dependent**. The default ("Activist Ultimatum") is only shown if no ending pathway override is active. See §6 for all 5 pathway variants.

| Option | Title | Treasury | Key Effect |
|---|---|---|---|
| A | Resist & Integrate | −$5M | Requires Synergy Score > 80; synergy bonus + terminal valuation calculated |
| B | Spin-off | +$10M | Spins off weakest BU; partial value unlock |
| C | Divest | +$25M | `synergy_wipe`; SLO −12; NCD +8; short-term cash max, long-run value destroyed. The `divest_all` impact key is declared but deliberately inert pending a design ruling (C-6, 2026-08-31) |

**Terminal Valuation** runs after R10 options are applied (see §8).

---

## 5. Decision Pillars (Multi-Toggle Paradigm)

In the `multi_toggles` game paradigm, each round presents **5 strategic pillars**, each with **3 investment choices**. Players select one option per pillar simultaneously, in addition to the round's main crisis decision.

| Pillar | Icon | Focus Area |
|---|---|---|
| **Energy** | ⚡ | Carbon intensity, renewable transition, infrastructure |
| **Operations** | 🏭 | Process efficiency, governance, physical resilience |
| **Supply Chain** | 🔗 | Supplier ESG, transparency, resilience |
| **Offsetting** | 🌱 | Carbon credits, community impact, adaptation finance |
| **Human Resources** | 👥 | Talent, culture, wellbeing, green skills |

### Pillar Option Structure per Round

Each pillar option contains:
- `cost`: Treasury delta (negative = spend, positive = gain)
- `impacts`: Dict of KPI deltas (reputation, carbon_intensity_delta, social_license_delta, governance_risk_delta, natural_capital_debt_delta, burnout_delta)
- `flags_set`: List of boolean flags that carry consequences forward

### Round-by-Round Pillar Themes

| Round | Energy Focus | Operations Focus | Supply Chain Focus | Offsetting Focus | HR Focus |
|---|---|---|---|---|---|
| 1 | Renewable PPA / Solar CapEx | Lean Process / Digital Twin | Supplier Audit | Nature-Based Offsets | DEI Program / Leadership Dev |
| 2 | Green Tariff / Efficiency | Materiality Board | Blockchain Traceability | Community Impact Fund | People Analytics |
| 3 | Fleet Electrification | Closed-Loop Mfg | Rapid Supplier Switch | Science-Based Targets (SBTi) | Green Skills Academy |
| 4 | Green Energy Pivot | Full Factory Transparency | Supply Chain Remediation | Stakeholder Compensation Fund | Crisis Employee Support |
| 5 | Distributed Microgrids | Hard Engineering / Nature-Based | Geographic Diversification | Climate Adaptation Fund | Emergency Response Training |
| 6 | Green Data Centers | Ethical AI Overhaul | Scope 3 transparency | Impact Reporting | Upskilling & Reskilling |
| 7 | H2 / Long-Duration Storage | Circular Product Redesign | Supplier Circularity | Biodiversity Credits | Just Transition Training |
| 8 | Water-Energy Nexus | Water Efficiency Tech | Supply Chain Nearshoring | Watershed Restoration | Worker Wellbeing |
| 9 | Decarbonisation Capex | Factory Repurposing | Community Procurement | Just Transition Fund | Retraining Programs |
| 10 | Terminal Green Infra | Integrated Reporting | Stakeholder Compact | ESG Bond Refinancing | Leadership Legacy |

---

## 6. Ending Pathways (5 Alternate Ends)

The simulation has **5 ending pathways** that replace the default "Activist Ultimatum" R10 crisis. The pathway is selected by the **Facilitator** or **God Mode** at session creation. Players *never see the pathway name* — they only receive **foreshadowing events** (news items, market intelligence) injected from Rounds 5–8 that hint at what's coming.

### Pathway Overview

| ID | Name | R10 Crisis Title | Icon | Core Tension |
|---|---|---|---|---|
| `activist_ultimatum` | Activist Ultimatum *(default)* | Activist Ultimatum | 🏛️ | Integration vs. divestiture under activist pressure |
| `climate_black_swan` | Climate Black Swan | The Stranded Asset Reckoning | 🌋 | Decarbonise or face carbon Minsky Moment |
| `stakeholder_revolt` | Stakeholder Revolt | The Social Reckoning | 🪧 | Triple stakeholder ultimatum (employees + community + consumers) |
| `hostile_takeover` | Hostile Takeover | The Corporate Raider | 🦈 | Defend or capitulate to Cerberus Capital |
| `regulatory_shutdown` | Regulatory Shutdown | The Compliance Reckoning | ⚖️ | CSDDD enforcement — remediate, settle, or contest |

---

### Pathway 1: Activist Ultimatum (Default) 🏛️

**Foreshadowing**:
- R6: "Activist Fund Files 13D — 4.9% Stake Acquired"
- R7: "Analyst Note: 'Muressons Ripe for Restructuring'"
- R8: "Blocking Stake Reached — Board Engagement Imminent"

**R10 Options**:
| Option | Title | Effect |
|---|---|---|
| A | Resist & Integrate | Requires Synergy > 80; synergy bonus applied; −$5M |
| B | Spin-off | Divests weakest BU; +$10M; SLO −5 |
| C | Divest | Full divestiture; +$25M; `synergy_wipe`; Rep −10 |

---

### Pathway 2: Climate Black Swan 🌋

**Trigger Logic**: Activated when world crosses 1.5°C threshold (foreshadowed via IPCC reports).

**Special Rules**: Carbon tax **tripled** to $750/tonne. Exit multiple is **haircut by CI**: `Exit_Multiple = 12 × (1 − max(0, (avg_CI − 25) × 0.01))`.

**Foreshadowing**:
- R5: "IPCC: 1.5°C Overshoot Now 'Likely'"
- R6: "Carbon Futures Surge 40% — EU ETS Hits Record"
- R7: "Insurance Consortium: 'Uninsurable Assets by 2035'"
- R8: "ALERT: 1.5°C Threshold Breached — Carbon Markets in Turmoil" (sets `climate_threshold_breached`)

**R10 Options**:
| Option | Title | Effect |
|---|---|---|
| A | Emergency Decarbonisation | −$20M; all CI halved; NCD halved; +0.30 M_R if avg CI < 25 |
| B | Climate Adaptation Portfolio | Divests BUs with CI > 40 at 50% book value; reallocation capital |
| C | Deny & Delay | +$5M; carbon tax **tripled**; NCD doubled; exit multiple drops to 6×; M_R −0.40 |

**Pathway M_R Bonuses/Penalties**:
- +0.30 Climate Leader (avg CI < 25)
- +0.20 Adaptation Premium (nature_based_resilience + early_decarboniser)
- +0.15 Carbon Transition (CI reduced ≥ 40% from R1 baseline)
- −0.40 Stranded Asset Penalty (avg CI > 50)
- −0.20 Shadow Board (planet_expendable flag)

**Archetypes**: The Climate Pioneer · The Adapted Enterprise · The Stranded Giant · The Fossil Relic

---

### Pathway 3: Stakeholder Revolt 🪧

**Trigger Logic**: Employee burnout + community coalition + consumer boycott converge simultaneously.

**Special Rules**: SLO collapse threshold = 40; Burnout collapse threshold = 70.

**Foreshadowing**:
- R5: "Glassdoor Review: 'Muressons Culture is Toxic'"
- R6: "Community Coalition Forms Against Industrial Operations"
- R7: "Consumer Boycott Hashtag Gains 2M Impressions"
- R8: "#MuressonsExposed — Triple Stakeholder Ultimatum" (sets `social_media_campaign`)

**R10 Options**:
| Option | Title | Effect |
|---|---|---|
| A | Total Stakeholder Compact | −$18M; Revenue +15%; +0.35 M_R if avg SLO ≥ 70 AND burnout < 30 |
| B | Selective Appeasement | −$8M; fixes worst metric; unaddressed groups SLO −10 |
| C | Corporate Hardball | +$10M; all SLO −25; all burnout +20; shutters any BU with SLO = 0; M_R −0.30 |

**Pathway M_R Bonuses/Penalties**:
- +0.35 Social Regeneration (avg SLO ≥ 70 AND burnout < 30)
- +0.15 Employee Champion (burnout < 25 AND readiness ≥ 70)
- +0.15 Community Trust (avg SLO ≥ 80)
- −0.50 Social Collapse (avg SLO < 40 OR burnout > 70)

**Archetypes**: The People's Corporation · The Responsible Employer · The Contested Enterprise · The Social Pariah

---

### Pathway 4: Hostile Takeover 🦈

**Trigger Logic**: Weak governance + low market cap makes Muressons vulnerable to Cerberus Capital.

**Special Rules**: Defence viability threshold: synergy ≥ 1.3 (White Knight option). Takeover premium: +15%.

**Foreshadowing**:
- R6: "Unusual Share Volume Detected in Muressons Stock"
- R7: "PE Firm 'Cerberus Capital' Denies Acquisition Interest"
- R8: "Cerberus Files Preliminary Offer with Regulator" (sets `takeover_rumour`)

**R10 Options**:
| Option | Title | Effect |
|---|---|---|
| A | White Knight Defence | −$15M; Revenue −5%; +0.25 M_R if synergy ≥ 1.3 AND treasury > $30M |
| B | Poison Pill + Crown Jewel Lock-Up | −$25M; exit multiple overridden to 10× (debt overhang) |
| C | Accept the Bid | +$20M; exit multiple locked to 8×; M_R capped at 1.0; M_R −0.50 |

**Pathway M_R Bonuses/Penalties**:
- +0.25 Strategic Integration (synergy ≥ 1.3 AND treasury > $30M)
- +0.20 Fortress Premium (EBITDA margin > 20% AND no scandal flags)
- +0.15 Conglomerate Premium (synergy ≥ 1.5)
- −0.40 Vulnerable Target (synergy < 1.1 AND treasury < $10M)
- −0.20 Shadow Board (shareholder_alienated flag)

**Takeover Vulnerability Index (TVI)**: `100 − (synergy × 30) − (treasury_M × 5) − (EBITDA_margin × 50)` — displayed as a live foreshadowing KPI.

**Archetypes**: The Untouchable Fortress · The Defended Platform · The Vulnerable Target · The Broken Conglomerate

---

### Pathway 5: Regulatory Shutdown ⚖️

**Trigger Logic**: Whistleblower triggers CSDDD investigation. Years of governance failures exposed.

**Special Rules**: Carbon tax elevated to $350/tonne. Base fine: $30M. Compliance cost: $4M per BU.

**Ethical Score**: `(avg_SLO × 0.3 + (100 − avg_CI) × 0.3 + group_reputation × 0.4) / 10` — gates M_R bonuses.

**Foreshadowing**:
- R5: "EU Adopts Corporate Sustainability Due Diligence Directive (CSDDD)"
- R6: "Sector Peers Face €50M+ CSDDD Compliance Costs"
- R7: "Whistleblower Contacts Environmental Regulator"
- R8: "Regulator Issues Show Cause Notice to Muressons" (sets `whistleblower_investigation`)

**R10 Options**:
| Option | Title | Effect |
|---|---|---|
| A | Full Remediation Programme | $4M per BU; +0.30 M_R if ethical_score > 7 AND no scandal flags |
| B | Negotiate Consent Decree | −$30M; exit multiple to 10×; third-party monitoring for 3 years |
| C | Contest the Ruling | −$10M legal costs; if ethical_score < 5: double fine ($60M); exit multiple to 7×; Rep −30; M_R −0.35 |

**Pathway M_R Bonuses/Penalties**:
- +0.30 Regulatory Exemplar (ethical_score > 7 AND no scandal flags)
- +0.20 Supply Chain Transparency (scope_3_transparency OR full_remediation). `scope_3_transparency` is earned in R3 when Scope 3 data completeness reaches ≥80% (Option A, Direct Supplier Audit) — wired 2026-08-31 (B-2).
- +0.15 Proactive Compliance (ethical_score > 6 AND avg SLO > 60)
- −0.45 Regulatory Failure (ethical_score < 4)
- −0.25 Shadow Board (governance_fragility flag)

**Compliance Risk Index (CRI)**: `(avg_CI × 0.4) + ((100 − avg_SLO) × 0.3) + ((100 − group_rep) × 0.3)` — foreshadowing KPI.

**Archetypes**: The Compliance Champion · The Regulated Enterprise · The Monitored Entity · The Suspended Operation

---

### Foreshadowing KPIs (displayed live from R5)

| KPI | Formula | Pathway Relevance |
|---|---|---|
| Stranded Asset Exposure (SAE) | `avg_CI × total_NCD / 1000` | Climate Black Swan |
| Social Capital Index (SCI) | `avg_SLO×0.4 + (100−burnout)×0.3 + group_rep×0.3` | Stakeholder Revolt |
| Takeover Vulnerability Index (TVI) | `100 − synergy×30 − treasury_M×5 − EBITDA_margin×50` | Hostile Takeover |
| Compliance Risk Index (CRI) | `avg_CI×0.4 + (100−avg_SLO)×0.3 + (100−group_rep)×0.3` | Regulatory Shutdown |

---

## 7. Side Tracks (6 Parallel Mini-Simulations)

Side tracks are **self-contained mini-simulations** (4–7 rounds each) that run **sequentially** — the main simulation pauses while a side track is active. All side tracks share the same `process_tick()` engine with full formula support.

### Control Hierarchy
- **God Mode**: Enables/disables tracks globally and per-facilitator.
- **Facilitator**: Assigns enabled tracks to cohorts and sets injection timing.
- **Player**: Plays through assigned tracks sequentially.

### Data Bridge Contract (both directions)
- **`seed_from_main_state()`**: Reads main sim state → initialises side track state.
- **`write_back_to_main()`**: Outputs flags/modifiers → merged into main sim `active_event_flags`.

---

### Side Track 1: Supply Chain 🔗

**Focus**: Supply chain visibility, supplier risk scoring, circular economy integration.  
**Rounds**: Available R3–R7 (5 rounds).  
**Scoring Dimensions**: Supply Visibility, Supplier Risk, ESG Compliance, Circular Economy Score.  
**Write-back Flags**: supply chain transparency metrics → affects Black Swan probability reduction.

---

### Side Track 2: Ethics & Sustainability 🌿

**Focus**: Ethical governance, anti-corruption, human rights due diligence.  
**Rounds**: Available R2–R7.  
**Cross-Track Prerequisite**: None.  
**Write-back Flags**: ethics integrity flags → improve BRSR NGRBC starting position.

---

### Side Track 3: Stakeholder Management 🤝

**Focus**: NPC stakeholder dynamics, trust building, coalition management.  
**Rounds**: Available R3–R8.  
**Write-back Flags**: Stakeholder Fatigue Engine modifiers; SLO floor improvements.

---

### Side Track 4: Sustainability Reporting 📋

**Focus**: CSRD/ESRS report building, assurance, disclosure quality.  
**Rounds**: Available R4–R8.  
**Write-back Flags**: `regulatory_readiness` score → boosts BRSR NGRBC starting position.

---

### Side Track 5: Corporate SDG Deep Track 🌐

**Focus**: UN SDG alignment across 5 thematic rounds.  
**Rounds**: 5 rounds; available R1–R8.  
**Scoring**: SDG Impact Score (−11 to 105 raw points).

**Round Themes**:
| ST Round | Theme | Target BUs |
|---|---|---|
| 1 | PAI Audit & Baseline | Group-wide |
| 2 | Living Wage Commitment | Electronics, Consumer Goods |
| 3 | Circular Procurement | Electronics, Consumer Goods |
| 4 | Biodiversity Net-Gain | Consumer Goods, Pharma |
| 5 | Integrated Reporting | Group-wide |

**Terminal Valuation Integration**:
```
M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25
Range: 0.97 (all C, score -11) → 1.26 (all A, score 105)
```
M_SDG is a **multiplier** on the full terminal valuation formula: `TV = EBITDA × Exit × M_R × M_SDG`

**SDG Drag/Boost System**:
- Score < 40 → `regulatory_ratchet_active` (OPEX uplift next round)
- Score > 70 → +2 group reputation per SDG round
- `circular_leader` flag → synergy multiplier protected from erosion (floor 1.10)
- `nature_positive` flag → NCD interest rate reduced −1% per round

**SDG Archetypes**: SDG Champion (A+) · SDG Leader (A) · SDG Performer (B) · SDG Starter (C) · SDG Laggard (D)

---

### Side Track 6: BRSR NGRBC Deep Dive 🇮🇳

**Focus**: SEBI BRSR framework — all 9 NGRBC principles, Essential vs Leadership indicators, BRSR Core assurance.  
**Rounds**: 5 rounds; available R2–R8.  
**Cross-Track Prerequisites**: `sustainability_reporting`, `ethics_sustainability` (enrich starting position).

**Round Themes**:
| ST Round | NGRBC Principles |
|---|---|
| 1 | Governance & Ethics (P1/P7) |
| 2 | Human Capital (P3/P5) |
| 3 | Environmental Stewardship (P6/P2) |
| 4 | Value Chain & Stakeholder (P4/P8/P9) |
| 5 | Integrated BRSR Core Disclosure |

**Scoring Dimensions** (weighted composite):
- Governance & Ethics (P1/P7): 20%
- Human Capital (P3/P5): 20%
- Environmental Stewardship (P6/P2): 25%
- Value Chain & Stakeholder (P4/P8/P9): 20%
- Integrated Disclosure Quality: 15%

**Write-back Flags**:
- Score ≥ 80 → `brsr_net_positive_dividend` (+0.05 M_R ESG Alpha Dividend at terminal valuation)
- `brsr_pioneer`, `brsr_core_assured`, `brsr_living_wage` → individual archetype flags
- `governance_fragility` → `brsr_truth_premium_cost_doubled`
- `brsr_greenwash_risk` → SEBI show-cause notice in ST-R4 (−12 reputation, −$2.5M)

**Special Events**:
- ST-R4 with `brsr_greenwash_risk`: SEBI issues show-cause notice on unverifiable Scope 3 claims.
- ST-R5 with `governance_fragility`: Whistleblower leak triggers SEBI scrutiny; treasury −$2.5M.
- ST-R5 with `brsr_core_assured`: Crisis severity −10 (assurance bonus).

**BRSR Archetypes**: BRSR Pioneer · Responsible Steward · Compliance Pragmatist · Regulatory Laggard

---

## 8. Terminal Valuation & Archetypes

Terminal valuation runs after all Round 10 decisions are applied. It is a comprehensive model connecting every ESG decision made across the simulation into a single enterprise value.

### Formula

```
Terminal_EBITDA = Σ(BU Revenue − BU OPEX) − (Total_tCO₂e × Carbon_Tax_Per_Tonne)

Terminal Value (EV) = (Terminal_EBITDA + Green_Fund) × Exit_Multiple × M_R × M_SDG

Equity Value = Terminal Value − Net Debt

Price Per Share = Equity Value / 100,000,000 shares
```

**IPO Price**: $50.00/share (100M shares outstanding)

---

### Exit Multiple

**Default (fixed)**: 12.0×  
**Dynamic (WACC-linked)**: `(1 + g) / (WACC − g)` where g = 2% long-run growth.
- Floor: 6.0×, Ceiling: 18.0×  
- WACC > 9% triggers a visible "WACC Penalty" warning in the UI.
- NCD raises WACC. Macro rate cycles also affect WACC.

**Pathway Overrides**: Hostile Takeover can reduce to 8–10×; Climate Black Swan haircuts by CI; Regulatory Shutdown to 7–10×.

---

### Regenerative Multiple (M_R)

M_R is the ESG quality / risk modifier. The maximum achievable value is ~1.93 without Just Transition scaling and ~2.02 with it.

| M_R Component | Trigger | Value |
|---|---|---|
| Base | Always | +1.00 |
| Materiality Governance | `materiality_aligned` flag (≥80% accuracy AND Option A) | +0.10 |
| Materiality Governance — partial | `materiality_partial` flag (≥80% accuracy AND Option B; mutually exclusive with the full premium) | +0.05 |
| Synergy Strategic Premium | `synergy_unlock` AND synergy ≥ 0.80 | +0.15 |
| Resilience Champion | No `insurance_only` AND no `electronics_water_priority` | +0.20 |
| Truth Premium | `ethical_ai_overhaul` | +0.15 |
| Community Champion | `community_fund` (×JT scaling) | +0.18 |
| Just Transition | `managed_transition` (×JT scaling) | +0.12 |
| Workforce Excellence | workforce_readiness ≥ 75 | +0.10 |
| Wellbeing Champion | avg burnout < 20 | +0.05 |
| BRSR ESG Alpha Dividend | `brsr_net_positive_dividend` | +0.05 |
| **Planet Expendable Penalty** | `planet_expendable` | −0.20 |
| **Instability Discount** | avg SLO < 75 | −0.40 |

**JT Scaling Factor**: `min(1.5, 1.0 + HR_investment_rounds × 0.10)` — rewards consistent HR investment.

**Max Achievable M_R**: ~1.93 (without JT scaling; ~2.03 with max JT scaling).

---

### SDG Multiplier (M_SDG)

`M_SDG = 1.0 + (SDG_Impact_Score / 100) × 0.25`

- Sessions without the Corporate SDG side track: M_SDG = 1.0 (neutral).
- Range: 0.97 → 1.26.

---

### Company Archetypes (by M_R)

| M_R Range | Archetype | Icon | Default Gradient |
|---|---|---|---|
| ≥ 1.8 | **The Regenerative Titan** | 🌱 | Emerald green |
| 1.2–1.79 | **The De-risked Safe-Haven** | 🏦 | Blue |
| 0.8–1.19 | **The Fragile Giant** | ⚠️ | Amber |
| < 0.8 | **The Stranded Relic** | 💀 | Red |
| Survival Mode | **The Turnaround Manager** | 🔧 | Purple (M_R capped 0.80) |

> Each ending pathway has its own **archetype override titles/icons** that replace the defaults.

---

### Cross-Pathway M_R Normalization (Leaderboard)

To enable fair comparison across sessions with different pathways, M_R is normalized:
`Normalized_M_R = Raw_M_R × Pathway_Difficulty_Coefficient`

| Pathway | Difficulty Coefficient |
|---|---|
| Activist Ultimatum | 1.00 |
| Climate Black Swan | 1.15 |
| Stakeholder Revolt | 1.10 |
| Hostile Takeover | 1.20 |
| Regulatory Shutdown | 1.12 |

---

## 9. Stochastic Systems

### Round 5: Cyclone Damage Roll
- If random roll > 0.75: full $12M base damage applied.
- Resilience Factor from chosen option reduces damage: `actual_damage = base_damage × (1 − resilience_factor)`.
- Option A (Hard Engineering) or Option B (Nature-Based): protection active from R7 onward (2-round delay).

### Round 9: Strike Probability
- Triggered if Social Licence is low and `immediate_closure` flag is set.
- Strike probability override: 75% chance of strike zeroing revenue for that round.

### Greenwashing Engine
- Activates when a player selects a "green" option (A or C) without backing it with ≥ 15% investment ratio.
- Penalty: −15 reputation (group level), sets auditor tolerance to Hostile.
- Moderate choices (B): lower threshold at 10%.

### Macro Interest Rate Cycles
| Rounds | Regime | WACC Modifier |
|---|---|---|
| R1–R2 | Easing | −1% |
| R3–R5 | Neutral | 0% |
| R6–R8 | Tightening | +2% |
| R9–R10 | Crisis Premium | +3% |

---

## 10. Black Swan Events

Black Swan events are **stochastic, low-probability, high-impact events** evaluated each round via `evaluate_black_swans()`. They are drawn from Taleb's fat-tail theory and Weick & Sutcliffe's High Reliability Organisation framework.

### Difficulty Scaling
| Tier | Prob. Multiplier | Impact Multiplier | Treasury Floor |
|---|---|---|---|
| Easy (Introductory) | 0.5× | 0.7× | −$500M |
| Standard (Professional) | 1.0× | 1.0× | −$200M |
| Expert (Executive) | 1.5× | 1.3× | −$50M |

### Global Black Swan Events

| Event | Icon | Round Range | Base Prob | Key Impact |
|---|---|---|---|---|
| Sovereign Debt Crisis | 🏦 | R4–R8 | 8% | −12% treasury, +300bps interest, −10% revenue |
| Internal Whistleblower Scandal | 🔔 | R3–R9 | 6% | Rep −20, treasury −8%, SLO −15, Gov Risk +15 |
| Pandemic Disruption Wave | 🦠 | R5–R9 | 6% | 30% workforce loss, OPEX +15%, burnout +20 |
| AI Disruption Wave | 🤖 | R6–R10 | 10% | Software Rev +20%, ops displacement 15%, burnout +10 |
| Climate Litigation Ruling | ⚖️ | R7–R10 | 5% | −$8M, asset writedown 10%, Rep −10 |
| Critical Mineral Embargo | 🚫 | R4–R9 | 7% | Electronics/Pharma Rev −15%, OPEX +10% |
| Ransomware Attack | 💀 | R3–R10 | 7% | −$5M, Revenue −5%, Rep −8, Gov Risk +12 |
| Viral Consumer Boycott | 📱 | R4–R9 | 5% | Consumer Goods Rev −20%, Rep −12, SLO −10 |

### Region-Specific Events

| Event | Icon | Region | Round Range | Base Prob |
|---|---|---|---|---|
| ASEAN Trade Corridor Dispute | 🚢 | ASEAN | R3–R8 | 10% |
| South Asia Extreme Monsoon | 🌧️ | South Asia | R2–R7 | 9% |
| EU Carbon Border Adjustment (CBAM) | 🌿 | Europe | R4–R9 | 11% |
| SEC Climate Disclosure Enforcement | 📋 | North America | R5–R9 | 8% |
| African Resource Nationalisation | ⛏️ | Africa | R3–R9 | 7% |

**Conditional Modifiers**: Many events have higher probability when specific metrics are poor. E.g., Whistleblower probability +15% if `greenwashing_detected` is active. This creates compounding risk curves.

---

## 11. Flag Dependency Graph

Flags are boolean state markers set by decisions that carry cross-round consequences. Below is the complete causal dependency graph.

| Source Round | Flag | Target Round | Effect | Category |
|---|---|---|---|---|
| R1 | `deep_audit_completed` | R4 | Halves crisis severity (40 vs 80) | governance |
| R1 | `electronics_blindspot` | R4 | Doubles crisis severity to 80 | risk |
| R2 | `materiality_aligned` | R3 | Green Bond −$500K discount (option B) | governance |
| R2 | `materiality_aligned` | R10 | +0.10 M_R Governance bonus | governance |
| R2 | `materiality_partial` | R3 | Green Bond −$250K half-discount (option B) | governance |
| R2 | `materiality_partial` | R10 | +0.05 M_R Governance bonus (partial) | governance |
| R2 | `materiality_ignored` | R3 | Green Bond +$1M risk premium (option B) | risk |
| R2 | `blockchain_traceability` | R8 | Prevents supply chain scandal | supply_chain |
| R3 | `early_decarboniser` | R7 | +0.10 synergy multiplier bonus | climate |
| R3 | `greenwash_risk` | R5 | Triggers greenwash if inv < 15% | risk |
| R5 | `insurance_only` | R10 | BLOCKS +0.20 Resilience M_R bonus | climate |
| R6 | `ethical_ai_overhaul` | R10 | +0.15 Truth Premium M_R | governance |
| R6 | `ai_monetised` | R7 | EU AI Act costs from R7+ | risk |
| R7 | `synergy_unlock` | R10 | +0.15 Synergy M_R (strategic premium; OPEX savings already in EBITDA) | strategic |
| R8 | `electronics_water_priority` | R10 | BLOCKS +0.20 Resilience M_R bonus | risk |
| R9 | `community_fund` | R10 | +0.18 Community Champion M_R (×JT) | social |
| R9 | `managed_transition` | R10 | +0.12 Just Transition M_R (×JT) | social |
| BRSR-R1 | `brsr_pioneer` | R10 | Enables BRSR Pioneer archetype path | governance |
| BRSR-R1 | `governance_fragility` | BRSR-R5 | Triggers Whistleblower Governance Leak (−$2.5M) | governance |
| BRSR-R4 | `brsr_greenwash_risk` | BRSR-R4 | SEBI Show-Cause Notice (−12 Reputation) | risk |
| BRSR-R5 | `brsr_net_positive_dividend` | R10 | +0.05 ESG Alpha Dividend M_R (BRSR Pioneer) | governance |

**Shadow Board Flags** (R5 — if player rejects director recommendation):
- Reject Planet director → `planet_expendable` → −0.20 M_R (all pathways) + amplifies Climate Black Swan
- Reject Shareholder director → `shareholder_alienated` → −0.20 M_R (Hostile Takeover pathway)
- Reject Governance director → `governance_fragility` → −0.25 M_R (Regulatory Shutdown) + BRSR leak

---

## 12. Core Engine Modules

All 30 registered modules live primarily in `backend/engine.py` and satellite files. They run inside `process_tick()` each round.

| # | Module | Key Formula | Trigger |
|---|---|---|---|
| 1 | Carbon Accounting | `tCO₂e = CI × rev / 1M`; revenue-weighted avg CI | Every round |
| 2 | Corporate Strategic Fund (CSF) | `CSF = Σ(Rev − OPEX) − Dividends` | Every round |
| 3 | Contagion Engine | `Rep = Avg_Rep − 50 × sigmoid((severity − 30) / 15)` | Crisis rounds |
| 4 | Synergy Engine | `New_OPEX = Old_OPEX × (1 − sqrt(ratio) × 0.7 × Synergy)` | When invested |
| 5 | Natural Capital Cost of Debt | `rate = base_rate + NCD × 0.0001` | Every round |
| 6 | VRIO Decay | 2% decay per round unless reinvested | Every round |
| 7 | Burnout Accumulation | Natural drift +6/round; OPEX quadratic penalty > 20 | Every round |
| 8 | Workforce Readiness | ±8–16 per round; penalty < 40; bonus > 75 | Every round |
| 9 | Talent Brain-Drain | Attrition from high burnout + low readiness | Every round |
| 10 | Strike Probability | SLO + burnout → probability of revenue-zeroing strike | Every round |
| 11 | Natural Decay | Scores decay toward baseline when uninvested | Every round |
| 12 | Macroeconomic Inflation | OPEX inflation per macro cycle | Every round |
| 13 | Execution Overrun Risk | Investment budget overruns add OPEX drag | Every round |
| 14 | Technical Debt | Deferred IT/ops investment accumulates latent cost | Every round |
| 15 | Revenue Cannibalization | BUs > 15% above avg revenue cannibalize overlapping BUs | Every round |
| 16 | Stakeholder Fatigue | `efficiency = 1 / (1 + 0.3 × crisis_count)` | After crises |
| 17 | Supply Chain Contagion | SC disruption propagates revenue/OPEX shocks | When flagged |
| 18 | Competitor Pressure | Market share erosion when peers decarbonise faster | R5+ |
| 19 | Cash Conversion | Treasury → liquidity ratio → covenant trigger | Every round |
| 20 | Dividend Ratchet | Dividend expectations grow with profitability history | R4+ |
| 21 | Talent Allocation Pressure | Cross-BU talent competition reduces marginal returns | R3+ |
| 22 | Technology Lock-In | Early tech choices create switching costs | R4+ |
| 23 | ESG Greenwashing Risk | Green option + inv < 15% → reputation penalty −15 | When flagged |
| 24 | Macro Interest Rate | 4-phase rate cycle modifies WACC | Every round |
| 25 | Biodiversity Engine | `biodiversity_engine.py` | When NCD or nature flags set |
| 26 | Balance Sheet Engine | IAS 1 format; liquidity ratio covenant | Every round |
| 27 | Systemic Risk Engine | `systemic_risk_engine.py`; emissions cap breach | Every round |
| 28 | Terminal Valuation | `terminal_valuation.py`; EBITDA × Exit × M_R × M_SDG | R10 only |
| 29 | Regulatory Sandbox | `regulatory_sandbox.py`; CSRD/ESRS gate logic | R2+, R7+ |
| 30 | Black Swan Registry | `black_swan_registry.py`; fat-tail stochastic events | R2–R10 |

---

## 13. Simulation Config & Tuneable Parameters

All parameters live in `simulation_config.json` and are loaded as typed constants by `backend/config.py`. **Never hardcode these values in engine logic.**

| JSON Path | Config Constant | Default | Description |
|---|---|---|---|
| `simulation_settings.rounds` | `SIM_ROUNDS` | 10 | Total main simulation rounds |
| `simulation_settings.agents` | `SIM_AGENTS` | 50 | Number of NPC / autonomous stakeholder agents (DOC-2: this is the NPC agent pool, **not** the 4 business-unit slots — BUs come from the seed JSON / `bu_profiles.py`) |
| `simulation_settings.initial_budget` | `SIM_INITIAL_BUDGET` | $50,000,000 | Starting Corporate Strategic Fund |
| `economic_parameters.carbon_price_base` | `ECONOMIC_CARBON_PRICE_BASE` | $50.00 | Base carbon price (USD/tCO₂e) — DOC-1: reconciled to match `simulation_config.json` (source of truth) |
| `economic_parameters.carbon_price_growth_rate` | `ECONOMIC_CARBON_PRICE_GROWTH` | 0.05 | Annual carbon price escalation — DOC-1: reconciled to match `simulation_config.json` |
| `economic_parameters.circular_economy_efficiency_bonus` | `ECONOMIC_CIRCULAR_ECONOMY_BONUS` | 0.15 | OPEX bonus from circular decisions |
| `constraints.max_carbon_emissions` | `CONSTRAINT_MAX_CARBON_EMISSIONS` | 5,000 tCO₂e | Group-wide emissions cap |
| `constraints.min_liquidity_ratio` | `CONSTRAINT_MIN_LIQUIDITY_RATIO` | 0.2 | Minimum cash/assets ratio |

### Terminal Valuation Constants
- Shares outstanding: 100,000,000 (fixed)
- IPO opening price: $50.00/share
- Long-run terminal growth: 2%
- Exit multiple floor: 6×, ceiling: 18×

---

## 14. Industry Verticals (BU Substitutions)

Facilitators can replace any of the 4 default BU slots with an industry vertical. Slot-fit restrictions ensure pedagogical coherence.

| Vertical | Icon | Replaces Slot | Carbon Intensity | Key Character |
|---|---|---|---|---|
| Oil & Gas | 🛢️ | Pharma | 95 | Extreme carbon; stranded asset risk; NCD 350 |
| Banking & Financial Services | 🏦 | Software | 8 | Financed emissions; systemic risk; Gov Risk 30 |
| Retail/FMCG | 🛍️ | Consumer Goods | 42 | Packaging; labour-intensive; brand-risk |
| Agriculture | 🌾 | Consumer Goods | 55 | Water 90; biodiversity; land-use emissions |
| Technology (AI/Cloud) | 🧠 | Software | 15 | Data centre energy; talent brain-drain; Gov Risk 28 |

### Slot-Fit Rules
```
pharma    → [oil_gas]
electronics → [oil_gas]
consumer_goods → [retail_fmcg, agriculture]
software  → [banking_financial_services, technology]
```

### Vertical Blindspot Flags
Each vertical has its own "blindspot" equivalent set in Round 1 if players choose a shallow audit:
- Oil & Gas: `refinery_blindspot`
- Banking: `governance_blindspot`
- Retail/FMCG: `supply_chain_blindspot`
- Agriculture: `land_use_blindspot`
- Technology: `data_centre_blindspot`

---

## 15. Role Hierarchy: God Mode → Facilitator → Player

### God Mode (Platform Admin)
- Enables/disables side tracks globally and per-facilitator
- Sets difficulty tier (Easy / Standard / Expert)
- Injects specific Black Swan events (forced event ID)
- Sets the ending pathway (or `random`)
- Sets the region (ASEAN, South Asia, Europe, North America, Africa) for region-specific Black Swan events
- Manages player passwords, session codes, benchmark data

### Facilitator
- Creates sessions for their cohort
- Assigns which side tracks players will encounter and their injection timing
- Can override round decisions (decision_overrides.json)
- Views the Teleprompter (admin_teleprompter.py) for guided facilitation scripts
- Accesses the Admin Analytics dashboard for real-time session monitoring

### Player (Team)
- Receives Player Briefing (company background, starting position)
- Makes crisis decisions (A/B/C) each round
- Makes pillar decisions (5 areas) each round
- Plays through assigned side tracks when activated
- Sees their KPI dashboard, event narratives, and foreshadowing items (but NOT the pathway name)
- At R10: sees full terminal valuation breakdown, company archetype, and score vs benchmarks

---

## Appendix A: Key Codebase Files

| File | Role |
|---|---|
| `backend/engine.py` | Core 30+ formula modules; `process_tick()` |
| `backend/round_configs.py` | All 10 main round crisis configs (A/B/C) |
| `backend/pillar_configs.py` | All 10 rounds × 5 pillars × 3 options |
| `backend/ending_pathways.py` | 5 pathway R10 configs, foreshadowing, M_R calculators |
| `backend/terminal_valuation.py` | M_R, M_SDG, Exit Multiple, Equity Bridge, Archetypes |
| `backend/black_swan_registry.py` | 13 Black Swan events, evaluation engine |
| `backend/bu_profiles.py` | Default BU profiles + 5 industry verticals |
| `backend/side_tracks/__init__.py` | Side track registry + auto-registration |
| `backend/side_tracks/corporate_sdg/` | Corporate SDG 5-round track |
| `backend/side_tracks/brsr_ngrbc/` | BRSR NGRBC 5-round track |
| `backend/round_logic.py` | Session-level tick orchestration |
| `backend/router.py` | FastAPI routes for all player actions |
| `backend/admin_router.py` | Facilitator/God Mode admin routes |
| `backend/database.py` | PostgreSQL + in-memory session persistence |
| `backend/database_memory.py` | In-memory fallback (zero-dependency offline mode) |
| `backend/config.py` | Typed config constants from simulation_config.json |
| `blueprint.md` | Module blueprint & registry for all engine modules |
| `simulation_config.json` | Tuneable parameters (source of truth) |
| `DEPENDENCY_MAP.md` | Full static import-chain dependency map (2026-07) |

---

## Appendix B: Optimal Strategy Heuristics

Understanding what constitutes a "high M_R" path:

1. **R1**: Choose Deep Forensic Audit (B) → avoids R4 severity doubling.
2. **R2**: Score ≥80% on the materiality matrix AND choose Full Materiality Alignment (A) → `materiality_aligned` +0.10 M_R + ESRS compliance. (Accuracy alone earns nothing under Option C; Option B caps you at +0.05.)
3. **R3**: Choose Green Bond (B) or Rapid Switch (A) → set `early_decarboniser` for R7 synergy bonus.
4. **R4**: Full Transparency (A) → prevents ongoing SLO erosion.
5. **R5**: Nature-Based Solutions (B) → sets resilience, avoids insurance_only penalty, reduces NCD.
6. **R6**: Ethical AI Overhaul (B) → +0.15 Truth Premium.
7. **R7**: Waste-to-Energy (C) → `synergy_unlock` → +0.15 Synergy M_R.
8. **R8**: Water Efficiency for All (A) → preserves Resilience M_R bonus; avoids `electronics_water_priority`.
9. **R9**: Community Investment Fund (C) → +0.18 Community Champion M_R (amplified by consistent HR investment).
10. **R10**: Resist & Integrate (A) → requires synergy > 80 from R7 synergy unlock.

**Maximum achievable M_R without side tracks**: ~1.93 (before JT scaling)  
**Maximum M_R with BRSR Pioneer**: ~1.98  
**Maximum M_R with Corporate SDG (all A, score 105)**: M_SDG = 1.26 → TV boosted by 26%.

---

## 16. Runtime Dependency Map

> Added 2026-07-08. Full static map is in `DEPENDENCY_MAP.md` at the project root.

### Application Entry Point

`backend/main.py` starts the FastAPI server. At startup it:
1. Detects whether PostgreSQL is reachable — selects `database.py` (PostgreSQL) or `database_memory.py` (in-memory fallback).
2. Injects the selected db module as `sys.modules["database"]` so all routers share the same backend.
3. Mounts 5 routers: `simulation_router`, `admin_router`, `teleprompter_router`, `resources_router`, `analytics_router`.
4. Seeds missing facilitator cohorts on startup.

### Layer 1 — Routers

| Router File | URL Prefix | Responsibility |
|---|---|---|
| `router.py` | `/api/*` | All player-facing simulation endpoints (tick, login, decisions, stakeholder map, CEO interview) |
| `admin_router.py` | `/api/admin/*` | Facilitator + God Mode admin endpoints; WebSocket broadcast manager |
| `admin_teleprompter.py` | `/api/admin/teleprompter/*` | Live teleprompter and slide presentation endpoints |
| `admin_resources.py` | `/api/admin/resources/*` | File upload/download, quiz bank management |
| `admin_analytics.py` | `/api/admin/analytics/*` | Session analytics, real-time score aggregation |

### Layer 2 — Core Infrastructure

| Module | Depends On | Purpose |
|---|---|---|
| `config.py` | stdlib, dotenv | All env vars: DATABASE_URL, MASTER_PASSWORD, SIM_ROUNDS, carbon price, etc. |
| `database.py` | config | PostgreSQL async pool (asyncpg) |
| `database_memory.py` | config | Thread-safe in-memory dict store; optional SQLite snapshot |
| `materiality_db.py` | stdlib | JSON-backed materiality issue store (no DB connection required) |
| `admin_shared.py` | config | Shared in-process mutable state: `_facilitator_registry`, `_god_mode_settings` |
| `models.py` | pydantic | Pydantic request/response models |
| `password_hashing.py` | bcrypt | Password hash / verify / upgrade helpers |
| `auth_jwt.py` | jose, fastapi | JWT token issue, verify, cookie management |
| `option_shuffle.py` | stdlib | Deterministic option shuffling per player |

### Layer 3 — Simulation Engine

| Module | Key Local Imports | Role |
|---|---|---|
| `engine.py` | rng_util, config, stakeholder_sentiment, systemic_risk_engine, sdg_configs | Core tick processor — advances game state each round |
| `round_logic.py` | round_configs, impact_engine, config, healthcare_configs, npc_stakeholders, pedagogical_engine, round_analytics, dynamic_cases, biodiversity_engine | Pre/post tick; calls `run_new_engines()` |
| `impact_engine.py` | round_configs | Computes ESG impact deltas per decision |
| `rng_util.py` | stdlib (hashlib) | Deterministic per-cohort RNG seeding |
| `round_configs.py` | stdlib | Loads per-round configuration; reads simulation_config.json |
| `pillar_configs.py` | stdlib | ESG pillar option configuration |
| `healthcare_configs.py` | stdlib | Healthcare vertical round options |

### Layer 4 — Extended Engine Modules

All 39 modules below are actively imported by the core routers or engine. **None are standalone scripts.**

| Module | Imported By | Description |
|---|---|---|
| `autonomous_agents.py` | router | Autonomous NPC agent logic |
| `balance_sheet.py` | router | IAS 1 balance sheet engine |
| `biodiversity_engine.py` | round_logic | Biodiversity impact scoring |
| `black_swan_registry.py` | admin_router | Fat-tail stochastic event registry |
| `board_governance.py` | router | Board governance decision layer |
| `branching_engine.py` | router | Narrative branching logic |
| `brsr_controller.py` | admin_router | BRSR/NGRBC track controller |
| `bu_profiles.py` | admin_router | Business unit profile definitions |
| `ceo_diary.py` | router | CEO diary narrative system |
| `ceo_interview.py` | router | CEO interview dialogue engine |
| `consequence_dna_api.py` | router | Consequence chain API |
| `dynamic_cases.py` | router, round_logic | Dynamic case injection |
| `elevenlabs_tts.py` | router | ElevenLabs TTS voice integration |
| `email_service.py` | admin_router | Email dispatch (SMTP) |
| `ending_pathways.py` | router | Game ending pathway logic |
| `journey_improvements.py` | admin_teleprompter | Player journey improvement suggestions |
| `meadows_leverage.py` | router | Meadows leverage point analysis |
| `npc_stakeholders.py` | round_logic | NPC stakeholder behaviour |
| `org_politics.py` | router | Organisational politics layer |
| `pedagogical_engine.py` | round_logic | Pedagogical scaffolding logic |
| `real_world_parallels.py` | admin_teleprompter | Real-world case parallel data |
| `regional_reporting.py` | admin_router | Regional reporting aggregation |
| `regulatory_sandbox.py` | router | Regulatory sandbox simulation (CSRD/ESRS gate) |
| `round_analytics.py` | round_logic | Per-round analytics computation |
| `round_recap_engine.py` | admin_teleprompter | Round recap generation for facilitators |
| `sdg_configs.py` | engine, router | SDG configuration and linkage data |
| `sdg_linkage_engine.py` | router | SDG linkage scoring engine |
| `shadow_board_audit.py` | router | Shadow board audit layer |
| `stakeholder_db.py` | admin_router | Stakeholder persistence helpers |
| `stakeholder_sentiment.py` | engine | Stakeholder sentiment scoring |
| `supply_chain_network.py` | router | Supply chain network model |
| `systemic_risk_engine.py` | engine | Systemic risk calculation |
| `tcfd_scenarios.py` | router | TCFD climate scenario data |
| `teachable_moments.py` | admin_analytics | Teachable moments identification |
| `terminal_valuation.py` | consequence_dna_api, ending_pathways | Terminal valuation model (M_R, M_SDG, archetypes) |
| `vertical_stakeholders.py` | admin_router | Industry vertical stakeholder sets |
| `config_excel.py` | admin_router | Excel-based session config reader |
| `materiality_config_excel.py` | admin_router | Materiality config Excel reader |
| `stakeholder_config_excel.py` | admin_router | Stakeholder config Excel reader |

### Layer 5 — Sub-Packages

**`backend/side_tracks/`** — Plugin system for all 6 side tracks. Each sub-directory contains `__init__.py`, `configs.py`, and `track.py`. The registry in `side_tracks/__init__.py` auto-discovers tracks on import.

**`backend/verticals/`** — Industry vertical profiles. `verticals/__init__.py` re-exports all four vertical data sets (Oil & Gas, Banking/FS, Retail/FMCG, Agriculture). `vertical_stakeholders.py` references these for BU substitution.

### Dependency Rules for New Development

- **New feature module → per-request**: import in `router.py` or `admin_router.py`.
- **New feature module → per-tick**: import in `round_logic.py` or `engine.py`.
- **Admin/facilitator only**: import in one of the `admin_*.py` modules.
- **One-shot script** (data migration, doc generator): place in `scripts/` or `temp_archive/` — do NOT import from any runtime module.
- **Never import `router.py` or `admin_router.py` from an engine module** — this creates a circular dependency.
- **Database access pattern**: always `import database as db` (resolved by main.py injection). Never import `database_memory` directly in engine modules.

---

## 17. Codebase Provenance & Refactor Log

### 2026-07-08: Refactor-by-Isolation

A full static dependency trace was performed from `backend/main.py`. **139 files** were identified as non-runtime (one-shot scripts, versioned document duplicates, ad-hoc test scripts, output artifacts) and moved to `/temp_archive/` in the project root. The running application was not affected.

**Files protected (never moved):** All 46 core runtime Python modules, `backend/tests/` (29-file organized test suite), `backend/side_tracks/`, `backend/verticals/`, `frontend/` (Next.js app), all Docker/env/infrastructure files, `sessions.json`, `backend/market_dynamics.py`.

**Safety documents created:**
- `SAFETY_MANIFEST.txt` — logs every moved file, its original path, archive destination, and rationale.
- `revert.py` — run `python revert.py` to restore all 139 files from `/temp_archive/` to their original paths.
- `DEPENDENCY_MAP.md` — full layer-by-layer dependency reference for ongoing development.

**Archive breakdown:**

| Category | Description | Files |
|---|---|---|
| A | Root-level one-shot document generators | 38 |
| B | Root-level ad-hoc test scripts | 8 |
| C | Root-level output artifacts (.txt, .json, .html) | 5 |
| D | Backend one-shot patch/audit/verify scripts | 32 |
| F | Superseded versioned .docx duplicates (v2–v9/v10) | 35 |
| G | docs/ generators + duplicate .docx | 14 |
| H | scripts/ one-shot utilities | 7 |
| **Total** | | **139** |

**Latest document versions retained at project root:**
- Facilitator Manual: `Muressons_Facilitator_Manual_v10.docx`
- Student Manual: `Muressons_Student_Manual_v9.docx`
- Simulation Briefings: `Muressons_Simulation_Briefings ver 11.docx` + `ver 11_with_CEO_Debrief.docx`
- Technical Glossary: `Muressons_Technical_Glossary_with_CAROIC.docx`

### Infrastructure & Architecture History

| Date | Change |
|---|---|
| 2026-05 | Initial production deployment; PostgreSQL + in-memory fallback (SEC-2) |
| 2026-05 | JWT authentication hardening (SEC-6); CORS whitelist (AUDIT-011) |
| 2026-05 | Security headers middleware (HIGH-010); generic error handler (LOW-009) |
| 2026-05 | Admin router split into sub-routers: teleprompter, resources, analytics (ARCH-002) |
| 2026-05 | 111 automated tests across 29 test files in `backend/tests/` |
| 2026-07-08 | Refactor-by-isolation: 139 non-runtime files archived; DEPENDENCY_MAP.md written |

---

*Last updated: 2026-07-08 | Maintained by the Muressons simulation engineering team.*
*Reference files: `round_configs.py`, `pillar_configs.py`, `ending_pathways.py`, `terminal_valuation.py`, `black_swan_registry.py`, `bu_profiles.py`, `side_tracks/`, `DEPENDENCY_MAP.md`*

---

## Engine repairs — full-course impact audit (2026-08-31, branch `fix/full-course-impact-audit`)

Behavioural changes shipped after the whole-course audit (companion to the Round 2
repair of the same date). **Do not apply to a mid-course cohort — cohort-boundary only.**

- **C-1** `social_license_delta` is applied in ALL ten rounds. It moved into
  `_apply_common_impacts` (guarded per round, legacy mode only); R1/R2/R3/R7/R10 had
  silently discarded it (a ±23-point swing on the lever behind the −0.40 Instability
  Discount). R10 applies its own delta in-handler, before the M_R instability check
  reads the closing SLO average.
- **C-5** Round 2 now charges its chosen option's `treasury` (Option A: −$2.5M via the
  green-fund-aware applier, before the Option C clawback). Option A no longer strictly
  dominates Option B — the tiered premium trade-off is real again.
- **C-2** `natural_capital_debt_delta` likewise applies generically (R5/R8 deferrals
  preserved; R10 in-handler before the DMAV solvency gate).
- **C-3** The social-media velocity amplifier escalates for real: 1.1× in R4 up to
  1.7× in R10, applied every round from R4 on while group reputation < 60 (design
  ruling: persistent escalation).
- **C-4** One spelling per impact concept: `reputation` and `social_license_delta` are
  canonical; `reputation_delta` and `social_license` were migrated out of the configs
  and are honoured as read-aliases for ONE release only.
- **B-1** `just_transition_passed` (6 social-ESG points) = R9 `managed_transition` OR
  `community_fund`. The old test read two never-written flags and then the ROUND 10
  choice; it now agrees with the +0.12 M_R just-transition bonus.
- **B-2 / B-3** `scope_3_transparency` (R3 ≥80% Scope 3 completeness) and
  `retraining_succeeded` (R9 ITEM 20 outcome) are now written; both reads were dead.
  The R9 retraining clawback's `reputation_applied_r9` read is also live for the first
  time — failed retraining actually claws back 30% of the R9 reputation gain.
- **B-4** `electronics_blindspot_doubles_crisis`, `stochastic_event`,
  `low_social_license_strike_trigger` and `regulatory_friction_enabled` are read by the
  code that implements them (default True) — real facilitator switches now.
- **C-6** `divest_all` stays declared but inert, pending a design ruling.
- **Ceilings unchanged**: M_R max 1.93 / 2.02 (with JT scaling), pinned by
  `test_mr_ceilings_unchanged`. The financial golden trace was rebaselined in the same
  branch. Invariants live in `backend/tests/test_engine_invariants.py` (7 test
  families; the AST-resolved impact-key coverage check is the acceptance criterion).

### Addendum — pillar-mode impact ownership (2026-08-31, branch `fix/pillar-impact-ownership`)

In pillar (multi_toggles) mode, the router is the single applier of option impacts
for R1–R9 (aggregates × effectiveness); the legacy A/B/C translation is bookkeeping
only and its config impacts no longer stack on top (they silently did, every round,
until this fix). Round 10 is the exception: the pillar selections map to an A/B/C
ending whose full impact set — including, newly, its SLO and NCD — is the single
impact source, and R10 pillar aggregates are not applied. `pillar_cost_applied` is
always set on pillar commits, even at zero cost. Open design item: pillar options
declare no revenue impacts, so pillar mode currently has no decision-driven revenue
lever — the pre-fix leak was masking this. Cohort-boundary shipping only.

### Addendum — single M_R arbiter + EU AI Act enforcement (2026-08-31, branch `fix/mr-single-arbiter`)

`terminal_valuation.calculate_mr` is now the ONLY Regenerative Multiple formula: the
R10 award equals the mid-game projection exactly. Thresholds are GAME-2 ramps (±5
points around SLO 75 / readiness 75 / burnout 20), the synergy premium requires
`synergy_unlock` AND synergy multiplier ≥ 0.80 (waste_to_energy alone no longer
qualifies), and one global clamp [0.0, 2.05] governs the final M_R after ending-
pathway bonuses and the hostile-takeover cap — pathway stacking previously reached
~2.58 unclamped and penalty stacks could go negative. Default-pathway maxima stay
1.93 / 2.02 (JT-scaled). Separately, the EU AI Act threat shown at R6 Monetise is
now real: $3M conformity assessment + governance +5 once at R7, then $1M/round
ongoing monitoring while `ai_monetised` stands (it previously never fired — dead
code). Behavioural at thresholds and pathway extremes only; cohort-boundary
shipping.

### Addendum — seeded stochastics (2026-08-31, branch `fix/seeded-stochastics`)

The R5 cyclone, R5 NBS establishment, R9 strike and R9 retraining rolls now draw
from the GAME-4 per-cohort streams (`rng_util.event_rng`) like every other
stochastic engine: all teams in a cohort meet the same events, and a graded run
replays exactly from its `stochastic_seed`. Unseeded/legacy contexts keep the
historical module-RNG behaviour unchanged. The money path now makes zero
un-seeded random draws (tripwire test holds it there).

### Addendum — config-driven greenwash claims + strike doc parity (2026-08-31, branch `fix/greenwash-claims-strike-docs`)

Which options constitute a public green/ESG claim is now per-option config
(`green_claim: "full"` = 15% investment threshold / −15 SLO; `"moderate"` = 10% /
−7.5; absent = never greenwash-checked) instead of the positional rule that
treated every Option A/C as green — so Deny & Deflect, CEO-Only Sign-Off,
Immediate Closure and Divest can no longer trigger greenwashing scandals, while
green bonds, offsets, circular redesigns and net-zero claims remain fully
checked. The technical glossary's strike-engine entries are generated from the
R9 config (50% base below SLO 50; burnout adds up to +20pts, cap 95%).
