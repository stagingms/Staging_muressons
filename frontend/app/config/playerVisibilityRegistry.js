/**
 * playerVisibilityRegistry.js — SINGLE source of truth for the PLAYER-facing
 * visibility catalog.
 *
 * WHY THIS FILE EXISTS
 * --------------------
 * The facilitator catalog was consolidated into analyticsRegistry.js after the
 * Railway §4.3 audit found the same keys hand-maintained in two arrays with
 * separately-worded tooltips. The player catalog had the identical problem and
 * had already drifted further:
 *
 *   CreateCohortModal.PLAYER_ANALYTICS     19 keys
 *   AnalyticsControlPanel.PLAYER_ANALYTICS  3 keys
 *
 * and AnalyticsControlPanel built its DEFAULT_VIS map from its own short list,
 * so saving from that panel wrote a player map missing sixteen keys. Both
 * surfaces now import from here, so a key exists once.
 *
 * The backend dict `_analytics_visibility["player"]` in admin_analytics.py stays
 * authoritative — its setters silently DROP unknown keys, so a key added only
 * here can never persist. `__tests__/player-visibility-registry.test.js` fails
 * if the two key sets diverge.
 *
 * Fields:
 *   key      — visibility key; isPlayerVisible(key) gates the surface
 *   label    — what the facilitator reads in the Create-Cohort form
 *   icon     — leading glyph in that form
 *   group    — section heading, purely for form layout
 *   tooltip  — hover copy; states any gate that COMPOSES with this switch
 *   default  — false only where the surface ships off; omitted means visible
 *
 * ADDING A SURFACE: add the key here, add it to the backend dict in the same
 * commit, and wrap the render site in isPlayerVisible(key). The test enforces
 * all three.
 *
 * A SWITCH IS A VETO, NOT AN OVERRIDE. Every key composes with whatever already
 * limits the surface — a round-number floor, an engine-module toggle, its own
 * legacy flag. Turning a switch on does not force a Round-9 panel to appear in
 * Round 2; turning it off reliably hides the surface. That direction is the one
 * a facilitator depends on, and isPlayerVisible is fail-open, so a failed
 * settings fetch shows everything rather than blanking a cockpit.
 */

export const PLAYER_VISIBILITY_CARDS = [
    // ── Core analytics ──
    { key: 'peer_benchmarking', label: 'Peer Benchmarking', icon: '🏆', tooltip: 'Shows the player their anonymous percentile ranking vs. the cohort for Treasury, Reputation, and Synergy. Includes bar visualizations with their value compared against the cohort average. Answers: "How do I rank among my peers?"', group: 'Core analytics', audience: 'compare' },
    { key: 'decision_impact', label: 'Decision Impact', icon: '🧠', tooltip: 'Per-round KPI attribution — shows how each choice affected Treasury, Reputation, and Synergy with colour-coded delta badges (+/-) and a narrative explanation of the outcome. Answers: "What impact did my decisions actually have?"', group: 'Core analytics', audience: 'insight' },
    { key: 'what_if_simulator', label: 'What-If Simulator', icon: '📈', tooltip: 'Counterfactual analysis — shows what would have happened if the player had chosen the most popular alternative option. Displays projected Treasury and Reputation diffs. Only appears when choices differ from the majority. Disabled by default.', group: 'Core analytics', default: false, audience: 'metacog' },
    // ── Performance & history ──
    { key: 'kpi_dashboard', label: 'KPI Dashboard', icon: '📟', tooltip: 'The player\'s personal KPI cockpit — Treasury, Reputation, Synergy, EBITDA and ESG headline metrics with round-on-round deltas. Answers: "Where do I stand right now?"', group: 'Performance & history', audience: 'core' },
    { key: 'decision_history', label: 'Decision History', icon: '🕰️', tooltip: 'A log of the player\'s own past decisions with the rationale captured and the outcome that followed. Answers: "What have I chosen so far and why?"', group: 'Performance & history', audience: 'core' },
    { key: 'consequence_timeline', label: 'Consequence Timeline', icon: '⏳', tooltip: 'Shows consequences unfolding across future rounds from earlier decisions (delayed effects, compounding debt). Answers: "What did my past choices set in motion?"', group: 'Performance & history', audience: 'insight' },
    { key: 'stock_performance', label: 'Stock Performance', icon: '📉', tooltip: 'Share-price / enterprise-value chart tracking the market\'s valuation of the player\'s company over the ten rounds. Answers: "Is the market rewarding my strategy?"', group: 'Performance & history', audience: 'insight' },
    { key: 'balanced_scorecard', label: 'Balanced Scorecard', icon: '🎯', tooltip: 'Sustainability balanced scorecard across financial, customer, internal-process and learning/ESG perspectives. Advanced pedagogy. Disabled by default.', group: 'Performance & history', default: false, audience: 'specialist' },
    // ── Risk & strategy lenses ──
    { key: 'risk_radar', label: 'Risk Radar', icon: '🕸️', tooltip: 'Multi-axis radar of the player\'s current risk exposure (carbon, natural-capital, social-licence, governance, liquidity). Answers: "Where am I fragile?"', group: 'Risk & strategy lenses', audience: 'insight' },
    { key: 'esg_leadership', label: 'ESG Leadership Profile', icon: '🌱', tooltip: 'Profiles the player\'s ESG leadership style from the pattern of decisions taken across the run. Reflective debrief tool. Disabled by default.', group: 'Risk & strategy lenses', default: false, audience: 'specialist' },
    { key: 'competitor_intel', label: 'Competitor Intel', icon: '🔭', tooltip: 'Rival-intelligence cards giving partial, fog-of-war signals about other teams\' moves. Disabled by default (competitive cohorts only).', group: 'Risk & strategy lenses', default: false, audience: 'compare' },
    // ── Reports & engagement ──
    { key: 'annual_report', label: 'Annual Report', icon: '📕', tooltip: 'A narrative annual report generated from the player\'s results — financials, ESG highlights, and board commentary. Answers: "How does my year read as a story?"', group: 'Reports & engagement', audience: 'core' },
    { key: 'achievement_badges', label: 'Achievement Badges', icon: '🏅', tooltip: 'Gamified milestone badges earned for strategic and sustainability achievements during the run. Drives engagement.', group: 'Reports & engagement', audience: 'flourish' },
    { key: 'regret_meter', label: 'Regret Meter', icon: '😬', tooltip: 'A counterfactual "regret" gauge estimating value left on the table versus the best available path. Reflective tool. Disabled by default.', group: 'Reports & engagement', default: false, audience: 'metacog' },
    { key: 'glossary', label: 'Glossary', icon: '📖', tooltip: 'In-game technical glossary explaining KPIs, engines, and sustainability terminology on demand. Answers: "What does this term mean?"', group: 'Reports & engagement', audience: 'core' },
    // ── Right-hand context rail ──
    // The rail's tabs are player-facing surfaces like any other panel but were
    // missing from this list, so a facilitator could not switch them off. The
    // 'Decisions' tab is deliberately absent: it renders DecisionHistory and is
    // gated by the existing `decision_history` toggle above (one surface, one
    // switch — a duplicate key would let the two disagree).
    { key: 'rail_mailbox', label: 'Rail · Mailbox', icon: '📬', tooltip: 'The right-hand rail\'s Executive Mailbox tab — board memos, stakeholder letters and injected messages. Turn off for a stripped-back cockpit or when running the narrative offline.', group: 'Context rail', audience: 'core' },
    { key: 'rail_engines', label: 'Rail · Engines', icon: '🌎', tooltip: 'The right-hand rail\'s Engines tab — live engine widgets showing contagion, talent and systemic-risk state. Advanced; hide for introductory cohorts.', group: 'Context rail', audience: 'specialist' },
    { key: 'rail_climate', label: 'Rail · Climate', icon: '🌡️', tooltip: 'The right-hand rail\'s Climate tab — the TCFD scenario dashboard. Hide when the cohort is not running the climate-disclosure thread.', group: 'Context rail', audience: 'specialist' },
    { key: 'market_reality_feed', label: 'Market Reality Feed', icon: '📡', tooltip: 'The rail\'s live market/consequence feed with traceability back to the decisions that caused each event. Hide to reduce ambient noise during focused decision rounds.', group: 'Context rail', audience: 'narrative' },

    // ── End of game & debrief ──
    { key: 'boardroom_showdown', label: 'Boardroom Moment / Showdown', icon: '🏛️', group: 'End of game & debrief', tooltip: 'Final 3-phase board exercise: motion briefing, pick a recommendation, write the next-decade plan.', audience: 'debrief' },
    { key: 'archetype_reveal', label: 'Archetype Reveal', icon: '🎭', group: 'End of game & debrief', tooltip: 'Cinematic R10 reveal of their leadership archetype and terminal valuation.', audience: 'debrief' },
    { key: 'mirror_debrief', label: 'Mirror Debrief', icon: '🪞', group: 'End of game & debrief', tooltip: 'The single highest-impact counterfactual — what one choice cost them.', audience: 'debrief' },
    { key: 'rewind_ribbon', label: 'Rewind Ribbon', icon: '⏪', group: 'End of game & debrief', tooltip: 'Animated ribbon of every M_R-bearing decision, captured vs missed.', audience: 'debrief' },
    { key: 'mr_ladder_reveal', label: 'M_R Ladder Reveal', icon: '🪜', group: 'End of game & debrief', tooltip: 'Stacking animation of each Regenerative Multiple component with BLOCKED/MISSED tags.', audience: 'debrief' },
    { key: 'archetype_card', label: 'Shareable Archetype Card', icon: '🖼️', group: 'End of game & debrief', tooltip: 'Branded keepsake card with M_R, EV, share price, equity-wipeout stamp.', audience: 'flourish' },
    { key: 'three_key_insights', label: '3 Key Insights', icon: '💡', group: 'End of game & debrief', tooltip: 'Best Decision / Most Costly Decision / Sharpest Reputation Swing, from the round-by-round record. Renders nothing when the run cannot separate a best from a worst.', audience: 'debrief' },
    { key: 'calibration_report', label: 'Calibration Report', icon: '🎰', group: 'End of game & debrief', tooltip: 'Stated confidence vs actual hit rate, with an overconfidence index.', audience: 'metacog' },
    { key: 'ceo_interview', label: 'CEO Interview & Assessment', icon: '🎤', group: 'End of game & debrief', tooltip: 'Oral-exam modal about their run, with a graded assessment. Also requires the facilitator to have authored interview questions.', audience: 'debrief' },
    { key: 'student_report_export', label: 'Student Report Export', icon: '📤', group: 'End of game & debrief', tooltip: 'Downloadable strategy report: performance, decision timeline, BU performance.', audience: 'debrief' },
    { key: 'front_page_reveal', label: 'Front Page Reveal', icon: '📰', group: 'End of game & debrief', tooltip: 'Fake newspaper front page of their run, exportable as PNG. Also respects the existing front_page_enabled global flag.', audience: 'flourish' },
    { key: 'side_track_results', label: 'Side Track Results', icon: '🛤️', group: 'End of game & debrief', tooltip: 'Grade, archetype and M_R bonus/penalty for each completed side track. Only appears for side tracks the player actually completed.', audience: 'debrief' },
    // ── Valuation & causal analytics ──
    { key: 'consequence_dna', label: 'Consequence DNA', icon: '🧬', group: 'Valuation & causal analytics', tooltip: 'Inline causal chains linking past decisions to currently active flags. Only from Round 4.', audience: 'causal' },
    { key: 'consequence_dna_sankey', label: 'Consequence DNA Sankey', icon: '🌊', group: 'Valuation & causal analytics', tooltip: 'Full Sankey of decision to consequence flows. Only from Round 4.', audience: 'specialist' },
    { key: 'esg_constellation_3d', label: '3D ESG Constellation', icon: '🌌', group: 'Valuation & causal analytics', tooltip: '3D causal-chain constellation across all rounds. Only from Round 4.', audience: 'specialist' },
    { key: 'terminal_valuation_calc', label: 'Terminal Valuation Estimator', icon: '📊', group: 'Valuation & causal analytics', tooltip: 'Live enterprise value, net debt and equity value in the finale rounds. Only from Round 9.', audience: 'finance' },
    { key: 'synergy_tracker', label: 'Synergy Multiplier Tracker', icon: '🔗', group: 'Valuation & causal analytics', tooltip: 'Synergy multiplier with workforce-readiness modifier. Only from Round 7.', audience: 'finance' },
    { key: 'ebitda_waterfall', label: 'EBITDA Waterfall', icon: '💧', group: 'Valuation & causal analytics', tooltip: 'Waterfall from revenue through OPEX, crisis cost and carbon tax to EBITDA.', audience: 'finance' },
    { key: 'balance_sheet_modal', label: 'Balance Sheet & Covenants', icon: '📒', group: 'Valuation & causal analytics', tooltip: 'Full balance sheet with D/E and a covenant traffic light. Only when the engine emits a balance sheet.', audience: 'finance' },
    { key: 'consequence_replay', label: 'Consequence Replay', icon: '🎞️', group: 'Valuation & causal analytics', tooltip: 'Animated causal chain from their commit to its outcomes. Also respects the existing consequence_replay_enabled flag.', audience: 'causal' },
    { key: 'benchmarks_panel', label: 'FTSE 100 ESG Benchmarks', icon: '📈', group: 'Valuation & causal analytics', tooltip: 'Percentile gauges against FTSE-100 ESG benchmarks. Only from Round 2.', audience: 'finance' },
    { key: 'living_planet_globe', label: 'Living Planet Globe', icon: '🌍', group: 'Valuation & causal analytics', tooltip: 'Animated planet-health globe: temperature, biosphere, people.', audience: 'insight' },
    // ── Prediction & reflection ──
    { key: 'prediction_prompts', label: 'Predict Before You Commit', icon: '🔮', group: 'Prediction & reflection', tooltip: 'The two free-text prediction prompts inside the review-and-commit step. Named for the prompts, not the modal: that modal also carries the ONLY commit button, so it is never hidden — switching this off leaves a plain review-and-commit step. Note the separate pedagogical \'Prediction Gates\' toggle does not currently gate this surface; this switch does.', audience: 'metacog' },
    { key: 'prediction_comparison', label: 'Prediction vs Reality', icon: '⚖️', group: 'Prediction & reflection', tooltip: 'Scores their pre-commit prediction against the actual result.', audience: 'metacog' },
    { key: 'quick_reflection_box', label: 'Quick Reflection box', icon: '💭', group: 'Prediction & reflection', tooltip: 'Optional free-text reflection before advancing.', audience: 'metacog' },
    { key: 'reflective_prompt', label: 'Reflective Nudge card', icon: '🤔', group: 'Prediction & reflection', tooltip: 'One coaching question keyed to the round tier.', audience: 'scaffold' },
    // ── Narrative & stakeholders ──
    { key: 'briefing_video', label: 'Briefing: Watch (video)', icon: '🎬', group: 'Narrative & stakeholders', tooltip: 'The Read | Watch choice on each round briefing. Off makes the cohort read-only even where briefing video URLs are configured — useful for a room with no audio, a bandwidth-limited cohort, or when you want everyone on the written text. Composes with the URL config: Watch still only appears for rounds that actually have a video.', audience: 'scaffold' },
    { key: 'briefing_theory_card', label: 'Briefing: Academic Framework', icon: '📚', group: 'Narrative & stakeholders', tooltip: 'Academic framing (CSRD, Mendelow, ILO) woven into the briefing. Also respects the existing briefing_theory_enabled flag (off by default).', audience: 'scaffold' },
    { key: 'briefing_stakeholder_voices', label: 'Briefing: Stakeholder Voices', icon: '💬', group: 'Narrative & stakeholders', tooltip: 'In-character stakeholder quotes about this round.', audience: 'narrative' },
    { key: 'briefing_midgame_valuation', label: 'Briefing: Mid-Game Valuation', icon: '📉', group: 'Narrative & stakeholders', tooltip: 'Low-to-high terminal value range based on trajectory. Only after Round 5.', audience: 'finance' },
    { key: 'briefing_butterfly_hints', label: 'Briefing: Butterfly Hints', icon: '🦋', group: 'Narrative & stakeholders', tooltip: 'Hints that earlier choices are now compounding.', audience: 'narrative' },
    { key: 'briefing_last_round_recap', label: 'Briefing: Last Round Recap', icon: '📋', group: 'Narrative & stakeholders', tooltip: 'Collapsible recap of last round\'s decision and treasury impact. Only from Round 2.', audience: 'scaffold' },
    { key: 'ceo_diary', label: 'CEO Diary', icon: '📔', group: 'Narrative & stakeholders', tooltip: 'In-character diary entry narrating the round.', audience: 'narrative' },
    { key: 'round_retrospect', label: 'What Happened This Round / Road Not Taken', icon: '🔍', group: 'Narrative & stakeholders', tooltip: 'Grouped risk, financial and ESG events plus the regret line.', audience: 'narrative' },
    { key: 'stakeholder_agent_panel', label: 'Autonomous Stakeholder Agents', icon: '🤖', group: 'Narrative & stakeholders', tooltip: 'Each agent\'s escalation stage, tolerance, actions taken and cascades fired.', audience: 'narrative' },
    { key: 'market_intel_cards', label: 'Market News & Rating Actions', icon: '📰', group: 'Narrative & stakeholders', tooltip: 'Rival press items and credit-rating upgrade/downgrade cards. Nested inside the Mailbox rail tab, so rail_mailbox hides it too.', audience: 'narrative' },
    { key: 'player_annotations', label: 'Facilitator Annotations', icon: '📝', group: 'Narrative & stakeholders', tooltip: 'The facilitator\'s per-round notes addressed to this player.', audience: 'scaffold' },
    { key: 'flag_dependency_warnings', label: 'Flag Dependency Warnings', icon: '🚩', group: 'Narrative & stakeholders', tooltip: 'Explains which active flags are constraining this round.', audience: 'scaffold' },
    // ── Help & reference ──
    { key: 'ai_advisor', label: 'AI Strategic Advisor', icon: '🧠', group: 'Help & reference', tooltip: 'AI chat assistant answering strategy questions mid-round.', audience: 'scaffold' },
    { key: 'podcast_player', label: 'Boardroom Briefing Podcast', icon: '🎧', group: 'Help & reference', tooltip: 'Audio briefing player with a bonus-points incentive.', audience: 'scaffold' },
    { key: 'learning_hub', label: 'Learning Hub notebooks', icon: '📚', group: 'Help & reference', tooltip: 'NotebookLM-style notebooks with podcast, quiz and review actions.', audience: 'scaffold' },
    { key: 'resources_sidebar', label: 'Resources Library', icon: '📁', group: 'Help & reference', tooltip: 'Searchable per-round resource library with new-this-round and archive.', audience: 'scaffold' },
    { key: 'detailed_option_descriptions', label: 'Detailed Option Descriptions', icon: '🔎', group: 'Help & reference', tooltip: 'Long-form description, cost and impacts for each option on hover.', audience: 'scaffold' },
    // ── Dock & ambient ──
    { key: 'dock_sdg_radar', label: 'Dock: SDG Alignment Radar', icon: '🌐', group: 'Dock & ambient', tooltip: 'Group SDG score and per-goal radar, shown for every paradigm. Shown for every paradigm today.', audience: 'specialist' },
    { key: 'market_ticker', label: 'Market Ticker', icon: '📡', group: 'Dock & ambient', tooltip: 'Scrolling engine-derived symbols: carbon fee, WACC and similar.', audience: 'compare' },
    { key: 'decision_pressure_timer', label: 'Decision Pressure Timer', icon: '⏲️', group: 'Dock & ambient', tooltip: 'Countdown plus how many rival teams have already committed.', audience: 'compare' },
];

/** Every player visibility key, in form order. */
export const PLAYER_VISIBILITY_KEYS = PLAYER_VISIBILITY_CARDS.map((c) => c.key);

/**
 * The default visibility map. Mirrors the backend defaults: a key ships visible
 * unless it carries `default: false`. Used by AnalyticsControlPanel as its
 * pre-fetch placeholder — it must cover EVERY key, because that panel PUTs the
 * whole map and a missing key would silently drop a surface's setting.
 */
export const PLAYER_VISIBILITY_DEFAULTS = Object.fromEntries(
    PLAYER_VISIBILITY_CARDS.map((c) => [c.key, c.default !== false]),
);


// ── Audience tiers ──────────────────────────────────────────────────────────
/**
 * Every card carries exactly ONE `audience` tag, and each scenario preset
 * declares the SET of tags it shows (backend `_scenario_presets[].default_audiences`).
 *
 * WHY TAGS RATHER THAN A TABLE. The direct schema is four booleans per key —
 * 65 × 4 = 260 hand-maintained cells. That is the same shape as every drift bug
 * this area has produced: a 3-key list against a 19-key one, a toggle offered
 * but not persistable, a dropdown offering a value the validator rejects. A
 * 260-cell table maintained by hand drifts within two features. With tags, a new
 * surface is ONE word and it lands correctly in all four presets automatically,
 * because the profiles are DERIVED from this catalog rather than duplicating it.
 *
 * The presets already advertised these postures in their own subtitles —
 * "Foundation Visibility", "Progressive Disclosure", "Full Visibility",
 * "No Scaffolding" — while every cohort in fact got the identical panel set.
 * This is what makes the subtitles true.
 */
export const AUDIENCE_TAGS = [
    'core',         // the instruments nobody can play without
    'scaffold',     // teaching support; the group experienced participants find patronising
    'narrative',    // the simulation's texture — diary, stakeholders, market news
    'insight',      // light analytics answering "where do I stand", no finance background needed
    'finance',      // instruments that assume a finance vocabulary
    'causal',       // decision-to-consequence tracing; needs rounds behind it to read
    'specialist',   // powerful and easy to get lost in — Sankeys, 3D, scorecards, engine rails
    'compare',      // peer ranking and competitive pressure
    'metacog',      // prediction, calibration, regret — requires willingness to be shown you were wrong
    'debrief',      // the end-of-game payoff
    'flourish',     // engagement machinery that reads as gimmick to a senior room
];

/**
 * The player visibility map a set of audience tags implies.
 *
 * Derived, never hand-written: a card whose tag is not in the set is hidden.
 * Used at cohort creation to seed the override map from the chosen experience
 * level. It is a STARTING POINT, not a policy — the facilitator's own edits win,
 * and are never recomputed from the preset afterwards.
 */
export function visibilityForAudiences(tags) {
    const on = new Set(tags || []);
    return Object.fromEntries(
        PLAYER_VISIBILITY_CARDS.map((c) => [c.key, on.has(c.audience)]),
    );
}

/** Cards grouped by audience tag — for explaining a preset in the form. */
export function cardsByAudience() {
    const out = {};
    for (const c of PLAYER_VISIBILITY_CARDS) (out[c.audience] ||= []).push(c);
    return out;
}

/** Cards grouped by `group`, preserving declaration order, for form rendering. */
export function playerVisibilityGroups() {
    const out = [];
    for (const card of PLAYER_VISIBILITY_CARDS) {
        const g = card.group || 'Other';
        let bucket = out.find((b) => b.group === g);
        if (!bucket) { bucket = { group: g, cards: [] }; out.push(bucket); }
        bucket.cards.push(card);
    }
    return out;
}
