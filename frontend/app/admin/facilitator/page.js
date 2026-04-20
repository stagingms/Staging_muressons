'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import styles from '../page.module.css'; // Reuse existing admin layout

import LeaderboardMatrix from '../../components/LeaderboardMatrix';
import ManualOverride from '../../components/ManualOverride';
import SwipeFile from '../../components/SwipeFile';
import SessionViewer from '../../components/SessionViewer';
import PlayerRegistry from '../../components/PlayerRegistry';
import MaterialityConfig from '../../components/MaterialityConfig';
import InterventionConfig from '../../components/InterventionConfig';
import AuditTrail from '../../components/AuditTrail';
import DebriefReport from '../../components/DebriefReport';
import PlatformAnalytics from '../../components/PlatformAnalytics';

// ── New Capsim-inspired components ──
import DashboardHome from '../../components/DashboardHome';
import UndoRound from '../../components/UndoRound';
import FacilitatorNotes from '../../components/FacilitatorNotes';
import TeamImpersonation from '../../components/TeamImpersonation';
import ReportsExport from '../../components/ReportsExport';
import RoundTimeline from '../../components/RoundTimeline';
import BalancedScorecardEvaluator from '../../components/BalancedScorecardEvaluator';
import StudentBonuses from '../../components/StudentBonuses';
import SimulationManager from '../../components/SimulationManager';
import CreateCohortModal from '../../components/CreateCohortModal';
import PeerEvaluation from '../../components/PeerEvaluation';
import BulkMessaging from '../../components/BulkMessaging';
import UsernamePromptModal from '../../components/UsernamePromptModal';
import RoundPacingControl from '../../components/RoundPacingControl';
import ComplexityEventFeed from '../../components/ComplexityEventFeed';
import CohortComparison from '../../components/CohortComparison';
import AutoPauseConfig from '../../components/AutoPauseConfig';
import DecisionTimeline from '../../components/DecisionTimeline';
import FacilitatorTeleprompter from '../../components/FacilitatorTeleprompter';
import FacilitatorAnnotations from '../../components/FacilitatorAnnotations';
import TechnicalGlossary from '../../components/TechnicalGlossary';

const API = process.env.NEXT_PUBLIC_API_URL || '';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || `ws://${typeof window !== 'undefined' ? window.location.host : 'localhost:8000'}`;

/* ── Seed data for standalone frontend development ─────────── */
const SEED_LEADERBOARD = [
    {
        session_id: 'demo-alpha',
        cohort_name: 'Cohort Alpha — MBA Spring 2026',
        round_number: 6,
        terminal_value: 67_320_000,
        total_cash: 42_100_000,
        group_synergy: 1.28,
        group_reputation: 62,
        avg_natural_capital_debt: 14.2,
        avg_social_license: 58.5,
        talent_flight_risk: false,
        talent_penalty_multiplier: 1.04,
        active_flags: ['deep_audit_completed', 'green_bond_active'],
    },
    {
        session_id: 'demo-beta',
        cohort_name: 'Cohort Beta — Exec Program',
        round_number: 4,
        terminal_value: 51_800_000,
        total_cash: 38_500_000,
        group_synergy: 1.12,
        group_reputation: 44,
        avg_natural_capital_debt: 28.7,
        avg_social_license: 41.2,
        talent_flight_risk: true,
        talent_penalty_multiplier: 1.47,
        active_flags: ['electronics_blindspot', 'carbon_deferred'],
    }
];

/* ═════════════════════════════════════════════════════════════════
 *  LOGIN GATE — Facilitator must authenticate before accessing
 * ═════════════════════════════════════════════════════════════════ */

function FacilitatorLoginGate({ onLogin }) {
    const [facId, setFacId] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!facId.trim() || !password.trim()) return;
        setLoading(true);
        setError('');
        try {
            const res = await fetch(`${API}/api/admin/facilitators/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    facilitator_id: facId.trim(),
                    password: password.trim(),
                }),
            });
            if (res.ok) {
                const data = await res.json();
                sessionStorage.setItem('facilitator_auth', JSON.stringify(data));
                onLogin(data);
            } else {
                const err = await res.json();
                setError(err.detail || 'Login failed');
            }
        } catch {
            setError('Cannot connect to server');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--bg-body)',
            padding: '2rem',
        }}>
            <div style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-lg)',
                padding: '3rem',
                maxWidth: '420px',
                width: '100%',
                boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
            }}>
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>🎓</div>
                    <h1 style={{
                        fontSize: '1.5rem',
                        fontWeight: 800,
                        color: 'var(--text-primary)',
                        margin: '0 0 0.5rem 0',
                    }}>
                        Facilitator Login
                    </h1>
                    <p style={{
                        fontSize: '0.82rem',
                        color: 'var(--text-muted)',
                        margin: 0,
                    }}>
                        Enter your facilitator credentials to access the Workshop Control Room.
                    </p>
                </div>

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                        <label style={{
                            display: 'block',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            letterSpacing: '0.1em',
                            color: 'var(--text-muted)',
                            marginBottom: '0.4rem',
                        }}>
                            Facilitator ID
                        </label>
                        <input
                            type="text"
                            value={facId}
                            onChange={(e) => setFacId(e.target.value)}
                            placeholder="e.g. FAC-001"
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '0.7rem 1rem',
                                borderRadius: 'var(--radius-md)',
                                border: '1px solid var(--border-subtle)',
                                background: 'var(--bg-body)',
                                color: 'var(--text-primary)',
                                fontSize: '0.9rem',
                                fontFamily: 'var(--font-mono)',
                                outline: 'none',
                                boxSizing: 'border-box',
                            }}
                        />
                    </div>
                    <div>
                        <label style={{
                            display: 'block',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            letterSpacing: '0.1em',
                            color: 'var(--text-muted)',
                            marginBottom: '0.4rem',
                        }}>
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                            disabled={loading}
                            style={{
                                width: '100%',
                                padding: '0.7rem 1rem',
                                borderRadius: 'var(--radius-md)',
                                border: '1px solid var(--border-subtle)',
                                background: 'var(--bg-body)',
                                color: 'var(--text-primary)',
                                fontSize: '0.9rem',
                                outline: 'none',
                                boxSizing: 'border-box',
                            }}
                        />
                    </div>

                    {error && (
                        <div style={{
                            padding: '0.6rem 1rem',
                            borderRadius: 'var(--radius-md)',
                            background: 'rgba(239, 68, 68, 0.1)',
                            border: '1px solid rgba(239, 68, 68, 0.3)',
                            color: '#ef4444',
                            fontSize: '0.8rem',
                            fontWeight: 600,
                        }}>
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading || !facId.trim() || !password.trim()}
                        style={{
                            padding: '0.8rem',
                            borderRadius: 'var(--radius-md)',
                            border: 'none',
                            background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                            color: '#fff',
                            fontSize: '0.9rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            opacity: loading ? 0.7 : 1,
                            transition: 'all 0.2s',
                            boxShadow: '0 4px 16px rgba(59, 130, 246, 0.3)',
                        }}
                    >
                        {loading ? '⏳ Authenticating...' : '🔐 Sign In'}
                    </button>
                </form>
                <div style={{ textAlign: 'center', marginTop: '1.25rem' }}>
                    <a href="/admin" style={{
                        fontSize: '0.8rem',
                        color: 'var(--text-muted)',
                        textDecoration: 'none',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        opacity: 0.7,
                    }}>
                        ← Back to Admin Portal
                    </a>
                </div>
            </div>
        </div>
    );
}


/* ═════════════════════════════════════════════════════════════════
 *  MAIN FACILITATOR DASHBOARD (wrapped with login gate)
 * ═════════════════════════════════════════════════════════════════ */

export default function FacilitatorPage() {
    const [authData, setAuthData] = useState(null);
    const [checked, setChecked] = useState(false);

    useEffect(() => {
        try {
            const stored = sessionStorage.getItem('facilitator_auth');
            if (stored) setAuthData(JSON.parse(stored));
        } catch { /* ignore */ }
        setChecked(true);
    }, []);

    const handleLogout = () => {
        sessionStorage.removeItem('facilitator_auth');
        setAuthData(null);
    };

    if (!checked) return null; // Avoid flash

    if (!authData) {
        return <FacilitatorLoginGate onLogin={setAuthData} />;
    }

    return <FacilitatorDashboard authData={authData} onLogout={handleLogout} />;
}


function FacilitatorDashboard({ authData, onLogout }) {
    const [leaderboard, setLeaderboard] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [activityLog, setActivityLog] = useState([]);
    const [clockTime, setClockTime] = useState('');
    const wsRef = useRef(null);
    const [showChangePw, setShowChangePw] = useState(false);

    // God Mode visibility controls — drives which tabs are shown
    const [godVisibility, setGodVisibility] = useState({ materiality_matrix: true, technical_reference: true });

    // New state for Sidebar UI
    const [activeTab, setActiveTab] = useState('dashboard_home');
    const [createCohortOpen, setCreateCohortOpen] = useState(false);
    const [openCategories, setOpenCategories] = useState({
        command: true,
        classroom: false,
        analytics: false,
        config: false,
    });

    const toggleCategory = (catId) => {
        setOpenCategories(prev => ({ ...prev, [catId]: !prev[catId] }));
    };

    /* ── Client-only clock ── */
    useEffect(() => {
        setClockTime(new Date().toLocaleTimeString());
        const t = setInterval(() => setClockTime(new Date().toLocaleTimeString()), 1000);
        return () => clearInterval(t);
    }, []);

    /* ── Fetch God Mode visibility settings ── */
    useEffect(() => {
        fetch(`${API}/api/admin/god/analytics-visibility`)
            .then(r => r.ok ? r.json() : {})
            .then(d => {
                const fv = d.facilitator || {};
                setGodVisibility(prev => ({
                    ...prev,
                    materiality_matrix: fv.materiality_matrix !== false,
                    technical_reference: fv.technical_reference !== false,
                }));
            })
            .catch(() => { /* keep defaults (visible) */ });
    }, []);

    /* ── WebSocket for real-time admin updates ─────────────── */
    useEffect(() => {
        let ws;
        try {
            ws = new WebSocket(`${WS_URL}/api/admin/ws/admin?facilitator_id=${authData.facilitator_id}`);
            ws.onmessage = (evt) => {
                const data = JSON.parse(evt.data);
                if (data.type === 'sessions_refresh' || data.type === 'sessions_refresh_trigger') {
                    fetchLeaderboard();
                } else {
                    addLog(data);
                }
            };
            ws.onopen = () => addLog({ type: 'system', message: 'Admin WebSocket connected' });
            ws.onerror = () => addLog({ type: 'system', message: 'WebSocket: using seed data (backend offline)' });
            wsRef.current = ws;
        } catch {
            // Backend offline — use seed data
        }
        return () => ws?.close();
    }, []);

    const addLog = useCallback((entry) => {
        setActivityLog((prev) => [
            { ...entry, timestamp: new Date().toLocaleTimeString() },
            ...prev.slice(0, 49),
        ]);
    }, []);

    /* ── Fetch leaderboard on mount ─────────────────────────── */
    const fetchLeaderboard = useCallback(async () => {
        try {
            const res = await fetch(`${API}/api/admin/leaderboard?facilitator_id=${authData.facilitator_id}`);
            if (res.ok) {
                const data = await res.json();
                if (data.leaderboard?.length) setLeaderboard(data.leaderboard);
            }
        } catch {
            // Backend offline — keep seed data
        }
    }, []);

    useEffect(() => {
        fetchLeaderboard();
    }, [fetchLeaderboard]);

    const handleOverride = useCallback(
        (result) => {
            addLog({ type: 'override', ...result });
            fetch(`${API}/api/admin/leaderboard?facilitator_id=${authData.facilitator_id}`)
                .then((r) => r.json())
                .then((d) => d.leaderboard?.length && setLeaderboard(d.leaderboard))
                .catch(() => { });
        },
        [addLog]
    );

    const handleMessageSent = useCallback(
        (result) => {
            addLog({ type: 'inject', message: `Injected: ${result.message?.title}` });
        },
        [addLog]
    );

    /* ── Reset handlers ──────────────────────────────────────── */
    const handleResetSession = useCallback(async (sid, cohortName, hard = false) => {
        const name = cohortName || leaderboard.find(s => s.session_id === sid)?.cohort_name || sid.slice(0, 12);
        const isPlayer = name.includes('Player');
        const prompt = isPlayer
            ? `⚠️ Remove "${name}"?\n\nThis will permanently remove this player's session and all their round data.`
            : `⚠️ Delete cohort "${name}" and ALL its players?\n\nThis will remove the cohort and every player session under it.`;
        if (!confirm(prompt)) return;
        if (hard) {
            if (!confirm(`🧨 HARD DELETE: Are you absolutely sure you want to completely wipe "${name}" today without the 7-day grace period?\n\nClick OK to confirm HARD DELETION.`)) return;
        } else {
            if (!confirm(`Are you absolutely sure you want to delete "${name}"?\n\nClick OK to confirm.`)) return;
        }
        
        try {
            const endpoint = `${API}/api/admin/${sid}/reset${hard ? '?hard=true' : ''}`;
            const res = await fetch(endpoint, { method: 'DELETE' });
            if (res.ok) {
                const data = await res.json();
                const msg = data.players_removed > 0
                    ? `"${name}" deleted (${data.players_removed} player${data.players_removed > 1 ? 's' : ''} removed)`
                    : `"${name}" deleted`;
                addLog({ type: 'system', message: msg });
                // Remove from leaderboard: the deleted session + any child player sessions
                setLeaderboard(prev => prev.filter(s => s.session_id !== sid));
                if (data.players_removed > 0 && !isPlayer) {
                    // Refresh full leaderboard to clear cascade-deleted player sessions
                    fetchLeaderboard();
                }
                if (selectedSession === sid) setSelectedSession(null);
            } else {
                addLog({ type: 'system', message: `Delete failed: ${res.status}` });
            }
        } catch { addLog({ type: 'system', message: 'Delete failed: network error' }); }
    }, [leaderboard, selectedSession, addLog, fetchLeaderboard]);

    const handleResetAll = useCallback(async () => {
        if (!confirm('☢️ RESET ALL SESSIONS?\nThis will DELETE every session and all data. Cannot be undone.')) return;
        if (!confirm('Are you absolutely sure? Type OK to proceed.')) return;
        try {
            const res = await fetch(`${API}/api/admin/reset-all`, { method: 'DELETE' });
            if (res.ok) {
                const d = await res.json();
                addLog({ type: 'system', message: `All ${d.sessions_removed} sessions reset` });
                setLeaderboard([]);
                setSelectedSession(null);
            }
        } catch { addLog({ type: 'system', message: 'Reset all failed' }); }
    }, [addLog]);

    const SIDEBAR_CONFIG = [
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
                { id: 'manual_override',label: 'Manual Overrides',      icon: '⚡', tooltip: 'Directly modify a session\'s KPIs (Treasury, Reputation, Synergy) with absolute or delta values, or force-advance rounds. Used for live interventions, correcting data errors, or simulating external shocks. Answers: "How do I manually change a team\'s numbers?"' },
                { id: 'intervention_config', label: 'Interventions',    icon: '🎮', tooltip: 'Configure which master interventions (manual overrides and narrative swipe files) are available for each cohort. Controls the intervention toolkit available during live facilitation. Answers: "Which intervention tools should this cohort have access to?"' },
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
                { id: 'round_pacing',        label: 'Round Pacing',          icon: '⏱️', tooltip: 'Control the pace of round progression: set countdown timers per round, enforce manual gating (facilitator must unlock each round), or configure auto-advance after all decisions are submitted. Answers: "How fast should rounds progress?"' },
                { id: 'auto_pause',          label: 'Auto-Pause Triggers',   icon: '⏸️', tooltip: 'Configure automatic pause conditions that halt round progression for facilitator intervention: low treasury thresholds, reputation floor breaches, bankruptcy detection, or custom KPI triggers. Answers: "When should the simulation automatically pause for my attention?"' },
                { id: 'undo_round',          label: 'Undo Round',             icon: '↩️', tooltip: 'Roll back the last completed round for a selected session, restoring all KPIs to their previous state. Useful for correcting data entry errors or re-running a round after a teaching moment. Requires confirmation. Answers: "How do I reverse a round that went wrong?"' },
                { id: 'materiality',         label: 'Materiality Matrix',    icon: '🧩', tooltip: 'Mendelow\'s Materiality Matrix — interactive drag-and-drop issue mapping grid with financial impact (x-axis) vs. societal impact (y-axis). Upload custom issue dictionaries via CSV or use global defaults. Used for teaching ESG stakeholder analysis and materiality assessment. Answers: "How do I configure the materiality framework?"' },
                { id: 'notes',               label: 'Facilitator Notes',      icon: '📓', tooltip: 'Private notes workspace for the facilitator — jot down observations, reminders, per-cohort commentary, or debrief preparation notes. Persisted across sessions and only visible to the facilitator. Answers: "Where can I keep my private teaching notes?"' },
                { id: 'annotations',         label: 'Annotations',            icon: '📌', tooltip: 'Add timestamped annotations to specific sessions or rounds: flag interesting decisions, mark teaching moments, or tag sessions for post-simulation review and debrief preparation. Answers: "How do I bookmark key moments for later discussion?"' },
                { id: 'technical_glossary',  label: 'Technical Reference',   icon: '📐', tooltip: 'Comprehensive reference guide explaining simulation terminology, engine mechanics (Contagion, Talent/Burnout, NCD, Governance), KPI calculation formulas, scorecard weighting, and decision paradigm differences. Answers: "How do the simulation engines and calculations actually work?"' },
                { id: 'activity_log',        label: 'Activity Logs & Resets', icon: '📋', tooltip: 'Facilitator activity audit log showing all actions taken (overrides, messages, resets) with timestamps. Includes session management controls for soft/hard deleting cohorts, removing individual players, or performing a full system reset. Answers: "What actions have been taken and how do I clean up sessions?"' },
            ]
        },
    ];

    // Apply God Mode visibility filtering
    const FILTERED_SIDEBAR = SIDEBAR_CONFIG.map(group => ({
        ...group,
        items: group.items.filter(item => {
            if (item.id === 'materiality' && !godVisibility.materiality_matrix) return false;
            if (item.id === 'technical_glossary' && !godVisibility.technical_reference) return false;
            return true;
        }),
    }));

    // Breadcrumb helper
    const getTabMeta = (tabId) => {
        for (const group of FILTERED_SIDEBAR) {
            const item = group.items.find(i => i.id === tabId);
            if (item) return { label: item.label, category: group.category, categoryIcon: group.icon };
        }
        return { label: 'Dashboard', category: 'Command Center', categoryIcon: '🎯' };
    };

    const renderActiveComponent = () => {
        // Only top-level cohort sessions (no player sub-sessions) owned by this facilitator
        const ownCohorts = leaderboard.filter(
            s => !s.player_id && (!s.facilitator_id || s.facilitator_id === authData.facilitator_id)
        );

        switch (activeTab) {
            // ── Overview tabs ──
            case 'dashboard_home':
                return (
                    <>
                        <DashboardHome leaderboard={leaderboard} onNavigate={setActiveTab} onCreateCohort={() => setCreateCohortOpen(true)} />
                        <CreateCohortModal
                            isOpen={createCohortOpen}
                            onClose={() => setCreateCohortOpen(false)}
                            onCreated={(newSession) => {
                                setCreateCohortOpen(false);
                                fetchLeaderboard();
                            }}
                            currentFacilitatorId={authData.facilitator_id}
                        />
                    </>
                );
            case 'timeline':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <RoundTimeline sessionId={selectedSession} leaderboard={leaderboard} />

                        {/* Quiz Controls for Facilitator */}
                        <QuizControlPanel sessions={leaderboard.filter(s => !s.player_id).map(s => ({ session_id: s.session_id, cohort_name: s.cohort_name }))} />
                    </div>
                );
            case 'teleprompter':
                return <FacilitatorTeleprompter currentRound={leaderboard.reduce((max, s) => Math.max(max, s.round_number || 1), 1)} sessionId={selectedSession} />;

            // ── Monitoring tabs ──
            case 'leaderboard':
                return (
                    <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <div />
                            <button
                                onClick={() => setCreateCohortOpen(true)}
                                style={{
                                    padding: '0.55rem 1.25rem',
                                    borderRadius: '8px',
                                    border: 'none',
                                    background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                                    color: '#fff',
                                    fontSize: '0.82rem',
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    boxShadow: '0 4px 16px rgba(59, 130, 246, 0.25)',
                                    transition: 'all 0.2s',
                                }}
                            >
                                + New Cohort
                            </button>
                        </div>
                        <LeaderboardMatrix leaderboard={leaderboard} selectedSession={selectedSession} onSelectSession={setSelectedSession} onDeleteSession={handleResetSession} />
                        <CreateCohortModal
                            isOpen={createCohortOpen}
                            onClose={() => setCreateCohortOpen(false)}
                            onCreated={(newSession) => {
                                setCreateCohortOpen(false);
                                fetchLeaderboard();
                            }}
                            currentFacilitatorId={authData.facilitator_id}
                        />
                    </>
                );
            case 'registry':
                return <PlayerRegistry leaderboard={leaderboard} />;
            case 'session_viewer':
                return <SessionViewer leaderboard={leaderboard} />;
            case 'audit_trail':  // merged into Decision History
                return <AuditTrail sessionId={selectedSession} />;
            case 'debrief':
                return <DebriefReport sessionId={selectedSession} />;
            case 'impersonate':
                return <TeamImpersonation leaderboard={leaderboard} selectedSession={selectedSession} />;
            case 'undo_round':
                const fullSession = leaderboard.find(s => s.session_id === selectedSession);
                return <UndoRound session={fullSession} />;

            // ── Interventions tabs ──
            case 'intervention_config':
                return <InterventionConfig sessionId={selectedSession} />;
            case 'round_pacing':
                return <RoundPacingControl sessions={ownCohorts} />;
            case 'auto_pause':
                return <AutoPauseConfig />;
            case 'manual_override':
                return (
                    <div className={styles.controlsRow}>
                        <ManualOverride sessionId={selectedSession} onOverrideApplied={handleOverride} />
                    </div>
                );
            case 'swipe_file':
                return <SwipeFile sessionId={selectedSession} onMessageSent={handleMessageSent} />;
            case 'broadcast':
                return <BulkMessaging leaderboard={leaderboard} />;

            // ── Reports & Analytics tabs ──
            case 'reports':
                return <ReportsExport leaderboard={leaderboard} />;
            case 'scorecard_evaluator':
                return (
                    <div style={{ padding: '1.5rem', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
                        <h2 style={{ marginBottom: '1rem', color: 'var(--text-primary)', fontSize: '1.4rem' }}>🧮 Scorecard Sandbox (Teaching Tool)</h2>
                        <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.9rem', maxWidth: '600px' }}>
                            Interactive whiteboard to demonstrate the mathematical weighting of the Triple Bottom Line framework. Modifying these sliders does not impact live session data.
                        </p>
                        <BalancedScorecardEvaluator />
                    </div>
                );
            case 'notes':
                return <FacilitatorNotes sessionId={selectedSession} />;
            case 'cohort_comparison':
                return <CohortComparison facilitatorId={authData.facilitator_id} />;
            case 'complexity_feed':
                return <ComplexityEventFeed sessionId={selectedSession} />;
            case 'decision_replay':
                return <DecisionTimeline sessionId={selectedSession} leaderboard={leaderboard} />;
            case 'annotations':
                return <FacilitatorAnnotations sessionId={selectedSession} leaderboard={leaderboard} />;

            // ── Collaboration tabs ──
            case 'bonuses':
                return <StudentBonuses sessionId={selectedSession} />;
            case 'peer_eval':
                return <PeerEvaluation sessionId={selectedSession} />;

            // ── Config & System tabs ──
            case 'materiality':
                return <MaterialityConfig sessionId={selectedSession} isFacilitator={true} />;
            case 'technical_glossary':
                return (
                    <div style={{ padding: '1.5rem' }}>
                        <TechnicalGlossary />
                    </div>
                );
            case 'platform_analytics':
                return <PlatformAnalytics visibility={null} />;
            case 'activity_log':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <section className={styles.resetPanel}>
                            <div className={styles.resetHeader}>
                                <span>🔄</span>
                                <h2>Session Management</h2>
                            </div>
                            <div className={styles.resetBody}>
                                <FacilitatorSessionManager 
                                    leaderboard={leaderboard} 
                                    authData={authData} 
                                    handleResetSession={handleResetSession} 
                                    styles={styles} 
                                />
                            </div>
                        </section>

                        <section className={styles.logPanel}>
                            <h2>Facilitator Activity Log</h2>
                            <div className={styles.logBox}>
                                {activityLog.map((log, i) => (
                                    <div key={i} className={`${styles.logEntry} ${styles[log.type]}`}>
                                        <span className={styles.logTime}>{log.timestamp}</span>
                                        {log.type === 'system' ? '💻' : log.type === 'override' ? '⚡' : '✉️'}
                                        <strong>{log.type.toUpperCase()}</strong>: {log.message}
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>
                );

            default:
                return null;
        }
    };

    return (
        <div className={styles.dashboard} data-theme="light">
            {/* Choose Username Overlay */}
            {!authData.username && (
                <div style={{ position: 'fixed', inset: 0, zIndex: 16000 }}>
                    <UsernamePromptModal 
                        userId={authData.facilitator_id}
                        role="facilitator"
                        onComplete={(newUsername) => {
                            const updated = { ...authData, username: newUsername };
                            sessionStorage.setItem('facilitator_auth', JSON.stringify(updated));
                            window.location.reload(); 
                        }}
                    />
                </div>
            )}
            
            {/* ── Change Password Modal ── */}
            {showChangePw && (
                <FacilitatorChangePasswordModal
                    facilitatorId={authData.facilitator_id}
                    onClose={() => setShowChangePw(false)}
                />
            )}

            {/* ── Sidebar ── */}
            <aside className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <h1>🎓 Facilitator</h1>
                    <div className={styles.godBadge} style={{
                        background: 'rgba(59, 130, 246, 0.08)',
                        border: '1px solid rgba(59, 130, 246, 0.2)',
                        boxShadow: 'none',
                        color: '#60a5fa',
                        fontSize: '0.72rem',
                        letterSpacing: '0.06em',
                        fontFamily: 'var(--font-mono)',
                    }}>
                        🕐 {clockTime || '--:--:--'}
                    </div>
                    {authData && (
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            marginTop: '0.75rem',
                            paddingTop: '0.75rem',
                            borderTop: '1px solid var(--border-subtle)',
                        }}>
                            <span style={{
                                fontSize: '0.72rem',
                                color: 'var(--text-muted)',
                                fontWeight: 600,
                            }}>
                                👤 {authData.username ? authData.username.toUpperCase() : authData.name} ({authData.facilitator_id})
                            </span>
                            <div style={{ display: 'flex', gap: '4px' }}>
                                <button
                                    onClick={() => setShowChangePw(true)}
                                    style={{
                                        background: 'none',
                                        border: '1px solid rgba(59, 130, 246, 0.3)',
                                        color: '#60a5fa',
                                        fontSize: '0.65rem',
                                        fontWeight: 700,
                                        padding: '3px 8px',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                    }}
                                    title="Change password"
                                >
                                    🔑
                                </button>
                                <button
                                    onClick={onLogout}
                                    style={{
                                        background: 'none',
                                        border: '1px solid rgba(239, 68, 68, 0.3)',
                                        color: '#ef4444',
                                        fontSize: '0.65rem',
                                        fontWeight: 700,
                                        padding: '3px 8px',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                    }}
                                    title="Sign out"
                                >
                                    Logout
                                </button>
                            </div>
                        </div>
                    )}
                </div>


                <nav className={styles.sidebarNav}>
                    {FILTERED_SIDEBAR.map((group) => (
                        <div key={group.id} className={styles.navCategory}>
                            <div
                                className={styles.categoryHeader}
                                onClick={() => toggleCategory(group.id)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={e => e.key === 'Enter' && toggleCategory(group.id)}
                            >
                                <span>{group.icon} {group.category}</span>
                                <span className={`${styles.categoryArrow} ${openCategories[group.id] ? styles.categoryArrowOpen : ''}`}>▶</span>
                            </div>

                            <div className={`${styles.categoryItems} ${openCategories[group.id] ? styles.categoryOpen : ''}`}>
                                {group.items.map((item) => (
                                    <button
                                        key={item.id}
                                        className={`${styles.navItem} ${activeTab === item.id ? styles.activeNav : ''}`}
                                        onClick={() => setActiveTab(item.id)}
                                        data-tooltip={item.tooltip}
                                    >
                                        {item.icon && <span style={{ width: '18px', textAlign: 'center', flexShrink: 0, fontSize: '0.85rem' }}>{item.icon}</span>}
                                        <span>{item.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ))}
                </nav>


            </aside>

            {/* ── Main Workspace ── */}
            <main className={styles.mainPanel}>
                <header className={styles.topBar}>
                    <div className={styles.meta}>
                        {(() => {
                            const meta = getTabMeta(activeTab);
                            return (
                                <nav style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.78rem' }}>
                                    <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>🎓 Facilitator</span>
                                    <span style={{ color: 'var(--text-muted)', opacity: 0.35 }}>›</span>
                                    <span style={{ color: 'var(--text-muted)' }}>{meta.categoryIcon} {meta.category}</span>
                                    <span style={{ color: 'var(--text-muted)', opacity: 0.35 }}>›</span>
                                    <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{meta.label}</span>
                                </nav>
                            );
                        })()}
                    </div>
                </header>

                <div className={styles.mainContent}>
                    {renderActiveComponent()}
                </div>
            </main>
        </div>
    );
}


/* ═════════════════════════════════════════════════════════════════
 *  QUIZ CONTROL PANEL — Difficulty + Per-Cohort Enable/Disable
 * ═════════════════════════════════════════════════════════════════ */

function QuizControlPanel({ sessions = [] }) {
    const [quizDifficulty, setQuizDifficulty] = useState('medium');
    const [quizEnabledMap, setQuizEnabledMap] = useState({});
    const [status, setStatus] = useState(null);

    // Fetch current difficulty
    useEffect(() => {
        fetch(`${API}/api/admin/quiz-difficulty`).then(r => r.json()).then(d => setQuizDifficulty(d.difficulty || 'medium')).catch(() => {});
    }, []);

    // Fetch per-cohort quiz enabled states
    useEffect(() => {
        if (sessions.length === 0) return;
        const fetchAll = async () => {
            const map = {};
            for (const s of sessions) {
                try {
                    const res = await fetch(`${API}/api/admin/quiz-enabled/${s.session_id}`);
                    if (res.ok) { const d = await res.json(); map[s.session_id] = d.quiz_enabled; }
                } catch { map[s.session_id] = true; }
            }
            setQuizEnabledMap(map);
        };
        fetchAll();
    }, [sessions]);

    const updateDifficulty = async (level) => {
        try {
            const res = await fetch(`${API}/api/admin/quiz-difficulty`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ difficulty: level }),
            });
            if (res.ok) {
                setQuizDifficulty(level);
                setStatus(`✅ Quiz difficulty set to ${level.charAt(0).toUpperCase() + level.slice(1)}`);
                setTimeout(() => setStatus(null), 3000);
            }
        } catch (e) { console.error(e); }
    };

    const toggleQuiz = async (sessionId, enabled) => {
        try {
            const res = await fetch(`${API}/api/admin/quiz-enabled/${sessionId}`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quiz_enabled: enabled }),
            });
            if (res.ok) {
                setQuizEnabledMap(prev => ({ ...prev, [sessionId]: enabled }));
                setStatus(`✅ Quiz ${enabled ? 'enabled' : 'disabled'} for cohort`);
                setTimeout(() => setStatus(null), 3000);
            }
        } catch (e) { console.error(e); }
    };

    return (
        <section style={{
            background: 'var(--bg-card, #fff)', border: '1px solid var(--border-subtle, #e2e8f0)',
            borderRadius: 'var(--radius-lg, 16px)', padding: '1.5rem 2rem',
            boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
                <span style={{ fontSize: '1.5rem' }}>🧩</span>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        Quiz Settings
                    </h2>
                    <p style={{ margin: '0.15rem 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        Control quiz difficulty and availability for each cohort. Players get 10 random questions per attempt (max 2 attempts).
                    </p>
                </div>
            </div>

            {status && (
                <div style={{
                    padding: '8px 14px', borderRadius: 10, marginBottom: 12,
                    background: '#f0fdf4', border: '1px solid #86efac',
                    fontSize: '0.8rem', color: '#166534', fontWeight: 600,
                }}>{status}</div>
            )}

            <div style={{
                background: 'linear-gradient(135deg, #eef2ff, #f5f3ff)', borderRadius: 14,
                padding: '16px 20px', border: '1px solid #c7d2fe',
            }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
                    {/* Difficulty Toggle */}
                    <div>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#4338ca', textTransform: 'uppercase', marginBottom: 6 }}>
                            Difficulty Level
                        </div>
                        <div style={{ display: 'flex', gap: 4 }}>
                            {['easy', 'medium', 'hard'].map(level => (
                                <button
                                    key={level}
                                    onClick={() => updateDifficulty(level)}
                                    style={{
                                        padding: '6px 16px', borderRadius: 8, border: 'none',
                                        background: quizDifficulty === level
                                            ? (level === 'easy' ? '#22c55e' : level === 'medium' ? '#eab308' : '#ef4444')
                                            : '#e2e8f0',
                                        color: quizDifficulty === level ? '#fff' : '#64748b',
                                        fontWeight: 600, fontSize: '0.78rem', cursor: 'pointer',
                                        transition: 'all 0.2s',
                                    }}
                                >
                                    {level === 'easy' ? '🟢' : level === 'medium' ? '🟡' : '🔴'} {level.charAt(0).toUpperCase() + level.slice(1)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Per-Cohort Toggle */}
                    <div>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#4338ca', textTransform: 'uppercase', marginBottom: 6 }}>
                            🎯 Quiz Availability by Cohort
                        </div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {sessions.length === 0 ? (
                                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>No active cohorts — create one from the Leaderboard</span>
                            ) : sessions.map(s => {
                                const enabled = quizEnabledMap[s.session_id] !== false;
                                return (
                                    <button
                                        key={s.session_id}
                                        onClick={() => toggleQuiz(s.session_id, !enabled)}
                                        style={{
                                            padding: '5px 12px', borderRadius: 8,
                                            border: `1px solid ${enabled ? '#86efac' : '#fca5a5'}`,
                                            background: enabled ? '#f0fdf4' : '#fef2f2',
                                            color: enabled ? '#166534' : '#991b1b',
                                            fontWeight: 600, fontSize: '0.72rem', cursor: 'pointer',
                                            transition: 'all 0.2s',
                                        }}
                                        title={`${enabled ? 'Disable' : 'Enable'} quiz for ${s.cohort_name}`}
                                    >
                                        {enabled ? '✅' : '❌'} {s.cohort_name}
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}


/* ═════════════════════════════════════════════════════════════════
 *  CHANGE PASSWORD MODAL
 * ═════════════════════════════════════════════════════════════════ */

function FacilitatorChangePasswordModal({ facilitatorId, onClose }) {
    const [oldPw, setOldPw] = useState('');
    const [newPw, setNewPw] = useState('');
    const [confirmPw, setConfirmPw] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (newPw.length < 3) { setError('New password must be at least 3 characters.'); return; }
        if (newPw !== confirmPw) { setError('Passwords do not match.'); return; }
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/facilitators/change-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    facilitator_id: facilitatorId,
                    old_password: oldPw,
                    new_password: newPw,
                }),
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || 'Failed to change password.');
            }
            setSuccess(true);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const inputStyle = {
        width: '100%',
        padding: '0.7rem 1rem',
        borderRadius: 'var(--radius-md, 6px)',
        border: '1px solid var(--border-subtle, #cbd5e1)',
        background: 'var(--bg-body, #f1f5f9)',
        color: 'var(--text-primary, #1e293b)',
        fontSize: '0.9rem',
        outline: 'none',
        boxSizing: 'border-box',
    };

    const labelStyle = {
        display: 'block',
        fontSize: '0.72rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        color: 'var(--text-muted, #64748b)',
        marginBottom: '0.4rem',
    };

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000,
            background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            <div style={{
                background: 'var(--bg-card, #fff)',
                border: '1px solid var(--border-subtle, #e2e8f0)',
                borderRadius: 'var(--radius-lg, 12px)',
                padding: '2rem',
                maxWidth: '400px',
                width: '90%',
                boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary, #1e293b)' }}>
                        🔑 Change Password
                    </h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: 'var(--text-muted, #94a3b8)' }}>×</button>
                </div>

                {success ? (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>✅</div>
                        <h3 style={{ color: 'var(--text-primary, #1e293b)', margin: '0 0 0.5rem' }}>Password Updated</h3>
                        <p style={{ color: 'var(--text-muted, #64748b)', fontSize: '0.85rem' }}>
                            Your password has been changed successfully.
                        </p>
                        <button onClick={onClose} style={{
                            marginTop: '1rem', background: 'linear-gradient(135deg, #3b82f6, #06b6d4)', color: '#fff',
                            border: 'none', padding: '0.6rem 1.5rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer',
                        }}>Done</button>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {error && (
                            <div style={{
                                background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                                color: '#ef4444', padding: '0.6rem', borderRadius: '6px', fontSize: '0.85rem',
                            }}>{error}</div>
                        )}
                        <div>
                            <label style={labelStyle}>Current Password</label>
                            <input type="password" value={oldPw} onChange={e => setOldPw(e.target.value)} placeholder="Enter current password" required style={inputStyle} />
                        </div>
                        <div>
                            <label style={labelStyle}>New Password</label>
                            <input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="At least 3 characters" required style={inputStyle} />
                        </div>
                        <div>
                            <label style={labelStyle}>Confirm New Password</label>
                            <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} placeholder="Re-enter new password" required style={inputStyle} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                            <button type="button" onClick={onClose} style={{
                                background: 'transparent', border: '1px solid var(--border-subtle, #cbd5e1)',
                                color: 'var(--text-secondary, #475569)', padding: '0.5rem 1rem', borderRadius: '6px',
                                fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer',
                            }}>Cancel</button>
                            <button type="submit" disabled={loading} style={{
                                background: 'linear-gradient(135deg, #3b82f6, #06b6d4)', color: '#fff', border: 'none',
                                padding: '0.5rem 1.25rem', borderRadius: '6px', fontSize: '0.85rem',
                                fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1,
                            }}>{loading ? '⏳ Updating...' : 'Update Password'}</button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}

/* ═════════════════════════════════════════════════════════════════
 *  FACILITATOR SESSION MANAGER (Multi-select Deletion)
 * ═════════════════════════════════════════════════════════════════ */

function FacilitatorSessionManager({ leaderboard, authData, handleResetSession, styles }) {
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [loading, setLoading] = useState(false);

    // Group leaderboard by unique session_id to list the cohorts/teams.
    // Facilitators ONLY see their own, so we don't need additional filtering.
    const uniqueSessionsMap = new Map();
    leaderboard.forEach(s => {
        if (!uniqueSessionsMap.has(s.session_id)) {
            uniqueSessionsMap.set(s.session_id, s);
        }
    });
    const sessionsList = Array.from(uniqueSessionsMap.values());

    const toggleSession = (id) => {
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const toggleAll = () => {
        if (selectedIds.size === sessionsList.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(sessionsList.map(s => s.session_id)));
        }
    };

    const handleDeleteMultiple = async (hardDelete) => {
        if (selectedIds.size === 0) return;
        const hardWarning = hardDelete 
            ? "🧨 HARD DELETE: Are you sure you want to COMPLETELY WIPE these teams and bypass the 7-day retention period?" 
            : `🗑️ Soft Delete ${selectedIds.size} team(s)? Data stays recoverable for 7 days.`;
            
        if (!confirm(hardWarning)) return;

        setLoading(true);
        try {
            // Wait for all deletions sequentially or in parallel
            for (let sid of selectedIds) {
                const endpoint = hardDelete 
                    ? `${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/sessions/${sid}?hard=true` 
                    : `${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/sessions/${sid}`;
                    
                await fetch(endpoint, { method: 'DELETE' });
            }
            alert(`✅ Successfully deleted ${selectedIds.size} team(s).`);
            
            // Trigger a page reload to refresh leaderboard state cleanly
            window.location.reload();
        } catch (e) {
            alert('❌ Failed to delete sessions: ' + e.message);
            setLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Select specific teams below to delete them. You can delete multiple at once.
            </div>

            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '6px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                        <tr style={{ background: 'var(--bg-body)', textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                            <th style={{ padding: '0.75rem', width: '40px' }}>
                                <input 
                                    type="checkbox" 
                                    checked={sessionsList.length > 0 && selectedIds.size === sessionsList.length}
                                    onChange={toggleAll}
                                />
                            </th>
                            <th style={{ padding: '0.75rem' }}>Team / Cohort Name</th>
                            <th style={{ padding: '0.75rem', color: 'var(--text-muted)', textAlign: 'right' }}>Current Round</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sessionsList.length === 0 ? (
                            <tr>
                                <td colSpan="3" style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>No teams available to delete.</td>
                            </tr>
                        ) : sessionsList.map(s => (
                            <tr key={s.session_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                <td style={{ padding: '0.75rem' }}>
                                    <input 
                                        type="checkbox" 
                                        checked={selectedIds.has(s.session_id)}
                                        onChange={() => toggleSession(s.session_id)}
                                    />
                                </td>
                                <td style={{ padding: '0.75rem', fontWeight: 500 }}>
                                    {s.cohort_name || s.session_id.slice(0, 8)}
                                </td>
                                <td style={{ padding: '0.75rem', color: 'var(--text-muted)', textAlign: 'right' }}>
                                    R{s.round_number || 1}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexDirection: 'column', alignItems: 'flex-start' }}>
                <button 
                    className={styles.resetSessionBtn} 
                    onClick={() => handleDeleteMultiple(false)}
                    disabled={selectedIds.size === 0 || loading}
                    style={{ opacity: selectedIds.size === 0 || loading ? 0.6 : 1 }}
                >
                    {loading ? 'Processing...' : `🗑️ Soft Delete ${selectedIds.size} Selected Team(s)`}
                </button>
                {authData?.facilitator_id === 'admin' && (
                    <button 
                        className={styles.resetSessionBtn} 
                        onClick={() => handleDeleteMultiple(true)}
                        disabled={selectedIds.size === 0 || loading}
                        style={{ 
                            background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', borderColor: '#ef4444',
                            opacity: selectedIds.size === 0 || loading ? 0.6 : 1 
                        }}
                        title="God Mode Only: Bypasses 7-day retention."
                    >
                        {loading ? 'Processing...' : '🧨 Hard Delete (Immediately Wipe)'}
                    </button>
                )}
            </div>
        </div>
    );
}
