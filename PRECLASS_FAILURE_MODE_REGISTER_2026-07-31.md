# Muressons — Pre-Classroom Launch Check & Failure-Mode Register

**Date:** 2026-07-31 · **Live commit:** `d331d5a` on `cso.mastersustainability.org` · **Verdict: GO**, with the standing-fix shortlist below.

---

## 1. What was verified today (live + local)

| Check | Result |
|---|---|
| All commits pushed | `origin/main` = local HEAD; nothing unpushed except the two commits made during this check (see §4) |
| Railway deployment | `d331d5a` ACTIVE, "Deployment successful"; single service on one domain (the old two-deployment ambiguity is resolved) |
| `/health` | `postgresql`, `demo_mode:false`, volume `/data` writable + durable |
| **Login 500 (the "password not working" bug)** | **Fixed and verified live**: wrong-password probe returns 403 with a clean message, not 500. Root cause was a `null` identity field in the facilitator registry crashing the login scan for *every* account including god_mode. Fixed in three layers (crash-proof read, null-refusing write, self-healing load); the self-heal repaired the production registry on deploy. |
| Route discipline | Unknown admin routes 404; real routes unauthenticated 401; no stack traces leak |
| Security headers | `X-Frame-Options: DENY`, `nosniff`, CSP present. **HSTS missing** (F-20) |
| Latency | `/health` 297–303 ms ×5 (India→US East); server-side response time ~15 ms |
| Resource headroom | CPU ~0, memory ~180 MB flat, error rate 0% — ample for a 20-player class |
| Postgres PITR | Bucket at 20.1 MB and growing — WAL archiving genuinely active |
| Classroom drill (same code, local) | god login → cohort → 3 players join → 3 full decision rounds → round advances → treasury evolves sanely (50M→85.3M) → engines (board-governance, supply-chain, biodiversity), peer-leaderboard, SDG dashboard all 200 → cross-player access refused → negotiation gated cleanly |
| Guardrails observed working | Missing-BU decisions → 400 naming the BUs; stale round → 409 "Refresh your dashboard"; double-commit → 429 "Wait 5 seconds"; roster cap enforced |
| Backend tests | 1707 passed (chunked); only failure is the sandbox-only `test_off_railway_repo_dir_is_durable` (read-only mount here; passes on a writable checkout) |
| Frontend tests | All 27 suites pass after repairing four stale test anchors (see §4) |
| Production build | Proven by Railway's successful image build of `d331d5a` |

---

## 2. Failure-mode register

Likelihood: L(ow)/M(ed)/H(igh) for a typical class day. Blast: what a class actually experiences.

### A. Platform & infrastructure

| # | Failure mode | L | Blast radius | Detection | Classroom workaround | Permanent fix |
|---|---|---|---|---|---|---|
| A1 | Railway container restart mid-round | L | ~30 s outage; JWT cookies survive; state is in Postgres | Players see spinner; `/health` down | Wait 60 s, refresh. Nothing is lost — commits are transactional | **In place** (Postgres + volume + restart-safe bans). Optional: add a Railway healthcheck alert |
| A2 | Postgres outage / connection refusal | L | Total — no reads or writes | 500s everywhere; `/health` shows db error | None in-room; pause the class | **Mitigated**: PITR + daily backups verified. Recovery = Railway restore, ~minutes. Keep the restore runbook (§3.1) printed |
| A3 | Connection-pool exhaustion under commit bursts | L | Commits hang, then 30 s timeouts | Slow commits at round deadlines | Stagger the round deadline ("commit when ready", not "everyone at 10:00:00") | **Fixed** earlier: pool 10→40, bounded acquire (10 s) + command (30 s) timeouts; 20-player load test passed |
| A4 | Deploy triggered mid-class (a push to `main` auto-deploys) | M | ~1–2 min restart + old cached JS against new API | Railway dashboard | **Do not push during class.** If it happens: everyone hard-refreshes | Proposed: enable Railway "wait for CI" or use a `production` branch so class-time pushes to `main` don't deploy (config change, 10 min) |
| A5 | Domain/TLS failure on `cso.mastersustainability.org` | L | Total for anyone using that URL | Browser TLS error | Fall back to the `*.up.railway.app` URL — keep it written down | Railway manages the cert; nothing to do beyond keeping the fallback URL handy |
| A6 | Volume full (`/data`) | L | Writes fail; packs/configs stop saving | `/health` `writable:false` | None | Proposed: a `df` check in `/health` payload + Railway volume alert (small) |

### B. Authentication & access

| # | Failure mode | L | Blast radius | Detection | Classroom workaround | Permanent fix |
|---|---|---|---|---|---|---|
| B1 | The null-identity login 500 (all accounts, incl. god_mode) | — | Was total | 500 on login | — | **Fixed + live-verified today** (`d331d5a`); regression-tested and mutation-tested; loader self-heals poisoned files |
| B2 | Facilitator mistypes password 10× on the classroom NAT → 60 s IP ban on `fac_login` | M | Facilitator locked out 60 s (players unaffected — `player_login` has a separate 300/min-per-IP ceiling and per-account buckets) | 429 "wait N seconds" | Wait out the 60 s; it says how long | Working as designed. Optional: raise `fac_login` to the HIGH_IP class if co-facilitators share the NAT |
| B3 | Student loses their player password | M | One student idle | They tell you | Facilitator regenerates the player or reads the credential from the roster export made at setup | **In place** (generate-player, bulk roster export). Print the roster before class |
| B4 | Cookies blocked (privacy extensions, Safari ITP, kiosk browsers) | M | That browser can't hold a session | Login "succeeds" then immediately logged out | Use a normal Chrome/Edge profile; same-origin cookies usually survive default settings | Same-origin design already minimises this. Add a login-page banner "enable cookies" (small UX fix) |
| B5 | Master password leaked (it has appeared in chat/screens) | M | Full god-mode compromise | Audit log `master_password_bypass` entries you didn't make | — | **Do before class:** rotate `MASTER_PASSWORD` in Railway variables (the break-glass audit trail is already in place). Also **revoke the two GitHub PATs pasted in chat** — treat both as compromised |
| B6 | JWT signing key changes on redeploy | — | — | — | — | **Verified closed 2026-07-31**: `auth_jwt.py` persists a generated secret to the volume (`jwt_secret.key`, 0600) when `JWT_SECRET` is unset — sessions survive restarts and redeploys |

### C. Data & configuration

| # | Failure mode | L | Blast radius | Detection | Classroom workaround | Permanent fix |
|---|---|---|---|---|---|---|
| C1 | Config edits lost on redeploy (old in-image storage) | — | Was: silent revert of stakeholder/materiality edits | — | — | **Fixed**: both stores + packs live on the `/data` volume; durability pinned by tests |
| C2 | A pack references a deleted config → empty matrix mid-class | L | Would be one BU's materiality module | — | — | **Designed out**: resolution falls through to the shipped matrix; `pack_coverage` shows gaps *before* class. Check the coverage badge when selecting a pack |
| C3 | Region workbook sheet silently skipped on upload | L | One SBU on defaults without anyone knowing | Upload response lists `unmatched_sheets` and `missing_slots` | Re-upload with corrected sheet names | **In place** — but *read the upload response*; it is the only place the warning appears |
| C4 | Excel round-trip mangles engagement-tactic ids | — | Was: tactic references broke after export→reimport | — | — | **Fixed 2026-07-31**: id travels as an optional 4th field; legacy 3-field files parse unchanged; round-trip pinned by `test_tactic_id_roundtrip.py` |
| C5 | UI offered `un_sdg`/`brsr_ngrbc` paradigms the server 422s | — | Was: validation wall at cohort submit | — | — | **Fixed 2026-07-31**: both removed from the cohort/facilitator dropdowns (BRSR is correctly a *side track*, un_sdg is solo-only); solo-start now derives its set from config; drift test pins UI to `VALID_DECISION_PARADIGMS` |
| C6 | Stray untracked files in `db/` confuse a future migration | — | — | `git status` | — | **Done 2026-07-31**: `db/` clean (last stray `.write_probe` removed; the 12 `vertical_*__region.json` files are tracked and legitimate) |
| C7 | Facilitator deletion cascades to their cohorts | M (operator error) | A live cohort vanishes | Immediate | Soft-delete is the default; restore from registry | **In place** (soft delete). Never hard-delete during term |

### D. Gameplay & pacing

| # | Failure mode | L | Blast radius | Detection | Classroom workaround | Permanent fix |
|---|---|---|---|---|---|---|
| D1 | Student double-clicks Commit | H | 429 "Wait 5 seconds" — by design | Toast | Wait 5 s | **In place** (throttle). Frontend already disables the button during submit |
| D2 | Stale dashboard commit (tab open since yesterday) | M | 409 "Stale round: refresh your dashboard" | Toast says exactly what to do | Refresh | **In place** (optimistic locking with `expected_round`) |
| D3 | Two tabs / two devices, same player | M | Second tab gets 409s; no corruption | 409s | Close the extra tab | **In place** — locking makes it safe; no fix needed |
| D4 | Student stranded on a hidden end-game phase | — | Was: dead-end screen | — | — | **Fixed** (phase ladder hands forward past hidden/completed phases; re-pinned by tests today) |
| D5 | Late joiner after round 3 | M | Joins at current round with baseline state | — | Acceptable pedagogically; or regenerate the player | Works; document the expectation for TAs |
| D6 | Auto-advance fires while a team is presenting | M | Round closes under them | Pacing panel | Lead facilitator has pause/override | **In place** (`lead_facilitator` pacing controls). Assign at least one lead per room |
| D7 | Whole class commits in the same second | M | Brief queueing; pool now absorbs it | Slow spinner ≤ a few s | Nothing | **Fixed** via A3; verified by the 20-player load test |

### E. Client-side / classroom environment

| # | Failure mode | L | Blast radius | Detection | Classroom workaround | Permanent fix |
|---|---|---|---|---|---|---|
| E1 | Stale JS bundle after a deploy (API/client mismatch) | M if A4 happens | Odd errors for un-refreshed tabs | Console 4xx on old chunk names | Hard-refresh (Ctrl-Shift-R) | Avoid class-time deploys (A4). Next.js hashed chunks make refresh sufficient |
| E2 | Campus firewall blocks WebSockets | M (varies by campus) | Live push features degrade (broadcasts, shockwaves); polling paths still work | Shockwave doesn't appear on player screens | Use the wired fallbacks; test on the actual classroom network beforehand | **Do:** a 10-minute on-network smoke test the day before (checklist §3.2) |
| E3 | Projector <1280 px hides the atmosphere layer | H on small projectors | Cosmetic — facilitator theatre only | Obvious | Use a ≥1280 px output | By design (slotting rule); note in the facilitator guide |
| E4 | Very old browsers (lab machines) | L | White screen | Immediate | Move to Chrome/Edge/Firefox current | Accept; add a version banner if labs are a known risk |

### F. Security posture (open items — none block launch)

| # | Item | Risk | Fix |
|---|---|---|---|
| F-20 | No HSTS header on the app shell | — | **Fixed 2026-07-31**: added to `next.config.mjs` headers (backend `/api` already sent it) |
| F-21 | `esg_profile_weights` readable via public `/api/admin/global-settings`; raw GET `/esg-profile-weights` unguarded | — | **Fixed 2026-07-31**: weights disclosed only to authenticated facilitators or finished sessions (client falls back to defaults mid-game); raw GET now gated like its setter; pinned by `test_rubric_disclosure.py` |
| F-22 | Starlette CVEs (needs FastAPI upgrade) | Known DoS vectors | Scheduled upgrade + full suite; do in a maintenance window, **not** before class day |
| F-23 | `npm audit` 4 vulns (needs next@16) | Build-time exposure mostly | Same maintenance window as F-22 |
| F-24 | Pasted GitHub PATs ×2 | Repo compromise | **Revoke now** (user action) |
| F-25 | Master password appeared in plaintext contexts | God-mode compromise | Rotate `MASTER_PASSWORD` before class (B5) |

### G. Development-process risks (won't hit a class, will hit you)

| # | Item | Note |
|---|---|---|
| G1 | Full backend suite hangs on `test_twenty_players_can_actually_join` **only in full-suite order** (passes alone and in chunks; reproduces without today's changes) | Pre-existing cross-test interaction — likely shared rate-limit/registry state. Track down before it masks a real failure. Until then run chunked, as CI does |
| G2 | Stale test anchors (4 repaired today) | Pattern: tests pinning source layout instead of properties. When adding UI around existing code, run the *whole* frontend suite, not just the new test |
| G3 | Sandbox-only failure `test_off_railway_repo_dir_is_durable` | Expected here (read-only mount); passes on a writable checkout — not a defect |

---

## 3. Runbooks

### 3.1 If the platform dies mid-class
1. `https://cso.mastersustainability.org/health` — if it answers, it's client-side; hard-refresh.
2. Railway dashboard → Mayen service → if crashed, `Restart`. State survives (Postgres).
3. If Postgres itself is down: Railway → Postgres → restore from PITR to a few minutes ago. Cohort resumes at the last committed round.
4. Meanwhile: run the round on paper; commits can be entered when service returns (late-commit is tolerated by design).

### 3.2 Day-before smoke test (10 min, on the classroom network)
1. Open the player URL on the room's Wi-Fi *and* the projector machine.
2. Facilitator login (also proves B1 stays fixed).
3. Create a throwaway cohort → join as one player → commit round 1 → delete cohort.
4. Fire one test shockwave; confirm it appears on the player screen (tests E2).
5. Check the pack coverage badge on the cohort you'll actually use (C2/C3).

### 3.3 Before class (one-time, ~20 min total — the code-side items are DONE)
- Rotate `MASTER_PASSWORD`; revoke both GitHub PATs (F-24/F-25).
- Push the pending commits (§4) — *not* on class day (A4).
- ~~C6, F-20, F-21, C5, C4~~ all implemented 2026-07-31.
- Remaining scheduled (maintenance window, after class): FastAPI/Starlette upgrade (F-22), next@16 (F-23), the full-suite test-order hang (G1).

---

## 4. Pending push

Ready locally and verified; push when convenient (not during class):

- `cb180bc` — four stale frontend test anchors repaired (test-only).
- The hardening commit (F-20, F-21, C4, C5 + register/tests) made 2026-07-31 after this document was first written.

`d331d5a` (the login fix) is already pushed and live.
