# SPEC — Role Asymmetry Inside Teams (CEO / CFO / CSO)

Status: proposed · Depends on: calibration feature (shipped), store-parity APIs (shipped)
Related: PLAN_Calibration_Analytics.md, SPEC_Turnaround_PostR10_Extension.md

## 1. Goal

Turn a team's commit from solo optimization into a **negotiation between
legitimately conflicting mandates** — the actual learning objective of ESG
education. Three roles with different private information and different
success pressure must explicitly reach consensus before a round commits:

| Role | Mandate | Private information (server-verified sources) |
|---|---|---|
| **CEO** | Overall M_R + narrative; owns the tiebreak | Board sentiment: `board_governance` state + shadow-board deltas (exists in engine ledgers) |
| **CFO** | Covenant compliance, liquidity, dividends | True covenant headroom: `check_covenants()` diagnostics — ratio, trigger distance, surcharge forecasts (`balance_sheet.py:393`), incl. the swept short-term-debt reality |
| **CSO** | Social licence, stakeholder trust, transition | Early stakeholder intel: `build_stakeholder_intel()` (F6, `npc_stakeholders.py:801`) — demands/leverage/trend cards one round BEFORE the intel rail shows them, plus NPC patience counters |

Pedagogical claim being operationalised: each player sees a *different* slice
of the truth, so the optimal group move is discoverable only by talking.

## 2. Current state (audited, file:line)

- `team_consensus` is **decorative**: written on every decision insert
  (`database_memory.py:911`, `database.py:805`, default `"majority"`;
  `"auto_default"` for auto-commits at `admin_router.py:2894`) and read by
  nothing. It is the natural anchor for a real mechanic.
- A team = ONE session with ONE owner: SEC-3 binds a single `player_id`
  (`router._assert_player_owns_session`). Cohorts track `registered_players`
  and `allowed_player_ids` (membership helper already exists at
  `database_memory.py:706`) — but per-session, not per-seat.
- Per-session WebSocket push exists (`admin_ws.ConnectionManager
  .push_to_session:52`) for nudging seats when the proposal changes.
- Both private-info sources are already computed server-side each tick; no
  new simulation math is required — only **projection and access control**.
- Pedagogy toggles + per-cohort overrides + experience-level presets are an
  established pattern (e.g. `prediction_gates_enabled`), reused wholesale.

## 3. The hard architectural decision: seats vs. sessions

True multi-seat (three humans, three devices, one team session) requires
extending the auth model beyond one-owner-per-session. Doing that carelessly
reopens audit #9 (session-UUID bearer attacks). The spec therefore ships in
two deliberately separable modes, same data model:

**Mode A — Hot-seat roles (Phase 1–3).** One device per team (the common
classroom reality: one laptop per table). The session keeps its single
owner; role switching is an in-cockpit action ("pass the laptop"). Private
briefs are fetched per role with a short-lived role token so the UI can
enforce "CFO eyes only" moments theatrically, while the server never
releases another role's brief under the active role token.

**Mode B — Multi-seat (Phase 4, optional).** Three real `player_id`s bind to
one team session via a `seat_roster` (`{player_id → role}`) stored on the
session record. `_assert_player_owns_session` gains one clause: an
`X-Player-Id` that appears in the seat roster is an authorised caller with
that seat's role. All existing single-owner sessions behave byte-identically
(empty roster ⇒ current rule). Commit rights and private-brief access key on
the roster role, not the header alone.

Phase 1–3 deliver the full pedagogy on Mode A; Mode B is an auth extension,
not a redesign.

## 4. Data model

On the session record (cohort-provisioned, `update_session_metadata`):
```json
"role_play": {
  "enabled": true,
  "mode": "hotseat" | "multiseat",
  "seat_roster": {"P-101": "cfo", "P-102": "cso"},   // multiseat only; owner defaults to CEO
  "consensus_rule": "unanimous" | "majority_ceo_tiebreak"
}
```

Per round, in `active_event_flags.consensus_log` (same both-representations
persistence pattern as `predictions_log` — the pack/unpack parity lesson):
```json
{
  "round": 4,
  "proposal": {"choice": "option_b", "allocations": {...}, "proposed_by": "ceo"},
  "votes": {"ceo": "approve", "cfo": "object", "cso": "approve"},
  "objections": [{"role": "cfo", "reason": "breaches covenant headroom", "at": "…"}],
  "resolution": "unanimous" | "ceo_tiebreak" | "override",
  "resolved_at": "…"
}
```
`team_consensus` on each decision row is then written with the REAL
resolution (`unanimous` / `ceo_tiebreak` / `override`) instead of the
hardcoded `"majority"` — retroactively giving the existing analytics field
meaning.

## 5. Server API (all new, all SEC-3-guarded)

| Endpoint | Purpose |
|---|---|
| `GET /{sid}/role-brief/{role}` | The role's private brief. **Server-side projection** — the response for `cfo` contains covenant diagnostics that appear NOWHERE in the shared dashboard payloads; `cso` gets next-round intel cards; `ceo` gets board-sentiment digest. Client-side hiding is explicitly forbidden (a shared payload with CSS-hidden fields is a lie, and students inspect network tabs). |
| `POST /{sid}/consensus/propose` | Stage the round's proposal (choice + allocations snapshot). Overwrites any un-resolved proposal for the round. |
| `POST /{sid}/consensus/vote` | `{role, vote: approve\|object, reason?}`. Objection requires a reason ≥ 10 chars — the reason IS the pedagogy (it lands in the debrief). |
| `GET /{sid}/consensus` | Current round's proposal + votes (shared; reasons visible to all roles — objections are public inside the team). |

Commit gate (in `_commit_turn_impl`, next to the existing gates): when
`role_play.enabled`, a commit is refused (409 + explanation) unless the
current round's consensus_log satisfies the cohort's `consensus_rule` AND the
committed decisions match the approved proposal (choice + allocation hash) —
otherwise a team could "approve A, commit B". Facilitator override: the
existing manual-override surface can force-resolve (`resolution: "override"`,
audited), so a deadlocked table never blocks a class.

## 6. Consensus mechanics (kept deliberately small)

- `unanimous`: all three roles approve. An objection returns the proposal to
  draft with the reason attached.
- `majority_ceo_tiebreak`: 2-of-3 approves; a 1-1-1 or 2-object state lets
  the CEO invoke the tiebreak, which is **recorded** (`ceo_tiebreak`) — the
  debrief and ESG Leadership Profile can then surface "how often did this
  team resolve by authority instead of persuasion?"
- Timer integration: if `decision_timer_enabled` and the timer expires with
  an unresolved proposal, resolution auto-records `override` with reason
  `timer_expired` — fluency is never hostage to the mechanic.

## 7. Player UI (V-D slotting — no new ambient panels)

- **Role HUD chip** in the existing header identity area: current role badge
  + (hot-seat) a "Switch role" action. Slot: ⋯ More/identity, not a panel.
- **Private brief**: renders inside the existing Expand drawer (deep-dive,
  summoned not ambient), styled as a sealed memo ("FOR CFO EYES ONLY").
- **Consensus tray**: replaces the commit button's immediate action when
  role-play is on — the Predict-Before-Commit modal grows a third section
  (proposal summary + three vote chips + objection reasons). No new screen;
  the same single modal, one more section. Skip-path unchanged when the
  feature is off.
- **Results stage**: the round's consensus record (votes, objections,
  resolution) renders as one chip next to PredictionComparison — V-A
  retrospective placement.
- Facilitator: consensus state per team joins the Cohort Pulse payload
  (column: `awaiting: cfo` / `objection: cso` / `resolved: unanimous`), and
  the teleprompter gains one line ("Table 3 resolved by CEO tiebreak twice —
  ask the CFO what they conceded").

## 8. Toggles & tiering

- `role_play_enabled` (default OFF) + `role_play_consensus_rule` — global
  defaults in `_god_mode_settings`, `COHORT_OVERRIDABLE_KEYS`, exposed via
  `global-settings?session_id`, preset per experience level:
  Classroom OFF · Workshop OFF · Executive ON (unanimous) · Chaos ON
  (majority_ceo_tiebreak). Custom levels inherit the existing whitelist
  machinery (`_ALLOWED_PED_KEYS`).
- Backend catalog + frontend registry additions land in the same commit
  (the `calibration_analytics` missing-key lesson).

## 9. Risks & mitigations (ranked)

| Risk | Mitigation |
|---|---|
| Auth regression via seat roster (Mode B) | Roster clause is additive; empty roster ⇒ exact current behaviour. Dedicated guard tests: non-roster player 403, roster player limited to own role's brief, owner unaffected. Mode B ships behind its own flag after Mode A soaks. |
| Private info leaks via shared payloads | Briefs are separate endpoints with role-scoped projections; a tripwire-style test asserts covenant diagnostics and next-round intel keys appear in NO shared dashboard response. |
| Deadlock kills class pacing | Facilitator force-resolve + timer auto-override + the commit-gate 409 message tells players exactly which role is blocking. |
| Solo players / 1-person teams | `role_play.enabled` auto-suppresses when the session has one registered seat and mode=multiseat; hot-seat works solo by design (role rotation is itself a reflective exercise). |
| Commit/proposal mismatch exploit | Allocation hash comparison in the commit gate (approve A, commit B is refused). |
| Store parity (Postgres) | consensus_log uses the predictions_log dual-representation pattern; store-access tripwire already guards the class. |
| Engine contamination | The mechanic gates WHEN commit happens, never touches tick math. Control-run proof (seed-pinned, same technique as calibration P5): outcomes byte-identical with role-play on vs off for identical decisions. |

## 10. Verification plan

1. Unit: consensus resolution table (unanimous/majority/tiebreak/override ×
   vote permutations), proposal-hash mismatch, reason-length validation.
2. Guard: role-brief access matrix (per mode), commit-gate 409s, facilitator
   force-resolve audit trail.
3. Leak test: recursively scan `/dashboard`, `/global-settings`,
   `/round-config` responses for covenant-diagnostic and intel-card keys.
4. E2E (memory + tripwire-clean): 3-round hot-seat run — propose, CFO
   objects with reason, revise, unanimous, commit; assert `team_consensus`
   on the decision rows carries the real resolution; snapshot-restart keeps
   the consensus log.
5. Control run: seed-pinned engine-outcome diff, role-play on vs off.

## 11. Non-goals

- No LLM mediation of negotiations (the humans ARE the mechanic).
- No per-role scoring/leaderboards (would incentivise defection from the
  team optimum; the debrief surfaces resolution styles instead).
- No mid-round role rotation enforcement in hot-seat mode (tables
  self-organise; the timer already bounds dithering).
- No changes to solo-paradigm flows when the toggle is off — byte-identical.

## 12. Phasing (each lands green + committed separately)

| Phase | Scope | Size |
|---|---|---|
| 1 | Data model + consensus endpoints + commit gate + `team_consensus` becomes real | backend, ~1 day |
| 2 | Role briefs (3 projections) + leak test | backend, ~1 day |
| 3 | Cockpit UI (HUD chip, drawer brief, modal tray, results chip) + facilitator pulse/teleprompter + toggles/presets | frontend-heavy, ~2 days |
| 4 (opt) | Multi-seat roster auth (Mode B) + guard matrix | backend, ~1 day, after Mode A soaks in a real class |
