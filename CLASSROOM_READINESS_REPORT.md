# Muressons — Classroom Readiness Report

**Date:** 29 July 2026
**Commit audited:** `2591121` (local working tree byte-identical to `origin/main`)
**Deployment audited:** `mayen-production.up.railway.app` (project `perceptive-enchantment`)

**Verdict: GO for classroom use, with three items to action first — none of them blocking a session that starts today.**

---

## 1. What was tested

Four independent layers, because passing tests and working in a classroom are different claims:

| Layer | Method | Result |
|---|---|---|
| Backend logic | Full pytest suite, memory store | **1546 pass**, 1 environment-only failure |
| Storage parity | Parity suite against a real PostgreSQL server | **6/6 pass** |
| Whole-game flow | Scripted class: facilitator, 3 players, rounds 1→10, final report | **Completed end to end** |
| Live production | HTTP probes against the running Railway service | Healthy, correctly authenticated |

The single failing test, `test_off_railway_repo_dir_is_durable`, needs a writable `db/` directory. The audit sandbox mounts it read-only (files can be created but not unlinked), so the durability probe fails there. Verified passing on a writable copy — it will be green on your machine and in CI.

---

## 2. The end-to-end classroom drill

This is the check that matters most, because it is the only one shaped like a real session. A facilitator was created, a cohort opened, three player IDs generated and joined, and one player driven through all ten rounds.

Everything held:

- Three players joining produced three **distinct sub-sessions** — no ID collision.
- Round config loaded for every round 1 through 10.
- The Round 1 stakeholder map and Round 2 CSRD materiality matrix both submitted.
- **Submitting the materiality matrix twice was a clean no-op.** This is the exact path that used to return HTTP 500 and trap players in a loop through the CFO override modal. It is fixed and stays fixed.
- Mid-round save worked in every round — a student can save and come back.
- Commit advanced the round correctly every time, 1→2→…→10. **No stalls.**
- The final report rendered with a terminal archetype.

Concurrency was tested separately, since a real class commits together:

- **Five simultaneous commits: all five accepted**, no lost updates.
- Player A reading Player B's session: **403**. Isolation holds.
- Duplicate commit for the same round: **409**. Correctly rejected.

The 10-round arc drove treasury to roughly **−$25M to −$95M** across runs. That is the engine responding to a deliberately naive strategy (identical mid-level spend every round, never adapting), not a defect — but it does mean insolvency is reachable, so expect some teams to end there and be ready to teach into it.

---

## 3. A security finding I raised and then disproved

Worth recording because the reasoning generalises.

Probing production, `/api/admin/facilitators` returned **200 with the full facilitator registry** — names, your email address, roles, permissions — apparently without authentication. I had set `credentials: 'omit'`. That looked like a serious PII leak.

It was not. `frontend/app/layout.js` installs a `window.fetch` interceptor that **forces `credentials: 'include'` on every URL containing `/api/admin`**, silently overwriting my flag. The browser was sending your real HttpOnly session cookie. A follow-up attempt using `XMLHttpRequest` with `withCredentials = false` was equally invalid — that flag only affects cross-origin requests; same-origin XHR always sends cookies.

The decisive test was a request from outside the browser entirely, with no cookie jar:

| Endpoint | Anonymous result |
|---|---|
| `/api/admin/facilitators` | **blocked (401)** |
| `/api/admin/leaderboard` | **blocked (401)** |
| `/api/admin/global-settings` | 200 — intentionally public, the player cockpit reads it |

This matches local behaviour exactly. **Authentication is working correctly.** The lesson: a browser is not a neutral instrument for testing authentication. Any probe run inside a page inherits that page's cookies and any client-side interception.

---

## 4. Findings to action

### 4.1 Scoring weights are publicly readable — pedagogical, not security

`/api/admin/global-settings` is unauthenticated by design, because the player cockpit needs it. It also returns `esg_profile_weights` — the complete ESG scoring rubric: which levers carry which multipliers, the exact thresholds for `climate_leader`, `truth_premium`, `just_transition` and the rest.

A curious student who opens developer tools can read the marking scheme and optimise directly against it. Whether that matters is your call — some instructors would consider a transparent rubric a feature. But it should be a decision, not an accident. If you want it hidden, the fix is to strip `esg_profile_weights` (and the other server-side tuning constants) from the unauthenticated response and serve them only to authenticated facilitators.

### 4.2 No HSTS header

Responses carry `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` and a well-formed Content-Security-Policy, but **no `Strict-Transport-Security`**. Railway terminates TLS and redirects, so exposure is small, but adding HSTS to the `headers()` block in `next.config.mjs` is a one-line hardening.

### 4.3 Two dead-code artefacts (cosmetic — verified harmless)

Static analysis flagged two undefined names in production modules. I checked both; **neither can execute**:

- `autonomous_agents.py:1043` — `return summary` sits after an unconditional `return` and is unreachable (AST-confirmed). Delete it.
- `engine.py:314` — `payload: "DataBridgeOutput"` is a deliberate string forward-reference, imported at line 346, already marked `# noqa: F821`. Correct as written.

Both are noise. They matter only because they make the linter's output less trustworthy — the peer-trends outage earlier this week was a genuine undefined name hiding in exactly this kind of output. Clearing the two known-benign ones keeps the signal clean.

---

## 5. Production configuration

Live `/health`:

```json
{"status":"ok","database":"postgresql","demo_mode":false,
 "storage":{"data_dir":"/data","configured":true,"writable":true,
            "on_railway":true,"durable":true}}
```

- **PostgreSQL, durable volume, demo mode off** — correct.
- `ALLOW_MEMORY_DB_IN_PROD` has been removed. If the database becomes unreachable the service will now **refuse to start** rather than silently serving an empty simulation. That failure mode caused this week's outage; it cannot recur silently.
- Your **facilitator accounts survived** on the volume: `FAC-001` (Jose PD, super_admin), `FAC-002` (lead_facilitator), plus `FAC-EMERGENCY`. Passwords are masked in all API responses.
- Repeated bad logins returned 403 consistently — the limiter is engaged.

**One caveat: the Postgres database is new and empty.** Cohorts and runs from the previous database were lost when it was deleted. Facilitators survived only because they live in a JSON file on the volume, not in Postgres.

---

## 6. Before the session — a short runbook

1. **Do a dry run on the real URL**, not just locally: log in, create a throwaway cohort, generate two player IDs, join both in separate browsers, and commit Round 1. Ten minutes. It exercises login, provisioning, join and commit — the four things that ruin a class if they break.
2. **Decide on the scoring-weights question** (§4.1) before students have devtools open in a live session.
3. **Have the `FAC-EMERGENCY` credentials to hand** but do not use them routinely; the password prints once at startup in the deploy logs.
4. **Know the two rate limits**, because they look like bugs from the front of a room: commits are limited to **one per session per 5 seconds**, and login attempts are throttled after repeated failures. A student mashing Commit will see "Rate limited. Wait 5 seconds" — that is correct behaviour, not a fault.
5. **Expect insolvency.** Teams that spend a flat amount every round without adapting will finish deep in negative treasury. The engine is working; it is a teaching moment.
6. **Resolve the second deployment.** `cso.mastersustainability.org` (project `acceptable-manifestation`) is a separate Muressons instance on its own database, running **older code** — its `/health` returns the pre-`demo_mode` response shape, so none of this week's fixes are in it. Confirm which URL students will actually use. If it is that one, it needs redeploying from `main` before class.

---

## 7. Bottom line

The simulation is **stable enough to run a class on**. The round engine completes ten rounds without stalling, concurrent commits are safe, player sessions are isolated, the duplicate-materiality trap is closed, storage is durable, and authentication is sound.

The genuine risks are not in the code. They are: pointing students at the wrong deployment (§6.6), and an empty database that will not contain any cohort you set up on the old one (§5).
