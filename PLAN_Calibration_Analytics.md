# PLAN — Calibration Analytics on the Predict-Before-Commit Gate

Goal: measure whether players' mental models of the system improve, by scoring
their pre-commit predictions against actual engine outcomes — **without adding
any friction, screens, or engine coupling that would break the core round
fluency.**

## Where we start from (audited 2026-07-19)

| Piece | State today |
|---|---|
| Predict modal (`ExecutiveCockpit.js` ~3570) | Ships. Free-text only; saved to `sessionStorage` and never sent to the backend. Skip & Commit path exists. |
| `predictions` state → `PredictionComparison` | Dead wire: `setPredictions` is never called, so the results-stage comparison never renders. |
| `confidence_calibration_enabled` toggle | Exists (global + per-cohort + tiered presets) but nothing reads it in the player UI. |
| `pedagogical_engine.create/evaluate_prediction` | Unused; scoring is keyword-sentiment guessing ("increase" in text ⇒ optimistic). |
| Storage | No server-side prediction store at all. |

So this feature is 80% *plumbing what already half-exists*, 20% new analytics.

## Fluency principles (non-negotiable)

1. **No new screens, no new steps.** The one existing modal gains ~8 seconds of
   optional structured input. Skip & Commit remains one click and is never
   penalised into a nag.
2. **Scoring is post-tick and read-only w.r.t. the engine.** Calibration reads
   the deltas the tick already produced; it can never alter a simulation
   outcome. (Hard rule: the scorer writes only to the predictions log, never to
   engine ledgers.)
3. **Player-facing surfaces are results-stage / game-over only** (V-A + V-D:
   no new ambient panel, no KPI-belt change; the results chip rides inside the
   existing results overlay, the curve inside the existing final report).
4. **Everything gated by the two existing toggles**, per-cohort overridable,
   so a facilitator can run a zero-calibration cohort identical to today.

## Data model

One append-only log per session, stored under
`active_event_flags.predictions_log` (survives the memory-store flags
pack/unpack — the parity class we already hardened; add key to ENGINE-adjacent
carry NOT needed since flags carry whole).

```json
{
  "player_id": "…", "round": 4, "choice": "option_b",
  "treasury_band": "down_big|down|flat|up|up_big",   // bands: ±$1M, ±$5M edges
  "reputation_dir": "down|flat|up",                   // flat = |Δ| < 2
  "confidence": 0.7,                                   // 0.5–1.0 slider
  "note": "optional free text (kept for the debrief)",
  "submitted_at": "…",
  "score": {            // written post-tick by the scorer, null until then
    "treasury_hit": true, "reputation_hit": false,
    "hits": 1, "of": 2,
    "brier": 0.245      // mean over KPIs of (confidence − hit)²
  }
}
```

Structured bands replace sentiment parsing entirely; `evaluate_prediction`'s
heuristic is retired.

## Phases

### Phase 1 — Capture (backend + modal) 
- `POST /api/simulations/{sid}/predictions` — body = record above minus score.
  Guards: session exists, `_assert_player_owns_session` + `playerIdHeader()`
  from the client (the CSRD-repeat lesson: every player POST carries
  `X-Player-Id`). Idempotent per (player, round): re-submit overwrites.
- Modal: two compact segmented pickers (Treasury band, Reputation direction)
  above the existing textarea; confidence slider rendered **only when**
  `confidence_calibration_enabled`. Confirm & Commit posts the record
  fire-and-forget (a failed POST must never block the commit).
- `GET /api/simulations/{sid}/predictions?player_id=` for the results screen.

### Phase 2 — Scoring at tick 
- In the commit path, after the engine tick returns (same place agent_summary
  is finalised): compute actual Δtreasury / Δreputation for the round, score
  every unscored prediction for that round, write `score` back into the log.
- Pure function in `pedagogical_engine.py` (`score_prediction(pred, deltas)`)
  with unit tests: band edges, flat thresholds, Brier math, missing-KPI cases.
- Failure isolation: scorer wrapped so an exception can never fail a commit.

### Phase 3 — Player feedback (results + game over) 
- Rewire `PredictionComparison` to server data (kill sessionStorage): one
  compact chip in the existing results overlay — "You predicted ▼ Treasury /
  ▲ Reputation at 70% confidence → 1 of 2, Brier 0.25" with a plain-language
  line ("You were more confident than accurate this round").
- Game-over: a small SVG calibration curve (confidence buckets 50-60-70-80-90-100
  vs realised hit-rate; diagonal = perfect) + **Overconfidence Index**
  (mean confidence − mean hit-rate) added to the final report and the ESG
  Leadership Profile as a signal (weight configurable in the existing
  `esg_profile_weights` rubric, default small).
- Copy tone: descriptive, never scolding; a well-calibrated *pessimist* scores
  as well as a well-calibrated optimist.

### Phase 4 — Facilitator analytics 
- New card in the analytics registry (`FACILITATOR_ANALYTICS` key
  `calibration_analytics`, so the existing admin visibility-profile system
  gates it for free): cohort scatter (player × mean confidence vs hit-rate),
  round trend line ("does the cohort calibrate by R6?"), and the three most
  over/under-confident teams.
- One teleprompter line per round for live teaching: "3 teams predicted ▲
  treasury with ≥80% confidence and missed — name the planning fallacy."

### Phase 5 — Verification 
- Headless E2E: two players, rounds 1–4, mixed skip/submit, assert scores
  appear post-commit, survive a snapshot restart, and never alter engine
  KPIs vs a control run with identical decisions and no predictions
  (byte-compare global state minus the predictions log).
- Guard checks: header-less POST 403s on owned sessions; other-player read
  blocked; facilitator card obeys visibility profiles.

## Explicit non-goals
- No LLM scoring (deterministic bands only — auditable and free).
- No mid-round prompts, streaks, badges, or leaderboards for calibration
  (comparison pressure would corrupt honest confidence reporting).
- No blocking validation on the modal: skip stays first-class.

## Risk table

| Risk | Mitigation |
|---|---|
| Modal friction creeps up | Hard budget: 2 pickers + 1 slider, all optional; measure via existing time_to_decision. |
| Scorer breaks a commit | try/except isolation + Phase 5 control-run diff. |
| Memory-store loses the log | Lives in flags (packed/unpacked by parity layer); restart-survival test in Phase 5. |
| Players game confidence (always 50%) | Brier already optimal only for honest reports; say so in the chip copy once. |
