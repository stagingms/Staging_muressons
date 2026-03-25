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
import StudentBonuses from '../../components/StudentBonuses';
import SimulationManager from '../../components/SimulationManager';
import PeerEvaluation from '../../components/PeerEvaluation';
import BulkMessaging from '../../components/BulkMessaging';

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

    // New state for Sidebar UI
    const [activeTab, setActiveTab] = useState('dashboard_home');
    const [openCategories, setOpenCategories] = useState({
        overview: true,
        monitoring: true,
        interventions: true,
        reports: true,
        collaboration: true,
        system: true
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

    /* ── WebSocket for real-time admin updates ─────────────── */
    useEffect(() => {
        let ws;
        try {
            ws = new WebSocket(`${WS_URL}/api/admin/ws/admin`);
            ws.onmessage = (evt) => {
                const data = JSON.parse(evt.data);
                if (data.type === 'sessions_refresh') {
                    setLeaderboard(data.sessions || []);
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
            const res = await fetch(`${API}/api/admin/leaderboard`);
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
            fetch(`${API}/api/admin/leaderboard`)
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
    const handleResetSession = useCallback(async (sid, cohortName) => {
        const name = cohortName || leaderboard.find(s => s.session_id === sid)?.cohort_name || sid.slice(0, 12);
        const isPlayer = name.includes('Player');
        const prompt = isPlayer
            ? `⚠️ Remove "${name}"?\n\nThis will permanently delete this player's session and all their round data.`
            : `⚠️ Delete cohort "${name}" and ALL its players?\n\nThis will permanently remove the cohort and every player session under it. This action cannot be undone.`;
        if (!confirm(prompt)) return;
        if (!confirm(`Are you absolutely sure you want to delete "${name}"?\n\nClick OK to confirm deletion.`)) return;
        try {
            const res = await fetch(`${API}/api/admin/${sid}/reset`, { method: 'DELETE' });
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
                { id: 'dashboard_home', label: 'Dashboard Home', component: 'DashboardHome' },
                { id: 'timeline', label: 'Round Timeline', component: 'RoundTimeline' },
                { id: 'sim_manager', label: 'Simulation Manager', component: 'SimulationManager' },
            ]
        },
        {
            category: 'Players & Teams',
            icon: '👥',
            id: 'players',
            items: [
                { id: 'registry', label: 'Player Registry', component: 'PlayerRegistry' },
                { id: 'leaderboard', label: 'Leaderboard', component: 'LeaderboardMatrix' },
                { id: 'session_viewer', label: 'Session Viewer', component: 'SessionViewer' },
                { id: 'impersonate', label: 'Team Impersonation', component: 'TeamImpersonation' },
                { id: 'bonuses', label: 'Student Bonuses', component: 'StudentBonuses' },
                { id: 'peer_eval', label: 'Peer Evaluations', component: 'PeerEvaluation' },
            ]
        },
        {
            category: 'Actions & Interventions',
            icon: '⚡',
            id: 'actions',
            items: [
                { id: 'intervention_config', label: 'Intervention Config', component: 'InterventionConfig' },
                { id: 'manual_override', label: 'Manual Overrides', component: 'ManualOverride' },
                { id: 'swipe_file', label: 'Swipe File / Inbox', component: 'SwipeFile' },
                { id: 'broadcast', label: 'Bulk Messaging', component: 'BulkMessaging' },
                { id: 'undo_round', label: 'Undo Round', component: 'UndoRound' },
            ]
        },
        {
            category: 'Analytics & Reports',
            icon: '📊',
            id: 'analytics',
            items: [
                { id: 'platform_analytics', label: 'Platform Analytics', component: 'PlatformAnalytics' },
                { id: 'audit_trail', label: 'Decision Audit Trail', component: 'AuditTrail' },
                { id: 'debrief', label: 'Round Debrief', component: 'DebriefReport' },
                { id: 'reports', label: 'Export Reports', component: 'ReportsExport' },
                { id: 'notes', label: 'Facilitator Notes', component: 'FacilitatorNotes' },
            ]
        },
        {
            category: 'Settings & System',
            icon: '⚙️',
            id: 'settings',
            items: [
                { id: 'materiality', label: 'Materiality Matrix', component: 'MaterialityConfig' },
                { id: 'activity_log', label: 'Activity Logs & Resets', component: 'ActivityLog' },
            ]
        }
    ];

    const renderActiveComponent = () => {
        switch (activeTab) {
            // ── Overview tabs ──
            case 'dashboard_home':
                return <DashboardHome leaderboard={leaderboard} onNavigate={setActiveTab} />;
            case 'timeline':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <RoundTimeline sessionId={selectedSession} leaderboard={leaderboard} />

                        {/* Quiz Controls for Facilitator */}
                        <QuizControlPanel sessions={leaderboard.filter(s => !s.player_id).map(s => ({ session_id: s.session_id, cohort_name: s.cohort_name }))} />
                    </div>
                );
            case 'sim_manager':
                return <SimulationManager leaderboard={leaderboard} onSessionCreated={fetchLeaderboard} />;

            // ── Monitoring tabs ──
            case 'leaderboard':
                return <LeaderboardMatrix leaderboard={leaderboard} selectedSession={selectedSession} onSelectSession={setSelectedSession} onDeleteSession={handleResetSession} />;
            case 'registry':
                return <PlayerRegistry leaderboard={leaderboard} />;
            case 'session_viewer':
                return <SessionViewer leaderboard={leaderboard} />;
            case 'audit_trail':
                return <AuditTrail sessionId={selectedSession} />;
            case 'debrief':
                return <DebriefReport sessionId={selectedSession} />;
            case 'impersonate':
                return <TeamImpersonation leaderboard={leaderboard} selectedSession={selectedSession} />;
            case 'undo_round':
                return <UndoRound sessionId={selectedSession} />;

            // ── Interventions tabs ──
            case 'intervention_config':
                return <InterventionConfig sessionId={selectedSession} />;
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
            case 'notes':
                return <FacilitatorNotes sessionId={selectedSession} />;

            // ── Collaboration tabs ──
            case 'bonuses':
                return <StudentBonuses sessionId={selectedSession} />;
            case 'peer_eval':
                return <PeerEvaluation sessionId={selectedSession} />;

            // ── Config & System tabs ──
            case 'materiality':
                return <MaterialityConfig sessionId={selectedSession} isFacilitator={true} />;
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
                                {selectedSession ? (
                                    <button className={styles.resetSessionBtn} onClick={() => handleResetSession(selectedSession)}>
                                        🗑️ Delete Selected Team ({selectedSession.slice(0, 12)}…)
                                    </button>
                                ) : (
                                    <div style={{ color: 'var(--text-muted)' }}>Select a session in the Leaderboard to delete it individually.</div>
                                )}

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
                        background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
                        boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)',
                        fontSize: '0.8rem',
                        letterSpacing: '0.08em',
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
                                👤 {authData.name} ({authData.facilitator_id})
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
                    {SIDEBAR_CONFIG.map((group) => (
                        <div key={group.id} className={styles.navCategory}>
                            <div className={styles.categoryHeader}>
                                <span>{group.icon} {group.category}</span>
                                <span className={styles.categoryArrow}>▶</span>
                            </div>

                            <div className={styles.categoryItems}>
                                {group.items.map((item) => (
                                    <button
                                        key={item.id}
                                        className={`${styles.navItem} ${activeTab === item.id ? styles.activeNav : ''}`}
                                        onClick={() => setActiveTab(item.id)}
                                    >
                                        {item.label}
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
                        <h1>Workshop Facilitator</h1>
                        <span className={styles.selectedTag}>
                            {selectedSession ? `Target: ${selectedSession.slice(0, 12)}...` : 'Global Mode'}
                        </span>
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
