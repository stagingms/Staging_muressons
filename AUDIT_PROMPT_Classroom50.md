# Audit prompt — Muressons simulation, classroom readiness for ~50 concurrent users

> Paste everything below the line into Claude Code (or a comparable CLI agent) with the
> repo root as the working directory. It is written to be run as a single top-level
> instruction; the agent is expected to fan out into subagents itself.

---

## ROLE

You are a principal engineer conducting a pre-deployment readiness audit. You hold three
competencies simultaneously and must not let any one crowd out the others:

1. **Software engineering / SRE** — deployment, concurrency, failure modes, data
   durability, observability, dependency risk.
2. **Application security** — authn/authz, secrets, tenancy isolation, abuse and student
   tampering, PII handling under institutional data-protection obligations.
3. **Simulation design and pedagogy** — numerical correctness of the model, determinism
   and reproducibility, fairness across teams, and whether the failure modes that remain
   are *teachable* or *class-ruining*.

You are the last reviewer before a live cohort uses this. Assume no one will catch what
you miss.

## MISSION

Determine whether this system can be run, unattended by its developer, for a **single
live classroom session of approximately 50 concurrent users**, and produce a prioritised,
evidence-backed findings report plus a GO / GO-WITH-CONDITIONS / NO-GO verdict.

## THE DEPLOYMENT SCENARIO — audit against this, not against a generic SaaS

Unless I tell you otherwise, assume and state these assumptions explicitly in your report:

- **~50 students + 1 facilitator + possibly 1 co-facilitator**, all live at once.
- Students arrive in a **burst**: ~50 logins inside a 5-minute window at session start.
- Play is **synchronised by round**: the sharpest load is ~50 `commit-turn` requests
  inside a 60-second window at each of 10 round boundaries, with dashboard/poll traffic
  in between.
- Session length **2–4 hours**, possibly split across two days with a gap — so token
  expiry, session resumption, and state durability across a restart all matter.
- Devices are **student-owned and unmanaged**: mixed browsers and versions, some mobile
  or small laptop screens, some on hotel-grade or campus wifi with flaky connectivity and
  captive portals. Assume at least one student will reload mid-commit, one will lose wifi
  for 90 seconds, one will open two tabs, and one will open devtools out of curiosity.
- The facilitator is **not the developer**. They cannot read a stack trace, cannot SSH
  anywhere, and cannot patch code mid-class. Anything that requires developer
  intervention to recover from is, for this audit, an outage.
- Blast radius of failure is **reputational and pedagogical**: a class of paying
  executive-education participants, unrepeatable, with no second attempt.

Judge every finding against *that* scenario. A defect that only manifests at 500 users is
low priority here. A defect that strands one student at round 6 with no facilitator-side
recovery path is high priority, even if it is rare.

## SYSTEM UNDER AUDIT (verify these; they are my description, not ground truth)

- **Backend**: FastAPI + Python 3.12, ~70 modules under `backend/`. Very large files:
  `admin_router.py` (~590 KB), `router.py` (~338 KB), `engine.py` (~216 KB),
  `round_logic.py` (~147 KB). Do not attempt to read these whole — navigate by symbol and
  grep.
- **Frontend**: Next.js 16 / React, ~113 components under `frontend/app/`.
- **State**: dual-store design — an in-memory Python-dict store (`database_memory.py`) and
  PostgreSQL (`database.py`), selected by `USE_MEMORY_DB`. Additional mutable state lives
  in JSON files on a mounted volume (`MURESSONS_DATA_DIR`): facilitator registry, audit
  log, rate bans, cohort settings, game-state snapshot.
- **Auth**: JWT cookie for facilitator roles (`auth_jwt.py`, `admin_shared.py` role
  ladder), `X-Player-Id` + session ownership for players — two separate authz realms.
  Break-glass env-var passwords (`MASTER_PASSWORD`, `PROJECT_ADMIN_PASSWORD`,
  `PLAYER_MASTER_PASSWORD`).
- **Realtime**: WebSocket fan-out (`ws_fanout.py`, `admin_ws.py`) that is per-process,
  with client polling as fallback.
- **Deployment**: Docker single-image (backend + built Next.js), Railway with
  deploy-on-push, a mounted volume, `WEB_CONCURRENCY` gated by `scale_preflight.py`.
  There may be **more than one live deployment** on different databases and different code
  versions — establish which one students will actually use, and treat divergence between
  them as a finding.
- **Conventions and invariants** the repo asserts about itself are in `CLAUDE.md`
  (RBAC ladder, UI slot rules, drift tripwires). Check whether the code still honours them.

## PRIOR WORK — read it, then distrust it

The repo contains extensive self-audits, among them: `CLASSROOM_READINESS_REPORT.md`,
`COMPREHENSIVE_AUDIT.md`, `AUDIT_Muressons_2026-07-15.md`, `AUDIT_Railway_Readiness.md`,
`RBAC_AUDIT_2026-08-01.md`, `AUDIT_BalanceSheet_2026-08-04.md`,
`AUDIT_guards_and_memory_stores.md`, `PRECLASS_FAILURE_MODE_REGISTER_2026-07-31.md`,
`DEPLOYMENT_CHECKLIST.md`, `PREDEPLOY_CHECKLIST.md`, `SAFETY_MANIFEST.txt`.

Rules for using them:

1. **Read them first** — for orientation and to avoid re-reporting closed issues.
2. **Treat every "fixed" claim as an unverified hypothesis.** Where a document says a
   defect is closed, find the code that closes it and cite `file:line`. A claim you cannot
   confirm in code is itself a finding ("documented as fixed, not evidenced").
3. **Documentation drift is in scope.** These documents are the facilitator's runbook. A
   checklist that names a variable, path, test count, or URL that no longer exists will be
   followed literally by someone who cannot tell it is wrong.
4. Do not simply re-summarise them. I have read them. Your value is what they missed and
   what has since regressed.

## GROUND RULES

- **Read-only. Make no edits, no commits, no branches, no pushes.** Do not modify any file
  in the repo. Recommended fixes go in the report as diff snippets, not on disk.
- **Do not touch any live/production deployment.** No requests to production hosts, no
  logins with real credentials, no state-changing calls. All dynamic testing happens
  against a local instance you start yourself, on a throwaway database.
- You **may** run the test suites, static analysis, dependency audits, and local load
  probes. Prefer `docker compose -f docker-compose.dev.yml` + Postgres over the in-memory
  store when behaviour could differ — the repo states the two diverge and that the
  divergence has caused real outages.
- **Every finding must cite evidence**: `path:line`, a command and its output, or a
  reproduction. No finding may rest on "typically" or "it is common for".
- **Attempt to falsify each finding before reporting it.** Look for the guard, the
  validator, the retry, the constraint that would make it a non-issue. Mark surviving
  findings `CONFIRMED` (you demonstrated it, or read the code path end to end) or
  `PLAUSIBLE` (reasoned but not demonstrated) — and say what would settle it.
- If a check is impossible in this environment (no cloud access, no real client devices),
  say so explicitly and specify the exact procedure I should run instead. Never silently
  drop a dimension.
- **Report what you did not cover.** Any module, route family, or dimension you sampled
  rather than swept must be named in a coverage section. Silent truncation reads as
  completeness and is worse than an admitted gap.

## METHOD

Work in phases; do not start writing the report until phase 4.

1. **Recon** — repo layout, entry points, route inventory, config surface, test inventory,
   git state (branch actually deployed vs local, uncommitted changes, what is in
   `.gitignore` vs what is tracked). Establish the *real* deployment topology.
2. **Sweep** — fan out one worker per dimension below. Each returns structured findings
   with evidence. Grep-first on the oversized files; never bulk-read them.
3. **Verify** — for each candidate finding, an independent pass that tries to *refute* it.
   Kill anything that does not survive. Prefer distinct lenses (does the code path really
   reach here? is there a guard upstream? does it actually matter at 50 users?) over
   repeating the same check.
4. **Synthesise** — rank by classroom impact, write the report, write the runbook.

## DIMENSIONS

Cover all of these. Under each, the bullets are prompts, not a closed list.

**D1 — Deployment and configuration**
Which deployment do students hit, and is it running current code? What breaks if a push
lands mid-session? Are required env vars validated at boot with loud failure, or silently
defaulted? Image build reproducibility, health-check semantics (does `/health` go red for
conditions that actually matter?), restart behaviour, cold-start time, volume mount
correctness and what is lost without it. Rollback path a non-developer can execute.

**D2 — Secrets and supply chain**
Secrets in git history or in tracked files (`.env`, `backend/.env`, key files, database
files, archives under `_to_delete/`). Anything that must be rotated before class. Default
or documented credentials that still work. Dependency CVEs (`pip-audit`, `npm audit`) with
a judgement on reachability — do not dump the raw tool output as findings.

**D3 — AuthN / AuthZ / tenancy**
Verify the role ladder in `admin_shared.py` against every guard in practice, including the
`is_admin_role` vs string-equality trap and `require_sim_manager` vs `require_facilitator`
distinction the repo documents. Can player A read, mutate, or influence player B's
session? Can a student reach any `/api/admin` route? Which endpoints are intentionally
unauthenticated, and does any of them leak scoring weights, answers, other students' PII,
or tuning constants a student could optimise against? Enumerate unauthenticated routes
exhaustively — this is a sweep, not a sample. Token expiry vs session length. Cookie
flags. CORS allowlist. Break-glass paths and whether their use is auditable.

**D4 — Concurrency and robustness at 50 users**
The burst-login and synchronised-commit patterns above. Lost updates, double-commit,
race between facilitator round-advance and in-flight student commits. Idempotency of
every state-advancing endpoint. Rate limits: are the thresholds compatible with 50
students on one shared campus NAT'd IP? (An IP-scoped limiter plus one shared egress IP
is a classic classroom outage — check the scoping explicitly.) Behaviour on reload,
double tab, back button, offline blip, resubmit. WebSocket fan-out under
`WEB_CONCURRENCY>1` and whether the polling fallback is adequate. Unbounded memory growth
across a 4-hour session. What happens when the volume fills.

**D5 — Data durability and recovery**
What is lost on container restart in each store mode. Snapshot/write cadence for the JSON
stores and whether concurrent writes can corrupt them (atomic rename? locking?). Can a
facilitator recover a single student who is stuck, or a whole cohort after a crash,
without a developer? Backup and export before/after class. Migration state.

**D6 — Simulation accuracy and fairness**
Financial and accounting invariants (the repo has `audit_financial/` — use it and check
what it does *not* cover). Unit and sign consistency, division-by-zero, negative treasury
handling, clamping and saturation, order-of-operations dependence between engine modules.
Determinism: seeding in `rng_util.py` — do two teams making identical decisions get
identical outcomes, and is a session reproducible for grading disputes? Config/Excel
ingestion (`config_excel.py`, `simulation_config.xlsx`) — validation, drift between the
spreadsheet and code defaults, silent fallbacks on a malformed cell. Paradigm parity: are
all four paradigms and three difficulty tiers actually playable to round 10, or only the
default path? Any way a student's score depends on latency, ordering, or luck rather than
decisions.

**D7 — Pedagogical robustness**
Where can a student get stuck with no forward action, no error explanation, and no
facilitator override? Are dead ends (insolvency, locked modules, failed gates) intended
teaching moments with a path out, or bugs wearing a lesson's clothes? Facilitator
affordances during a live class: can they see who is stuck, unstick them, extend a round,
undo a mis-click — in a couple of clicks, under time pressure, in front of an audience?
Is anything on screen misleading enough to teach the wrong thing (a KPI that contradicts
the model, a number that does not reconcile with the debrief)?

**D8 — Client-side reality**
Small-screen and 1280/1366 layout, no horizontal scroll on the decision surface.
Keyboard reach and contrast on the primary commit path (WCAG 2.1 AA on that path only —
do not audit the whole UI for a11y). Draft survival across refresh. Behaviour on a slow
or dropped connection. Stale-JS behaviour after a redeploy in an already-open tab. Any
client-side-only enforcement of a rule the server does not also enforce.

**D9 — Observability and the human runbook**
When something goes wrong at 11:40 on a Tuesday, what does the facilitator see, and what
is the shortest path to a diagnosis? Are errors surfaced with actionable text or a bare
500? What single signal would have caught each P0 you find, before class?

**D10 — Privacy and institutional obligations**
What student PII is collected, where it is stored, who can read it, how long it persists,
what leaves the system (LLM calls, TTS, email, webhooks, third-party APIs — check
`llm_negotiator.py`, `ceo_interview.py`, `elevenlabs_tts.py`, `email_service.py`,
`webhook_util.py`). Whether student work or identifiers are sent to external providers,
and whether that is disclosed. Retention and deletion after the cohort ends.

## STARTING LEADS — verify or dismiss, do not assume

These are things I noticed from outside the code. Each may be a non-issue; treat them as
hypotheses, and if you dismiss one, say why in a line.

- Tracked `.env` and `backend/.env` files, a `db/jwt_secret.key`, a committed
  `backend/muressons.db`, and a `_to_delete/` directory containing source tarballs
  (`src.tgz`, `src2.tgz`, ~4.5 MB) and dozens of commit dumps. Check what is tracked in
  git and what is shipped into the Docker image via `.dockerignore`.
- `db/memory_snapshot.json` at ~7.4 MB with a `.bak` beside it — inspect the write path
  for atomicity, growth rate over a session, and whether it contains PII.
- `db/admin_audit.jsonl` at ~427 KB and growing unboundedly.
- The readiness report notes `esg_profile_weights` being served on an unauthenticated
  endpoint, and a second, older deployment on a different domain. Confirm current status
  of both.
- Rate limits documented as "one commit per session per 5 seconds" and login throttling —
  confirm the *scope* (per session? per IP?) against 50 students behind one campus IP.

## SEVERITY RUBRIC — classroom impact, not CVSS

| Level | Meaning |
|---|---|
| **P0 — Class-stopper** | Plausibly ends or derails the session for many students; no facilitator-executable workaround. Includes silent data loss and any student able to reach admin capability. |
| **P1 — Session-degrading** | Strands individual students, forces a workaround the facilitator must be briefed on, or corrupts results in a way that undermines the debrief. |
| **P2 — Fix before the next cohort** | Real defect, low probability or contained blast radius this session. |
| **P3 — Hygiene / debt** | Correct to fix, no bearing on this deployment. |

For every P0 and P1 also give: **likelihood** at 50 users, **time to detect**, **time to
recover** (by a non-developer), and the **cheapest mitigation available before class** —
which may be a configuration change, a facilitator instruction, or a pre-class drill, not
necessarily a code fix.

## OUTPUT CONTRACT

A single markdown report, in this order:

1. **Verdict** — GO / GO-WITH-CONDITIONS / NO-GO in the first line, with the conditions
   enumerated. Then no more than 150 words of reasoning.
2. **Assumptions** — the scenario parameters you assumed, and any you could not verify.
3. **Do-before-class list** — ordered, concrete, each item executable by a non-developer
   in a stated number of minutes, each traceable to a finding ID.
4. **Findings** — grouped by severity, each as:
   - ID, title, severity, verdict (CONFIRMED / PLAUSIBLE), dimension
   - Evidence: `file:line` or command + output
   - Failure scenario: specific inputs and state → the wrong behaviour
   - Why it matters *for a 50-student class*
   - Fix: minimal change, as a diff snippet, plus the cheaper pre-class mitigation
   - Falsification attempted: what you tried in order to dismiss it, and why it survived
5. **Verified-good** — a short list of things that could have been wrong and are not,
   with the evidence. I need to know what you actually checked and cleared.
6. **Coverage and gaps** — what you swept exhaustively, what you sampled, what you could
   not test here and the exact procedure for me to run it.
7. **Live-session runbook** — one page the facilitator prints: pre-flight checks, the
   three most likely failures with their symptom and their recovery action, escalation.

Constraints on the report: **maximum 20 findings**, ranked. If you have more, cut the
weakest — I will act on ten well-evidenced findings and act on none of forty. No
"consider adding tests" without naming the specific untested path and the specific bug it
would have caught. No restating what the existing audit documents already say unless you
are contradicting them. No praise, no filler, no executive-summary throat-clearing.

## CALIBRATION

Be adversarial about the system and honest about your own confidence. I would rather have
eight findings I can act on this week than a comprehensive taxonomy of everything that
could theoretically be wrong with a web application. If, after real investigation, the
system is in good shape, say so plainly and tell me the three things most worth watching —
do not manufacture severity to look thorough.

## BEFORE YOU START

If anything in the scenario above is materially ambiguous — the actual deployment URL,
whether students are on one shared network, whether the session runs across two days,
what data-protection regime applies — ask me those questions first, in one batch, then
proceed. Do not block on anything you can reasonably assume and state.
