/**
 * Unified Sidebar Configuration
 * Single source of truth for both God Mode and Facilitator sidebar navigation.
 * Generates role-filtered tab lists using the 3-tier RBAC model.
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
            { id: 'activity_log',        label: 'Activity & Complexity', icon: '📋', tooltip: 'Immutable audit trail and live firehose of systemic interactions and complexity events' },
        ]
    },
    {
        category: 'Cohort Orchestration',
        icon: '🎓',
        id: 'orchestration',
        items: [
            { id: 'facilitator_registry', label: 'Facilitator Registry', icon: '👥', tooltip: 'Manage facilitators: create, edit roles (Super Admin / Lead / Facilitator), set permissions and cohort limits' },
            { id: 'cohort_provisioning',  label: 'Cohort Provisioning',  icon: '🗂️', tooltip: 'Provision and manage cohort sessions, assign facilitators, and configure paradigms' },
            { id: 'session_controls',     label: 'Session Controls',     icon: '🎛️', tooltip: 'Round pacing, universal broadcasts, visibility controls, and cross-cohort scheduling' },
            { id: 'master_interventions', label: 'Team Interventions',   icon: '🚀', tooltip: 'Directly inject capital, penalties, or narrative events into target teams' },
            { id: 'crisis_overrides',     label: 'Crisis Overrides',     icon: '🚨', tooltip: 'Manually activate crises, deploy Black Swans, or trigger end-game pathways' },
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
            { id: 'systemic_risk_controls', label: 'Systemic Risk',      icon: '🌡️', tooltip: 'Toggle Black Swan events, NPC cascades, tipping points, and foreshadowing signals. Difficulty tier is set per-cohort via Experience Level.' },
            { id: 'materiality_config',  label: 'Materiality Matrix',   icon: '🦭', tooltip: 'Configure double materiality weightings — global defaults that facilitators inherit' },
            { id: 'archetype_editor',    label: 'Profile Archetypes',   icon: '🏆', tooltip: 'Define Year 5 outcome profiles based on Regenerative Multiple (M_R) thresholds' },
            { id: 'scorecard_evaluator', label: 'Scorecard Evaluator',  icon: '📊', tooltip: 'Interactive whiteboard for demonstrating the Triple Bottom Line scorecard weighting formula' },
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
        category: 'Command Center',
        icon: '🎯',
        id: 'command',
        items: [
            { id: 'dashboard_home', label: 'Dashboard Home',      icon: '🏠', tooltip: 'At-a-glance overview: active cohort count, enrolled players, average round progression, and KPI health alerts (lagging teams, low treasury, low reputation). Includes quick-action buttons and the current round\'s Teleprompter briefing card. Answers: "What\'s the overall state of my simulation right now?"' },
            { id: 'timeline',       label: 'Round Timeline',       icon: '📅', tooltip: 'Visual timeline of round progression across all cohorts. Includes quiz controls for setting difficulty (easy/medium/hard) and enabling/disabling quizzes per cohort. Answers: "Which cohorts are ahead or behind, and are quizzes active?"' },
            { id: 'teleprompter',   label: 'Teleprompter',         icon: '🎤', tooltip: 'Full-screen teleprompter with round-by-round facilitator briefing scripts: talking points to deliver, engines likely to fire, discussion prompts for class debate, and key themes. Answers: "What should I say to the class before this round?"' },
            { id: 'leaderboard',    label: 'Leaderboard',          icon: '🏆', tooltip: 'Ranked matrix of all cohorts and players showing Treasury, Reputation, Synergy, EBITDA, round progress, and terminal value scores. Sortable and searchable with delete/reset controls per session. Answers: "Who\'s winning and who needs help?"' },
        ]
    },
    {
        category: 'Live Classroom',
        icon: '👥',
        id: 'classroom',
        items: [
            { id: 'registry',       label: 'Player Registry',      icon: '📋', tooltip: 'Full registry of all enrolled players with session IDs, parent cohort assignment, player names, join timestamps, and active/inactive connection status. Answers: "Who has joined and which cohort are they in?"' },
            { id: 'session_viewer', label: 'Session Viewer',        icon: '👁️', tooltip: 'Deep-dive inspector for any individual session: full KPI breakdown (Treasury, Reputation, Synergy, EBITDA, CO₂), complete round history with decisions made, and real-time state. Answers: "What exactly is happening inside this specific session?"' },
            { id: 'impersonate',    label: 'Team Impersonation',   icon: '🎭', tooltip: 'View the simulation cockpit exactly as a specific player sees it — their dashboard, mailbox, decision interface, and KPI readouts. Useful for live debugging, classroom walkthroughs, or demonstrating the player experience. Answers: "What does this player\'s screen look like right now?"' },
            { id: 'swipe_file',     label: 'Swipe File / Inbox',   icon: '📬', tooltip: 'Send pre-written narrative swipe files or compose custom in-game messages to individual teams. Messages appear in the player\'s mailbox as stakeholder communications, board directives, or crisis alerts. Answers: "How do I inject narrative events into a specific team\'s experience?"' },
            { id: 'broadcast',      label: 'Bulk Messaging',        icon: '📢', tooltip: 'Send announcements, narrative events, or system messages to all cohorts simultaneously or to selected cohort groups. Supports both pre-written templates and custom messages. Answers: "How do I communicate with all teams at once?"' },
            { id: 'manual_override',label: 'Manual Overrides',      icon: '⚡', tooltip: 'Directly modify a session\'s KPIs (Treasury, Reputation, Synergy) with absolute or delta values, or force-advance rounds. Used for live interventions, correcting data errors, or simulating external shocks. Answers: "How do I manually change a team\'s numbers?"', requiredRole: 'lead_facilitator' },
            { id: 'intervention_config', label: 'Interventions',    icon: '🎮', tooltip: 'Configure which master interventions (manual overrides and narrative swipe files) are available for each cohort. Controls the intervention toolkit available during live facilitation. Answers: "Which intervention tools should this cohort have access to?"', requiredRole: 'lead_facilitator' },
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
            { id: 'scorecard_evaluator', label: 'Scorecard Sandbox',      icon: '🧲', tooltip: 'Interactive whiteboard for demonstrating the Triple Bottom Line scorecard weighting formula. Adjust sliders for Financial, Social, and Environmental weights to show students how terminal value is calculated. Teaching tool only — does not affect live session data. Answers: "How does the scoring formula work?"' },
            { id: 'bonuses',             label: 'Student Bonuses',        icon: '🎁', tooltip: 'Award manual bonuses or grade adjustments to individual players or teams: participation rewards, presentation bonuses, or custom facilitator-assigned points. Tracks all bonus history by category. Answers: "How do I reward exceptional student performance?"' },
            { id: 'peer_eval',           label: 'Peer Evaluations',       icon: '🔄', tooltip: 'Manage and review peer evaluation submissions where students anonymously rate team members on collaboration, contribution, and communication. Aggregates scores for grading integration. Answers: "How are students rating each other\'s teamwork?"' },
            { id: 'reports',             label: 'Export Reports',          icon: '📤', tooltip: 'Generate and download CSV/PDF reports of session data, full leaderboard snapshots, per-student decision trails, analytics summaries, and grading-ready spreadsheets. Answers: "How do I export data for grading or record-keeping?"' },
        ]
    },
    {
        category: 'Configuration',
        icon: '⚙️',
        id: 'config',
        items: [
            { id: 'auto_pause',          label: 'Auto-Pause Triggers',   icon: '⏸️', tooltip: 'Configure automatic pause conditions that halt round progression for facilitator intervention: low treasury thresholds, reputation floor breaches, bankruptcy detection, or custom KPI triggers. Answers: "When should the simulation automatically pause for my attention?"', requiredRole: 'lead_facilitator' },
            { id: 'undo_round',          label: 'Undo Round',             icon: '↩️', tooltip: 'Roll back the last completed round for a selected session, restoring all KPIs to their previous state. Useful for correcting data entry errors or re-running a round after a teaching moment. Requires confirmation. Answers: "How do I reverse a round that went wrong?"', requiredRole: 'lead_facilitator' },
            { id: 'regulatory_sandbox',  label: 'Regulatory Sandbox',     icon: '⚖️', tooltip: 'Dynamically inject regulatory instruments (e.g., Carbon Tax, Due Diligence) into the simulation to test resilience.', requiredRole: 'lead_facilitator' },
            { id: 'materiality',         label: 'Materiality Matrix',    icon: '🧩', tooltip: 'Mendelow\'s Materiality Matrix — interactive drag-and-drop issue mapping grid. Lead facilitators can customize per-cohort; base facilitators have read-only access to global defaults. Answers: "How do I view/configure the materiality framework?"', requiredRole: 'lead_facilitator' },
            { id: 'teaching_journal',    label: 'Teaching Journal',       icon: '📝', tooltip: 'Private workspace combining notes and timestamped annotations. Jot observations, bookmark key moments, and prepare debrief commentary. Persisted across sessions. Answers: "Where can I keep my private teaching notes and bookmarks?"' },
            { id: 'technical_glossary',  label: 'Technical Reference',   icon: '📐', tooltip: 'Comprehensive reference guide explaining simulation terminology, engine mechanics (Contagion, Talent/Burnout, NCD, Governance), KPI calculation formulas, scorecard weighting, and decision paradigm differences. Answers: "How do the simulation engines and calculations actually work?"' },
            { id: 'activity_log',        label: 'Activity Logs & Resets', icon: '📋', tooltip: 'Facilitator activity audit log showing all actions taken (overrides, messages, resets) with timestamps. Includes session management controls for soft/hard deleting cohorts, removing individual players, or performing a full system reset. Answers: "What actions have been taken and how do I clean up sessions?"', requiredRole: 'lead_facilitator' },
        ]
    },
];


// ═══════════════════════════════════════════════════════════════
//  ROLE-BASED FILTERING
// ═══════════════════════════════════════════════════════════════

const ROLE_HIERARCHY = {
    super_admin: 3,
    lead_facilitator: 2,
    facilitator: 1,
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
            items: group.items.filter(item => {
                // Check role requirement on the item itself
                if (item.requiredRole) {
                    const requiredLevel = ROLE_HIERARCHY[item.requiredRole] || 0;
                    if (userLevel < requiredLevel) return false;
                }
                // Check backend-provided allowed tabs
                if (!allAllowed && !allowedTabs.includes(item.id)) return false;
                return true;
            }),
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
