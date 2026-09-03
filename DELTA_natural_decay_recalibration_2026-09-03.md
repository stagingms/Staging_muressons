# Delta — natural-decay tier recalibration (item 4)

**Status: WRITTEN BEFORE ANY REBASELINE, per constraint 2.3. The golden traces and
`BALANCE_REPORT_BASELINE.md` have NOT been regenerated. Two golden-trace tests are
failing on this branch on purpose, and stay failing until this delta is signed off.**

Ruling: recalibrate the tiers to the range players actually occupy (2026-09-03).

---

## 1. What changed

`backend/config.py` — four new `engine_parameters.slo_ramp` keys, each with a default
and a bound; present in both `simulation_config.json` copies and in the Excel importer.

| Constant | Before | After |
|---|---|---|
| no-decay band | `0.15` (bare literal in engine.py) | `NATURAL_DECAY_NO_DECAY_RATIO` = **0.10** |
| mild-growth band | `NATURAL_DECAY_MID_RATIO` = 0.20 | **0.25** |
| full-growth band | `0.30` (bare literal in engine.py) | `NATURAL_DECAY_GROWTH_RATIO` = **0.50** |
| "counts as invested" | `capex_allocated > 0` | `capex_allocated >= NATURAL_DECAY_MIN_ABS_CAPEX` = **$500,000** |

Bounds: the tiers must satisfy `0 < no_decay < mid < growth <= 1`, and
`0 <= min_abs_capex <= growth_abs_capex`. A configuration breaking either falls back to
the whole default set — never a half-applied mixture — with a `[CONFIG] WARNING`.

## 2. Why these numbers, from the 241 stored real decisions

`investment_ratio` reconstructed with the router's own formula
(`capex_allocated / max(treasury × 0.20, 5M)`).

**The old bands were degenerate.**

| band | real decisions caught |
|---|---|
| `0.15 <= ratio < 0.20` (no-decay tier) | **0** |
| `0.20 <= ratio < 0.30` (mild tier) | 9 — 3.7% |
| `ratio >= 0.30` (full growth) | 63 — **87% of every substantive allocation** |

Two adjacent tiers were indistinguishable, and the top tier was near-automatic for
anyone who spent real money. Substantive allocations run 0.20 → 1.00, median 0.50, so
the bands move onto that distribution. Resulting populations: decay 70.1%, no-decay
2.1%, mild 12.4%, growth 15.4% — every tier distinct and non-trivial.

**The decay tier was unreachable, and no band value could have fixed it.**
The call site read `invested = ratio >= 0.15 or capex_allocated > 0`, while `router.py`
refuses any commit giving a BU under $1 (VULN-009). So `capex_allocated > 0` held for
every decision ever committed, `invested` was always True, and the full-decay branch was
unreachable across the entire 0.0–1.0 ratio range. Verified by sweeping the whole range
with `invested=True`: no ratio reaches decay. Hence the predicate change.

**$500,000 comes from a gap in the data, not from taste.** The 241 stored decisions are
bimodal: **169 at exactly $1, then nothing at all until $1,000,000**, then a continuous
spread to $9,300,000. Any floor strictly inside ($1, $1,000,000) reclassifies exactly the
token allocations and cannot misclassify a single real one. $500,000 sits mid-gap.

## 3. What it moves — measured, not estimated

### 3.1 Financial golden trace — small and non-compounding

A single R1 effect of **−$346,441.84** on corporate treasury, carried forward as a
**constant** offset through R10. Nothing compounds. No other numeric field moves except
cost of capital:

| round | cost_of_capital before | after |
|---|---|---|
| R6 | 0.0500 | 0.0519 |
| R7 | 0.0500 | 0.0519 |
| R8 | 0.0502 | 0.0519 |
| R9 | 0.0582 | 0.0585 |

EBITDA, emissions, synergy, M_R, terminal value, all BU fields: **unchanged**.

### 3.2 Stakeholder golden trace — large and compounding

This is the significant one. The trace's scenario sits at investment_ratio ≈ **0.312** —
it cleared the old 0.30 growth bar and now falls to the mild tier, so SLO grows at
+1.00/round instead of +3.12/round.

| round | SLO before | after | delta |
|---|---|---|---|
| R1 | 58.12 | 56.00 | −2.12 |
| R5 | 70.62 | 60.00 | −10.62 |
| R10 | 64.25 | 43.00 | **−21.25** |

`community_leader` NPC satisfaction falls 53.25 → 52.40 at R1 and 54.70 → 46.20 at R10,
and its escalation level moves **`watchful` → `protest` from R7 onward**. That is a
visible, in-class stakeholder consequence, not a number on a report.

### 3.3 Balance report — three of six reference strategies flip to insolvent

| strategy | TV before | TV after | bankruptcy before | after |
|---|---|---|---|---|
| pure_A | $0.0M | $0.0M | R7 | R7 |
| **pure_B** | $148.1M | $148.4M | — (solvent) | **R10** |
| pure_C | $0.0M | $0.0M | R7 | R7 |
| aggressive_green | $891.4M | $891.4M | — | — |
| **extractive** | $35.2M | **$0.0M** | R7 | **R6** |
| **balanced** | $415.3M | $409.2M | — (solvent) | **R9** |

CapEx ladder: 5% $412.5M → **$185.9M** (final treasury $110.0M → **$0.1M**);
10% $166.4M → $68.3M. `wellbeing_bonus` attainment 82% → 73%. Every lever-sensitivity
row moves. "No dead levers" still holds.

## 4. The judgement call this delta exists to surface

The recalibration does what it was asked to do: all four tiers are now reachable and
distinct, and full growth is a choice rather than a default. **The cost is a substantial
difficulty increase.** A team at ratio 0.31 — previously earning full licence growth —
now earns a third of it, ends 21 SLO points lower, and triggers a stakeholder protest.
Three of six reference strategies stop being survivable.

For a launch of thirty simultaneous cohorts, that is a live pedagogical change: teams
that would have finished solvent will now go bankrupt, and facilitator materials quoting
survivability or SLO trajectories become wrong.

**Options if that is more than intended:** raise `min_abs_capex` toward $1,000,000 (still
inside the empty gap, same reclassification), or set `growth_ratio` to 0.40 rather than
0.50 so ratios in the low 0.30s keep full growth. Both are one config value and neither
needs a code change — that is the point of moving the literals into config.

## 5. Not done, pending sign-off

* `test_financial_golden_trace.py::test_golden_trace_matches` — **failing, not rebaselined**
* `test_stakeholder_golden_trace.py::test_golden_trace_matches` — **failing, not rebaselined**
* `BALANCE_REPORT_BASELINE.md` — **not regenerated**

Nothing was skipped, xfailed or loosened to hide these. `test_stakeholder_recs.py::
test_natural_decay_has_a_mild_middle_growth_tier` was **retargeted** (it probed ratio 0.22,
which encoded the old 0.20 band; it now probes the midpoint of the new mild tier, with the
assertion unchanged in strength), and a new test pins that all four tiers are reachable
and distinct — the regression that let the decay tier die unnoticed.

On sign-off: rebaseline with `MURESSONS_REBASELINE_GOLDEN=1` for both traces and
`python3 scripts/balance_report.py --write`, committing the JSON and markdown diffs in the
same commit as this delta.
