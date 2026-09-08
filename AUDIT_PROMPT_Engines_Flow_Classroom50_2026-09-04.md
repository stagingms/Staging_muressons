# Audit prompt — Muressons: engine correctness, play flow, and classroom-50 readiness

> **How to use this.** Start a fresh Cowork session on the device `jmj-home` with the folder
> `C:\Users\Home\.gemini\antigravity\scratch\muressons-sim` connected, and paste everything
> below the line as a single top-level instruction. It supersedes
> `AUDIT_PROMPT_Classroom50.md` (2026-08-13), which was written for a Claude Code CLI run and
> weighted toward deployment and security. This one is weighted toward the **mathematical
> engines** and the **lived flow of a session**, with classroom readiness as the verdict.

---

## ROLE

You are the last reviewer before a live executive-education cohort uses this system. You hold
four competencies at once and must not let any one crowd out the others:

1. **Simulation and systems modelling** — numerical correctness, conservation, determinism,
   sensitivity, whether a model's behaviour is defensible as a representation of the world.
2. **Systems architecture** — module boundaries, data flow, order-of-operations coupling,
   single-source-of-truth violations, config precedence.
3. **Software engineering / SRE** — concurrency, failure modes, durability, recovery by a
   non-developer.
4. **Pedagogy and facilitation** — whether what the model computes is *teachable*, whether the
   numbers a participant sees support the debrief you intend to run, and whether a facilitator
   can operate the room without the developer.

You are not here to be reassuring. You are here to be right.

## MISSION

Answer three questions, in this order of weight, and produce one evidence-backed report.

**Q1 — Are the mathematical engines correct and defensible?**
Two distinct standards, and you must judge both separately for each engine you examine:
- **Accuracy** — does the code compute what it claims to compute? Conservation, units, signs,
  clamps, division guards, ordering, determinism, single arbiter per quantity, config actually
  reaching the formula.
- **Relevance** — is the thing it computes a defensible model of the phenomenon it names, at
  magnitudes a participant with domain knowledge would not laugh at, with levers that move in
  the direction and roughly the proportion the real world moves? An engine can be arithmetically
  perfect and pedagogically indefensible. Say so when it is.

**Q2 — Does the simulation flow hold up, played end to end, from both seats?**
Trace a full session as a **participant** and, separately, as a **facilitator**. Not a feature
inventory — a narrated walkthrough of what is on screen, what is decidable, what is confusing,
what is unrecoverable.

**Q3 — Is this classroom-ready for a cohort of 50?**
GO / GO-WITH-CONDITIONS / NO-GO, with the conditions enumerated and each one executable by a
non-developer in a stated number of minutes.

## OPERATING ENVIRONMENT — read this before you plan anything

You are running in Cowork, reaching the repo through the device bridge, **not** in a terminal at
the repo root. Plan around these facts; do not discover them the hard way.

- The repo is mounted at `$HOME/mnt/muressons-sim` for `device_bash`. Do all work there with
  `device_bash`. Do **not** stage source files into the container to read or edit them.
- **Each `device_bash` call is a fresh shell with roughly a 45-second budget.** No `cd` or env
  carryover between calls. Long sweeps must be split, or written as a script that a later call
  runs in the background with output to a file you then read. Anchor every path at `$HOME`.
- Keep scratch **outside** `mnt/` — use `$HOME/audit_scratch/`. Anything you write inside
  `mnt/muressons-sim` lands in the owner's working tree. Do not do that except for the final
  report, and only where the owner told you to put it.
- Verified working on this device as of 2026-09-04: `python3` is **3.10.12** (the repo targets
  3.12 — treat any 3.12-only syntax error as an environment artifact, not a finding), `node`
  v22, `pip3 install` and `npm` reach the network, and — importantly — `backend/config.py` and
  `backend/engine.py` **import cleanly from `backend/` with no extra dependencies**. Executable
  verification of engine math is therefore available to you. Use it.
- Assume Docker is **not** available. If a check genuinely needs it, say so and specify the exact
  command for the owner to run instead.
- **Read-only on the repo.** No edits, no commits, no branch changes, no `git checkout`. Fixes go
  in the report as diff snippets. Do not touch any live Railway deployment: no requests to
  production hosts, no logins, no state-changing calls.

## THE SCENARIO — audit against this, not a generic SaaS

State these assumptions explicitly at the top of your report, and flag any you could not verify.

- **~50 participants + 1 facilitator** (possibly a co-facilitator), all live at once. Executive
  education: paying, senior, unforgiving of a broken number, and there is no second attempt.
- Arrival is a **burst** — ~50 logins inside five minutes. Play is **round-synchronised** — ~50
  commits inside a 60-second window at each of ten round boundaries.
- Session length **2–4 hours**, possibly split across two days, so token expiry, resume, and
  durability across a restart matter.
- Devices are participant-owned and unmanaged; assume one reloads mid-commit, one drops wifi for
  90 seconds, one opens two tabs, one is on a 1366-wide laptop, and 50 of them may share one
  campus egress IP.
- The facilitator **is not the developer**: cannot read a stack trace, cannot SSH, cannot patch
  mid-class. Anything needing developer intervention is, for this audit, an outage.

A defect that only appears at 500 users is low priority. A wrong number on the debrief slide, or
one participant stranded at round 6 with no facilitator-side recovery, is high priority.

## SYSTEM UNDER AUDIT — my description, not ground truth; verify each claim

- **Backend**: FastAPI + Python, ~100 modules under `backend/`. Oversized files you must
  **navigate by symbol and grep, never bulk-read**: `admin_router.py` (~13k lines),
  `router.py` (~7.6k), `engine.py` (~4.8k), `round_logic.py` (~3.4k), `database.py` (~2.1k),
  `admin_shared.py` (~2.0k), `pillar_configs.py` (~1.8k), `database_memory.py` (~1.7k).
- **Model surface** (the primary object of Q1) includes at least: `engine.py`, `round_logic.py`,
  `balance_sheet.py`, `terminal_valuation.py`, `pillar_configs.py`, `impact_engine.py`,
  `market_dynamics.py`, `systemic_risk_engine.py`, `black_swan_registry.py`,
  `biodiversity_engine.py`, `sdg_linkage_engine.py`, `meadows_leverage.py`,
  `turnaround_engine.py`, `ending_pathways.py`, `branching_engine.py`, `stakeholder_sentiment.py`,
  `npc_stakeholders.py`, `org_politics.py`, `autonomous_agents.py`, `pedagogical_engine.py`,
  `consequence_dna_api.py`, `validation_logic.py`, `rng_util.py`. **Enumerate the real list
  yourself** — do not treat mine as complete, and say in your coverage section which of them you
  swept, which you sampled, and which you never opened.
- **Config chain**: `backend/config.py` defaults → `simulation_config.json` in the repo →
  a **separate copy on the mounted data volume** (`MURESSONS_DATA_DIR`) → `simulation_config.xlsx`
  via `config_excel.py`, plus `simulation_config.provenance.json`. The precedence order, and what
  happens when the volume copy is stale or a cell is malformed, is itself an audit target — the
  repo's own commit log shows a stale volume copy silently overriding a code default.
- **State**: dual-store — in-memory dict (`database_memory.py`) and PostgreSQL (`database.py`),
  selected by `USE_MEMORY_DB`, plus JSON files on the volume. The repo asserts the two stores have
  diverged before.
- **Frontend**: Next.js / React under `frontend/app/`.
- **Deployment**: Docker single image, Railway deploy-on-push. As of this writing the working tree
  is on `fix/launch-readiness-20260903` with untracked audit files, and the repo's own launch
  report says `production` sits several commits behind `main`. **Establish which code the cohort
  will actually run**, and treat any divergence between what you audit and what ships as a P0
  finding in its own right.
- **Existing harnesses you should use rather than reinvent**: `backend/tests/` (~164 test files,
  including `test_engine_invariants.py`, `test_financial_golden_trace.py`, `test_caroic.py`,
  `test_calibration_scoring.py`, `test_concurrent_commit_race.py`, `test_extended_horizon.py`,
  and `backend/tests/golden/`), `audit_financial/` (`financial_invariants.py`, `recon.py`,
  `re_bridge.py`, `edges.py`, `run_trace.py`), and `scripts/` (`monte_carlo_stress_test.py`,
  `balance_report.py`, `harness/`). For each harness you rely on, state what it covers **and what
  it does not** — an invariant suite that passes tells you only about the invariants it encodes.

## PRIOR WORK — read it, then distrust it

The repo carries extensive self-audits. At minimum skim: `AUDIT_ENGINES_DEEP_2026-08-31.md`,
`AUDIT_Independent_Review_2026-09-01.md`, `AUDIT_Independent_BugHunt_2026-09-03.md`,
`REPORT_launch_readiness_2026-09-03.md`, `AUDIT_BalanceSheet_2026-08-04.md`,
`AUDIT_Classroom50_Readiness_2026-08-13.md`, `CALIBRATION_DIAGNOSIS_2026-09-01.md`,
`DELTA_combined_rebaseline_2026-09-03.md`, `MODEL_CARD.md`, `BALANCE_REPORT_BASELINE.md`,
`SIMULATION_CONTEXT.md`, `CLAUDE.md`, `blueprint.md`.

Rules for using them:

1. **Read first, for orientation and to avoid re-reporting closed issues.**
2. **Every "fixed" claim is an unverified hypothesis** until you find the code that closes it and
   quote it with `file:line`. A fix claimed and not evidenced is itself a finding.
3. **Every number in them is stale until you recompute it.** Do not quote a prior audit's figure
   as your own result. If you cite one, label it as *their* claim and say whether you reproduced it.
4. **Documentation drift is in scope.** These files are the facilitator's runbook. A checklist
   naming an env var, path, threshold, or URL that no longer exists will be followed literally by
   someone who cannot tell it is wrong.
5. Do not re-summarise them. The owner has read them. Your value is what they missed, what has
   since regressed, and what they asserted without evidence.

**Named open leads from the repo's own last engine audit — determine, on the code that will ship,
whether each is still open, and cite the code either way:**

- The R6 EU AI Act deferred charge registered only at `_POST_TICK_MAP[6]`, so the R7+ consequence
  shown to the player in words can never fire.
- **Two arbiters for M_R** — an inline award in `_post_r10_grand_finale` versus
  `terminal_valuation.calculate_mr` used for mid-game projection — diverging on synergy gating,
  cliffs vs ramps, and clamping (the inline path reportedly having no floor or ceiling).
- A money-conservation gap reported at up to ~$656M per run.
- A large share of declared flags reported inert — set somewhere, consumed nowhere.
- High-stakes stochastic draws reported to bypass the facilitator's fairness seed.
- Transient OPEX surcharges that leaked permanently, and a published M_R ceiling that was
  unreachable — both claimed fixed in early September. Verify.
- The natural-decay recalibration that was applied, partly reverted, then rebaselined across three
  commits on 2026-09-03. Determine what the shipped values now are, whether the golden traces were
  rebaselined against them, and whether the documentation still describes the reverted version.

## EVIDENCE STANDARD — this is the part I care most about

The instruction "do not hallucinate, check every recommendation twice" is operationalised as
follows. A finding that does not meet this bar must be cut, not softened.

**1. Every factual claim carries evidence inline.** Either `path:line` **with the line quoted**,
or a command and its actual output. You may not cite a line number you have not read. You may not
name a file, function, symbol, config key, or env var that you have not confirmed exists — every
identifier in your report must be greppable in the tree.

**2. Two passes, and they must use different methods.** For each finding, one pass discovers it
and a second, methodologically distinct pass re-derives it:

| Pass A (any one) | Pass B must be a *different* row |
|---|---|
| Static read of the code path end to end, from HTTP entry point to state write |
| Executable probe — import the module in a throwaway script under `$HOME/audit_scratch/` and observe the real value |
| Independent approach from a different entry point (the caller, the test, the config, the UI surface) |
| Check against an existing harness — golden trace, invariant suite, monte-carlo script |

Re-reading the same code twice is one pass, not two. Say which two you used. Where the engine
imports cleanly (it does), an executable probe is strongly preferred as one of them — a printed
number beats a confident reading.

**3. Falsify before you report.** For each candidate finding, actively hunt the guard, clamp,
validator, retry, or upstream caller that would make it a non-issue. Report only what survives.
Mark each **CONFIRMED** (demonstrated, or the path read end to end) or **PLAUSIBLE** (reasoned,
not demonstrated) — and for PLAUSIBLE, state the single check that would settle it.

**4. Never infer an output you did not observe.** If a probe will not run, or a check is
impossible here, write "not verified" and give the exact command for the owner to run. A gap you
name is fine; a gap you paper over is a defect in the audit.

**5. Words that mean you have not finished.** If you write *likely*, *presumably*, *should*,
*typically*, *appears to*, or *it is common for* — stop and go check. If after checking it is
still uncertain, say exactly what is uncertain and why.

**6. Separate what the code does from what the docs say it does.** Where they disagree, that
disagreement is a finding, and the code wins.

**7. Keep a claims ledger.** For every claim you carry over from a prior audit or a doc, record:
the claim, its source, whether you reproduced it, and the evidence. Include the ledger in an
appendix. Claims you could not reproduce are the most interesting rows in the report.

## METHOD — work in phases; do not draft the report before phase 5

1. **Recon** — repo layout, git state (which branch ships, what diverges), module and route
   inventory, config chain and its precedence, test and harness inventory, which stores are in
   play. Establish the real topology before forming any hypothesis.
2. **Model map** — for the model surface, produce a one-line-per-engine map: what quantity it
   owns, who calls it, what it reads from config, what it writes to state, and which round(s) it
   fires in. This map is what makes ordering bugs and duplicate arbiters visible; it is also a
   deliverable (appendix).
3. **Engine sweep** — Q1. Fan out subagents by engine cluster, each returning structured findings
   with evidence. Grep-first on the oversized files.
4. **Flow walkthroughs and classroom sweep** — Q2 and Q3.
5. **Verify** — an independent pass per surviving finding that tries to *refute* it (see the
   evidence standard). Kill what does not survive.
6. **Synthesise** — rank by classroom and pedagogical impact; write the report and the runbook.

Prefer several small, precisely scoped subagents over one broad one, and give each the evidence
standard verbatim — an unbriefed subagent will hand you exactly the confident prose this prompt
exists to prevent.

## DIMENSION E — the mathematical engines (primary)

**E1 — Conservation and closure.** Does money reconcile end to end for a full ten-round run, in
every paradigm and difficulty tier the config actually ships (count them; do not assume four)?
Balance sheet identity, retained-earnings bridge, cash bridge, and the treatment of transient vs
permanent effects. Quantify any gap in currency units per run and say whether it ratchets. Use
`audit_financial/` and state what it does **not** cover.

**E2 — Single arbiter per quantity.** For each headline number a participant sees — terminal
valuation / M_R, scores, pillar levels, stakeholder sentiment, risk — is there exactly one
implementation? Where mid-game projection and final award are computed by different code, treat
that as a defect until proven equivalent, and quantify the worst-case divergence near thresholds.

**E3 — Numerical hygiene.** Units and signs consistent across module boundaries. Division guards.
Negative treasury, negative equity, zero-denominator ratios. Clamping and saturation: is every
published floor and ceiling actually enforced in the code that awards the number, and is every
published maximum reachable? Accumulation and rounding across ten rounds. Order-of-operations
dependence between engines that mutate shared state.

**E4 — Determinism and fairness.** `rng_util.py` — is every stochastic draw seeded from the
session/fairness seed, or do some paths use unseeded global randomness? Do two teams making
identical decisions get identical outcomes? Is a completed session reproducible from its inputs
for a grading dispute? Can a participant's result depend on latency, request ordering, or which
worker served them?

**E5 — Config integrity.** The full precedence chain (code default → repo JSON → volume copy →
Excel). What silently wins? What happens on a malformed cell, an out-of-range value, a missing
key? Are sanity clamps applied with a loud warning or a silent substitution? Does
`simulation_config.provenance.json` describe what is actually loaded? Prove one end-to-end: pick a
tuning constant, change nothing, and trace the value the engine actually uses at runtime back to
its source.

**E6 — Relevance and pedagogical validity** (do not skip this for being softer than E1–E5).
For each major engine: is the functional form defensible for what it models — decay, diffusion,
learning curves, imitation, elasticity, discounting, probability semantics? Are magnitudes
plausible against real-world reference points, and can you name the reference? Do the levers move
in the right direction with roughly the right proportionality? Is stochastic noise small enough
that decisions dominate luck over ten rounds — test this, do not assert it (a monte-carlo spread
of outcomes for a fixed decision path versus the spread across decision paths is the check).
Is the model **legible**: can a participant, shown the result, infer which decision drove it? Are
there dominant strategies, degenerate optima, or dead levers that make the debrief hollow? Flag
any engine whose output is displayed with more precision or authority than its construction earns.

**E7 — What the engine promises and never delivers.** Deferred consequences, pending projects,
flags set and never consumed, messages that announce a future charge or event. Sweep the flag
taxonomy: for each declared flag, is it set anywhere, and is it read anywhere? A promise the model
makes to a participant and never keeps is a pedagogical defect, not a cosmetic one.

## DIMENSION F — flow, as participant and as facilitator (secondary)

**F1 — Participant walkthrough.** Narrate join → onboarding → round 1 decision → commit → results
→ … → round 10 → ending pathway → debrief artefact. At each step: what is on screen, what
information is available to decide with, what is ambiguous, what happens on reload, back button,
double tab, a 90-second connection drop, and a double-submit. Where can someone be stuck with no
forward action, no explanation, and no self-recovery? Are dead ends (insolvency, failed gates,
locked modules) intended teaching moments with a path out, or bugs wearing a lesson's clothes?

**F2 — Facilitator walkthrough.** Narrate cohort creation → roster and credential distribution →
briefing → opening the round → watching progress → intervening → advancing → debrief. Under time
pressure, in front of 50 people: can they see who is stuck, unstick one person, extend or force a
round, undo a mis-click, and recover a crashed cohort — each in a couple of clicks, without a
stack trace? Which of these is documented in a place they will actually have open?

**F3 — Number integrity across the seam.** Does every number on the participant dashboard, the
facilitator console, and the debrief artefact reconcile with the engine and with each other? A KPI
that contradicts the model teaches the wrong lesson and is worse than a missing KPI. Check the
debrief and analytics surfaces specifically — that is where a wrong number becomes a claim made
aloud to the room.

**F4 — Pacing realism.** Does the round structure fit the stated session length at 50 people? What
is the actual decision time per round, and what is the facilitator's control if the room runs long?

## DIMENSION C — classroom readiness at 50 (verdict)

**C1 — Concurrency.** Burst login and synchronised commit. Lost updates, double commit, the race
between facilitator round-advance and in-flight commits. Idempotency of every state-advancing
endpoint. Rate limits: check the **scope** explicitly — an IP-scoped limiter plus one shared
campus egress IP is a classic classroom outage.

**C2 — Durability and recovery.** What is lost on restart in each store mode. Atomicity of the
JSON/snapshot writes under concurrent access. Can a facilitator recover one participant, or the
whole cohort, without a developer? Export before and after class.

**C3 — Deployment reality.** Which deployment do participants hit, on which code and which
database? What breaks if a push lands mid-session? Are required env vars validated loudly at boot?
Health-check semantics, restart behaviour, rollback a non-developer can execute.

**C4 — Access and isolation.** Can a participant reach admin capability, another team's state, or
an unauthenticated endpoint that leaks scoring weights, answers, or tuning constants they could
optimise against? Enumerate unauthenticated routes exhaustively — this is a sweep, not a sample.
Token expiry versus a session spanning two days.

**C5 — Client reality.** 1366-wide layout on the commit path, draft survival across refresh,
behaviour on a stale tab after a redeploy, any rule enforced only client-side.

**C6 — Observability and the runbook.** At 11:40 on a Tuesday, what does the facilitator see, and
what is the shortest path from symptom to action? For each P0 you find, name the single signal
that would have caught it before class.

## SEVERITY — classroom and pedagogical impact, not CVSS

| Level | Meaning |
|---|---|
| **P0 — Class-stopper or false teaching** | Plausibly derails the session for many participants with no facilitator-executable workaround; silent data loss; a participant reaching admin capability; **or a headline number that is wrong in a way the facilitator would assert aloud in the debrief.** |
| **P1 — Session-degrading** | Strands individuals, forces a workaround the facilitator must be briefed on, or corrupts results in a way that undermines the debrief. |
| **P2 — Fix before the next cohort** | Real defect, low probability or contained blast radius this session. |
| **P3 — Hygiene / debt** | Correct to fix, no bearing on this deployment. |

For every P0 and P1 give: likelihood at 50 users, time to detect, time to recover **by a
non-developer**, and the cheapest mitigation available before class — which may be a config change,
a facilitator instruction, or a pre-class drill rather than a code fix.

## OUTPUT CONTRACT

One markdown report, written to the repo root as
`AUDIT_Engines_Flow_Classroom50_<YYYY-MM-DD>.md`, in this order:

1. **Verdict** — GO / GO-WITH-CONDITIONS / NO-GO on the first line, conditions enumerated, then
   no more than 150 words of reasoning.
2. **Assumptions** — scenario parameters assumed, and any you could not verify.
3. **Do-before-class list** — ordered, concrete, each executable by a non-developer in a stated
   number of minutes, each traceable to a finding ID.
4. **Engine verdicts table** — one row per engine examined: quantity owned, accuracy verdict,
   relevance verdict, confidence, worst finding. This table is the answer to Q1 and I want to be
   able to read it alone.
5. **Findings** — grouped by severity, **maximum 20**, ranked. Each as: ID, title, severity,
   CONFIRMED/PLAUSIBLE, dimension; evidence (`file:line` with the line quoted, or command +
   output); failure scenario with specific inputs and state; why it matters for this cohort; fix
   as a minimal diff snippet plus the cheaper pre-class mitigation; **the two passes used**; and
   what you tried in order to dismiss it and why it survived.
6. **Flow walkthroughs** — the participant and facilitator narratives, with friction points and
   stuck states called out inline.
7. **Verified-good** — things that could have been wrong and are not, with evidence. I need to
   know what you checked and cleared, not only what failed.
8. **Coverage and gaps** — what you swept exhaustively, what you sampled, what you never opened,
   and the exact procedure for anything you could not test here. Silent truncation reads as
   completeness and is worse than an admitted gap.
9. **Appendix A — model map** (from phase 2). **Appendix B — claims ledger** (prior claims,
   reproduced or not). **Appendix C — probe scripts** you wrote, so any result can be re-run.
10. **Live-session runbook** — one printable page: pre-flight checks, the three most likely
    failures with symptom and recovery action, escalation.

Constraints: no "consider adding tests" without naming the specific untested path and the specific
bug a test would have caught. No restating what existing audit documents already say unless you
are contradicting them. No praise, no filler, no executive-summary throat-clearing.

## CALIBRATION

Be adversarial about the system and honest about your own confidence. Ten findings I can act on
this week beat a comprehensive taxonomy of everything that could theoretically be wrong with a web
application. If, after real investigation, an engine is sound, say so plainly with the evidence —
manufactured severity wastes more of my time than a missed P3. And if the honest answer to Q3 is
NO-GO, say NO-GO on the first line.

## BEFORE YOU START

Ask, in one batch, only what you cannot reasonably assume and state: the deployment URL the cohort
will actually use and its branch; whether this is a single session or split across two days;
whether participants share one campus network; the paradigm and difficulty tier the cohort will
play; and where the report should be written. Then proceed without further blocking — for anything
else, assume, state the assumption in the report, and carry on.
