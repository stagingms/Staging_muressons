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
import CreateCohortModal from '../../components/CreateCohortModal';
import FacilitatorManager from '../../components/FacilitatorManager';
import PasswordInput from '../../components/PasswordInput';
import PeerEvaluation from '../../components/PeerEvaluation';
import BulkMessaging from '../../components/BulkMessaging';
import UsernamePromptModal from '../../components/UsernamePromptModal';
import RoundPacingControl from '../../components/RoundPacingControl';
import ComplexityEventFeed from '../../components/ComplexityEventFeed';
import CohortComparison from '../../components/CohortComparison';
import AutoPauseConfig from '../../components/AutoPauseConfig';
import DecisionTimeline from '../../components/DecisionTimeline';
import DNAComparison from '../../components/DNAComparison';
import FacilitatorTeleprompter from '../../components/FacilitatorTeleprompter';
import FacilitatorAnnotations from '../../components/FacilitatorAnnotations';
import TechnicalGlossary from '../../components/TechnicalGlossary';
import RegulatorySandboxControl from '../../components/RegulatorySandboxControl';
import { FACILITATOR_SIDEBAR, filterSidebarForRole, getTabMeta as _getTabMeta } from '../../config/sidebarConfig';
import NotificationBell from '../../components/NotificationBell';
import OnboardingWizard from '../../components/OnboardingWizard';
import CohortPulse from '../../components/CohortPulse';
import CohortSelector from '../../components/CohortSelector';
import { useConfirm } from '../../components/ConfirmModal';
import ShortcutSheet from '../../components/ShortcutSheet';
import FacilitatorTeachableMoments from '../../components/FacilitatorTeachableMoments';

const API = process.env.NEXT_PUBLIC_API_URL || '';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || `ws://${typeof window !== 'undefined' ? window.location.host : 'localhost:8000'}`;

// Phase R1 (V2-8): single source for the shortcut sheet — if a binding in the
// keydown handler changes, change it HERE too (same file, one constant).
// F-8 (v3): the Ctrl+1…N row is generated at render time from the role's
// actual FILTERED_SIDEBAR group count (the Administration group made the
// hardcoded "4" wrong for super_admin and project_admin).
const FACILITATOR_STATIC_SHORTCUTS = [
    ['Ctrl+Shift+B', 'Open Bulk Messaging (broadcast)'],
    ['?', 'Show / hide this sheet'],
    ['Esc', 'Close dialogs'],
];

/* F1(d): the old SEED_LEADERBOARD constant was removed — it was never wired
 * to anything, and the WS error handler falsely claimed "using seed data". */

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
                // C-3: credentials:'include' is required so the browser stores
                // the HttpOnly mur_session JWT cookie returned by the server.
                // Without this the Set-Cookie response header is silently ignored.
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                // C-2: Store only the display-safe subset in localStorage.
                // Sensitive profile fields (email, contact, programme) must not
                // be persisted to localStorage — XSS can read everything there.
                // The JWT cookie (HttpOnly) holds the real session credential.
                // F-7 (v3/S5): `permissions` is a display-safe boolean map the
                // backend has always returned — the destructure dropped it, so
                // the UI couldn't know e.g. can_create_cohorts. Still C-2
                // compliant: booleans only, no PII.
                const { facilitator_id, role, allowed_tabs, is_admin, username, name, shockwave_enabled, trading_floor_enabled, situation_room_enabled, must_change_password, permissions } = data;
                localStorage.setItem('facilitator_auth', JSON.stringify(
                    { facilitator_id, role, allowed_tabs, is_admin, username, name, shockwave_enabled, trading_floor_enabled, situation_room_enabled, must_change_password, permissions }
                ));
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
            height: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--bg-body)',
            padding: '2rem',
            overflow: 'hidden',
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
                        <PasswordInput
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
                            transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
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
    const [sessionExpired, setSessionExpired] = useState(false);

    useEffect(() => {
        let cachedAuth = null;
        try {
            const stored = localStorage.getItem('facilitator_auth');
            if (stored) {
                cachedAuth = JSON.parse(stored);
                setAuthData(cachedAuth);
            }
        } catch { /* ignore */ }
        setChecked(true);

        // Immediately sync role from backend — localStorage may have a stale role
        // (e.g. facilitator was promoted to super_admin while already logged in).
        if (cachedAuth) {
            fetch(`${API}/api/admin/auth/refresh`, {
                method: 'POST',
                credentials: 'include',
            })
                .then(r => r.ok ? r.json() : null)
                .then(data => {
                    if (data && data.role) {
                        const synced = {
                            ...cachedAuth,
                            role: data.role,
                            is_admin: data.is_admin ?? (data.role === 'super_admin'),
                            allowed_tabs: data.allowed_tabs || cachedAuth.allowed_tabs,
                            permissions: data.permissions || cachedAuth.permissions,
                            name: data.name || cachedAuth.name,
                            username: data.username ?? cachedAuth.username,
                            shockwave_enabled: data.shockwave_enabled ?? cachedAuth.shockwave_enabled,
                            trading_floor_enabled: data.trading_floor_enabled ?? cachedAuth.trading_floor_enabled,
                            situation_room_enabled: data.situation_room_enabled ?? cachedAuth.situation_room_enabled,
                        };
                        localStorage.setItem('facilitator_auth', JSON.stringify(synced));
                        setAuthData(synced);
                    }
                })
                .catch(() => { /* silent — backend may be offline */ });
        }
    }, []);

    const handleLogout = async () => {
        // C-2: Call the server-side logout endpoint so the HttpOnly JWT cookie
        // is properly cleared by the server.  We clear localStorage regardless
        // of whether the server call succeeds (network failure must not trap
        // the user in an authenticated state).
        // M5: Also clear godmode_auth — a super_admin may be simultaneously
        // logged in on both dashboards; logout here should clear both.
        try {
            await fetch(`${API}/api/admin/auth/logout`, {
                method: 'POST',
                credentials: 'include',
            });
        } catch { /* ignore — clear local state regardless */ }
        localStorage.removeItem('facilitator_auth');
        localStorage.removeItem('godmode_auth');
        setAuthData(null);
        setSessionExpired(false);
    };

    const handleSessionExpired = () => {
        localStorage.removeItem('facilitator_auth');
        localStorage.removeItem('godmode_auth');
        setAuthData(null);
        setSessionExpired(true);
    };

    if (!checked) return null; // Avoid flash

    if (!authData) {
        return (
            <>
                {sessionExpired && (
                    <div style={{
                        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 99999,
                        background: 'linear-gradient(90deg, #3b82f6, #06b6d4)',
                        color: '#fff', padding: '0.75rem 1.5rem',
                        display: 'flex', alignItems: 'center', gap: '0.75rem',
                        fontSize: '0.85rem', fontWeight: 600,
                    }}>
                        <span>⏱️</span>
                        <span>Your session has expired. Please sign in again to continue.</span>
                    </div>
                )}
                <div style={{ paddingTop: sessionExpired ? '3rem' : 0 }}>
                    <FacilitatorLoginGate onLogin={(data) => { setAuthData(data); setSessionExpired(false); }} />
                </div>
            </>
        );
    }

    return <FacilitatorDashboard authData={authData} onLogout={handleLogout} onSessionExpired={handleSessionExpired} />;
}


function FacilitatorDashboard({ authData, onLogout, onSessionExpired }) {
    const [leaderboard, setLeaderboard] = useState([]);
    const [selectedSession, _setSelectedSession] = useState(null);
    const [activityLog, setActivityLog] = useState([]);
    const [clockTime, setClockTime] = useState('');
    const wsRef = useRef(null);
    const [showChangePw, setShowChangePw] = useState(false);

    // Phase 4 (F1): admin-WS liveness. The dashboard previously fetched the
    // leaderboard once and then depended forever on a socket with no
    // reconnect — a dropped connection silently froze every panel.
    const [wsState, setWsState] = useState('connecting'); // 'connecting' | 'live' | 'reconnecting'
    const [lastDataAt, setLastDataAt] = useState(null);
    const reconnectAttempts = useRef(0);
    const reconnectTimer = useRef(null);
    const wsMountedRef = useRef(true);

    // Phase 5 (F4): shared tiered confirmation — replaces every chained
    // native confirm() on this screen. See ConfirmModal.js.
    const [confirmAction, confirmModal] = useConfirm();

    // SessionContext persistence — persists selected session across tab switches
    const setSelectedSession = useCallback((sid) => {
        _setSelectedSession(sid);
        try {
            if (sid) localStorage.setItem('fac_selected_session', sid);
            else localStorage.removeItem('fac_selected_session');
        } catch { /* ignore */ }
    }, []);

    /* ── JWT auto-refresh — keeps session alive during long workshops ── */
    useEffect(() => {
        const doRefresh = async () => {
            try {
                const r = await fetch(`${API}/api/admin/auth/refresh`, {
                    method: 'POST',
                    credentials: 'include',
                });
                // If refresh itself returns 401 the cookie has fully expired — trigger re-login
                if (r.status === 401 && onSessionExpired) onSessionExpired();
            } catch { /* silent — backend may be restarting */ }
        };
        // Refresh every 90 minutes (well before 2h JWT expiry)
        const iv = setInterval(doRefresh, 90 * 60 * 1000);
        // Also refresh on window focus (catches overnight/long-idle scenarios)
        const onFocus = () => doRefresh();
        window.addEventListener('focus', onFocus);
        return () => { clearInterval(iv); window.removeEventListener('focus', onFocus); };
    }, []);

    // Restore persisted session on mount
    useEffect(() => {
        try {
            const stored = localStorage.getItem('fac_selected_session');
            if (stored) _setSelectedSession(stored);
        } catch { /* ignore */ }
    }, []);

    // F9 (Phase 5): tab access is derived from the SAME filtered sidebar the
    // nav renders from — see canAccessTab below FILTERED_SIDEBAR. Previously
    // the sidebar used role + allowed_tabs while the quick bar checked
    // allowed_tabs alone, so the two surfaces could disagree.

    // Scaffolding status fetched from God Mode for read-only visibility.
    // Phase 2 (F10): track sync freshness so the strip can show when it last
    // agreed with God Mode instead of silently rendering stale pills.
    const [scaffoldingStatus, setScaffoldingStatus] = useState(null);
    const [scaffoldingSync, setScaffoldingSync] = useState({ at: null, failed: false });
    const refreshScaffolding = useCallback(() => {
        fetch(`${API}/api/admin/scaffolding-status`)
            .then(r => r.ok ? r.json() : null)
            .then(d => {
                if (d) { setScaffoldingStatus(d); setScaffoldingSync({ at: Date.now(), failed: false }); }
                else setScaffoldingSync(s => ({ ...s, failed: true }));
            })
            .catch(() => setScaffoldingSync(s => ({ ...s, failed: true })));
    }, []);
    useEffect(() => {
        refreshScaffolding();
        const interval = setInterval(refreshScaffolding, 30000);
        return () => clearInterval(interval);
    }, [refreshScaffolding]);

    // God Mode analytics visibility state — controls which sections are shown to facilitators
    const [godVisibility, setGodVisibility] = useState({
        materiality_matrix: true,
        technical_reference: true,
    });

    // New state for Sidebar UI
    const [activeTab, setActiveTab] = useState('dashboard_home');
    const [createCohortOpen, setCreateCohortOpen] = useState(false);
    const [editCohortSession, setEditCohortSession] = useState(null); // set to a session object to open edit modal
    const [sidebarOpen, setSidebarOpen] = useState(true); // Mobile sidebar toggle
    const [openCategories, setOpenCategories] = useState({
        command: true,
        classroom: false,
        analytics: false,
        config: false,
    });

    const toggleCategory = (catId) => {
        setOpenCategories(prev => ({ ...prev, [catId]: !prev[catId] }));
    };

    // Keyboard shortcuts — Phase 6 (F12):
    //  · Ctrl+1–4 toggles the target group WITHOUT collapsing the others
    //    (the old exclusive-open was a surprise, not a feature)
    //  · broadcast moved off Ctrl+B (browser bookmark/bold conflict) to
    //    Ctrl+Shift+B — same binding semantics as God Mode
    //  · '?' opens a discoverable shortcut sheet
    const [showShortcuts, setShowShortcuts] = useState(false);
    // F-8 (v3): Ctrl+1…N addresses the groups the sidebar actually renders for
    // this role (updated each render below, after FILTERED_SIDEBAR is derived)
    // instead of a hardcoded 4-entry list that predates the Administration group.
    const sidebarGroupIdsRef = useRef([]);
    useEffect(() => {
        const handler = (e) => {
            const tag = e.target?.tagName;
            const typing = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.target?.isContentEditable;
            if (!typing && e.key === '?' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                setShowShortcuts(s => !s);
                return;
            }
            if (e.key === 'Escape') setShowShortcuts(false);
            if (e.ctrlKey || e.metaKey) {
                const categoryKeys = sidebarGroupIdsRef.current;
                if (e.key >= '1' && e.key <= '9') {
                    const idx = parseInt(e.key) - 1;
                    if (categoryKeys[idx]) {
                        e.preventDefault();
                        setOpenCategories(prev => ({ ...prev, [categoryKeys[idx]]: !prev[categoryKeys[idx]] }));
                    }
                }
                if (e.shiftKey && (e.key === 'b' || e.key === 'B')) {
                    e.preventDefault();
                    setActiveTab('broadcast');
                }
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, []);

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

    /* ── WebSocket for real-time admin updates — Phase 4 (F1) ──────────
       Auto-reconnect with capped exponential backoff. ADMIN socket only:
       the player socket (hooks/useSimulation.js) is deliberately untouched.
       Wire protocol, URL, and message handling are identical — only the
       lifecycle around the socket changed. */
    useEffect(() => {
        wsMountedRef.current = true;

        const scheduleReconnect = () => {
            if (!wsMountedRef.current || reconnectTimer.current) return;
            setWsState('reconnecting');
            reconnectAttempts.current += 1;
            // 2s, 4s, 8s, 16s, 30s cap — fast enough for a venue Wi-Fi blip,
            // slow enough not to hammer a restarting backend.
            const delay = Math.min(30000, 1000 * 2 ** Math.min(reconnectAttempts.current, 5));
            reconnectTimer.current = setTimeout(() => {
                reconnectTimer.current = null;
                connect();
            }, delay);
        };

        const connect = () => {
            if (!wsMountedRef.current) return;
            // Idempotent: close any previous socket so reconnects never leak
            // connections (verifiable via WS CONNECTIONS in God Mode).
            try { wsRef.current?.close(); } catch { /* ignore */ }
            let ws;
            try {
                ws = new WebSocket(`${WS_URL}/api/admin/ws/admin?facilitator_id=${authData.facilitator_id}`);
            } catch {
                scheduleReconnect();
                return;
            }
            wsRef.current = ws;

            ws.onopen = () => {
                if (!wsMountedRef.current) return;
                const wasRetry = reconnectAttempts.current > 0;
                reconnectAttempts.current = 0;
                setWsState('live');
                addLog({ type: 'system', message: wasRetry ? 'Admin WebSocket reconnected' : 'Admin WebSocket connected' });
                // Catch up on anything missed while disconnected. Events from
                // the gap live in the server-side audit trail, not this feed.
                if (wasRetry) fetchLeaderboard();
            };
            ws.onmessage = (evt) => {
                setLastDataAt(Date.now());
                const data = JSON.parse(evt.data);
                if (data.type === 'sessions_refresh' || data.type === 'sessions_refresh_trigger') {
                    fetchLeaderboard();
                } else if (data.type === 'settings_changed') {
                    // God Mode Event Bus: refresh scaffolding strip immediately
                    refreshScaffolding();
                    addLog({ type: 'god_mode', message: `⚙️ God Mode updated: ${(data.changed_keys || []).join(', ')}` });
                } else if (data.type === 'pacing_override') {
                    addLog({ type: 'god_mode', message: `⏱️ Pacing changed to "${data.new_mode}" on session ${data.session_id}`, severity: 'warning' });
                    fetchLeaderboard();
                } else if (data.type === 'system_freeze') {
                    // Refresh scaffolding to pick up freeze state
                    refreshScaffolding();
                    addLog({ type: 'god_mode', message: data.frozen ? '❄️ System FROZEN by God Mode' : '🟢 System UNFROZEN', severity: data.frozen ? 'critical' : 'info' });
                } else if (data.type === 'universal_broadcast') {
                    // Facilitators also see God Mode broadcasts in their activity log
                    const icon = data.priority === 'critical' ? '🚨' : data.priority === 'warning' ? '⚠️' : '📢';
                    addLog({ type: 'god_mode', message: `${icon} Broadcast: "${data.title}" — ${data.message}`, severity: data.priority || 'info' });
                } else {
                    addLog(data);
                }
            };
            ws.onerror = () => {
                if (wsMountedRef.current) addLog({ type: 'system', message: 'WebSocket error — live updates may be interrupted', severity: 'warning' });
            };
            ws.onclose = () => {
                if (wsMountedRef.current) scheduleReconnect();
            };
        };

        connect();
        return () => {
            wsMountedRef.current = false;
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
            try { wsRef.current?.close(); } catch { /* ignore */ }
        };
    }, []);

    const addLog = useCallback((entry) => {
        setActivityLog((prev) => [
            { ...entry, timestamp: new Date().toLocaleTimeString() },
            ...prev.slice(0, 49),
        ]);
    }, []);

    /* ── Auth-aware fetch helper for admin endpoints ──────────────────── */
    // All admin requests authenticate via the HttpOnly JWT cookie (credentials:'include').
    // The X-Facilitator-Id header was removed — the backend ignores it for auth.
    // Super-admin sees ALL cohorts; regular facilitators are scoped to their own
    const isSuperAdmin = authData.role === 'super_admin' || authData.is_admin;
    const leaderboardUrl = isSuperAdmin
        ? `${API}/api/admin/leaderboard`
        : `${API}/api/admin/leaderboard?facilitator_id=${authData.facilitator_id}`;

    /* ── Fetch leaderboard on mount ─────────────────────────── */
    const fetchLeaderboard = useCallback(async () => {
        try {
            const res = await fetch(leaderboardUrl, {
                credentials: 'include',
            });
            if (res.ok) {
                const data = await res.json();
                setLeaderboard(data.leaderboard || []);
                setLastDataAt(Date.now());
            }
        } catch {
            // Backend offline — keep existing data
        }
    }, [leaderboardUrl]);

    useEffect(() => {
        fetchLeaderboard();
    }, [fetchLeaderboard]);

    // Phase 4 (F1): polling fallback — ONLY while the socket is down. The
    // dashboard degrades to "slow" instead of "silently frozen", and stops
    // polling the moment the socket is back (no steady-state load change).
    useEffect(() => {
        if (wsState === 'live') return;
        const t = setInterval(() => {
            fetchLeaderboard();
            refreshScaffolding();
        }, 30000);
        return () => clearInterval(t);
    }, [wsState, fetchLeaderboard, refreshScaffolding]);

    const handleOverride = useCallback(
        (result) => {
            addLog({ type: 'override', ...result });
            fetch(leaderboardUrl, { credentials: 'include' })
                .then((r) => r.json())
                .then((d) => d.leaderboard && setLeaderboard(d.leaderboard))
                .catch(() => { });
        },
        [addLog, leaderboardUrl]
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
        // F4: one confirm with a blast-radius preview beats a chain of
        // identical dialogs that trains click-through.
        const childPlayers = leaderboard.filter(s => s.parent_cohort_id === sid).length;
        const round = leaderboard.find(s => s.session_id === sid)?.round_number || 1;
        const ok = await confirmAction({
            title: hard ? `🧨 Hard delete "${name}"` : (isPlayer ? `🗑️ Remove "${name}"` : `🗑️ Delete cohort "${name}"`),
            message: isPlayer
                ? 'This permanently removes this player session and all of its round data.'
                : 'This removes the cohort and every player session under it.',
            impact: `${isPlayer ? 'Player session' : `Cohort + ${childPlayers} player session(s)`} · currently at Round ${round}.${hard ? ' HARD delete bypasses the 7-day recovery window.' : ' Recoverable for 7 days (soft delete).'}`,
            requirePhrase: hard ? 'DELETE' : null,
            confirmLabel: hard ? 'Hard delete now' : 'Delete',
        });
        if (!ok) return;

        try {
            const endpoint = `${API}/api/admin/${sid}/reset${hard ? '?hard=true' : ''}`;
            const res = await fetch(endpoint, { method: 'DELETE', credentials: 'include' });
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
    }, [leaderboard, selectedSession, addLog, fetchLeaderboard, confirmAction]);

    // Phase R1 (V2-7): the old handleResetAll callback was DEAD CODE — no
    // button ever invoked it, while the activity_log tooltip advertised a
    // "full system reset" that therefore didn't exist on this screen. The
    // real reset-all lives in God Mode's Danger Zone (typed-phrase guarded).
    // Removed rather than wired: a facilitator screen has no business
    // destroying every other facilitator's cohorts.


    // Apply role-based tab filtering using shared config
    // Also gate the Regulatory Sandbox behind God Mode's regulatory_sandbox_enabled toggle
    const sandboxEnabledByGodMode = scaffoldingStatus?.features?.find(f => f.key === 'regulatory_sandbox_enabled')?.enabled ?? false;
    const FILTERED_SIDEBAR = filterSidebarForRole(FACILITATOR_SIDEBAR, authData.role || 'facilitator', authData.allowed_tabs || ['*'])
        .map(group => ({
            ...group,
            items: group.items.filter(item => {
                if (item.id === 'regulatory_sandbox' && !sandboxEnabledByGodMode) return false;
                return true;
            }),
        }))
        .filter(group => group.items.length > 0);

    // F9: ONE access gate consumed by the sidebar, the quick-action bar, and
    // the tab router.
    const visibleTabIds = new Set(FILTERED_SIDEBAR.flatMap(g => g.items.map(i => i.id)));
    const canAccessTab = (tabId) => visibleTabIds.has(tabId);

    // F-8 (v3): keep the shortcut handler's group list in sync with what the
    // sidebar renders (ref write on every render — the handler reads it live).
    sidebarGroupIdsRef.current = FILTERED_SIDEBAR.map(g => g.id);

    const getTabMeta = (tabId) => _getTabMeta(FILTERED_SIDEBAR, tabId);

    const renderActiveComponent = () => {
        // Only top-level cohort sessions (no player sub-sessions) owned by this facilitator
        const ownCohorts = leaderboard.filter(
            s => !s.player_id && s.facilitator_id === authData.facilitator_id
        );

        // Phase 3 (F2): session-scoped tools embed the SAME global selector in
        // their empty state instead of sending the facilitator to hunt for the
        // hidden click-a-leaderboard-row convention.
        const requireCohort = (title, node) => {
            if (selectedSession) return node;
            return (
                <div style={{ padding: '3rem 2rem', textAlign: 'center', background: 'var(--bg-card)', borderRadius: '12px', border: '1px dashed var(--border-subtle)' }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem', opacity: 0.5 }}>🎯</div>
                    <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>{title} needs a target cohort</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '520px', margin: '0 auto 1rem' }}>
                        Choose the cohort this tool should act on. The same selection drives every
                        session-scoped tool and the quick actions in the bottom bar.
                    </p>
                    <CohortSelector leaderboard={leaderboard} selectedSession={selectedSession} onSelect={setSelectedSession} />
                </div>
            );
        };

        // F9: unknown or role-hidden tabs render an explicit state instead of
        // silently falling through. 'audit_trail' stays reachable as a legacy
        // alias (merged into Decision History).
        const LEGACY_TABS = new Set(['audit_trail']);
        if (!visibleTabIds.has(activeTab) && !LEGACY_TABS.has(activeTab)) {
            return (
                <div style={{ padding: '3rem 2rem', textAlign: 'center', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem', opacity: 0.4 }}>🔒</div>
                    <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>This view isn&apos;t available</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                        It may require a higher role, or the link that brought you here is stale.
                    </p>
                    <button onClick={() => setActiveTab('dashboard_home')} style={{ padding: '0.5rem 1.2rem', borderRadius: '8px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', cursor: 'pointer', fontWeight: 600 }}>
                        ← Back to Dashboard
                    </button>
                </div>
            );
        }

        switch (activeTab) {
            // ── Overview tabs ──
            case 'dashboard_home':
                return (
                    <>
                        {/* Scaffolding Status Strip — read-only view of God Mode settings */}
                        {scaffoldingStatus && (
                            <div style={{
                                display: 'flex', flexWrap: 'wrap', gap: '0.4rem', padding: '0.75rem 1rem',
                                background: 'var(--bg-elevated)', borderRadius: '10px',
                                border: '1px solid var(--border-subtle)', marginBottom: '1rem',
                                alignItems: 'center', overflow: 'visible',
                            }}>
                                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginRight: '0.5rem' }}>
                                    🔧 Active Scaffolding:
                                </span>
                                {scaffoldingStatus.features.map(f => (
                                    <div key={f.key} className={styles.pillWrap} data-tip={f.description || ''}>
                                    <span style={{
                                        fontSize: '0.7rem', padding: '0.2rem 0.5rem',
                                        borderRadius: '6px', fontWeight: 600,
                                        background: f.enabled ? 'rgba(34,197,94,0.15)' : 'rgba(107,114,128,0.12)',
                                        color: f.enabled ? '#22c55e' : 'var(--text-muted)',
                                        border: `1px solid ${f.enabled ? 'rgba(34,197,94,0.3)' : 'rgba(107,114,128,0.2)'}`,
                                    }}>
                                        {f.enabled ? '●' : '○'} {f.label}
                                    </span>
                                    </div>
                                ))}
                                {scaffoldingStatus.system_frozen && (
                                    <span style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', borderRadius: '6px', fontWeight: 700, background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }}>
                                        🧊 SYSTEM FROZEN
                                    </span>
                                )}
                                {scaffoldingSync.failed ? (
                                    <span style={{ marginLeft: 'auto', fontSize: '0.68rem', fontWeight: 700, color: '#ef4444' }}>
                                        ⚠️ Not synced{scaffoldingSync.at ? ` — showing state from ${new Date(scaffoldingSync.at).toLocaleTimeString()}` : ''}
                                    </span>
                                ) : scaffoldingSync.at ? (
                                    <span style={{ marginLeft: 'auto', fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                                        synced {new Date(scaffoldingSync.at).toLocaleTimeString()}
                                    </span>
                                ) : null}
                            </div>
                        )}
                        {/* F-7 (v3/S5): the button's truth is the per-profile
                            can_create_cohorts permission (toggled in the
                            Registry), not the role string. Fallback to the old
                            role heuristic when the flag is absent (older cached
                            auth / project_admin virtual account). */}
                        <DashboardHome leaderboard={leaderboard} onNavigate={setActiveTab} selectedSession={selectedSession} onCreateCohort={(
                            authData.permissions?.can_create_cohorts !== undefined
                                ? authData.permissions.can_create_cohorts !== false
                                : (authData.role || 'facilitator') !== 'facilitator'
                        ) ? () => setCreateCohortOpen(true) : null} canAccessTab={canAccessTab} role={authData.role || 'facilitator'} />
                        <CreateCohortModal
                            isOpen={createCohortOpen}
                            onClose={() => setCreateCohortOpen(false)}
                            onCreated={(newSession) => {
                                setCreateCohortOpen(false);
                                fetchLeaderboard();
                            }}
                            currentFacilitatorId={authData.facilitator_id}
                            currentFacilitatorRole={authData.role || 'facilitator'}
                        />
                    </>
                );
            case 'facilitator_registry':
                // W-PA: registry surface for project_admin (and super_admin)
                // inside the facilitator portal — same component God Mode uses.
                return <FacilitatorManager onNavigate={(tab) => setActiveTab(tab)} authContext={authData} />;

            case 'timeline': {
                // F7: keep the per-cohort ceo_interview_* fields the leaderboard
                // already carries, so the Interview panel renders each cohort's
                // actual configuration instead of a copied global.
                const filteredSessions = leaderboard
                    .filter(s => !s.player_id && (authData.role !== 'facilitator' || s.facilitator_id === authData.facilitator_id))
                    .map(s => ({
                        session_id: s.session_id,
                        cohort_name: s.cohort_name,
                        ceo_interview_enabled: s.ceo_interview_enabled,
                        ceo_interview_voice_gender: s.ceo_interview_voice_gender,
                    }));
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <RoundTimeline sessionId={selectedSession} leaderboard={leaderboard} />

                        {/* F7: pacing/quiz/interview grouped under an explicit
                            "Session Setup" heading. A dedicated sidebar tab was
                            rejected: the backend's ROLE_ALLOWED_TABS lists are
                            explicit, so an unknown tab id would silently vanish
                            for non-super-admins (backend edits are out of scope). */}
                        <div>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.6rem', margin: '0 0 0.75rem' }}>
                                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                                    ⚙️ Session Setup
                                </h2>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    pacing · quizzes · CEO interview — configured per cohort
                                </span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                                <RoundPacingControl sessions={filteredSessions} selectedSession={selectedSession} />
                                <QuizControlPanel sessions={filteredSessions} />
                                <InterviewControlPanel sessions={filteredSessions} />
                            </div>
                        </div>
                    </div>
                );
            }
            case 'teleprompter': {
                // Derive round from the selected cohort session — not the global max
                const selectedCohort = leaderboard.find(s => s.session_id === selectedSession);
                const cohortRound = selectedCohort?.round_number || 1;
                return (
                    <FacilitatorTeleprompter
                        currentRound={cohortRound}
                        sessionId={selectedSession}
                        leaderboard={leaderboard}
                        onSelectSession={setSelectedSession}
                        situationRoomEnabled={authData?.situation_room_enabled !== false}
                    />
                );
            }

            // ── Monitoring tabs ──
            case 'leaderboard':
                return (
                    <LeaderboardMatrix leaderboard={leaderboard} selectedSession={selectedSession} onSelectSession={setSelectedSession} onDeleteSession={isSuperAdmin ? handleResetSession : null} />
                );
            case 'registry':
                return (
                    <>
                        {authData.role !== 'facilitator' && (
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
                                        transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                                    }}
                                >
                                    + New Cohort
                                </button>
                            </div>
                        )}
                        <PlayerRegistry
                            leaderboard={leaderboard}
                            isSuperAdmin={isSuperAdmin}
                            isLeadOrAdmin={authData.role === 'lead_facilitator' || isSuperAdmin}
                            onEditCohort={setEditCohortSession}
                            currentFacilitatorRole={authData.role || 'facilitator'}
                        />
                        {/* Create new cohort modal */}
                        <CreateCohortModal
                            isOpen={createCohortOpen}
                            onClose={() => setCreateCohortOpen(false)}
                            onCreated={(newSession) => {
                                setCreateCohortOpen(false);
                                fetchLeaderboard();
                            }}
                            currentFacilitatorId={authData.facilitator_id}
                            currentFacilitatorRole={authData.role || 'facilitator'}
                        />
                        {/* Edit existing cohort modal */}
                        <CreateCohortModal
                            isOpen={!!editCohortSession}
                            onClose={() => setEditCohortSession(null)}
                            onCreated={() => {
                                setEditCohortSession(null);
                                fetchLeaderboard();
                            }}
                            editSession={editCohortSession}
                            currentFacilitatorId={authData.facilitator_id}
                            currentFacilitatorRole={authData.role || 'facilitator'}
                        />
                    </>
                );
            case 'session_viewer':
                return <SessionViewer leaderboard={leaderboard} />;
            case 'audit_trail':  // merged into Decision History
                return <AuditTrail sessionId={selectedSession} />;
            case 'debrief':
                return <DebriefReport sessionId={selectedSession} />;
            case 'impersonate':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        <TeamImpersonation leaderboard={leaderboard} selectedSession={selectedSession} />
                        {!selectedSession && (
                            <div style={{ padding: '2rem', background: 'var(--bg-elevated)', borderRadius: '12px', border: '1px dashed var(--border-subtle)', textAlign: 'center' }}>
                                <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem', opacity: 0.5 }}>🎭</div>
                                <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Select a team to see their simulation exactly as they do</h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '500px', margin: '0 auto' }}>
                                    Useful for: live debugging, screen-sharing during debrief, demonstrating the player experience, or verifying a student&apos;s reported issue.
                                </p>
                            </div>
                        )}
                    </div>
                );
            case 'undo_round': {
                const fullSession = leaderboard.find(s => s.session_id === selectedSession);
                return requireCohort('Undo Round', <UndoRound session={fullSession} />);
            }

            // ── Interventions tabs ──
            case 'intervention_config':
                return requireCohort('Interventions', <InterventionConfig sessionId={selectedSession} />);
            case 'auto_pause':
                return requireCohort('Auto-Pause Triggers', <AutoPauseConfig sessionId={selectedSession} />);
            case 'manual_override':
                return requireCohort('Manual Overrides', (
                    <div className={styles.controlsRow}>
                        <ManualOverride sessionId={selectedSession} onOverrideApplied={handleOverride} />
                    </div>
                ));
            case 'swipe_file':
                return requireCohort('Swipe File / Inbox', <SwipeFile sessionId={selectedSession} onMessageSent={handleMessageSent} />);
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
            case 'dna_comparison':
                return <DNAComparison sessionId={selectedSession} leaderboard={leaderboard} />;
            case 'annotations':
                return <FacilitatorAnnotations sessionId={selectedSession} leaderboard={leaderboard} />;

            // ── Collaboration tabs ──
            case 'bonuses':
                return requireCohort('Student Bonuses', <StudentBonuses sessionId={selectedSession} />);
            case 'peer_eval':
                return requireCohort('Peer Evaluations', <PeerEvaluation sessionId={selectedSession} />);

            case 'teaching_journal':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <FacilitatorNotes sessionId={selectedSession} />
                        <FacilitatorAnnotations sessionId={selectedSession} leaderboard={leaderboard} />
                    </div>
                );

            // ── Config & System tabs ──
            case 'regulatory_sandbox': {
                if (!sandboxEnabledByGodMode) {
                    return (
                        <div style={{
                            padding: '3rem 2rem', textAlign: 'center',
                            background: 'var(--bg-card)', borderRadius: '12px',
                            border: '1px solid var(--border-subtle)',
                        }}>
                            <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.4 }}>🔒</div>
                            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Regulatory Sandbox Locked</h3>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', maxWidth: '500px', margin: '0 auto' }}>
                                This feature must be enabled by the Super Administrator in God Mode before it becomes available.
                                Contact your system administrator to enable the Regulatory Sandbox engine.
                            </p>
                        </div>
                    );
                }
                return <RegulatorySandboxControl sessionId={selectedSession} />;
            }
            case 'materiality':
                return <MaterialityConfig sessionId={selectedSession} isFacilitator={true} readOnly={authData?.role === 'facilitator'} />;
            case 'technical_glossary':
                return (
                    <div style={{ padding: '1.5rem' }}>
                        <TechnicalGlossary />
                    </div>
                );
            case 'platform_analytics':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <PlatformAnalytics visibility={null} leaderboard={leaderboard} onNavigate={setActiveTab} onSelectSession={setSelectedSession} />
                        {/* Cohort Pulse heatmap — shows live KPI grid across all teams in selected cohort */}
                        <CohortPulse cohortId={selectedSession} />
                        {/* B5: teachable-moment prompts when a cohort converges on an adverse flag */}
                        <FacilitatorTeachableMoments cohortId={selectedSession} />
                    </div>
                );

            case 'activity_log':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        {isSuperAdmin && (
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
                                        onRefresh={fetchLeaderboard}
                                        confirmAction={confirmAction}
                                        isSuperAdmin={isSuperAdmin}
                                    />
                                </div>
                            </section>
                        )}

                        <section className={styles.logPanel}>
                            {/* F11: this log is in-memory only (50 entries, cleared on
                                refresh) — it must not present itself as the audit trail. */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                                <h2>Live Feed (this browser session)</h2>
                                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                    Entries are kept in memory only and cleared on refresh — the durable record is{' '}
                                    <button
                                        onClick={() => setActiveTab('decision_replay')}
                                        style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', textDecoration: 'underline', fontSize: '0.75rem', padding: 0 }}
                                    >
                                        Decision History
                                    </button>.
                                </span>
                            </div>
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

    // If no username set, show ONLY the username prompt — no dashboard behind it
    if (!authData.username) {
        return (
            <div style={{
                position: 'fixed', inset: 0, zIndex: 16000,
                background: '#080c18',
            }}>
                <UsernamePromptModal 
                    userId={authData.facilitator_id}
                    role="facilitator"
                    onComplete={(newUsername) => {
                        // C-2: keep only the safe display subset (same rule as login)
                        const { facilitator_id, role, allowed_tabs, is_admin, name, shockwave_enabled, trading_floor_enabled, situation_room_enabled } = authData;
                        const updated = { facilitator_id, role, allowed_tabs, is_admin, name, username: newUsername, shockwave_enabled, trading_floor_enabled, situation_room_enabled };
                        localStorage.setItem('facilitator_auth', JSON.stringify(updated));
                        window.location.reload();
                    }}
                />
            </div>
        );
    }

    return (
        <div className={styles.dashboard} data-theme="dark">
            
            {/* Phase 5 (F4): shared tiered confirmation modal */}
            {confirmModal}

            {/* Phase 6 (F12): shortcut sheet ('?') — F-8 (v3): the Ctrl+1…N row
                reflects this role's actual group count. */}
            {showShortcuts && (
                <ShortcutSheet
                    onClose={() => setShowShortcuts(false)}
                    shortcuts={[
                        [FILTERED_SIDEBAR.length > 1 ? `Ctrl+1…${FILTERED_SIDEBAR.length}` : 'Ctrl+1', 'Toggle sidebar group open/closed'],
                        ...FACILITATOR_STATIC_SHORTCUTS,
                    ]}
                />
            )}

            {/* ── Change Password Modal ── */}
            {showChangePw && (
                <FacilitatorChangePasswordModal
                    facilitatorId={authData.facilitator_id}
                    onClose={() => setShowChangePw(false)}
                />
            )}

            {/* ── Forced first-login password change ──
                Facilitators are created with the default password
                (Muressons123); the login response sets must_change_password
                and this modal cannot be dismissed until a personal password
                is set. Master-bypass logins never see it (server suppresses
                the flag). */}
            {authData?.must_change_password && !showChangePw && (
                <FacilitatorChangePasswordModal
                    facilitatorId={authData.facilitator_id}
                    forced
                    onClose={() => {}}
                    onSuccess={() => {
                        setAuthData(prev => { const u = { ...prev }; delete u.must_change_password; return u; });
                        try {
                            const cached = JSON.parse(localStorage.getItem('facilitator_auth') || '{}');
                            delete cached.must_change_password;
                            localStorage.setItem('facilitator_auth', JSON.stringify(cached));
                        } catch {}
                    }}
                />
            )}

            {/* ── Onboarding Wizard (first-time only) ── */}
            <OnboardingWizard mode="facilitator" userId={authData.facilitator_id} onStepChange={(tab) => setActiveTab(tab)} />

            {/* ── Sidebar ── */}
            <aside className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <div style={{
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        textTransform: 'uppercase',
                        letterSpacing: '0.18em',
                        color: '#f59e0b',
                        marginBottom: '0.3rem',
                        textShadow: '0 0 12px rgba(245,158,11,0.25)',
                    }}>MURESSONS GLOBAL</div>
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
                            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                                <NotificationBell activityLog={activityLog} />
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
                                        transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
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
                                        transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
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

                    {/* ── Live-session consoles (moved from God Mode) ──
                        Visibility is driven by the per-facilitator capability
                        flags set in the Facilitator Registry; the ring-bell and
                        shockwave endpoints enforce the same flags server-side
                        (403 when off), so hiding the link is presentation, not
                        the security boundary. */}
                    {authData?.trading_floor_enabled !== false && (
                        <a
                            href="/admin/trading-floor"
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.navItem}
                            data-tooltip="Project the live market board + closing bell on the room screen"
                            style={{
                                display: 'flex', alignItems: 'center', gap: '8px', margin: '12px 8px 0',
                                padding: '8px 10px', borderRadius: '8px', textDecoration: 'none',
                                color: 'var(--accent-gold, #f59e0b)', fontWeight: 700,
                                border: '1px solid rgba(245,158,11,0.35)', background: 'rgba(245,158,11,0.08)',
                            }}
                        >
                            <span style={{ width: '18px', textAlign: 'center', flexShrink: 0, fontSize: '0.85rem' }}>🔔</span>
                            <span>Trading Floor ↗</span>
                        </a>
                    )}
                    {authData?.shockwave_enabled !== false && (
                        <a
                            href="/admin/shockwave"
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.navItem}
                            data-tooltip="DESTRUCTIVE — opens the console that detonates a synchronized crisis across every team in a cohort. Nothing fires until you confirm inside the console."
                            style={{
                                display: 'flex', alignItems: 'center', gap: '8px', margin: '8px 8px 0',
                                padding: '8px 10px', borderRadius: '8px', textDecoration: 'none',
                                color: '#ef4444', fontWeight: 700,
                                border: '1px solid rgba(239,68,68,0.35)', background: 'rgba(239,68,68,0.08)',
                            }}
                        >
                            <span style={{ width: '18px', textAlign: 'center', flexShrink: 0, fontSize: '0.85rem' }}>🌊</span>
                            <span>Shockwave Console ↗</span>
                        </a>
                    )}
                    {/* W-E (W7): Region War-Map projector — read-only view of the
                        existing leaderboard; the page has its own ON/OFF switch,
                        so the link needs no capability flag. */}
                    <a
                        href="/admin/war-map"
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.navItem}
                        data-tooltip="Project the live situation map — teams by region, crisis pulses, R5 cyclone track. Read-only."
                        style={{
                            display: 'flex', alignItems: 'center', gap: '8px', margin: '8px 8px 0',
                            padding: '8px 10px', borderRadius: '8px', textDecoration: 'none',
                            color: '#2dd4bf', fontWeight: 700,
                            border: '1px solid rgba(45,212,191,0.35)', background: 'rgba(45,212,191,0.08)',
                        }}
                    >
                        <span style={{ width: '18px', textAlign: 'center', flexShrink: 0, fontSize: '0.85rem' }}>🗺️</span>
                        <span>Region War-Map ↗</span>
                    </a>
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

            {/* ── Floating Action Bar ── */}
            <div style={{
                position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 1200,
                display: 'flex', alignItems: 'center', gap: '0.75rem', rowGap: '0.4rem',
                flexWrap: 'wrap', /* R5 (V2-5): wrap at laptop widths, never clip */
                padding: '0.6rem 1.5rem',
                background: 'rgba(17,24,39,0.95)', backdropFilter: 'blur(12px)',
                borderTop: '1px solid var(--border-subtle)',
                fontSize: '0.78rem',
            }}>
                {/* Role badge */}
                <span style={{
                    padding: '0.2rem 0.6rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.68rem',
                    textTransform: 'uppercase', letterSpacing: '0.05em',
                    background: authData?.role === 'super_admin' ? 'rgba(245,158,11,0.15)' :
                                authData?.role === 'lead_facilitator' ? 'rgba(99,102,241,0.15)' : 'rgba(59,130,246,0.15)',
                    color: authData?.role === 'super_admin' ? '#f59e0b' :
                           authData?.role === 'lead_facilitator' ? '#818cf8' : '#60a5fa',
                    border: `1px solid ${authData?.role === 'super_admin' ? 'rgba(245,158,11,0.3)' :
                                          authData?.role === 'lead_facilitator' ? 'rgba(99,102,241,0.3)' : 'rgba(59,130,246,0.3)'}`,
                }}>
                    {authData?.role === 'super_admin' ? '👑 Super Admin' :
                     authData?.role === 'lead_facilitator' ? '⭐ Lead' : '🎓 Facilitator'}
                </span>

                {/* Phase 4 (F1): connection truth — a facilitator must be able to
                    tell "live data" from "last known snapshot" at a glance. */}
                <span
                    title={wsState === 'live'
                        ? 'Real-time connection healthy'
                        : 'Live updates interrupted — reconnecting automatically; data refreshes every 30s meanwhile. Events during the gap are in the server audit trail (Decision History).'}
                    style={{
                        padding: '0.2rem 0.6rem', borderRadius: '6px', fontWeight: 700, fontSize: '0.68rem',
                        background: wsState === 'live' ? 'rgba(34,197,94,0.12)' : 'rgba(245,158,11,0.15)',
                        color: wsState === 'live' ? '#22c55e' : '#f59e0b',
                        border: `1px solid ${wsState === 'live' ? 'rgba(34,197,94,0.3)' : 'rgba(245,158,11,0.35)'}`,
                        whiteSpace: 'nowrap',
                    }}
                >
                    {wsState === 'live' ? '● Live' : wsState === 'connecting' ? '○ Connecting…' : '⟳ Reconnecting…'}
                    {lastDataAt ? ` · ${new Date(lastDataAt).toLocaleTimeString()}` : ''}
                </span>

                {/* Phase 3 (F2): the selection is now settable right where the
                    quick actions need it — not only via the hidden
                    click-a-leaderboard-row convention. */}
                <span style={{ color: 'var(--text-muted)', flex: 1, display: 'inline-flex', alignItems: 'center', gap: '0.6rem' }}>
                    <CohortSelector
                        leaderboard={leaderboard}
                        selectedSession={selectedSession}
                        onSelect={setSelectedSession}
                        compact
                    />
                    {selectedSession ? (
                        <span
                            title={`${leaderboard.find(s => s.session_id === selectedSession)?.cohort_name || selectedSession} — R${leaderboard.find(s => s.session_id === selectedSession)?.round_number || '?'}`}
                            style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                        >
                            <span style={{ color: '#22c55e', fontWeight: 600 }}>●</span>{' '}
                            {leaderboard.find(s => s.session_id === selectedSession)?.cohort_name || selectedSession.slice(0, 12)}
                            {' — R'}
                            {leaderboard.find(s => s.session_id === selectedSession)?.round_number || '?'}
                        </span>
                    ) : (
                        <span style={{ opacity: 0.5, whiteSpace: 'nowrap' }}>No cohort selected — session tools disabled</span>
                    )}
                </span>

                {/* Quick action buttons */}
                <button
                    onClick={() => setActiveTab('manual_override')}
                    disabled={!selectedSession || !canAccessTab('manual_override')}
                    title={!canAccessTab('manual_override') ? 'Not available for your role'
                        : !selectedSession ? 'Select a cohort first — click its row in the Leaderboard'
                        : 'Open Manual Overrides for the selected cohort'}
                    style={{
                        padding: '0.3rem 0.7rem', borderRadius: '6px', fontSize: '0.72rem',
                        fontWeight: 600, border: '1px solid rgba(245,158,11,0.3)',
                        background: 'rgba(245,158,11,0.1)', color: '#f59e0b',
                        cursor: selectedSession && canAccessTab('manual_override') ? 'pointer' : 'not-allowed',
                        opacity: selectedSession && canAccessTab('manual_override') ? 1 : 0.4,
                    }}
                >⚡ Override</button>
                <button
                    onClick={() => setActiveTab('swipe_file')}
                    disabled={!selectedSession}
                    title={!selectedSession ? 'Select a cohort first — click its row in the Leaderboard'
                        : 'Send a message to the selected cohort'}
                    style={{
                        padding: '0.3rem 0.7rem', borderRadius: '6px', fontSize: '0.72rem',
                        fontWeight: 600, border: '1px solid rgba(59,130,246,0.3)',
                        background: 'rgba(59,130,246,0.1)', color: '#60a5fa',
                        cursor: selectedSession ? 'pointer' : 'not-allowed',
                        opacity: selectedSession ? 1 : 0.4,
                    }}
                >📬 Message</button>
                <button
                    onClick={() => setActiveTab('undo_round')}
                    disabled={!selectedSession || !canAccessTab('undo_round')}
                    title={!canAccessTab('undo_round') ? 'Not available for your role'
                        : !selectedSession ? 'Select a cohort first — click its row in the Leaderboard'
                        : 'Roll back a round for the selected cohort'}
                    style={{
                        padding: '0.3rem 0.7rem', borderRadius: '6px', fontSize: '0.72rem',
                        fontWeight: 600, border: '1px solid rgba(107,114,128,0.3)',
                        background: 'rgba(107,114,128,0.1)', color: 'var(--text-muted)',
                        cursor: selectedSession && canAccessTab('undo_round') ? 'pointer' : 'not-allowed',
                        opacity: selectedSession && canAccessTab('undo_round') ? 1 : 0.4,
                    }}
                >↩️ Undo</button>

                {/* Keyboard shortcut hints — F-8 (v3): count matches this role's groups */}
                <span className="fac-bar-hint" style={{ fontSize: '0.68rem', color: 'var(--text-muted)', opacity: 0.5, whiteSpace: 'nowrap' }}>
                    Ctrl+1–{FILTERED_SIDEBAR.length}: toggle groups · Ctrl+Shift+B: broadcast · ?: shortcuts
                </span>
            </div>

            {/* ── Mobile Sidebar Toggle ── */}
            <button
                onClick={() => setSidebarOpen(prev => !prev)}
                style={{
                    display: 'none', position: 'fixed', bottom: '4rem', right: '1rem', zIndex: 1300,
                    width: '48px', height: '48px', borderRadius: '50%',
                    background: 'var(--accent-blue)', color: '#fff', border: 'none',
                    fontSize: '1.3rem', cursor: 'pointer',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
                }}
                className="mobile-sidebar-toggle"
            >
                {sidebarOpen ? '✕' : '☰'}
            </button>

            {/* Mobile responsive CSS */}
            <style>{`
                /* R5 (V2-5): the hint is duplicated in the ? sheet — below
                   1200px its row-space belongs to the actual controls. */
                @media (max-width: 1200px) {
                    .fac-bar-hint { display: none !important; }
                }
                @media (max-width: 768px) {
                    .mobile-sidebar-toggle { display: flex !important; align-items: center; justify-content: center; }
                    .${styles.sidebar} {
                        position: fixed !important;
                        left: ${sidebarOpen ? '0' : '-280px'} !important;
                        top: 0 !important;
                        z-index: 1250 !important;
                        transition: left 0.3s ease !important;
                        box-shadow: ${sidebarOpen ? '4px 0 24px rgba(0,0,0,0.5)' : 'none'} !important;
                    }
                    .${styles.mainPanel} {
                        margin-left: 0 !important;
                        padding-bottom: 4rem !important;
                    }
                }
            `}</style>
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
    // Phase 2 (F10): failures must be visible, not console-only.
    const [statusOk, setStatusOk] = useState(true);
    const flash = (msg, ok = true) => {
        setStatusOk(ok);
        setStatus(msg);
        setTimeout(() => setStatus(null), ok ? 3000 : 6000);
    };

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
                credentials: 'include',
                body: JSON.stringify({ difficulty: level }),
            });
            if (res.ok) {
                setQuizDifficulty(level);
                flash(`✅ Quiz difficulty set to ${level.charAt(0).toUpperCase() + level.slice(1)}`);
            } else {
                flash(`❌ Difficulty NOT saved (HTTP ${res.status}) — still ${quizDifficulty}`, false);
            }
        } catch { flash('❌ Difficulty NOT saved — network error', false); }
    };

    const toggleQuiz = async (sessionId, enabled) => {
        try {
            const res = await fetch(`${API}/api/admin/quiz-enabled/${sessionId}`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ quiz_enabled: enabled }),
            });
            if (res.ok) {
                setQuizEnabledMap(prev => ({ ...prev, [sessionId]: enabled }));
                flash(`✅ Quiz ${enabled ? 'enabled' : 'disabled'} for cohort`);
            } else {
                flash(`❌ Quiz toggle NOT saved (HTTP ${res.status})`, false);
            }
        } catch { flash('❌ Quiz toggle NOT saved — network error', false); }
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
                    background: statusOk ? 'rgba(16,185,129,0.10)' : 'rgba(239,68,68,0.10)',
                    border: `1px solid ${statusOk ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
                    fontSize: '0.8rem', color: statusOk ? '#10b981' : '#ef4444', fontWeight: 600,
                }}>{status}</div>
            )}

            <div style={{
                background: 'rgba(99,102,241,0.08)', borderRadius: 14,
                padding: '16px 20px', border: '1px solid rgba(99,102,241,0.25)',
            }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
                    {/* Difficulty Toggle */}
                    <div>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', marginBottom: 6 }}>
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
                                            : 'rgba(148,163,184,0.15)',
                                        color: quizDifficulty === level ? '#fff' : 'var(--text-muted)',
                                        fontWeight: 600, fontSize: '0.78rem', cursor: 'pointer',
                                        transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                                    }}
                                >
                                    {level === 'easy' ? '🟢' : level === 'medium' ? '🟡' : '🔴'} {level.charAt(0).toUpperCase() + level.slice(1)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Per-Cohort Toggle */}
                    <div>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', marginBottom: 6 }}>
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
                                            border: `1px solid ${enabled ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)'}`,
                                            background: enabled ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.10)',
                                            color: enabled ? '#4ade80' : '#f87171',
                                            fontWeight: 600, fontSize: '0.72rem', cursor: 'pointer',
                                            transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
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
 *  CEO INTERVIEW CONTROL PANEL — Per-Cohort Enable/Disable + Voice
 * ═════════════════════════════════════════════════════════════════ */

function InterviewControlPanel({ sessions = [] }) {
    const [interviewMap, setInterviewMap] = useState({});
    const [status, setStatus] = useState(null);
    // Phase 2 (F10): failures must be visible, not console-only.
    const [statusOk, setStatusOk] = useState(true);
    const flash = (msg, ok = true) => {
        setStatusOk(ok);
        setStatus(msg);
        setTimeout(() => setStatus(null), ok ? 3000 : 6000);
    };

    // F7: seed from the per-cohort values the leaderboard already carries.
    // The old code fetched GLOBAL settings and painted the same value onto
    // every row — silently misrepresenting cohorts configured differently.
    // (Per-session PUTs were already correct; only the read lied.)
    useEffect(() => {
        const map = {};
        sessions.forEach(s => {
            map[s.session_id] = {
                enabled: s.ceo_interview_enabled || false,
                voice_gender: s.ceo_interview_voice_gender || 'female',
            };
        });
        setInterviewMap(map);
    }, [sessions]);

    const toggleInterview = async (sessionId, enabled) => {
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/ceo-interview`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ ceo_interview_enabled: enabled }),
            });
            if (res.ok) {
                setInterviewMap(prev => ({ ...prev, [sessionId]: { ...prev[sessionId], enabled } }));
                flash(`✅ Interview ${enabled ? 'enabled' : 'disabled'}`);
            } else {
                flash(`❌ Interview toggle NOT saved (HTTP ${res.status})`, false);
            }
        } catch { flash('❌ Interview toggle NOT saved — network error', false); }
    };

    const switchVoice = async (sessionId, gender) => {
        try {
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/ceo-interview`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ ceo_interview_voice_gender: gender }),
            });
            if (res.ok) {
                setInterviewMap(prev => ({ ...prev, [sessionId]: { ...prev[sessionId], voice_gender: gender } }));
                flash(`✅ Voice → ${gender === 'female' ? 'Victoria' : 'Alexander'}`);
            } else {
                flash(`❌ Voice NOT changed (HTTP ${res.status})`, false);
            }
        } catch { flash('❌ Voice NOT changed — network error', false); }
    };

    return (
        <section style={{
            background: 'var(--bg-card, #fff)', border: '1px solid var(--border-subtle, #e2e8f0)',
            borderRadius: 'var(--radius-lg, 16px)', padding: '1.5rem 2rem',
            boxShadow: '0 4px 20px rgba(0,0,0,0.06)',
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
                <span style={{ fontSize: '1.5rem' }}>🎤</span>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                        CEO Interview
                    </h2>
                    <p style={{ margin: '0.15rem 0 0', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        Enable/disable post-game CEO interview per cohort. Select Victoria (female) or Alexander (male) Muressons.
                    </p>
                </div>
            </div>
            {status && (
                <div style={{
                    padding: '8px 14px', borderRadius: 10, marginBottom: 12,
                    background: statusOk ? 'rgba(16,185,129,0.10)' : 'rgba(239,68,68,0.10)',
                    border: `1px solid ${statusOk ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
                    fontSize: '0.8rem', color: statusOk ? '#10b981' : '#ef4444', fontWeight: 600,
                }}>{status}</div>
            )}
            <div style={{
                background: 'rgba(245,158,11,0.08)', borderRadius: 14,
                padding: '16px 20px', border: '1px solid rgba(245,158,11,0.3)',
            }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', marginBottom: 8 }}>
                    🎙️ Per-Cohort Configuration
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {sessions.length === 0 ? (
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>No active cohorts</span>
                    ) : sessions.map(s => {
                        const cfg = interviewMap[s.session_id] || { enabled: false, voice_gender: 'female' };
                        return (
                            <div key={s.session_id} style={{
                                display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
                                padding: '6px 10px', background: 'rgba(255,255,255,0.04)',
                                borderRadius: 8, border: '1px solid rgba(251,191,36,0.2)',
                            }}>
                                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-primary)', minWidth: 100 }}>
                                    {s.cohort_name}
                                </span>
                                <button
                                    onClick={() => toggleInterview(s.session_id, !cfg.enabled)}
                                    style={{
                                        padding: '4px 12px', borderRadius: 6, border: 'none',
                                        background: cfg.enabled ? '#10b981' : 'rgba(148,163,184,0.15)',
                                        color: cfg.enabled ? '#fff' : 'var(--text-muted)',
                                        fontWeight: 700, fontSize: '0.68rem', cursor: 'pointer',
                                    }}
                                >
                                    {cfg.enabled ? '● ON' : '○ OFF'}
                                </button>
                                {cfg.enabled && (
                                    <button
                                        onClick={() => switchVoice(s.session_id, cfg.voice_gender === 'female' ? 'male' : 'female')}
                                        style={{
                                            padding: '4px 10px', borderRadius: 6, border: '1px solid rgba(99,102,241,0.35)',
                                            background: 'rgba(99,102,241,0.10)',
                                            color: '#818cf8', fontWeight: 700, fontSize: '0.65rem', cursor: 'pointer',
                                        }}
                                    >
                                        {cfg.voice_gender === 'female' ? '👩‍💼 Victoria' : '👨‍💼 Alexander'}
                                    </button>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}


/* ═════════════════════════════════════════════════════════════════
 *  CHANGE PASSWORD MODAL
 * ═════════════════════════════════════════════════════════════════ */

function FacilitatorChangePasswordModal({ facilitatorId, onClose, forced = false, onSuccess = null }) {
    const [oldPw, setOldPw] = useState('');
    const [newPw, setNewPw] = useState('');
    const [confirmPw, setConfirmPw] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (newPw.length < 8) { setError('New password must be at least 8 characters.'); return; }
        if (newPw !== confirmPw) { setError('Passwords do not match.'); return; }
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/facilitators/change-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
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
            if (onSuccess) setTimeout(onSuccess, 1400); // let the confirmation register, then release the gate
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
                        {forced ? '🔐 Set Your Password' : '🔑 Change Password'}
                    </h2>
                    {!forced && (
                        <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: 'var(--text-muted, #94a3b8)' }}>×</button>
                    )}
                </div>
                {forced && !success && (
                    <p style={{ margin: '-0.75rem 0 1rem', fontSize: '0.78rem', color: 'var(--text-muted, #64748b)', lineHeight: 1.5 }}>
                        You signed in with the default password. Choose a personal password to continue — your current password is the one you just used.
                    </p>
                )}

                {success ? (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>✅</div>
                        <h3 style={{ color: 'var(--text-primary, #1e293b)', margin: '0 0 0.5rem' }}>Password Updated</h3>
                        <p style={{ color: 'var(--text-muted, #64748b)', fontSize: '0.85rem' }}>
                            Your password has been changed successfully.
                        </p>
                        <button onClick={forced ? (onSuccess || onClose) : onClose} style={{
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
                            <PasswordInput value={oldPw} onChange={e => setOldPw(e.target.value)} placeholder="Enter current password" required style={inputStyle} />
                        </div>
                        <div>
                            <label style={labelStyle}>New Password</label>
                            <PasswordInput value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="At least 8 characters" required style={inputStyle} />
                        </div>
                        <div>
                            <label style={labelStyle}>Confirm New Password</label>
                            <PasswordInput value={confirmPw} onChange={e => setConfirmPw(e.target.value)} placeholder="Re-enter new password" required style={inputStyle} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                            {!forced && (
                                <button type="button" onClick={onClose} style={{
                                    background: 'transparent', border: '1px solid var(--border-subtle, #cbd5e1)',
                                    color: 'var(--text-secondary, #475569)', padding: '0.5rem 1rem', borderRadius: '6px',
                                    fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer',
                                }}>Cancel</button>
                            )}
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

function FacilitatorSessionManager({ leaderboard, authData, handleResetSession, styles, onRefresh, confirmAction, isSuperAdmin = false }) {
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [loading, setLoading] = useState(false);
    const [resultMsg, setResultMsg] = useState('');

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
        // F4: impact preview + typed phrase for the irreversible variant —
        // and no window.location.reload(), which used to dump the facilitator
        // back to Dashboard Home mid-session and wipe the live feed.
        const names = sessionsList
            .filter(s => selectedIds.has(s.session_id))
            .map(s => s.cohort_name || s.session_id.slice(0, 8));
        const ok = await confirmAction?.({
            title: hardDelete ? `🧨 Hard delete ${selectedIds.size} team(s)` : `🗑️ Soft delete ${selectedIds.size} team(s)`,
            message: hardDelete
                ? 'Completely wipes these teams immediately, bypassing the 7-day retention window.'
                : 'Data stays recoverable for 7 days.',
            impact: `Affected: ${names.join(', ')}`,
            requirePhrase: hardDelete ? 'DELETE' : null,
            confirmLabel: hardDelete ? 'Hard delete now' : 'Soft delete',
        });
        if (!ok) return;

        setLoading(true);
        setResultMsg('');
        try {
            // Same endpoints, same order — only the gate in front changed.
            for (let sid of selectedIds) {
                const endpoint = hardDelete 
                    ? `${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/sessions/${sid}?hard=true` 
                    : `${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/sessions/${sid}`;
                    
                await fetch(endpoint, { method: 'DELETE', credentials: 'include' });
            }
            setResultMsg(`✅ ${selectedIds.size} team(s) deleted.`);
            setSelectedIds(new Set());
            onRefresh?.();
        } catch (e) {
            setResultMsg('❌ Failed to delete sessions: ' + e.message);
        } finally {
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

            {resultMsg && (
                <div style={{
                    padding: '8px 12px', borderRadius: '6px', fontSize: '0.82rem', fontWeight: 600,
                    color: resultMsg.startsWith('✅') ? '#10b981' : '#ef4444',
                    background: resultMsg.startsWith('✅') ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                }}>{resultMsg}</div>
            )}

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexDirection: 'column', alignItems: 'flex-start' }}>
                <button 
                    className={styles.resetSessionBtn} 
                    onClick={() => handleDeleteMultiple(false)}
                    disabled={selectedIds.size === 0 || loading}
                    style={{ opacity: selectedIds.size === 0 || loading ? 0.6 : 1 }}
                >
                    {loading ? 'Processing...' : `🗑️ Soft Delete ${selectedIds.size} Selected Team(s)`}
                </button>
                {isSuperAdmin && (
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
