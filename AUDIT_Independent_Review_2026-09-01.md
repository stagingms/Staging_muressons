# Muressons-sim — Independent Code Audit

**Date:** 2026-09-01/02 · **Scope:** backend (`backend/`, 75.6K lines Python), frontend (`frontend/app`, 84K lines JS), schema, deploy config, docs · **Snapshot audited:** working copy at `C:\Users\Home\.gemini\antigravity\scratch\muressons-sim`, in sync with `origin/main` @ `81c23f9` · **Method:** full read of the engine and round-advancement path, targeted reads of routers/stores/auth, and executable probes over the real HTTP surface against both the in-memory store and a real PostgreSQL 16 (production store). No code was modified. Probe scripts are listed in Appendix B.

---

## 0. Overall assessment

**Not safe to run with 30 cohorts as-is.** The engine is directionally sane (green strategies beat extractive ones) but four defects in the core model mean the numbers students see are wrong in ways they can and will notice: group reputation is recomputed from scratch every round, so every reputation consequence of a decision vanishes at the next commit; a units error pins the cost of capital at the 20% cap from round 1 for every team, which forces the exit multiple to its 6× floor (not the documented 12×) and disables the whole ESG→WACC teaching loop; a second units error makes the CBAM levy $100,000/tCO₂e, which under the production database (and only there — the test suite cannot see it) takes $80–110M off any Advanced-Climate team in round 3; and several "flow" penalties are compounded permanently into the revenue/OPEX base, so an extractive team ends with OPEX 15× revenue and a terminal value of −$2.4B. On the platform side, any logged-in facilitator can list every cohort on the platform including every team's plaintext initial password, and can lock, shock or re-roster cohorts they do not own; player identity is a spoofable header; and ≥40 simultaneous commits (plausible when 150 teams share round timers) deadlock the single worker with no error surfaced. Fix the items in §7 "Before launch" and this becomes a defensible classroom tool; the rest of the codebase — input validation, JWT handling, SQL parameterisation, the round state machine — is in better shape than the "vibe-coded" label suggests.

---

## 1. Reconnaissance and baseline

### 1.1 What the system is
* **Per-team simulation state.** Each team is a *sub-session* (its own `global_state` + `bu_states` rows per round) linked to a *cohort* session via `parent_cohort_id` (stored inside `sessions.metadata` JSONB, not a column). A team's "commit" (`POST /api/simulations/{sid}/commit-turn`) runs the engine for that team alone and inserts the next round. Cohort-level "advancing" is really pacing (`unlocked_round`) plus an optional force-advance that auto-commits stragglers.
* **Engine:** `backend/engine.py::process_tick` (4 layers: stochastic → financial → operational → reporting) wrapped by `round_logic.pre_tick/post_tick/run_new_engines` and orchestrated in `router.py::_commit_turn_impl` (L2077–2949). Terminal valuation lives in `round_logic._post_r10_grand_finale` (L2210–2960), *not* in `terminal_valuation.py`, which is a partially-used library.
* **Data model:** two stores with a parity contract — `database.py` (asyncpg/Postgres, production) and `database_memory.py` (dicts + JSON snapshot, dev/tests). Schema in `db/init.sql` + inline DDL in `database.py`. Global state extras are packed into `active_event_flags` JSONB; BU extras go into `risk_factors` JSONB **in Postgres only** (the memory store whitelists BU fields — §3.1 F-05).
* **Auth/authz:** facilitators use a signed HS256 JWT cookie (`auth_jwt.py`) with a role ladder in `admin_shared.ROLE_HIERARCHY` and guards `require_facilitator/sim_manager/lead_facilitator/super_admin`; session ownership is a separate, per-endpoint call `_assert_session_ownership`. Players have **no token**: identity is the plain `X-Player-Id` header compared to the session's owner (`router.py::_assert_player_owns_session`, L232–285).
* **Deploy:** Railway, Docker, `docker-start.sh` → `scale_preflight.py` clamps to **one worker** unless `MURESSONS_MULTIWORKER_VERIFIED=true` (the code itself lists ~12 per-process stores that make multi-worker unsafe). Facilitator registry, bans, token versions, JWT secret live as JSON files under `MURESSONS_DATA_DIR` (must be a mounted volume).

### 1.2 Assumptions made
1. Production runs **Postgres, one gunicorn/uvicorn worker**, as `scale_preflight.py` enforces by default. Where memory-mode and Postgres behave differently I say so and tested both.
2. The seed in `db/seed_round1.json` is the classroom seed (the docs' BU table in `SIMULATION_CONTEXT.md §2` disagrees with it — see F-30).
3. Rules documents of record are `SIMULATION_CONTEXT.md`, `MODEL_CARD.md`, and the docstrings/config comments; where they conflict with code I flag the conflict rather than pick a side.
4. "30 cohorts × several teams" ≈ 150 teams plus observers; drivers poll `/dashboard` every 5 s (`useSimulation.js` L665–731).

### 1.3 Test baseline (run by me)
| Suite | Result | Notes |
|---|---|---|
| `backend/tests` (memory store) | **2249 passed, 2 failed, 8 skipped** in 48 s | Both failures are `test_deploy_image_hygiene.py` needing `git ls-tree` on a git checkout — they pass on the real repo (seed files are tracked). 6 skips are the PG parity suite, 1 is an allow-listed dead impact key (`divest_all`), 1 is data-dependent. |
| `tests/test_postgres_parity.py` against real PG 16 | **6 passed** | |
| `frontend` jest | **1098 passed, 1 failed, 4 skipped** | Failure is `player-visibility-wiring.test.js:268`, a brittle source-parsing tripwire that matches a *comment* mentioning `COHORT_OVERRIDABLE_KEYS` (admin_shared.py:296) before the real definition (L457); the keys it looks for are present (L519–520). Not a product regression, but the frontend suite is red. |
| `pip install -r backend/requirements-dev.txt` | **fails** | `pytest==8.3.4` is pinned but `pytest-asyncio==1.4.0` requires `pytest>=8.4` (`ResolutionImpossible`). `.github/workflows/ci.yml` installs exactly this file, so **CI cannot currently run** and the "Wait for CI" deploy gate protects nothing. (F-37) |

Coverage note: the suite is broad (160 files) but runs almost entirely on the memory store; several production-only defects below (F-05, F-06) are invisible to it by construction.

---

## 2. Findings — Category 1: Mathematical and logical correctness of the engine

Severity key: **Critical** = wrong results shown to students / data leak / crash under normal use; **High**; **Medium**; **Low**.

### F-01 · Critical · Group reputation is memoryless — every reputation consequence is discarded at the next commit
**Where:** `engine.py` L2865 (`ctx.group_reputation = calc_contagion(ctx.new_bus, ctx.crisis_severity)`), L4190 (assembled into next state); `calc_contagion` L409–483 reads only BU `reputation_score`. Writers of `group_reputation` that are therefore wiped: option impacts `round_logic.py` L1278–1284 (`_apply_common_impacts`), round handlers L499, L1412, L1672, L1709, L1755, L1889, L1966, L2039, L2108, L2481, L2490; stakeholder-map penalty `router.py` L4323; materiality penalty L3916; facilitator shockwaves/custom events `admin_router.py` L6487, L6667; side-track bridge deltas `engine.py` L286.
**Mechanism:** `group_reputation_next = mean(BU reputation_score) − CONTAGION_MAX_DROP·σ((severity−30)/15)`. Nothing writes `group_reputation` back into BU `reputation_score`, and BU reputation is only ever *lowered* (natural decay L700–741, dividend ratchet L2633, one −15 at `round_logic.py` L1406). So the persisted `group_reputation` is a one-round display value.
**Evidence (probe `engine_proofs.py` §1, seed state):** input `group_reputation` 20 / 50 / 80 / 100 → output **47.29** in all four cases. Full-game traces show BU-average reputation frozen at 53.2 for 10 rounds while displayed group reputation bounces 50 → 49 → 44 → 46 → **4.2** (R4 crisis) → 37 → **0.0** (after a −20 option) → 4.9 → 41.6 → 27.6, with the `reputation_applied_rN` deltas (+2, +2, +4, +10, −5, −20, +4, +5, −15) each visible for exactly one round.
**Consequences:** (a) a team's reputation "recovers" 30+ points automatically after R4 without doing anything; (b) a facilitator shockwave's reputation hit lasts one round; (c) NPC satisfaction drivers weight `group_reputation` (`npc_stakeholders.py` L213–219, L262–266) so the artificially low, jumpy value feeds the SLO collapse in F-11; (d) brain-drain (threshold 65, `calc_talent_braindrain` L660) fires *every* round for every team because the baseline is ≈ mean−6 ≈ 47.
**Related (same root):** at severity 0 the sigmoid still removes 50/(1+e^{30/15}) = **5.96 points** every round; the frontend sends `crisis_severity: 0` (`page.js` L821), so for 9 of 10 rounds "contagion" is a constant −6 haircut, and in R4 (severity 40–100 from `_pre_r4_contagion`) it removes 33–46 points for one round.

### F-02 · Critical · Cost of capital is pinned at the 20% cap from round 1 by a units error → exit multiple is always the 6× floor
**Where:** `engine.py` L3161 passes `_avg_water = mean(water_dependency)` (0–100 scale; seed mean **54.25**) as `biodiversity_dependency` to `systemic_risk_engine.calc_esg_adjusted_wacc` (L19–37), whose formula `nature_premium = biodiversity_dependency × (1 − transparency/100) × 0.02` assumes a 0–1 input ("WACC 3%–15%, ±10% ESG swing").
**Calculation:** 54.25 × (1 − 30/100) × 0.02 = **+0.76** (76 percentage points) → `min(0.20, …)` clamps WACC to **0.20** every tick. Then the regulatory ratchet (L3749–3763) never lets it fall below its historical max. Probe §4: `cost_of_capital` by round with NCD = 0 and zero investment: `[0.05, 0.20, 0.20, … 0.20]`. The macro cycle (`_MACRO_RATE_CYCLES` L1125, ±1–2%), NCD→WACC (`MODEL_CARD §2.3`), SBTi/taxonomy surcharges and the Stranded-Asset premium are all invisible under the cap.
**Downstream:** R10 exit multiple = (1+g)/(WACC−g) = 1.02/0.18 = 5.67 → floored to **6.0** (`round_logic.py` L2637–2646, `terminal_valuation.calculate_dynamic_exit_multiple` L293–330). Every trace I ran, all strategies, all paradigms: `exit_multiple: 6.0`. Documentation says 12× default / 6–18 dynamic (`SIMULATION_CONTEXT §8`). Terminal values are therefore roughly half what the rules promise, and `MODEL_CARD §2.2` has rationalised the observed 20% as "stylized" rather than recognising it as this bug. The frontend live share price (`stockValuationEngine.js` L60–75) divides the 6× multiple by a 17× baseline, so the ticker shows a ~65% price collapse in round 1 for every team.
**Also:** debt-service interest on a negative treasury (L3063) and NCD compounding (L2941–2944) both use this 20%-per-half-year rate.

### F-03 · Critical (Advanced Climate on Postgres) · CBAM levy is $100,000 per tonne and fires only in production
**Where:** `engine.py` L3253–3273; `config.py` L412 `CBAM_SURCHARGE_RATE = 100_000`; `cbam_surcharge = Σ(scope1+2 tCO₂e) × 100_000`.
**Calculation (seed):** Scope-1+2 tonnage ≈ 21×18 + 18×16.5 + 12×10.5 + 7.8×8.5 ≈ 867–964 t → **$87–96M** (real EU CBAM ≈ €75/t; the code's own docstring calls this an "import carbon surcharge").
**Store parity twist:** the levy reads `bu["scope_1_ci"]`/`scope_2_ci` from the *previous* round's persisted BU state. Postgres packs every extra BU key into `risk_factors` and unpacks it (`database.py` L1185–1218, L989–998); the memory store persists a fixed whitelist (`database_memory.py` L857–884) that drops them → 0 → CBAM never fires in tests or dev. **Measured on real Postgres (`pg_probe.py`):** extractive team R3 `cbam_surcharge_applied = 107,620,172` (treasury $89M → −$1.7M), R7 $120M; a *balanced* all-B/20% team R3 **$81.4M** (treasury $69.5M → $3.5M). Same runs on the memory store: `cbam = None` every round.

### F-04 · High · "Flow" penalties compounded into the persistent base (ratchet economy, part 2)
The 2026-09-01 rulings made cash-conversion, FX, cannibalisation, micro-strike, NCD-opex and talent penalties transient (`ctx.record_transient`, reversed at L4354–4364). These were missed and still compound every round into `revenue_base`/`opex_base`:
* **Supply-chain contagion** L2453–2460: `opex × Σ_others(gov_risk) × 0.002` (`config.py` L378). Seed: pharma +7.6%, electronics +6.6%, consumer goods +8.6%, software +9.0% of OPEX **per round, permanently** — $2.64M/round vs $1.72M from 5% inflation (probe §5). In the extractive trace gov_risk reaches 97 → 58%/round → OPEX $34M → **$525M** by R10, treasury −$557M, TV **−$2.39B**. Direction is right; magnitude is nonsensical and it, not the ESG story, decides the loser's outcome.
* **DSO deferral** L2487–2503: `revenue_base −= deferred` (2–15% of revenue) is *not* transient, but the cash comes back to *treasury* next round as "Deferred Revenue Collection" (L2801–2813). Net: a timing effect permanently shrinks the revenue base ≈3.4%/round (probe §6: revenue +0.55% in a round with +4.27% revenue inflation). Ruling A fixed the sibling `calc_cash_conversion` line (L2510–2520) but not this one.
* **Green Premium Squeeze** L4024–4028: `revenue_base −= revenue × (60−SLO) × 0.005` — at SLO 0 that is **−30% of revenue per round, permanent**. This is what turned the naive "always option A" trace's revenue from $53.5M to $16.8M.
* **Supplier defection** L4017–4019 (`opex ×1.10`, `revenue ×0.95`, permanent multiplicative), employer-brand penalty L3181–3188, talent-allocation surcharge L2751–2758, technical debt L2838 — permanent by design or by omission; the code does not say which.
* Minor: the additive reversal is applied *after* multiplicative inflation, so a residual `delta × inflation` (≈0.2% of revenue/round) leaks into the base (L4349–4353 claims exactness; it holds only for stacking of additive deltas before any multiplier).

### F-05 · High · CapEx is never deducted from treasury; the balance sheet capitalises money that was never spent
**Where:** `engine.py` L2644–2730: `free_csf_limit = 0.20 × treasury`; `loan_principal = max(0, capex − free)`; `new_treasury = treasury + CSF − interest`. The only cost of CapEx is 12% interest on the portion above 20% of treasury, charged once (no loan balance is carried). Probe §3: capex $4 → treasury 63.4M; capex $10M → 62.3M; capex **$100M** (capped at 2× treasury) → 49.9M, i.e. $100M of CapEx costs $10.8M total. `MODEL_CARD §2.2` records "interest-only, principal never debits treasury" as a known simplification but describes the first 20% as "free" and the rest as "principal" — in code *all* of it is free apart from the interest line. Meanwhile `balance_sheet.py` L577–583 capitalises `total_capex_allocated` into PPE. Students who read the waterfall will see treasury *rise* in a round they "invested" $10M. Combined with `calc_synergy_opex` (F-06) this is the dominant incentive in the game.

### F-06 · High · Synergy OPEX reduction is −35% per round at a 25% ratio, compounding to a 35% floor
**Where:** `calc_synergy_opex` L510–530: `factor = 1 − √ratio × 0.7 × synergy`. Probe §7: ratio 0.05 → −15.7%/round, 0.25 → −35%, 1.0 → −70%, repeated every round until `synergy_opex_floor` (35% of first-seen OPEX, L496–507). In every trace OPEX hits the floor (~$14M from $34M) by R4–R5 and margins go from 36% to 70%+. Docs describe "diminishing returns"; the sqrt curve is diminishing *within* a round but the reduction is re-applied to the already-reduced base every round, so a modest, free (F-05) investment removes two-thirds of costs in four rounds.

### F-07 · High · Client controls engine parameters: `imitation_decay_rate`, `crisis_severity`, `emergency_credit_used`
**Where:** `models.py` L283–305 (fields on the *player* request), `router.py` L2386 (`crisis_severity=body.crisis_severity` → `pre_tick`), L2399 (`effective_crisis = pre_result.get(..., body.crisis_severity)`), L2429 (`imitation_decay_rate=body.imitation_decay_rate`). `pre_tick` overrides severity **only for round 4** (`round_logic.py` L243–246); for the other nine rounds the client value flows straight into `calc_contagion`. The model's own comment says "TECH-1: DEPRECATED — server derives crisis severity… Any value sent here is ignored" — it is not. Probe §12: `imitation_decay_rate=0.0` → synergy 1.5 → 1.5 (no decay); the security probe committed a round for another team with `imitation_decay_rate: 0` and got `201`. Also an inconsistency: the frontend hard-codes 0.05 (`page.js` L822) while `config.DEFAULT_IMITATION_DECAY_RATE = 0.10` and `process_tick`'s default is 0.10 — the config value is never used in live play.

### F-08 · Medium · Stakeholder fatigue (FEATURE 7) can never fire
**Where:** `engine.py` L2867–2880: `recovery_gap = max(0, ctx.group_reputation − mean(BU rep))`, but `group_reputation` was just computed as `mean(BU rep) − drop` with `drop > 0` always, so `recovery_gap ≡ 0`. Probe §2: 0 of 24 severity × crisis-count combinations fired. `SIMULATION_CONTEXT §12` lists it as a live mechanic; the event `stakeholder_fatigue_efficiency` also hard-codes `0.3` instead of `STAKEHOLDER_FATIGUE_FACTOR`.

### F-09 · Medium · Positional option effects on carbon intensity contradict the option configs
**Where:** `engine.py` L3144–3150: any `option_a` → CI −3, any `option_c` → CI +2, every round, in addition to the option's configured `carbon_intensity_delta`. Probe §11: R6-A "Monetise the Algorithm" gets the −3 "green tech" bonus; R9-C "Community Investment Fund" gets the +2 "dirtier ops" penalty; R1-A "Surface-Level Scan" is configured +2 and the engine adds −3 (net −1, opposite sign to the config). This is the same positional heuristic that DEEP-6 removed from the greenwash check. Also L3139–3142: comment says "up to −5%/round", code is `ratio × 0.10` (up to −10%). Net effect in the disciplined-ESG trace: revenue-weighted CI reaches **0.0** by R10 (a pharma/electronics conglomerate with zero emissions), which also zeroes its R10 carbon tax.

### F-10 · Medium · Units mismatches make three scored mechanics permanently inert
* **NCD thresholds:** `config.py` L178–184 `NCD_HARD_CAP = 1,000,000`, `NCD_WARN_THRESHOLD = 500,000`, `NCD_OPEX_SCALING_FACTOR = 50,000` are dollar-scale; BU NCD is an index (seed 0; docs say 30–200; 10 rounds of neglect reach ~2,170 — probe §10). The "credit downgrade" black-swan card (L2948–2960), the forecast countdown (L1762–1767) and the Advanced-Climate NCD OPEX penalty (L3277: NCD 1000 → **$250**) can never matter.
* **SDG 6 & 14:** `_SDG_MAPPING` L1871/L1879 thresholds 0.4/0.3 vs `water_dependency` 12–82 → `raw_score = 0` for every possible state (probe §9). Both SDGs are dead weight (1.6 of 9.3 total weight) in the SDG index and grade.
* **Regulatory ratchet baseline:** `REG_RATCHET_BASELINE 10` vs seed mean gov-risk 17.5 → an unavoidable **$3.75M** fine in round 1 and $1.25M in round 2 for every team before any decision takes effect (L3992–4002; visible in every trace's `regFine` column).

### F-11 · High · With the 2026-09-01 stakeholder defaults, SLO collapses to 0 for balanced play and the top archetypes are unreachable
**Where:** F2 continuous NPC pressure defaulted ON (`admin_router.py` L1322; `EVAL_Stakeholder_SLO_2026-09-01.md §2` still says "OFF by default"); `apply_stakeholder_slo_feedback` (`npc_stakeholders.py` L808–853) applies −2/−3.5 per hostile NPC per BU per round, coalition-amplified; NPC satisfaction is driven by the broken `group_reputation` (F-01).
**Evidence:** `slo_probe.py` — all-B/25% team: avg SLO 53.8 → 56.5 → 43.2 → 38.0 → 5.6 → **0.0** by R5, with `npc_slo_feedback` of −3 per NPC per BU each round from R2 and −5.25 in R4. Canonical-script traces (`run_trace.py`): balanced all-B/20% ends SLO 0, M_R 0.875; disciplined ESG script (B,A,B,A,B,B,A,A,C,A at 35%) ends SLO 56.9, M_R **1.18** → still "Fragile Giant". The repo's own `BALANCE_REPORT_BASELINE.md` agrees: `instability_discount` earned in **11/11** runs, `materiality_governance/synergy/truth/workforce` **0/11**, best strategy M_R 1.02. Whatever the pedagogy intends, no scripted or naive strategy can reach De-risked Safe-Haven (≥1.2), and the rules' M_R ceiling of 1.93–2.02 is theoretical.

### F-12 · Medium · Two terminal-value formulas; the live one omits M_SDG and never floors EBITDA
`terminal_valuation.calculate_terminal_value` (L456–560) implements `TV = (EBITDA₊ + GreenFund) × multiple × M_R × M_SDG` with EBITDA floored at 0 ("WARNING-3 fix"). The live R10 path `round_logic.py` L2516, L2647 computes `TV = (EBITDA + GreenFund) × multiple × M_R` — no `M_SDG` (the Corporate SDG side-track's documented 0.97–1.26 multiplier has no effect on results) and no floor (`BALANCE_REPORT_BASELINE` shows TV **−$2,021M**; my extractive trace −$2.39B with `price_per_share` floored at $1). `net_debt` defaults the revolver to $50M when the balance-sheet engine has not produced a ledger (L2652–2657).

### F-13 · Medium · `ci_baseline_r1` is read but never written; per-BU SBTi status is always "off track" from R2
`engine.py` L3314 uses `bu.get("ci_baseline_r1", current CI)` → target = current × 0.9178^(r−1) < current → `aligned=False` for every BU from round 2 regardless of decarbonisation. Group-level SBTi uses a fixed 36.25 baseline and is fine.

### F-14 · Low · Structural penalties at the seed and other boundary notes
Cannibalisation (L832–870): pharma (18M) and electronics (16.5M) exceed 1.15× the mean (13.4M) from round 1, so consumer goods and software lose 1–2% of revenue every round no matter what (transient, small). `calc_macro_noise` L1277 `randint(0, 3)` assumes 4 BUs (guarded by `% len` at L2540 — clean). Empty `choice_selected` silently becomes Option B (`_get_primary_choice` L3154–3164; probe: R1 ledger −$3M Deep Forensic Audit with `choice=""`). Momentum's NCD component reads `ncd_transparency` from flags — works but fragile.

### Category 1 — checked and clean
`calc_contagion` sigmoid algebra and clamps; `calc_synergy_opex` ratio clamp; `calc_natural_capital_interest` NCD floor; `calc_sdg_impact` phase ordering (CRITICAL-5 fix is correct); `_process_pending_projects` purity and accumulation; dividends clamped to treasury; CapEx capped at 2× treasury; austerity clamp uses pre-austerity ratio consistently; server-side `investment_ratio` recompute (`router.py` L2373–2378); option impacts applied exactly once (`test_engine_invariants`, passing); seeded per-cohort stochastics (`rng_util.event_rng`) for FX, noise, overrun, fog, offsets; R10 finale committed exactly once (`game_over` gate L2156).

---

## 3. Findings — Category 2: Internal consistency

### F-15 · High · Store parity: the memory store drops engine-written BU fields that Postgres keeps
`database_memory.py` L857–884 whitelists BU columns; `database.py` L1185–1218 packs everything else into `risk_factors` and L989–998 unpacks it. Fields that exist only in production: `scope_1/2/3_ci`, `absolute_emissions`, `supplier_defection_active`, `green_premium_squeeze`. Consequence: F-03 (CBAM) and anything else reading these next round behaves differently in production than in every test. The `PG_PARITY` CI job runs six tests and would not catch it.

### F-16 · Medium · Player-facing glossary teaches a stale M_R formula
`TechnicalGlossary.js` L273–274: "M_R = 1.0 + 0.30·synergy + 0.20·resilience + 0.15·truth − 0.40·instability; Maximum 1.65", and L284 "synergy_unlock → M_R +0.30". Backend `calculate_mr` (mirrored at `round_logic.py` L2574–2588 comment) has 11 components, synergy +0.15, max 1.93/2.02. `useSimulation.js` L440 (demo mode) still uses `synergy_bonus: 0.3`.

### F-17 · Medium · Frontend valuation surfaces disagree with the backend and with each other
* Live ticker `stockValuationEngine.js` L14–75: `price = 50 × EBITDA/19.2M × sentiment × (multiple/17)` with `ncdPenalty = NCD/100` (NCD 50 → −50% sentiment) — a different model from the R10 equity bridge; with WACC pinned (F-02) `multipleRatio = 6/17` → every team's share price falls ~65% in round 1.
* `RoundBriefing.js` L281–287 "preliminary valuation" uses `exitMultiple = 12.0` and `mrProxy = synergy × rep/60` — neither matches the R10 computation (6× and flag-based M_R). `rivalIntel.js` L139 benchmarks rivals at **17×** while the player is valued at 6×.
* `GameOverSummary.js` L705 falls back to 12× when the payload lacks it.

### F-18 · Medium · Naming/semantic drift
`group_reputation` (per-round derived) vs BU `reputation_score` (the real stock) — F-01. `investment_ratio` in the frontend is *capex / CSF pool*, in `apply_natural_decay` it is compared to absolute `capex_abs`, and in greenwash to `avg_capex ≥ $3M` — three thresholds for "invested enough". `crisis_severity` in `CommitTurnRequest` says "ignored", `router.py` uses it. `DEFAULT_IMITATION_DECAY_RATE` 0.10 vs frontend 0.05 vs docs 5%. `SIMULATION_CONTEXT §2` BU table (CI 35/72/48/12, OPEX 12/11.5/7.5/5.5M, NCD 120/200/150/30) vs `db/seed_round1.json` (CI 45/72/38/28, OPEX 11.5/10.8/7.8/4.2M, NCD 0). `EVAL_Stakeholder_SLO` says F1–F5 are OFF by default; `admin_router.py` L1320–1324 defaults them ON.

### F-19 · Medium · `run_new_engines` failures are swallowed per team
`router.py` L2526–2535 wraps the whole new-engines batch (balance sheet, NPC stakeholders, biodiversity, board, supply chain, agents) in `except Exception: _log.warning(...)`. One team hitting an exception silently gets a round with no stakeholder/balance-sheet update while its siblings do, and the round commits as if nothing happened. Same pattern for the sentiment update (`engine.py` L4122–4123) and hidden-resource triggers (`router.py` L2592). 47 bare `except:` blocks in `router.py`, 66 in `admin_router.py`.

### Category 2 — checked and clean
`historical_ebitda`/`tco2e_emissions` resync from the final BU table (L2559–2568) makes dashboard totals equal their rows; shockwave catalog and role hierarchy have drift tripwires that pass; `_bu_out` serialisation is consistent across dashboard/commit/history; option deshuffle is symmetric for saved drafts; currency-rate handling has tests.

---

## 4. Findings — Category 3: Security and access control

All probes in `security_probe.py`, run over HTTP against the app (two facilitators A and B, cohort A with one team; B is unrelated).

### F-20 · Critical · Any facilitator can list every cohort on the platform, including every team's plaintext initial password
`GET /api/admin/sessions` (`admin_router.py` L5114–5158) scopes by an **optional client-supplied query parameter** `facilitator_id`, not by the JWT; omit it and `fetch_all_sessions()` returns all cohorts with `registered_players` (`database_memory.py` L1207; Postgres `database.py` L1341–1361 does `sess_dict.update(metadata)`). Roster records carry `plaintext_password` until the student changes it (`admin_router.py` L4206, L5214, L5292). **Probe:** facilitator B received cohort A with `{"player_id": "MUR-RQD", "password": "$2b$12$…", "plaintext_password": "MUR-RQD@123", "must_change_password": true}`. `GET /api/admin/{cohort}/player-sessions` (L8380, `require_facilitator`, no ownership) then yields every team's session UUID.

### F-21 · Critical · Cross-cohort control: 51 of 87 session-scoped admin endpoints have no ownership check
`_assert_session_ownership` (L122–152) exists but is called on 36 endpoints. Unowned-cohort writes confirmed by probe as facilitator B against cohort A: `PUT /api/admin/cohort/{id}/pacing` → **200** (locked cohort A at round 1; `set_by`/`source` are taken from the *request body*, L10660–10661); `POST /api/admin/{id}/shockwave` → **200 "detonated", teams_hit: 1** (−$5M/−3 rep to every team; L6628); `POST /api/admin/{id}/generate-player` → **200** (minted a credential in cohort A; L5163). Also unguarded for ownership: bulk player upload (L5547), decade-plan, notes/bonuses/peer-evaluations (L9275–9507), BRSR decide (L9734), finale bell, situation-room bulletin, annotations (L11283–11307), side-track assignment (L11939), pedagogical settings (L10571), clone (L10989), what-if replay (L12122). `PATCH /sessions/{id}/metadata` (L4005, lead_facilitator) has no ownership check either and allows setting `facilitator_id` — a lead facilitator can take over any pre-start cohort. Reads without any auth at all (anonymous **200** in probe): `/api/admin/{id}/interventions` (L3869), `/api/admin/sessions/{id}/pacing` (L3509), plus `/practice-mode`, `/bu-composition`, `/r2-bu-selection`, `/complexity-events/{id}`, `/cohorts/{id}/side-tracks`.

### F-22 · High · Player identity is an unauthenticated header; defaults are deterministic and never enforced
`_assert_player_owns_session` (`router.py` L232–285) accepts any request whose `X-Player-Id` equals the session owner; there is no player token for HTTP (only a WS ticket). **Probe:** a cookie-less client with only `{session_uuid, "MUR-RQD"}` read the dashboard (**200**) and **committed a round** for that team (**201**). Player IDs are random 3-letter codes, but default passwords are the deterministic `MUR-XXX@123` / facilitator `FAC-NNN@321` (`admin_router.py` L218, L4166, L5195, L1942, sequential facilitator IDs), `must_change_password` is only *reported* at login (`router.py` L813, `admin_router.py` L2691) and never enforced by any guard — probe: login with `MUR-RQD@123` → **200 "rejoined"** and a facilitator with the default can use every admin route. Session UUIDs leak to any facilitator (F-20/F-21) and via URL/screen-share (acknowledged in the docstring).

### F-23 · Medium · 32 session-scoped player reads have no ownership check (44 of 73 player routes carry no guard at all)
Anyone holding a team's session UUID reads (anonymous **200** in probe): `/balance-sheet`, `/journey-responses` (student free-text), `/final-report`, `/consequence-dna-data`, `/sdg-dashboard`, `/shadow-board-audit`, `/side-tracks/*/history`, `/ceo-interview/results`, `/npc-stakeholders`, `/board-governance`, `/annotations`, `/front-page`, `/commit-notifications`, `/peer-trend-history`, `/session-info`, `/resources`, `/tcfd-scenarios`, `/leverage-analysis`, and more (enumerated by AST scan of `router.py`; the remaining unguarded routes are reference data such as `/pillar-config`, `/quiz/{id}`, `/stakeholder-map/master`).

### F-24 · Medium · Unauthenticated mutation and brute-force endpoints
`POST /api/simulations/set-username` (`router.py` L548–639) renames any player or facilitator with no auth — probe renamed player A and facilitator A (**200**, **200**) and it doubles as an ID-existence oracle. `POST /change-password` (L4365) verifies the old password with **no rate limit** — 40 rapid wrong attempts → all `403`, never `429` (login is rate-limited per id/IP; this path bypasses it). `POST /esg-profile-weights` (L3590, `require_sim_manager`) lets any facilitator change a **platform-wide** scoring setting in `_god_mode_settings`.

### F-25 · Medium · Committed break-glass credential and secret hygiene
`MASTER_PASSWORD: sim2026@iim` is committed in `.github/workflows/ci.yml` and `backend/tests/conftest.py`; the local `.env` on the audited machine sets `MASTER_PASSWORD=sim…` (same prefix). If production reuses that value, god_mode is public. Verify and rotate. Otherwise: no secrets in tracked files (grep of `git ls-files` for key/secret/password literals came back clean), `.gitignore` covers `.env`, JWT secret file, registry files. `PLAYER_MASTER_PASSWORD` is a second shared secret that unlocks *any* player account (`router.py` L716) — a design choice worth a second look.

### Category 3 — checked and clean
Facilitator JWT: HS256 pinned, `httponly`, `secure` (unless relaxed), `samesite=strict`, expiry = `JWT_EXPIRY_HOURS`, token-version revocation (`auth_jwt.py`). Websocket auth requires JWT or a signed, session-scoped ticket (`admin_router.py` L9109–9159). SQL is parameterised throughout (`database.py`; the only f-string is a constant `CREATE EXTENSION`). `PATCH /sessions/{id}/metadata` and the settings endpoints use explicit allow-lists (no mass assignment). Commit input validation: duplicate/unknown/missing BU ids, min $1 capex, option key validation, `decisions` bounded to 64, pydantic bounds on all numeric fields. CORS uses an explicit origin list with enumerated methods/headers (`main.py` L399–421); security-headers middleware present. Player login is rate-limited per player-id and per IP with persistent bans. bcrypt cost floor 12 outside pytest. Postgres immutability triggers on completed rounds, `uq_session_round`.

---

## 5. Findings — Category 4: Concurrency and scalability at 30 cohorts

### F-26 · Critical · ≥40 simultaneous commits deadlock the worker with no error
`database.py` L312–352: each commit holds one pooled connection for the advisory lock for its whole duration while its queries acquire *more* connections from the same pool (`DB_MAX_CONNECTIONS = 40`, `config.py` L45). Only the advisory acquire has a timeout (10 s, L334); the inner `pool.acquire()` calls have none. **Measured (`pg_deadlock_probe.py`, real PG):** 15/21/30 simultaneous R1 commits → all `201` in 0.4–0.7 s; **40 and 60 → hung >90 s, zero 503s**. With ~150 teams, a facilitator-paced round that opens at the same time across cohorts, or a shared deadline, can produce this; because there is one worker, every other request queues behind it. The code comment at L319–330 knows about the 2-connections-per-commit cost but sized the pool for one 20-team cohort.

### F-27 · High · Dashboard polling: 1 MB payload every 5 s per client, 2N+1 queries, no gzip
`useSimulation.js` L665–731 polls `/dashboard` every 5 s **without** `since_round` (the PER-1 optimisation exists but the poller does not use it). `get_dashboard` (`router.py` L1897–1994) returns the full round history, whose `active_event_flags` carry every engine event, so the payload grows to **~1.0–1.2 MB at R10** (`payload_probe.py`: 117 KB at R1 → 1,057 KB at R10; PG: 1,203 KB). On Postgres `fetch_round_history` (`database.py` L1038–1075) issues 1 + 2×rounds queries, and the handler then calls `_cohort_commit_progress` **and** `_cohort_advance_status`, each doing `fetch_latest_round` per sibling — ~30 round-trips per poll at R10 for a 5-team cohort. There is no `GZipMiddleware` (`main.py`). Measured on one worker with real PG: **~18–19 dashboard req/s** at R10 state. 150 drivers polling every 5 s = 30 req/s → the worker saturates on polling alone in late rounds, before observers (up to 5 per team) and admin dashboards; egress ≈ 30 MB/s.

### F-28 · Medium · Work that scales with platform size, not cohort size
`parent_cohort_id` lives in `sessions.metadata` JSONB (no column, no index; `database.py` L557). Sibling lookups therefore do `fetch_all_sessions_raw()` + Python filter on every leaderboard call (`router.py` L4830–4855, then `fetch_round_history` per sibling), and `detonate_shockwave`, `undo_round(cohort_wide)`, peer stats and cohort pulse do the same. Historic cohorts never leave the table. `_commit_locks`/`_commit_timestamps` dicts grow unbounded per process (L180–192).

### F-29 · Medium · Memory-store snapshot is O(total state) and synchronous on every write
`database_memory._persist` (L93–157) serialises the *entire* store to JSON on each `save_round` (and 12 other writers) under a lock, on the event loop. Measured: 40 sessions × 9 commits took **348 s (~1 commit/s)**; 40 R10 commits with 120 concurrent polls took 175 s. Production is Postgres, but the README recommends memory mode for workshops, and any multi-cohort workshop in that mode will crawl.

### F-30 · Medium · Blocking calls on the single event loop
bcrypt verify/hash at cost 12 (~180 ms) runs synchronously in async handlers (`password_hashing.py` L78–99; player login, change-password, facilitator login, roster generation). A 100-student "everyone log in now" moment serialises ~20 s of CPU on the loop. `openpyxl` roster/report generation and JSON snapshot writes are also synchronous. `random.seed()` on the global RNG inside `get_peer_leaderboard` (`router.py` L4771–4773) mutates process-wide state on every request (only cosmetic given the seeded engine streams).

### F-31 · Medium · Identity data on the filesystem, per-process caches, multi-worker not viable
Facilitator registry, token versions, bans, virtual-account profiles are JSON files (`admin_shared.py` L1350–1359 et al.) — durable only if `MURESSONS_DATA_DIR` is a mounted volume (documented in `DEPLOYMENT_CHECKLIST.md §2`); there is no file locking across processes. `scale_preflight.py` L86–108 enumerates ~12 per-process stores and forces one worker; `_session_players` must be lazily rebuilt after restarts (`router.py` L299–305, L392–398). Net: horizontal scaling is not available as a mitigation for F-26/F-27.

### Category 4 — checked and clean
Per-session asyncio lock with deterministic 409 on concurrent commit (`router.py` L2017–2029); Postgres advisory lock for cross-process exclusion (works at ≤30 concurrent); `uq_session_round` makes rounds 1–9 idempotent; R10 in-place update is protected by `game_over`; `expected_round` optimistic lock when the client sends it (the current client does); indexes exist on `session_id`, `global_state_id`, `round_number`; pacing/god-mode/freeze state is externalised to `coordination_state` on Postgres; WS fan-out has a shared-store path.

---

## 6. Findings — Category 5: Edge cases and resilience

### F-32 · Medium · Extended Horizon (rounds 11–20) is dead end-to-end
`POST /{sid}/extend` (`router.py` L6824–6905) inserts round 11 and clears `game_over`, but `_commit_turn_impl` L2136 rejects `current_round > 10` with 409 "Simulation has already completed all 10 rounds" (probe: activate → 200 round 11; commit → **409**). On Postgres the insert itself violates `round_number SMALLINT CHECK (BETWEEN 1 AND 10)` (`db/init.sql` L52, `database.py` L117/L151) → 500. The frontend also treats `current_round > 10` as game over (`useSimulation.js` L709).

### F-33 · Medium · Force-advance/timeout auto-commit picks a *random* option, not "Option B"
`_auto_commit_request` (`router.py` L356–384) hard-codes `choice = saved_decision_choice or "option_b"`; `_commit_turn_impl` L2301–2306 then **deshuffles** the choice as if it were a displayed key (correct for saved drafts, which are display keys, wrong for the literal default). The canonical option a straggler receives is whichever canonical key sits in display slot B for that session/round. The disclosure stamped on the round (L427–431) tells the student they got "Option B". Traced in code; consistent with the shuffle contract in `option_shuffle.py` L135–160.

### F-34 · Low · Facilitator "unlock next round" is a blind increment
`POST /sessions/{id}/pacing/unlock` (`admin_router.py` L3771–3794) does `unlocked_round += 1` with no idempotency, no cap at 10 and no relation to the cohort's actual round; a double-click or a retried request opens two rounds. A `relock` endpoint exists as the manual undo.

### F-35 · Low · Other edge behaviour observed
Empty `choice_selected` is accepted and silently becomes Option B (F-14). `expected_round` is optional (a stale bundle can still double-advance; guarded only by the 5 s cooldown). Late submissions are handled by pacing (`is_round_unlocked`) and cohort `max_round`; refresh mid-form is covered by `saved_allocations`/`saved_decision_choice`; double submission is covered by the per-session lock + `expected_round`; cohort restart (`reset_session`, `undo_round`) is super-admin/lead-only with an immutability-trigger toggle; team dropout is covered by force-advance (subject to F-33). These paths are exercised by the existing suite and behaved correctly in my probes.

---

## 7. Findings — Category 6: Code quality that affects correctness or maintainability

### F-36 · Medium · Swallowed exceptions on the critical path
See F-19. In addition `except Exception: pass` around `seed_effective_flags` (`router.py` L2501–2506) means a mid-run Switchboard change can silently not apply; the `MURESSONS_*` file persistence helpers print and continue on failure (`admin_shared.py` L1358, `database_memory.py` L156), so a full volume loses facilitator registry writes without an HTTP error (partly mitigated by disk-space health, `DEPLOYMENT_CHECKLIST §2b`).

### F-37 · High · Dev/CI dependency set does not resolve
`backend/requirements-dev.txt` pins `pytest==8.3.4` and `pytest-asyncio==1.4.0` (which requires `pytest>=8.4`). `ci.yml` installs this file in both jobs → CI cannot start → the Postgres parity deploy gate is not running. (Verified with `pip download` metadata: `Requires-Dist: pytest<10,>=8.4`.)

### F-38 · Medium · Duplicated and dead logic
`calc_revenue_weighted_avg_ci` and `_calc_rw_avg_ci` (`engine.py` L150–177) are identical; two terminal-value implementations (F-12); `check_bu_greenwash_scandal` was removed but its docs remain; `terminal_valuation.calculate_terminal_value` is never called by the live path; `divest_all` is a configured-but-inert impact key (allow-listed); 3 root-level `test_*.py` scripts and `dry_run.py` are `__main__` harnesses not collected by pytest; `revert.py`, `archive/` (206 MB local), `scratch/` are repo clutter. `admin_router.py` is 12.7K lines; `ExecutiveCockpit.js` 5.6K lines. 25 backend modules use `print()` for logging alongside the structured logger.

### F-39 · Low · Stale comments and docs that describe behaviour that no longer exists
`CommitTurnRequest.crisis_severity` "ignored" (F-07); `engine.py` L2282–2283 "All computation is identical to the previous monolithic implementation"; `MODEL_CARD §2.2` describing the 20% WACC as a design choice (F-02); `EVAL_Stakeholder_SLO` default-OFF statements (F-11); `SIMULATION_CONTEXT §2` seed table (F-18); `SIMULATION_CONTEXT §9` "strike probability override: 75%" vs `round_configs.py` L627 `0.50` (and `MODEL_CARD` says 50%); frontend glossary (F-16). Unused frontend deps: `@dnd-kit/sortable`, `styled-jsx`; `three`/`@react-three/*` pulled in for one component.

### Category 6 — checked and clean
Dependencies are otherwise used; pins are explicit with CVE notes; the engine is genuinely pure (deep-copies inputs, no I/O); config constants are centralised in `config.py` with provenance JSON; drift tripwires (role hierarchy, shockwave catalog, option constraints, pillar descriptions) are a good pattern and pass.

---

## 8. Prioritised fix list

### Must change before a 30-cohort launch
1. **F-01** Make reputation a stock: either persist `group_reputation` and let contagion *modify* it, or write option/shockwave reputation deltas to BU `reputation_score` (and retire the derived value). Re-run the balance report afterwards — NPC behaviour (F-11) will change.
2. **F-02** Pass `water_dependency/100` (or a real 0–1 biodiversity dependency) to `calc_esg_adjusted_wacc`; then re-examine the regulatory ratchet floor and re-baseline `MODEL_CARD §2.2`. Expect exit multiples to move off 6× and terminal values to roughly double.
3. **F-03 + F-15** Set `CBAM_SURCHARGE_RATE` to a per-tonne price in the €/$ 50–100 range (or express it as tCO₂e × price explicitly), and make the memory store pack/unpack extra BU keys exactly like Postgres so tests see production behaviour.
4. **F-20 / F-21** Scope `GET /api/admin/sessions` by the JWT, strip `password`/`plaintext_password` from every list/read response, and add `_assert_session_ownership` to all 51 session-scoped admin endpoints (ownership is one line each; the helper already exists).
5. **F-22** Issue a signed player token at login (the WS ticket code already exists) and require it on player routes; enforce `must_change_password` server-side; stop deriving default passwords from the ID.
6. **F-26** Cap concurrent commits below the pool (a semaphore of ~`DB_MAX_CONNECTIONS/2 − 2`), give inner `pool.acquire()` a timeout, or take the advisory lock on the same connection the commit uses. Load-test with 150 simultaneous commits before launch.
7. **F-27** Poll with `since_round`, add `GZipMiddleware`, drop `_prev_global_states`/`consequence_dna_snapshot` from the polled payload, and collapse the duplicate sibling scans in `get_dashboard`. Target <50 KB per poll.
8. **F-37** Fix `requirements-dev.txt` so CI runs again, then make the PG parity job run the full-run E2E and a CBAM/scope-key round-trip.

### Should change soon (first maintenance window)
9. **F-04** Record supply-chain contagion, DSO, green-premium squeeze and supplier defection as transient flows (same `record_transient` mechanism), or deliberately re-scale them; re-run the balance report. **F-05/F-06** decide whether CapEx debits treasury and cap the per-round synergy reduction; document whichever you choose in `MODEL_CARD`.
10. **F-07** Derive `crisis_severity` and `imitation_decay_rate` server-side from round config; remove them from the player request model.
11. **F-11** Re-tune F2 pressure and/or the SLO faucets so that a disciplined ESG script can clear the instability discount; the top two archetypes should be reachable.
12. **F-08, F-09, F-10, F-12, F-13** Dead/positional mechanics: delete or fix stakeholder fatigue, positional CI deltas, NCD/SDG unit thresholds, single TV formula with `M_SDG` and EBITDA floor, write `ci_baseline_r1` at session creation.
13. **F-23, F-24** Ownership on the 44 player GET routes; auth on `set-username`; rate-limit `change-password`; super-admin-gate `esg-profile-weights`.
14. **F-16, F-17, F-18** Align glossary, briefing valuation, ticker and rival benchmark with the backend formulas (ideally by serving them from the backend).
15. **F-19, F-36** Fail the commit (or at least surface a visible warning to the facilitator) when `run_new_engines` throws.

### Can wait
16. **F-28** Promote `parent_cohort_id` to an indexed column. **F-29** Debounce/offload the memory snapshot (or stop recommending memory mode for workshops). **F-30** `run_in_executor` for bcrypt/openpyxl. **F-31** Move registries to Postgres.
17. **F-32, F-33, F-34, F-35** Extended Horizon (fix or remove), canonical default option in auto-commit, idempotent unlock.
18. **F-38, F-39** Cruft: duplicate helpers, dead TV library path, root-level scripts, stale comments/docs, unused deps, print-logging.

---

## Appendix A — Coverage: what was checked and found clean (not repeated above)

* **Engine formulas read line-by-line:** all 30 numbered helpers in `engine.py`, `process_tick` and its four layers, `_assemble_global_state`, transient-reversal logic, `_process_pending_projects`, `calc_sdg_impact`, `calc_caroic`, `calc_forecast`, `calc_momentum_score`, `detect_distress`; `round_logic.pre_tick`, `_apply_common_impacts`, R4 severity handler, R10 finale valuation/archetype; `terminal_valuation` exit multiple and equity bridge; `systemic_risk_engine.calc_esg_adjusted_wacc`; `npc_stakeholders.apply_stakeholder_slo_feedback`; `option_shuffle`.
* **Round advancement:** `commit_turn` wrapper and `_commit_turn_impl` end to end, `_run_commit_locked`, `_auto_commit_laggards`, `_cohort_advance_status`, pacing unlock/relock, `activate_extended_mode`.
* **Persistence:** `create_session`, `save_round`/`insert_next_round`, `fetch_latest_state`, `fetch_round_history`, `fetch_all_sessions*`, advisory locks, pool config, `init.sql` schema and inline DDL, memory snapshot, `coordination_store`, `runtime_paths`, `scale_preflight`, `docker-start.sh`, `railway.json`, `ci.yml`.
* **Auth:** `auth_jwt.py` (token creation/decoding/cookie flags/WS tickets), `_assert_player_owns_session`, `_assert_session_ownership`, `require_*` guards, `rate_limit.py`, player login, join, change-password, set-username, facilitator listing; AST enumeration of all 73 player routes and 232 admin routes for guards.
* **Frontend:** commit payload construction (`page.js`), `useSimulation.js` polling/commit/resume, `stockValuationEngine.js`, `RoundBriefing.js` valuation, `GameOverSummary.js`, `TechnicalGlossary.js`, `PeerComparison.js` polling, dependency usage, jest suite.
* **Executed:** backend pytest (memory), PG parity suite (real PG 16), jest; 8 probe scripts (Appendix B) including 10-round games on both stores, direct engine proofs, a two-facilitator cross-cohort attack scenario, payload/latency measurement, and a Postgres pool-exhaustion test.
* **Not covered (out of time/scope):** side-track engines (`side_tracks/*`), healthcare/BRSR/UN-SDG paradigm-specific handlers beyond what the shared path exercises, CEO-interview LLM scoring, ElevenLabs/webhook integrations, the 20-tab/29-tab admin UIs beyond the endpoints they call, accessibility, i18n/currency display.

## Appendix B — Probe scripts (kept in the session workspace; not added to the repo)
`run_trace.py` (10-round HTTP games, canonical-option scripts, per-round table), `slo_probe.py` (SLO drivers per round), `engine_proofs.py` (12 direct `process_tick` proofs), `cbam_probe.py`, `payload_probe.py` (dashboard size/latency), `load_probe.py` (memory-store throughput), `security_probe.py` (two-facilitator cross-cohort + anonymous scenario), `extended_probe.py`, `empty_choice_probe.py`, `pg_probe.py` (production store trace), `pg_load_probe.py`, `pg_deadlock_probe.py`. All read-only against the app; none modify repository code. Happy to hand them over or turn the most useful into regression tests.

## Appendix C — Housekeeping
To read the code in the container I created `_to_delete/audit_snapshot.tgz` (9.5 MB, gitignored path) in the repo folder; delete it when convenient.

---

## Addendum — 2026-09-02, written while implementing §8 items 1–8 (branch `fix/launch-blockers`)

### F-40 · Critical · Player ids are unique only within a cohort; login resolves them platform-wide
**Where:** `backend/database.py` `generate_player_id` (uniqueness checked against the cohort's own `allowed_player_ids` only; 17,576-value `MUR-XXX` space); `backend/admin_router.py` bulk-upload and `induct_player` paths mint sequential `MUR-NNN` from `_next_player_id`, an in-process counter that **restarts at 1 on every deploy**; `router.py` `player_login` takes the first registry/roster record matching the id.
**Failure scenario:** cohort B's team `MUR-001` signs in with its default credential (`MUR-001@123`, derived from the id) and is placed in **cohort A's** `MUR-001` game — another team's decisions, results and roster (data leak, wrong game); or, once team A has personalised its password, team B is refused with "Incorrect password" and cannot play. Birthday bound for 150 random-letter ids ≈ 47% that at least one pair collides; for sequential ids after any redeploy a collision is certain.
**Evidence:** surfaced when the new Postgres parity tests ran against a database holding earlier probe cohorts — a freshly minted player could not log in because another cohort held the same id. Missed by the original audit.
**Fixed in the branch:** every mint checks the whole platform (`db.player_id_in_use`, deleted cohorts included); the sequential counter is seeded from every id ever issued and still checks each candidate; legacy collisions are resolved at login by which record's password verifies, and refused with `409 player_id_ambiguous` when even that is ambiguous. Random ids widened to four letters in the same branch (456,976 ids; three-letter ids stay valid).

### Correction to F-26
The report described ≥40 simultaneous commits as "hung >90 s with zero 503s". Re-instrumented: at 40 in flight every commit holds its advisory-lock connection and waits for a second one none will release; after `DB_ACQUIRE_TIMEOUT_SECONDS` (10 s) **39 fail with an unhandled `asyncio.TimeoutError` (HTTP 500) and 1 receives a 503 — none succeed.** The probe's `except asyncio.TimeoutError` caught the application's own exception and printed "HUNG". Severity unchanged (an entire round's commits rejected for everyone); mechanism is a 10-second total failure, not a hang. After the fix: 40/60/150 simultaneous commits all return 201 in 1.1/1.4/3.4 s.

### Status of §8 "Must change before launch" after the branch
Items 1–8 implemented, tested on both stores (memory suite 2283 passed; Postgres parity set 111 passed), documented in `CHANGES_launch_blockers_2026-09-02.md`. Two side findings hardened on the way (F-24: `/set-username` authorisation, `/change-password` rate limit). `MODEL_CARD.md` and `BALANCE_REPORT_BASELINE.md` rebaselined; terminal values are ≈2× the previous baseline because the exit multiple is no longer pinned at the 6× floor.

## Addendum 2 — 2026-09-02, written while implementing §8 items 9–18 (same branch)

### F-41 · High · The stakeholder-sentiment engine had never run
**Where:** `backend/stakeholder_sentiment.py` defines neither `initialise_sentiment` nor `update_stakeholder_sentiment`; `backend/round_logic.py::run_new_engines` imports both inside a `try` whose `except` printed `[WARN] … failed` and continued.
**Failure scenario:** every commit since the engine was wired raised `ImportError`, swallowed; `sentiment_stakeholders` / `sentiment_history` were never populated, so every UI surface and M_R component that reads them saw the empty default. Nobody noticed because the failure was a stdout line on the server.
**Evidence:** surfaced the moment F-36 replaced the `print` with `_engine_failed` (logged at ERROR and recorded in `events["engine_failures"]`) — the first full game after that change reported the ImportError on every round.
**Fixed in the branch:** both functions implemented; three full 10-round games (legacy_abc, advanced_climate, multi_toggles) commit over HTTP with an empty `engine_failures`.

### F-04b · High · Per-round penalties assessed after gross profit never reached cash
**Where:** `backend/engine.py` — the financial layer banks `new_treasury = base + CSF − …`; the talent retention premium and NCD OPEX penalty (rulings A/C, already transient at the baseline) and, after F-04, supplier defection and the green-premium squeeze, are recorded as transients in the operational/reporting layers *after* that line and reversed from the base before the tick ends.
**Failure scenario:** the penalty is applied to figures the treasury has already been computed from, then removed before persistence — it costs nothing, this round or next. The MODEL_CARD describes all four as costs. At the baseline the talent premium and NCD penalty were therefore narrative only; F-04 would have extended that to defection and squeeze.
**Evidence:** the treasury fingerprints — after F-04 the `multi_toggles` runner case (which triggers supplier defection every round) produced a fingerprint bit-identical to `legacy_abc`. Once the charge is real, the treasury-waterfall runner's DEFAULT_4_BU/legacy_abc case shows `Flow surcharges after gross profit` of −$0.9M … −$1.4M a round (talent premium + NCD penalty), and its multi_toggles case −$7.9M … −$11.2M (adding defection on four BUs).
**Fixed in the branch:** `TickContext.csf_banked`; a transient recorded after the banking line debits treasury directly, is evented (`post_csf_flow_adjustments_cash`) and waterfalled; the ledger conservation law gained the term and closes to 0.00 on every round of every runner case.

### Harness finding · `dry_run.py` measured a permanent crisis
**Where:** `backend/dry_run.py::_run_one` passed `crisis_severity=40.0` into `pre_tick`/`process_tick` for **every** round. Production sent 0 (client) and `pre_tick` overrides only the R4 crisis round to 40 — which is exactly what F-07's `base_crisis_severity_for_round` now derives server-side.
**Consequence:** the contagion dip at severity 40 is ≈31 reputation points, every round, so group reputation reached 0 by R4 in every scripted run and the talent premium ran at its maximum (×1.975 on software OPEX). `BALANCE_REPORT_BASELINE.md`, the calibration rulings' evidence and the F-11 verification were all measured on that game, not the deployed one. It went unnoticed because under the transient rule the maxed premium cost nothing (F-04b); with F-04b it bankrupted every strategy, which is how it surfaced.
**Fixed in the branch:** the runner uses the router's three server-derived values. Regenerated report: aggressive_green $891M / M_R 1.43 / SAFE_HAVEN, balanced $415M / 1.03, pure_B $148M / 0.92 (solvent); pure_A / pure_C / extractive bankrupt R7; no dead levers. F-11 verified against it: with F2 pressure ON the same disciplined bot reaches only M_R 1.03.

### Status of §8 items 9–18 after the branch
All implemented (F-31 deferred by decision, F-32 removed by decision). Memory suite 2311 passed / 2 skipped; Postgres CI list 116 passed; jest unchanged (1 baseline failure); eslint no new problems. Goldens, fingerprints and the balance report rebaselined; details in `CHANGES_launch_blockers_2026-09-02.md` ("Phase 3").
