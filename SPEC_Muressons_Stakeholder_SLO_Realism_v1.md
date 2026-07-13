# SPEC — Stakeholder / SLO Realism & Engagement Upgrade (v1)

**Status:** Design spec, pre-implementation
**Scope:** The stakeholder ↔ Social-License-to-Operate (SLO) segment of the round loop
**Author intent:** Make the segment more life-like and engaging *without* easy work-arounds
and *without* breaking existing simulation logic, round order, or the drift tripwires.

---

## 0. Read this first — why this spec is written defensively

The stakeholder segment is **not** a greenfield. Three subsystems already touch SLO, and
they were built at different times with different memory models. The single biggest risk in
this work is **adding a fourth parallel system** that silently double-counts or contradicts the
other three. Every feature below is therefore framed as *extend / reconcile an existing engine*,
never *bolt on a new one*.

### 0.1 The existing stakeholder surface area

| Subsystem | File | Unit of state | Memory? | Writes back to… |
|---|---|---|---|---|
| Named NPCs (SI-2) | `backend/npc_stakeholders.py` | 4 named NPCs, `satisfaction` 0–100 | **No** — `calc_npc_satisfaction` recomputes from current metrics every round; the `trust` field is initialised to 50 and **never updated** (dead state) | `group_reputation`, treasury (regulator fine) via `process_npc_tick` |
| Reaction cascades (PHASE-1) | `backend/systemic_risk_engine.py::evaluate_npc_cascades` + `STAKEHOLDER_REACTION_GATES` | discrete gate crossings | Partial — `persistence_rounds`, `active_npc_cascades` | **SLO** (`social_license_delta`), treasury, reputation, burnout, OPEX — applied in `round_logic.py` post-tick |
| Portfolio sentiment | `backend/stakeholder_sentiment.py::update_stakeholder_sentiment` | stakeholder *list* with `attitude_score` 0–100 + salience quadrant | **Yes** — deltas accumulate on the prior `attitude_score` | Nothing mechanical today — narrative + `sentiment_history` only |
| Autonomous agent pool (SI-2+) | `backend/autonomous_agents.py` | ~50-agent pool | (separate) | its own diagnostics |

Plus the **systemic tipping engine** (`evaluate_tipping_points`) which caps SLO at 50 when the
social dimension "tips" — an irreversibility ceiling applied in `round_logic.py`.

**Key inconsistency to resolve (F1):** the same conceptual thing — "how a stakeholder feels about
us" — is modelled twice with opposite memory semantics. `npc_stakeholders` is memoryless;
`stakeholder_sentiment` has memory. Players cannot form a mental model of a stakeholder whose
mood resets every round. F1 makes the NPC layer the *memoryful* one and demotes the raw
satisfaction number to an input, mirroring how `attitude_score` already works.

### 0.2 Round order of operations (do not reorder)

The SLO value a stakeholder reacts to is produced earlier in the same tick. Order today:

1. **`engine.py::process_tick`** — pillar-decision SLO deltas → `apply_natural_decay` (investment-ratio
   gradated growth/decay) → contagion → strike probability → **final bounds-clamp of `social_license_score`**
   (engine.py ~line 3809) → `update_stakeholder_sentiment` (~3820).
2. **`engine.py::_assemble_global_state`** — builds `new_global` from an **explicit whitelist** of keys.
3. **`round_logic.py::post_tick`** — runs board → org-politics → supply-chain → **NPC tick →
   `evaluate_npc_cascades` (writes SLO deltas)** → autonomous agents → **tipping-point penalties
   (SLO ceiling)**.

**Implication for every SLO-writing feature:** SLO is *finalised for the round's economics* at the
end of step 1, but is still legally mutated in step 3 by cascades and tipping. New stakeholder→SLO
feedback (F2) must therefore live in **step 3, after the NPC tick, before tipping penalties**, and
must be **idempotent within the round** (never re-run on replays) so it composes with — rather than
fights — the existing cascade write-backs. See F2 §"double-count guard".

### 0.3 Conventions that must be honoured (from `CLAUDE.md` + observed code)

- **Toggle + defensive try/except.** Every engine in `post_tick` is wrapped
  `if _toggles.get("<name>_enabled", True): try: … except Exception as exc: print("[WARN] …")`.
  A stakeholder-engine failure must **never** block the tick. All new engines follow this exactly.
- **Seeded RNG (GAME-4).** Any randomness uses `rng_util.event_rng(active_event_flags, …)` /
  `event_seed(...)` so every team in a cohort faces the same roll. **No bare `random.*`** in new
  gameplay-affecting paths. (Note: the *legacy* `npc_stakeholders.determine_npc_action` currently
  uses bare `random` for cosmetic fine amounts — F4 replaces this with the seeded stream.)
- **State persistence is the raw `global_state` dict, not `GlobalStateOut`.** Engine sub-states
  (`npc_stakeholders`, `org_politics`, …) live as sub-dicts on `global_state` and survive because the
  DB stores the raw JSON; `GlobalStateOut` (models.py, tightened by AUDIT-026 to **reject arbitrary
  extras**) is only the API response shape. **Rule:** new persistent stakeholder state goes in a
  sub-dict on `global_state` (like `npc_stakeholders`); anything the *client* must read is surfaced
  through the per-round `extra`/diagnostics channel, **not** by loosening `GlobalStateOut`. If a
  scalar genuinely must round-trip through the typed response, add it as an explicit `Optional`
  field on `GlobalStateOut` (the AUDIT-026 pattern), never via `extra="allow"`.
- **Drift tripwires exist and will fail your build.** `shockwave-catalog.test.js`,
  `test_role_hierarchy_sync.py`, and the sidebar-tooltip audits pin mirrored constants. Any new
  catalog that is mirrored front/back (e.g. a stakeholder-action catalog for the UI) must ship with
  its own tripwire or extend an existing one, in the **same commit**.
- **Player-UI slotting (V-D).** Every new player-facing surface occupies **exactly one** slot
  (canvas / KPI belt / expand drawer / rail tab / ⋯ / projector / OverlayHost) and uses
  `tokens.css` — no raw hex for danger/success/caution. F5 and F6 name their slots explicitly.

---

## 1. F1 — Stakeholder memory (trust as a stock)

### 1.1 Realism rationale
Real stakeholders have history: trust is a reservoir that fills slowly and drains fast, and a
betrayal leaves a scar that caps how quickly goodwill can return. The current NPC layer resets
mood each round, so players optimise a gauge instead of managing a relationship. This is the
highest realism-per-line change and the foundation the other features read from.

### 1.2 Mechanic
Introduce a persistent per-NPC `trust` stock (0–100) that **integrates** the existing per-round
`satisfaction` signal with asymmetric gains/losses and a scar term. `satisfaction` stays exactly as
computed today (`calc_npc_satisfaction`) and becomes the *target/pressure*, not the state.

```
# per NPC, each round, AFTER satisfaction is computed
gap        = satisfaction - trust_prev              # how far mood is from stored trust
gain_rate  = TRUST_GAIN_RATE      # e.g. 0.25  (trust rises slowly)
loss_rate  = TRUST_LOSS_RATE      # e.g. 0.55  (trust falls ~2.2x faster)
rate       = gain_rate if gap >= 0 else loss_rate
trust_raw  = trust_prev + rate * gap

# betrayal scar: broken promise (F5) or deny_and_deflect / greenwash flag this round
if betrayal_event:
    trust_raw  -= SCAR_IMMEDIATE          # e.g. 12
    scar_until  = round + SCAR_DURATION   # e.g. 3 rounds
# while scarred, cap recovery ceiling
trust_ceiling = SCAR_CEILING if round <= scar_until else 100   # e.g. 60
trust = clamp(min(trust_raw, trust_ceiling), 0, 100)
```

`satisfaction` continues to drive cascades **but cascades gate on `trust` once F1 ships** (one-line
change in `evaluate_npc_cascades` caller: pass `trust`, not `satisfaction`, into the gate metric) so
the discrete reactions inherit memory automatically and stop flickering on/off round-to-round.

### 1.3 Where it plugs in
- `npc_stakeholders.py`: new `update_trust(npc_state, satisfaction, betrayal_event, round_number)`;
  call it inside `process_npc_tick` right after `calc_npc_satisfaction`. Populate the **already-existing
  but dead** `npc_state["trust"]` field — no schema change to the NPC state shape.
- Escalation (`determine_npc_action`) reads `trust` instead of raw `satisfaction` for tier selection;
  keep `satisfaction` in the returned dict for the debrief/facilitator view.
- Persistence: `trust` and `scar_until` are new keys inside the `npc_stakeholders` sub-dict, so no
  `GlobalStateOut` change is needed — **BUT** the sub-dict does not actually survive between rounds
  today. See §1.7: fixing that carry-forward is a hard prerequisite for this whole feature, because a
  trust *stock* is meaningless if the dict holding it is rebuilt every tick.

### 1.4 Reconciliation with `stakeholder_sentiment`
Do **not** run two memory models. Choose one of:
- **(Recommended) Bridge:** keep `attitude_score` (portfolio list) as the *broad* sentiment surface
  and derive each named NPC's `satisfaction` input partly from the matching sentiment cohort, so the
  two agree by construction. Named NPCs get the trust stock; the portfolio list stays as-is for the
  map/heat view.
- **(Alternative) Merge:** promote named NPCs to be first-class rows in the sentiment list. Larger
  refactor; defer unless the duplication proves confusing in playtests.
Pick the bridge for Phase 1; document the decision in the module header.

### 1.5 Config, RNG, failure modes
- New constants in `config.py` beside `STAKEHOLDER_FATIGUE_FACTOR` (config-Excel backed):
  `TRUST_GAIN_RATE`, `TRUST_LOSS_RATE`, `SCAR_IMMEDIATE`, `SCAR_DURATION`, `SCAR_CEILING`.
- No RNG (deterministic integrator) — good; keeps it reproducible.
- Failure mode: first round has no `trust_prev` → initialise `trust = satisfaction` on the genuine
  round 1 so the stock doesn't start at a misleading 50. Guard `scar_until` default 0. **Note:** this
  round-1 branch is only correct *after* §1.7 lands — today every round looks like round 1 (see below),
  so without the carry-forward fix `trust` would re-seed to `satisfaction` every tick and never
  integrate.

### 1.6 Tests
- Unit: monotone-gain vs fast-loss asymmetry; scar caps recovery for exactly `SCAR_DURATION`;
  round-1 initialisation.
- Regression: cascades that used to fire on transient satisfaction dips no longer flicker (golden
  round-trace test on a seeded cohort).
- **Carry-forward test (new, gates §1.7):** run ≥3 rounds and assert `trust`/`scar_until` from an
  earlier round are still present and evolving on the later round's `npc_stakeholders` sub-dict — i.e.
  the state is not silently re-initialised. This test must exist and pass *before* the trust
  integrator is trusted.

### 1.7 Prerequisite (Phase-0 finding): engine sub-state must actually carry forward

**This is a hard blocker for F1, discovered while building the Phase-0 golden oracle. Do it first.**

`engine.py::_assemble_global_state` builds the next-round `global_state` from an **explicit whitelist**
of keys. `npc_stakeholders` (and `board_governance`, `org_politics`, `supply_chain`, …) are **not** in
that whitelist, so they are dropped from the assembled state. `round_logic.py::run_new_engines` then
sees no `npc_stakeholders` key and calls `create_initial_npc_state()` — meaning **the entire NPC state
is re-initialised every round**. The NPC layer is therefore not merely memoryless in its satisfaction
*formula* (as §0.1 framed it); its state dict is thrown away each tick. Populating a `trust` stock is
pointless until this is fixed — it would reset to its round-1 seed on every commit.

Why it looks like it works today: in production the *router* persists the post-`run_new_engines`
`global_state` (which by then contains a freshly-initialised `npc_stakeholders`) and reloads it next
round, so cascades' short `persistence_rounds` windows mostly survive within a single tick's evaluation
— but across the `process_tick` boundary the sub-dict is still rebuilt. (Separately, the Phase-0 oracle
found the same whitelist drops `active_event_flags["stochastic_seed"]`; the router re-merges it via
`merged_flags`, which is why seeded RNG stays reproducible in prod but not in a bare harness.)

**The fix — pick ONE, in priority order; do not paper over it in `run_new_engines`:**

1. **(Recommended) Whitelist the engine sub-states in `_assemble_global_state`.** Add a small,
   named passthrough — e.g. copy a fixed `ENGINE_STATE_KEYS = ("npc_stakeholders", "board_governance",
   "org_politics", "supply_chain", "autonomous_agents", "systemic_tipping_state", …)` from
   `ctx.current_global` into the returned dict. This is explicit, greppable, and keeps
   `_assemble_global_state` as the single source of truth for what persists. Ship the key list as a
   module-level constant so it can't drift silently.
2. **(Alternative) Restore from `_prev_global_states`.** `_assemble_global_state` already preserves the
   last three `current_global` snapshots; `run_new_engines` could hydrate `npc_stakeholders` from the
   most recent one when absent. Rejected as the default: it hides the persistence contract in the
   consumer instead of the producer, and couples the NPC engine to an unrelated history buffer.

**Guardrails so this fix doesn't break the flow:**
- **Scope creep risk:** carrying `board_governance`/`org_politics`/etc. forward *changes their
  behaviour too* (they also currently reset each round). Carry forward **only `npc_stakeholders`** in
  the F1 commit unless a golden diff for the others is reviewed and intended; add the rest in separate,
  individually-reviewed commits. The Phase-0 golden oracle will flag any unintended change to the
  others.
- **`GlobalStateOut` stays untouched** — these are internal engine sub-dicts on the raw `global_state`,
  never surfaced through the typed response (per §0.3).
- **Idempotency / re-commit:** because the sub-dict now persists, the F2 `slo_feedback_applied_round`
  marker and any once-per-round guards become load-bearing across the boundary — verify they key off
  `round_number`, not mere presence.
- **Re-baseline the oracle deliberately:** turning on real NPC persistence *will* change the golden
  trace (trust/satisfaction now evolve instead of resetting). That diff is the *intended* signal of F1
  working; review it line-by-line and commit the new golden with the change (per §10).

---

## 2. F2 — Close the SLO loop (continuous action → SLO)

### 2.1 Realism rationale
Today a stakeholder *reaction* changes reputation/treasury and (only at discrete cascade gates) SLO.
Between gates, an angry-but-not-yet-cascading community has zero effect on its own social license, so
the "spiral" in the loop diagram is broken except at threshold jumps. Real mobilisation hardens
stances continuously.

### 2.2 Mechanic — a graduated feedback term, not another gate
Add a **small continuous** SLO pressure from each stakeholder's *current escalation tier*, applied to
the BUs that stakeholder is attached to (community_leader → water/agri BUs, regulator → all, etc.):

```
tier_pressure = {cooperative:+1.0, watchful:0.0, protest:-2.0, legal/hostile:-3.5}[tier]
slo_feedback  = tier_pressure * STAKEHOLDER_SLO_COUPLING   # coupling e.g. 1.0, tunable
bu.social_license_score = clamp(bu.social_license_score + slo_feedback)
```

This is intentionally **weaker per-round than a cascade** (which stays the discrete "big event").
Continuous feedback provides the *slope*; cascades provide the *cliffs*.

### 2.3 Double-count guard (the critical correctness point)
- Apply F2 in `round_logic.py` **post-tick, immediately after `process_npc_tick`, before
  `evaluate_npc_cascades`**, so cascade gates then evaluate on the freshly-pressured trust and there
  is one clear ordering.
- **Never** let F2 and a cascade both charge for the same escalation in the same round. Rule: if an
  NPC triggers a cascade this round, its continuous `slo_feedback` is **suppressed** that round (the
  cascade's `social_license_delta` supersedes). Implement as a per-round set of `cascaded_npc_ids`.
- Respect the **tipping SLO ceiling** applied later in `post_tick`: F2 writes raw deltas; the existing
  social-tipping cap (≤50) still runs afterwards and will clamp — do not duplicate that clamp.
- Idempotency: F2 must key off `round_number` and a `slo_feedback_applied_round` marker in
  `npc_stakeholders` state so a re-entrant/retried commit cannot apply it twice.

### 2.4 Where it plugs in
- New `apply_stakeholder_slo_feedback(npc_master_state, bu_states, round_number, cascaded_ids)` in
  `npc_stakeholders.py`; called from the existing NPC `try/except` block in `round_logic.py`.
- Surface the per-BU deltas into `extra["npc_slo_feedback"]` for the UI/debrief (so players see *why*
  SLO moved).

### 2.5 Config / tests
- `config.py`: `STAKEHOLDER_SLO_COUPLING`, `TIER_PRESSURE_MAP` (or inline constant table).
- Tests: sum of F2 + cascade on the same NPC in one round equals the cascade alone (no double count);
  F2 never pushes SLO above the tipping ceiling; idempotent on double-commit.

---

## 3. F3 — Coalitions & salience contagion

### 3.1 Realism rationale
Stakeholder risk is *correlated*, not independent (Mitchell-Agle-Wood: salience is dynamic and
relational). A community protest plus a critical journalist becomes a viral story that raises
*everyone's* urgency. The engine already hints at this: `STAKEHOLDER_REACTION_GATES` cascades carry
`cascading_triggers: ["journalist_hostile", …]` — but they're only referenced as narrative today.

### 3.2 Mechanic — activate the latent `cascading_triggers`
1. **Salience amplification.** When ≥2 NPCs are simultaneously at `protest`/`legal`/`hostile`, raise a
   shared `coalition_pressure` scalar (0–1) = f(count, combined salience power×urgency×legitimacy from
   each NPC's `salience` profile). This scales the **strike coefficient** and F2 tier pressure for the
   round (a coalition makes each action bite harder), and can nudge `activist_investor`/`regulator`
   satisfaction down (contagion).
2. **Trigger propagation.** Honour `cascading_triggers` mechanically: a fired cascade sets a one-round
   `+urgency`/`−satisfaction` nudge on the named target NPCs (with a hop cap of 1 to prevent runaway
   chains), evaluated **before** the next NPC's gate check within the same tick pass.

### 3.3 Guardrails
- **Hop cap = 1** and a global "max 1 coalition event/round" to keep the tick bounded and the drama
  legible; uncapped contagion produces death spirals players can't read (anti-engagement).
- Deterministic given seeded inputs — contagion is rule-based, no RNG.
- Fits the strike formula cleanly: `P_strike = base + (1−SLO/100)·W · (1 + coalition_pressure·k)`;
  `k` small (e.g. 0.5) and capped so P stays ≤ 1.0 (the formula already clamps).

### 3.4 Where it plugs in
- `systemic_risk_engine.py`: extend `evaluate_npc_cascades` to emit `coalition_pressure` and apply
  `cascading_triggers` nudges to the `npc_satisfaction`/trust map before returning.
- Strike coupling: thread `coalition_pressure` into the strike calc (engine exposes
  `calc_strike_probability`; add an optional multiplier arg defaulting to 1.0 → **backwards compatible**).
- `extra["stakeholder_coalition"]` for UI (this is the "oh no, they're teaming up" moment).

### 3.5 Tests
- Two NPCs hostile → coalition_pressure > 0 and strike prob strictly higher than either alone;
  hop-cap prevents 3rd-order propagation; P_strike still clamps at 1.0.

---

## 4. F4 — Uncertain thresholds + patience clocks

### 4.1 Realism rationale
Fixed 70/50/30 escalation tiers are gameable — players park one point above a line. Real tipping
points are uncertain and *time-dependent*: a stakeholder kept "watchful" long enough escalates even
if the metric is flat ("our patience is not infinite," which is already in Patil's `watchful`
dialogue — the mechanic should match the narrative).

### 4.2 Mechanic
- **Seeded threshold jitter.** Perturb each NPC's escalation thresholds by a small band
  (±`THRESHOLD_JITTER`, e.g. ±4) drawn **once per cohort per session** from `event_rng` so all teams
  share the same hidden lines (fair) but no team knows them exactly (tense). Store the drawn offsets
  in `npc_stakeholders` state at init.
- **Patience clock.** Track `rounds_at_tier`; if an NPC sits at `watchful` (or worse) for
  `PATIENCE_LIMIT` rounds, force one tier of escalation regardless of metric, then reset the clock.
  Recovering to `cooperative` resets patience generously (goodwill).

### 4.3 Guardrails / RNG
- **This replaces the only bare-`random` call in the stakeholder path** (`determine_npc_action`'s
  cosmetic `{fine}`), moving it onto the seeded stream — a net correctness improvement flagged under
  GAME-4, not a regression.
- Jitter drawn at **session init**, not per round, so thresholds don't shimmer mid-game.
- Keep bands small; large jitter feels arbitrary (anti-engagement). Facilitator view may reveal true
  thresholds for debrief.

### 4.4 Where it plugs in
- `npc_stakeholders.py`: jitter offsets in `create_initial_npc_state` (needs the session seed —
  pass it through, mirroring how engine.py sources `event_seed(active_event_flags, …)`);
  `rounds_at_tier` + patience logic in `determine_npc_action`.

### 4.5 Tests
- Same seed → identical thresholds across two runs; different seed → different; patience forces
  escalation on a flat-metric trace; cooperative resets patience.

---

## 5. F5 — Dialogic verb (engagement actions + promise ledger)

### 5.1 Realism rationale
Players currently manage stakeholders only through org-wide levers (investment ratio, pillar choice).
Real stakeholder management is dialogic: you make a *specific* promise to a *specific* group, and you
are held to it. This is the biggest *engagement* unlock and it gives F1's scar term its teeth.

### 5.2 Mechanic
A lightweight **per-round engagement action** targeting one NPC:
- **Options** (small catalog): *town hall* (small trust bump now, no promise), *public pledge*
  (bigger trust bump now **+ registers a promise** with a metric target and due round), *private
  commitment* (cheap, targeted, promise), *do nothing*.
- **Promise ledger** on `global_state.stakeholder_promises`: `{npc_id, metric, target, due_round,
  cost, state: open|kept|broken}`. At each tick, evaluate open promises whose `due_round` ≤ now:
  - metric met → `kept`: trust bonus + small SLO/reputation credit.
  - metric missed → `broken`: fires the **F1 betrayal scar** (hard trust hit + recovery ceiling) and a
    reputation ding. This is the risk that makes pledges a real decision, not free points.
- Cost: spends treasury and/or the round's attention budget so it trades against other decisions.

### 5.3 UI slot (V-D compliance — stated explicitly)
- The action lives in the **canvas stage** during the decision step (it *is* a current-stage
  decision), rendered as a compact choice on the stakeholder the player selects.
- The **promise ledger / relationship history** lives in an **expand drawer** or a **rail tab**
  (asynchronous context), **not** a new always-visible panel. Locked/undue promises render as a
  *locked summary naming the due round* (V-B/V-C precedent), never full prose behind a click-intercept.
- Uses `tokens.css` semantic colours (kept=success, broken=danger) — no raw hex.

### 5.4 Where it plugs in
- New `stakeholder_engagement.py` (state init + `resolve_promises(...)`), toggled + try/except in
  `post_tick` **after** F1 trust update (so kept/broken feeds trust the same round it matures).
- Decision intake: the engagement choice arrives with the round's decisions (extend the commit
  request payload; the router already deep-copies `decisions_raw` — thread one optional
  `engagement_action` field, defaulting `None` → **fully backwards compatible**, old clients unaffected).
- Persistence: `stakeholder_promises` is a sub-dict on `global_state` (raw-JSON persisted). If the
  cockpit must show a promise *count* via the typed response, add one `Optional[int]` field to
  `GlobalStateOut` (AUDIT-026 pattern) — otherwise surface via `extra`.
- LLM: `get_npc_llm_prompt` already exists — feed promise state in so dialogue references the pledge
  ("you promised us the water plant by round 6"). Deterministic template fallback stays.

### 5.5 Tests
- Kept promise → trust/SLO credit; broken → scar fires exactly once; ledger survives round-trip;
  `engagement_action=None` reproduces today's behaviour byte-for-byte (golden test).

---

## 6. F6 — Intent-forward UI (show demand & leverage, de-emphasise the raw score)

### 6.1 Realism rationale
A "satisfaction: 43" readout invites optimising the number instead of reading the person. Engagement
comes from *readable intent + leverage*: what this stakeholder wants next, and how much power they
have to hurt you if ignored.

### 6.2 Mechanic (mostly presentation — least engine risk)
For each named NPC, compute and surface:
- **Demand:** the top unmet `satisfaction_driver` in plain language ("wants the water-recycling
  pledge honoured").
- **Leverage:** salience label from `power × urgency × legitimacy` (already in each NPC `salience`
  profile) → e.g. "high legitimacy, low power — for now".
- **Trend arrow:** from F1 trust delta.
Keep the numeric score in the **facilitator/debrief** view only.

### 6.3 UI slot
- Stakeholder cards live in a **rail tab** (asynchronous context — "intel"), one open at a time, per
  V-D. The relationship timeline (promises, past actions) is the **expand drawer** deep-dive.
- Reuse the existing `get_sentiment_summary` / `get_salience_weighted_score` outputs where possible
  rather than computing new numbers client-side.

### 6.4 Tests / guardrails
- Any front/back mirrored copy (demand phrasings keyed to driver ids) that could drift gets a small
  tripwire or is generated from a single source of truth (backend emits the phrase).
- Sidebar/tooltip audit rule: if this adds an admin tab, the tooltip describes what it renders *today*.

---

## 7. Cross-cutting: the memory-model reconciliation (must not be skipped)

F1 and F5 both assume **one** authoritative "how does X feel about us" value per named stakeholder.
Before Phase 2 ships, decide and document (module header + this spec's changelog):
`trust` (memoryful, named NPCs) is authoritative for **escalation, cascades, strikes, promises**;
`attitude_score` (sentiment list) is authoritative for the **portfolio heat-map / salience-weighted
overview**; the two are bridged (F1 §1.4). Encode the bridge in one function so there is a single
place to reason about it. Skipping this produces two drifting truths — the exact failure this spec
exists to prevent.

---

## 8. Phased implementation plan

Each phase is independently shippable, toggle-guarded, and leaves the sim green. Order is chosen so
every phase depends only on earlier ones.

### Phase 0 — Instrumentation & guardrails (0.5–1 day, no gameplay change)
- Add a **golden round-trace test**: seed a cohort, run 10 rounds, snapshot SLO / reputation / NPC
  states per round. This is the regression oracle every later phase must not disturb (except where a
  phase intentionally changes numbers, in which case the golden is re-baselined deliberately).
- Add `stakeholder_engine` feature toggles to the `_toggles` map (default off for new behaviour,
  so phases can land dark and be enabled per-cohort).

### Phase 1 — Memory (F1) + reconciliation decision (§7)
- **Step 1 (prerequisite — do first): fix engine sub-state carry-forward (§1.7).** Whitelist
  `npc_stakeholders` in `_assemble_global_state` so its state survives the `process_tick` boundary,
  and land the carry-forward regression test (§1.6). Until this passes, `trust` cannot integrate. Carry
  forward **only `npc_stakeholders`** in this commit; leave the other engine sub-states for separate
  reviewed commits so their golden diffs stay isolated.
- Implement trust stock, populate the dead `trust` field, switch escalation + cascade gating to trust.
- Bridge to `stakeholder_sentiment` (F1 §1.4, recommended option).
- **Depends on:** Phase 0. **Ships behind:** `stakeholder_memory_enabled`.
- **Exit test:** carry-forward test green; asymmetry + scar unit tests; golden trace re-baselined and
  the diff reviewed to be *only* the expected trust/satisfaction-now-persisting fields.

### Phase 2 — Close the loop (F2)
- Continuous tier→SLO feedback with the double-count guard against cascades and the tipping ceiling.
- **Depends on:** F1 (reads trust/tier). **Ships behind:** `stakeholder_slo_feedback_enabled`.
- **Exit test:** no double-count vs cascade; idempotent on re-commit; never breaches tipping cap.

### Phase 3 — Promises & dialogic verb (F5)
- Engagement action in the decision payload, promise ledger, kept/broken resolution feeding F1 scars.
- Canvas-stage UI + drawer/rail per V-D; `tokens.css`.
- **Depends on:** F1 (scars), F2 (SLO credit path). **Ships behind:** `stakeholder_engagement_enabled`.
- **Exit test:** `engagement_action=None` golden-identical; kept/broken effects fire once.

### Phase 4 — Coalitions (F3)
- Activate `cascading_triggers`, coalition_pressure into strike + F2, hop-cap + one-coalition-per-round.
- **Depends on:** F2 (pressure applies to feedback) and cascade layer. **Ships behind:**
  `stakeholder_coalitions_enabled`.
- **Exit test:** strike prob monotonic in coalition size, clamps at 1.0, hop-cap holds.

### Phase 5 — Uncertain thresholds & patience (F4)
- Seeded jitter at session init, patience clocks; retire the bare-`random` cosmetic call.
- **Depends on:** F1 (tiers now on trust). **Ships behind:** `stakeholder_uncertainty_enabled`.
- **Exit test:** seed-reproducibility; patience forces escalation on flat trace.

### Phase 6 — Intent-forward UI (F6)
- Demand/leverage/trend surfacing; rail tab + expand drawer; facilitator keeps raw numbers.
- **Depends on:** F1–F5 for the data it displays. **Ships behind:** `stakeholder_intel_ui_enabled`.
- **Exit test:** no client-side score math; tooltip/mirror tripwires green.

**Sequencing note:** Phases 1→2→3 deliver the core "relationship with stakes and history" and are the
minimum viable upgrade. 4–6 deepen drama and legibility and can follow after a playtest of 1–3.

---

## 9. Risk register — what could break, and the mitigation

| Risk | Why it happens | Mitigation |
|---|---|---|
| **Double-counting SLO** | F2 + cascades + tipping all write SLO | F2 suppressed for cascaded NPCs same round; tipping clamp runs last untouched; golden trace |
| **Two drifting "feel" values** | `trust` vs `attitude_score` | §7 reconciliation, single bridge function, documented authority |
| **New state silently dropped** | `GlobalStateOut` rejects extras (AUDIT-026) | keep new state in `global_state` sub-dicts (raw-JSON persisted); typed fields only via explicit `Optional` add |
| **NPC state resets every round** | `_assemble_global_state` whitelist drops `npc_stakeholders`; `run_new_engines` re-inits it (Phase-0 finding) | §1.7 prerequisite — whitelist `npc_stakeholders` in `_assemble_global_state`; carry-forward regression test gates F1 |
| **Non-determinism across cohort** | bare `random` / per-round jitter | all RNG via `event_rng`; jitter drawn once at session init |
| **Runaway contagion death-spiral** | uncapped `cascading_triggers` | hop-cap 1, one coalition/round, strike clamps at 1.0 |
| **Tick blocked by a stakeholder bug** | new engine throws | toggle + try/except `[WARN]` wrapper, matching every existing engine |
| **UI review defect (v3)** | new always-on panels | V-D: each surface names exactly one slot; canvas/drawer/rail only |
| **Silent behaviour change for old clients** | new decision field | `engagement_action` optional/`None` default; golden-identical test |
| **Mirror/catalog drift** | new front/back action catalog | ship a tripwire or generate copy from one backend source |

---

## 10. Verification approach (before merge of each phase)

1. **Golden round-trace** (Phase 0 oracle) diffed; intentional changes reviewed line-by-line.
2. **Unit tests** per feature as listed.
3. **Existing tripwires green:** `test_role_hierarchy_sync.py`, `shockwave-catalog.test.js`,
   `test_universal_math_engine.py`, `test_qa_monte_carlo.py` (SLO/strike Monte-Carlo bounds).
4. **Determinism harness:** run the same seeded cohort twice; assert identical state hashes.
5. **Toggle-off = today:** with all `stakeholder_*_enabled` flags off, the full golden trace must be
   byte-identical to pre-change `main`.
6. **Playtest gate after Phase 3:** facilitator dry-run of a 10-round session; confirm the
   relationship/promise loop reads as intended and pacing isn't overwhelmed.

---

---

## 11. Enabling the stakeholder waves (operations)

All six waves ship **dark** — every one is gated on its own pedagogical toggle, all default
**off**, so a fresh install behaves exactly like pre-change `main` and the golden trace stays
byte-identical. Nothing below requires a code change; the toggles are per-cohort.

**The toggles** (default off):

| Toggle | Wave |
|---|---|
| `stakeholder_memory_enabled` | F1 — trust stock, scars, sentiment bridge |
| `stakeholder_slo_feedback_enabled` | F2 — continuous tier→SLO feedback |
| `stakeholder_engagement_enabled` | F5 — engagement actions + promise ledger |
| `stakeholder_coalitions_enabled` | F3 — coalitions & salience contagion |
| `stakeholder_uncertainty_enabled` | F4 — seeded thresholds + patience |
| `stakeholder_intel_ui_enabled` | F6 — intent-forward intel rail |

**How to flip them (no code):** a facilitator sets them per cohort in the cohort-setup modal
(Simulation Engine → stakeholder waves). The switch writes the key into the session's
`pedagogical_overrides`, which `round_logic.run_new_engines` reads through
`get_pedagogical_toggles` each round. The keys are whitelisted in
`save_cohort_pedagogical_settings` and listed in the god-mode features dashboard for visibility.

**Recommended enablement order** (matches the phase dependencies):

1. `stakeholder_memory_enabled` first — it's the foundation the others read (trust, tiers).
2. then `stakeholder_slo_feedback_enabled` — the closed loop builds on memory.
3. then `stakeholder_engagement_enabled` — promises feed the F1 scars.
4. `stakeholder_coalitions_enabled`, `stakeholder_uncertainty_enabled`,
   `stakeholder_intel_ui_enabled` can follow in any order once 1–3 feel right in playtest.

Enabling F1–F5 is expected to **change the golden trace** (trust/SLO now evolve). That diff is the
signal the wave is working — review it and re-baseline deliberately with
`MURESSONS_REBASELINE_GOLDEN=1` in the same commit that turns the wave on by default (per §10). F6
is diagnostics-only and never moves the golden.

**Calibration:** all tunables (trust rates, SLO coupling, coalition gains, jitter band, patience
limit, engagement costs) resolve through `config.py`'s config-dict pipeline, so they can be tuned in
`simulation_config.xlsx` without a code change.

---

*End of spec v1. Open decision for sign-off: F1 §1.4 bridge-vs-merge, and the exact tunable values
(trust rates, coupling, jitter band, patience limit) — recommend setting these in
`simulation_config.xlsx` so facilitators can calibrate without a code change, consistent with the
existing config-Excel pipeline.*
