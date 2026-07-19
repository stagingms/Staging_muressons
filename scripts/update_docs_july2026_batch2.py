#!/usr/bin/env python3
"""
update_docs_july2026_batch2.py — second documentation pass, folding the
July-2026 work into the remaining eight manuals.

Batch 1 (update_docs_july2026.py) covered the Facilitator Manual, System
Architecture, Student Manual, Simulation Design Document and God Mode
Administration Guide. This batch covers the operational, reference and
curriculum documents. The Simulation Design Document is deliberately NOT
repeated here — it already carries its July-2026 section.

Every endpoint path, field name, default and threshold below was read out of
the code it documents.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from append_docx_section import append_section  # noqa: E402

DOCS = Path(__file__).resolve().parent.parent / "docs"
H1, H2, H3, H4 = "Heading1", "Heading2", "Heading3", "Heading4"


# ════════════════════════════════════════════════════════════════════
# 1. PATHWAY MAP — where the new surfaces sit in the round flow
# ════════════════════════════════════════════════════════════════════
PATHWAY = [
    (H1, "July 2026 — Additions to the Round Flow"),
    ("", "The additions below are optional branches, not new mandatory stages. With every "
         "feature switched off the pathway is unchanged from the map above."),

    (H2, "Briefing stage — Read | Watch"),
    ("", "Where the facilitator has configured a video for the round, the briefing screen offers a "
         "Read | Watch toggle. Both routes carry the same content and the player may switch freely; "
         "no downstream state depends on the choice. Rounds with no configured video show no toggle."),

    (H2, "Decision stage — one commit screen"),
    ("", "The former two-screen commit (Review Your Decisions → Predict Before You Commit) is now a "
         "single screen. Predict Before You Commit carries the staged decision summary, the per-unit "
         "allocation breakdown, the projected cost, and the Go Back & Edit action alongside the "
         "prediction questions. Skip & Commit remains a one-click exit, so the fast path through the "
         "round is one step shorter than before."),
    ("", "Where predictions are enabled the player may record a treasury band and a reputation "
         "direction, plus a confidence rating when that toggle is on. Recording a prediction is "
         "optional and never blocks the commit."),

    (H2, "Optional branch — Stakeholder Negotiation Rooms"),
    ("", "This branch opens only when all of the following hold: the cohort has negotiation rooms "
         "enabled, the owning facilitator holds the capability, and at least one autonomous "
         "stakeholder has escalated to hostile or triggered."),
    ("", "Entry: the stakeholder's card in the rail offers Request a meeting. An entry fee is charged "
         "on opening, regardless of outcome."),
    ("", "Inside the room the player may talk (up to six turns), accept at most one binding concession "
         "and one free action from that stakeholder's menu, or walk out. The room closes on walk-out, "
         "on the turn limit, or automatically when the round commits — it never blocks or outlives "
         "the round."),
    ("", "Exits and their consequences: a deal raises tolerance (capped at the watching threshold) and, "
         "for substantive concessions, registers a promise due two rounds later; walking out with no "
         "deal increases the stakeholder's patience counter; a promise that later fails applies a trust "
         "scar that raises the price of subsequent meetings by 25%."),

    (H2, "Results stage — retrospective surfaces"),
    ("", "Three retrospective chips may appear in the results overlay, all read-only: the prediction "
         "comparison (what you called against what happened), the round's negotiated deals, and the "
         "existing consequence map. At game over the player additionally receives a calibration curve "
         "and Overconfidence Index alongside the front page and archetype card."),
]


# ════════════════════════════════════════════════════════════════════
# 2. STAKEHOLDER MODULE REFERENCE — the deep reference for negotiation
# ════════════════════════════════════════════════════════════════════
STAKEHOLDER = [
    (H1, "Negotiation Rooms (July 2026)"),
    ("", "Negotiation rooms add a player-initiated interaction to the five autonomous agents "
         "documented above. They do not change escalation, tolerance decay, cascade behaviour or "
         "triggered events; they add a bounded transaction that can raise tolerance at a price, and "
         "they reuse the F5 engagement primitives for execution."),

    (H2, "Preconditions"),
    ("ListBullet", "The cohort setting negotiation_rooms_enabled is on (default off)."),
    ("ListBullet", "The owning facilitator holds the per-facilitator capability of the same name "
                   "(default off, granted by a super admin). Player calls re-check this, so revoking "
                   "it stops rooms on live cohorts."),
    ("ListBullet", "The target agent's escalation_stage is hostile or triggered. Any other stage is "
                   "refused with an explanation naming the current stage."),

    (H2, "Grievances are computed, never authored"),
    ("", "The grievance list shown in the room is derived from the agent's own monitored_metrics "
         "entries in AGENT_PROFILES, compared against live values from _compute_agent_metrics. Each "
         "row carries the metric, its current value, the agent's red line, the direction of the "
         "breach and the metric weight; breached rows sort first. An agent therefore cannot raise a "
         "concern the engine does not model, and the numbers quoted in dialogue are the same numbers "
         "driving escalation."),

    (H2, "Concession catalogue"),
    ("", "Menus are per-agent, derived from what that persona monitors. The catalogue below is the "
         "v1 whitelist; costs are base values before multipliers."),
    (H3, "Remediation Fund — regulator, community activist"),
    ("ListBullet", "Cost $2,000,000 · tolerance +12 · promise: average social licence must rise by 5 points."),
    (H3, "Independent Governance Audit — regulator, institutional investor"),
    ("ListBullet", "Cost $1,500,000 · tolerance +10 · immediate governance-risk relief of 3 points · "
                   "promise on group reputation (+3)."),
    (H3, "Radical Transparency Pact — journalist"),
    ("ListBullet", "Cost $500,000 · tolerance +8 · sets a transparency flag for two rounds · promise "
                   "on group reputation (+2)."),
    (H3, "Workforce Wellbeing Program — Gen-Z employee representative"),
    ("ListBullet", "Cost $1,000,000 · tolerance +10 · immediate burnout relief of 4 points · promise "
                   "on average social licence (+3)."),
    (H3, "Dividend Commitment Signal — institutional investor"),
    ("ListBullet", "Cost $500,000 · tolerance +8 · promise on group reputation (+2)."),
    (H3, "Public Apology — any agent"),
    ("ListBullet", "Free · tolerance +4 · group reputation −2 · no promise. The free tier costs "
                   "standing rather than cash."),
    ("", "Promise metrics are limited to directionally increasing measures (average social licence, "
         "group reputation) because the shared resolver judges a promise kept when the metric is at or "
         "above target. Relief on inverted metrics such as governance risk or burnout is therefore "
         "applied as an immediate bounded effect instead of a promise."),

    (H2, "Pricing"),
    ("", "The displayed price is the base cost multiplied by a repeat ladder — ×1 for the first "
         "accepted deal with that agent, ×1.5 for the second, ×2 thereafter — plus a further 25% while "
         "a broken-promise trust scar is live on that agent. A meeting fee of $250,000 is charged on "
         "opening the room whether or not a deal follows."),

    (H2, "Tolerance cap"),
    ("", "A concession raises tolerance but never above the agent's watching threshold, as defined in "
         "that agent's escalation_thresholds. Deals therefore buy a team out of hostility but cannot "
         "restore a dormant relationship; recovery beyond the cap remains a function of clean rounds "
         "and the agent's recovery_rate."),

    (H2, "Promise ledger integration"),
    ("", "Substantive concessions append to the same promises ledger used by the F5 engagement "
         "system, tagged source=\"negotiation\", with a metric, a target computed from the current "
         "value plus the concession's bump, and a due round two rounds out. resolve_agent_promises "
         "judges them at the due round: kept promises pay the standard tolerance, social-licence and "
         "reputation credits; broken promises apply the immediate tolerance penalty and set scar_until, "
         "which both dampens the relationship and raises future negotiation prices."),
    ("", "Note for maintainers: promise resolution runs for negotiation-sourced promises even when the "
         "F5 engagement toggle is off, otherwise a negotiated promise would never come due and the "
         "mechanic would be a free tolerance pump. Engagement actions themselves remain gated by the "
         "F5 toggle."),

    (H2, "Session limits"),
    ("ListBullet", "One open room at a time per team."),
    ("ListBullet", "Two meetings per round per team."),
    ("ListBullet", "Six player turns per room."),
    ("ListBullet", "One promised concession plus one free action per meeting."),
    ("ListBullet", "Rooms auto-close when the round commits."),

    (H2, "Dialogue layer"),
    ("", "Where an LLM key is configured the agent's replies are generated in persona from a prompt "
         "assembled entirely from engine truth: the persona block, computed grievances, the priced "
         "menu with its concession ids, deals already agreed in this meeting, and whether a trust scar "
         "is live. The model returns a single JSON object containing dialogue, an optional offer and a "
         "mood."),
    ("", "The model holds no authority. An offer survives validation only if its concession id appears "
         "on that agent's live menu, and even then it renders as a highlighted suggestion — applying a "
         "concession still requires the player's explicit accept call, which re-runs whitelist "
         "validation. Any failure (no key, timeout, HTTP error, malformed JSON, invented or "
         "off-menu id) falls back to the deterministic scripted line, so a deployment without a key "
         "plays the identical mechanic."),

    (H2, "Facilitator visibility"),
    ("", "Cohort Pulse shows a negotiating flag against a team while a room is open. Session Viewer "
         "exposes full transcripts per team, with deals, costs, tolerance movements and the state of "
         "every negotiated promise."),
]


# ════════════════════════════════════════════════════════════════════
# 3. MBA COURSE SYLLABUS — curriculum framing
# ════════════════════════════════════════════════════════════════════
SYLLABUS = [
    (H1, "Curriculum Additions (July 2026)"),

    (H2, "Learning outcome: forecast calibration"),
    ("", "The platform can now measure, per student, whether their model of the system improves over "
         "the ten rounds. Before each commit a student records a directional forecast (treasury band, "
         "reputation direction) and, optionally, a confidence level; the engine scores those calls "
         "against realised outcomes using a proper scoring rule."),
    ("", "This supports an outcome that is otherwise difficult to assess directly: judgement under "
         "uncertainty, and specifically the metacognitive skill of knowing how much to trust one's own "
         "forecasts. The cohort-level trend answers whether the room is learning the system or merely "
         "accumulating results."),
    ("ListBullet", "Enable 🔮 Predictions in Pedagogical Scaffolding; add 🎰 Confidence for the "
                   "calibration curve and Overconfidence Index."),
    ("ListBullet", "Recommended for Executive-level cohorts; optional for first-time classroom groups, "
                   "where the extra step can crowd the decision discussion."),
    ("ListBullet", "Deliberately unscored and unranked: no leaderboard is attached, because comparison "
                   "pressure corrupts honest confidence reporting."),

    (H2, "Session activity: stakeholder negotiation"),
    ("", "Where enabled, a team facing a hostile stakeholder may request a meeting and negotiate a "
         "priced, binding concession. The exercise targets three teachable behaviours: reading a "
         "counterparty's actual mandate rather than assuming a generic one; pricing a concession "
         "against its downstream obligation; and recognising reputation as capital that compounds in "
         "both directions."),
    ("", "Suggested debrief questions:"),
    ("ListBullet", "Which stakeholder did you meet first, and why that one?"),
    ("ListBullet", "What did the meeting cost you before you conceded anything — and was the "
                   "information worth the fee?"),
    ("ListBullet", "You promised a target two rounds out. What did you change to deliver it, or what "
                   "did you decide to sacrifice instead?"),
    ("ListBullet", "For teams carrying a trust scar: what does it now cost you to be believed, and "
                   "when did that become clear?"),
    ("ListBullet", "Did anyone walk out? What did that buy, and what did it cost?"),

    (H2, "Assessment evidence available to instructors"),
    ("ListBullet", "Calibration: per-student hit-rate, mean confidence, Overconfidence Index, and the "
                   "round-by-round trend (Cohort Analytics → Calibration)."),
    ("ListBullet", "Negotiation: full transcripts, concessions accepted, amounts committed, and "
                   "whether each promise was kept or broken (Session Viewer)."),
    ("ListBullet", "Financial literacy: the year-by-year statement of financial position now shows all "
                   "five years, with cash deficits presented as short-term debt, making it suitable for "
                   "a statement-reading exercise."),

    (H2, "Preparation note for instructors"),
    ("", "Before a teaching session, run the Dry-Run Simulator against the cohort configuration. It "
         "plays four archetypal strategies through the real engine and reports whether opposed "
         "strategies produce distinct, survivable outcomes. A configuration graded brutal will "
         "demoralise a novice group; one graded forgiving will not reward the ESG reasoning the "
         "course is teaching."),
]


# ════════════════════════════════════════════════════════════════════
# 4. FACILITATOR OPERATIONS MANUAL — runbook
# ════════════════════════════════════════════════════════════════════
OPERATIONS = [
    (H1, "Operational Additions (July 2026)"),

    (H2, "Pre-session checklist additions"),
    ("BodyText", "Add the following to the standard pre-session run-through."),
    ("BodyText", "Run a dry run. Command Centre → Dry-Run Simulator, select the cohort, three "
                 "repetitions, run. Confirm the difficulty grade is balanced or punishing rather than "
                 "brutal or forgiving, and read the warnings panel. This takes under a second and "
                 "catches configuration problems that would otherwise surface mid-class."),
    ("BodyText", "Confirm briefing media. If you are using videos, open the round-1 briefing as a "
                 "player and confirm the Read | Watch pill appears and the video plays. Videos are "
                 "referenced by URL, so a broken or private link fails at play time, not at "
                 "configuration time."),
    ("BodyText", "Confirm feature toggles for the cohort. Predictions and Confidence under "
                 "Pedagogical Scaffolding; Negotiation Rooms and the Black Swan Injector under "
                 "Analytics & Cohort Controls. Selecting an experience level presets these; verify "
                 "rather than assume, particularly on a cohort cloned from an earlier programme."),
    ("BodyText", "Confirm your capabilities. Negotiation Rooms require a per-facilitator grant from a "
                 "super admin; if the toggle is absent from your panel, you do not hold it."),

    (H2, "During the session"),
    ("BodyText", "Cohort Pulse gains a negotiating flag showing which team currently has a "
                 "negotiation room open and with which stakeholder. A team that has been in a room for "
                 "an extended period is usually deliberating rather than stuck — the room closes "
                 "automatically when they commit, so it cannot stall the round."),
    ("BodyText", "The teleprompter surfaces a calibration prompt each round where predictions are "
                 "enabled, for example noting how many teams predicted with high confidence and missed "
                 "every call. This is written to be read aloud."),
    ("BodyText", "Custom Black Swan injections are audited and the injection history is visible in "
                 "your panel, scoped to your own cohorts. The history now survives a backend restart."),

    (H2, "Debrief material"),
    ("BodyText", "Session Viewer, expanded card: negotiation transcripts per team — who they met, the "
                 "full exchange, what was conceded, what it cost, and the state of each promise (open, "
                 "kept, broken). A broken promise with its downstream price is usually the strongest "
                 "single teaching artefact the platform produces."),
    ("BodyText", "Cohort Analytics → Calibration: confidence-versus-accuracy scatter, cohort hit-rate "
                 "trend by round, and the most over- and under-confident teams."),

    (H2, "Troubleshooting"),
    (H3, "A control I expect is missing"),
    ("BodyText", "Most new features are gated twice: a per-cohort setting and, for Negotiation Rooms, "
                 "a per-facilitator capability. If a panel is absent rather than disabled, the "
                 "capability is not granted to your profile — ask a super admin."),
    (H3, "A settings change appeared to save but did nothing"),
    ("BodyText", "Cohort-settings responses now list keys refused for your role under "
                 "rejected_for_role. Previously such keys were discarded silently. If a change does not "
                 "take effect, that field will name it."),
    (H3, "I was told I lack permission for something I administer"),
    ("BodyText", "An expired session now reports “Session expired — please log in again” rather than a "
                 "permissions error. If you see a permissions message, it is genuinely a role or "
                 "capability issue. Facilitator sessions also survive a backend restart now."),
    (H3, "The negotiation room will not open"),
    ("BodyText", "Rooms open only for stakeholders at hostile or triggered stage; the refusal names "
                 "the current stage. Other limits: one room at a time, two meetings per round per team."),
]


# ════════════════════════════════════════════════════════════════════
# 5. DEPLOYMENT & INFRASTRUCTURE GUIDE
# ════════════════════════════════════════════════════════════════════
DEPLOYMENT = [
    (H1, "Deployment Changes (July 2026)"),

    (H2, "Session secret durability"),
    ("BodyText", "If JWT_SECRET is not present in the environment the platform previously generated an "
                 "ephemeral per-process secret, so every restart or redeploy invalidated all "
                 "facilitator sessions — while dashboards continued to render from cached client state, "
                 "making the failure look like a permissions problem."),
    ("BodyText", "A generated secret is now written once to the durable data directory as "
                 "jwt_secret.key with 0600 permissions and reused on subsequent starts. This makes a "
                 "mounted volume more important, not less: without one the file is lost on redeploy and "
                 "the old behaviour returns."),
    ("SourceCode", "JWT_SECRET=$(openssl rand -hex 32)     # recommended: set explicitly"),
    ("SourceCode", "JWT_EXPIRY_HOURS=8                     # default 2; raise for long workshops"),

    (H2, "Durable volume contents"),
    ("BodyText", "Set MURESSONS_DATA_DIR to a mounted volume (for example /data). The following "
                 "mutable files live there and must survive redeploys:"),
    ("SourceCode", "facilitator_registry.json    facilitator accounts + capability grants"),
    ("SourceCode", "token_versions.json          session revocation kill-switch"),
    ("SourceCode", "jwt_secret.key               generated session secret (new)"),
    ("SourceCode", "admin_audit.jsonl            audit trail incl. black-swan injection history (new)"),
    ("SourceCode", "rate_bans.json               rate-limit bans"),
    ("SourceCode", "memory_snapshot.json         in-memory-mode game state (offline runs only)"),
    ("BodyText", "Note that custom Black Swan injection history is now served from the audit trail "
                 "rather than process memory, so losing this volume loses that history and makes it "
                 "inconsistent between workers."),

    (H2, "Store selection and worker concurrency"),
    ("BodyText", "docker-start.sh defaults USE_MEMORY_DB to false, so a Railway deployment runs "
                 "against PostgreSQL unless explicitly overridden. The worker preflight clamps the "
                 "process count to one unless the shared store is active; set WEB_CONCURRENCY to scale "
                 "out only under PostgreSQL."),
    ("BodyText", "Endpoints that previously read the in-memory store directly have been ported to the "
                 "shared database API, and a test-suite tripwire fails the build if that pattern "
                 "returns. Two memory-only features (session cloning and post-creation paradigm "
                 "rewrite) return HTTP 501 with guidance under PostgreSQL rather than silently "
                 "appearing to succeed."),

    (H2, "Content-Security-Policy"),
    ("BodyText", "Briefing-video embeds require frame-src. Without it, iframes fall back to "
                 "default-src 'self' and the browser blocks the embed with the application's own "
                 "policy — the visible symptom is a “content is blocked” panel where the video should "
                 "be. The shipped policy in next.config.mjs now includes:"),
    ("SourceCode", "frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://player.vimeo.com"),
    ("SourceCode", "media-src 'self' blob: https:"),
    ("BodyText", "frame-ancestors 'none' is unchanged, so the application itself still cannot be framed."),

    (H2, "Optional LLM configuration"),
    ("BodyText", "The stakeholder negotiation dialogue layer is optional. With no key configured the "
                 "feature runs fully scripted and requires no external calls; configuring a key enables "
                 "in-persona improvisation only."),
    ("SourceCode", "LLM_PROVIDER=anthropic|openai     LLM_API_KEY=…     LLM_MODEL=…"),
    ("BodyText", "Cost and latency are bounded per turn: 500 max tokens, a 15-second timeout, at most "
                 "six turns per room and two rooms per team per round. Any failure degrades to the "
                 "scripted line rather than surfacing an error to the player."),

    (H2, "Healthcheck"),
    ("BodyText", "railway.json points the healthcheck at /api/health, served by the Next.js route "
                 "handler; the backend additionally exposes /health on its internal port. No change is "
                 "required, but note that the frontend route is the one Railway probes."),
]


# ════════════════════════════════════════════════════════════════════
# 6. API REFERENCE
# ════════════════════════════════════════════════════════════════════
API = [
    (H1, "API Additions and Changes (July 2026)"),

    (H2, "Player endpoints — negotiation rooms"),
    ("BodyText", "Base path /api/simulations. All require session ownership (X-Player-Id binding) and "
                 "the cohort's negotiation_rooms_enabled setting; they additionally re-check the owning "
                 "facilitator's capability, returning 403 when it has been revoked."),
    ("SourceCode", "POST /{session_id}/negotiation/open        {agent_id}"),
    ("SourceCode", "GET  /{session_id}/negotiation"),
    ("SourceCode", "POST /{session_id}/negotiation/say         {text}"),
    ("SourceCode", "POST /{session_id}/negotiation/accept      {concession_id}"),
    ("SourceCode", "POST /{session_id}/negotiation/walk-out"),
    ("BodyText", "open returns {room, menu}; the room carries persona, computed grievances, turns and "
                 "deals. say returns {room, menu, suggested_concession, mood} — suggested_concession is "
                 "advisory only and is always either null or an id already present in menu. accept "
                 "returns {deal, promise, room, menu}. walk-out and turn-limit closure return "
                 "{closed}. State-machine refusals (not hostile, room already open, meeting cap, "
                 "off-menu concession) return 422 with an error code and human-readable detail."),

    (H2, "Player endpoints — calibration"),
    ("SourceCode", "POST /{session_id}/predictions   {treasury_band, reputation_dir, confidence?, note?}"),
    ("SourceCode", "GET  /{session_id}/predictions?player_id="),
    ("BodyText", "treasury_band is one of down_big, down, flat, up, up_big; reputation_dir is one of "
                 "down, flat, up; at least one must be supplied. confidence is clamped to 0.5–1.0. "
                 "Submission is idempotent per (player, round). Records are scored post-tick and the "
                 "score object is added in place."),

    (H2, "Admin endpoints"),
    ("SourceCode", "POST /api/admin/dry-run                       {session_id, n_reps?, strategies?}"),
    ("SourceCode", "GET  /api/admin/calibration-analytics?session_id="),
    ("SourceCode", "GET  /api/admin/{session_id}/negotiation-transcripts"),
    ("SourceCode", "POST /api/admin/sessions/{session_id}/briefing-videos"),
    ("BodyText", "dry-run requires an authenticated facilitator and session ownership; it is a pure "
                 "read that returns a difficulty report and never mutates the cohort. "
                 "calibration-analytics and negotiation-transcripts are facilitator-guarded and scoped "
                 "to owned cohorts for non-admin callers. briefing-videos accepts "
                 "{briefing_video_base, briefing_videos} where the map is keyed by round number as a "
                 "string; blank entries are stripped."),

    (H2, "Changed semantics"),
    (H3, "Authentication versus authorisation"),
    ("BodyText", "require_super_admin, require_lead_facilitator and require_registry_admin now return "
                 "401 with detail “Session expired — please log in again” for anonymous callers, "
                 "before any role evaluation. A 403 from these guards now reliably means a role or "
                 "capability problem rather than an expired cookie."),
    (H3, "Cohort settings"),
    ("BodyText", "PATCH /api/admin/sessions/{id}/cohort-settings returns rejected_for_role alongside "
                 "the existing rejected_non_overridable. Keys the caller's role may not set were "
                 "previously discarded silently with a 200 response."),
    (H3, "Facilitator records"),
    ("BodyText", "Create, update, bulk-upload and login payloads carry "
                 "negotiation_rooms_enabled, a per-facilitator capability defaulting to false. It is "
                 "also accepted as a bulk-upload column."),
    (H3, "Global settings"),
    ("BodyText", "GET /api/admin/global-settings additionally exposes negotiation_rooms_enabled, "
                 "custom_black_swan_enabled, briefing_video_base and briefing_videos, each resolved "
                 "per cohort when session_id is supplied. briefing_video_base and briefing_videos are "
                 "also writable through PATCH /api/admin/global-settings."),
    (H3, "Custom black swan log"),
    ("BodyText", "GET /api/admin/custom-black-swan-log now requires a lead facilitator or above and "
                 "returns only events for cohorts the caller owns (admins see all). It is served from "
                 "the durable audit trail rather than process memory."),

    (H2, "Database API parity (internal)"),
    ("BodyText", "Both store implementations expose fetch_all_sessions_raw() — every session including "
                 "per-player children, which the leaderboard-oriented fetch_all_sessions excludes — and "
                 "fetch_all_decisions(). Application code must use the async database API rather than "
                 "the memory store's module globals; a test-suite tripwire enforces this."),
]


# ════════════════════════════════════════════════════════════════════
# 7. ASSESSMENT & SCORING GUIDE
# ════════════════════════════════════════════════════════════════════
ASSESSMENT = [
    (H1, "Assessment Additions (July 2026)"),

    (H2, "Calibration scoring"),
    ("BodyText", "Where the prediction gate is enabled, each player's pre-commit forecast is scored "
                 "against realised outcomes. Scoring is deterministic and runs after the engine tick; "
                 "it is read-only with respect to engine state and does not affect any simulation "
                 "result or existing score."),
    (H3, "Bands"),
    ("BodyText", "Treasury movement is classified into five bands: a change within ±$1M is flat, "
                 "beyond ±$1M up to ±$5M is down or up, and beyond ±$5M is down_big or up_big. "
                 "Reputation is classified as flat when the absolute change is under 2 points, "
                 "otherwise up or down. A prediction is a hit only on an exact band match."),
    (H3, "Confidence and the Brier term"),
    ("BodyText", "Where confidence is recorded, each predicted KPI contributes (confidence − hit)², "
                 "and the reported Brier value is the mean across predicted KPIs. This is a proper "
                 "scoring rule: a player minimises it by reporting their true belief, so overstating "
                 "confidence is penalised even on a correct call, and understating it is penalised "
                 "even on an incorrect one."),
    (H3, "Overconfidence Index"),
    ("BodyText", "Reported at game over as mean confidence minus mean hit-rate across all scored "
                 "rounds. Positive values indicate overconfidence, negative underconfidence; the "
                 "conventional reading is that values within ±0.10 represent good calibration."),
    (H3, "Using calibration in grading"),
    ("BodyText", "Calibration is intended as formative evidence rather than a graded score. If it is "
                 "assessed, assess the trajectory and the reflection rather than the absolute "
                 "hit-rate: a student who begins overconfident and converges toward the diagonal has "
                 "demonstrated the target learning, while a consistently accurate but "
                 "systematically overconfident student has not. Note also that only players who chose "
                 "to predict are scored — the gate is skippable by design."),

    (H2, "Negotiation as assessable evidence"),
    ("BodyText", "Negotiation rooms produce a durable, per-team record suitable for assessment: the "
                 "full transcript, each concession accepted with its price and the multiplier applied, "
                 "tolerance movement, and the lifecycle of every promise (open, kept, broken)."),
    ("BodyText", "Suggested criteria: whether the team read the stakeholder's actual mandate (did they "
                 "offer something that persona values?); whether they priced the obligation, not just "
                 "the cash cost; whether promises made were resourced in subsequent rounds; and how "
                 "they responded to a trust scar once incurred."),
    ("BodyText", "Available under Session Viewer for each team, and via the negotiation-transcripts "
                 "endpoint for export."),

    (H2, "Financial statement literacy"),
    ("BodyText", "The statement of financial position now presents cash deficits correctly: a negative "
                 "cash position is swept into short-term debt and charged interest, rather than being "
                 "displayed as negative cash against zero borrowings. Total liabilities, gearing, "
                 "liquidity and covenant readings are therefore internally consistent, and the "
                 "statement is now suitable for a statement-reading or ratio-analysis exercise."),
    ("BodyText", "The year-by-year statement shows all five years, including for sessions that began "
                 "before this change, allowing students to trace how a position accumulated."),
]


# ════════════════════════════════════════════════════════════════════
# 8. DEVELOPER CHEATSHEET
# ════════════════════════════════════════════════════════════════════
CHEATSHEET = [
    (H1, "July 2026 — Conventions and New Modules"),

    (H2, "Store access: use the database API, never the memory globals"),
    ("BodyText", "PostgreSQL is the deployment default. Reading the memory store's private "
                 "dictionaries returns empty data there, silently, with a 200 response."),
    ("SourceCode", "# WRONG — empty under PostgreSQL, no error"),
    ("SourceCode", "sessions = getattr(db, '_sessions', {})"),
    ("SourceCode", "import database_memory; rows = database_memory._global_states[sid]"),
    ("SourceCode", ""),
    ("SourceCode", "# RIGHT"),
    ("SourceCode", "sessions = await db.fetch_all_sessions_raw()   # incl. player child sessions"),
    ("SourceCode", "latest   = await db.fetch_latest_state(sid)"),
    ("SourceCode", "history  = await db.fetch_round_history(sid)"),
    ("SourceCode", "decs     = await db.fetch_all_decisions()"),
    ("BodyText", "tests/test_store_access_tripwire.py fails on getattr(db, '_…') and on references to "
                 "_global_states, _bu_states, _decision_log or _round_states outside the store modules. "
                 "Reads of the _sessions mirror are legal (PostgreSQL hydrates it). For a genuinely "
                 "memory-only feature, guard it with _in_memory_backend_active() and a 501, then mark "
                 "the block with a tripwire-allow comment."),

    (H2, "Per-round state must be written twice"),
    ("BodyText", "The memory store unpacks flag keys to the top level of global state on read and "
                 "re-packs on write, with top-level values winning. Writing only the flags copy is "
                 "therefore silently overwritten by the stale top-level copy."),
    ("SourceCode", "flags['predictions_log'] = log"),
    ("SourceCode", "gs['predictions_log']    = log     # both, always"),

    (H2, "Role decisions: level, not string"),
    ("BodyText", "god_mode and project_admin are virtual identities with no registry record. Deriving "
                 "a role from the registry silently demotes them to “facilitator”, which has already "
                 "caused a delivery bug (admin broadcast reaching nobody) and a broken capability gate."),
    ("SourceCode", "# WRONG"),
    ("SourceCode", "role = get_role(caller_fac) if caller_fac else 'facilitator'"),
    ("SourceCode", "if role == 'super_admin': ..."),
    ("SourceCode", ""),
    ("SourceCode", "# RIGHT"),
    ("SourceCode", "role = get_fac_role(request)"),
    ("SourceCode", "if is_admin_role(role): ...        # level-based, includes god_mode"),
    ("BodyText", "Related: when a role filter refuses a key, report it (rejected_for_role) rather than "
                 "dropping it — a settings write that returns 200 and changes nothing is worse than an "
                 "error."),

    (H2, "New modules"),
    ("SourceCode", "backend/negotiation.py        room state machine, concession whitelist, pricing"),
    ("SourceCode", "backend/llm_negotiator.py     optional dialogue layer (validated, non-authoritative)"),
    ("SourceCode", "backend/dry_run.py            bot playthrough + difficulty report"),
    ("BodyText", "negotiation.say() accepts an optional pre-validated llm_reply and re-checks the "
                 "concession id itself; the accept path is the only route to state and always re-runs "
                 "whitelist validation. dry_run must be called on the event loop with the process RNG "
                 "state saved and restored — it seeds the global random module."),

    (H2, "Commit path hooks"),
    ("BodyText", "_commit_turn_impl runs three post-tick, exception-isolated steps that must never "
                 "fail a commit: negotiation room auto-close, calibration scoring (reads realised "
                 "deltas, writes only the predictions log), and the existing engine batch. New hooks "
                 "should follow the same pattern — wrapped, logged, never raising."),

    (H2, "Verification recipes"),
    ("SourceCode", "USE_MEMORY_DB=true MURESSONS_DATA_DIR=/tmp/x python -m pytest tests/ -q"),
    ("SourceCode", "python -m pytest tests/test_store_access_tripwire.py -q      # store parity"),
    ("SourceCode", "python -m pytest tests/test_role_hierarchy_sync.py -q        # RBAC drift"),
    ("SourceCode", "python -m pytest tests/test_negotiation_llm.py -q            # injection suite"),
    ("SourceCode", "MURESSONS_REBASELINE_GOLDEN=1 python -m pytest tests/test_stakeholder_golden_trace.py"),
    ("BodyText", "For any change that could touch engine behaviour, run a seed-pinned control: pin "
                 "random.seed and the session's shuffle_seed, play identical decisions with the feature "
                 "on and off, and diff the per-round KPI tuples. This is how calibration, negotiation "
                 "rooms and the dry run were each proven inert with respect to engine outcomes."),
]


JOBS = [
    ("Muressons_Pathway_Map.docx", PATHWAY),
    ("Muressons_Stakeholder_Module_Reference.docx", STAKEHOLDER),
    ("Muressons_MBA_Course_Syllabus.docx", SYLLABUS),
    ("Muressons_Facilitator_Operations_Manual.docx", OPERATIONS),
    ("Muressons_Deployment_Infrastructure_Guide.docx", DEPLOYMENT),
    ("Muressons_API_Reference.docx", API),
    ("Muressons_Assessment_and_Scoring_Guide.docx", ASSESSMENT),
    ("Muressons_Developer_Cheatsheet.docx", CHEATSHEET),
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
