# Muressons — Implementation Plans: 3 Grand Wow Features

*Plans for #1 Trading-Floor Finale, #6 Synchronized Shockwave, #5 Year-5 Front Page. Each is grounded in existing code, is additive (no change to engine math or round flow), and degrades gracefully. Effort is rough dev-days for one experienced engineer.*

**Shared foundations (all three lean on these — verify once):**
- **Realtime:** `admin_router.py` `ConnectionManager` with `broadcast_admin()`, `broadcast_students()`, `broadcast()`; player WS at `/ws/session/{id}` (now ticket-authed), admin WS at `/ws/admin`. Players already handle typed messages in `page.js` (`msg.type === 'universal_broadcast'`, `round_unlocked`, etc.) — new event types slot into the same switch.
- **Sound:** `CockpitSounds.js` + `utils/soundManager.js` for stingers (bell, klaxon).
- **Fairness:** per-cohort deterministic RNG (`rng_util.py`) — a *forced* event is identical for all teams by construction.

---

## Feature #1 — The Trading-Floor Finale
*Synchronized "market close" at Year 5: a live ticker of every team's share price on the room screen, a bell, and an IPO-style ranking reveal.*

### The moment
Facilitator opens a projector view. A ticker of all teams' share prices scrolls live. At Year 5 the facilitator clicks **Ring the Bell** → bell sound on every screen, prices freeze, and the leaderboard slams into a ranked reveal.

### Architecture
Purely a presentation layer over data you already compute. No engine changes.

- **Data source:** the existing leaderboard (share price / terminal value per team). Confirm the leaderboard endpoint returns `price_per_share` and `terminal_value` per team; if not, add them from `terminal_valuation`.
- **Projector view:** a new facilitator-only route/panel that polls the leaderboard (or subscribes to `/ws/admin`) and renders the ticker + board.
- **The "close":** a facilitator action broadcasts a `market_close` event to the cohort; every screen reacts.

### Files
- **New:** `frontend/app/components/TradingFloorFinale.js` — full-screen projector layout: `MarketTicker`-style scroller across the top, a large ranked board, a **Ring the Bell** button (facilitator only). Reuses `StockPerformanceChart` for per-team sparklines.
- **New backend endpoint:** `POST /api/admin/{cohort}/finale/ring-bell` (`require_facilitator`) → builds the ranked payload and calls `manager.broadcast(cohort, {type:'market_close', ranking:[...], closed_at})`.
- **Edit (small):** `page.js` player WS switch — on `market_close`, show a lightweight "📉 Market closed — see the main screen" overlay with the team's own final rank. Zero required interaction.
- **Reuse:** `soundManager` for the bell; existing leaderboard fetch.

### Build steps
1. Backend: confirm/extend leaderboard payload with `price_per_share`; add the `ring-bell` endpoint + broadcast.
2. Frontend: `TradingFloorFinale.js` — ticker + live board, polling every ~5s and updating on WS `round_committed`.
3. Wire the bell: button → endpoint → `market_close` broadcast → freeze + ranked reveal + bell sound.
4. Player overlay on `market_close` (optional but nice).
5. Add a God-Mode/Facilitator menu entry "🔔 Trading Floor (project this)".

### Effort / risk
~2–3 days. **Low risk** — additive view + one endpoint; touches no round logic. Fallback: if WS drops, the projector view still polls the leaderboard, so it never goes blank (your resilience pattern).

### Guardrails
Facilitator-triggered only; the "close" is cosmetic (freezes the *display*, not the sim). Works even mid-game as a "current standings" board if you don't ring the bell.

---

## Feature #6 — The Synchronized Shockwave
*Facilitator "detonates" a global black-swan event; every team gets a simultaneous full-screen takeover with klaxon, countdown, and a forced response.*

### The moment
Facilitator picks an event (Ransomware, Carbon-Tax Spike, Supply Collapse) and hits **Detonate**. Every player screen is taken over at once: red alert, klaxon, a countdown timer, the event brief, and a **Respond Now** button that drops them into the decision. Because it's forced, all teams face the identical shock — the debrief is a clean comparison of crisis leadership.

### Architecture
Two parts: (a) **inject** the event so the engine applies its impacts on the next tick, and (b) **broadcast** the dramatic alert. You already have both halves.

- **Event catalogue:** `black_swan_registry.py` → `BLACK_SWAN_EVENTS`, `get_available_black_swans(round)`, `apply_black_swan_impacts()`. A forced detonation sets the chosen event **active regardless of probability**.
- **Injection:** for each player session in the cohort, mark the event as active/pending so the next `process_tick` runs it through `apply_black_swan_impacts` (same code path as a natural black swan — no new math).
- **Broadcast:** reuse the `universal_broadcast` mechanism (`admin_router.py:6550`) with a new `type:'shockwave'` payload (event id, title, brief, `expires_at`).

### Files
- **New backend endpoint:** `POST /api/admin/{cohort}/shockwave` (`require_facilitator`), body `{event_id}` → (1) for every child session of the cohort, set the forced event in its active-event/pending state; (2) `manager.broadcast_students(cohort, {type:'shockwave', event, expires_at})`.
- **New:** `frontend/app/components/ShockwaveOverlay.js` — full-screen takeover: pulsing red vignette, event title + brief, `CountdownTimer` (you have it), **Respond Now** → routes to decisions. Klaxon via `soundManager`.
- **Edit (small):** `page.js` player WS switch — on `shockwave`, mount `ShockwaveOverlay`.
- **Facilitator control:** extend the existing `CrisisTriggerConfig.js` / `CustomBlackSwanBuilder.js` with a "Detonate to cohort" button (event picker + confirm).

### Build steps
1. Backend: `shockwave` endpoint. The careful part is the **forced injection** — add a helper in `black_swan_registry` like `force_event(session_state, event_id)` that inserts the event into the same structure `evaluate_black_swans` normally populates, so the next tick applies it verbatim. Unit-test that a forced event applies its documented treasury/rep impact.
2. Backend: broadcast the `shockwave` alert to students.
3. Frontend: `ShockwaveOverlay` + WS handler + klaxon + countdown.
4. Facilitator: detonate control (reuse the crisis-trigger UI + a confirm modal).
5. Debrief hook: tag the forced event in each team's history so the recap can compare responses.

### Effort / risk
~3–4 days. **Medium risk** — the injection touches engine *state* (not math). Mitigate with a dedicated `force_event` helper + a unit test asserting impacts match the registry, and by reusing `apply_black_swan_impacts` rather than writing new effect code. Fallback: if injection fails for a team, they still get the *visual* shockwave (pure theatre) and the facilitator can apply the impact via the existing manual-override path — so the room moment never breaks.

### Guardrails
Facilitator-gated, confirm-to-fire. Reuses the existing black-swan effect pipeline, so a forced event behaves exactly like a natural one — defensible and balance-safe. Determinism is automatic (it's forced, not rolled).

---

## Feature #5 — The Year-5 Front Page (AI newsreel)
*A mock Financial Times / Bloomberg front page per team, generated from their trajectory, exportable as an image — with a "brown" cautionary contrast version.*

### The moment
On the game-over screen, a newspaper front page fades in: masthead ("THE MURESSONS TIMES · YEAR 5"), a headline that fits the team's fate ("REGENERATIVE TITAN OF THE DECADE" vs "£2BN STRANDED-ASSET WRITEDOWN"), a sub-head, an analyst quote, a mini stock chart, and a **Download front page** button. Optionally show the counterfactual brown version side-by-side.

### Architecture
LLM generates the copy from real final data; **always** falls back to deterministic templates so it works with no API key. Rendering + export reuse the `ArchetypeCard` SVG→canvas→PNG pattern you already shipped.

- **Backend:** new endpoint gathers final-report data (archetype, M_R, terminal value, share price, notable captured/missed flags, trajectory) and calls the LLM using the existing plumbing in `ceo_interview.py` (`score_responses_with_llm` shows the `httpx` + `LLM_API_KEY/PROVIDER/MODEL`, anthropic/openai branches). Returns structured JSON `{tone, headline, subhead, analyst_quote, bullets[]}`.
- **Fallback:** if `LLM_API_KEY` is unset or the call fails, return a deterministic template keyed by archetype band (so the feature is never dead).
- **Frontend:** a newspaper-styled component + PNG export.

### Files
- **New backend endpoint:** `GET /api/simulations/{session}/front-page` (player-readable) → returns the front-page JSON. Cache per session (low temperature; regenerate on request only if forced) so it's stable across reloads.
- **New:** `backend/front_page.py` — `build_front_page_prompt(final_data)` + `FALLBACK_TEMPLATES[archetype_band]`. Wrap the team's data in clear delimiters and instruct "return JSON only" (prompt-injection hygiene — same as the interview scorer).
- **New:** `frontend/app/components/FrontPageReveal.js` — masthead + headline + subhead + quote + mini `StockPerformanceChart`, styled as newsprint. **Download** button reuses the SVG→canvas→PNG approach from `ArchetypeCard.js`. Sanitize LLM text with `sanitizeHtml` before render.
- **Edit (small):** `GameOverSummary.js` — mount `FrontPageReveal` near the archetype hero (you already added the wow block there); include a loading state and the fallback.

### Build steps
1. Backend: `front_page.py` with the prompt builder + per-archetype fallback templates; endpoint that assembles final data, calls the LLM, validates JSON, falls back on any error.
2. Backend: reuse `ceo_interview.py`'s LLM call shape (anthropic/openai, 30s timeout, JSON-only).
3. Frontend: `FrontPageReveal.js` (newsprint layout + PNG export), sanitized render, loading/fallback states.
4. Wire into `GameOverSummary`; optional "show the brown counterfactual" toggle using the same generator with the missed-M_R flags flipped.

### Effort / risk
~2–3 days. **Low–medium risk** — the deterministic fallback guarantees it always works; the LLM path is optional polish. Reuses your proven export pattern and existing LLM plumbing. Guardrail: LLM output is untrusted → JSON-schema-validate server-side and `sanitizeHtml` client-side before rendering.

### Guardrails
Never blocks the debrief (fallback template on any LLM failure/timeout). Grounded in the team's real scores, so headlines are earned, not random. Low temperature + JSON-only + sanitisation keeps it safe and repeatable.

---

## Suggested build order (wow-per-effort)
1. **#1 Trading-Floor Finale** — lowest risk, highest room-energy payoff, mostly reuses the ticker + leaderboard + WS. Ship first.
2. **#5 Year-5 Front Page** — self-contained, reuses your export + LLM patterns, and the fallback makes it safe. Great shareable.
3. **#6 Synchronized Shockwave** — highest theatre but touches engine state, so do it last with the `force_event` helper + a unit test as the safety net.

**Cross-cutting prerequisites to nail once:** (a) confirm the player WS is reliably delivering typed messages end-to-end (the ticket auth is in; test a round-trip), (b) add 2–3 short audio stingers (bell, klaxon, market-close) to `soundManager`, (c) a small facilitator "Showrunner" menu to launch the finale / detonate / reveal, so the theatre is one click during a live session.

*Each plan is intentionally additive: no changes to `engine.py`, `round_logic.py`, or `terminal_valuation.py` scoring — these features present, broadcast, or force-inject via existing pipelines, so balance and continuity are preserved.*
