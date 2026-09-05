/**
 * Unified Sidebar Configuration
 * Single source of truth for both God Mode and Facilitator sidebar navigation.
 * Generates role-filtered tab lists using the 3-tier RBAC model.
 *
 * TOOLTIP CONVENTION (Phase R1 / V2-7): a tooltip must describe what the tab
 * actually RENDERS today — never planned or aspirational capability. Three
 * separate audits (G7, Phase 6 timeline, V2-1 leaderboard) each found a
 * tooltip promising features the tab didn't have. When you change what a tab
 * contains, update its tooltip in the same commit.
 *
 * LIVE-ROUND SUBSET (UX audit #13): an item carrying `liveRound: true` is one a
 * facilitator reaches for WHILE a round is being run in the room. The flag is
 * presentation only — it never widens access, and it is applied AFTER role
 * filtering (see filterSidebarForLiveRound). Keep the set TIGHT: the whole
 * point of the mode is fewer surfaces, so analytics, configuration and
 * reference tabs stay out even when they are useful before or after a round.
 * Same discipline as the tooltip convention above — if a tab stops being a
 * during-the-round tool, drop its flag in the same commit.
 *
 * Architecture (Audit §9.1):
 *   admin_shared.py  ─── ROLE_ALLOWED_TABS (backend enforcement)
 *   sidebarConfig.js ─── Tab definitions + role filtering (frontend display)
 */

// ═══════════════════════════════════════════════════════════════
//  GOD MODE SIDEBAR
// ═══════════════════════════════════════════════════════════════

export const GOD_MODE_SIDEBAR = [
    {
        category: 'Command Center',
        icon: '📡',
        id: 'command_center',
        items: [
            { id: 'system_overview',     label: 'System Overview',       icon: '📊', tooltip: 'Unified dashboard of system status, session health, and pedagogical scaffolding controls' },
            { id: 'platform_analytics',  label: 'Platform Analytics',    icon: '📈', tooltip: 'Aggregated macro statistics across all active cohorts with drill-down capability' },
            // O2: Tab ID is 'god_activity_log' (not 'activity_log') to prevent
            // collision with the Facilitator sidebar which uses 'activity_log'
            // for a completely different component (Session Management + local log).
            { id: 'god_activity_log',    label: 'Activity & Complexity', icon: '📋', tooltip: 'Immutable audit trail and live firehose of systemic interactions and complexity events' },
        ]
    },
    {
        category: 'Cohort Orchestration',
        icon: '🎓',
        id: 'orchestration',
        items: [
            { id: 'facilitator_registry', label: 'Facilitator Registry', icon: '👥', tooltip: 'Manage facilitators: create, edit roles (Super Admin / Lead / Facilitator), set permissions and cohort limits' },
            { id: 'cohort_provisioning',  label: 'Cohort Provisioning',  icon: '🗂️', tooltip: 'Provision and manage cohort sessions, assign facilitators, and configure paradigms' },
            // G7/Phase 6: the tab now contains what the original tooltip always
            // promised — broadcasts AND per-cohort round pacing.
            { id: 'session_controls',     label: 'Session Controls',     icon: '🎛️', tooltip: 'Universal broadcasts to every active cohort, plus per-cohort round pacing (free play / manual / scheduled)' },
            { id: 'master_interventions', label: 'Team Interventions',   icon: '🚀', tooltip: 'Directly inject capital, penalties, or narrative events into target teams' },
            { id: 'crisis_overrides',     label: 'Crisis Overrides',     icon: '🚨', tooltip: 'Manually activate crises, deploy preset Black Swans, or trigger end-game pathways. (The CUSTOM Black Swan Injector now lives on the facilitator dashboard, unlocked per cohort.)' },
            { id: 'decision_timeline',    label: 'Decision History',     icon: '🕰️', tooltip: 'Chronological audit trail of every decision across all sessions with KPI deltas and CapEx breakdowns' },
            { id: 'debrief_view',         label: 'Round Debrief',        icon: '📝', tooltip: 'Round-by-round debrief reports with performance trends and critical analysis for facilitator use' },
        ]
    },
    {
        category: 'Engine Configuration',
        icon: '⚙️',
        id: 'engine_core',
        items: [
            { id: 'macro_economics',     label: 'Macro Economics',      icon: '🔧', tooltip: 'Adjust global economic baselines, scenario presets, and override master variables' },
            { id: 'sim_switchboard',     label: 'Sim Switchboard',      icon: '🛤️', tooltip: 'Toggle the Advanced Climate Engine, adjust carbon/hostility/Scope-3 parameters, and enable Side Track Simulations globally. Also holds the cohort settings matrix, the simulation-config uploader, and Live Engine Configuration — which reads the values the running process is ACTUALLY using and names every way they disagree with what was configured.' },
            { id: 'systemic_risk_controls', label: 'Systemic Risk',      icon: '🌡️', tooltip: 'Toggle Black Swan events, NPC cascades, tipping points, and foreshadowing signals. Difficulty tier is set per-cohort via Experience Level.' },
            { id: 'materiality_config',  label: 'Materiality Matrix',   icon: '🦭', tooltip: 'Configure double materiality weightings — global defaults that facilitators inherit' },
            { id: 'stakeholder_config',  label: 'Stakeholder Config',   icon: '👥', tooltip: 'Edit stakeholder profiles per geographic region — power, interest, quadrant, and engagement tactics' },
            { id: 'pillar_config',       label: 'Pillar Configurator',  icon: '🏛️', tooltip: 'Manage strategic pillar areas per industry vertical — add custom decision areas and override standard ones' },
            { id: 'archetype_editor',    label: 'Profile Archetypes',   icon: '🏆', tooltip: 'Define Year 5 outcome profiles based on Regenerative Multiple (M_R) thresholds' },
            { id: 'scorecard_evaluator', label: 'Scorecard Evaluator',  icon: '📊', tooltip: 'Interactive whiteboard for demonstrating the Triple Bottom Line scorecard weighting formula' },
            // esg_weights moved to the Facilitator sidebar (Analytics & Assessment),
            // open to all facilitators — no longer a God Mode tab.
            { id: 'regulatory_sandbox',  label: 'Regulatory Sandbox',   icon: '⚖️', tooltip: 'Inject Pigou taxes, Coase bargaining, and Ostrom governance instruments into live sessions to test systemic resilience' },
        ]
    },
    {
        category: 'Resources & Content',
        icon: '📚',
        id: 'content',
        items: [
            { id: 'resources',          label: 'Resource Library',    icon: '📁', tooltip: 'Manage unlockable swipe files, PDFs, and in-game glossary definitions for teams' },
            { id: 'doc_reference',      label: 'Documentation',       icon: '📑', tooltip: 'Developer documentation, simulation reference, and engine mechanics guide' },
        ]
    },
    {
        category: 'Danger Zone',
        icon: '☢️',
        id: 'danger',
        items: [
            { id: 'system_export',  label: 'Backup & Export', icon: '💾', tooltip: 'Download comprehensive simulation snapshots for backup or compliance reporting' },
            { id: 'session_reset',  label: 'Factory Reset',   icon: '💥', tooltip: 'Hard wipe databases and permanently destroy all cohort data — requires typed confirmation' },
        ]
    }
];


// ═══════════════════════════════════════════════════════════════
//  FACILITATOR SIDEBAR
// ═══════════════════════════════════════════════════════════════

export const FACILITATOR_SIDEBAR = [
    {
        // W-PA: shown only when the backend includes 'facilitator_registry'
        // in allowed_tabs (project_admin fixed set; super_admin '*').
        category: 'Administration',
        icon: '🗝️',
        id: 'administration',
        items: [
            { id: 'facilitator_registry', label: 'Facilitator Registry', icon: '👥', tooltip: 'Create facilitator accounts one-by-one, from CSV, or by Excel bulk upload. Registry admins only.' },
        ]
    },
    {
        category: 'Command Center',
        icon: '🎯',
        id: 'command',
        items: [
            // UX audit #13: dashboard_home / timeline / teleprompter / leaderboard
            // are the four Command Center surfaces used mid-round (state of play,
            // round pacing, what to say next, who is where). dry_run is a
            // pre-flight tool — deliberately NOT in the live-round subset.
            { id: 'dashboard_home', label: 'Dashboard Home',      icon: '🏠', liveRound: true, tooltip: 'At-a-glance overview: active cohort count, enrolled players, average round progression, and KPI health alerts (lagging teams, low treasury, low reputation). Includes quick-action buttons and the current round\'s Teleprompter briefing card. Answers: "What\'s the overall state of my simulation right now?"' },
            { id: 'timeline',       label: 'Round Timeline',       icon: '📅', liveRound: true, tooltip: 'Visual timeline of round progression across all cohorts, plus the per-cohort Session Setup group: round pacing, quiz difficulty & availability, and the CEO Interview toggle. Answers: "Which cohorts are ahead or behind, and how is each session configured?"' },
            { id: 'teleprompter',   label: 'Teleprompter',         icon: '🎤', liveRound: true, tooltip: 'Full-screen teleprompter with round-by-round facilitator briefing scripts: talking points to deliver, engines likely to fire, discussion prompts for class debate, and key themes. Answers: "What should I say to the class before this round?"' },
            { id: 'leaderboard',    label: 'Leaderboard',          icon: '🏆', liveRound: true, tooltip: 'Ranked matrix of all cohorts and players showing Treasury, Reputation, Synergy, EBITDA, round progress, and terminal value scores. Sortable and searchable with delete/reset controls per session. Answers: "Who\'s winning and who needs help?"' },
            // DRY-RUN-1 (2026-08-02): tab hidden. DryRunSimulator.js POSTs to
            // /api/admin/dry-run, and no such route exists — the backend's
            // run_dry_run() has zero callers — so clicking this tab 404s.
            // Restore it in the SAME commit that adds the route, and not
            // before removing dry_run.py's `random.seed(seed)` (line ~119),
            // which reseeds the PROCESS-GLOBAL PRNG and would rewind every
            // live cohort's randomness while a workshop is running.
            // Original entry, verbatim, for that commit:
            // { id: 'dry_run',        label: 'Dry-Run Simulator',    icon: '🛫', tooltip: 'Pre-flight check: plays four bot strategies (aggressive-green, extractive, balanced, chaotic) headlessly through the real engine from the selected cohort\'s current state to Round 10, several seeded repetitions each, WITHOUT touching the cohort. Reports a difficulty grade, bankruptcy risk and KPI trajectories per strategy, which crises bite hardest, and config warnings. Answers: "Is this cohort configuration survivable — and does strategy actually matter — before my class plays it?"' },
        ]
    },
    {
        category: 'Live Classroom',
        icon: '👥',
        id: 'classroom',
        items: [
            // UX audit #13: every item here is a live-round tool EXCEPT
            // intervention_config, which decides which tools a cohort gets —
            // a setup decision made before the room fills, not mid-round.
            // TT-1 (UX audit #17): tooltip previously promised "active/inactive
            // connection status" — the component renders no such column.
            { id: 'registry',       label: 'Player Registry',      icon: '📋', liveRound: true, tooltip: 'Full registry of all enrolled players with session IDs, parent cohort assignment, player names, and join timestamps. Answers: "Who has joined and which cohort are they in?"' },
            { id: 'session_viewer', label: 'Session Viewer',        icon: '👁️', liveRound: true, tooltip: 'Deep-dive inspector for any individual session: full KPI breakdown (Treasury, Reputation, Synergy, EBITDA, CO₂), complete round history with decisions made, and real-time state. Answers: "What exactly is happening inside this specific session?"' },
            { id: 'impersonate',    label: 'Team Impersonation',   icon: '🎭', liveRound: true, tooltip: 'View the simulation cockpit exactly as a specific player sees it — their dashboard, mailbox, decision interface, and KPI readouts. Useful for live debugging, classroom walkthroughs, or demonstrating the player experience. Answers: "What does this player\'s screen look like right now?"' },
            { id: 'swipe_file',     label: 'Swipe File / Inbox',   icon: '📬', liveRound: true, tooltip: 'Send pre-written narrative swipe files or compose custom in-game messages to individual teams. Messages appear in the player\'s mailbox as stakeholder communications, board directives, or crisis alerts. Answers: "How do I inject narrative events into a specific team\'s experience?"' },
            { id: 'broadcast',      label: 'Bulk Messaging',        icon: '📢', liveRound: true, tooltip: 'Send announcements, narrative events, or system messages to all cohorts simultaneously or to selected cohort groups. Supports both pre-written templates and custom messages. Answers: "How do I communicate with all teams at once?"' },
            // TT-1 (UX audit #17): tooltip previously promised generic
            // absolute/delta KPI edits — the backend applies exactly three
            // preset narrative overrides (see admin_router.apply_override).
            { id: 'manual_override',label: 'Manual Overrides',      icon: '⚡', liveRound: true, tooltip: 'Apply one of three preset narrative overrides to a session — Carbon Tax (treasury shock), Omni-Tech Poach (talent raid), or Force Strike (labour action) — each with its scripted KPI impact. Answers: "How do I hit this session with a preset intervention?"', requiredRole: 'lead_facilitator' },
            // UX-7.6: moved here from Configuration. Advancing a round lives in
            // Live Classroom, so its inverse must too — a facilitator who
            // over-advances in front of a cohort should not have to change
            // sidebar category to find the fix. showDisabled renders it (greyed,
            // with the reason) for base facilitators so the escalation path is
            // discoverable rather than invisible.
            { id: 'undo_round',     label: 'Undo Round',           icon: '↩️', liveRound: true, tooltip: 'Roll back the last completed round for a selected session, restoring all KPIs to their previous state. Use after an accidental advance or a teaching do-over. Tiered confirmation; cohort-wide rollback (every team back to the round before the furthest team, the cohort shell untouched) requires typing ROLL BACK. Answers: "How do I reverse a round that went wrong?"', requiredRole: 'lead_facilitator', showDisabled: true, disabledReason: 'Lead facilitator or above can roll a round back — ask them to undo it for this cohort.' },
            { id: 'intervention_config', label: 'Interventions',    icon: '🎮', tooltip: 'Configure which master interventions (manual overrides and narrative swipe files) are available for each cohort. Controls the intervention toolkit available during live facilitation. Answers: "Which intervention tools should this cohort have access to?"' },
            { id: 'custom_black_swan', label: 'Black Swan Injector', icon: '🦢', liveRound: true, tooltip: 'Compose a custom crisis (title, narrative, treasury / reputation / social-licence / natural-capital-debt deltas) and inject it into ONE selected cohort, with an injection history below the form. Lists only cohorts a super admin has enabled for the injector. Answers: "How do I hit this specific cohort with a crisis of my own design?"', requiredRole: 'lead_facilitator' },
        ]
    },
    {
        category: 'Analytics & Assessment',
        icon: '📊',
        id: 'analytics',
        items: [
            { id: 'platform_analytics',  label: 'Cohort Analytics',      icon: '📈', tooltip: 'Full analytics suite with 6 tabbed modules: Decision Heatmap (choice distributions), Time-to-Decision (speed analytics), Cohort Comparison (KPI trajectories), Convergence Analysis (strategy similarity), Learning Outcomes (badges & engagement), and Risk Exposure (ESG risk tracking). Answers: "What patterns are emerging across all my cohorts?"' },
            { id: 'cohort_comparison',   label: 'Cohort Comparison',     icon: '📊', tooltip: 'Side-by-side KPI trajectory comparison across cohorts plotted on SVG line charts. Toggle between Treasury, Reputation, Synergy, and EBITDA metrics with colour-coded lines per cohort. Answers: "How do different cohorts perform against each other over time?"' },
            { id: 'complexity_feed',     label: 'Complexity Feed',        icon: '📡', tooltip: 'Real-time chronological feed of complexity events fired across all sessions: engine triggers (Contagion, Talent/Burnout, NCD), system-generated narrative injections, and math engine outputs. Answers: "What complexity events are unfolding in real-time?"' },
            { id: 'decision_replay',     label: 'Decision History',       icon: '🕰️', tooltip: 'Chronological audit trail of every player decision across all sessions: timestamps, round numbers, choices selected, CapEx allocations, and resulting KPI deltas. Filterable by cohort and player. Answers: "What decisions has each team made and when?"' },
            { id: 'dna_comparison',       label: 'DNA Comparison',         icon: '🧬', tooltip: 'Consequence DNA Sankey diagram comparison across selected cohorts. Visualizes how different strategic paths led to divergent systemic outcomes, agent conflicts, and M_R trajectories. Answers: "How did different teams\' causal chains diverge?"' },
            { id: 'debrief',             label: 'Round Debrief',          icon: '📝', tooltip: 'Post-round debrief summary reports: key decisions made across cohorts, aggregate outcomes, notable outliers, and suggested discussion points for classroom review. Answers: "What should I highlight in the post-round discussion?"' },
            // DN-1 (UX audit §9 / item #12): the debrief writes itself.
            { id: 'debrief_narrative',   label: 'Debrief Narrative',      icon: '🎙️', tooltip: 'Auto-assembled story of the selected cohort\'s run: final ranking, the round where the field split, each player\'s biggest turning point, predicted-vs-actual comparisons, and auto-committed rounds flagged for grading. Each section has a Project button sized for the room screen. Read-only. Answers: "What is the story of this run, ready to read aloud?"' },
            { id: 'scorecard_evaluator', label: 'Scorecard Sandbox',      icon: '🧲', tooltip: 'Interactive whiteboard for demonstrating the Triple Bottom Line scorecard weighting formula. Adjust sliders for Financial, Social, and Environmental weights to show students how terminal value is calculated. Teaching tool only — does not affect live session data. Answers: "How does the scoring formula work?"' },
            { id: 'esg_weights',         label: 'ESG Profile Weights',    icon: '🎚️', tooltip: 'Tune the weight each performance signal carries in the five ESG Leadership Profile dimensions (Climate Resilience, Governance, Social Impact, Environmental, Innovation) shown to players at game end. Sets the GLOBAL assessment rubric shared by every cohort on the platform, so editing is Super Admin only (F-24); other facilitators can read the current weights from the game-end radar. Answers: "How is the end-of-game ESG radar scored, and how do I reweight it?"', requiredRole: 'super_admin' },
            { id: 'bonuses',             label: 'Student Bonuses',        icon: '🎁', tooltip: 'Award manual bonuses or grade adjustments to individual players or teams: participation rewards, presentation bonuses, or custom facilitator-assigned points. Tracks all bonus history by category. Answers: "How do I reward exceptional student performance?"' },
            { id: 'peer_eval',           label: 'Peer Evaluations',       icon: '🔄', tooltip: 'Manage and review peer evaluation submissions where students anonymously rate team members on collaboration, contribution, and communication. Aggregates scores for grading integration. Answers: "How are students rating each other\'s teamwork?"' },
            // TT-1 (UX audit #17): tooltip previously promised PDF export —
            // the component exports CSV and JSON only (print-to-PDF lives in
            // the student report view).
            { id: 'reports',             label: 'Export Reports',          icon: '📤', tooltip: 'Generate and download CSV or JSON exports of session data, full leaderboard snapshots, per-student decision trails, and grading-ready spreadsheets. Answers: "How do I export data for grading or record-keeping?"' },
        ]
    },
    {
        category: 'Configuration',
        icon: '⚙️',
        id: 'config',
        items: [
            { id: 'auto_pause',          label: 'Auto-Pause Triggers',   icon: '⏸️', tooltip: 'Configure automatic pause conditions that halt round progression for facilitator intervention: low treasury thresholds, reputation floor breaches, bankruptcy detection, or custom KPI triggers. Answers: "When should the simulation automatically pause for my attention?"', requiredRole: 'lead_facilitator' },
            { id: 'regulatory_sandbox',  label: 'Regulatory Sandbox',     icon: '⚖️', tooltip: 'Dynamically inject regulatory instruments (e.g., Carbon Tax, Due Diligence) into the simulation to test resilience.', requiredRole: 'lead_facilitator' },
            // I2 (Workstream C): read-only view of each owned cohort's effective
            // climate settings vs the global default, and where its BU scope is
            // decided. Renders CohortSettingsMatrix (same component as the God Mode
            // Switchboard card); the backend /effective-settings/summary scopes
            // rows to sessions this lead owns.
            { id: 'cohort_settings_view', label: 'Cohort Settings',       icon: '🗂️', tooltip: 'Read-only: your cohorts\' effective climate parameters (branch, carbon fee, hostility, Scope-3) vs the global default, with which values are overridden and where each cohort\'s BU scope is set. Answers: "Which of my cohorts run non-default settings?"', requiredRole: 'lead_facilitator' },
            { id: 'materiality',         label: 'Materiality Matrix',    icon: '🧩', tooltip: 'Mendelow\'s Materiality Matrix — interactive drag-and-drop issue mapping grid. Super Admin only: editing the materiality matrix is restricted to super administrators; other facilitators do not see this tab. Answers: "How do I configure the materiality framework?"', requiredRole: 'super_admin' },
            { id: 'teaching_journal',    label: 'Teaching Journal',       icon: '📝', tooltip: 'Private workspace combining notes and timestamped annotations. Jot observations, bookmark key moments, and prepare debrief commentary. Persisted across sessions. Answers: "Where can I keep my private teaching notes and bookmarks?"' },
            { id: 'technical_glossary',  label: 'Technical Reference',   icon: '📐', tooltip: 'Comprehensive reference guide explaining simulation terminology, engine mechanics (Contagion, Talent/Burnout, NCD, Governance), KPI calculation formulas, scorecard weighting, and decision paradigm differences. Answers: "How do the simulation engines and calculations actually work?"' },
            { id: 'activity_log',        label: 'Activity Logs & Resets', icon: '📋', tooltip: 'Facilitator activity audit log showing all actions taken (overrides, messages, resets) with timestamps. Includes session management controls for soft/hard deleting cohorts or removing individual players. Answers: "What actions have been taken and how do I clean up sessions?"', requiredRole: 'lead_facilitator' },
        ]
    },
];


// ═══════════════════════════════════════════════════════════════
//  ROLE-BASED FILTERING
// ═══════════════════════════════════════════════════════════════

// SYNC-WARNING: This must match ROLE_HIERARCHY in backend/admin_shared.py.
// If you add or rename a role, update both files. There is currently no
// automated check — a drift will silently break tab filtering.
// SYNC-WARNING: mirrors backend admin_shared.py:ROLE_HIERARCHY EXACTLY.
// Enforced by the drift tripwire tests/test_role_hierarchy_sync.py — if you add
// or renumber a role here, update admin_shared.py in the SAME commit or the
// tripwire fails.
const ROLE_HIERARCHY = {
    god_mode: 4,       // C6: distinct top tier (virtual break-glass identity)
    super_admin: 3,
    admin: 3,          // legacy alias for super_admin
    lead_facilitator: 2,
    facilitator: 1,
    // C4: project_admin is OFF the run ladder (level 0), a DISTINCT role from
    // facilitator — not a peer. Its tabs come from its FIXED allowed_tabs set;
    // the level keeps requiredRole-tagged (lead+) tabs hidden from it.
    project_admin: 0,
};

/**
 * Filter sidebar config based on user's role and allowed tabs.
 * @param {Array} sidebarConfig - The full sidebar config array
 * @param {string} role - User's role ('super_admin', 'lead_facilitator', 'facilitator')
 * @param {string[]} allowedTabs - Array of allowed tab IDs (from backend), ['*'] means all
 * @returns {Array} Filtered sidebar config with empty groups removed
 */
export function filterSidebarForRole(sidebarConfig, role, allowedTabs = ['*']) {
    const userLevel = ROLE_HIERARCHY[role] || 0;
    const allAllowed = allowedTabs.includes('*');

    return sidebarConfig
        .map(group => ({
            ...group,
            items: group.items
                .map(item => {
                    // UX-7.6: an item marked showDisabled stays VISIBLE below its
                    // role tier, rendered inert with a reason, so the user can see
                    // that the capability exists and who to ask. Everything else
                    // keeps the previous hide-entirely behaviour.
                    if (item.requiredRole) {
                        const requiredLevel = ROLE_HIERARCHY[item.requiredRole] || 0;
                        if (userLevel < requiredLevel) {
                            return item.showDisabled ? { ...item, _locked: true } : null;
                        }
                    }
                    return item;
                })
                .filter(item => {
                    if (!item) return false;
                    // Check backend-provided allowed tabs. A locked item is a
                    // signpost, not a route, so it survives this check.
                    if (item._locked) return true;
                    if (!allAllowed && !allowedTabs.includes(item.id)) return false;
                    return true;
                }),
        }))
        .filter(group => group.items.length > 0);
}

/**
 * UX audit #13 — Live Round mode.
 * Reduce a sidebar config to the tabs a facilitator needs WHILE a round is
 * being run (see the LIVE-ROUND SUBSET note in the file header).
 *
 * Composition contract: this runs AFTER filterSidebarForRole and only ever
 * REMOVES items, so every role decision that function made survives intact —
 * including `_locked` signpost items (UX-7.6), which stay visible-but-inert in
 * live-round mode when they carry the flag. It never re-admits a tab the role
 * filter dropped, so it cannot widen access; ROLE_ALLOWED_TABS semantics are
 * untouched.
 *
 * The caller keeps its own access gate (canAccessTab) on the ROLE-filtered
 * list, not on this one — hiding a tab from the sidebar must never blank a
 * workspace the user is already looking at.
 *
 * @param {Array} sidebarConfig - Sidebar config array (normally already role-filtered)
 * @returns {Array} Only items flagged `liveRound`, group structure preserved, empty groups removed
 */
export function filterSidebarForLiveRound(sidebarConfig) {
    return sidebarConfig
        .map(group => ({
            ...group,
            items: group.items.filter(item => item && item.liveRound === true),
        }))
        .filter(group => group.items.length > 0);
}

/**
 * Find tab metadata (label, category, icon) by tab ID.
 * @param {Array} sidebarConfig - The sidebar config array to search
 * @param {string} tabId - The tab ID to look up
 * @returns {{ label: string, category: string, categoryIcon: string }}
 */
export function getTabMeta(sidebarConfig, tabId) {
    for (const group of sidebarConfig) {
        const item = group.items.find(i => i.id === tabId);
        if (item) return { label: item.label, category: group.category, categoryIcon: group.icon };
    }
    return { label: 'Overview', category: 'Command Center', categoryIcon: '📡' };
}

/**
 * Get all unique tab IDs from a sidebar config.
 * @param {Array} sidebarConfig
 * @returns {string[]}
 */
export function getAllTabIds(sidebarConfig) {
    return sidebarConfig.flatMap(group => group.items.map(item => item.id));
}
