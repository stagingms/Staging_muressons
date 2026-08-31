# Deep Engine Audit — Model Integrity & Cross-Engine Consistency
**Date:** 2026-08-31 · **Baseline:** `main` @ 8c0ec8b (post full-course + pillar repairs) · **Method:** executable sweeps + targeted deep reads; every HIGH finding verified by executing the engine against its own shipped configuration
**Scope:** the surfaces the 2026-08-31 impact audit left open (flags_set, stochastic paths, side tracks, healthcare/BRSR verticals) plus model-integrity axes it never covered: valuation math consistency, money conservation, RNG reproducibility, probability semantics, economic realism.

---

## Verdict in one paragraph

The impact-key surface repaired earlier today is sound — healthcare and BRSR both sweep clean, the pending-projects engine is a well-designed pure function, and the seed and ramp infrastructure (GAME-2/GAME-4) is good engineering. The problems this pass found are one level up: **the engine has two arbiters for its most important number (M_R) and they disagree; its most-advertised deferred consequence (the EU AI Act) is a bluff that can never fire; its highest-stakes dice rolls ignore the facilitator's fairness seed; 63% of all declared flags do nothing anywhere; and the money does not reconcile** (a documented, ratcheted gap of up to $656M/run). None of this blocks the current deployment — every finding is either invisible to players today or has been invisible for thirty cohorts — but items 1–4 below should be the next branch.

---

## Findings (verified, ranked)

### DEEP-1 · The EU AI Act enforcement is dead code — the R6 threat is a bluff · HIGH
**Verified by execution.** R6 Option A (Monetise AI) shows the player: *"Compliance audit costs will apply from Round 7."* The $3M charge + governance +5 lives inside `_post_r6_ai_bias` behind `"ai_monetised" in all_flags and round_number >= 7` — but that handler is registered only at `_POST_TICK_MAP[6]` and never runs again, and at its one invocation `prev_flags` cannot yet contain the flag it set this same round. Ten-round execution: `eu_ai_act_pending` fires at R6, `eu_ai_act_compliance` **never** fires (R7–R10 all silent). The only live consequence of `ai_monetised` is a +0.08 black-swan probability nudge. Same defect class as C-1: a promise the model makes and never keeps — except here the promise is shown to the player in so many words.
**Fix:** move the deferred charge out of the R6 handler into a recurring-consequence path that runs every round ≥7 (post_tick generic section, or a `recurring_liability` pending-project type — the pending-projects engine already has exactly the right shape). Decide once vs per-round charging with the design owner; the message says ongoing.

### DEEP-2 · Two M_R implementations disagree — the projection players see is not the formula the engine awards · HIGH
The engine awards M_R inline in `_post_r10_grand_finale`; `terminal_valuation.calculate_mr` is a second, divergent implementation used by `consequence_dna_api` (mid-game projected M_R shown for in-progress sessions) and `pedagogical_engine`. Three material divergences:
- **Synergy:** inline grants +0.15 for `synergy_unlock` **or `waste_to_energy`**, ungated. `calculate_mr` requires the flag **and** `synergy_multiplier ≥ 0.80`, ramped. Worse, `waste_to_energy` earning the "synergy" premium contradicts R7's own mutual-exclusivity design, where waste-to-energy is the path that *conflicts with* circular redesign.
- **Cliffs vs ramps:** `calculate_mr` ramps its thresholds (GAME-2); the inline engine uses hard cliffs (workforce ≥75, burnout <20, SLO <75). A team hovering at SLO 74.8 sees a mid-game projection ~0.4 higher than the final award.
- **Clamps:** `calculate_mr` clamps to [0, 2.05]; the inline engine has **no floor or ceiling at all** (see DEEP-3).
Also: the inline function carries three contradictory stated maxima in its own comments (2.08, 1.95, "+0.30 synergy") versus the actual 1.93.
**Fix:** single source of truth. `calculate_mr` already accepts a `pathway_bonuses` parameter — make the R10 handler call it and delete the inline duplicate. Expect a golden-trace rebaseline and edge-case behavioural deltas near thresholds (the ramps are the *better* pedagogy); cohort boundary.

### DEEP-3 · Pathway M_R stacking is unclamped — the pinned ceiling governs only one ending in five · MEDIUM-HIGH
The four alternate endings add pathway bonuses on top of base M_R with no clamp: climate_black_swan +0.65 max, stakeholder_revolt +0.65, regulatory_shutdown +0.65, hostile_takeover +0.60. Engine-side M_R can reach ≈2.58 (≈2.67 with JT scaling) — while `test_mr_ceilings_unchanged` pins 1.93/2.02 and `calculate_mr` clamps at 2.05. Downside is worse: penalty stacks (e.g. −0.40 stranded assets −0.50 revolt −0.20 shadow board on top of −0.40 instability) can drive M_R **negative**, flipping terminal value to a negative number against positive EBITDA — economically meaningless. The archetype gate (`regenerative_titan ≥ 1.8`) is also dramatically easier on some pathways than others.
**Fix:** explicit floor (≈0.1) and per-pathway ceiling at the engine; extend the ceiling test to all five pathways. Folds naturally into the DEEP-2 consolidation.

### DEEP-4 · Split-brain RNG: the facilitator's fairness seed doesn't reach the biggest dice rolls · MEDIUM-HIGH
GAME-4 lets a facilitator stamp `stochastic_seed` on a cohort; engine-side stochastics (FX, macro noise) honour it. But every post-tick roll in `impact_engine` — the R5 cyclone (up to −$20M+), the R9 strike (revenue-zeroing), retraining success, NBS establishment — uses the bare module-level `random.random()`: unseeded, shared across all concurrent sessions, non-reproducible. A facilitator who seeds a classroom for fairness gets deterministic *noise* and non-deterministic *catastrophes*, and two teams committing simultaneously interleave one global stream.
**Fix:** derive `Random(hash((stochastic_seed, session_id, round_number)))` per commit and thread it into post_tick; the seeded-RNG pattern already exists in engine.py to copy.

### DEEP-5 · 171 of 271 declared flags (63%) are read by nothing, anywhere · MEDIUM
Full-surface sweep (core, healthcare, pillar, all six side tracks) against every backend module **and** `frontend/src` (which references `active_event_flags` zero times). 171 flags exist only as stored strings: nearly the whole sustainability_reporting side track (18 flags), most healthcare vertical consequence flags (`union_busted`, `telehealth_litigation`, `closed_loop_water`…), most pillar bookkeeping flags, and `ceo_only_signoff` in the core game. Each is a consequence the config promises and the model ignores — the pre-repair F-7/B-4 class, at scale.
**Fix:** triage, don't wire blindly: (a) flags that should have mechanics → design ruling + writer/reader pairs; (b) flags that are genuinely narrative → move to a documented `narrative_tags` field so the invariant can distinguish them; (c) delete the rest. Then add the inverse of the existing flag-writer test: every *declared* flag has a reader or an allow-list reason.

### DEEP-6 · The greenwashing engine thinks "Deny & Deflect" is a green claim · MEDIUM
`calc_greenwashing_risk` classifies **every** `option_a`/`option_c` in **every** round as "green" (option_b as "moderate"). So R4 Deny & Deflect, R9 Immediate Closure, R2 CEO-Only Sign-Off, and R10 Divest can all trigger a *greenwashing* scandal ("your green rhetoric doesn't match your investment") when capex is thin — a semantically wrong penalty with a player-facing message asserting they made a green claim they never made. (The related COR-1 behaviour — `investment_ratio` in the API is overridden by a capex-derived recompute — is deliberate and tested, but deserves a note in the API schema; the submitted field is accepted and ignored.)
**Fix:** replace the positional heuristic with a per-option `green_claim: true` config key — the same config-driven treatment B-4 gave the special_rules switches. One sweep to tag the genuinely green options, engine reads the key.

### DEEP-7 · The strike engine is documented three incompatible ways · MEDIUM (docs)
Code: flat 50% below SLO 50 (`strike_probability_override: 0.50`) + burnout boost up to +0.20, cap 0.95. The student-facing glossary says **75%** *and* prints a formula (`P = Base + (1−SLO/100)×0.4`) that exists nowhere in the code. SIMULATION_CONTEXT says 50%. Students plan around the glossary.
**Fix:** align glossary and context doc to the code (or implement the formula if that's the design intent — it's arguably the better model, SLO-proportional); add the R2-style doc-matches-generator test for the glossary numbers.

### DEEP-8 · The money does not reconcile — a documented, ratcheted gap of up to $656M/run · MEDIUM (accounting integrity)
`test_treasury_waterfall.py` is admirably honest about it: the six-term `RoundLedger` cannot explain treasury movement flowing through carbon fees, green-fund transfers, fines, black swans, board resolutions, NPC penalties — and now pillar costs/revenue. Recorded residual ceilings run to $656M on a game that starts with $50M. The test even leaves a solved-looking lead unclaimed: `SINGLE_BU_PHARMA/legacy` has a residual of exactly $2,000,000.00 — precisely that run's `total_capex`, i.e. one ledger term double-counted or never applied. A golden trace can never catch a leak that was always there; only this ledger can.
**Fix:** work the ratchet down as the test itself prescribes — claim the $2M lead first, then add ledger terms one at a time (carbon, green fund, fines, black swans, NPC, pillar flows). No behaviour changes; pure attribution.

### DEEP-9 · The supply-chain side track's M_R bonuses are written and never read · MEDIUM
The track's data bridge writes `sc_track_mr_bonus` (+0.05/+0.10) and `sc_track_mr_penalty` (−0.05) into the flag namespace — and neither M_R implementation, nor anything else, ever reads them. Students who earn the track's headline reward get nothing at terminal valuation. (Silver lining: this is why the side track cannot breach the M_R ceiling.)
**Fix:** consume them in the consolidated `calculate_mr` (DEEP-2) as a documented component, and extend the ceiling test accordingly — or remove the bonus framing from the track's scoring screen.

---

## What came back clean — do not re-investigate
Healthcare impact-key coverage (every key generic-applied or handler-owned, R1–R10); BRSR impact keys (all 7 referenced in brsr code); ESG dimension weights (coherent, deep-merged defaults); pending-projects lifecycle (pure function, copy-on-write, single application); midgame carbon vs terminal carbon tax (R10 skip guard verified); legacy R5/R8 bailout flags reachable in both paradigms; the R2 and full-course repairs (all invariants green at baseline).

## Suggested sequencing
1. **DEEP-1 + DEEP-2 + DEEP-3 as one branch** (`fix/mr-single-arbiter`): consolidate M_R into `calculate_mr` with pathway bonuses, clamps, and the EU AI Act recurring charge; golden rebaseline; per-pathway ceiling tests. Behavioural — cohort boundary.
2. **DEEP-4** (`fix/seeded-stochastics`): thread the cohort seed into impact_engine. Behaviour-preserving for unseeded cohorts, deterministic for seeded ones.
3. **DEEP-6 + DEEP-7**: config-driven green_claim key; doc/glossary alignment + generator test. Small.
4. **DEEP-8**: ledger completion, starting with the $2M lead. Non-behavioural, high trust value.
5. **DEEP-5 + DEEP-9**: flag triage with the design owner (the biggest single sweep, mostly rulings not code).
