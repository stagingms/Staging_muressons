# Muressons — Facilitator Evidence Pack

*Generated 2026-07-01 23:19 UTC · 60 runs per strategy profile · read-only engine harness.*

This pack is regenerated from the live engine. Bring it into the room to
answer the two questions every competitive cohort asks.

## 1. Is any strategy strictly dominant? — **No.**

No single strategy profile beats every other on M_R **and** treasury survival **and** reputation. The profiles trade off, which is the intended design: there is no button that wins everything.

| Profile | M_R P10 | M_R P50 | M_R P90 | Treasury survival | Instability-discount rate | Avg reputation |
|---|---|---|---|---|---|---|
| RANDOM | 1.25 | 1.25 | 1.25 | 98.3% | 0.0% | 31.46 |
| FINANCIAL | 0.65 | 0.65 | 0.65 | 1.7% | 100.0% | 25.07 |
| ESG_OPTIMISED | 1.53 | 1.53 | 1.53 | 100.0% | 0.0% | 30.32 |

## 2. Can M_R go out of bounds? — **No.**

Configured bounds: **[0.0, 2.05]**. Observed across all runs: **min 0.65, max 1.68**.

Every simulated outcome stayed inside the floor/ceiling clamp — no bonus or penalty stack can produce an economically meaningless valuation.

## 3. Vertical-swap parity (BU substitution)

_skipped_

## 4. Determinism note

Every team in a cohort shares one RNG seed (`rng_util.py`), so the stochastic events above roll identically for all teams. Distribution spread reflects **strategy**, not luck.
