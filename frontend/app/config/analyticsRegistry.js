/**
 * analyticsRegistry.js — SINGLE source of truth for the facilitator analytics
 * cards (Railway audit §4.3).
 *
 * Previously two hand-maintained lists — FACILITATOR_ANALYTICS in
 * AnalyticsControlPanel (visibility toggles) and TABS in PlatformAnalytics
 * (the rendered tabs) — shared keys but separately-worded tooltip copy, and
 * every new card had to be added twice (empirically: the calibration card
 * required both edits). Both components now import from here.
 *
 * Fields:
 *   key     — visibility key (analytics-visibility profiles gate on this)
 *   tabId   — PlatformAnalytics tab id (omitted for cards that only gate
 *             dashboard panels, e.g. materiality_matrix)
 *   label / icon / desc / tooltip — shared copy for both surfaces
 */

export const ANALYTICS_CARDS = [
    { key: 'decision_heatmap', tabId: 'heatmap', label: 'Decision Heatmap', icon: '📊', desc: 'Choice distributions per round', tooltip: 'Choice distribution matrix showing which strategic options (A, B, C, etc.) were selected in each round across all players. Includes a heatmap grid with counts/percentages and stacked bar charts for visual comparison. Answers: "What are the most popular choices per round?"' },
    { key: 'time_to_decision', tabId: 'timing', label: 'Time-to-Decision', icon: '⏱', desc: 'Decision speed analytics', tooltip: 'Decision speed analytics — how long players take to commit their choices each round. Displays average, median, min, and max times in seconds with horizontal bar visualizations. Answers: "Are players deliberating or rushing?"' },
    { key: 'cohort_comparison', tabId: 'cohorts', label: 'Cohort Comparison', icon: '📈', desc: 'KPI trajectories side-by-side', tooltip: 'Plots KPI trajectories side-by-side for multiple cohorts on an SVG line chart. Togglable between Treasury, Reputation, Synergy, and EBITDA metrics. Answers: "How do different cohorts perform against each other over time?"' },
    { key: 'convergence_analysis', tabId: 'convergence', label: 'Convergence Analysis', icon: '🔄', desc: 'Strategy similarity metrics', tooltip: 'Measures strategy similarity using a convergence gauge (0–100%). Tracks choice entropy (bits of unpredictability) and CapEx standard deviation per round. Low entropy = players thinking alike. Answers: "Are teams converging on the same strategy or diversifying?"' },
    { key: 'learning_outcomes', tabId: 'learning', label: 'Learning Outcomes', icon: '🎯', desc: 'Quiz scores, badges, engagement', tooltip: 'Tracks gamification and engagement: total learning bonuses awarded, manual facilitator awards, badge distribution counts, and bonuses by category. Answers: "How engaged are students and what milestones have they hit?"' },
    { key: 'risk_exposure', tabId: 'risk', label: 'Risk Exposure', icon: '📉', desc: 'Carbon, NCD, social license trends', tooltip: 'Multi-axis tracking of non-financial risks per cohort over time: Carbon Intensity, Natural Capital Debt, Social License, and Governance Risk. Rendered as vertical bar charts per cohort. Answers: "How are teams managing ESG/sustainability risks?"' },
    { key: 'calibration_analytics', tabId: 'calibration', label: 'Calibration', icon: '🎯', desc: 'Confidence vs accuracy from Predict-Before-Commit', tooltip: 'Scores each team\'s Predict-Before-Commit forecasts against actual outcomes: per-team stated confidence vs realised hit-rate (scatter with the perfect-calibration diagonal), cohort trend by round, and the most over/under-confident teams. Includes a one-line debrief prompt. Data only exists when 🔮 Predictions is enabled for the cohort. Answers: "Are my students\' mental models of the system actually improving?"' },
    // Dashboard-panel gates (no PlatformAnalytics tab):
    { key: 'materiality_matrix', label: 'Materiality Matrix', icon: '🧩', desc: 'Show/hide Materiality Matrix on Facilitator Dashboard', tooltip: 'Toggles the Mendelow\'s Materiality Matrix panel — the drag-and-drop issue mapping grid with financial vs. societal impact axes for stakeholder analysis. Used for teaching ESG materiality assessment.' },
    { key: 'technical_reference', label: 'Technical Reference', icon: '📐', desc: 'Show/hide Technical Glossary on Facilitator Dashboard', tooltip: 'Toggles the Technical Glossary panel — a comprehensive reference guide explaining simulation terminology, engine mechanics, KPI calculation formulas, and contagion/talent engine parameters.' },
];

// PlatformAnalytics tab list (cards that render a tab), in display order.
export const ANALYTICS_TABS = ANALYTICS_CARDS
    .filter((c) => c.tabId)
    .map((c) => ({ id: c.tabId, key: c.key, label: `${c.icon} ${c.label}`, title: c.tooltip }));

// ── Extended visibility catalog ─────────────────────────────────────────────
// Panels gated by analytics-visibility that are NOT PlatformAnalytics tabs
// (live monitoring, deep-dive/audit, ESG dashboards). Together with
// ANALYTICS_CARDS this mirrors the backend `_analytics_visibility.facilitator`
// dict in admin_analytics.py — the setter endpoints silently DROP any key not
// present there, so add keys in both places in the same commit.
export const EXTENDED_VISIBILITY_CARDS = [
    // ── Live cohort monitoring ──
    { key: 'cohort_pulse', label: 'Cohort Pulse', icon: '🩺', tooltip: 'Live cohort health pulse — real-time engagement, commit progress, and sentiment across all teams in the active round. Answers: "Is the room with me right now?"' },
    { key: 'leaderboard_matrix', label: 'Leaderboard Matrix', icon: '🥇', tooltip: 'Ranked matrix of every team across the headline KPIs (Treasury, Reputation, Synergy, M_R) with movement since last round. Answers: "Who is leading and who is falling behind?"' },
    { key: 'session_health', label: 'Session Health', icon: '💓', tooltip: 'Operational health of the live session — player connections, commit/lock status per team, pacing drift, and stalled players. Answers: "Is the session running cleanly?"' },
    { key: 'engine_event_feed', label: 'Engine Event Feed', icon: '📡', tooltip: 'Chronological stream of engine/complexity events fired this run (crises, shockwaves, black swans, threshold breaches). Answers: "What has the engine thrown at the teams?"' },
    // ── Deep-dive & audit ──
    { key: 'consequence_dna', label: 'Consequence DNA', icon: '🧬', tooltip: 'Decision→outcome causal visualiser — traces how each choice propagated through the engines into KPI movement. Answers: "Why did this team get this result?"' },
    { key: 'decision_timeline', label: 'Decision Timeline', icon: '🧭', tooltip: 'Per-team chronology of every decision, override, and intervention across the ten rounds. Answers: "What was this team\'s narrative arc?"' },
    { key: 'stakeholder_map', label: 'Stakeholder Map', icon: '🗺️', tooltip: 'Region-specific Mendelow stakeholder grid (power × interest) with live satisfaction/trust state per stakeholder. Answers: "Who holds leverage over these teams?"' },
    { key: 'audit_trail', label: 'Audit Trail', icon: '📜', tooltip: 'Immutable log of facilitator actions — overrides, unlocks, injections, grading, and God-Mode changes. Answers: "What was changed, by whom, and when?"' },
    { key: 'shadow_board_audit', label: 'Shadow Board Audit', icon: '🕵️', tooltip: 'Advanced governance audit contrasting each team\'s decisions against a shadow board\'s recommendations. Executive-tier debrief tool. Disabled by default.' },
    // ── ESG / disclosure dashboards ──
    { key: 'sdg_alignment', label: 'SDG Alignment Radar', icon: '🌐', tooltip: 'Radar of each cohort\'s alignment to the 17 UN SDGs derived from decisions taken. Answers: "Which goals are teams advancing or neglecting?"' },
    { key: 'tcfd_dashboard', label: 'TCFD Scenarios', icon: '🌡️', tooltip: 'TCFD climate-scenario dashboard (orderly 1.5°C / disorderly 2°C / hothouse 4°C) with each team\'s exposure. Advanced-climate cohorts. Disabled by default.' },
    { key: 'peer_evaluation', label: 'Peer Evaluation', icon: '🧑‍⚖️', tooltip: 'Aggregated inter-team peer-evaluation results and rubric scores. Surfaces only when the peer-evaluation exercise is run. Disabled by default.' },
];

// Full facilitator visibility catalog (what CreateCohortModal's visibility
// matrix renders) — mirrors the backend dict, one source, no third copy.
export const ANALYTICS_VISIBILITY_CATALOG = [...ANALYTICS_CARDS, ...EXTENDED_VISIBILITY_CARDS];
