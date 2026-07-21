#!/usr/bin/env python3
"""
update_docs_july2026.py — fold the July-2026 feature work into the five
shipped manuals, each in its own voice and for its own audience.

Every statement here was checked against the code/commits it describes; where
a feature is specified but not yet built (role asymmetry) it is labelled as
such rather than documented as shipped.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from append_docx_section import append_section  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "docs"

H1, H2, H3 = "Heading1", "Heading2", "Heading3"


# ════════════════════════════════════════════════════════════════════
# 1. FACILITATOR MANUAL — how to run the new tools in a classroom
# ════════════════════════════════════════════════════════════════════
FACILITATOR = [
    (H1, "New Facilitation Tools (July 2026 Release)"),
    ("Normal", "This chapter covers the facilitation features added since v10 was first issued. "
               "Everything here is off by default: an existing cohort runs exactly as before until you "
               "switch a feature on, either per cohort or (for Negotiation Rooms) once a super admin has "
               "granted your profile the capability."),

    (H2, "Briefing Videos — the Read | Watch choice"),
    ("Normal", "Each round briefing can carry a companion video. Players see a Read | Watch pill at the top "
               "of the briefing and choose how they take the material in; the written briefing always remains "
               "available, so nothing is gated behind the video."),
    ("Normal", "Videos are referenced by URL only — nothing is uploaded into the platform, so the repository "
               "stays light and you keep control of your media. YouTube and Vimeo links are converted to "
               "embeds automatically; any other direct video URL plays in a native player."),
    ("Normal", "To configure: open Analytics & Cohort Controls, select the cohort, and use the Briefing Videos "
               "block. Enter one line per round in the form “1 = https://youtu.be/…”, or set a pattern such as "
               "https://cdn.example.edu/briefing-{round}.mp4 where {round} is substituted automatically. Rounds "
               "without a configured video simply show no pill."),

    (H2, "Dry-Run Simulator — fly the cohort before the class does"),
    ("Normal", "The Dry-Run Simulator is a pre-flight check on your cohort configuration. It plays four bot "
               "boards — Aggressive Green, Extractive, Balanced and Chaotic — headlessly through the real "
               "engine, from the cohort's current state to Round 10, several seeded repetitions each. Your "
               "cohort's actual state is never touched; a full run takes under a second."),
    ("Normal", "The report gives you a difficulty grade (forgiving / balanced / punishing / brutal), and per "
               "strategy: bankruptcy risk with the typical failure round, a treasury trajectory sparkline, "
               "final KPIs, the lowest social licence reached and peak stakeholder escalation. Beneath that, a "
               "“which rounds bite hardest” table shows median crisis damage, and a warnings panel flags "
               "configuration problems in plain language — for example that extractive play survives too "
               "comfortably, or that no strategy is survivable."),
    ("Normal", "Use it whenever you change starting treasury, crisis severity, carbon fee or market hostility. "
               "A configuration that grades brutal will demoralise a first-time cohort; one that grades "
               "forgiving will not reward the ESG thinking you are trying to teach."),
    ("Normal", "Find it under Command Centre → Dry-Run Simulator. Select a cohort, choose repetitions, run."),

    (H2, "Custom Black Swan Injector — now yours, per cohort"),
    ("Normal", "The Custom Black Swan Injector has moved from God Mode to the facilitator dashboard "
               "(Live Classroom → Black Swan Injector). Compose a crisis — title, narrative, and treasury, "
               "reputation, social-licence and natural-capital-debt deltas — and inject it into one cohort."),
    ("Normal", "Access is granted per cohort by a super admin. Your dropdown lists only the cohorts you own "
               "that have been unlocked; if none have, the panel explains who can unlock them. The injection "
               "history below the form shows only your own cohorts' events."),

    (H2, "Stakeholder Negotiation Rooms"),
    ("Normal", "When one of the five autonomous stakeholders escalates to hostile, players may request a "
               "meeting: a bounded negotiation in which the stakeholder appears in persona, states a grievance "
               "computed from live engine values, and names what they would accept."),
    ("Normal", "Availability is two-key. A super admin grants your facilitator profile the Negotiation Rooms "
               "capability (off by default); you then open rooms per cohort from Analytics & Cohort Controls. "
               "If the capability is revoked mid-programme, rooms stop immediately on live cohorts."),
    (H3, "What the players experience"),
    ("Normal", "An entry fee is charged simply for taking the meeting — advisor hours are not free. Inside, the "
               "stakeholder opens by citing their breached red line (“my limit is 55; you are at 65”). Players "
               "may talk, offer one binding concession and one free action, or walk out. Concessions are drawn "
               "from a per-stakeholder menu, so the regulator cannot be bought with a PR campaign."),
    ("Normal", "Concessions buy tolerance, but the increase is capped at the “watching” threshold: a deal buys "
               "a team out of a fire, never into being liked. The road back to calm is still clean rounds."),
    ("Normal", "Every substantive concession registers a promise with a metric, a target and a due round. If "
               "the team delivers, the engine pays them; if they do not, a trust scar applies and every future "
               "meeting with that stakeholder costs 25% more. Repeat deals with the same stakeholder also "
               "escalate in price (×1.5, then ×2). Walking out without a deal is remembered."),
    (H3, "Using it in the debrief"),
    ("Normal", "Open a team's card in Session Viewer to read the full transcripts: who they met, what was said, "
               "what it cost, what they promised, and whether the promise was kept or broken. Cohort Pulse "
               "shows a live “negotiating” flag while a room is open, so you can see which table is at the "
               "table. The richest discussion is usually about a broken promise: what did it cost them later, "
               "and did they understand they were spending trust rather than money?"),
    ("Normal", "If your deployment has an LLM key configured, the stakeholder improvises in character rather "
               "than reading scripted lines. The mechanic is identical either way — the model can only speak "
               "and gesture at concessions that already exist on the menu, and players must still click to "
               "accept. Without a key, the room runs fully scripted."),

    (H2, "Calibration — are their mental models improving?"),
    ("Normal", "The Predict-Before-Commit gate now captures structured forecasts: players pick a treasury band "
               "and a reputation direction, and (when Confidence is enabled) rate how sure they are. After the "
               "round resolves, they see a chip comparing what they called with what happened."),
    ("Normal", "At game over each player gets a calibration curve — stated confidence against realised "
               "hit-rate, with the perfect-calibration diagonal — and an Overconfidence Index."),
    ("Normal", "For you, Cohort Analytics gains a Calibration tab: a scatter of every team's confidence versus "
               "accuracy, the cohort's hit-rate trend by round (is the room's model of the system sharpening?), "
               "the most over- and under-confident teams, and a ready-to-read debrief prompt such as “three "
               "teams predicted with ≥80% confidence and missed every call — name the planning fallacy.”"),
    ("Normal", "Enable 🔮 Predictions (and optionally 🎰 Confidence) in Pedagogical Scaffolding. Scoring is "
               "deterministic and uses a proper scoring rule, so honest confidence beats bravado: a "
               "well-calibrated pessimist scores as well as a well-calibrated optimist."),

    (H2, "Experience levels and cohort setup"),
    ("Normal", "Selecting an experience level at cohort creation now preselects both the pedagogical "
               "scaffolding and the player-dashboard visibility appropriate to that audience, which you may "
               "then override for the specific cohort. Classroom and Workshop keep the newer mechanics off; "
               "Executive and Chaos enable Negotiation Rooms and (Executive) Predictions with Confidence."),
    ("Normal", "You can also author and save your own experience levels, and update an existing one rather "
               "than creating duplicates. The cohort wizard is laid out in two columns so the whole "
               "configuration fits on one screen, with the quiz settings inside Pedagogical Scaffolding and "
               "Advanced Controls as their own section."),

    (H2, "Corrections in this release"),
    ("Normal", "Undo Round and Decision History replay now work correctly (both were reading an empty store). "
               "The commit flow is a single screen: Predict Before You Commit carries the decision review and "
               "the Go Back & Edit action, so the separate review screen is gone. Session expiry is now "
               "reported as “session expired — please log in again” instead of a misleading permissions error, "
               "and facilitator sessions survive a backend restart."),
]


# ════════════════════════════════════════════════════════════════════
# 2. SYSTEM ARCHITECTURE — technical reference
# ════════════════════════════════════════════════════════════════════
ARCHITECTURE = [
    (H1, "14. July 2026 Architectural Changes"),
    ("BodyText", "This section records structural changes made after v2.0 of this document, with the "
                 "invariants each one establishes. Several were driven by a Railway-readiness audit whose "
                 "findings are tracked in AUDIT_Railway_Readiness.md."),

    (H2, "14.1 Store parity layer and the direct-access tripwire"),
    ("BodyText", "Deployment defaults to PostgreSQL (docker-start.sh sets USE_MEMORY_DB=false), and the "
                 "worker-count preflight only permits multiple uvicorn workers under the shared store. A class "
                 "of endpoints was reading the in-memory store's private dictionaries directly — "
                 "getattr(db, '_sessions'), or importing database_memory. Under PostgreSQL those reads return "
                 "empty structures, so the endpoints returned HTTP 200 with no data and no error."),
    ("BodyText", "Two parity APIs were added to both stores: fetch_all_sessions_raw() (all sessions including "
                 "per-player child sessions, which the leaderboard variant excludes) and fetch_all_decisions(). "
                 "All affected surfaces were ported to the async db API: situation-room bulletin, complexity "
                 "events, session health, cross-paradigm and cohort comparison, cohort pulse, god/player "
                 "analytics, agent teleprompter, teachable moments, peer leaderboard and trend history, "
                 "side-track round gating, username propagation, join-roster rebuild, consent capture, solo "
                 "round configs and player annotations."),
    ("BodyText", "Two memory-only write features (session clone; post-creation paradigm rewrite) now return "
                 "HTTP 501 with guidance under the shared store instead of writing to a detached dictionary "
                 "and reporting success."),
    ("BodyText", "The invariant is enforced by tests/test_store_access_tripwire.py, a tokenizer-based scan "
                 "that fails on getattr(db, '_…') and on any reference to _global_states, _bu_states, "
                 "_decision_log or _round_states outside the store modules. Reads of the _sessions mirror "
                 "remain legal because database.get_pool() hydrates it under PostgreSQL."),

    (H2, "14.2 Authentication and role resolution"),
    ("BodyText", "When JWT_SECRET is unset the process previously generated an ephemeral secret, so every "
                 "restart invalidated all facilitator cookies while the dashboard continued to render from "
                 "cached client state. A secret is now generated once and persisted to the durable data "
                 "directory (0600, gitignored); an explicit JWT_SECRET still takes precedence."),
    ("BodyText", "Guards distinguish authentication from authorisation: require_super_admin, "
                 "require_lead_facilitator and require_registry_admin return 401 “Session expired” for an "
                 "anonymous caller before evaluating role, rather than a role-based 403."),
    ("BodyText", "Virtual identities (god_mode, project_admin) have no registry record. Endpoints that derived "
                 "the caller role from the registry silently demoted them to “facilitator”. In "
                 "broadcast_message this produced a delivery failure — an admin broadcast returned 200 “sent” "
                 "while its ownership filter matched nothing. Role decisions now resolve through "
                 "get_fac_role(request) and is_admin_role(), per the role convention in CLAUDE.md. Cohort "
                 "settings additionally report keys refused by the caller's role as rejected_for_role instead "
                 "of dropping them silently."),

    (H2, "14.3 Negotiation subsystem"),
    ("BodyText", "backend/negotiation.py owns a server-side state machine (open / say / accept / walk_out / "
                 "close_on_commit) over active_event_flags.negotiation_log, using the dual-representation "
                 "persistence pattern described in 14.5. Concession menus derive per agent from "
                 "AGENT_PROFILES.monitored_metrics; grievances are computed from live engine values via "
                 "_compute_agent_metrics. Pricing applies a repeat ladder (×1, ×1.5, ×2) plus a 25% surcharge "
                 "while a broken-promise scar is live. Tolerance gains are capped at the agent's watching "
                 "threshold. Accepted concessions register promises on the existing F5 ledger tagged "
                 "source=\"negotiation\"; resolve_agent_promises runs for those promises even when the F5 "
                 "engagement toggle is off, while engagement actions themselves stay gated."),
    ("BodyText", "backend/llm_negotiator.py is the optional dialogue layer. It assembles a per-turn prompt "
                 "from engine truth only and accepts a single JSON object {dialogue, offer?, mood}. An offer "
                 "survives validation only if its concession id is on that agent's live menu, and even then it "
                 "renders as a suggestion — applying a concession still requires the player's explicit accept "
                 "call, which re-runs whitelist validation. Every failure path (no key, timeout, HTTP error, "
                 "malformed JSON, off-menu id) degrades to the deterministic scripted line. The boundary is "
                 "covered by an injection suite that feeds fully compromised payloads into the room and asserts "
                 "an unchanged state snapshot."),
    ("BodyText", "Availability is two-key: a per-facilitator capability flag on the registry record "
                 "(negotiation_rooms_enabled, default false, granted by a super admin) plus a per-cohort "
                 "setting. Player-side calls re-check the owning facilitator's capability, so revocation takes "
                 "effect on live cohorts."),

    (H2, "14.4 Pre-flight simulation (dry run)"),
    ("BodyText", "backend/dry_run.py plays four bot strategies through the production call chain "
                 "(pre_tick → process_tick → post_tick → run_new_engines) on deepcopied state, N seeded "
                 "repetitions each, and returns a difficulty report. Bot choices are scored from configured "
                 "option impacts rather than hard-coded, so they track facilitator re-tuning. Both entropy "
                 "channels are pinned per repetition (the global random module and the GAME-4 stochastic_seed "
                 "streams). The endpoint runs the simulation on the event loop and restores the process RNG "
                 "state afterwards, so a dry run cannot perturb a concurrent live commit."),

    (H2, "14.5 Engine state persistence and reporting fidelity"),
    ("BodyText", "ENGINE_STATE_KEYS carries eight stateful engine sub-dictionaries across the process_tick "
                 "boundary (npc_stakeholders, autonomous_agents, balance_sheet, biodiversity_state, "
                 "board_governance, org_politics, supply_chain, regulatory_sandbox), which previously "
                 "re-initialised every round. The stakeholder/SLO golden trace was rebaselined for this "
                 "behaviour change; the oracle protocol is documented in the test itself."),
    ("BodyText", "New per-round state (predictions_log, negotiation_log) is written to both the flags "
                 "dictionary and the top level of global state. The memory store unpacks flag keys to the top "
                 "level on read and re-packs on write with explicit values winning, so writing only one "
                 "representation is silently overwritten."),
    ("BodyText", "The balance sheet no longer reports negative cash. process_balance_sheet_tick sweeps any "
                 "cash deficit into short_term_debt (cash floors at zero, the line is set rather than "
                 "accumulated because cash re-syncs from treasury each tick) and charges half-year revolver "
                 "interest on the drawn amount. corporate_treasury remains the engine's single source of truth "
                 "for cash and may be negative; the sweep is presentation-layer correctness so that total "
                 "liabilities, gearing, liquidity and covenant readings are computed from a coherent "
                 "statement. The year-by-year statement stitches history across round rows at read time, "
                 "recovering all five years for sessions that predate the ledger-carry fix."),

    (H2, "14.6 Calibration capture"),
    ("BodyText", "Structured predictions (treasury band, reputation direction, optional confidence) are "
                 "captured through a player-guarded endpoint into predictions_log and scored post-tick by a "
                 "deterministic band scorer in pedagogical_engine.py, using a Brier term over the predicted "
                 "KPIs. Scoring is read-only with respect to engine ledgers and exception-isolated; a "
                 "seed-pinned control run demonstrates identical engine outcomes with and without predictions."),

    (H2, "14.7 Content-Security-Policy"),
    ("BodyText", "The CSP in next.config.mjs previously omitted frame-src, so iframes fell back to "
                 "default-src 'self' and briefing-video embeds were blocked by the application's own policy. "
                 "frame-src now allows www.youtube.com, www.youtube-nocookie.com and player.vimeo.com, and "
                 "media-src allows https: for direct-URL video. frame-ancestors 'none' is unchanged."),
]


# ════════════════════════════════════════════════════════════════════
# 3. STUDENT MANUAL — player voice, second person
# ════════════════════════════════════════════════════════════════════
STUDENT = [
    (H1, "New in Your Cockpit"),
    ("Normal", "Your facilitator decides which of these are switched on for your cohort, so you may not see "
               "all of them."),

    (H2, "Read or watch your briefing"),
    ("Normal", "Where your facilitator has provided one, the round briefing carries a Read | Watch choice at "
               "the top. Watch plays a short video of the same material; Read gives you the written briefing. "
               "Neither is a shortcut — they carry the same content, so use whichever you absorb better. You "
               "can switch back and forth at any time."),

    (H2, "Predict before you commit"),
    ("Normal", "Before your decisions are locked in, you will be asked to call the round: whether treasury "
               "will fall or rise and by roughly how much, and which way reputation will move. If your cohort "
               "has confidence enabled, you also say how sure you are."),
    ("Normal", "This is not a test you can fail, and it does not affect your results. When the round resolves "
               "you see what you called against what actually happened, and at the end of the simulation you "
               "get a calibration curve: your stated confidence plotted against how often you were right, with "
               "an Overconfidence Index."),
    ("Normal", "The scoring rewards honesty, not bravado. Being 70% right while claiming 70% confidence scores "
               "better than being 70% right while claiming certainty. A well-calibrated pessimist scores as "
               "well as a well-calibrated optimist. Knowing how much to trust your own forecasts is the skill "
               "being measured."),

    (H2, "Negotiating with hostile stakeholders"),
    ("Normal", "The five stakeholders watching your company react to what you do. If one becomes hostile, you "
               "may be able to request a meeting from their card in the stakeholder panel."),
    ("Normal", "Read the room before you spend. There is a fee simply for taking the meeting. The stakeholder "
               "opens by telling you exactly which of their limits you have breached and by how much — that is "
               "real data from your simulation, not flavour text. What they will accept is specific to them: "
               "the regulator wants remediation and audits, the journalist wants transparency, your workforce "
               "representative wants wellbeing measures."),
    ("Normal", "Three things are worth understanding before you agree to anything. First, a concession buys "
               "you calm, not affection — tolerance recovers only so far, and the rest has to be earned with "
               "clean rounds. Second, most concessions are promises: a metric, a target, and a deadline. Keep "
               "it and you are rewarded; break it and you carry a trust scar that makes every future meeting "
               "with that stakeholder more expensive. Third, going back to the same stakeholder repeatedly "
               "costs progressively more."),
    ("Normal", "You can also walk out. That is sometimes right — but it is remembered."),

    (H2, "One commit screen"),
    ("Normal", "Committing a round is now a single screen. Predict Before You Commit shows your staged "
               "decisions, your allocation per business unit and the projected cost, alongside the prediction "
               "questions. Go Back & Edit is on that screen if you want to change anything, and Skip & Commit "
               "is always available if you would rather not predict."),

    (H2, "Reading your balance sheet"),
    ("Normal", "If your company runs out of cash, the statement no longer shows a negative cash balance. As in "
               "a real business, the shortfall appears as Short-Term Debt on the liabilities side, and you pay "
               "interest on it each round. This means your total liabilities, gearing and covenant position "
               "reflect the true situation — and that borrowing to survive has a visible, compounding cost."),
    ("Normal", "The Year-by-Year Statement shows every year of the simulation, so you can trace how the "
               "position built up rather than seeing only where it ended."),
]


# ════════════════════════════════════════════════════════════════════
# 4. SIMULATION DESIGN DOCUMENT — rationale and pedagogy
# ════════════════════════════════════════════════════════════════════
DESIGN = [
    (H1, "Design Additions — July 2026"),
    ("BodyText", "This section records the pedagogical intent behind features added after the original design "
                 "document, and the design constraints each accepted."),

    (H2, "Calibration as a measured learning outcome"),
    ("BodyText", "The simulation's stated aim is improved mental models of a complex system. Until now that "
                 "claim was assessed indirectly, through outcomes. Structured prediction makes it measurable: "
                 "players commit to a treasury band and reputation direction before each round, optionally "
                 "with a confidence rating, and the engine scores those calls against realised deltas."),
    ("BodyText", "Three design decisions matter. Bands are deliberately coarse (flat is ±$1M; big moves are "
                 "beyond ±$5M) because the goal is directional literacy, not point estimation. Scoring uses a "
                 "Brier term, a proper scoring rule, so a player's best strategy is honest reporting — "
                 "overstating confidence is penalised even when the call is right. And no leaderboard or badge "
                 "is attached to calibration: comparison pressure would corrupt the very self-report being "
                 "measured. The facilitator sees a cohort trend by round, which answers whether the room's "
                 "model is sharpening as the game proceeds."),

    (H2, "Negotiation rooms — pricing a concession"),
    ("BodyText", "The autonomous stakeholder system is the platform's most distinctive engine, but players "
                 "experienced it passively: stakeholders escalated at them. Negotiation rooms make the "
                 "relationship transactional and therefore teachable — the skill being exercised is reading a "
                 "counterparty's mandate and pricing what it costs to satisfy it."),
    ("BodyText", "Grievances shown in the room are computed from the same monitored metrics that drive "
                 "escalation, so the character cannot claim a concern the engine does not model. Menus are "
                 "per-persona, which teaches that stakeholders are not interchangeable: an audit does not "
                 "placate a journalist."),
    ("BodyText", "Two constraints keep the mechanic honest. De-escalation purchased in a room is capped at the "
                 "watching threshold, so a wealthy team cannot buy its way back to a clean relationship — "
                 "money defers consequences, it does not undo them. And substantive concessions register "
                 "promises with deadlines, so the mechanic becomes a repeated game: a broken promise applies a "
                 "trust scar and raises the price of every subsequent meeting. This is the intended lesson — "
                 "reputation is capital that compounds in both directions."),
    ("BodyText", "Where an LLM is configured it roleplays the persona, but it holds no authority: it may only "
                 "gesture at concessions already on the validated menu, and applying anything requires an "
                 "explicit player action. The mechanic is therefore identical with or without a model, which "
                 "keeps the pedagogy reproducible across deployments."),

    (H2, "Reporting fidelity corrections"),
    ("BodyText", "Three fidelity defects were corrected because they taught incorrect lessons."),
    ("BodyText", "Negative cash. The statement of financial position previously displayed a negative Cash & "
                 "Equivalents balance against zero short-term debt — an accounting impossibility that "
                 "understated liabilities by the entire deficit and corrupted gearing, liquidity and covenant "
                 "readings. Deficits are now swept into short-term debt and charged interest. For a tool that "
                 "teaches statement literacy, the displayed statement must be one a student could defend."),
    ("BodyText", "Synergy operating expenditure. Compounding synergy reductions could drive a unit's operating "
                 "cost toward zero, which made the risk radar meaningless in late rounds. Reductions are now "
                 "floored at 35% of the Round-1 baseline, preserving the incentive while keeping the cost base "
                 "credible."),
    ("BodyText", "Engine memory. Several stateful engines — stakeholders, board governance, balance sheet, "
                 "supply chain — were silently re-initialised each round, so accumulated consequences did not "
                 "accumulate. They now persist across the round boundary, which materially changes late-game "
                 "trajectories: neglect compounds as designed."),

    (H2, "Configuration quality assurance"),
    ("BodyText", "Difficulty tuning was previously validated only by running a cohort. The dry-run simulator "
                 "plays four archetypal strategies through the real engine and reports whether opposed "
                 "strategies produce distinct, survivable-but-consequential outcomes. It exists because a "
                 "configuration in which every strategy bankrupts, or in which extractive play is comfortable, "
                 "defeats the simulation's teaching purpose regardless of how the engine behaves internally."),

    (H2, "Specified but not yet implemented: role asymmetry"),
    ("BodyText", "SPEC_Role_Asymmetry_Teams.md specifies assigning CEO, CFO and Chief Sustainability Officer "
                 "roles within a team, each holding private information (the CFO sees true covenant headroom; "
                 "the CSO sees stakeholder intelligence early) and requiring explicit consensus to commit. The "
                 "intent is to convert solo optimisation into negotiation between legitimately conflicting "
                 "mandates, which is closer to the actual practice of ESG decision-making. The specification "
                 "is complete and phased; no implementation has shipped as of this revision."),
]


# ════════════════════════════════════════════════════════════════════
# 5. GOD MODE ADMINISTRATION GUIDE — platform administration
# ════════════════════════════════════════════════════════════════════
GODMODE = [
    (H1, "New Administrative Controls (July 2026)"),

    (H2, "Per-facilitator capability: Stakeholder Negotiation Rooms"),
    ("BodyText", "Negotiation Rooms follow the console-capability pattern used for Shockwave, Trading Floor "
                 "and Situation Room, with one difference: the grant defaults to OFF. The feature is opt-in "
                 "per facilitator."),
    ("BodyText", "Grant it in Cohort Orchestration → Facilitator Registry, in the facilitator's drawer "
                 "(“🤝 Stakeholder Negotiation Rooms”). It is also accepted as a negotiation_rooms_enabled "
                 "column in bulk CSV upload."),
    ("BodyText", "Semantics: a lead facilitator holding the grant may switch Negotiation Rooms on for their "
                 "own cohorts from Analytics & Cohort Controls. Without it the control is hidden and a direct "
                 "API attempt is refused with an explanation. Super admins and god_mode may enable it on any "
                 "cohort regardless of the owner's grant. Revoking the grant takes effect immediately on live "
                 "cohorts — every player-side negotiation call re-checks the owning facilitator's capability, "
                 "so an open room stops accepting turns rather than continuing until the cohort flag is "
                 "cleared."),

    (H2, "Custom Black Swan Injector: per-cohort unlock"),
    ("BodyText", "The injector has moved to the facilitator dashboard. Unlock it per cohort from Analytics & "
                 "Cohort Controls → Facilitator Tools; the owning lead facilitator can then compose and inject "
                 "custom crises into that cohort only. Enforcement is server-side (lead role, session "
                 "ownership and the per-cohort unlock), and the injection history is scoped to the caller's "
                 "own cohorts. God Mode retains the preset crisis catalogue under Crisis Overrides."),
    ("BodyText", "Injection history is written to the durable audit trail rather than process memory, so it "
                 "survives restarts and is consistent across workers."),

    (H2, "Analytics visibility: platform, per facilitator, per cohort"),
    ("BodyText", "Analytics visibility resolves in three layers: the platform default, an optional "
                 "per-facilitator profile, and any per-cohort override. Per-facilitator profiles are edited "
                 "from the Facilitator Registry and stored sparsely — only keys you explicitly set are "
                 "recorded, and a profile can be cleared to fall back to the platform default."),
    ("BodyText", "Note when adding cards: a visibility key must exist in the backend catalogue "
                 "(_analytics_visibility in admin_analytics.py) as well as the frontend registry "
                 "(app/config/analyticsRegistry.js). The setter endpoints silently discard unknown keys, so a "
                 "key present only in the frontend produces a toggle that cannot persist."),

    (H2, "Briefing videos"),
    ("BodyText", "briefing_video_base and briefing_videos are ordinary global settings, overridable per "
                 "cohort, and are configured from Analytics & Cohort Controls. They accept URLs only — no "
                 "media is stored on the platform. Because they are cohort-overridable settings they can also "
                 "be set through the Sim Switchboard PATCH; hand-editing the state snapshot is not required "
                 "and is not recommended, as a running server may overwrite it on its next persist."),

    (H2, "Experience-level presets"),
    ("BodyText", "Each experience level now carries a default pedagogical-scaffolding set, a default "
                 "player-dashboard visibility set and default player features, applied when the level is "
                 "selected at cohort creation and overridable per cohort. Negotiation Rooms are preset ON for "
                 "Executive and Chaos, OFF for Classroom and Workshop. Facilitator-authored custom levels are "
                 "supported, with an update path for an existing level rather than duplicate creation; custom "
                 "levels are restricted to whitelisted keys."),

    (H2, "Session, identity and delivery corrections"),
    ("BodyText", "Session expiry. An expired or invalidated cookie now returns 401 “Session expired — please "
                 "log in again” rather than a role-based 403. Previously a dead session surfaced as a "
                 "permissions error (for example “Registry-admin access required” for god_mode) while the "
                 "dashboard still appeared logged in."),
    ("BodyText", "Session durability. If JWT_SECRET is not set in the environment, the platform now generates "
                 "a secret once and persists it in the durable data directory, so facilitator sessions survive "
                 "a restart or redeploy. Setting JWT_SECRET explicitly remains the recommended production "
                 "practice; for long workshops, JWT_EXPIRY_HOURS controls the two-hour default."),
    ("BodyText", "Universal Broadcast. Broadcasts sent from a god_mode session were delivered to no cohorts "
                 "while reporting success: the caller's role was resolved from the facilitator registry, in "
                 "which god_mode has no record, so it was treated as a plain facilitator and the ownership "
                 "filter matched nothing. Role decisions now resolve from the signed token. Ownership scoping "
                 "for named facilitators is unchanged — they still reach only their own cohorts."),
    ("BodyText", "Cohort settings. Keys a caller's role may not set are now reported in the response as "
                 "rejected_for_role instead of being discarded silently, so a refused change is visible rather "
                 "than appearing to succeed."),

    (H2, "Dry-run simulator"),
    ("BodyText", "Available to any facilitator for cohorts they own (Command Centre → Dry-Run Simulator), the "
                 "dry run plays four bot strategies through the production engine on a copy of the cohort's "
                 "state and returns a difficulty report with configuration warnings. It never mutates the "
                 "cohort. Use it to validate platform-level parameter changes — carbon fee, market hostility, "
                 "starting treasury — before they reach a classroom."),
]


JOBS = [
    ("Muressons_Facilitator_Manual_v10.docx", FACILITATOR),
    ("Muressons_System_Architecture.docx", ARCHITECTURE),
    ("Muressons_Student_Manual_v10.docx", STUDENT),
    ("Muressons_Simulation_Design_Document.docx", DESIGN),
    ("Muressons_God_Mode_Administration_Guide.docx", GODMODE),
]


if __name__ == "__main__":
    for fname, blocks in JOBS:
        path = DOCS / fname
        if not path.exists():
            print(f"  !! missing: {fname}")
            continue
        append_section(path, blocks)
        words = sum(len(t.split()) for _, t in blocks)
        print(f"  ✓ {fname}: +{len(blocks)} paragraphs (~{words} words)")
