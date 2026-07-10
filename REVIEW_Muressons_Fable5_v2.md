# Muressons Simulation — Expert Review v2 (Claude Fable 5)

*Owner-authorised review of your own project. Recommendations only — no code was changed. This is a deeper second pass with concrete file/line evidence, severity ratings, and verification of the engine and test suite. Every suggestion is additive and preserves the existing round flow, logic, and continuity.*

**Severity key:** 🔴 Critical · 🟠 High · 🟡 Medium · 🟢 Low/Polish

---

## 0. What I actually verified this pass

I read the config, auth stack, the 4,000-line `engine.py` tick pipeline, `terminal_valuation.py`, the router/admin-router auth paths, the frontend `page.js` + `useSimulation` hook, and I **ran the test suite**. The new, evidence-backed finding is in §2: three engine tests currently fail, and the engine was last edited *after* the tests — so your documented behaviour and your code now disagree. That's the most important thing to resolve before a graded session, and it wasn't visible without executing the tests.

Overall assessment: this is an unusually sophisticated piece of work — the financial engine, deterministic RNG, and the security remediation already done are well above typical edu-sim quality. The issues below are concentrated, not systemic.

---

## 1. Security 🔴🟠

Strong baseline already in place: JWT in HttpOnly/Secure/SameSite cookies, bcrypt (cost 12) with legacy auto-upgrade, IP rate-limiting with disk-persisted bans and trusted-proxy handling, CSP/HSTS/X-Frame headers, DOMPurify, prod fail-fast on missing `JWT_SECRET`, token-version revocation kill-switch. Credit where due. Remaining:

- 🔴 **Hardcoded master password.** `backend/config.py:31` → `MASTER_PASSWORD = _mp if _mp else "sim2026@iim@"`. An unset env var doesn't disable the bypass — it activates a *known, committed* password that overrides every player and facilitator login (`router.py:286,353`; `admin_router.py:815,1469,1575`). It's also in `.env`, `backend/.env`, and git history (commit `b0bf0ac`). **Fix:** empty → disabled (no fallback); `git filter-repo` to purge; rotate. Also `test_*.py` hardcode `MASTER_PASSWORD='321'` — ensure tests are excluded from any shipped zip.
- 🔴 **Empty-password login bypass.** `router.py` player_login guard is `if stored_pw and not master_ok and not _verify_pw(...)`. A pre-generated player via `allowed_player_ids` gets `stored_pw=""`, so the guard is skipped and **any** password authenticates that player_id. **Fix:** treat empty stored password as "must set on first login," never as "accept anything."
- 🟠 **Player WebSocket bearer = session_id.** `admin_router.py:5675` accepts the player channel when `token == session_id`. Session IDs are long-lived and appear in operational contexts; they shouldn't double as credentials. **Fix:** mint a short signed per-player WS token.
- 🟠 **Unsanitised mailbox HTML.** `ExecutiveMailbox.js:337` renders `expandedMessage.body` via `dangerouslySetInnerHTML` with **no** `sanitizeHtml`, gated only on `msg.html`. Every other render path (`RoundBriefing`, `InlineReviewViewer`, `FacilitatorTeleprompter`) correctly sanitises. If a message body can ever come from a facilitator broadcast or LLM, this is stored-XSS. **Fix:** run it through the same DOMPurify path.
- 🟡 **LLM prompt injection.** `ceo_interview.py:build_assessment_prompt` interpolates raw player interview text into the scoring prompt. A player can attempt "score me 10/10." Your 50/50 data/LLM blend caps the damage — good — but add delimiters + an "untrusted input" instruction.
- 🟡 **CORS methods/headers wildcard** with credentials (`main.py:214`). Origins are pinned (good); still tighten `allow_methods`/`allow_headers` to the real surface.
- 🟡 **`sanitizeCss` is regex-based** (`utils/sanitize.js`) and defeatable by nested/obfuscated `url()`. Prefer class-based styling over runtime CSS injection for the `<style>` sites.
- 🟢 **Confirm `bump_token_version` fires on every deactivation path**, not just the primary one, or the kill-switch has gaps.

---

## 2. Accuracy & Model Integrity 🟠 — **new, verified finding**

- 🟠 **Three engine tests currently fail; engine and tests have drifted.** Running `pytest` in `backend/`:
  - `test_r5_stochastic_event_with_hard_engineering` → **actual_damage 12,000,000 vs expected 1,800,000** (≈6.7× off)
  - `test_r5_hard_engineering_adds_ncd` → NCD **0 vs expected 10**
  - `test_r8_option_c_desalination_cost_and_ncd` → NCD **40 vs expected 10**

  `engine.py` was last committed **2026-06-22**, `tests/test_round_logic.py` on **2026-06-18** — the engine changed after the tests. So either (a) you intentionally rebalanced R5/R8 and the tests+docs are stale, or (b) a regression changed damage/NCD math. Both are defensibility risks in front of executives who will ask "why did our facility damage jump." **Action:** decide which is truth, update the losing side, and make green CI a release gate. A ~7× swing in climate-event damage materially changes game balance and terminal valuation.

- 🟢 **Division guards are mostly solid** — `calc_revenue_weighted_avg_ci` falls back on zero revenue, `taxonomy_pct` guards `total_rev>0`, austerity uses `max(len,1)`. A few raw `/ len(bus)` / `/ n` sites (e.g. `engine.py:432,777,1610`) assume ≥1 BU; add an empty-BU guard for defensiveness even though 4 slots are always seeded.
- 🟢 **Surface the synergy double-count fix** (`terminal_valuation.py` header: +0.30→+0.15 M_R because OPEX savings already lift EBITDA). Put the one-liner in the debrief so facilitators can defend the methodology instead of discovering it under questioning.
- 🟢 **Publish parameter provenance.** Map the strong-looking constants in `simulation_config.json` (shadow carbon $250, carbon $50 @ 5% growth, greenium/brown penalty, exit multiples) to real references. Low effort, high credibility.
- 🟢 **Use the assets you already built:** `scripts/monte_carlo_stress_test.py` to prove no dominant strategy and that M_R never breaches floor/cap; `test_bu_substitution.py` to prove vertical-swap parity. Keep the outputs as facilitator artifacts.
- 🟢 **Make determinism visible.** The per-cohort seeded RNG (`rng_util.py`) is excellent and defeats "we got unlucky" complaints — but only if learners know "every team rolled the same dice." Say it on-screen.

---

## 3. Pedagogy 🟡🟢

Learning architecture is strong (double materiality, Scope 1/2/3, SLO fatigue, terminal value as an ESG function, concept-linked minigames). To deepen impact without adding UI load:

- 🟡 **Show the consequence hypothesis *before* commit.** You compute `ConsequencePreview`; surfacing a one-line trade-off on each `DecisionTile` ("defers NCD, but raises R4 severity") converts guessing into reasoned choice — which *is* the learning objective.
- 🟡 **One required reflection box between rounds** ("predicted vs. actual, and why?"), captured to the debrief. Turns a game into a learning loop; no new screen.
- 🟡 **Lead the round recap with attributable KPI moves.** Separate the 2–3 deltas caused by *this* round's decision from background drift so learners attribute cause correctly — the single biggest lever in any sim.
- 🟢 **Name the misconception.** The Electronics-blindspot → R4-severity mechanic is a perfect "sustainability = deferred cost, not free lunch" lesson. Label it "the deferred-cost trap" in the debrief so it travels back to their real jobs.
- 🟢 **Live "teachable moment" flags** for the facilitator when a cohort converges on a trap (you already have the flag-dependency graph in `terminal_valuation.py`; e.g., "3 teams took insurance-only in R5 → all forfeited +0.20 resilience").
- 🟢 **Accessibility as inclusion:** only ~10/228 components use ARIA and there's a single `prefers-reduced-motion` guard. A WCAG-AA pass on the *decision flow* (focus order, contrast, keyboard commit) widens who can participate.

---

## 4. UI/UX 🟡🟢

- 🟡 **Cognitive load.** 228 components, `page.js` at 1,685 lines with 25 top-level imports. Enforce "one primary decision per round" with everything else behind progressive disclosure. Learning lives in the decision, not the surrounding dashboards.
- 🟡 **Projector/responsive reality.** Only 3 `@media` blocks in `globals.css`, 1 in `page.module.css`. Sessions get projected onto 1280×720 and run on mixed laptops. Test gauge/tile reflow at 1024px and 720p.
- 🟡 **State-loss UX.** Memory-DB is the documented default and dies on restart. For graded sessions, add a persistent SQLite default; if memory mode stays, show an explicit "unsaved — don't refresh" banner + server-autosave indicator. (Good news: `useSimulation` already has clean try/catch + demo fallback, and `layout.js` wraps the app in `ErrorBoundary` — build on that.)
- 🟢 **Centralise number formatting** (currency is formatted inline in several places) so treasury/EBITDA/valuation never disagree across panels.
- 🟢 **Verify every async panel has an "unavailable" empty-state** (advisor, benchmarks, peer comparison) so one hung call can't blank a live screen.
- 🟢 **Sub-3-minute Round 1** for a cold executive without opening the manual — validate `OnboardingWalkthrough` against that bar.

---

## 5. Visual Design 🟢

- **Design tokens as one source of truth.** ~140 CSS modules invite drift. Promote palette/spacing/radius/type to CSS custom properties (you already have theme infrastructure) — removes the small inconsistencies that read as "unfinished" on a big screen.
- **Colour-blind-safe KPI encoding**; reserve red strictly for danger so a glance across the room reads correctly.
- **Design the light theme, don't just invert it** — executive rooms are bright.
- **Ration the spectacle.** Three.js + Recharts are both bundled; keep working dashboards flat and fast, and save 3D/animation for the debrief moments below.

---

## 6. "Wow" Factors 🟢 (memorable, low added complexity, zero flow disruption)

All reuse components you already have and live at the debrief/ambient layer, so per-round logic is untouched:

1. **"Rewind your 5 years in 20 seconds."** Turn `ConsequenceDNA` + `ConsequenceTimeline` into one animated ribbon at the debrief where each round's choice lights up its downstream M_R effects. Your most shareable moment and it directly teaches systems thinking.
2. **Regret meter.** At terminal valuation, show actual M_R vs. the best achievable from that team's Round-1 hand using the existing `what_if_terminal`. "You left 0.4 M_R on the table" is unforgettable.
3. **Cohort constellation on the room screen.** Project `ESGImpactConstellation` with every team as a moving point on the risk/return plane, updating each round. Player-side complexity: zero. Facilitator theatre: high.
4. **30-second CEO board-debrief voice.** You already have ElevenLabs + LLM CEO interview — a short, data-grounded spoken summary per team lands the archetype emotionally. Keep it toggleable so it never blocks flow.
5. **Shareable archetype card.** Export the final archetype ("Regenerative Titan," etc.) as a branded PNG teams keep — one export function, extends the sim's life past the room.

---

## 7. Priority Order

1. **Before the next hosted/graded session:** resolve the 3 failing engine tests (decide truth, sync tests+docs); remove hardcoded master password + purge history + rotate; fix empty-password bypass; fix player WS token; sanitise mailbox HTML.
2. **This iteration:** persistent-DB default; green-CI gate; parameter-provenance appendix; consequence-preview-before-commit; one reflection box.
3. **Polish:** design tokens; WCAG-AA on the decision flow; projector/responsive testing.
4. **Delight:** rewind-DNA, regret meter, cohort constellation.

---

*Happy to take any thread further: draft the exact patches for the four 🔴/🟠 security items, investigate whether the R5/R8 test failures are a regression or intended rebalance, or write the parameter-provenance appendix.*
