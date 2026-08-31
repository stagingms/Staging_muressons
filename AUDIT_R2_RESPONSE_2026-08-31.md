# Round 2 (Double Materiality) — Audit Response · 2026-08-31

Branch: `fix/r2-materiality-audit` (12 commits, each independently revertible).
Ships at a cohort boundary — nothing here is a hotfix. Full backend suite:
2087 passed. Frontend jest: 1099 passed. `tests/test_materiality_idempotency.py`
passes with its pins updated to the new fund semantics.

## 1 · Reproductions (§6)

All four reproduced exactly as stated before any change was made:

| § | Finding | Reproduced | After the fix |
|---|---|---|---|
| 6.1 | `r2_governance_choice`: 2 reads, 0 writes | ✅ | Written by `_post_r2_materiality`; the two router reads are gone (their logic moved to the handler) |
| 6.2 | Either write path alone grants the premium (True/True/False, first case dual-flagged) | ✅ | Single writer + dual-form guard; all nine accuracy×option combos asserted through `_collect_all_flags` |
| 6.3 | 3 of 8 DEFAULT_CONFIG issues disagree; numeric rule yields only Q1/Q4 | ✅ | 0 disagreements; distribution q1×5, q2×2, q3×1 |
| 6.4 | Group base $75.5M; R2A −2.5M/BU = −$12.5M (16.6%) | ✅ | R2A revenue_delta = 0; only R10C (Divest, 13.2%) remains above the band, allow-listed pending §5.3 |

Note on 6.2: the snippet hand-builds contradictory flag states, so it still
prints True/True/False if run verbatim — it tests the collector, not the
writers. The repaired system can no longer *produce* those states; the tiering
tests assert that on real end-to-end state.

## 2 · Open decisions (§5) — what was implemented

**§5.1 Budget semantics → option (a), restricted fund.** The released amount
(`$15M × Q1 recall`) becomes `materiality_restricted_fund` — no treasury debit
at all (option (a) is a *restricted grant*; the old debit was the inversion).
The consumer follows the engine's existing Advanced-Climate green-fund
pattern: the fund pays ESG CapEx ahead of the overrun/loan/interest machinery,
in R2 and every later round until exhausted. Unspent balance stays restricted;
capital for missed issues is never released. The Option C clawback moved to
`_post_r2_materiality` (the only place the choice exists): 40% of the released
amount, taken from the fund, any shortfall charged to treasury — so it always
reduces the team's position, asserted by direction in a test.
`q2_disclosure_budget_unlocked` is credited into the same fund (its consumer),
pro-rata against the *active* dictionary's disclosure-carrying Q2 issues; the
old fixed CSRD denominator made full unlock impossible on other dictionaries,
and `DEFAULT_CONFIG` gained `disclosure_required` on its two Q2 issues so the
budget is unlockable on the default path at all.

**§5.2 R3 partial tier → the symmetric half-discount.** `materiality_partial`
earns a −$250K Green Bond discount (aligned −$500K, ignored +$1M unchanged),
as its own explicit branch with its own event message — not a fall-through.

**§5.3 R10 Divest → left unchanged.** −$10M of group revenue is plausibly the
point of a divestment. It carries a comment in `round_configs.py` and an
allow-list entry (with reason) in the per-unit sanity test. Needs a
design-owner ruling; nothing was changed silently.

## 3 · Round 2 economics, before → after

Per-round money effects for a 5-BU group at Q1 recall = accuracy band
(option impact costs beyond these are unchanged). "Fund" is restricted capital
spendable as ESG CapEx.

| Option | Accuracy | BEFORE: treasury / revenue | BEFORE: flags seen → M_R | AFTER: treasury / fund | AFTER: flag → M_R |
|---|---|---|---|---|---|
| A | <80% | −2.5M − 15M×recall / −12.5M permanent | aligned (from flags_set) + ignored → **+0.10** | −2.5M / +15M×recall | ignored → 0 |
| A | =80% | −2.5M − 12M / −12.5M permanent | aligned (both writers) → +0.10 | −2.5M / +12M | aligned → +0.10 |
| A | >80% | −2.5M − 15M / −12.5M permanent | aligned → +0.10 | −2.5M / +15M (+≤1M Q2) | aligned → +0.10 |
| B | <80% | −15M×recall / 0 | ignored → 0 | 0 / +15M×recall | ignored → 0 |
| B | =80% | −12M / 0 | aligned (accuracy path) → +0.10 | 0 / +12M | **partial → +0.05** |
| B | >80% | −15M / 0 | aligned → +0.10 | 0 / +15M (+≤1M Q2) | partial → +0.05 |
| C | <80% | −15M×recall / +2M | ignored → 0; **no clawback ever fired** | 0 / +15M×recall − 40% clawback | ignored → 0; clawback bites |
| C | =80% | −12M / +2M | aligned + ignored → **+0.10** | 0 / +12M − 4.8M clawback | ignored → 0 |
| C | >80% | −15M / +2M | aligned + ignored → **+0.10** | 0 / +15M − 6M clawback | ignored → 0 |

Bold = the defects: before, Option A at any accuracy and *Option C at ≥80%*
both collected the premium; Option A really cost ~$15M+ (treasury + permanent
revenue + budget debit) against Option B's free identical premium; the
dominant exploit (Option A, one issue in Q1, save $13M, keep the premium) is
gone — accuracy now buys fund capital, and the premium needs accuracy *and*
governance. R3 Green Bond: aligned −$500K, partial −$250K, ignored +$1M.
The M_R ceilings are unchanged and pinned by test: **1.93** without JT
scaling, **2.02** with (the audit's "~2.03" computes to 2.02 exactly:
0.18 × 1.5 cap adds 0.09).

## 4 · The commits

1. `29dbad4` F-1 — `_post_r2_materiality` registered at `_POST_TICK_MAP[2]`; single arbiter (tier, clawback, assurance, debrief)
2. `2273e02` F-2 — one flag owner; pillar options renamed to distinct markers; `FLAG_OVERRIDES[2]` reverse-map only; dual-form guard `_find_dual_form_flags`
3. `e236b56` §4.1 — `materiality_partial` (+0.05) wired through M_R (both implementations), R3 pricing, admin panels, Consequence DNA (backend + frontend), ESG weights (backend + frontend mirror), teleprompter
4. `5654ba6` F-6 — `correct_quadrant_v2` in `round2_csrd.py`: dual-axis only with all four fields, else string labels; also fixes panel recommendations defaulting every issue to q4 on dictionaries without `correct_quadrant`
5. `f5ffd0e` F-6 follow-up — `q1_target_issue_ids` and admin Q1 counts through the same classifier
6. `282dcb6` F-3 — restricted fund + CapEx-offset consumer + clawback re-expression + Q2 disclosure consumer; idempotency pins updated
7. `450a28a` F-7 — R2A `revenue_delta: 0`, treasury −2.5M kept; R10C annotated, not changed
8. `6b8ea91` F-5 — `living_wage`, `plastic_packaging`, `philanthropy` flagged `is_ambiguous`; adjacency half-credit path live and tested
9. `5ad97df` — 38-test regression suite (`tests/test_r2_materiality_audit.py`)
10. `05b9950` F-4 + docs — SIMULATION_CONTEXT.md R2 rewritten; mechanics tables generated by `scripts/generate_r2_mechanics_table.py` from config + test fixtures, staleness enforced by a test; phantom 90%/$2M special_rules keys replaced by real, engine-read values
11. `d1ab585` — financial golden trace rebaselined (diff is exactly the F-7/F-3 repair)
12. `f418423` — beyond the list: `_collect_all_flags` no longer recurses into `_`-prefixed state bags

## 5 · Found beyond the list

Fixed: **(a)** `compute_panel_recommendations` defaulted `correct_quadrant` to 4
when absent — on `DEFAULT_CONFIG` every commissioned panel group, experts
included, recommended q4 for every issue ($750K for wrong advice). Now falls
back to the single classifier. **(b)** `_collect_all_flags` recursed into the
`_materiality_idempotency` bundle, surfacing debrief booleans
(`governance_board`, `q1_recall`, …) as active flags despite the bundle's
comment promising otherwise — same namespace-pollution class as F-2.

Fixed in a follow-up commit after review sign-off: **(c)** healthcare R9
"Halt Automation" carried `revenue_delta: -2_500_000` per unit — the F-7
failure mode outside the sweep's reach (−$10M / 17.4% of the $57.5M
healthcare group, −31% for telehealth, where every other healthcare option
sits at 3.5–5.6%). Rescaled to −625K/unit = −$2.5M group (4.3%), and the
per-unit sanity sweep now covers `HEALTHCARE_ROUND_CONFIGS` against the
healthcare seed's own group base, with the two pre-existing revenue-EXPANSION
outliers (R1A bed expansion +13.9%, R2A ICU expansion +10.4%) allow-listed
with reasons pending design-owner review.

Reported, not changed:
- **Convention inconsistency**: `opex_penalty` is group-scaled (divided across
  BUs) while `revenue_delta` is per-unit — this asymmetry is exactly how F-7
  happened. Worth a schema-level rename (`revenue_delta_per_bu`) some day.
- **`db/materiality_config_healthcare.json` is empty** (0 issues); healthcare
  scoring rides on `BU_DEFAULT_CONFIGS` instead. Probably intentional, worth
  confirming.
- **`DEFAULT_CONFIG` has no Q4 issue** (5×q1, 2×q2, 1×q3): the matrix has no
  true low/low distractor, so Q4 is only reachable as a wrong answer.
- **Industry JSON libraries** carry no `is_ambiguous` and no
  `disclosure_required`, so on those dictionaries `ambiguous_handled` remains
  unearnable and the Q2 disclosure budget stays locked. Content curation per
  industry — needs the design owner, not a units fix. Several also lack q4
  (and agriculture lacks q3) under the string rule; the new coverage test
  asserts no dictionary collapses to the Q1/Q4 diagonal (the F-6 signature)
  rather than demanding all-four content everywhere.
- **`_apply_common_impacts` other loops** (§10 request): `carbon_intensity_delta`
  and `governance_risk_delta` apply the same delta to each BU, but both are
  intensities/scores (0–100), not money — dimensionally sound, no F-7
  analogue. `reputation` applies once to the group. Healthcare's
  `elective_surgery_cancel` uses explicit per-BU dollar amounts — fine.

## 6 · Where I disagree with (or qualify) the audit

- **Max M_R with JT scaling is 2.02, not ~2.03** (0.18 × 1.5 − 0.18 = +0.09 on
  1.93). Pinned at 2.02 in `test_mr_ceilings_unchanged`. If teaching material
  says 2.03, it's rounding the same number.
- **F-4 is drift in both directions**: the "90% / $2M" figures did exist — as
  dead keys in `round_configs`/`healthcare_configs` `special_rules` that
  nothing consumed. Rather than only rewriting the doc, those keys now hold
  the real values (80% / 1000 points) and the router and post-tick handler
  read them, so the three surfaces (config, code, doc) can't diverge silently
  again.
- Everything else reproduced and was repaired as specified; nothing on the
  list turned out to be deliberate design.

## 7 · Notes for reviewers

- Tests that commit a *specific* option must translate it through the
  session's `shuffle_seed` (`commit-turn` deshuffles); the new suite has a
  helper. At least one historical test's option choice was effectively random.
- `ESGLeadershipProfile.js` shows a whole-file diff in commit 3: the blob
  predates `.gitattributes` `text=auto` and normalises on any touch.
- Postgres parity (`PG_PARITY=1`) was not run here (no live Postgres in this
  environment); the fund key rides the same generic flags-packing path as the
  existing materiality keys in both backends.
