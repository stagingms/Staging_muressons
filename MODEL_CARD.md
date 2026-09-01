# Muressons Simulation — Model Card

**Version:** 2026-09-01 (post engine-excellence campaign; see PLAN_Engine_Excellence_Roadmap.md)
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

### 2.2 Valuation

| Parameter | Shipped | Benchmark | Verdict |
|---|---|---|---|
| Exit multiple (`TV_EXIT_MULTIPLE_*`) | 6–18× EV/EBITDA, 12× at baseline WACC, WACC-coupled | 2026 sector multiples: household products ≈ 13.7×, pharma ≈ 18.6×, electronics ≈ 25.9×, application software ≈ 31.8× | `realistic-conservative` — 12× is below the blended market for the default BU mix, appropriate for a conglomerate discount; the 6–18 band brackets the non-tech range |
| Regenerative Multiple M_R | clamp [0.0, 2.05]; components per calculate_mr; pinned ceilings 1.93 (legacy) / 2.02 (pillar) | ESG valuation premia in the literature run ~10–30% of EV, not ±100% | `pedagogical` — deliberately amplified so ESG strategy dominates the leaderboard; the model's central teaching lever |
| Cost of capital | base ≈ 20%/period + macro cycle (−1% … +2%) + ESG-adjusted WACC premia | Real corporate WACC ≈ 7–11%/yr | `stylized` — a 6-month round carries roughly a year's worth of capital cost so that debt bites within the course; direction and ESG-coupling faithful |
| CapEx financing | 20% of treasury free (`FINANCIAL_FREE_CSF_PCT`), excess becomes principal at 12% (`FINANCIAL_DEFAULT_LOAN_RATE`), **interest-only — principal never debits treasury** (see DEEP-8) | BBB corporate lending ≈ 5–7%; principal amortises | `stylized` — the interest-only design is an explicit simplification; whether to amortise principal is an open design question recorded here |
| Insolvency floor | −$500M + $200M × ESG investment ratio (`FINANCIAL_TREASURY_FLOOR`), evented as Insolvency Floor Relief | Real firms enter administration far earlier | `pedagogical` — keeps failed teams playing to R10 while still ranking them last |

### 2.3 ESG–finance couplings

| Parameter | Shipped | Benchmark | Verdict |
|---|---|---|---|
| NCD → cost of debt (`NCD_INTEREST_COEFFICIENT`) | +1bp per NCD unit, compounding (NCD 500 ⇒ +5pts) | Corporate-bond studies find ESG-quartile spreads of tens of bps, not hundreds | `pedagogical` — amplified ~10× so natural-capital neglect becomes a visible debt spiral within 10 rounds; direction supported by the cost-of-debt literature |
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

## 3. Known limitations

1. **Interest-only CapEx** (§2.2): principal is never repaid from treasury; teams can
   over-lever without amortisation pressure. Recorded as an open design question.
2. **Round compression**: one round = 6 months, but several rates (WACC, inflation
   5%/round, NCD compounding) behave closer to annual rates, an intentional 2× speed-up.
3. **Pillar-mode balance is unmeasured headlessly**: the router owns pillar impact
   application, so BALANCE_REPORT covers legacy_abc only.
4. **Scripted-bot bankruptcy**: at bot capex levels every scripted strategy goes bankrupt
   by R4–R7 (BALANCE_REPORT §1). Real cohorts out-perform bots (minigames, side tracks,
   adaptive capex), but this is the current empirical difficulty floor — cross-check
   against cohort telemetry (roadmap W4.3) before recalibrating.
5. **M_R amplification** dominates terminal spread by design; instructors should present
   TV rankings as strategy quality, not market realism.
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
