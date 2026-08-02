# Muressons — Comprehensive Deployment & Classroom Audit

**Date:** 29 July 2026
**Audited:** `2591121` → fixes committed as `e307b36`
**Deployment:** `mayen-production.up.railway.app` (Railway project `perceptive-enchantment`)
**Auditor role:** system architect / senior developer review, sole-owner context

---

## Verdict

**Deploy `e307b36`, then do two Railway actions, and you are ready for the classroom.**

Four defects were found that would each have hit a live class. None were visible to the test suite — all 1546 tests passed with every one of them present. They were found by auditing the *deployment* and the *shape of the code*, not by running the tests again.

| # | Defect | Severity | Status |
|---|---|---|---|
| 1 | Connection-pool deadlock when a class commits together | **Critical** | Fixed + tripwire |
| 2 | Cross-team tampering via 16 unguarded endpoints | **Critical** | Fixed + tripwire |
| 3 | `max_players` silently ignored — 20-player cohorts capped at 5 | **High** | Fixed + tripwire |
| 4 | Extended Horizon (rounds 11–20) 100% broken | **High** | Fixed + tripwire |
| 5 | Dependency CVEs incl. the JWT signing library | Medium | 3 of 4 fixed |
| 6 | **No database backups at all** | **Critical (operational)** | Needs your action |

---

## 1. Connection-pool deadlock — the worst finding

This one fires at the precise moment a class is most exposed: everyone presses Commit at the end of a round.

`acquire_advisory_lock` takes a connection from the pool and **holds it for the entire commit**, while that same commit's queries take further connections from the same pool. Each in-flight commit therefore costs roughly two connections. The default was `DB_MAX_CONNECTIONS=10`, so a cohort past about five students could consume every connection holding locks, leaving none for the queries those locks were taken for.

Worse, `pool.acquire()` was called with no timeout, so it did not degrade — it waited forever. Measured against a real PostgreSQL server:

| Concurrent commits | Pool size | Result |
|---|---|---|
| 12 | 10 (old default) | **Never returned** |
| 12 | 40 | 0.4s, all `201` |
| 20 | 40 | 0.5s, all `201` |

A class of 12+ committing simultaneously would have hung the server with no error and no recovery short of a restart.

**Fixed on both axes**, because either alone still fails:

- Default pool raised to **40**, above 2× the 20-player ceiling, with headroom for facilitator dashboards and websockets. It stays well inside a managed Postgres limit of ~100 — but note the pool is **per worker**, so if you ever raise `WEB_CONCURRENCY`, keep `workers × DB_MAX_CONNECTIONS` under the server's `max_connections`.
- All 23 acquire sites now carry a timeout, plus a `command_timeout` on the pool. Exhaustion becomes a visible `503` instead of a silent hang. Verified: pool of 2 with 8 committers now errors in ~2s.

---

## 2. Cross-team tampering — proven, not theoretical

Sixteen mutating handlers under `/api/simulations/{session_id}/...` were declared like this:

```python
async def board_vote(session_id: str, body: dict):
```

No `request` parameter. There is nothing to read a cookie or `X-Player-Id` from, so **no ownership check could run** — not because someone deleted it, but because the handler could not physically perform one.

I proved the consequence end to end against a victim session:

```
anonymous POST /api/simulations/{victim}/board-vote  ->  200 OK
victim's group_reputation AND corporate_treasury both changed
```

In a classroom, session IDs are exposed constantly — projected on a screen, sitting in a browser URL bar, in a screen-share, in a support screenshot. A student who notes another team's session ID could vote in their boardroom, run their supply-chain audits, activate regulatory instruments, or submit their CEO interview.

Affected: `board-vote`, `supply-chain-audit`, `coalition-check`, `regulatory-sandbox/activate` and `/trigger-event`, all five `ceo-interview/*` endpoints, `negotiation/open` and `/say`, `side-tracks/{id}/commit`, `paradigm`, `pace-lock`, `round-timer`.

All sixteen now take `request` and call `_assert_player_owns_session`. `join_session` remains deliberately exempt — it authenticates with player ID + password, which is how a player obtains a session in the first place.

**Verified after the fix:** the same anonymous attack now returns `403` on every attempt with zero state change, while the legitimate owner still gets `200`.

---

## 3. `max_players` was silently ignored

`resolve_roster_cap` read only `team_count`. The `max_players` control — named for roster size, clamped to a ceiling of 20, and the entire point of the "up to 20 players per cohort" work — was inert:

```
PATCH cohort-settings {"max_players": 20}   ->  200 OK, saved, reads back as 20
6th student joins                            ->  400 "roster cap of 5 player(s)"
```

The save succeeded and the setting read back correctly. Only the join gate disagreed, so nothing surfaced the mismatch until students were already in the room and the sixth could not get in.

Both knobs now raise the cap and the larger wins, so setting either does what you meant and no existing cohort shrinks. **Verified: 20 students generate, join, and commit concurrently.**

---

## 4. Extended Horizon was 100% broken

`POST /{session_id}/extend` called `db.advance_round(...)` — a function that exists in **neither** backend. Every call raised `AttributeError` → HTTP 500. Rounds 11–20 could never be activated by anyone, on either backend, ever.

It was also the most severe instance of defect 2: with no `request` parameter, an anonymous caller could clear `game_over` on any session.

Now uses `insert_next_round` (the same parity call `commit_turn` uses), is ownership-guarded, and is idempotent so a double-click cannot violate `uq_session_round`. Verified: `403` anonymous, `403` wrong player, `200` owner, dashboard advances to round 11, re-activation safe.

---

## 5. Dependencies

`pip-audit` found 22 advisories across 5 packages. Fixed and re-verified against the full suite:

- **`python-jose` 3.3.0 → 3.4.0** — the highest-value one: this library signs your facilitator auth cookie. Mitigating detail worth knowing: every `decode` call already pins `algorithms=["HS256"]`, which blunts the algorithm-confusion class, but the library fix belongs in place rather than relying on call-site care.
- `python-multipart` 0.0.20 → 0.0.31 (6 advisories)
- `python-dotenv` 1.0.1 → 1.2.2

**Not fixed — needs a scheduled change, not a pre-class one:** `starlette 0.41.3` carries 8 advisories but is pinned transitively by `fastapi==0.115.6`. Patched Starlette requires ≥0.47, which means a FastAPI major upgrade and a full regression pass. Do it deliberately, not the week of a class.

Frontend `npm audit`: 4 vulnerabilities (1 moderate, 3 high) in `postcss` and `sharp`, both build/image-pipeline dependencies rather than request-path code. The fix requires `next@16`, again a scheduled upgrade.

**Secrets: clean.** No real credentials in the working tree or in git history — every match was a documented placeholder (`CHANGE_ME`, `user:pass`). `.env` files are correctly gitignored.

---

## 6. Backups — the biggest remaining risk, and it needs you

I checked both services in Railway:

- **Postgres: point-in-time recovery is OFF. No volume backup schedule. Zero backups exist.**
- **Mayen service volume: no backup schedule, no backups.** This volume holds `facilitator_registry.json` — your facilitator accounts.

You lost a database once already this week. Right now there is nothing to restore from if it happens again, and the volume holding your accounts is equally unprotected.

Two actions, both in the Railway UI:

1. **Postgres → Backups → Enable PITR.** Note it triggers one redeploy, so do it before a class, not during.
2. **Both services → Backups → Edit schedule** — set a daily volume backup.

I did not enable these myself: PITR forces a redeploy and both are billable settings on your account, so they are yours to authorise.

---

## 7. What is healthy

Worth stating plainly, because most of the system is in good shape.

- **Authentication is sound.** Anonymous probes from outside the browser: `/api/admin/facilitators` and `/api/admin/leaderboard` both return `401`. `/api/admin/global-settings` is `200` by design — the player cockpit reads it.
- **Player isolation holds.** Player A reading Player B's session: `403`. Duplicate commit for a round: `409`. Password change requires the current password (verified against missing, wrong and empty).
- **Concurrency is safe** once the pool is sized: 20 simultaneous commits, no lost updates, every player correctly advanced.
- **Worker safety is handled.** `scale_preflight` clamps to 1 worker unless Postgres is active, so per-process state can't split-brain. Railway currently runs 1 worker.
- **The SEC-2 guard works.** I confirmed it live — with `DEBUG=false` and no reachable database, the app refuses to start rather than silently serving an empty simulation. That is the guard that was disabled during last week's outage.
- **Storage is durable:** `/data` on a volume, `durable: true`.
- **CI covers** pytest, a real Postgres parity job, and jest.
- **Full game loop works:** 10 rounds, no stalls, final report with archetype.

Two cosmetic items confirmed harmless: `autonomous_agents.py:1043` is unreachable dead code (`return summary` after an unconditional return, AST-confirmed) and `engine.py:314` is a deliberate string forward-reference.

---

## 8. Deployment checklist

1. **Push `e307b36`** (`git push origin main`) and let Railway redeploy.
2. **Enable Postgres PITR + daily volume backups** (§6).
3. **Verify after deploy:**
   ```
   /health  ->  {"database":"postgresql","demo_mode":false,"storage":{"durable":true}}
   ```
4. **Dry run on the real URL:** log in, create a cohort, set max players to 20, generate and join two IDs in separate browsers, commit round 1.
5. **Decide the scoring-weights question** (below).
6. **Resolve the second deployment.** `cso.mastersustainability.org` (project `acceptable-manifestation`) is a separate Muressons instance on its own database running **older code** — none of this week's fixes, including everything in this audit. Confirm which URL students use; if it is that one, it must be redeployed from `main`.

**Still open, your call:** `/api/admin/global-settings` is unauthenticated by design and returns `esg_profile_weights` — the complete ESG scoring rubric, every multiplier and threshold. A student with developer tools can read the marking scheme. Some instructors would call a transparent rubric a feature; it should be a decision rather than an accident.

---

## 9. The pattern worth naming

Every defect here shares one shape: **the code compiled, the tests passed, and the feature was broken or open anyway.**

- `board_vote` had no guard because its *signature* made a guard impossible.
- `/extend` called a function that did not exist in either backend.
- `max_players` was saved and read back correctly by a gate that ignored it.
- The pool deadlock only appears above a concurrency threshold no test crossed.

Unit tests cannot see any of these, which is why each fix ships with a tripwire that asserts the *shape* rather than the behaviour: a signature scan for missing `request` parameters, an arithmetic check on pool size against roster ceiling, a scan for bare `pool.acquire()`, and a pin that `advance_round` is absent from both backends. The pool tripwire is mutation-tested — reintroducing a single bare acquire fails it.

Backend suite: **1614 passing** (was 1546). Postgres parity: **6/6** against a real server.
