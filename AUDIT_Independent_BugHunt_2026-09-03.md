# Independent bug hunt — 2026-09-03

Unprompted audit, after the launch-readiness work order. Read-only: **no behaviour was
changed and nothing here is fixed.** Every finding below was reproduced by execution on
this working tree, not inferred from reading. Where I could not reproduce a claim myself I
say so explicitly.

Method: five parallel deep code reads (M_R input pipeline, process-global state under
concurrency, stochastic seeding, transient/treasury conservation, flag plumbing), then
independent verification of every candidate. Function ownership resolved by AST. Values
obtained by executing the real functions. Two candidates were **discarded** because my
first harness was not deterministic and the magnitudes did not survive a matched A/B —
see §Discarded.

---

## B-1 · CRITICAL — an HTTP page load reseeds the RNG that gameplay draws from

> **FIXED 2026-09-03, commit `fc1dff0`.** Both sites take a local `Random` from the new
> `rng_util.stable_rng`; a tripwire in `test_seeded_stochastics.py` resolves every
> `<alias>.seed(...)` by AST and blocks a recurrence. It found three further offline sites
> on its first run, allow-listed with reasons plus a guard that fires if production ever
> imports one.

**`backend/router.py:5255-5257`** (`get_peer_leaderboard`) and **`:5445-5447`**
(`get_peer_trend_history`):

```python
import random as _rng          # binds the MODULE, not a Random instance
seed = hash(session_id) & 0xFFFFFFFF
_rng.seed(seed + player_round) # reseeds the PROCESS-GLOBAL Mersenne Twister
```

Executed:

```
org_politics         random is the module: True
supply_chain_network random is the module: True
engine               random is the module: True

cohort A's next three draws, no foreign page view : [0.45238,  0.559772, 0.924211]
cohort A's next three draws, after ANOTHER cohort
        opened the peer leaderboard               : [0.787288, 0.09004,  0.106485]
cohort A's draws changed                          : True
```

`org_politics.evaluate_csuite_support` draws with `random.random() < final_prob`; the same
global stream feeds `supply_chain_network` and `engine`'s unseeded fallbacks.

**Consequence at thirty cohorts in one process:** a student in cohort B opening the peer
leaderboard changes the C-suite vote and supplier-disruption rolls in cohort A. It is not
reproducible either — `hash()` is PYTHONHASHSEED-randomised, so the comment's claim
("consistent across refreshes") is false across any restart:

```
PYTHONHASHSEED=0 -> 2685746558     PYTHONHASHSEED=1 -> 3074045476     PYTHONHASHSEED=2 -> 312725925
```

The same `hash()` defect was fixed in `dry_run._stable_strategy_offset` and these two sites
were missed. `rng_util.event_seed` is correct (SHA-256, process-stable — I verified it
under three hash seeds), so the per-cohort machinery is sound; these two endpoints bypass it.

**Recommendation.** Replace both with a local instance — `_r = random.Random(...)` — seeded
from `rng_util.event_seed(...)` or a SHA-256 of the session id, and use `_r.` for the AI
benchmark draws. Two lines each, no gameplay change, and it removes the only path by which
one class can perturb another. **Do this before launch.** Then add a tripwire asserting no
module-level `random.seed(` exists outside tests.

---

## B-2 · HIGH — transient OPEX surcharges leak permanently (F-04 reopened)

> **FIXED 2026-09-03, commit `5cc0c2e`** — new `TickContext.rescale_bu_transients`, wired at
> synergy and technical debt. Leak −$39,391.65 → −$0.01 (2dp rounding). NOT wired at
> supplier defection: a multiplier that records its own full delta is already exact, and
> doing so cost $50,350 of footprint until an existing test caught it. **Moves all 15
> treasury fingerprints — held for sign-off, see `DELTA_combined_rebaseline_2026-09-03.md`.**

The engine's own invariant (`TickContext.scale_transients`, `engine.py:2505`) is that a
purely transient charge leaves **zero** permanent footprint. Reversal is additive
(`engine.py:4681`: `_b[fld] = round(_b[fld] - _delta, 2)`), which is exact only if every
step in between is additive or calls `scale_transients`. `scale_transients("opex_base")` is
called **once**, at `engine.py:2725`. `calc_synergy_opex` then multiplies `opex_base`
permanently at **`engine.py:2789`** (`_run_financial_layer`, AST-resolved) and does not
scale the outstanding deltas.

Matched A/B — same seed, same pinned `stochastic_seed`, harness determinism asserted first;
the only difference is a purely transient $1,000,000/BU surcharge applied and reversed:

```
harness determinism check: PASSED

as shipped                                   TOTAL   -39,391.65
     pharma:-9,847.92  electronics:-9,847.91  consumer_goods:-9,847.91  software:-9,847.91
with calc_synergy_opex neutralised           TOTAL        +0.00
+ tech-debt neutralised                      TOTAL        +0.00
+ supplier-defection multiplier neutralised  TOTAL        +0.00

leak as a fraction of the transient charged: -0.9848%
```

Neutralising that one call site takes the footprint to **exactly zero**, which isolates the
cause completely. The leak is uniform across BUs and **negative** — `opex_base` is
permanently *reduced*, so costs are understated and treasury/EBITDA overstated. Money is
created, every round, on every transient OPEX surcharge.

Two further permanent multipliers sit after the same single scale call and will leak the
same way whenever they fire (they did not in this scenario, so they are latent, not clean):
`calc_technical_debt` ×1.04 at **`engine.py:3070`** (needs a zero-investment streak) and
`SUPPLIER_DEFECTION_OPEX_MULT` ×1.10 at **`engine.py:4289`**.

**Why no test caught it.** `test_launch_audit_2026_09_01.py::TestF04FlowPenaltiesAreTransient`
is the exact invariant test — and it runs at `investment_ratio=0.3`, above
`IMPLEMENTATION_LAG_INV_THRESHOLD` (0.10), so the synergy branch is skipped. Its own comment
says so.

**Recommendation.** Call `ctx.scale_transients("opex_base", f)` alongside each permanent
multiplicative step, where `f` is the factor actually applied — or, better, route every
permanent multiplier through one helper that cannot forget. Then re-run the F-04 invariant
test at a ratio **below** the lag threshold; it currently cannot fail. This moves the
golden traces and the balance report, so it needs a written delta like the item-4 one.

---

## B-3 · HIGH — `planet_expendable` is charged twice, and it flips the archetype

> **FIXED 2026-09-03, commit `fe7cf1e`.** Swing 0.40 → 0.20 as documented. A parametrized
> test now sweeps all four pathway calculators × nine canon-owned flags; only the
> planet_expendable cell was failing, confirming no other pair is double-billed. Moves no
> baseline.

`terminal_valuation.calculate_mr:238` applies `-0.20`. On the `climate_black_swan` ending,
`round_logic._post_r10_grand_finale:2610` also feeds
`ending_pathways.calc_climate_black_swan_mr` back in as `pathway_bonuses["pathway_mr_delta"]`,
and that function applies **another** `-0.20` for the same flag (`ending_pathways.py:588`).
Both source comments document a single `-0.20`.

Executed:

```
flags={'planet_expendable'}   calculate_mr's own penalty  : -0.2
                              pathway_mr_delta            : -0.2
                              => M_R 0.85
flags={}                      => M_R 1.25
swing for one flag: 0.40  (documented: 0.20)
```

`0.80` is exactly the `fragile_giant` / `stranded_relic` boundary in
`terminal_valuation._THRESHOLDS`, so the double charge can hand a team the wrong ending
archetype — the single most visible number a cohort takes away.

`planet_expendable` is the **only** flag double-counted this way; the other three pathway
calculators key off flags `calculate_mr` never reads, which I confirmed.

**Recommendation.** Decide which layer owns it — the canon or the pathway — and remove the
other. I'd keep it in `calculate_mr` (it is a general flag, not pathway-specific) and drop
lines 587-590 of `ending_pathways.py`. Add a test asserting the total swing for that flag is
0.20 on every ending pathway.

---

## B-4 · HIGH — a pinned, published M_R ceiling is unreachable (writer/reader key mismatch)

> **FIXED 2026-09-03, commit `b1d0dd4`.** All three published ceilings now reconcile
> exactly (1.930 / 2.020 / 1.980) and are pinned by a test. Also corrected the
> max-achievable comment (2.03 → 2.02) and two what-if reads of keys nothing writes.
> Moves no baseline.

Work order §2.8 pins **"1.930 without JT scaling, 2.020 with"** as values that must not
move. Executed:

```
hr_investment_rounds=0 : M_R 1.93  jt_scaling 1.0
hr_investment_rounds=5 : M_R 2.02  jt_scaling 1.5
```

So 2.020 requires `hr_investment_rounds > 0`. Five readers look for flags named
`hr_invested_r{N}`:

```
round_logic.py:2599   ceo_interview.py:213,367   pedagogical_engine.py:452
```

The only writer writes a **differently named** key — `round_logic.py:1597`,
`extra["hr_invested"] = hr_invested`, a plain boolean with no `_r{round}` suffix. A full
10-round game confirms it:

```
flag keys observed across 10 rounds : 351
keys matching 'hr_invest'           : ['hr_invested']      <- not 'hr_invested_r1' ...
jt_scaling_factor in the M_R breakdown: None
```

`jt_scaling` is therefore pinned at 1.0 forever, the Just Transition scaling mechanic is
dead, and **the published 2.020 ceiling cannot be reached by any team**. Related, unverified
by me but structurally identical: `admin_router.py:12450` reads
`hr_roi_investment_rounds` and `:12448` reads `workforce_readiness_score`, neither of which
has any writer.

**Recommendation.** This is a two-character-class bug with a published-material consequence.
Either write the per-round keys the readers expect (`extra[f"hr_invested_r{round_number}"] = True`)
or change the readers to count the key that is actually written. Whichever way, the textbook
number moves or the mechanic starts firing — so it needs a written delta and a decision
about which of 1.930 / 2.020 is the true ceiling. Then pin the max-M_R value in a test so a
published ceiling can never silently drift out of reach again.

---

## B-5 · MEDIUM-HIGH — the conservation law is not run on 3 of 5 paradigms, and one breaks

> **FIXED 2026-09-03, commit `76ab0ec`.** Four ledger terms added, `_CASES` now covers all
> five declared paradigms (15 cases). The six existing fingerprints are UNCHANGED, which
> proves the new terms are 0.00 there; nine new ones were each computed twice under
> different PYTHONHASHSEEDs before being pinned. Test-only.

`tests/test_treasury_waterfall.py:134` `_CASES` covers `legacy_abc` and `multi_toggles`
only. Running the test's **own** `_residual` over every paradigm the registry declares valid:

```
paradigm               worst round residual       10-round sum
advanced_climate                -253,141.94      -1,813,896.38   <- NOT COVERED
healthcare                            -0.00              -0.00   <- NOT COVERED
legacy_abc                            -0.00              -0.00   <- COVERED
multi_toggles                          0.00               0.00   <- COVERED
un_sdg                                -0.00              -0.00   <- NOT COVERED
```

The break is monotone-growing and confined to `advanced_climate`. The mechanism is the
**Internal Carbon Fee**: `_run_operational_layer` debits `ctx.new_treasury` by
`internal_carbon_fee_deducted` (`engine.py:3718` writes the event), the debit is gated on
`decision_paradigm == "advanced_climate"`, and there is **no matching term in `_residual`**
(grep for `internal_carbon_fee` in that test file returns nothing).

*Verification caveat, stated plainly:* the parallel agent measured the residual equal to the
fee to the cent, round by round. I confirmed the paradigm-scoped break, the treasury debit
and the missing ledger term, but my isolated tick used different decisions than the runner's
choice map (fee $113,165 vs residual $121,635), so I did **not** myself reproduce the
cent-level identity.

**Recommendation.** Add `internal_carbon_fee` as a `RoundLedger` term and to `_residual`,
and extend `_CASES` to all five paradigms. The law closing at $0.00 today is a statement
about two paradigms, not about the engine.

---

## B-6 · HIGH operationally — a cohort freeze is all-or-nothing across all thirty

> **FIXED 2026-09-03, commit `fc1dff0`** — the `system_frozen` half only. The guard now
> also reads `get_effective_settings(session_id)`, either freeze applies, and four
> end-to-end tests in `test_freeze_scoping.py` were verified red against the old guard.
> The four sibling reads below are NOT fixed: they need `session_id` threaded into
> `TickContext`, which has no such field.

`COHORT_OVERRIDABLE_KEYS` includes `system_frozen`, and `admin_router.py:1131-1139`
explicitly grants a `lead_facilitator` write access to it **for cohorts they own**. But the
only enforcement point, `router._commit_turn_impl:2423-2424`, reads the process-global
`_god_mode_settings`, not `get_effective_settings(session_id)`.

So a lead facilitator freezing their own cohort for a discussion **does not stop that
cohort's commits** (the PATCH returns 200 and the settings screen shows it applied), and a
super-admin freeze **stops all thirty classes at once**. Four other tick-path reads have the
same shape — `overrun_probability`, `overrun_severity` (`engine.py:2854-2856`),
`foreshadowing_enabled` (`round_logic.py:595`), `decision_regret_enabled`
(`router.py:3285`) — all of them keys the per-cohort layer claims to own. `TickContext` has
no `session_id` field at all, so the engine structurally cannot resolve per-cohort settings
today.

**Recommendation.** Route those five reads through `get_effective_settings(session_id)`, which
means threading the session id into `TickContext`. Before launch, at minimum fix
`system_frozen` — it is the one a facilitator will reach for mid-class, and today it either
does nothing or stops everyone.

---

## Also found, lower severity (verified structurally, not by full execution)

* **The BRSR ESG Alpha Dividend is silently dropped on the side-track route.**
  `_collect_all_flags` only emits boolean-`True` keys and members of `*flag*` lists;
  `brsr_net_positive_dividend` is the float `0.05`, so it is invisible to
  `_post_r10_grand_finale`. A team completing BRSR as a **side track** on a normal paradigm
  is promised +0.05 M_R by the dependency viewer and the consequence DNA, and the finale
  pays nothing. (The BRSR *paradigm* route is correct — it reads the value explicitly.)
* **Every projection surface disagrees with the award.** `consequence_dna_api`,
  `pedagogical_engine`, `what_if_terminal` and `engine.process_tick`'s valuation preview pass
  the raw flags dict; the finale passes `_collect_all_flags` output. Measured divergence on
  one realistic end state: award M_R 1.66 vs projection 1.43, and not in one direction — the
  projection grants a +0.20 resilience bonus the finale denies while missing synergy, truth
  premium and community champion. `engine.py`'s own comment claims it is "the same
  calculate_mr projection the finale uses". It is not.
* **The VUL-017 guard in `calculate_mr` does not exclude `bool`** (`isinstance(True, int)` is
  True in Python), so a bool in `pathway_bonuses` adds +1.00. No in-repo caller passes one —
  latent. `admin_router.what_if_replay` forwards an unvalidated request body into
  `what_if_terminal`, which is the one place a caller could.
* **`_engine_tunables`: 21 of 23 knobs are inert.** Only `overrun_probability` and
  `overrun_severity` are forwarded anywhere; the rest return `{"changed": ...}` and do
  nothing. `config_introspect`'s own inert-tunable check under-reports this (it exempts five
  keys because a similarly-named config constant exists, though nothing copies into them).
* **`regulatory_sandbox.py:873-875`** rolls a €30M fine from the bare global `random`, and
  **`supply_chain_network.py:484-491`**'s disruption branch is gated on
  `overall_visibility < 0.40` against a measured constant 0.482 — unreachable from the
  shipped state. Both sit behind default-off toggles or dead gates, which is exactly why
  `_EXPECTED_BARE_RANDOM_DRAWS = 0` can stay at zero: the tripwire cannot rise for a draw it
  never reaches.

---

## Discarded — did not survive verification

* **"The transient leak is ~1.4% / costs $2.8M over 10 rounds."** My first three harnesses
  were not deterministic — `process_tick` draws from the global RNG, so repeated calls
  advanced it differently and my A/B pairs were unmatched. Successive runs gave −$187,431,
  −$68,427 and −$3,252 for the same scenario. Only after pinning both the global seed and the
  cohort `stochastic_seed`, and asserting determinism first, did the number stabilise at
  **−$39,391.65 / −0.9848%**. The defect is real; the magnitudes I would have reported from
  the unmatched harness were not. Treat any leak figure not accompanied by a determinism
  check as unverified — including the parallel agent's $2.8M, which I did not reproduce.
* **"The `$3M` absolute CapEx escape is what lifts the 60% ladder rung's SLO."** Already
  corrected in the launch-readiness report; instrumentation showed every tier taking the
  `flat` branch 40/40 times and the greenwashing penalty being the real lever.

---

## Recommended order

| # | Finding | Before launch? | Moves pinned values? |
|---|---|---|---|
| B-1 | Global RNG reseed from a page load | **DONE** `fc1dff0` | No |
| B-6 | `system_frozen` (at minimum) read from the global | **DONE** `fc1dff0` | No |
| B-3 | `planet_expendable` charged twice | **DONE** `fe7cf1e` | No baseline moved |
| B-2 | Transient OPEX leak | **DONE** `5cc0c2e` | Fingerprints + balance — held |
| B-4 | JT scaling dead / 2.020 unreachable | **DONE** `b1d0dd4` | No baseline moved |
| B-5 | Conservation law coverage | **DONE** `76ab0ec` | No (test-only) |

B-1, B-6 and B-3 are all small, self-contained, and none of them moves a golden trace or a
published number — B-3 changes an outcome, but toward the documented one. B-2 and B-4 are
real behavioural changes that need the same delta-first treatment item 4 got.
