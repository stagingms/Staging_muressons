import React, { useState, useEffect, useRef } from 'react';
import styles from './CreateCohortModal.module.css';
import { CURRENCIES } from '../contexts/CurrencyContext';
import { VERTICAL_CATALOG, VERTICAL_SLOT_MAP, SLOT_META } from '../lib/verticalCatalog';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// Analytics-visibility catalog. Keys MUST stay in sync with the backend
// _analytics_visibility dict in admin_analytics.py — the setter endpoints reject
// any key not present there (add in both, same commit).
const FACILITATOR_ANALYTICS = [
    // ── Core analytics ──
    { key: 'decision_heatmap', label: 'Decision Heatmap', icon: '📊', tooltip: 'Choice distribution matrix showing which strategic options (A, B, C, etc.) were selected in each round across all players. Includes a heatmap grid with counts/percentages and stacked bar charts for visual comparison. Answers: "What are the most popular choices per round?"' },
    { key: 'time_to_decision', label: 'Time-to-Decision', icon: '⏱', tooltip: 'Decision speed analytics — how long players take to commit their choices each round. Displays average, median, min, and max times in seconds with horizontal bar visualizations. Answers: "Are players deliberating or rushing?"' },
    { key: 'cohort_comparison', label: 'Cohort Comparison', icon: '📈', tooltip: 'Plots KPI trajectories side-by-side for multiple cohorts on an SVG line chart. Togglable between Treasury, Reputation, Synergy, and EBITDA metrics. Answers: "How do different cohorts perform against each other over time?"' },
    { key: 'convergence_analysis', label: 'Convergence Analysis', icon: '🔄', tooltip: 'Measures strategy similarity using a convergence gauge (0–100%). Tracks choice entropy (bits of unpredictability) and CapEx standard deviation per round. Low entropy = players thinking alike. Answers: "Are teams converging on the same strategy or diversifying?"' },
    { key: 'learning_outcomes', label: 'Learning Outcomes', icon: '🎯', tooltip: 'Tracks gamification and engagement: total learning bonuses awarded, manual facilitator awards, badge distribution counts, and bonuses by category. Answers: "How engaged are students and what milestones have they hit?"' },
    { key: 'risk_exposure', label: 'Risk Exposure', icon: '📉', tooltip: 'Multi-axis tracking of non-financial risks per cohort over time: Carbon Intensity, Natural Capital Debt, Social License, and Governance Risk. Rendered as vertical bar charts per cohort. Answers: "How are teams managing ESG/sustainability risks?"' },
    { key: 'materiality_matrix', label: 'Materiality Matrix', icon: '🧩', tooltip: 'Toggles the Mendelow\'s Materiality Matrix panel — the drag-and-drop issue mapping grid with financial vs. societal impact axes for stakeholder analysis. Used for teaching ESG materiality assessment.' },
    { key: 'technical_reference', label: 'Technical Reference', icon: '📐', tooltip: 'Toggles the Technical Glossary panel — a comprehensive reference guide explaining simulation terminology, engine mechanics, KPI calculation formulas, and contagion/talent engine parameters.' },
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

const PLAYER_ANALYTICS = [
    // ── Core analytics ──
    { key: 'peer_benchmarking', label: 'Peer Benchmarking', icon: '🏆', tooltip: 'Shows the player their anonymous percentile ranking vs. the cohort for Treasury, Reputation, and Synergy. Includes bar visualizations with their value compared against the cohort average. Answers: "How do I rank among my peers?"' },
    { key: 'decision_impact', label: 'Decision Impact', icon: '🧠', tooltip: 'Per-round KPI attribution — shows how each choice affected Treasury, Reputation, and Synergy with colour-coded delta badges (+/-) and a narrative explanation of the outcome. Answers: "What impact did my decisions actually have?"' },
    { key: 'what_if_simulator', label: 'What-If Simulator', icon: '📈', tooltip: 'Counterfactual analysis — shows what would have happened if the player had chosen the most popular alternative option. Displays projected Treasury and Reputation diffs. Only appears when choices differ from the majority. Disabled by default.' },
    // ── Performance & history ──
    { key: 'kpi_dashboard', label: 'KPI Dashboard', icon: '📟', tooltip: 'The player\'s personal KPI cockpit — Treasury, Reputation, Synergy, EBITDA and ESG headline metrics with round-on-round deltas. Answers: "Where do I stand right now?"' },
    { key: 'decision_history', label: 'Decision History', icon: '🕰️', tooltip: 'A log of the player\'s own past decisions with the rationale captured and the outcome that followed. Answers: "What have I chosen so far and why?"' },
    { key: 'consequence_timeline', label: 'Consequence Timeline', icon: '⏳', tooltip: 'Shows consequences unfolding across future rounds from earlier decisions (delayed effects, compounding debt). Answers: "What did my past choices set in motion?"' },
    { key: 'stock_performance', label: 'Stock Performance', icon: '📉', tooltip: 'Share-price / enterprise-value chart tracking the market\'s valuation of the player\'s company over the ten rounds. Answers: "Is the market rewarding my strategy?"' },
    { key: 'balanced_scorecard', label: 'Balanced Scorecard', icon: '🎯', tooltip: 'Sustainability balanced scorecard across financial, customer, internal-process and learning/ESG perspectives. Advanced pedagogy. Disabled by default.' },
    // ── Risk & strategy lenses ──
    { key: 'risk_radar', label: 'Risk Radar', icon: '🕸️', tooltip: 'Multi-axis radar of the player\'s current risk exposure (carbon, natural-capital, social-licence, governance, liquidity). Answers: "Where am I fragile?"' },
    { key: 'esg_leadership', label: 'ESG Leadership Profile', icon: '🌱', tooltip: 'Profiles the player\'s ESG leadership style from the pattern of decisions taken across the run. Reflective debrief tool. Disabled by default.' },
    { key: 'competitor_intel', label: 'Competitor Intel', icon: '🔭', tooltip: 'Rival-intelligence cards giving partial, fog-of-war signals about other teams\' moves. Disabled by default (competitive cohorts only).' },
    // ── Reports & engagement ──
    { key: 'annual_report', label: 'Annual Report', icon: '📕', tooltip: 'A narrative annual report generated from the player\'s results — financials, ESG highlights, and board commentary. Answers: "How does my year read as a story?"' },
    { key: 'achievement_badges', label: 'Achievement Badges', icon: '🏅', tooltip: 'Gamified milestone badges earned for strategic and sustainability achievements during the run. Drives engagement.' },
    { key: 'regret_meter', label: 'Regret Meter', icon: '😬', tooltip: 'A counterfactual "regret" gauge estimating value left on the table versus the best available path. Reflective tool. Disabled by default.' },
    { key: 'glossary', label: 'Glossary', icon: '📖', tooltip: 'In-game technical glossary explaining KPIs, engines, and sustainability terminology on demand. Answers: "What does this term mean?"' },
    // ── Right-hand context rail ──
    // The rail's tabs are player-facing surfaces like any other panel but were
    // missing from this list, so a facilitator could not switch them off. The
    // 'Decisions' tab is deliberately absent: it renders DecisionHistory and is
    // gated by the existing `decision_history` toggle above (one surface, one
    // switch — a duplicate key would let the two disagree).
    { key: 'rail_mailbox', label: 'Rail · Mailbox', icon: '📬', tooltip: 'The right-hand rail\'s Executive Mailbox tab — board memos, stakeholder letters and injected messages. Turn off for a stripped-back cockpit or when running the narrative offline.' },
    { key: 'rail_engines', label: 'Rail · Engines', icon: '🌎', tooltip: 'The right-hand rail\'s Engines tab — live engine widgets showing contagion, talent and systemic-risk state. Advanced; hide for introductory cohorts.' },
    { key: 'rail_climate', label: 'Rail · Climate', icon: '🌡️', tooltip: 'The right-hand rail\'s Climate tab — the TCFD scenario dashboard. Hide when the cohort is not running the climate-disclosure thread.' },
    { key: 'market_reality_feed', label: 'Market Reality Feed', icon: '📡', tooltip: 'The rail\'s live market/consequence feed with traceability back to the decisions that caused each event. Hide to reduce ambient noise during focused decision rounds.' },
];

const PEDAGOGICAL_TOGGLES = [
    { key: 'prediction_gates_enabled', label: 'Prediction Gates', icon: '🔮', tooltip: 'Pre-mortem prediction prompt before each decision. Players predict outcomes before committing — compared post-round. Klein (2007) Prospective Hindsight.', default: false },
    { key: 'confidence_calibration_enabled', label: 'Confidence Calibration', icon: '🎰', tooltip: 'Players rate their confidence (1-5) for each decision. Generates a calibration curve at R10 showing overconfidence/underconfidence patterns. Dunning-Kruger awareness.', default: false },
    { key: 'round_recap_enabled', label: 'Round Recap', icon: '📋', tooltip: 'Post-round "What Just Happened?" narrative showing the top 3 causal chains, stochastic vs strategic labelling, and a 3-word facilitator anchor.', default: false },
    { key: 'real_world_cards_enabled', label: 'Real-World Case Cards', icon: '🌍', tooltip: 'Displays real corporate case briefs (VW, Ørsted, Nike, etc.) paralleling each round\'s dilemma. Bridges simulation-reality transfer gap. Baldwin & Ford (1988).', default: false },
    { key: 'strategy_memo_enabled', label: 'Strategy Memo (R5)', icon: '📝', tooltip: 'Post-R5 structured writing exercise. Players assess position, identify risks, and justify resource allocation. Bloom\'s Create level.', default: false },
    { key: 'debrief_protocol_enabled', label: 'Debrief Protocol', icon: '🎭', tooltip: 'Thiagarajan (1993) three-phase structured debrief at R10: How Do You Feel? → What Happened? → So What / Now What?', default: false },
    { key: 'self_learning_mode', label: 'Self-Learning Mode', icon: '🎓', tooltip: 'Enables ALL pedagogical scaffolding automatically. Designed for facilitator-absent cohorts where the simulation must self-teach.', default: false },
];

const ENGINE_MODULE_TOGGLES = [
    { key: 'biodiversity_engine_enabled', label: 'Biodiversity', icon: '🌿', tooltip: 'TNFD-aligned ecosystem health tracking: EHI index, deforestation risk, water stress, and pollinator dependency.', default: true },
    { key: 'balance_sheet_enabled', label: 'Balance Sheet', icon: '📊', tooltip: 'Full double-entry balance sheet with assets, liabilities, D/E ratio, covenant monitoring, and working capital analysis.', default: true },
    { key: 'board_governance_enabled', label: 'Board Governance', icon: '🏛️', tooltip: 'Board of Directors simulation: director profiles, ESG alignment, voting resolutions, and activist investor pressure.', default: true },
    { key: 'supply_chain_network_enabled', label: 'Supply Chain', icon: '🔗', tooltip: '3-tier supply chain network with Scope 3 emissions estimation, supplier audit trails, and cascading risk.', default: true },
    { key: 'npc_stakeholders_enabled', label: 'NPC Agents', icon: '👥', tooltip: 'AI-ready NPC stakeholders (activist investor, regulator, community leader, media) reacting to player decisions.', default: true },
    { key: 'org_politics_enabled', label: 'Org Politics', icon: '🤝', tooltip: 'C-suite coalition dynamics: political capital, departmental resistance, and change management friction.', default: true },
    { key: 'branching_enabled', label: 'Branching (R5)', icon: '🔀', tooltip: 'Non-linear R5 branching: classifies players into archetypes with adaptive crisis severity.', default: true },
    { key: 'dynamic_cases_enabled', label: 'Case Injection', icon: '📰', tooltip: 'Contextual real-world case studies (BP, VW, Danone, Patagonia) triggered by matching game conditions.', default: true },
    { key: 'tcfd_scenarios_enabled', label: 'TCFD Analysis', icon: '🌡️', tooltip: 'TCFD-aligned climate scenario projections: orderly 1.5°C, disorderly 2°C, hothouse 4°C pathways.', default: true },
    { key: 'meadows_leverage_enabled', label: 'Leverage Points', icon: '🎯', tooltip: 'Donella Meadows leverage point analysis for post-game debrief and systemic intervention identification.', default: true },
    { key: 'system_archetypes_enabled', label: 'System Archetypes', icon: '🔄', tooltip: 'Peter Senge archetype detection: shifting the burden, fixes that fail, limits to growth.', default: true },
    { key: 'peer_learning_prompts_enabled', label: 'Peer Prompts', icon: '💬', tooltip: 'Mid-game (R5) and post-game (R10) peer reflection prompts for collaborative sense-making.', default: true },
    { key: 'decision_timer_enabled', label: 'Decision Timer', icon: '⏱️', tooltip: 'Cognitive pressure timer forcing decisions within a time limit. Simulates boardroom urgency.', default: false },
    { key: 'market_dynamics_enabled', label: 'Market Dynamics', icon: '📈', tooltip: 'Cross-player market: shared carbon credit pool, competitive talent hiring, scarcity pricing. Multiplayer only.', default: false },
    { key: 'regulatory_sandbox_enabled', label: 'Reg Sandbox', icon: '⚖️', tooltip: 'Expert-tier: students design carbon taxes, ETS, disclosure mandates with configurable parameters.', default: false },
    // Stakeholder realism waves (SPEC F1–F6) — default OFF; enable per cohort.
    // Recommended order: Memory → SLO Feedback → Promises, then the rest.
    { key: 'stakeholder_memory_enabled', label: 'Stakeholder Memory', icon: '🧠', tooltip: 'F1 — NPCs accumulate a trust stock (rises slowly, falls fast) with betrayal scars; trust gates escalation and cascades. Enable this first — the other waves build on it.', default: false },
    { key: 'stakeholder_slo_feedback_enabled', label: 'SLO Feedback', icon: '🔁', tooltip: 'F2 — each stakeholder\'s escalation tier continuously nudges the Social Licence of the BUs it is attached to, closing the reinforcing loop.', default: false },
    { key: 'stakeholder_engagement_enabled', label: 'Promises', icon: '🤝', tooltip: 'F5 — per-round engagement actions (town hall / public pledge / private commitment) with a promise ledger; kept promises pay off, broken ones scar trust.', default: false },
    { key: 'stakeholder_coalitions_enabled', label: 'Coalitions', icon: '🪧', tooltip: 'F3 — two or more hostile stakeholders form a coalition that amplifies SLO feedback and strike risk; fired cascades nudge their named targets (one hop).', default: false },
    { key: 'stakeholder_uncertainty_enabled', label: 'Uncertain Thresholds', icon: '🎲', tooltip: 'F4 — escalation thresholds jittered per cohort (seeded, so fair across teams) plus a patience clock that forces escalation over time.', default: false },
    { key: 'stakeholder_intel_ui_enabled', label: 'Intel Rail', icon: '🔎', tooltip: 'F6 — surfaces demand / leverage / trend cards per stakeholder; raw satisfaction and trust numbers stay in the facilitator view.', default: false },
];

const AccordionItem = ({ id, title, summary, children, isOpen, onToggle }) => {
    return (
        <div className={`${styles.accordionItem} ${isOpen ? styles.open : ''}`}>
            <button type="button" className={styles.accordionHeader} onClick={() => onToggle(id)}>
                <div className={styles.accHeaderContent}>
                    <span className={styles.accTitle}>{title}</span>
                    {!isOpen && summary && <span className={styles.accSummary}>{summary}</span>}
                </div>
                <span className={styles.accIcon}>{isOpen ? '▼' : '▶'}</span>
            </button>
            {isOpen && <div className={styles.accordionBody}>{children}</div>}
        </div>
    );
};

export default function CreateCohortModal({ isOpen, onClose, onCreated, currentFacilitatorId, currentFacilitatorRole = 'facilitator', editSession = null }) {
    const isSuperAdmin = currentFacilitatorRole === 'super_admin' || currentFacilitatorRole === 'admin';
    const isLeadFacilitator = currentFacilitatorRole === 'lead_facilitator';
    // F-6 (v3): project_admin is a PROVISIONING role, not a base facilitator.
    // The old catch-all sent it down the most-restricted branch (locked to
    // self, no facilitator assignment) — the opposite of its job — while the
    // registry entry point hardcoded "super_admin" for the same person.
    // Server ground truth (admin_router.py): the modal's sub-config chain and
    // GET /facilitators are require_facilitator (project_admin passes); only
    // the System Engine Modules section PATCHes require_super_admin — that
    // stays behind isSuperAdmin.
    const isProjectAdmin = currentFacilitatorRole === 'project_admin';
    const isBaseFacilitator = currentFacilitatorRole === 'facilitator' || (!isSuperAdmin && !isLeadFacilitator && !isProjectAdmin);
    // Who may assign the cohort to another facilitator (provisioning power):
    const canAssignFacilitator = isSuperAdmin || isProjectAdmin;
    const isEditMode = !!editSession; // true = editing existing cohort, false = creating new

    const [cohortName, setCohortName] = useState('');
    const [facilitatorId, setFacilitatorId] = useState('');
    const [availableFacilitators, setAvailableFacilitators] = useState([]);
    const [selectedParadigm, setSelectedParadigm] = useState('legacy_abc');

    // Cohort authorship (mandatory metadata)
    const [createdBy, setCreatedBy] = useState('');
    const [createdWhen, setCreatedWhen] = useState('');

    // Cohort scheduling
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    // Per-cohort experience level (unified preset replacing scenario_preset + difficulty_tier)
    const [scenarioPresets, setScenarioPresets] = useState([]);
    const [selectedExperienceLevel, setSelectedExperienceLevel] = useState('workshop_standard');
    const [pedagogyCustomised, setPedagogyCustomised] = useState(false);
    const [selectedCurrency, setSelectedCurrency] = useState('INR'); // stored as code

    // Ending Pathway
    const [endingPathways, setEndingPathways] = useState([]);
    const [selectedPathway, setSelectedPathway] = useState('activist_ultimatum');

    // CEO Interview
    const [ceoInterviewEnabled, setCeoInterviewEnabled] = useState(false);
    const [ceoVoiceGender, setCeoVoiceGender] = useState('female');
    const [elevenlabsStatus, setElevenlabsStatus] = useState(null);

    // Side Tracks
    const [sideTrackCatalog, setSideTrackCatalog] = useState([]);
    const [selectedSideTracks, setSelectedSideTracks] = useState([]);

    const [masterOverrides, setMasterOverrides] = useState([]);
    const [masterSwipes, setMasterSwipes] = useState([]);

    const [selectedOverrides, setSelectedOverrides] = useState([]);
    const [selectedSwipes, setSelectedSwipes] = useState([]);

    // Round Pacing
    const [pacingMode, setPacingMode] = useState('free_play');
    const [maxUnlockedRound, setMaxUnlockedRound] = useState(10);
    const [roundSchedules, setRoundSchedules] = useState({});

    // Advanced cohort controls (HIGH-tier) — persisted as cohort settings.
    const [rngSeed, setRngSeed] = useState('');                     // '' = non-deterministic
    const [resultsRevealRound, setResultsRevealRound] = useState(0);// 0 = always visible
    const [redactPeers, setRedactPeers] = useState(false);
    const [quizEnabled, setQuizEnabled] = useState(false);
    const [quizGraded, setQuizGraded] = useState(false);
    const [quizPassThreshold, setQuizPassThreshold] = useState(70);
    const [quizMaxAttempts, setQuizMaxAttempts] = useState(2);
    const [quizMandatory, setQuizMandatory] = useState(false);  // block decisions until the round's quiz is taken
    const [teamCount, setTeamCount] = useState(0);                  // 0 = unlimited
    const [maxTeamSize, setMaxTeamSize] = useState(0);              // 0 = unlimited
    const [joinMethod, setJoinMethod] = useState('code');           // code | open | roster
    const [joinCode, setJoinCode] = useState('');

    // MEDIUM-tier cohort controls — timers/timezone, late-join, report access.
    const [cohortTimezone, setCohortTimezone] = useState('');       // '' = browser-local
    const [roundTimerSeconds, setRoundTimerSeconds] = useState(0);  // 0 = no timer
    const [lateJoinPolicy, setLateJoinPolicy] = useState('anytime');// anytime | before_round_2 | closed
    const [reportAccess, setReportAccess] = useState('full');       // full | summary | facilitator_only

    // Clone-as-template: apply a saved settings template after creation, and/or
    // save this cohort's tuned settings under a name for future reuse.
    const [availableTemplates, setAvailableTemplates] = useState([]);
    const [applyTemplateId, setApplyTemplateId] = useState('');
    const [saveTemplateName, setSaveTemplateName] = useState('');

    // LOW-tier polish — accessibility defaults, branding, compliance, webhook.
    const [accHighContrast, setAccHighContrast] = useState(false);
    const [accFontScale, setAccFontScale] = useState(1.0);
    const [accReducedMotion, setAccReducedMotion] = useState(false);
    const [accColorblindSafe, setAccColorblindSafe] = useState(false);
    const [accScreenReader, setAccScreenReader] = useState(false);
    const [brandInstitution, setBrandInstitution] = useState('');
    const [brandLogoUrl, setBrandLogoUrl] = useState('');
    const [brandPrimaryColor, setBrandPrimaryColor] = useState('');
    const [dataRetentionDays, setDataRetentionDays] = useState(0);  // 0 = keep forever
    const [consentRequired, setConsentRequired] = useState(false);
    const [consentText, setConsentText] = useState('');
    const [webhookUrl, setWebhookUrl] = useState('');

    // Simulation mode & industry localisation
    const [simulationMode, setSimulationMode] = useState('conglomerate'); // 'conglomerate' | 'single_bu'
    const [industryVertical, setIndustryVertical] = useState('');
    const [regionId, setRegionId] = useState('');
    const [buRegions, setBuRegions] = useState({
        pharma: '',
        electronics: '',
        consumer_goods: '',
        software: '',
    });

    // Industry Vertical BU Substitution (cohort-formation-time)
    const [buSubstitutions, setBuSubstitutions] = useState({});

    // Analytics visibility per-cohort overrides
    const [visibilityDefaults, setVisibilityDefaults] = useState(null);
    const [visibility, setVisibility] = useState({
        facilitator: {},
        player: {},
    });

    const [engageAdvancedClimate, setEngageAdvancedClimate] = useState(false);
    const [carbonFee, setCarbonFee] = useState(40);
    const [hostility, setHostility] = useState(5);
    const [scope3, setScope3] = useState(2.5);

    const [pedagogicalToggles, setPedagogicalToggles] = useState(
        Object.fromEntries(PEDAGOGICAL_TOGGLES.map(t => [t.key, t.default]))
    );
    const [engineModuleToggles, setEngineModuleToggles] = useState(
        Object.fromEntries(ENGINE_MODULE_TOGGLES.map(t => [t.key, t.default]))
    );
    // difficultyTier is now derived from selectedExperienceLevel
    const [openTab, setOpenTab] = useState('core');

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const errorRef = useRef(null);

    // ═══ Phase R3 (V2-3): cohort setup integrity ════════════════════════
    // setupResults = { session, steps: [{name,url,payload,method,ok,error}] }
    // Non-null after a submit whose sub-config chain had failures — renders
    // the checklist panel with per-item retry instead of a dead-end string.
    const [setupResults, setSetupResults] = useState(null);
    const [retryingIdx, setRetryingIdx] = useState(null);

    // Scroll to error banner and open the relevant tab whenever an error is set
    const setValidationError = (msg, tab = null) => {
        setError(msg);
        if (tab) setOpenTab(tab);
        // Defer scroll so the DOM updates first
        setTimeout(() => errorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 80);
    };

    // lead_facilitator and super_admin may assign any registered track without
    // needing a global God Mode pre-authorization.
    const canAssignAllTracks = currentFacilitatorRole === 'lead_facilitator' || currentFacilitatorRole === 'super_admin';

    useEffect(() => {
        if (!isOpen) return;
        setError(null);
        setOpenTab('core');

        if (isEditMode && editSession) {
            // ── Edit mode: pre-populate from existing session ──
            setCohortName(editSession.cohort_name || '');
            setSelectedParadigm(editSession.decision_paradigm || 'legacy_abc');
            setSelectedCurrency(
                editSession.currency_symbol
                    ? (CURRENCIES.find(c => c.symbol === editSession.currency_symbol)?.code || 'INR')
                    : 'INR'
            );
            setCreatedBy(editSession.created_by || '');
            setCreatedWhen(editSession.created_when || new Date().toISOString().slice(0, 10));
            setStartDate(editSession.start_date || '');
            setEndDate(editSession.end_date || '');
            setSelectedPathway(editSession.ending_pathway || 'activist_ultimatum');
            setSimulationMode(editSession.simulation_mode === 'single_bu' ? 'single_bu' : 'conglomerate');
            setIndustryVertical(editSession.industry_vertical || '');
            setRegionId(editSession.region_id || '');
            setFacilitatorId(editSession.facilitator_id || currentFacilitatorId || '');
            setSelectedExperienceLevel(editSession.scenario_preset || editSession.experience_level || 'workshop_standard');
            setPedagogyCustomised(false);
            setEngageAdvancedClimate(editSession.simulation_mode === 'advanced_climate');
            setCarbonFee(editSession.global_carbon_fee ?? 40);
            setHostility(editSession.market_hostility_index ?? 5);
            setScope3(editSession.scope_3_threshold ?? 2.5);
            setBuSubstitutions(editSession.bu_substitutions || {});
        } else {
            // ── Create mode: reset to defaults ──
            setCohortName('');
            setSelectedExperienceLevel('workshop_standard');
            setPedagogyCustomised(false);
            setSelectedCurrency('INR');
            setSelectedParadigm('legacy_abc');
            setBuSubstitutions({});
            setCreatedBy('');
            setCreatedWhen(new Date().toISOString().slice(0, 10));
            setStartDate(new Date().toISOString().slice(0, 10));
            setEndDate('');
            setEngageAdvancedClimate(false);
            setCarbonFee(40);
            setHostility(5);
            setScope3(2.5);
        }

        // Fetch experience level presets
        fetch(`${API}/api/admin/scenario-presets`, { credentials: 'include' })
            .then(r => r.json()).then(d => {
                const presets = d.presets || [];
                setScenarioPresets(presets);
                // Auto-apply default preset's pedagogy
                const defaultPreset = presets.find(p => p.id === 'workshop_standard');
                if (defaultPreset?.default_pedagogy) {
                    setPedagogicalToggles(prev => ({ ...prev, ...defaultPreset.default_pedagogy }));
                }
            }).catch(() => {});

        // Fetch available ending pathways
        fetch(`${API}/api/admin/ending-pathways`, { credentials: 'include' })
            .then(r => r.json())
            .then(d => {
                setEndingPathways(d.pathways || []);
                setSelectedPathway(d.default || 'activist_ultimatum');
            })
            .catch(() => {});

        // Fetch CEO Interview state from global settings
        fetch(`${API}/api/admin/global-settings`, { credentials: 'include' })
            .then(r => r.json())
            .then(d => {
                setCeoInterviewEnabled(d.ceo_interview_enabled || false);
                setCeoVoiceGender(d.ceo_interview_voice_gender || 'female');
            })
            .catch(() => {});

        // Fetch ElevenLabs TTS API status
        fetch(`${API}/api/simulations/elevenlabs/status`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : null)
            .then(d => { if (d) setElevenlabsStatus(d); })
            .catch(() => {});

        // Fetch side track catalog
        fetch(`${API}/api/admin/side-tracks/catalog`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : null)
            .then(d => {
                if (d?.catalog) {
                    setSideTrackCatalog(d.catalog);
                    // Pre-select globally-enabled tracks
                    setSelectedSideTracks(d.catalog.filter(t => t.enabled_globally).map(t => t.track_id));
                }
            })
            .catch(() => {});

        // Fetch global analytics visibility defaults
        fetch(`${API}/api/admin/god/analytics-visibility`, { credentials: 'include' })
            .then(res => res.json())
            .then(data => {
                setVisibilityDefaults(data);
                setVisibility({
                    facilitator: { ...data.facilitator },
                    player: { ...data.player },
                });
            })
            .catch(() => {});

        // Fetch master lists
        fetch(`${API}/api/admin/interventions/master`, { credentials: 'include' })
            .then(res => res.json())
            .then(data => {
                setMasterOverrides(data.overrides || []);
                setMasterSwipes(data.swipes || []);
                // By default, select all
                setSelectedOverrides(data.overrides?.map(o => o.id) || []);
                setSelectedSwipes(data.swipes?.map(s => s.id) || []);
            })
            .catch(() => {});

        // Fetch saved cohort settings templates (clone-as-template)
        fetch(`${API}/api/admin/cohort-templates`, { credentials: 'include' })
            .then(r => r.ok ? r.json() : null)
            .then(d => { if (d?.templates) setAvailableTemplates(d.templates); })
            .catch(() => {});

        // Fetch facilitators
        fetch(`${API}/api/admin/facilitators`, { credentials: 'include' })
            .then(res => res.json())
            .then(data => {
                const facs = data.facilitators || [];
                setAvailableFacilitators(facs);
                const activeId = currentFacilitatorId || facilitatorId;
                if (activeId) {
                    const currentFac = facs.find(f => f.facilitator_id === activeId);
                    if (currentFac) {
                        if (currentFac.decision_paradigm) setSelectedParadigm(currentFac.decision_paradigm);
                        if (currentFac.ending_pathway) setSelectedPathway(currentFac.ending_pathway);
                        if (currentFac.side_tracks) setSelectedSideTracks(currentFac.side_tracks);
                        if (currentFac.simulation_mode) setSimulationMode(currentFac.simulation_mode);
                        if (currentFac.industry_vertical) setIndustryVertical(currentFac.industry_vertical);
                        if (currentFac.bu_substitutions) setBuSubstitutions(currentFac.bu_substitutions);
                        // Auto-populate Created By with facilitator's display name (create mode only)
                        if (!isEditMode && currentFac.name) setCreatedBy(currentFac.name);
                    }
                }
            })
            .catch(() => {});

        if (currentFacilitatorId && currentFacilitatorId !== 'project_admin') {
            // F-6 (v3): never default the assignment onto the project_admin
            // virtual account — it isn't an assignable facilitator. (When the
            // registry passes a real target facilitator id, prefill as before.)
            setFacilitatorId(currentFacilitatorId);
        }
    }, [isOpen, currentFacilitatorId]);

    if (!isOpen) return null;

    const toggleOverride = (id) => {
        setSelectedOverrides(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
    };

    const toggleSwipe = (id) => {
        setSelectedSwipes(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
    };

    // Backward-compat alias used in summary card (full catalog lookup)
    const INDUSTRY_VERTICALS = VERTICAL_CATALOG;


    const REGIONS = [
        { id: 'asean',         label: 'ASEAN',          flag: '🌏' },
        { id: 'south_asia',    label: 'India',           flag: '🇮🇳' },
        { id: 'china',         label: 'China',           flag: '🇨🇳' },
        { id: 'europe',        label: 'Europe',          flag: '🇪🇺' },
        { id: 'north_america', label: 'North America',   flag: '🇺🇸' },
        { id: 'africa',        label: 'Africa',          flag: '🌍' },
    ];

    // Cohort-level region options: extends REGIONS with the multi-region composite.
    // REGIONS itself stays clean for BU-level selects (which must be single regions).
    const COHORT_REGIONS = [
        ...REGIONS,
        { id: 'multi_region', label: 'Multi-Region', flag: '🌐', isComposite: true },
    ];

    // Derived flag — drives conditional UI and validation
    const isMultiRegion = regionId === 'multi_region';

    const PARADIGM_OPTIONS = [
        {
            id: 'legacy_abc',
            label: 'Narrative Crises',
            sub: 'A / B / C Choices',
            icon: '🏭',
            desc: 'Classic scenario-based rounds with structured A/B/C decision options. Best for standard MBA and leadership development.',
            color: '#6366f1',
            bg: 'rgba(99,102,241,0.1)',
            border: 'rgba(99,102,241,0.35)',
        },
        {
            id: 'multi_toggles',
            label: 'Strategic Pillars',
            sub: 'Toggle Investments',
            icon: '🎛️',
            desc: 'Players allocate investment across strategic pillars using toggles. No binary choices — continuous re-balancing.',
            color: '#f59e0b',
            bg: 'rgba(245,158,11,0.1)',
            border: 'rgba(245,158,11,0.3)',
        },
        {
            id: 'advanced_climate',
            label: 'Advanced Climate',
            sub: 'CSRD / ESG Engine',
            icon: '🌍',
            desc: 'CSRD-aligned simulation with Double Materiality Matrix, carbon accounting, and green transition fund mechanics.',
            color: '#10b981',
            bg: 'rgba(16,185,129,0.1)',
            border: 'rgba(16,185,129,0.3)',
        },
        {
            id: 'healthcare',
            label: 'Healthcare Edition',
            sub: 'Hospital BU Model',
            icon: '🏥',
            desc: 'Hospital and clinical network simulation. Business units are Hospitals, Clinics, Specialised Care, and Digital Health.',
            color: '#ef4444',
            bg: 'rgba(239,68,68,0.1)',
            border: 'rgba(239,68,68,0.3)',
        },
        {
            id: 'un_sdg',
            label: 'UN SDG Edition',
            sub: 'Sustainable Goals',
            icon: '🌐',
            desc: 'Strategy decisions are mapped to UN Sustainable Development Goals. Reputation is linked to SDG achievement scores.',
            color: '#0ea5e9',
            bg: 'rgba(14,165,233,0.1)',
            border: 'rgba(14,165,233,0.3)',
        },
        {
            id: 'brsr_ngrbc',
            label: 'BRSR NGRBC Edition',
            sub: 'India ESG Framework',
            icon: '🇮🇳',
            desc: 'A 10-round standalone paradigm focused on Business Responsibility and Sustainability Reporting under SEBI/NGRBC frameworks, defaulting display currency to Indian Rupees (₹).',
            color: '#f97316',
            bg: 'rgba(249,115,22,0.1)',
            border: 'rgba(249,115,22,0.3)',
        },
    ];

    const toggleVis = (role, key) => {
        setVisibility(prev => ({
            ...prev,
            [role]: { ...prev[role], [key]: !prev[role][key] },
        }));
    };

    // Check if any visibility setting differs from global defaults
    const hasVisibilityOverrides = () => {
        if (!visibilityDefaults) return false;
        for (const role of ['facilitator', 'player']) {
            for (const [key, val] of Object.entries(visibility[role] || {})) {
                if ((visibilityDefaults[role] || {})[key] !== val) return true;
            }
        }
        return false;
    };

    // ── Edit handler: PATCH metadata + re-apply all sub-configs ──────────────
    // ═══ Phase R3 (V2-3): ONE sub-config pipeline for create AND edit ═══
    // The two previous copies had already drifted (different warning
    // formats). Step ORDER and PAYLOADS are byte-identical to the pre-R3
    // chains; the only change is that outcomes are captured per step.
    const buildSubConfigSteps = (sid) => {
        const steps = [];
        if (hasVisibilityOverrides()) {
            steps.push({ name: 'Visibility', method: 'PUT', url: `${API}/api/admin/cohort/${sid}/analytics-visibility`, payload: visibility });
        }
        steps.push({
            name: 'Pedagogical Settings', method: 'PUT',
            url: `${API}/api/admin/cohort/${sid}/pedagogical-settings`,
            payload: {
                experience_level: selectedExperienceLevel,
                difficulty_tier: (scenarioPresets.find(pr => pr.id === selectedExperienceLevel) || {}).difficulty_tier || 'advanced',
                ...pedagogicalToggles,
                ...engineModuleToggles,
                // MEDIUM-tier: per-round timer duration. Setting a duration in
                // Advanced Controls also switches the Decision Timer toggle on.
                ...(roundTimerSeconds > 0 ? {
                    decision_timer_enabled: true,
                    decision_timer_seconds: roundTimerSeconds,
                } : {}),
            },
        });
        steps.push({
            name: 'CEO Interview', method: 'PUT',
            url: `${API}/api/admin/sessions/${sid}/ceo-interview`,
            payload: { ceo_interview_enabled: ceoInterviewEnabled, ceo_interview_voice_gender: ceoVoiceGender },
        });
        if (selectedSideTracks.length > 0) {
            steps.push({ name: 'Side Tracks', method: 'PUT', url: `${API}/api/admin/cohorts/${sid}/side-tracks`, payload: { tracks: selectedSideTracks } });
        }
        steps.push({
            name: 'Pacing', method: 'PUT',
            url: `${API}/api/admin/cohort/${sid}/pacing`,
            payload: {
                pacing_mode: pacingMode,
                max_unlocked_round: pacingMode === 'free_play' ? 10 : maxUnlockedRound,
                round_schedules: pacingMode === 'scheduled' ? roundSchedules : null,
            },
        });
        steps.push({
            name: 'Switchboard', method: 'PATCH',
            url: `${API}/api/admin/sessions/${sid}/cohort-settings`,
            payload: {
                simulation_mode: engageAdvancedClimate ? 'advanced_climate' : 'standard',
                global_carbon_fee: carbonFee,
                market_hostility_index: hostility,
                scope_3_threshold: scope3,
                // Advanced cohort controls (HIGH-tier). Backend clamps/coerces
                // these and stamps rng_seed onto the cohort's stochastic stream.
                rng_seed: rngSeed.trim(),
                results_reveal_round: resultsRevealRound,
                redact_peer_identities: redactPeers,
                quiz_enabled: quizEnabled,
                quiz_graded: quizGraded,
                quiz_pass_threshold: quizPassThreshold,
                quiz_max_attempts: quizMaxAttempts,
                quiz_mandatory: quizMandatory,
                team_count: teamCount,
                max_team_size: maxTeamSize,
                join_method: joinMethod,
                join_code: joinCode.trim(),
                // MEDIUM-tier controls. Backend validates the timezone against
                // the IANA db and clamps/coerces the rest. (The per-round timer
                // goes through the Pedagogical Settings step instead — it reuses
                // the engine's existing decision_timer toggles.)
                cohort_timezone: cohortTimezone.trim(),
                late_join_policy: lateJoinPolicy,
                report_access: reportAccess,
                // LOW-tier polish. Backend sanitises everything (https-only
                // URLs, hex-only colour, font scale clamped 0.8–1.6).
                accessibility_defaults: {
                    high_contrast: accHighContrast,
                    font_scale: accFontScale,
                    reduced_motion: accReducedMotion,
                    colorblind_safe: accColorblindSafe,
                    screen_reader_mode: accScreenReader,
                },
                branding_institution: brandInstitution.trim(),
                branding_logo_url: brandLogoUrl.trim(),
                branding_primary_color: brandPrimaryColor.trim(),
                data_retention_days: dataRetentionDays,
                consent_required: consentRequired,
                consent_text: consentText.trim(),
                webhook_url: webhookUrl.trim(),
            },
        });
        // Clone-as-template: apply a saved template's settings on top of the
        // switchboard (explicit switchboard values above win only where the
        // template doesn't set them — the template PATCH merges after).
        if (applyTemplateId) {
            steps.push({
                name: 'Apply Settings Template', method: 'POST',
                url: `${API}/api/admin/cohort-templates/${applyTemplateId}/apply/${sid}`,
                payload: {},
            });
        }
        // Save this cohort's tuned settings under a template name for reuse.
        if (saveTemplateName.trim()) {
            steps.push({
                name: 'Save As Template', method: 'POST',
                url: `${API}/api/admin/cohort-templates`,
                payload: { name: saveTemplateName.trim(), source_session_id: sid },
            });
        }
        if (Object.keys(buSubstitutions).length > 0 || Object.values(buRegions).some(v => v)) {
            steps.push({ name: 'BU Substitutions', method: 'PUT', url: `${API}/api/admin/${sid}/bu-composition`, payload: { substitutions: buSubstitutions, bu_regions: buRegions } });
        }
        return steps;
    };

    const runOneStep = async (step) => {
        try {
            const subRes = await fetch(step.url, {
                method: step.method,
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(step.payload),
            });
            if (!subRes.ok) {
                const errData = await subRes.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${subRes.status}`);
            }
            return { ...step, ok: true, error: null };
        } catch (err) {
            console.error(`[Cohort Config] Failed to apply ${step.name}:`, err);
            return { ...step, ok: false, error: err.message };
        }
    };

    // Sequential, same as the pre-R3 chains.
    const runSubConfigChain = async (sid) => {
        const results = [];
        for (const step of buildSubConfigSteps(sid)) {
            results.push(await runOneStep(step));
        }
        return results;
    };

    // Per-item retry: re-sends ONLY the failed step's identical payload.
    const retryStep = async (idx) => {
        setRetryingIdx(idx);
        const r = await runOneStep(setupResults.steps[idx]);
        setSetupResults(prev => ({ ...prev, steps: prev.steps.map((st, i) => (i === idx ? r : st)) }));
        setRetryingIdx(null);
    };

    // Leaving the panel — the cohort EXISTS either way, so the parent must
    // refresh; "Done" requires all-green, "Keep as-is" is the explicit escape.
    const finishSetup = () => {
        const sess = setupResults.session;
        setSetupResults(null);
        onCreated(sess);
    };

    const handleEdit = async (e) => {
        e.preventDefault();
        setError(null);
        if (!editSession?.session_id) return;
        setLoading(true);
        const sid = editSession.session_id;
        // Phase R3: sub-config execution moved to the shared pipeline above.

        try {
            // 1. PATCH core session metadata
            const metaRes = await fetch(`${API}/api/admin/sessions/${sid}/metadata`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    cohort_name: cohortName.trim() || editSession.cohort_name,
                    facilitator_id: facilitatorId,
                    decision_paradigm: selectedParadigm,
                    ending_pathway: selectedPathway || null,
                    created_by: createdBy.trim(),
                    created_when: createdWhen,
                    start_date: startDate || null,
                    end_date: endDate || null,
                    simulation_mode: simulationMode === 'single_bu' ? 'single_bu' : 'standard',
                    industry_vertical: simulationMode === 'single_bu' ? industryVertical : null,
                    region_id: regionId,
                    currency_symbol: (CURRENCIES.find(c => c.code === selectedCurrency) || CURRENCIES[0]).symbol,
                    scenario_preset: selectedExperienceLevel || null,
                    experience_level: selectedExperienceLevel || null,
                    difficulty_tier: (scenarioPresets.find(p => p.id === selectedExperienceLevel) || {}).difficulty_tier || 'advanced',
                }),
            });
            if (!metaRes.ok) {
                const d = await metaRes.json().catch(() => ({}));
                throw new Error(d.detail || `Metadata update failed (${metaRes.status})`);
            }

            // 2. Re-apply all sub-configs via the shared pipeline (same
            // endpoints, order, and payloads as before — outcomes per step).
            const results = await runSubConfigChain(sid);
            if (results.some(r => !r.ok)) {
                setSetupResults({
                    session: { session_id: sid, cohort_name: cohortName.trim() || editSession.cohort_name },
                    steps: results,
                });
            } else {
                onCreated({ session_id: sid, cohort_name: cohortName.trim() });
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        setError(null);

        // Validate mandatory fields
        if (!regionId) {
            setValidationError('Geographic Region is required. Please select a region.', 'core');
            return;
        }
        if (simulationMode === 'single_bu' && !industryVertical) {
            setValidationError('Industry Vertical is required for Single Business mode.', 'core');
            return;
        }
        // Multi-region mode: every BU slot must carry an explicit region because
        // there is no single cohort-level region to fall back to.
        if (isMultiRegion && simulationMode !== 'single_bu') {
            const BU_SLOTS = ['pharma', 'electronics', 'consumer_goods', 'software'];
            const unassigned = BU_SLOTS.filter(slot => !buRegions[slot]);
            if (unassigned.length > 0) {
                setValidationError(
                    `Multi-Region mode: all BU slots must have a region. Missing: ${unassigned.map(s => s.replace(/_/g, ' ')).join(', ')}.`,
                    'verticals'
                );
                return;
            }
        }

        setLoading(true);

        try {
            const res = await fetch(`${API}/api/simulations/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    cohort_name: cohortName.trim() || `Cohort_${Date.now()}`,
                    facilitator_id: facilitatorId,
                    decision_paradigm: selectedParadigm,
                    allowed_overrides: selectedOverrides,
                    allowed_swipes: selectedSwipes,
                    currency_symbol: (CURRENCIES.find(c => c.code === selectedCurrency) || CURRENCIES[0]).symbol,
                    scenario_preset: selectedExperienceLevel || null,
                    experience_level: selectedExperienceLevel || null,
                    difficulty_tier: (scenarioPresets.find(p => p.id === selectedExperienceLevel) || {}).difficulty_tier || 'advanced',
                    ending_pathway: selectedPathway || null,
                    created_by: createdBy.trim(),
                    created_when: createdWhen,
                    start_date: startDate || null,
                    end_date: endDate || null,
                    simulation_mode: simulationMode === 'single_bu' ? 'single_bu' : 'standard',
                    industry_vertical: simulationMode === 'single_bu' ? industryVertical : undefined,
                    region_id: regionId,
                })
            });

            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || `Failed to create cohort (${res.status})`);
            }

            const newSession = await res.json();

            // Phase R3: sub-configs via the shared pipeline (same endpoints,
            // order, and payloads as the previous inline copy — outcomes are
            // now captured per step, with retry, instead of one dead-end
            // warning string).
            const results = newSession.session_id ? await runSubConfigChain(newSession.session_id) : [];
            if (results.some(r => !r.ok)) {
                // StartSessionResponse carries session_id/state but NOT cohort_name,
                // so the summary header rendered an empty "" — stitch the name the
                // user just typed back in (the edit path already does this).
                setSetupResults({
                    session: { ...newSession, cohort_name: newSession.cohort_name || cohortName.trim() },
                    steps: results,
                });
            } else {
                onCreated(newSession);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.modal} style={{ position: 'relative' }}>
                {/* ═══ Phase R3 (V2-3): setup-integrity panel ═══
                    Shown when any sub-config step failed. The cohort EXISTS
                    at this point — this panel makes its true configuration
                    state explicit and recoverable instead of a dead-end
                    warning string. */}
                {setupResults && (
                    <div style={{
                        position: 'absolute', inset: 0, zIndex: 10,
                        background: 'var(--bg-card, #0f172a)', borderRadius: 'inherit',
                        display: 'flex', flexDirection: 'column',
                        padding: '1.5rem 1.75rem', overflowY: 'auto',
                    }}>
                        <h3 style={{ margin: '0 0 0.35rem', color: 'var(--text-primary)', fontSize: '1.05rem', fontWeight: 800 }}>
                            {setupResults.steps.every(st => st.ok)
                                ? '✅ Cohort setup complete'
                                : '⚠️ Cohort saved — but NOT fully configured'}
                        </h3>
                        <p style={{ margin: '0 0 1rem', color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: 1.5 }}>
                            &ldquo;{setupResults.session.cohort_name}&rdquo; exists and will run either way.
                            A failed item below means the cohort is on platform defaults for that
                            area — retry each one before running a live class with it.
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '1.25rem' }}>
                            {setupResults.steps.map((st, i) => (
                                <div key={st.name} style={{
                                    display: 'flex', alignItems: 'center', gap: '10px',
                                    padding: '8px 12px', borderRadius: '8px',
                                    background: st.ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
                                    border: `1px solid ${st.ok ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.3)'}`,
                                }}>
                                    <span style={{ width: 18, textAlign: 'center', fontWeight: 800, color: st.ok ? '#4ade80' : '#f87171' }}>{st.ok ? '✓' : '✗'}</span>
                                    <span style={{ flex: 1, fontWeight: 700, fontSize: '0.82rem', color: 'var(--text-primary)' }}>{st.name}</span>
                                    {!st.ok && (
                                        <span title={st.error} style={{ fontSize: '0.72rem', color: '#f87171', maxWidth: '42%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                            {st.error}
                                        </span>
                                    )}
                                    {!st.ok && (
                                        <button
                                            type="button"
                                            onClick={() => retryStep(i)}
                                            disabled={retryingIdx !== null}
                                            style={{
                                                padding: '4px 12px', borderRadius: '6px',
                                                border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.12)',
                                                color: '#f87171', fontWeight: 700, fontSize: '0.75rem',
                                                cursor: retryingIdx !== null ? 'wait' : 'pointer',
                                            }}
                                        >
                                            {retryingIdx === i ? '⏳ Retrying…' : '↻ Retry'}
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: 'auto' }}>
                            {!setupResults.steps.every(st => st.ok) && (
                                <button
                                    type="button"
                                    onClick={finishSetup}
                                    style={{
                                        padding: '0.55rem 1.1rem', borderRadius: '8px',
                                        border: '1px solid var(--border-subtle, #475569)', background: 'transparent',
                                        color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer',
                                    }}
                                >
                                    Keep as-is (failed settings stay unapplied)
                                </button>
                            )}
                            <button
                                type="button"
                                onClick={finishSetup}
                                disabled={!setupResults.steps.every(st => st.ok)}
                                style={{
                                    padding: '0.55rem 1.4rem', borderRadius: '8px', border: 'none',
                                    background: setupResults.steps.every(st => st.ok) ? '#22c55e' : 'rgba(34,197,94,0.2)',
                                    color: setupResults.steps.every(st => st.ok) ? '#fff' : 'rgba(255,255,255,0.4)',
                                    fontWeight: 800, fontSize: '0.85rem',
                                    cursor: setupResults.steps.every(st => st.ok) ? 'pointer' : 'not-allowed',
                                }}
                            >
                                ✓ Done
                            </button>
                        </div>
                    </div>
                )}
                <div className={styles.header} style={isEditMode ? { borderBottom: '2px solid rgba(251,191,36,0.4)', background: 'rgba(251,191,36,0.06)' } : {}}>
                    <h2>{isEditMode ? '✏️ Edit Cohort' : '🚀 Set Up New Cohort'}</h2>
                    {isEditMode && (
                        <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#fbbf24', background: 'rgba(251,191,36,0.12)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: '6px', padding: '3px 10px' }}>
                            Editing: {editSession?.cohort_name}
                        </span>
                    )}
                    <button className={styles.closeBtn} onClick={setupResults ? finishSetup : onClose} disabled={loading}>×</button>
                </div>

                <div className={styles.body}>
                    <form onSubmit={isEditMode ? handleEdit : handleCreate} className={styles.form}>
                        {error && <div ref={errorRef} className={styles.errorBox}>{error}</div>}

                        

                        
                                

                                

                        

                                

                        

                        

                        

                        
                        <AccordionItem id="core" title="1. Core Configuration" summary="Cohort Name, Facilitator, Scenario, & Currency" isOpen={openTab === 'core'} onToggle={(id) => setOpenTab(openTab === id ? null : id)}>
{/* ── Section 1: Core Details ── */}
                                <section className={styles.configSection}>
                                    <h3>1. Core Details</h3>
                                    <div className={styles.formGroup}>
                                        <label>Cohort Name / Identifier</label>
                                        <input
                                            type="text"
                                            value={cohortName}
                                            onChange={(e) => setCohortName(e.target.value)}
                                            placeholder="e.g. Exec MBA Spring 2026"
                                            required
                                        />
                                    </div>

{/* ── Simulation Mode toggle ── */}
                                    <div className={styles.formGroup}>
                                        <label>Simulation Mode</label>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            {[{v: 'conglomerate', label: '🏢 4-BU Conglomerate'}, {v: 'single_bu', label: '🏭 Single Business'}].map(m => (
                                                <button
                                                    key={m.v}
                                                    type="button"
                                                    onClick={() => setSimulationMode(m.v)}
                                                    style={{
                                                        flex: 1,
                                                        padding: '8px 12px',
                                                        borderRadius: '8px',
                                                        border: simulationMode === m.v ? '2px solid #6366f1' : '2px solid rgba(255,255,255,0.1)',
                                                        background: simulationMode === m.v ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.05)',
                                                        color: 'white',
                                                        cursor: 'pointer',
                                                        fontWeight: simulationMode === m.v ? 600 : 400,
                                                        transition: 'all 0.2s',
                                                    }}
                                                >{m.label}</button>
                                            ))}
                                        </div>
                                    </div>

{/* ── Industry Vertical (single_bu only) ── */}
                                    {simulationMode === 'single_bu' && (
                                        <div className={styles.formGroup}>
                                            <label>Industry Vertical <span style={{color:'#ef4444'}}>*</span></label>
                                            <small style={{ color: '#94a3b8', display: 'block', marginBottom: 4 }}>
                                                All verticals available — grouped by their simulation slot.
                                            </small>
                                            <select value={industryVertical} onChange={e => setIndustryVertical(e.target.value)} required>
                                                <option value="">-- Select Industry --</option>
                                                {SLOT_META.map(sm => {
                                                    const entries = VERTICAL_CATALOG.filter(v => v.slot === sm.slot);
                                                    return (
                                                        <optgroup key={sm.slot} label={`${sm.icon} ${sm.label} slot`}>
                                                            {entries.map(v => (
                                                                <option key={v.id} value={v.id}>
                                                                    {v.icon} {v.label}{v.isDefault ? '' : ' ↔'}
                                                                </option>
                                                            ))}
                                                        </optgroup>
                                                    );
                                                })}
                                            </select>
                                            {industryVertical && !VERTICAL_CATALOG.find(v => v.id === industryVertical)?.isDefault && (
                                                <small style={{ color: '#818cf8', marginTop: 3, display: 'block' }}>
                                                    ↔ Substitute: replaces the {SLOT_META.find(s => s.slot === VERTICAL_SLOT_MAP[industryVertical])?.label} slot in the seed.
                                                </small>
                                            )}
                                        </div>
                                    )}

{/* ── Geographic Region (always visible, mandatory) ── */}
                                    <div className={styles.formGroup}>
                                        <label>Geographic Region <span style={{color:'#ef4444'}}>*</span></label>
                                        <select value={regionId} onChange={e => setRegionId(e.target.value)} required>
                                            <option value="">-- Select Region --</option>
                                            {COHORT_REGIONS.map(r => (
                                                <option key={r.id} value={r.id}>{r.flag} {r.label}</option>
                                            ))}
                                        </select>
                                        <small style={{color: isMultiRegion ? '#f59e0b' : '#94a3b8'}}>
                                            {isMultiRegion
                                                ? '⚠ Multi-Region: each Business Unit must be assigned its own region in the Industry Verticals tab.'
                                                : 'Determines stakeholder grid, materiality matrix, and applicable regulations.'}
                                        </small>
                                    </div>

                                    <div className={styles.formGroup}>
                                        <label>Assigned Facilitator</label>
                                        {!canAssignFacilitator ? (
                                            <input
                                                type="text"
                                                value={currentFacilitatorId}
                                                disabled
                                                style={{ background: 'rgba(30,41,59,0.8)', color: '#94a3b8', border: '1px solid rgba(71,85,105,0.4)', borderRadius: 6, padding: '0.75rem 1rem' }}
                                            />
                                        ) : (
                                            <select
                                                value={facilitatorId}
                                                onChange={(e) => {
                                                    const selectedId = e.target.value;
                                                    setFacilitatorId(selectedId);
                                                    const facObj = availableFacilitators.find(f => f.facilitator_id === selectedId);
                                                    if (facObj) {
                                                        if (facObj.decision_paradigm) setSelectedParadigm(facObj.decision_paradigm);
                                                        if (facObj.ending_pathway) setSelectedPathway(facObj.ending_pathway);
                                                        if (facObj.side_tracks) setSelectedSideTracks(facObj.side_tracks);
                                                        if (facObj.simulation_mode) setSimulationMode(facObj.simulation_mode);
                                                        if (facObj.industry_vertical) setIndustryVertical(facObj.industry_vertical);
                                                        if (facObj.bu_substitutions) setBuSubstitutions(facObj.bu_substitutions);
                                                        // Keep Created By in sync with the selected facilitator's name
                                                        if (facObj.name) setCreatedBy(facObj.name);
                                                    }
                                                }}
                                                required
                                                className={styles.selectFacilitator}
                                            >
                                                <option value="" disabled>-- Select a Facilitator --</option>
                                                {availableFacilitators.map(fac => (
                                                    <option key={fac.facilitator_id} value={fac.facilitator_id}>
                                                        {fac.name} ({fac.facilitator_id})
                                                    </option>
                                                ))}
                                            </select>
                                        )}
                                    </div>

{/* ── Created By / When — auto-populated, not shown as inputs ── */}
                                    {/* createdBy is auto-set to the facilitator's name; createdWhen defaults to today */}

{/* ── Cohort Schedule (Start / End dates) ── */}
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 8 }}>
                                        <div className={styles.formGroup}>
                                            <label>
                                                Start Date
                                            </label>
                                            <input
                                                type="date"
                                                value={startDate}
                                                onChange={(e) => setStartDate(e.target.value)}
                                            />
                                            <span style={{ fontSize: '0.65rem', color: '#64748b', marginTop: 2 }}>
                                                Game accessible from this date (optional)
                                            </span>
                                        </div>
                                        <div className={styles.formGroup}>
                                            <label>
                                                End Date
                                            </label>
                                            <input
                                                type="date"
                                                value={endDate}
                                                onChange={(e) => setEndDate(e.target.value)}
                                                min={startDate || undefined}
                                            />
                                            <span style={{ fontSize: '0.65rem', color: '#64748b', marginTop: 2 }}>
                                                Game locked after this date — results stay visible
                                            </span>
                                        </div>
                                    </div>
                                </section>
{/* ── Section 3: Scenario & Display Currency ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>3. Scenario &amp; Display Currency</h3>
                                <p>Set the starting engine difficulty and the currency symbol shown on all monetary KPIs, investment panels, and reports for this cohort.</p>
                            </div>

{/* ── Experience Level (unified: engine difficulty + visibility + pedagogy) ── */}
                            {scenarioPresets.length > 0 && (
                                <div className={styles.formGroup}>
                                    <label>Experience Level</label>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 4 }}>
                                        {scenarioPresets.map(p => {
                                            const isSelected = selectedExperienceLevel === p.id;
                                            const presetColor = p.color || '#6366f1';
                                            return (
                                                <button
                                                    key={p.id}
                                                    type="button"
                                                    onClick={() => {
                                                        setSelectedExperienceLevel(p.id);
                                                        // Auto-apply preset pedagogy if user hasn't customised
                                                        if (!pedagogyCustomised && p.default_pedagogy) {
                                                            setPedagogicalToggles(prev => ({ ...prev, ...p.default_pedagogy }));
                                                        }
                                                    }}
                                                    style={{
                                                        display: 'flex', alignItems: 'center', gap: 12,
                                                        padding: '12px 16px', borderRadius: 10, cursor: 'pointer',
                                                        border: isSelected ? `2px solid ${presetColor}` : '1.5px solid rgba(100,116,139,0.3)',
                                                        background: isSelected ? `${presetColor}12` : 'rgba(15,23,42,0.5)',
                                                        transition: 'background 0.18s, color 0.18s, border-color 0.18s, box-shadow 0.18s, opacity 0.18s, transform 0.18s', textAlign: 'left', width: '100%',
                                                    }}
                                                >
                                                    <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{p.icon}</span>
                                                    <span style={{ flex: 1 }}>
                                                        <span style={{ display: 'block', fontWeight: 700, fontSize: '0.9rem', color: isSelected ? presetColor : '#e2e8f0' }}>
                                                            {p.name}
                                                            <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 8, color: isSelected ? presetColor : '#64748b', opacity: 0.85 }}>
                                                                {p.subtitle || ''}
                                                            </span>
                                                        </span>
                                                        <span style={{ display: 'block', fontSize: '0.72rem', color: isSelected ? '#cbd5e1' : '#64748b', marginTop: 2 }}>
                                                            {p.description}
                                                        </span>
                                                        {p.target_audience && (
                                                            <span style={{ display: 'block', fontSize: '0.65rem', color: isSelected ? presetColor : '#475569', marginTop: 3, fontStyle: 'italic' }}>
                                                                👥 {p.target_audience}
                                                            </span>
                                                        )}
                                                    </span>
                                                    {isSelected && (
                                                        <span style={{
                                                            fontSize: '0.72rem', fontWeight: 700, color: presetColor,
                                                            background: `${presetColor}18`, border: `1px solid ${presetColor}50`,
                                                            padding: '2px 8px', borderRadius: 999, whiteSpace: 'nowrap', flexShrink: 0,
                                                        }}>Selected</span>
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                    {selectedExperienceLevel && (() => {
                                        const sel = scenarioPresets.find(p => p.id === selectedExperienceLevel);
                                        return sel ? (
                                            <div style={{
                                                marginTop: 8, padding: '8px 12px', borderRadius: 8,
                                                background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(148,163,184,0.15)',
                                                fontSize: '0.7rem', color: '#94a3b8',
                                            }}>
                                                <strong style={{ color: '#cbd5e1' }}>This sets:</strong>{' '}
                                                Engine difficulty ({sel.name}) · Visibility tier ({sel.difficulty_tier}) ·{' '}
                                                {Object.entries(sel.default_pedagogy || {}).filter(([,v]) => v).map(([k]) =>
                                                    k.replace(/_enabled$/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                                                ).join(', ') || 'No scaffolding'} enabled by default
                                                {pedagogyCustomised && (
                                                    <span style={{ marginLeft: 6, color: '#f59e0b', fontWeight: 700 }}>⚙ Pedagogy customised</span>
                                                )}
                                            </div>
                                        ) : null;
                                    })()}
                                </div>
                            )}

                            {/* Currency Selector */}
                            <div className={styles.formGroup}>
                                <label>Display Currency</label>
                                <div style={{
                                    display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 6, marginTop: 4,
                                    background: 'rgba(255,255,255,0.02)', borderRadius: 10, padding: 6,
                                    border: '1px solid var(--border-subtle,#334155)',
                                }}>
                                    {CURRENCIES.map(c => {
                                        const isActive = c.code === selectedCurrency;
                                        return (
                                            <button
                                                key={c.code}
                                                type="button"
                                                onClick={() => setSelectedCurrency(c.code)}
                                                style={{
                                                    padding: '10px 4px', borderRadius: 8, cursor: 'pointer',
                                                    border: isActive ? '2px solid #6366f1' : '1.5px solid transparent',
                                                    background: isActive ? 'rgba(99,102,241,0.12)' : 'transparent',
                                                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
                                                    transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                                }}
                                                title={`${c.label} (${c.symbol})`}
                                            >
                                                <span style={{ fontSize: '1.25rem' }}>{c.flag}</span>
                                                <span style={{ fontWeight: 800, fontSize: '1rem', color: isActive ? '#818cf8' : '#e2e8f0' }}>{c.symbol}</span>
                                                <span style={{ fontSize: '0.6rem', color: isActive ? '#818cf8' : '#94a3b8', letterSpacing: '0.05em', fontWeight: 700 }}>{c.code}</span>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </section>
                        </AccordionItem>

                        {!isBaseFacilitator && (
                            <AccordionItem id="engine" title="2. Simulation Engine" summary="Decision Paradigm & Ending Pathway" isOpen={openTab === 'engine'} onToggle={(id) => setOpenTab(openTab === id ? null : id)}>
    {/* ── Section 2: Decision Paradigm ── */}
                                    <section className={styles.configSection}>
                                        <div className={styles.sectionHeader}>
                                            <h3>2. Decision Paradigm</h3>
                                            <p>
                                                Choose the simulation engine for this cohort.
                                                
                                            </p>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                            {PARADIGM_OPTIONS.map(p => {
                                                const isSelected = selectedParadigm === p.id;
                                                return (
                                                    <button
                                                        key={p.id}
                                                        type="button"
                                                        onClick={() => setSelectedParadigm(p.id)}
                                                        style={{
                                                            display: 'flex', alignItems: 'center', gap: 12,
                                                            padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                                                            border: isSelected ? `2px solid ${p.color}` : '1.5px solid rgba(100,116,139,0.3)',
                                                            background: isSelected ? p.bg : 'rgba(15,23,42,0.5)',
                                                            transition: 'background 0.18s, color 0.18s, border-color 0.18s, box-shadow 0.18s, opacity 0.18s, transform 0.18s',
                                                            textAlign: 'left', width: '100%',
                                                            opacity: 1,
                                                        }}
                                                    >
                                                        <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{p.icon}</span>
                                                        <span style={{ flex: 1 }}>
                                                            <span style={{ display: 'block', fontWeight: 700, fontSize: '0.88rem', color: isSelected ? p.color : '#e2e8f0' }}>
                                                                {p.label}
                                                                <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 6, color: isSelected ? p.color : '#64748b', opacity: 0.85 }}>({p.sub})</span>
                                                            </span>
                                                            <span style={{ display: 'block', fontSize: '0.72rem', color: isSelected ? '#cbd5e1' : '#64748b', marginTop: 2 }}>{p.desc}</span>
                                                        </span>
                                                        {isSelected && (
                                                            <span style={{
                                                                flexShrink: 0, fontSize: '0.68rem', fontWeight: 700,
                                                                padding: '2px 10px', borderRadius: 20,
                                                                background: p.bg, color: p.color,
                                                                border: `1px solid ${p.border}`,
                                                            }}>
                                                                Selected
                                                            </span>
                                                        )}
                                                    </button>
                                                );
                                            })}
                                        </div>
                                    </section>

                                    {/* ── Section 2b: Switchboard Parameters ── */}
                                    <section className={styles.configSection} style={{ marginTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1.25rem' }}>
                                        <div className={styles.sectionHeader}>
                                            <h3>⚙️ Simulation Switchboard</h3>
                                            <p>Configure default switchboard values and live engine variables for this cohort.</p>
                                        </div>

                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', background: 'rgba(255,255,255,0.02)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.04)' }}>
                                            {/* Advanced Climate Mode Toggle */}
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                <div>
                                                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0', display: 'block' }}>🌍 Advanced Climate Mode</span>
                                                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Activates the carbon tax, ETS credits, and carbon market dynamics.</span>
                                                </div>
                                                <div
                                                    onClick={() => setEngageAdvancedClimate(!engageAdvancedClimate)}
                                                    style={{
                                                        position: 'relative',
                                                        width: '38px',
                                                        height: '22px',
                                                        borderRadius: '11px',
                                                        cursor: 'pointer',
                                                        background: engageAdvancedClimate ? '#10b981' : '#475569',
                                                        transition: 'background 0.2s',
                                                    }}
                                                >
                                                    <div
                                                        style={{
                                                            position: 'absolute',
                                                            top: '2px',
                                                            left: engageAdvancedClimate ? '18px' : '2px',
                                                            width: '18px',
                                                            height: '18px',
                                                            borderRadius: '50%',
                                                            background: '#fff',
                                                            transition: 'left 0.2s',
                                                            boxShadow: '0 1px 2px rgba(0,0,0,0.2)',
                                                        }}
                                                    />
                                                </div>
                                            </div>

                                            {/* Global Carbon Fee Slider */}
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0' }}>💸 Global Carbon Fee</span>
                                                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#10b981' }}>{selectedCurrency === 'INR' ? '₹' : '$'}{carbonFee}/t</span>
                                                </div>
                                                <input
                                                    type="range"
                                                    min="20"
                                                    max="150"
                                                    step="5"
                                                    value={carbonFee}
                                                    onChange={(e) => setCarbonFee(parseInt(e.target.value, 10))}
                                                    style={{
                                                        width: '100%',
                                                        accentColor: '#10b981',
                                                        cursor: 'pointer',
                                                        background: 'rgba(255,255,255,0.1)',
                                                        height: '6px',
                                                        borderRadius: '3px',
                                                        outline: 'none',
                                                    }}
                                                />
                                                <span style={{ fontSize: '0.65rem', color: '#64748b' }}>Permitted tax bracket range: 20 to 150 carbon units.</span>
                                            </div>

                                            {/* Market Hostility Index Slider */}
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0' }}>🌋 Market Hostility Index</span>
                                                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f59e0b' }}>Level {hostility}/10</span>
                                                </div>
                                                <input
                                                    type="range"
                                                    min="1"
                                                    max="10"
                                                    step="1"
                                                    value={hostility}
                                                    onChange={(e) => setHostility(parseInt(e.target.value, 10))}
                                                    style={{
                                                        width: '100%',
                                                        accentColor: '#f59e0b',
                                                        cursor: 'pointer',
                                                        background: 'rgba(255,255,255,0.1)',
                                                        height: '6px',
                                                        borderRadius: '3px',
                                                        outline: 'none',
                                                    }}
                                                />
                                                <span style={{ fontSize: '0.65rem', color: '#64748b' }}>Determines competitor pricing strategy aggressiveness and supplier volatility.</span>
                                            </div>

                                            {/* Scope 3 Threshold Slider */}
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#e2e8f0' }}>🔗 Scope 3 Penalty Threshold</span>
                                                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#ef4444' }}>{scope3}x</span>
                                                </div>
                                                <input
                                                    type="range"
                                                    min="1.0"
                                                    max="5.0"
                                                    step="0.5"
                                                    value={scope3}
                                                    onChange={(e) => setScope3(parseFloat(e.target.value))}
                                                    style={{
                                                        width: '100%',
                                                        accentColor: '#ef4444',
                                                        cursor: 'pointer',
                                                        background: 'rgba(255,255,255,0.1)',
                                                        height: '6px',
                                                        borderRadius: '3px',
                                                        outline: 'none',
                                                    }}
                                                />
                                                <span style={{ fontSize: '0.65rem', color: '#64748b' }}>Cap multiplier on upstream supplier emissions before triggering Tier 3 supply chain penalties.</span>
                                            </div>
                                        </div>
                                    </section>

    {/* ── Section 3.5: Ending Pathway ── */}
                            {endingPathways.length > 0 && (
                                <section className={styles.configSection}>
                                    <div className={styles.sectionHeader}>
                                        <h3>🎯 Ending Pathway</h3>
                                        <p>Choose the R10 endgame crisis scenario. Players will never see the pathway name — only indirect hints between R5–R8.</p>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                        {/* Random option */}
                                        <button
                                            type="button"
                                            onClick={() => setSelectedPathway('random')}
                                            style={{
                                                display: 'flex', alignItems: 'center', gap: 10,
                                                padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                                                border: selectedPathway === 'random' ? '2px solid #a78bfa' : '1.5px solid rgba(100,116,139,0.3)',
                                                background: selectedPathway === 'random' ? 'rgba(167,139,250,0.1)' : 'rgba(15,23,42,0.5)',
                                                textAlign: 'left', width: '100%', transition: 'background 0.18s, color 0.18s, border-color 0.18s, box-shadow 0.18s, opacity 0.18s, transform 0.18s',
                                            }}
                                        >
                                            <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>🎲</span>
                                            <span style={{ flex: 1 }}>
                                                <span style={{ display: 'block', fontWeight: 700, fontSize: '0.88rem', color: selectedPathway === 'random' ? '#a78bfa' : '#e2e8f0' }}>
                                                    Random
                                                    <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 6, color: '#64748b' }}>(Surprise ending)</span>
                                                </span>
                                                <span style={{ display: 'block', fontSize: '0.72rem', color: '#64748b', marginTop: 2 }}>System randomly selects a pathway at session creation. Maximum surprise for facilitator and players.</span>
                                            </span>
                                        </button>
                                        {/* Pathway options */}
                                        {endingPathways.filter(p => p.implemented).map(p => {
                                            const isSelected = selectedPathway === p.id;
                                            return (
                                                <button
                                                    key={p.id}
                                                    type="button"
                                                    onClick={() => setSelectedPathway(p.id)}
                                                    style={{
                                                        display: 'flex', alignItems: 'center', gap: 10,
                                                        padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                                                        border: isSelected ? '2px solid #6366f1' : '1.5px solid rgba(100,116,139,0.3)',
                                                        background: isSelected ? 'rgba(99,102,241,0.1)' : 'rgba(15,23,42,0.5)',
                                                        textAlign: 'left', width: '100%', transition: 'background 0.18s, color 0.18s, border-color 0.18s, box-shadow 0.18s, opacity 0.18s, transform 0.18s',
                                                        opacity: p.implemented ? 1 : 0.4,
                                                    }}
                                                    disabled={!p.implemented}
                                                >
                                                    <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{p.icon}</span>
                                                    <span style={{ flex: 1 }}>
                                                        <span style={{ display: 'block', fontWeight: 700, fontSize: '0.88rem', color: isSelected ? '#818cf8' : '#e2e8f0' }}>
                                                            {p.title}
                                                            {!p.implemented && <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 6, color: '#f59e0b' }}>(Coming Soon)</span>}
                                                        </span>
                                                        <span style={{ display: 'block', fontSize: '0.72rem', color: isSelected ? '#cbd5e1' : '#64748b', marginTop: 2, lineHeight: 1.4 }}>{p.description?.substring(0, 120)}{p.description?.length > 120 ? '…' : ''}</span>
                                                    </span>
                                                    {isSelected && (
                                                        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#818cf8', background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.3)', padding: '2px 8px', borderRadius: 999, whiteSpace: 'nowrap', flexShrink: 0 }}>Selected</span>
                                                    )}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </section>
                            )}
                            </AccordionItem>
                        )}

                        {!isBaseFacilitator && simulationMode !== 'single_bu' && (
                            <AccordionItem id="verticals" title="2b. Industry Verticals" summary="Optional: Replace default BUs with industry-specific units" isOpen={openTab === 'verticals'} onToggle={(id) => setOpenTab(openTab === id ? null : id)}>
{/* ── BU Vertical Substitution (selected at cohort creation) ── */}
                            <section className={styles.configSection}>
                                <div className={styles.sectionHeader}>
                                    <h3>🏭 Industry Vertical Selection</h3>
                                    <p>
                                        Optionally replace default Muressons business units with industry-specific verticals.
                                        This changes the stakeholder map, materiality matrix, and engine parameters.
                                        <strong> Cannot be changed after the simulation begins.</strong>
                                    </p>
                                </div>
                                {/* Derived from VERTICAL_CATALOG: adding a new vertical to the catalog
                                    automatically populates it here in its slot's row. */}
                                {SLOT_META.map(sm => {
                                    const alternatives = VERTICAL_CATALOG.filter(v => v.slot === sm.slot && !v.isDefault);
                                    const slot = sm.slot;
                                    const slotLabel = sm.label;
                                    const slotIcon = sm.icon;
                                    return ({ slot, slotLabel, slotIcon, alternatives });
                                }).map(({ slot, slotLabel, slotIcon, alternatives }) => {
                                    const currentVertical = buSubstitutions[slot] || '';
                                    return (
                                        <div key={slot} className={styles.formGroup} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.75rem' }}>
                                            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, fontSize: '0.85rem' }}>
                                                <span>{slotIcon}</span>
                                                Business Unit Slot: {slotLabel}
                                            </label>
                                            <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                                                {/* Default option */}
                                                <button
                                                    type="button"
                                                    onClick={() => setBuSubstitutions(prev => {
                                                        const copy = { ...prev };
                                                        delete copy[slot];
                                                        return copy;
                                                    })}
                                                    style={{
                                                        padding: '6px 12px', borderRadius: 8,
                                                        border: !currentVertical ? '2px solid #6366f1' : '1.5px solid rgba(100,116,139,0.3)',
                                                        background: !currentVertical ? 'rgba(99,102,241,0.1)' : 'rgba(15,23,42,0.5)',
                                                        color: 'white', cursor: 'pointer', fontSize: '0.75rem', fontWeight: !currentVertical ? 600 : 400,
                                                        transition: 'all 0.15s',
                                                    }}
                                                >
                                                    Standard {slotLabel}
                                                </button>
                                                {/* Substitute options */}
                                                {alternatives.map(alt => {
                                                    const isSelected = currentVertical === alt.id;
                                                    return (
                                                        <button
                                                            key={alt.id}
                                                            type="button"
                                                            onClick={() => setBuSubstitutions(prev => ({ ...prev, [slot]: alt.id }))}
                                                            style={{
                                                                padding: '6px 12px', borderRadius: 8,
                                                                border: isSelected ? '2px solid #6366f1' : '1.5px solid rgba(100,116,139,0.3)',
                                                                background: isSelected ? 'rgba(99,102,241,0.1)' : 'rgba(15,23,42,0.5)',
                                                                color: 'white', cursor: 'pointer', fontSize: '0.75rem', fontWeight: isSelected ? 600 : 400,
                                                                transition: 'all 0.15s',
                                                            }}
                                                            title={alt.desc}
                                                        >
                                                            {alt.icon} {alt.label}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                            {/* Per-BU Region — optional override in standard mode, required in Multi-Region mode */}
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8 }}>
                                                <span style={{
                                                    fontSize: '0.72rem',
                                                    color: isMultiRegion && !buRegions[slot] ? '#ef4444' : isMultiRegion ? '#67e8f9' : 'var(--text-muted)',
                                                    fontWeight: isMultiRegion ? 600 : 400,
                                                }}>
                                                    📍 {isMultiRegion ? 'BU Region' : 'Local Region override:'}
                                                    {isMultiRegion && <span style={{ color: '#ef4444', marginLeft: 2 }}>*</span>}
                                                </span>
                                                <select
                                                    value={buRegions[slot] || ''}
                                                    onChange={e => setBuRegions(prev => ({ ...prev, [slot]: e.target.value }))}
                                                    style={{
                                                        width: 'auto', padding: '3px 8px', fontSize: '0.72rem',
                                                        borderRadius: 4, color: 'white',
                                                        background: 'rgba(15,23,42,0.6)',
                                                        border: isMultiRegion && !buRegions[slot]
                                                            ? '1.5px solid rgba(239,68,68,0.7)'
                                                            : '1px solid rgba(100,116,139,0.3)',
                                                    }}
                                                >
                                                    {/* In Multi-Region mode, hide the fallback option — a selection is mandatory */}
                                                    {!isMultiRegion && (
                                                        <option value="">Same as Cohort ({regionId ? (REGIONS.find(r => r.id === regionId)?.label || regionId) : 'None'})</option>
                                                    )}
                                                    {isMultiRegion && !buRegions[slot] && (
                                                        <option value="" disabled>-- Select region --</option>
                                                    )}
                                                    {REGIONS.map(r => (
                                                        <option key={r.id} value={r.id}>{r.flag} {r.label}</option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>
                                    );
                                })}
                        </section>
                        </AccordionItem>
                        )}

                        {!isBaseFacilitator && (
                            <AccordionItem id="modules" title="3. Optional Modules" summary="Engine Modules, Side Tracks & CEO" isOpen={openTab === 'modules'} onToggle={(id) => setOpenTab(openTab === id ? null : id)}>
{/* ── Engine Module Toggles ── */}
                        {isSuperAdmin && (
                            <section className={styles.configSection}>
                                <div className={styles.sectionHeader}>
                                    <h3>🔬 System Engine Modules</h3>
                                    <p>Toggle high-fidelity engines ON/OFF for this cohort. Disabled engines are safely skipped — no crash risk.</p>
                                </div>
                                <div style={{
                                    display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6,
                                }}>
                                    {ENGINE_MODULE_TOGGLES.map(t => {
                                        const isOn = engineModuleToggles[t.key];
                                        return (
                                            <button
                                                key={t.key}
                                                type="button"
                                                title={t.tooltip}
                                                onClick={() => setEngineModuleToggles(prev => ({ ...prev, [t.key]: !prev[t.key] }))}
                                                style={{
                                                    display: 'flex', alignItems: 'center', gap: 6,
                                                    padding: '7px 10px', borderRadius: 8, cursor: 'pointer',
                                                    border: isOn ? '1.5px solid rgba(16,185,129,0.4)' : '1.5px solid rgba(100,116,139,0.2)',
                                                    background: isOn ? 'rgba(16,185,129,0.08)' : 'rgba(15,23,42,0.3)',
                                                    transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s', textAlign: 'left',
                                                }}
                                            >
                                                <span style={{ fontSize: '1rem', flexShrink: 0 }}>{t.icon}</span>
                                                <span style={{
                                                    flex: 1, fontSize: '0.72rem', fontWeight: 700,
                                                    color: isOn ? '#4ade80' : '#64748b',
                                                }}>
                                                    {t.label}
                                                </span>
                                                <span style={{
                                                    width: 8, height: 8, borderRadius: '50%',
                                                    background: isOn ? '#10b981' : '#334155',
                                                    flexShrink: 0,
                                                }} />
                                            </button>
                                        );
                                    })}
                                </div>
                                <div style={{ marginTop: 6, display: 'flex', gap: 8 }}>
                                    <button type="button" onClick={() => setEngineModuleToggles(Object.fromEntries(ENGINE_MODULE_TOGGLES.map(t => [t.key, true])))}
                                        style={{ fontSize: '0.65rem', color: '#10b981', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 700 }}>
                                        ● Enable All
                                    </button>
                                    <button type="button" onClick={() => setEngineModuleToggles(Object.fromEntries(ENGINE_MODULE_TOGGLES.map(t => [t.key, false])))}
                                        style={{ fontSize: '0.65rem', color: '#ef4444', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 700 }}>
                                        ○ Disable All
                                    </button>
                                    <button type="button" onClick={() => setEngineModuleToggles(Object.fromEntries(ENGINE_MODULE_TOGGLES.map(t => [t.key, t.default])))}
                                        style={{ fontSize: '0.65rem', color: '#94a3b8', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 700 }}>
                                        ↺ Reset Defaults
                                    </button>
                                </div>
                            </section>
                        )}
{/* ── Section 3.9: Side Tracks ── */}
                        {sideTrackCatalog.length > 0 && (
                            <section className={styles.configSection}>
                                <div className={styles.sectionHeader}>
                                    <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                        🛤️ Side Track Simulations
                                        {canAssignAllTracks && (
                                            <span style={{
                                                fontSize: '0.62rem', fontWeight: 700, padding: '2px 7px',
                                                borderRadius: 999, background: 'rgba(99,102,241,0.15)',
                                                color: '#818cf8', border: '1px solid rgba(99,102,241,0.3)',
                                            }}>
                                                All tracks unlocked for your role
                                            </span>
                                        )}
                                    </h3>
                                    <p>
                                        Enable optional mini-simulations that run alongside the main game. Players can access these between rounds.
                                        {!canAssignAllTracks && (
                                            <span style={{ color: '#f59e0b', marginLeft: 4 }}>
                                                Greyed-out tracks require God Mode authorization — ask a super_admin to enable them globally.
                                            </span>
                                        )}
                                    </p>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                    {sideTrackCatalog.map(track => {
                                        const isSelected = selectedSideTracks.includes(track.track_id);
                                        // Lead facilitators and super admins can always assign; regular facilitators
                                        // need the track to be globally enabled or explicitly permitted.
                                        const canAssign = canAssignAllTracks || track.enabled_globally || track.facilitator_can_assign;
                                        return (
                                            <button
                                                key={track.track_id}
                                                type="button"
                                                disabled={!canAssign}
                                                title={!canAssign ? 'Requires God Mode authorization — ask a super_admin to enable this track globally' : ''}
                                                onClick={() => {
                                                    if (!canAssign) return;
                                                    setSelectedSideTracks(prev =>
                                                        prev.includes(track.track_id)
                                                            ? prev.filter(t => t !== track.track_id)
                                                            : [...prev, track.track_id]
                                                    );
                                                }}
                                                style={{
                                                    display: 'flex', alignItems: 'center', gap: 10,
                                                    padding: '10px 14px', borderRadius: 10,
                                                    cursor: canAssign ? 'pointer' : 'not-allowed',
                                                    border: isSelected ? '2px solid #6366f1' : '1.5px solid rgba(100,116,139,0.3)',
                                                    background: isSelected ? 'rgba(99,102,241,0.1)' : 'rgba(15,23,42,0.5)',
                                                    textAlign: 'left', width: '100%',
                                                    transition: 'background 0.18s, color 0.18s, border-color 0.18s, box-shadow 0.18s, opacity 0.18s, transform 0.18s',
                                                    opacity: canAssign ? 1 : 0.4,
                                                }}
                                            >
                                                <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>{track.icon || '📦'}</span>
                                                <span style={{ flex: 1 }}>
                                                    <span style={{ display: 'block', fontWeight: 700, fontSize: '0.88rem', color: isSelected ? '#818cf8' : '#e2e8f0' }}>
                                                        {track.display_name || track.track_id}
                                                        <span style={{ fontWeight: 400, fontSize: '0.72rem', marginLeft: 6, color: '#64748b' }}>
                                                            ({track.num_rounds || '?'} rounds)
                                                        </span>
                                                        {!track.enabled_globally && canAssign && (
                                                            <span style={{ marginLeft: 6, fontSize: '0.62rem', color: '#f59e0b', fontWeight: 600 }}>
                                                                ● Lead-only
                                                            </span>
                                                        )}
                                                    </span>
                                                    <span style={{ display: 'block', fontSize: '0.72rem', color: isSelected ? '#cbd5e1' : '#64748b', marginTop: 2 }}>
                                                        {track.description?.substring(0, 140) || 'No description available'}
                                                    </span>
                                                </span>
                                                <div style={{
                                                    width: 32, height: 18, borderRadius: 9, flexShrink: 0,
                                                    background: isSelected ? '#6366f1' : 'rgba(100,116,139,0.3)',
                                                    position: 'relative', transition: 'background 0.15s',
                                                }}>
                                                    <div style={{
                                                        width: 14, height: 14, borderRadius: 7,
                                                        background: '#fff', position: 'absolute', top: 2,
                                                        left: isSelected ? 16 : 2,
                                                        transition: 'left 0.15s',
                                                    }} />
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                                {selectedSideTracks.length > 0 && (
                                    <div style={{ marginTop: 6, fontSize: '0.68rem', color: '#818cf8', fontWeight: 600 }}>
                                        ✓ {selectedSideTracks.length} side track{selectedSideTracks.length !== 1 ? 's' : ''} will be activated for this cohort
                                    </div>
                                )}
                            </section>
                        )}
{/* ── Section 3.7: CEO Interview ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <div>
                                    <h3 style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                        🎤 Post-Game CEO Interview
                                    </h3>
                                    <p>Optional AI-driven competency assessment after R10. Players are interviewed by the CEO and scored on 6 dimensions.</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={async () => {
                                        const next = !ceoInterviewEnabled;
                                        setCeoInterviewEnabled(next);
                                        try {
                                            await fetch(`${API}/api/admin/global-settings`, {
                                                method: 'PATCH',
                                                headers: { 'Content-Type': 'application/json' },
                                                credentials: 'include',
                                                body: JSON.stringify({ ceo_interview_enabled: next }),
                                            });
                                        } catch {}
                                    }}
                                    style={{
                                        padding: '5px 14px', borderRadius: 8, border: 'none',
                                        background: ceoInterviewEnabled ? '#10b981' : 'rgba(148,163,184,0.15)',
                                        color: ceoInterviewEnabled ? '#fff' : '#94a3b8',
                                        fontWeight: 800, fontSize: '0.72rem', cursor: 'pointer',
                                        transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s', flexShrink: 0,
                                    }}
                                >
                                    {ceoInterviewEnabled ? '● ENABLED' : '○ DISABLED'}
                                </button>
                            </div>
                            {ceoInterviewEnabled && (
                                <div style={{
                                    display: 'flex', flexDirection: 'column', gap: '0.5rem',
                                    padding: '0.6rem 1rem', marginTop: '0.4rem',
                                    background: 'rgba(16,185,129,0.04)',
                                    border: '1px solid rgba(16,185,129,0.15)',
                                    borderRadius: 8,
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                        <span style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600 }}>CEO Voice:</span>
                                        <select
                                            value={ceoVoiceGender}
                                            onChange={async (e) => {
                                                setCeoVoiceGender(e.target.value);
                                                try {
                                                    await fetch(`${API}/api/admin/global-settings`, {
                                                        method: 'PATCH',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        credentials: 'include',
                                                        body: JSON.stringify({ ceo_interview_voice_gender: e.target.value }),
                                                    });
                                                } catch {}
                                            }}
                                            style={{
                                                padding: '3px 8px', borderRadius: 6, fontSize: '0.72rem',
                                                border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
                                                color: 'var(--text-primary)', fontWeight: 600, cursor: 'pointer',
                                            }}
                                        >
                                            <option value="female">👩‍💼 Victoria Muressons (Female)</option>
                                            <option value="male">👨‍💼 Alexander Muressons (Male)</option>
                                        </select>
                                        <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                                            5 questions · 6-dimension spider diagram · narrative feedback
                                        </span>
                                    </div>
                                    {/* ElevenLabs TTS Status */}
                                    <div style={{
                                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                                        padding: '0.5rem 0.8rem', borderRadius: 6,
                                        background: elevenlabsStatus?.available
                                            ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                                        border: `1px solid ${elevenlabsStatus?.available
                                            ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                                    }}>
                                        <span style={{ fontSize: '1rem' }}>
                                            {elevenlabsStatus?.available ? '🔊' : '🔇'}
                                        </span>
                                        <div style={{ flex: 1 }}>
                                            <div style={{
                                                fontSize: '0.68rem', fontWeight: 700,
                                                color: elevenlabsStatus?.available ? '#10b981' : '#ef4444',
                                            }}>
                                                ElevenLabs TTS {elevenlabsStatus?.available ? 'Connected' : 'Unavailable'}
                                            </div>
                                            <div style={{ fontSize: '0.6rem', color: '#64748b', marginTop: 1 }}>
                                                {elevenlabsStatus?.available
                                                    ? `${((elevenlabsStatus.subscription?.remaining || 0) / 1000).toFixed(0)}K characters remaining · Voice synthesis active`
                                                    : (elevenlabsStatus?.error || 'API key not configured — interview will use text-only mode')}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </section>
                        </AccordionItem>
                        )}

                        {!isBaseFacilitator && (
                            <AccordionItem id="interventions" title="4. Team Interventions" summary="Manual Overrides, Swipe Files & Round Pacing" isOpen={openTab === 'interventions'} onToggle={(id) => setOpenTab(openTab === id ? null : id)}>
{/* ── Section 4: Team Interventions ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>4. Team Interventions Configuration</h3>
                                <p>Select which specific Master Interventions are exposed for this session.</p>
                            </div>

                            <div className={styles.splitLists}>
                                <div className={styles.listCol}>
                                    <h4>⚡ Manual Overrides ({selectedOverrides.length}/{masterOverrides.length})</h4>
                                    <div className={styles.checkboxList}>
                                        {masterOverrides.map(ov => (
                                            <label key={ov.id} className={styles.checkboxItem}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedOverrides.includes(ov.id)}
                                                    onChange={() => toggleOverride(ov.id)}
                                                />
                                                <span className={styles.checkText}>
                                                    {ov.icon} {ov.title}
                                                </span>
                                            </label>
                                        ))}
                                        {masterOverrides.length === 0 && <div className={styles.empty}>No overrides defined globally.</div>}
                                    </div>
                                </div>

                                <div className={styles.listCol}>
                                    <h4>✉️ Swipe Files ({selectedSwipes.length}/{masterSwipes.length})</h4>
                                    <div className={styles.checkboxList}>
                                        {masterSwipes.map(sw => (
                                            <label key={sw.id} className={styles.checkboxItem}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedSwipes.includes(sw.id)}
                                                    onChange={() => toggleSwipe(sw.id)}
                                                />
                                                <span className={styles.checkText}>
                                                    {sw.icon} {sw.label}
                                                </span>
                                            </label>
                                        ))}
                                        {masterSwipes.length === 0 && <div className={styles.empty}>No swipe files defined globally.</div>}
                                    </div>
                                </div>
                            </div>
                        </section>

{/* ── Round Pacing Configuration ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>Round Pacing</h3>
                                <p>Control how rounds are unlocked for players in this cohort.</p>
                            </div>

                            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                                {[
                                    { id: 'free_play', icon: '🔓', label: 'Free Play', desc: 'All rounds unlocked immediately' },
                                    { id: 'manual', icon: '✋', label: 'Manual', desc: 'Facilitator unlocks each round' },
                                    { id: 'scheduled', icon: '📅', label: 'Scheduled', desc: 'Pre-schedule unlocks for all rounds' },
                                ].map(mode => (
                                    <div
                                        key={mode.id}
                                        onClick={() => setPacingMode(mode.id)}
                                        style={{
                                            flex: '1 1 160px',
                                            padding: '12px 14px',
                                            borderRadius: 10,
                                            border: pacingMode === mode.id
                                                ? '2px solid var(--accent-blue, #3b82f6)'
                                                : '1px solid var(--border-subtle)',
                                            background: pacingMode === mode.id
                                                ? 'rgba(59,130,246,0.08)'
                                                : 'var(--bg-card)',
                                            cursor: 'pointer',
                                            transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                        }}
                                    >
                                        <div style={{ fontSize: '1rem', marginBottom: 4 }}>{mode.icon} <strong style={{ color: 'var(--text-primary)' }}>{mode.label}</strong></div>
                                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>{mode.desc}</div>
                                    </div>
                                ))}
                            </div>

                            {pacingMode === 'manual' && (
                                <div style={{ marginTop: 12 }} className={styles.formGroup}>
                                    <label>Unlock Up To Round</label>
                                    <select
                                        value={maxUnlockedRound}
                                        onChange={e => setMaxUnlockedRound(Number(e.target.value))}
                                        className={styles.selectFacilitator}
                                    >
                                        {[...Array(10)].map((_, i) => (
                                            <option key={i + 1} value={i + 1}>Round {i + 1}</option>
                                        ))}
                                    </select>
                                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>
                                        Players can play up to this round. You can change this later from the dashboard.
                                    </span>
                                </div>
                            )}

                            {pacingMode === 'scheduled' && (
                                <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Round Unlock Schedule</label>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', maxHeight: '200px', overflowY: 'auto', paddingRight: '4px' }}>
                                        {[...Array(10)].map((_, i) => (
                                            <div key={i + 1} style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--bg-card)', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                                                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', width: '60px' }}>Round {i + 1}</span>
                                                <input
                                                    type="datetime-local"
                                                    value={roundSchedules[i + 1] || ''}
                                                    onChange={e => setRoundSchedules(prev => ({ ...prev, [i + 1]: e.target.value }))}
                                                    style={{ flex: 1, padding: '4px 8px', borderRadius: '4px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.75rem' }}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 2 }}>
                                        Rounds will automatically unlock for players at the specified times.
                                    </span>
                                </div>
                            )}
                        </section>

                        
                            </AccordionItem>
                        )}

                        <AccordionItem id="pedagogy" title="5. Pedagogy &amp; Analytics" summary="Toggles and Visibility" isOpen={openTab === 'pedagogy'} onToggle={(id) => setOpenTab(openTab === id ? null : id)}>
{/* ── Section 5: Pedagogical Scaffolding ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>5. Pedagogical Scaffolding</h3>
                                <p>Fine-tune metacognitive and formative assessment features.
                                    {selectedExperienceLevel && (() => {
                                        const sel = scenarioPresets.find(p => p.id === selectedExperienceLevel);
                                        return sel ? <span style={{ color: sel.color || '#6366f1', fontWeight: 600 }}> Defaults from: {sel.icon} {sel.name}</span> : null;
                                    })()}
                                    {pedagogyCustomised && <span style={{ color: '#f59e0b', fontWeight: 600, marginLeft: 6 }}>⚙ Customised</span>}
                                </p>
                            </div>

                            <div className={styles.visSection}>
                                <div className={styles.visRoleLabel}>🧠 Pedagogical Features</div>
                                <div className={styles.visGrid}>
                                    {PEDAGOGICAL_TOGGLES.map(t => (
                                        <div
                                            key={t.key}
                                            className={`${styles.visCard} ${pedagogicalToggles[t.key] ? styles.visCardActive : ''}`}
                                            onClick={() => {
                                                setPedagogicalToggles(prev => ({ ...prev, [t.key]: !prev[t.key] }));
                                                setPedagogyCustomised(true);
                                            }}
                                            data-tooltip={t.tooltip}
                                        >
                                            <span className={styles.visIcon}>{t.icon}</span>
                                            <span className={styles.visLabel}>{t.label}</span>
                                            <div className={styles.visToggleTrack}
                                                style={{ background: pedagogicalToggles[t.key] ? '#10b981' : '#475569' }}
                                            >
                                                <div className={styles.visToggleThumb}
                                                    style={{ left: pedagogicalToggles[t.key] ? '14px' : '2px' }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </section>
{/* ── Section 6: Analytics Visibility ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>6. Analytics Visibility</h3>
                                <p>Choose which analytics panels are visible for this cohort. Changes override the global defaults.</p>
                            </div>

                            <div className={styles.visSection}>
                                <div className={styles.visRoleLabel}>🎓 Facilitator Dashboard</div>
                                <div className={styles.visGrid}>
                                    {FACILITATOR_ANALYTICS.map(a => (
                                        <div
                                            key={a.key}
                                            className={`${styles.visCard} ${visibility.facilitator[a.key] ? styles.visCardActive : ''}`}
                                            onClick={() => toggleVis('facilitator', a.key)}
                                            data-tooltip={a.tooltip}
                                        >
                                            <span className={styles.visIcon}>{a.icon}</span>
                                            <span className={styles.visLabel}>{a.label}</span>
                                            <div className={styles.visToggleTrack}
                                                style={{ background: visibility.facilitator[a.key] ? '#10b981' : '#475569' }}
                                            >
                                                <div className={styles.visToggleThumb}
                                                    style={{ left: visibility.facilitator[a.key] ? '14px' : '2px' }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>

                                <div className={styles.visRoleLabel}>👤 Player Dashboard</div>
                                <div className={styles.visGrid}>
                                    {PLAYER_ANALYTICS.map(a => (
                                        <div
                                            key={a.key}
                                            className={`${styles.visCard} ${visibility.player[a.key] ? styles.visCardActive : ''}`}
                                            onClick={() => toggleVis('player', a.key)}
                                            data-tooltip={a.tooltip}
                                        >
                                            <span className={styles.visIcon}>{a.icon}</span>
                                            <span className={styles.visLabel}>{a.label}</span>
                                            <div className={styles.visToggleTrack}
                                                style={{ background: visibility.player[a.key] ? '#10b981' : '#475569' }}
                                            >
                                                <div className={styles.visToggleThumb}
                                                    style={{ left: visibility.player[a.key] ? '14px' : '2px' }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </section>
{/* ── Section 7: Advanced Controls (Quiz · Result Visibility · Teams · RNG Seed · Time/Timezone · Report Access · Templates) ── */}
                        <section className={styles.configSection}>
                            <div className={styles.sectionHeader}>
                                <h3>7. Advanced Controls</h3>
                                <p>Quizzes &amp; grading, result-visibility gating, team/roster limits, and a fair-play RNG seed. All optional; sensible defaults keep behaviour unchanged.</p>
                            </div>

                            {(() => {
                                const fld = { display: 'flex', flexDirection: 'column', gap: 4, minWidth: 150 };
                                const lbl = { fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', letterSpacing: '0.03em', textTransform: 'uppercase' };
                                const inp = { padding: '0.4rem 0.6rem', borderRadius: 8, border: '1px solid #334155', background: 'rgba(15,23,42,0.6)', color: '#e2e8f0', fontSize: '0.82rem' };
                                const row = { display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end', marginBottom: '1rem' };
                                const grp = { fontSize: '0.7rem', fontWeight: 800, color: '#c7d2fe', letterSpacing: '0.04em', textTransform: 'uppercase', margin: '0.2rem 0 0.5rem' };
                                const chk = (checked, onClick, label, hint) => (
                                    <div onClick={onClick} style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', padding: '0.35rem 0.1rem' }} data-tooltip={hint}>
                                        <div style={{ width: 34, height: 20, borderRadius: 10, background: checked ? '#10b981' : '#475569', position: 'relative', transition: 'background .15s', flexShrink: 0 }}>
                                            <div style={{ width: 16, height: 16, borderRadius: '50%', background: '#fff', position: 'absolute', top: 2, left: checked ? 16 : 2, transition: 'left .15s' }} />
                                        </div>
                                        <span style={{ fontSize: '0.82rem', color: '#e2e8f0' }}>{label}</span>
                                    </div>
                                );
                                return (
                                    <div>
                                        {/* Quiz & grading */}
                                        <div style={grp}>📝 Quiz &amp; Grading</div>
                                        <div style={row}>
                                            {chk(quizEnabled, () => setQuizEnabled(v => !v), 'Enable quizzes', 'Surface knowledge-check quizzes (quiz banks) to players.')}
                                            {chk(quizGraded, () => setQuizGraded(v => !v), 'Count toward grade', 'Include quiz scores in the cohort gradebook.')}
                                            {chk(quizMandatory, () => setQuizMandatory(v => !v), 'Mandatory', 'Block a player from committing their decisions until they have taken that round’s quiz. Rounds with no quiz are unaffected; passing is not required, so a struggling student is never permanently blocked.')}
                                            <div style={fld}>
                                                <label style={lbl}>Pass threshold (%)</label>
                                                <input type="number" min={0} max={100} step={5} value={quizPassThreshold} disabled={!quizEnabled}
                                                    onChange={e => setQuizPassThreshold(Number(e.target.value))} style={{ ...inp, width: 90, opacity: quizEnabled ? 1 : 0.5 }} />
                                            </div>
                                            <div style={fld}>
                                                <label style={lbl}>Max attempts</label>
                                                <input type="number" min={1} max={20} value={quizMaxAttempts} disabled={!quizEnabled}
                                                    onChange={e => setQuizMaxAttempts(Number(e.target.value))} style={{ ...inp, width: 90, opacity: quizEnabled ? 1 : 0.5 }} />
                                            </div>
                                        </div>

                                        {/* Result visibility */}
                                        <div style={grp}>👁 Result Visibility</div>
                                        <div style={row}>
                                            <div style={fld}>
                                                <label style={lbl}>Reveal results at round</label>
                                                <input type="number" min={0} max={10} value={resultsRevealRound}
                                                    onChange={e => setResultsRevealRound(Number(e.target.value))} style={{ ...inp, width: 110 }}
                                                    data-tooltip="Hide leaderboard, peer ranks and final valuation from players until this round. 0 = always visible; 10 = only at the finale." />
                                                <span style={{ fontSize: '0.66rem', color: '#64748b' }}>0 = always · 10 = finale only</span>
                                            </div>
                                            {chk(redactPeers, () => setRedactPeers(v => !v), 'Redact peer identities', 'Anonymise other teams in peer/benchmark views.')}
                                        </div>

                                        {/* Teams / roster */}
                                        <div style={grp}>👥 Teams &amp; Roster</div>
                                        <div style={row}>
                                            <div style={fld}>
                                                <label style={lbl}>Team count</label>
                                                <input type="number" min={0} max={500} value={teamCount}
                                                    onChange={e => setTeamCount(Number(e.target.value))} style={{ ...inp, width: 90 }} data-tooltip="Hard roster cap enforced when players join. 0 = platform default (5 players)." />
                                            </div>
                                            <div style={fld}>
                                                <label style={lbl}>Max team size</label>
                                                <input type="number" min={0} max={100} value={maxTeamSize}
                                                    onChange={e => setMaxTeamSize(Number(e.target.value))} style={{ ...inp, width: 90 }} data-tooltip="0 = unlimited." />
                                            </div>
                                            <div style={fld}>
                                                <label style={lbl}>Join method</label>
                                                <select value={joinMethod} onChange={e => setJoinMethod(e.target.value)} style={{ ...inp, width: 150 }}>
                                                    <option value="code">Join code</option>
                                                    <option value="open">Open link</option>
                                                    <option value="roster">Roster only</option>
                                                </select>
                                            </div>
                                            <div style={fld}>
                                                <label style={lbl}>Join code</label>
                                                <input type="text" value={joinCode} placeholder="auto" disabled={joinMethod !== 'code'}
                                                    onChange={e => setJoinCode(e.target.value)} style={{ ...inp, width: 130, opacity: joinMethod === 'code' ? 1 : 0.5 }} />
                                            </div>
                                        </div>

                                        {/* RNG seed */}
                                        <div style={grp}>🎲 Fair-Play RNG Seed</div>
                                        <div style={row}>
                                            <div style={{ ...fld, minWidth: 260 }}>
                                                <label style={lbl}>Stochastic seed</label>
                                                <input type="text" value={rngSeed} placeholder="blank = random each run"
                                                    onChange={e => setRngSeed(e.target.value)} style={{ ...inp, width: 260 }}
                                                    data-tooltip="A non-empty seed makes every stochastic event roll identically for all teams — rankings reflect strategy, not luck. Leave blank for legacy non-deterministic behaviour." />
                                                <span style={{ fontSize: '0.66rem', color: '#64748b' }}>Same seed ⇒ identical rolls for every team (fair comparison).</span>
                                            </div>
                                        </div>

                                        {/* Time & scheduling */}
                                        <div style={grp}>⏱️ Time &amp; Scheduling</div>
                                        <div style={row}>
                                            <div style={fld}>
                                                <label style={lbl}>Cohort timezone</label>
                                                <input type="text" value={cohortTimezone} placeholder="e.g. Asia/Kolkata (blank = local)"
                                                    onChange={e => setCohortTimezone(e.target.value)} style={{ ...inp, width: 210 }}
                                                    data-tooltip="IANA timezone used to render schedules and timers in the cohort's local time. Backend rejects unknown zones. Blank = each player's browser-local time." />
                                            </div>
                                            <div style={fld}>
                                                <label style={lbl}>Round timer (sec)</label>
                                                <input type="number" min={0} max={7200} value={roundTimerSeconds}
                                                    onChange={e => setRoundTimerSeconds(Number(e.target.value))} style={{ ...inp, width: 100 }}
                                                    data-tooltip="Per-round decision timer duration. Setting a value also enables the Decision Timer engine toggle (0 = leave the toggle's own setting in charge)." />
                                            </div>
                                            <div style={fld}>
                                                <label style={lbl}>Late joins</label>
                                                <select value={lateJoinPolicy} onChange={e => setLateJoinPolicy(e.target.value)} style={{ ...inp, width: 170 }}
                                                    data-tooltip="Enforced server-side at join. Rejoining players are never blocked.">
                                                    <option value="anytime">Allowed anytime</option>
                                                    <option value="before_round_2">Until Round 1 ends</option>
                                                    <option value="closed">Closed</option>
                                                </select>
                                            </div>
                                        </div>

                                        {/* Report access */}
                                        <div style={grp}>📄 Player Report Access</div>
                                        <div style={row}>
                                            <div style={fld}>
                                                <label style={lbl}>Final report visibility</label>
                                                <select value={reportAccess} onChange={e => setReportAccess(e.target.value)} style={{ ...inp, width: 230 }}
                                                    data-tooltip="Server-enforced. 'Summary' keeps headline numbers but withholds the narrative report bodies; 'Facilitator only' shows players a locked notice — you reveal it during the debrief.">
                                                    <option value="full">Full report (default)</option>
                                                    <option value="summary">Summary — numbers only</option>
                                                    <option value="facilitator_only">Facilitator only</option>
                                                </select>
                                            </div>
                                        </div>

                                        {/* Settings templates */}
                                        <div style={grp}>📦 Settings Template</div>
                                        <div style={row}>
                                            <div style={fld}>
                                                <label style={lbl}>Apply saved template</label>
                                                <select value={applyTemplateId} onChange={e => setApplyTemplateId(e.target.value)} style={{ ...inp, width: 230 }}
                                                    data-tooltip="Applies a previously saved cohort's settings to this cohort after creation — same validation as manual edits.">
                                                    <option value="">None</option>
                                                    {availableTemplates.map(t => (
                                                        <option key={t.template_id} value={t.template_id}>{t.name}</option>
                                                    ))}
                                                </select>
                                            </div>
                                            <div style={{ ...fld, minWidth: 230 }}>
                                                <label style={lbl}>Save these settings as</label>
                                                <input type="text" value={saveTemplateName} placeholder="e.g. Spring 2026 MBA setup"
                                                    onChange={e => setSaveTemplateName(e.target.value)} style={{ ...inp, width: 230 }}
                                                    data-tooltip="After creation, this cohort's settings are saved under this name for one-click reuse on future cohorts. Leave blank to skip." />
                                            </div>
                                        </div>

                                        {/* Accessibility defaults */}
                                        <div style={grp}>♿ Accessibility Defaults</div>
                                        <div style={row}>
                                            {chk(accHighContrast, () => setAccHighContrast(v => !v), 'High contrast', 'Brightens secondary text and strengthens borders for low-vision players.')}
                                            {chk(accReducedMotion, () => setAccReducedMotion(v => !v), 'Reduced motion', 'Collapses animations and transitions — vestibular-safe.')}
                                            {chk(accColorblindSafe, () => setAccColorblindSafe(v => !v), 'Colourblind-safe palette', 'Charts and badges switch to a blue/orange palette instead of red/green.')}
                                            {chk(accScreenReader, () => setAccScreenReader(v => !v), 'Screen-reader mode', 'Always-visible focus outlines and denser ARIA labelling.')}
                                            <div style={fld}>
                                                <label style={lbl}>Font scale</label>
                                                <select value={String(accFontScale)} onChange={e => setAccFontScale(Number(e.target.value))} style={{ ...inp, width: 110 }}
                                                    data-tooltip="Baseline text-size multiplier for the whole cockpit (players inherit it as their default).">
                                                    <option value="0.9">90%</option>
                                                    <option value="1">100%</option>
                                                    <option value="1.15">115%</option>
                                                    <option value="1.3">130%</option>
                                                    <option value="1.5">150%</option>
                                                </select>
                                            </div>
                                        </div>

                                        {/* White-label branding */}
                                        <div style={grp}>🏷️ White-Label Branding</div>
                                        <div style={row}>
                                            <div style={fld}>
                                                <label style={lbl}>Institution name</label>
                                                <input type="text" value={brandInstitution} placeholder="e.g. IIM Ahmedabad"
                                                    onChange={e => setBrandInstitution(e.target.value)} style={{ ...inp, width: 200 }}
                                                    data-tooltip="Shown in the player cockpit header and on reports. Blank = platform default." />
                                            </div>
                                            <div style={fld}>
                                                <label style={lbl}>Logo URL (https)</label>
                                                <input type="text" value={brandLogoUrl} placeholder="https://…/logo.png"
                                                    onChange={e => setBrandLogoUrl(e.target.value)} style={{ ...inp, width: 220 }}
                                                    data-tooltip="https-only; anything else is rejected server-side." />
                                            </div>
                                            <div style={fld}>
                                                <label style={lbl}>Accent colour</label>
                                                <input type="text" value={brandPrimaryColor} placeholder="#1E90FF"
                                                    onChange={e => setBrandPrimaryColor(e.target.value)} style={{ ...inp, width: 100 }}
                                                    data-tooltip="Hex #RRGGBB only. Blank = default theme." />
                                            </div>
                                        </div>

                                        {/* Compliance */}
                                        <div style={grp}>🔐 Data Retention &amp; Consent</div>
                                        <div style={row}>
                                            <div style={fld}>
                                                <label style={lbl}>Retention (days)</label>
                                                <input type="number" min={0} max={3650} value={dataRetentionDays}
                                                    onChange={e => setDataRetentionDays(Number(e.target.value))} style={{ ...inp, width: 100 }}
                                                    data-tooltip="Cohort data (incl. player sessions) is deleted this many days after the cohort's end date. 0 = keep forever (default). Players can export their own data any time via the API." />
                                            </div>
                                            {chk(consentRequired, () => setConsentRequired(v => !v), 'Require consent at join', 'New players must accept the consent statement before joining; acceptance is timestamped on their session.')}
                                            <div style={{ ...fld, minWidth: 260 }}>
                                                <label style={lbl}>Consent statement</label>
                                                <input type="text" value={consentText} placeholder="default statement" disabled={!consentRequired}
                                                    onChange={e => setConsentText(e.target.value)} style={{ ...inp, width: 260, opacity: consentRequired ? 1 : 0.5 }} />
                                            </div>
                                        </div>

                                        {/* Webhook / LMS */}
                                        <div style={grp}>🔗 Webhook / LMS Sync</div>
                                        <div style={row}>
                                            <div style={{ ...fld, minWidth: 280 }}>
                                                <label style={lbl}>Webhook URL (https)</label>
                                                <input type="text" value={webhookUrl} placeholder="https://lms.example.edu/hooks/muressons"
                                                    onChange={e => setWebhookUrl(e.target.value)} style={{ ...inp, width: 280 }}
                                                    data-tooltip="POSTed fire-and-forget on lifecycle events (round committed, game over) so an LMS/gradebook can sync without polling. https-only; blank = disabled." />
                                            </div>
                                        </div>
                                    </div>
                                );
                            })()}
                        </section>

                        </AccordionItem>

                        <AccordionItem id="lock" title="6. Summary & Lock Configuration" summary="Review and permanently lock choices for this cohort" isOpen={openTab === 'lock'} onToggle={(id) => setOpenTab(openTab === id ? null : id)}>
                            {(() => {
                                // ── Derived values for summary display ──
                                const facId = currentFacilitatorId || facilitatorId;
                                const facObj = availableFacilitators.find(f => f.facilitator_id === facId);
                                const facilitatorDisplay = facObj ? `${facObj.name} (${facId})` : facId || '—';
                                const presetInfo = scenarioPresets.find(p => p.id === selectedExperienceLevel);
                                const currencyInfo = CURRENCIES.find(c => c.code === selectedCurrency);
                                const paradigmInfo = PARADIGM_OPTIONS.find(p => p.id === selectedParadigm);
                                const pathwayInfo = selectedPathway === 'random'
                                    ? { icon: '🎲', title: 'Random (Surprise)' }
                                    : endingPathways.find(p => p.id === selectedPathway);
                                const enabledModules = ENGINE_MODULE_TOGGLES.filter(t => engineModuleToggles[t.key]);
                                // Region & BU lookups for Core Config card
                                const regionInfo = COHORT_REGIONS.find(r => r.id === regionId);
                                const regionDisplay = regionInfo ? `${regionInfo.flag} ${regionInfo.label}` : (regionId ? regionId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : null);
                                const buInfo = INDUSTRY_VERTICALS.find(v => v.id === industryVertical);
                                const buDisplay = buInfo ? `${buInfo.icon} ${buInfo.label}` : (industryVertical ? industryVertical.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : null);
                                const nonDefaultModules = ENGINE_MODULE_TOGGLES.filter(t => engineModuleToggles[t.key] !== t.default);
                                const selectedTrackDetails = sideTrackCatalog.filter(t => selectedSideTracks.includes(t.track_id));
                                const enabledPedagogy = PEDAGOGICAL_TOGGLES.filter(t => pedagogicalToggles[t.key]);
                                const visOverrideCount = (() => {
                                    if (!visibilityDefaults) return 0;
                                    let n = 0;
                                    for (const role of ['facilitator', 'player']) {
                                        for (const [k, v] of Object.entries(visibility[role] || {})) {
                                            if ((visibilityDefaults[role] || {})[k] !== v) n++;
                                        }
                                    }
                                    return n;
                                })();

                                // ── Shared micro-styles ──
                                const cardS = {
                                    background: 'rgba(15,23,42,0.65)',
                                    border: '1px solid rgba(100,116,139,0.22)',
                                    borderRadius: 10, padding: '11px 13px',
                                };
                                const headS = {
                                    display: 'flex', alignItems: 'center',
                                    justifyContent: 'space-between',
                                    marginBottom: 8, paddingBottom: 7,
                                    borderBottom: '1px solid rgba(100,116,139,0.14)',
                                };
                                const titleS = {
                                    fontSize: '0.64rem', fontWeight: 800,
                                    color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.07em',
                                };
                                const editS = {
                                    fontSize: '0.6rem', fontWeight: 700, color: '#6366f1',
                                    background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.28)',
                                    borderRadius: 5, padding: '2px 8px', cursor: 'pointer',
                                };
                                const rowS = { display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: '0.71rem', lineHeight: 1.45 };
                                const lblS = { color: '#64748b', flexShrink: 0, minWidth: 88 };
                                const valS = { color: '#e2e8f0', fontWeight: 600, flex: 1, wordBreak: 'break-word' };
                                const onChip = { display: 'inline-block', padding: '1px 6px', borderRadius: 999, fontSize: '0.6rem', fontWeight: 700, background: 'rgba(16,185,129,0.12)', color: '#4ade80', border: '1px solid rgba(16,185,129,0.28)', marginRight: 3, marginBottom: 2 };
                                const offChip = { display: 'inline-block', padding: '1px 6px', borderRadius: 999, fontSize: '0.6rem', fontWeight: 700, background: 'rgba(100,116,139,0.1)', color: '#64748b', border: '1px solid rgba(100,116,139,0.2)', marginRight: 3, marginBottom: 2 };
                                const indigoChip = { display: 'inline-block', padding: '1px 6px', borderRadius: 999, fontSize: '0.6rem', fontWeight: 700, background: 'rgba(99,102,241,0.14)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.28)', marginRight: 3, marginBottom: 2 };

                                return (
                                    <div style={{ padding: '0.5rem 0' }}>

                                        {/* ── Summary cards grid ── */}
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>

                                            {/* Card 1 — Core Configuration */}
                                            <div style={cardS}>
                                                <div style={headS}>
                                                    <span style={titleS}>📋 Core Configuration</span>
                                                    <button type="button" style={editS} onClick={() => setOpenTab('core')}>✎ Edit</button>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Cohort</span>
                                                        <span style={{ ...valS, color: cohortName.trim() ? '#e2e8f0' : '#ef4444' }}>
                                                            {cohortName.trim() || '⚠ Name required'}
                                                        </span>
                                                    </div>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Facilitator</span>
                                                        <span style={valS}>{facilitatorDisplay}</span>
                                                    </div>
                                                    {createdBy.trim() && (
                                                        <div style={rowS}>
                                                            <span style={lblS}>Created By</span>
                                                            <span style={valS}>{createdBy}</span>
                                                        </div>
                                                    )}
                                                    <div style={rowS}>
                                                        <span style={lblS}>Dates</span>
                                                        <span style={valS}>
                                                            {startDate || createdWhen || '—'}
                                                            {endDate ? ` → ${endDate}` : ''}
                                                        </span>
                                                    </div>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Region</span>
                                                        <span style={{ ...valS, color: regionDisplay ? '#67e8f9' : '#f59e0b' }}>
                                                            {regionDisplay || '⚠ Not selected'}
                                                        </span>
                                                    </div>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Business Unit</span>
                                                        <span style={{ ...valS, color: simulationMode === 'single_bu' ? (buDisplay ? '#a5b4fc' : '#f59e0b') : '#64748b' }}>
                                                            {simulationMode === 'single_bu'
                                                                ? (buDisplay || '⚠ Not selected')
                                                                : '🏢 4-BU Conglomerate (default)'}
                                                        </span>
                                                    </div>
                                                    {presetInfo && (
                                                        <div style={rowS}>
                                                            <span style={lblS}>Level</span>
                                                            <span style={valS}>
                                                                {presetInfo.icon} {presetInfo.name}
                                                                {pedagogyCustomised && <span style={{ marginLeft: 5, fontSize: '0.6rem', color: '#f59e0b', fontWeight: 700 }}>⚙ customised</span>}
                                                            </span>
                                                        </div>
                                                    )}
                                                    {currencyInfo && (
                                                        <div style={rowS}>
                                                            <span style={lblS}>Currency</span>
                                                            <span style={valS}>{currencyInfo.flag} {currencyInfo.symbol} — {currencyInfo.code}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Card 2 — Simulation Engine */}
                                            <div style={cardS}>
                                                <div style={headS}>
                                                    <span style={titleS}>⚙️ Simulation Engine</span>
                                                    <button type="button" style={editS} onClick={() => setOpenTab('engine')}>✎ Edit</button>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Paradigm</span>
                                                        <span style={valS}>
                                                            {paradigmInfo ? `${paradigmInfo.icon} ${paradigmInfo.label}` : selectedParadigm}
                                                        </span>
                                                    </div>
                                                    {paradigmInfo && (
                                                        <div style={rowS}>
                                                            <span style={lblS} />
                                                            <span style={{ fontSize: '0.63rem', color: '#64748b', flex: 1 }}>{paradigmInfo.sub}</span>
                                                        </div>
                                                    )}
                                                    <div style={rowS}>
                                                        <span style={lblS}>Ending</span>
                                                        <span style={valS}>
                                                            {pathwayInfo
                                                                ? `${pathwayInfo.icon} ${pathwayInfo.title}`
                                                                : selectedPathway || '—'}
                                                        </span>
                                                    </div>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Mode</span>
                                                        <span style={valS}>
                                                            {simulationMode === 'single_bu'
                                                                ? '🏭 Single Business Unit'
                                                                : '🏢 4-BU Conglomerate'}
                                                        </span>
                                                    </div>
                                                    {simulationMode === 'single_bu' && industryVertical && (
                                                        <div style={rowS}>
                                                            <span style={lblS}>BU Selected</span>
                                                            <span style={{ ...valS, color: '#a5b4fc' }}>
                                                                {industryVertical.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                                            </span>
                                                        </div>
                                                    )}
                                                    {/* Region is shown in Core Configuration card — not duplicated here */}
                                                </div>
                                            </div>

                                            {/* Card 3 — Industry Verticals (hidden in single_bu mode) */}
                                            {simulationMode !== 'single_bu' && (() => {
                                                // Slot definitions mirroring the 2B form
                                                const BU_SLOTS = [
                                                    { slot: 'pharma',         slotLabel: 'Pharma',         slotIcon: '💊' },
                                                    { slot: 'electronics',    slotLabel: 'Electronics',    slotIcon: '⚡' },
                                                    { slot: 'consumer_goods', slotLabel: 'Consumer Goods', slotIcon: '🛍️' },
                                                    { slot: 'software',       slotLabel: 'Software',       slotIcon: '💻' },
                                                ];
                                                // Flat lookup — must contain every vertical in SLOT_FIT_MAP (bu_profiles.py)
                                                const ALL_VERTICALS = [
                                                    // pharma-slot alternatives
                                                    { id: 'oil_gas',                    label: 'Oil & Gas',                   icon: '🛢️' },
                                                    { id: 'chemical',                   label: 'Chemical',                    icon: '⚗️' },
                                                    { id: 'cosmetics',                  label: 'Cosmetics & Personal Care',   icon: '💄' },
                                                    { id: 'food_beverage',              label: 'Food & Beverage',             icon: '🍽️' },
                                                    { id: 'power_utilities',            label: 'Power & Utilities',           icon: '⚡' },
                                                    // electronics-slot alternatives
                                                    { id: 'semiconductor',              label: 'Semiconductor',               icon: '💎' },
                                                    { id: 'medical_devices',            label: 'Medical Devices',             icon: '🩺' },
                                                    { id: 'automotive',                 label: 'Automotive',                  icon: '🚗' },
                                                    { id: 'telecom',                    label: 'Telecom',                     icon: '📶' },
                                                    // consumer_goods-slot alternatives
                                                    { id: 'retail_fmcg',               label: 'Retail / FMCG',               icon: '🛍️' },
                                                    { id: 'agriculture',                label: 'Agriculture',                 icon: '🌾' },
                                                    // software-slot alternatives
                                                    { id: 'technology',                 label: 'Technology',                  icon: '🧠' },
                                                    { id: 'banking_financial_services', label: 'Banking & Financial Services', icon: '🏦' },
                                                ];
                                                return (
                                                <div style={cardS}>
                                                    <div style={headS}>
                                                        <span style={titleS}>🏭 Industry Verticals</span>
                                                        <button type="button" style={editS} onClick={() => setOpenTab('verticals')}>✎ Edit</button>
                                                    </div>
                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                                        {BU_SLOTS.map(({ slot, slotLabel, slotIcon }) => {
                                                            const subVid = buSubstitutions[slot];
                                                            const subInfo = subVid ? ALL_VERTICALS.find(v => v.id === subVid) : null;
                                                            const vertLabel = subInfo
                                                                ? `${subInfo.icon} ${subInfo.label}`
                                                                : `${slotIcon} Standard ${slotLabel}`;
                                                            const buRegionId = buRegions[slot];
                                                            const buRegionInfo = buRegionId ? REGIONS.find(r => r.id === buRegionId) : null;
                                                            const regionLabel = buRegionInfo
                                                                ? `${buRegionInfo.flag} ${buRegionInfo.label}`
                                                                : `Same as Cohort${regionDisplay ? ` (${regionDisplay})` : ''}`;
                                                            return (
                                                                <div key={slot} style={{ paddingBottom: 5, borderBottom: '1px solid rgba(100,116,139,0.12)' }}>
                                                                    <div style={rowS}>
                                                                        <span style={{ ...lblS, minWidth: 96 }}>{slotIcon} {slotLabel}</span>
                                                                        <span style={{ ...valS, color: subVid ? '#a5b4fc' : '#e2e8f0' }}>{vertLabel}</span>
                                                                    </div>
                                                                    <div style={{ ...rowS, marginTop: 2 }}>
                                                                        <span style={{ ...lblS, minWidth: 96, fontSize: '0.63rem' }}>📍 Region</span>
                                                                        <span style={{ fontSize: '0.63rem', color: buRegionId ? '#67e8f9' : '#64748b', fontWeight: buRegionId ? 600 : 400 }}>
                                                                            {regionLabel}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                                );
                                            })()}

                                            {/* Card 4 — Optional Modules */}
                                            <div style={cardS}>
                                                <div style={headS}>
                                                    <span style={titleS}>🔬 Optional Modules</span>
                                                    <button type="button" style={editS} onClick={() => setOpenTab('modules')}>✎ Edit</button>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Engine</span>
                                                        <span style={valS}>
                                                            {enabledModules.length}/{ENGINE_MODULE_TOGGLES.length} on
                                                            {nonDefaultModules.length > 0 && (
                                                                <span style={{ marginLeft: 5, fontSize: '0.6rem', color: '#f59e0b', fontWeight: 700 }}>
                                                                    {nonDefaultModules.length} non-default
                                                                </span>
                                                            )}
                                                        </span>
                                                    </div>
                                                    {nonDefaultModules.length > 0 && (
                                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 2, marginTop: 1 }}>
                                                            {nonDefaultModules.map(t => (
                                                                <span key={t.key} style={engineModuleToggles[t.key] ? onChip : offChip}>
                                                                    {t.icon} {engineModuleToggles[t.key] ? '+' : '−'}{t.label}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}
                                                    <div style={rowS}>
                                                        <span style={lblS}>Side Tracks</span>
                                                        <span style={valS}>
                                                            {selectedTrackDetails.length === 0
                                                                ? <span style={{ color: '#64748b' }}>None selected</span>
                                                                : `${selectedTrackDetails.length} selected`}
                                                        </span>
                                                    </div>
                                                    {selectedTrackDetails.length > 0 && (
                                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                                                            {selectedTrackDetails.map(t => (
                                                                <span key={t.track_id} style={indigoChip}>
                                                                    {t.icon || '📦'} {t.display_name || t.track_id}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}
                                                    <div style={rowS}>
                                                        <span style={lblS}>CEO Interview</span>
                                                        <span style={ceoInterviewEnabled ? onChip : offChip}>
                                                            {ceoInterviewEnabled ? '● Enabled' : '○ Disabled'}
                                                        </span>
                                                        {ceoInterviewEnabled && (
                                                            <span style={{ fontSize: '0.63rem', color: '#64748b' }}>
                                                                {ceoVoiceGender === 'female' ? '👩‍💼 Victoria' : '👨‍💼 Alexander'}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Card 5 — Team Interventions */}
                                            <div style={cardS}>
                                                <div style={headS}>
                                                    <span style={titleS}>⚡ Team Interventions</span>
                                                    <button type="button" style={editS} onClick={() => setOpenTab('interventions')}>✎ Edit</button>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Overrides</span>
                                                        <span style={valS}>
                                                            {selectedOverrides.length}/{masterOverrides.length} selected
                                                            {selectedOverrides.length > 0 && selectedOverrides.length === masterOverrides.length && (
                                                                <span style={{ marginLeft: 5, fontSize: '0.6rem', color: '#4ade80', fontWeight: 700 }}>All</span>
                                                            )}
                                                        </span>
                                                    </div>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Swipe Files</span>
                                                        <span style={valS}>
                                                            {selectedSwipes.length}/{masterSwipes.length} selected
                                                            {selectedSwipes.length > 0 && selectedSwipes.length === masterSwipes.length && (
                                                                <span style={{ marginLeft: 5, fontSize: '0.6rem', color: '#4ade80', fontWeight: 700 }}>All</span>
                                                            )}
                                                        </span>
                                                    </div>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Round Pacing</span>
                                                        <span style={valS}>
                                                            {pacingMode === 'free_play' && '🔓 Free Play'}
                                                            {pacingMode === 'manual' && `✋ Manual (up to R${maxUnlockedRound})`}
                                                            {pacingMode === 'scheduled' && `📅 Scheduled (${Object.keys(roundSchedules).length} rounds set)`}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Card 6 — Pedagogy & Analytics */}
                                            <div style={cardS}>
                                                <div style={headS}>
                                                    <span style={titleS}>🎓 Pedagogy &amp; Analytics</span>
                                                    <button type="button" style={editS} onClick={() => setOpenTab('pedagogy')}>✎ Edit</button>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                                                    <div style={rowS}>
                                                        <span style={lblS}>Scaffolding</span>
                                                        <span style={valS}>
                                                            {enabledPedagogy.length === 0
                                                                ? <span style={{ color: '#64748b' }}>None enabled</span>
                                                                : `${enabledPedagogy.length} feature${enabledPedagogy.length !== 1 ? 's' : ''} active`}
                                                        </span>
                                                    </div>
                                                    {enabledPedagogy.length > 0 && (
                                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                                                            {enabledPedagogy.map(t => (
                                                                <span key={t.key} style={onChip}>{t.icon} {t.label}</span>
                                                            ))}
                                                        </div>
                                                    )}
                                                    <div style={rowS}>
                                                        <span style={lblS}>Visibility</span>
                                                        <span style={valS}>
                                                            {visOverrideCount === 0
                                                                ? <span style={{ color: '#4ade80' }}>✓ Global defaults</span>
                                                                : <span style={{ color: '#f59e0b' }}>{visOverrideCount} custom override{visOverrideCount !== 1 ? 's' : ''}</span>}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                        </div>{/* end grid */}

                                        {/* ── Permanent-lock warning (create only) ── */}
                                        {!isEditMode && (
                                        <div style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.3)', padding: '12px 16px', borderRadius: 8, color: '#fcd34d', fontSize: '0.83rem', display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                            <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>⚠️</span>
                                            <div>
                                                <strong style={{ display: 'block', marginBottom: 4, color: '#f59e0b' }}>PERMANENT COHORT CONFIGURATION</strong>
                                                By proceeding, choices made here (Decision Paradigm, Scenario Preset, Currency, Ending Pathway, Side Tracks, etc.) become <strong>permanent</strong> for this cohort and cannot be changed later.
                                            </div>
                                        </div>
                                        )}
                                        {isEditMode && (
                                        <div style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.25)', padding: '12px 16px', borderRadius: 8, color: '#93c5fd', fontSize: '0.83rem', display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                            <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>ℹ️</span>
                                            <div>
                                                <strong style={{ display: 'block', marginBottom: 4, color: '#60a5fa' }}>EDITING PRE-GAME COHORT</strong>
                                                Changes apply immediately. Only allowed while zero players are inducted and the game has not begun.
                                            </div>
                                        </div>
                                        )}

                                        <div className={styles.footer} style={{ borderTop: 'none', paddingTop: 0, marginTop: 0 }}>
                                            {/* Inline error at point of action — visible without scrolling */}
                                            {error && (
                                                <div style={{
                                                    width: '100%', marginBottom: 10,
                                                    background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.4)',
                                                    borderRadius: 7, padding: '8px 12px',
                                                    color: '#fca5a5', fontSize: '0.75rem', fontWeight: 600,
                                                    display: 'flex', alignItems: 'center', gap: 8,
                                                }}>
                                                    <span>⚠️</span>
                                                    <span>{error}</span>
                                                </div>
                                            )}
                                            <button type="button" className={styles.cancelBtn} onClick={onClose} disabled={loading}>Cancel</button>
                                            {isEditMode ? (
                                                <button type="submit" className={styles.submitBtn} disabled={loading || !cohortName.trim()} style={{ background: 'linear-gradient(135deg,#3b82f6,#06b6d4)', color: '#fff' }}>
                                                    {loading ? '⏳ Saving...' : '✏️ Save Changes'}
                                                </button>
                                            ) : (
                                                <button type="submit" className={styles.submitBtn} disabled={loading || !cohortName.trim()} style={{ background: '#f59e0b', color: '#1e293b' }}>
                                                    {loading ? 'Initializing Server...' : 'Permanently Lock & Create Cohort'}
                                                </button>
                                            )}
                                        </div>

                                    </div>
                                );
                            })()}
                        </AccordionItem>
                    </form>
                </div>
            </div>
        </div>
    );
}
