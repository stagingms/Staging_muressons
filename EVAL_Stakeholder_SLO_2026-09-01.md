# Stakeholder Management & Social License — Complete System Map and Evaluation

**Date:** 2026-09-01 · **Method:** full code walk of every stakeholder surface
(npc_stakeholders.py, autonomous_agents.py, stakeholder_sentiment.py,
stakeholder_map.py, stakeholder_engagement.py, negotiation.py / llm_negotiator.py,
systemic_risk_engine.py, the SLO write/read inventory across engine.py /
round_logic.py / impact_engine.py) plus controlled probes through
`process_npc_tick`. Companion: CALIBRATION_DIAGNOSIS_2026-09-01.md (the same
ratchet-vs-flow lens applied to money).

---

## 1. Verdict in one paragraph

The simulation runs **four distinct stakeholder surfaces**. Two of them — the
SLO stock itself and the five autonomous agents (Greta Berg, Commissioner
Carson, et al.) — are genuinely **accumulative and accelerating by default**:
tolerance integrates violations round over round, falls ~4× faster than it
recovers, agents amplify each other, and "triggered" is a permanent absorbing
state. The other two — the four **named NPCs** (activist investor, regulator,
community leader, journalist) and the portfolio **sentiment heat-map** — are
**memoryless by default**: NPC escalation is recomputed each round from the
current KPIs alone, so a team jumps to "Proxy Fight" in Round 1 and is
half-forgiven the instant its numbers recover. The accumulative model you are
asking for **already exists in the codebase** — a trust stock with asymmetric
dynamics and betrayal scars (F1), a continuous stakeholder→SLO feedback loop
(F2), coalitions (F3), a patience clock (F4), a promise ledger (F5), and a
full negotiation deal engine — but every one of those ships **default OFF**
behind per-cohort toggles. The single highest-leverage improvement is a
configuration decision, not code.

---

## 2. Surface A — SLO, the legitimacy stock (per BU, 0–100)

### Writers (every path that moves `social_license_score`)

| Writer | Where | Magnitude / condition | Cumulative? |
|---|---|---|---|
| Round-option impacts | round_logic `_apply_common_impacts` (guarded `social_license_applied_rN`) | per config, e.g. R9-A −20 | Yes — persists on the stock |
| Pillar aggregates | router `_apply_pillar_aggregate_impacts` | revenue-weighted × effectiveness | Yes |
| Greenwash scandal | engine ~3658 | −15/BU (full claim) or −7.5 (moderate), every round it fires | Yes, recurring |
| Natural decay / growth | engine `apply_natural_decay` (~698) | inv ratio <15% → −4%/round; 15–30% → flat; ≥30% → **+3/round** | Yes — the only unconditional faucet |
| Black swans | black_swan_registry ~813 | per event (whistleblower −15 etc.) | Yes |
| Agent triggered events | autonomous_agents | strike −20, media exposé −12, divestment −10 | Yes, one-shot |
| NPC cascade gates | systemic_risk_engine reaction gates | per gate effects | Yes |
| F2 continuous NPC pressure | npc_stakeholders `apply_stakeholder_slo_feedback` | +1.0 / 0 / −2.0 / −3.5 per round by tier, coalition-amplified | **OFF by default** |
| BRSR / regulatory sandbox / R10 handlers / admin override | various | bounded, guarded | Yes |

### Readers (what SLO gates)

R9 strike probability (50% base below SLO 50, burnout adds ≤ +20, cap 95%,
strike zeroes ALL round revenue, min penalty max($1M, 5% of treasury)); the
terminal **Instability Discount** (−0.40 M_R below avg 75, GAME-2 ramped over
a 5-point band — the glossary estimates ~$180M of terminal value); the
systemic-tipping **social tier**; SDG scores 1 and 2 (threshold 70); the
community NPC's satisfaction driver; agents' red lines (Greta Berg:
`avg_slo < 45`, weight 0.40); the R6 cascade chain severity; the forecast
panel.

### Behaviour of the stock — evaluation

SLO is correctly accumulative (a stock, not a recomputed score), with
double-apply guards from the 2026-08 audit. Its problem is **asymmetry of
faucets and drains**: below a 15% investment ratio the drains stack (−4%/round
decay, greenwash −7.5..15 recurring, option penalties, events) against zero
unconditional inflow — which is why every stored alpha team's SLO **pinned at
0 by mid-game** and stayed there (floor-clamped), locking in maximum strike
risk and the full instability discount with no recovery path. Note also that
the greenwash/decay thresholds are **relative ratios**: after the
ratchet-economy repair, treasuries are larger, so the same absolute capex now
produces a *lower* ratio — the SLO drains will bite harder for teams that
don't scale investment. (Already a MODEL_CARD watch item; it applies to SLO
even more than to cash.)

---

## 3. Surface B — the five autonomous agents (DEFAULT ON, accumulative)

`autonomous_agents.py`, run under `npc_stakeholders_enabled` (default true).
Five personas (regulator Carson, Gen-Z employee Greta Berg, journalist,
institutional investor, community activist), each with:

- **Tolerance stock** (starts 65–80): decays `patience_decay_rate` (8–15) ×
  (1 + severity) per violation round; recovers only 2–3/round on clean rounds
  (1.5× after 2 consecutive clean rounds). Falls roughly 4× faster than it
  heals — the asymmetry you want.
- **Grievance memory** (last 5 rounds) driving a trend label.
- **Acceleration mechanisms**, all live by default: severity-weighted decay
  (deeper red-line breach → faster loss); **interference pairs** (two agents
  at agitated+ multiply each other's decay — "internal and external
  grievances converge"); **cascade hits** (a triggered agent knocks 8–15
  tolerance off named targets); shadow-board decay modifiers.
- **Stages** dormant → watching → agitated → hostile → triggered, from the
  tolerance stock. `triggered` is **permanent** and fires a one-shot event:
  Carson's shutdown order (fine 4% of revenue), Greta's coordinated strike
  (SLO −20), the journalist's exposé (−12), divestment (−10).
- SLO enters via red lines (`avg_slo`), closing SLO → tolerance → stage →
  SLO. This is the one loop that both accumulates and accelerates out of the
  box — and the alpha data shows it working (teams sat at max violation
  pressure with SLO 0).

F4 (jittered thresholds + a patience clock that forces escalation the longer
you sit at a wary stage) would add "sitting still is also a decision" — built,
default off.

---

## 4. Surface C — the four named NPCs (DEFAULT: memoryless)

`npc_stakeholders.py`. Thornton (activist fund), Petrova (EU regulator),
community leader, journalist — Mitchell/Agle/Wood salience profiles, four
escalation tiers each, dialogue templates, and real consequences: hostile+
tiers cost −5 reputation *per round* (−3 legal/enforcement), regulator
enforcement draws a seeded $5–25M fine, tier states feed the reaction-gate
cascades (systemic_risk_engine) and F3 coalitions.

**The defect:** `calc_npc_satisfaction` is a pure function of the *current*
round's KPIs (`50 + Σ weight × (value − baseline)`), and by default the tier
gates directly on it. Probe (3 bad rounds, then instant KPI repair):

| | R1 bad | R2 bad | R3 bad | R4 good | R5 good | R6 good | R7 good |
|---|---|---|---|---|---|---|---|
| **Default** activist | adversarial | adversarial | adversarial | concerned | concerned | concerned | concerned |
| **F1 memory** activist (trust) | adversarial (27.5) | adversarial (15.5) | adversarial (6.5) | adversarial (21.4) | hostile (32.5) | hostile (40.9) | hostile (47.2) |

Default behaviour: **straight to the top tier in R1** (no staged escalation),
and **instant de-escalation** the moment KPIs recover — no memory of three
rounds of greenwashing. With `stakeholder_memory_enabled` (F1): trust
integrates satisfaction with `gain_rate < loss_rate` (rises slow, falls
fast), betrayal flags (deny-and-deflect, greenwashing, materiality_ignored)
subtract an immediate scar AND cap recovery for several rounds — the probe
shows a team needing **five clean rounds to climb out of hostile**. That is
precisely the accumulative response model; it is sitting behind a switch.

Bridging note: the NPC surface and the sentiment heat-map (Surface D) are
reconciled by construction *only when F1 is on* (`NPC_SENTIMENT_BRIDGE_WEIGHT`
blends them). Default-off means the two "how do they feel about us" surfaces
can visibly disagree in class.

---

## 5. Surface D — portfolio sentiment (the R1 map's ten stakeholders)

`stakeholder_sentiment.py` + `stakeholder_map.py`. The ten stakeholders the
teams place on the Mendelow power-interest grid in R1 acquire a persistent
`attitude_score`, updated every round by a flag→delta rule table (e.g.
renewables flags +5 across regulator/investor/NGO/community; fossil status quo
−6; deep audit +7) and by black swans; salience can migrate quadrants on
round events (C7, Ackermann & Eden). History is kept per round for the
heat-map and debrief. Cumulative, deterministic, display-oriented — its
scores gate nothing directly (by design: authority for consequences lives
with trust/tolerance), which is fine *once the F1 bridge makes it agree with
the surfaces that do gate*.

The R1 minigame itself is the entry point of stakeholder ANALYSIS: ≥80%
accuracy earns the reputation bonus and gates the R2 materiality path;
<60% takes a treasury penalty. It is the only place teams are *tested* on
stakeholder theory; everything after is consequences.

---

## 6. Where negotiation lives

There are three negotiation surfaces, in ascending explicitness:

1. **Implicit negotiation via options** — R9 Just Transition (closure vs
   $12M managed transition vs $20M community fund → community_champion
   +0.18 M_R), R4 crisis-response choices, CFO override (−5 rep to bypass the
   materiality gate). These are single-shot, priced trades with stakeholders;
   no dialogue, no memory.

2. **F5 engagement actions** (`stakeholder_engagement.py`, default OFF):
   once per round a team can hold a *town hall* (goodwill now, no promise),
   make a *public pledge* or *private commitment* — the latter two register on
   a **promise ledger** judged when they mature: kept promises pay trust,
   broken ones trigger the F1 betrayal scar plus a reputation ding. This is
   the "legitimacy is a repeated game" mechanic — and it requires F1 to bite.

3. **Stakeholder Negotiation Rooms** (`negotiation.py` + `llm_negotiator.py`,
   `negotiation_rooms_enabled`, default OFF, plus a per-facilitator
   capability gate): a real deal engine against the *autonomous agents*.
   $250K meeting fee, max 2 meetings/round, 6 dialogue turns (LLM-driven with
   a fully scripted fallback), a server-validated concession whitelist priced
   per persona ($0.5–2M: remediation fund, governance audit, transparency
   pact, wellbeing program…). Design rules worth teaching in themselves:
   **de-escalation is bought in tolerance and capped at the agent's
   "watching" threshold** — a deal buys you out of a fire, never into being
   loved; the road to dormant is clean rounds only. Deals register on the
   same F5 promise ledger (kept pays, broken scars), repeat deals with the
   same agent cost ×1.5 then ×2, and a live broken-promise scar adds a 25%
   surcharge. This is the most theoretically-honest negotiation model in the
   codebase and it has never been in front of a cohort.

**Game-performance impact of negotiation, quantified:** a successful room
visit converts $0.75–2.25M of treasury into 8–12 tolerance points — which is
1–2 rounds of violation decay bought back, i.e. it *delays* a strike
($35–40M+ of revenue at stake in a typical R9) or a shutdown order (4% of
revenue) rather than preventing them. Positive expectancy when used early at
"agitated"; near-worthless at "triggered" (absorbing). Kept promises then
compound through F1 trust into lower NPC pressure and (with F2) into +1.0
SLO/round from cooperative tiers — the only renewable SLO faucet besides the
≥30% investment growth branch.

---

## 7. Defects and friction found in this pass

1. **Default memorylessness of the named NPCs** (§4) — the headline gap
   against the "accumulative" requirement.
2. **No staged escalation by default**: tier gating on instantaneous
   satisfaction lets an NPC jump from nothing to its top tier in one round
   (probe: R1 "Proxy Fight"). Real escalation passes through stages; F4's
   patience clock only forces *upward* movement, nothing rate-limits it.
3. **SLO faucet/drain asymmetry** (§2): below 15% investment ratio the stock
   is a one-way street to 0; the alpha cohort's SLO-0-everywhere is this,
   not player skill. The relative-ratio thresholds get *harder* after the
   solvency repair.
4. **Surfaces disagree by default**: sentiment heat-map vs NPC tiers are
   only bridged under F1.
5. **Latent crash**: `process_npc_tick`'s enforcement path does
   `gs["corporate_treasury"] - fine` unguarded (KeyError on synthetic states;
   production states always carry the key — found via probe, worth a
   `.get(..., 0.0)` for harness safety).
6. **The stakeholder-management side track is orphaned**: its 12 outcome
   flags (`sm_esg_gold_standard`, `sm_community_partnership`…) were ruled
   narrative in the flag taxonomy — a track *about* stakeholder management
   whose outcomes never touch trust, tolerance, or sentiment.
7. NPC hostile tiers drain −5 rep/round while rep is itself a satisfaction
   driver — a doom loop that F1's slow-recovery would *deepen*; fine
   pedagogically, but it makes the negotiation/engagement exits matter, so
   those should not stay off if F1 is turned on.

## 8. Recommendations (none break core structure; ordered by leverage/cost)

1. **Turn on the built waves for the next cohort** — `stakeholder_memory_enabled`
   (F1), `stakeholder_slo_feedback_enabled` (F2), `stakeholder_uncertainty_enabled`
   (F4), and ideally `stakeholder_coalitions_enabled` (F3). Zero code; per-cohort
   toggles; every path is legacy-byte-identical when off, seeded when on. This
   alone delivers accumulative, accelerating, scarring stakeholder responses
   with a closed SLO loop.
2. **Open the negotiation surface with them** — `negotiation_rooms_enabled` +
   `stakeholder_engagement_enabled` (F5). F1 without exits is a doom spiral;
   the rooms and the promise ledger are the designed exits, and they carry the
   course's best lesson (trust is bought slowly, sold fast, and repurchased at
   a premium).
3. **One-tier-per-round escalation limiter** (small code, ~15 lines in
   `determine_npc_action`, behind the F4 toggle or a new one): an NPC's tier
   may worsen by at most one level per round from its previous tier. Preserves
   every threshold; adds the staging real stakeholders exhibit; makes early
   warnings readable instead of R1 detonations.
4. **Give SLO a floor-recovery ramp** (small config-level change): either
   raise the `apply_natural_decay` growth branch availability (e.g. ≥20%
   ratio → +1/round) or convert the greenwash/decay thresholds to
   `max(relative, absolute)` so the post-repair richer economy doesn't
   silently harden them. Decide with the next balance-report run.
5. **Always-on low-weight sentiment bridge** (one constant): let the heat-map
   and NPC surfaces converge even without F1, so the classroom never sees two
   contradictory moods for the same regulator.
6. **Wire the sm_ side track into trust** (one mapping): completion outcomes
   grant one-shot trust/tolerance credits (e.g. `sm_esg_gold_standard` → +8
   trust across NPCs) — the taxonomy entry then moves from `narrative` to
   read, and the track finally feeds the system it teaches.
7. **Guard the treasury key** in the enforcement path (one line).
8. **Telemetry**: add NPC tier trajectories, agent trigger counts, and
   negotiation-deal outcomes to `scripts/cohort_telemetry.py`, so the next
   cohort measures whether escalation timing lands where intended.

Sequencing: 1+2 are facilitator settings you can trial on a sandbox cohort
today; 3–7 are one small branch (`fix/stakeholder-staging`) with red tests
first; 8 rides with it. Nothing above touches the tick pipeline's structure,
the M_R ceilings, the conservation law, or any pinned baseline except via a
deliberate, documented rebaseline if 3 or 4 ship.

---

## 9. Implementation status (same day, branch `feat/stakeholder-waves-on`)

Recommendations **1 and 2 are IMPLEMENTED** (owner ruling): F1 memory, F2 SLO
feedback, F3 coalitions, F4 uncertain thresholds/patience, and F5 engagement
default ON in `DEFAULT_PEDAGOGICAL_TOGGLES` (per-cohort overrides unchanged;
F6 intel rail stays opt-in). Negotiation Rooms default ON at the platform
level (`_god_mode_settings`), and the per-facilitator capability contract
changed from opt-in to **default-granted, explicitly revocable** — the shared
rule lives in `admin_shared.facilitator_negotiation_granted`, used by both
the room gate and the cohort-settings gate; the revoke path (explicit False)
still refuses and still stops live cohorts. Acceptance: 5 red tests in
`tests/test_stakeholder_defaults.py` (defaults, overridability, capability
rule, and an end-to-end probe that the F1 trust stock initialises under
default toggles); the capability and parent-walk suites were updated to the
new contract with revocation coverage retained; the financial golden trace
was deliberately rebaselined; the stakeholder golden was unaffected (its
harness pins its own toggles). Balance report regenerated under waves-on:
aggressive_green solvent +$250M (stakeholder pressure costs ~$100M TV vs the
waves-off baseline), balanced solvent, extraction/neglect still fail; note
that scripted bots never negotiate or keep promises, so real teams should
outperform this floor using the exits the rooms provide. Full suite: 2242
passed. Recommendations 3–8 remain open.
