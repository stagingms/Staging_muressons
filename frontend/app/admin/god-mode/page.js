'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import styles from '../page.module.css';
import { isAdminRole } from '../../utils/roleRouting';

import MaterialityConfig from '../../components/MaterialityConfig';
import MasterInterventions from '../../components/MasterInterventions';
import ResourceManager from '../../components/ResourceManager';

import FacilitatorManager from '../../components/FacilitatorManager';
import PasswordInput from '../../components/PasswordInput';
import CrisisTriggerConfig from '../../components/CrisisTriggerConfig';

import GodModeStatus from '../../components/GodModeStatus';
import GodModeAuditLog from '../../components/GodModeAuditLog';
import UniversalBroadcast from '../../components/UniversalBroadcast';
import SystemExport from '../../components/SystemExport';
import PlatformAnalytics from '../../components/PlatformAnalytics';
import TechnicalGlossary from '../../components/TechnicalGlossary';
import BalancedScorecardEvaluator from '../../components/BalancedScorecardEvaluator';
import ArchetypeEditor from '../../components/ArchetypeEditor';
import MasterVariableEditor from '../../components/MasterVariableEditor';
import SimulationManager from '../../components/SimulationManager';
import EconomicEngineTunables from '../../components/EconomicEngineTunables';
import SystemicRiskControls from '../../components/SystemicRiskControls';
import SessionHealthDashboard from '../../components/SessionHealthDashboard';
import ComplexityEventFeed from '../../components/ComplexityEventFeed';
import DecisionTimeline from '../../components/DecisionTimeline';
import DNAComparison from '../../components/DNAComparison';
import DebriefReport from '../../components/DebriefReport';
import SimulationReference from '../../components/SimulationReference';
import RegulatorySandboxControl from '../../components/RegulatorySandboxControl';
import SimulationSwitchboard from '../../components/SimulationSwitchboard';
import { GOD_MODE_SIDEBAR, getTabMeta as _getTabMeta } from '../../config/sidebarConfig';
import { adminJson } from '../../utils/adminFetch';
import CohortSelector from '../../components/CohortSelector';
import { useConfirm } from '../../components/ConfirmModal';
import ShortcutSheet from '../../components/ShortcutSheet';
import RoundPacingControl from '../../components/RoundPacingControl';
import OnboardingWizard from '../../components/OnboardingWizard';
import StakeholderConfig from '../../components/StakeholderConfig';
import PillarConfigurator from '../../components/PillarConfigurator';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// Phase R1 (V2-8): single source for the shortcut sheet — if a binding in the
// keydown handler changes, change it HERE too (same file, one constant).
const GOD_SHORTCUTS = [
    ['Ctrl+1…5', 'Toggle sidebar group open/closed'],
    ['Ctrl+Shift+B', 'Open Session Controls (broadcast)'],
    ['?', 'Show / hide this sheet'],
    ['Esc', 'Close dialogs'],
];


/* ═════════════════════════════════════════════════════════════════
 *  CHANGE PASSWORD MODAL
 * ═════════════════════════════════════════════════════════════════ */

/* ═════════════════════════════════════════════════════════════════
 *  MASTER PASSWORD MODAL — rotates the break-glass credential
 * ═════════════════════════════════════════════════════════════════ */

function MasterPasswordModal({ onClose }) {
    const [currentPw, setCurrentPw] = useState('');
    const [newPw, setNewPw] = useState('');
    const [confirmPw, setConfirmPw] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    // G-5 (v3): caps-lock detection local to this modal (PasswordInput is
    // shared with player-facing surfaces and stays untouched).
    const [capsOn, setCapsOn] = useState(false);
    const trackCaps = (e) => {
        if (typeof e.getModifierState === 'function') setCapsOn(e.getModifierState('CapsLock'));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (newPw.length < 8) { setError('New master password must be at least 8 characters.'); return; }
        if (newPw !== confirmPw) { setError('Passwords do not match.'); return; }
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/master-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(typeof data.detail === 'string' ? data.detail : 'Failed to change the master password.');
            }
            setSuccess(true);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const inputStyle = {
        width: '100%', padding: '0.7rem 1rem', borderRadius: 'var(--radius-md, 6px)',
        border: '1px solid var(--border-subtle, #cbd5e1)', background: 'var(--bg-body, #f1f5f9)',
        color: 'var(--text-primary, #1e293b)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
    };
    const labelStyle = {
        display: 'block', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
        letterSpacing: '0.1em', color: 'var(--text-muted, #64748b)', marginBottom: '0.4rem',
    };

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000,
            background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            <div style={{
                background: 'var(--bg-card, #fff)', border: '1px solid rgba(239,68,68,0.35)',
                borderRadius: 'var(--radius-lg, 12px)', padding: '2rem', maxWidth: '420px', width: '90%',
                boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                    <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary, #1e293b)' }}>
                        🗝️ Change Master Password
                    </h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.3rem', cursor: 'pointer', color: 'var(--text-muted, #94a3b8)' }}>×</button>
                </div>
                <p style={{ margin: '0 0 1.25rem', fontSize: '0.75rem', color: 'var(--text-muted, #64748b)', lineHeight: 1.55 }}>
                    The break-glass credential: it signs in <strong>god_mode</strong> and bypass-logs into any
                    facilitator account. Changes take effect immediately, survive restarts, and supersede
                    the <code>.env</code> value. Rotating it does <strong>not</strong> sign anyone out —
                    dashboards already signed in stay signed in; the new password applies to future
                    master-bypass logins only.
                </p>

                {success ? (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>✅</div>
                        <h3 style={{ color: 'var(--text-primary, #1e293b)', margin: '0 0 0.5rem' }}>Master Password Rotated</h3>
                        <p style={{ color: 'var(--text-muted, #64748b)', fontSize: '0.85rem' }}>
                            The new master password is live on every master-bypass surface. Store it securely — it is not shown again.
                            Existing signed-in dashboards are unaffected; only future master-bypass logins use the new value.
                        </p>
                        <button onClick={onClose} style={{
                            marginTop: '1rem', background: 'linear-gradient(135deg, #ef4444, #f59e0b)', color: '#fff',
                            border: 'none', padding: '0.6rem 1.5rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer',
                        }}>Done</button>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} onKeyDown={trackCaps} onKeyUp={trackCaps}
                        style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {capsOn && (
                            <div style={{
                                background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)',
                                color: '#f59e0b', padding: '0.45rem 0.6rem', borderRadius: '6px', fontSize: '0.78rem',
                            }}>⇪ Caps Lock is on</div>
                        )}
                        {error && (
                            <div style={{
                                background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                                color: '#ef4444', padding: '0.6rem', borderRadius: '6px', fontSize: '0.85rem',
                            }}>{error}</div>
                        )}
                        <div>
                            <label style={labelStyle}>Current Master Password</label>
                            <PasswordInput value={currentPw} onChange={e => setCurrentPw(e.target.value)} placeholder="Confirm the current master password" required style={inputStyle} />
                        </div>
                        <div>
                            <label style={labelStyle}>New Master Password</label>
                            <PasswordInput value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="At least 8 characters" required style={inputStyle} />
                        </div>
                        <div>
                            <label style={labelStyle}>Confirm New Master Password</label>
                            <PasswordInput value={confirmPw} onChange={e => setConfirmPw(e.target.value)} placeholder="Re-enter new master password" required style={inputStyle} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                            <button type="button" onClick={onClose} style={{
                                background: 'transparent', border: '1px solid var(--border-subtle, #cbd5e1)',
                                color: 'var(--text-secondary, #475569)', padding: '0.5rem 1rem', borderRadius: '6px',
                                fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer',
                            }}>Cancel</button>
                            <button type="submit" disabled={loading} style={{
                                background: 'linear-gradient(135deg, #ef4444, #f59e0b)', color: '#fff', border: 'none',
                                padding: '0.5rem 1.25rem', borderRadius: '6px', fontSize: '0.85rem',
                                fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1,
                            }}>{loading ? '⏳ Rotating…' : 'Rotate Master Password'}</button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}

function GodModeChangePasswordModal({ facilitatorId, onClose }) {
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
                credentials: 'include',  // O4: send JWT cookie for god-mode auth
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
        width: '100%', padding: '0.7rem 1rem', borderRadius: 'var(--radius-md, 6px)',
        border: '1px solid var(--border-subtle, #cbd5e1)', background: 'var(--bg-body, #f1f5f9)',
        color: 'var(--text-primary, #1e293b)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
    };

    const labelStyle = {
        display: 'block', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
        letterSpacing: '0.1em', color: 'var(--text-muted, #64748b)', marginBottom: '0.4rem',
    };

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000,
            background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            <div style={{
                background: 'var(--bg-card, #fff)', border: '1px solid var(--border-subtle, #e2e8f0)',
                borderRadius: 'var(--radius-lg, 12px)', padding: '2rem', maxWidth: '400px', width: '90%',
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
                        <p style={{ color: 'var(--text-muted, #64748b)', fontSize: '0.85rem' }}>Your password has been changed successfully.</p>
                        <button onClick={onClose} style={{
                            marginTop: '1rem', background: 'linear-gradient(135deg, #f59e0b, #ef4444)', color: '#fff',
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
                            <button type="button" onClick={onClose} style={{
                                background: 'transparent', border: '1px solid var(--border-subtle, #cbd5e1)',
                                color: 'var(--text-secondary, #475569)', padding: '0.5rem 1rem', borderRadius: '6px',
                                fontSize: '0.85rem', fontWeight: 500, cursor: 'pointer',
                            }}>Cancel</button>
                            <button type="submit" disabled={loading} style={{
                                background: 'linear-gradient(135deg, #f59e0b, #ef4444)', color: '#fff', border: 'none',
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
 *  MAIN GOD MODE PAGE (wrapped with login gate)
 * ═════════════════════════════════════════════════════════════════ */

export default function GodModePage() {
    const router = useRouter();
    const [authData, setAuthData] = useState(null);
    const [checked, setChecked] = useState(false);
    const [sessionExpired, setSessionExpired] = useState(false);

    useEffect(() => {
        try {
            const stored = localStorage.getItem('godmode_auth');
            if (stored) setAuthData(JSON.parse(stored));
        } catch { /* ignore */ }
        setChecked(true);
    }, []);

    // Phase L: this console has ONE neutral entry point (/admin). Direct
    // navigation here no longer shows a "God Mode Access" login (which named a
    // privileged portal to any visitor). Unauthenticated → the single sign-in;
    // authenticated-but-not-admin (e.g. a facilitator's stale bookmark) → their
    // own dashboard, never stranded on a god-mode error. The server guards were
    // already rejecting their god-mode API calls; this is graceful UX on top.
    const isAdmin = authData ? isAdminRole(authData.role, authData.is_admin) : false;
    useEffect(() => {
        if (!checked) return;
        if (!authData) { router.replace(sessionExpired ? '/admin?expired=1' : '/admin'); return; }
        if (!isAdmin) router.replace('/admin/facilitator');
    }, [checked, authData, isAdmin, sessionExpired, router]);

    const handleLogout = async () => {
        // C-2: Call the server-side logout endpoint so the HttpOnly JWT cookie
        // is properly cleared by the server.  We clear localStorage regardless
        // of whether the server call succeeds (network failure must not trap
        // the user in an authenticated state).
        // M5: Also clear facilitator_auth — a super_admin may be simultaneously
        // logged in on the facilitator dashboard; logout here clears both.
        try {
            await fetch(`${API}/api/admin/auth/logout`, {
                method: 'POST',
                credentials: 'include',
            });
        } catch { /* ignore — clear local state regardless */ }
        localStorage.removeItem('godmode_auth');
        localStorage.removeItem('facilitator_auth');
        setAuthData(null);
        setSessionExpired(false);
    };

    const handleSessionExpired = () => {
        localStorage.removeItem('godmode_auth');
        localStorage.removeItem('facilitator_auth');
        setAuthData(null);
        setSessionExpired(true);
    };

    if (!checked) return null;
    // Phase L: while redirecting (unauth → /admin, or non-admin → their own
    // dashboard) render nothing — /admin is the only login surface.
    if (!authData || !isAdmin) return null;

    return <GodModeDashboard authData={authData} onLogout={handleLogout} onSessionExpired={handleSessionExpired} />;
}


/* ═════════════════════════════════════════════════════════════════
 *  GOD MODE DASHBOARD (protected behind login gate)
 * ═════════════════════════════════════════════════════════════════ */


/* ═════════════════════════════════════════════════════════════════
 *  SYSTEM STATUS — single shared poller (G4)
 *  One 10s poll on /god/system-status feeds both the context bar and the
 *  System Overview cards, so the two surfaces can never disagree. Replaces
 *  the previous duplicated pollers (bar @15s + GodModeStatus @10s).
 * ═════════════════════════════════════════════════════════════════ */
function useGodSystemStatus(intervalMs = 10000) {
    const [status, setStatus] = useState(null);
    const [lastSuccess, setLastSuccess] = useState(null);
    const [failedAttempts, setFailedAttempts] = useState(0);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        // Bound the request so a hung backend can't leave stale connections.
        const ctrl = new AbortController();
        const timer = setTimeout(() => ctrl.abort(), 8000);
        try {
            const res = await fetch(`${API}/api/admin/god/system-status`, {
                signal: ctrl.signal,
                credentials: 'include',
            });
            if (res.ok) {
                setStatus(await res.json());
                setLastSuccess(Date.now());
                setFailedAttempts(0);
            } else {
                setFailedAttempts(n => n + 1);
            }
        } catch {
            setFailedAttempts(n => n + 1);
        } finally {
            clearTimeout(timer);
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
        const t = setInterval(load, intervalMs);
        return () => clearInterval(t);
    }, [load, intervalMs]);

    return { status, lastSuccess, failedAttempts, loading, refresh: load };
}

/* ═════════════════════════════════════════════════════════════════
 *  SYSTEM CONTEXT BAR
 *  G1: tri-state (Live / Stale / Unreachable). Never fabricates zeros or
 *  an "Optimal" verdict when the backend can't be reached — during an
 *  outage the bar must alarm, not reassure.
 * ═════════════════════════════════════════════════════════════════ */
function SystemContextBar({ status, lastSuccess, failedAttempts }) {
    // Polling is every 10s; two consecutive failures ≈ >20s without truth.
    const unreachable = !status && failedAttempts > 0;
    const stale = !!status && failedAttempts >= 2;
    const live = !!status && failedAttempts < 2;

    const asOf = lastSuccess ? new Date(lastSuccess).toLocaleTimeString() : null;
    const isOptimal = live && (status.system_memory_mb || 0) < 500;
    const frozen = !!status?.system_frozen;

    const healthChip = live
        ? { icon: isOptimal ? '🟢' : '🔴', label: isOptimal ? 'Optimal' : 'Warning', color: isOptimal ? '#10b981' : '#ef4444' }
        : stale
            ? { icon: '🟡', label: `Stale — as of ${asOf}`, color: '#f59e0b' }
            : { icon: '⛔', label: 'Backend unreachable', color: '#ef4444' };

    const countVal = (v) => (status ? v : '—');

    return (
        <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'var(--bg-elevated)', borderBottom: '1px solid var(--border-subtle)',
            padding: '8px 24px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)',
            position: 'sticky', top: 0, zIndex: 10
        }}>
            <style dangerouslySetInnerHTML={{ __html: `
                @keyframes heartbeatPulse {
                    0% { transform: scale(1); opacity: 1; }
                    15% { transform: scale(1.15); opacity: 0.8; }
                    30% { transform: scale(1); opacity: 1; }
                    45% { transform: scale(1.15); opacity: 0.8; }
                    60% { transform: scale(1); opacity: 1; }
                }
            `}} />
            <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', opacity: live ? 1 : 0.65 }}>
                <span style={{ color: '#38bdf8' }}>📡 COMMAND UPLINK</span>
                <span>Live Cohorts: <span style={{ color: 'var(--text-primary)' }}>{countVal(status?.total_cohorts)}</span></span>
                <span>Active Players: <span style={{ color: 'var(--text-primary)' }}>{countVal(status?.total_players)}</span></span>
                {stale && <span style={{ color: '#f59e0b' }}>as of {asOf}</span>}
                {frozen && (
                    <span style={{
                        color: '#ef4444', fontWeight: 800, padding: '2px 8px', borderRadius: '12px',
                        background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)',
                    }}>
                        ❄️ SYSTEM FROZEN
                    </span>
                )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                System Health:
                <span style={{
                    color: healthChip.color,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: `${healthChip.color}1a`,
                }}>
                    <span style={{
                        display: 'inline-block',
                        // Heartbeat only when data is actually live — the animation
                        // must not imply liveness during an outage.
                        animation: live ? 'heartbeatPulse 2.5s infinite' : 'none',
                    }}>
                        {healthChip.icon}
                    </span>
                    {healthChip.label}
                </span>
            </div>
        </div>
    );
}

function GodModeDashboard({ authData, onLogout, onSessionExpired }) {
    const [activeTab, setActiveTab] = useState('system_overview');
    const [showChangePw, setShowChangePw] = useState(false);
    const [showMasterPw, setShowMasterPw] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [openCategories, setOpenCategories] = useState({
        command_center: true,
        orchestration: true,
        engine_core: false,
        content: false,
        danger: false,
    });
    // Global leaderboard — used by DecisionTimeline, DebriefReport, SimulationManager
    const [leaderboard, setLeaderboard] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);

    // G4: single system-status poller shared by the context bar and the
    // System Overview cards (previously two independent pollers).
    const sysStatus = useGodSystemStatus();

    useEffect(() => {
        const fetchLb = () => fetch(`${API}/api/admin/leaderboard`, {
            // M2: use JWT cookie (credentials:'include') instead of the
            // deprecated x-facilitator-id header for god-mode data fetches.
            credentials: 'include',
        })
            .then(r => r.ok ? r.json() : null)
            .then(d => d?.leaderboard && setLeaderboard(d.leaderboard))
            .catch(() => {});
        fetchLb();
        const t = setInterval(fetchLb, 30000);
        return () => clearInterval(t);
    }, [authData]);

    // Auto-refresh JWT cookie so a long session doesn't expire mid-workshop.
    // Calls /auth/refresh immediately on mount then every 30 minutes.
    // The backend will re-issue a fresh cookie (8h expiry) while the current one is still valid.
    useEffect(() => {
        const refresh = () => fetch(`${API}/api/admin/auth/refresh`, {
            method: 'POST',
            credentials: 'include',
        }).then(r => {
            // If refresh itself returns 401 the cookie has fully expired — trigger re-login
            if (r.status === 401 && onSessionExpired) onSessionExpired();
        }).catch(() => {});
        refresh(); // refresh on mount in case token is already close to expiry
        const t = setInterval(refresh, 30 * 60 * 1000); // refresh every 30 min
        // Also refresh on window focus (catches overnight/long-idle scenarios)
        const onFocus = () => refresh();
        window.addEventListener('focus', onFocus);
        return () => { clearInterval(t); window.removeEventListener('focus', onFocus); };
    }, [onSessionExpired]);

    const toggleCategory = (catId) => {
        setOpenCategories(prev => ({ ...prev, [catId]: !prev[catId] }));
    };

    // Keyboard shortcuts — Phase 6 (F12): identical semantics to the
    // facilitator dashboard. Ctrl+1–5 toggles a group without collapsing the
    // rest; broadcast lives on Ctrl+Shift+B on both screens; '?' opens the
    // shortcut sheet.
    const [showShortcuts, setShowShortcuts] = useState(false);
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
                const categoryKeys = ['command_center', 'orchestration', 'engine_core', 'content', 'danger'];
                if (e.key >= '1' && e.key <= '5') {
                    e.preventDefault();
                    const idx = parseInt(e.key) - 1;
                    if (categoryKeys[idx]) {
                        setOpenCategories(prev => ({ ...prev, [categoryKeys[idx]]: !prev[categoryKeys[idx]] }));
                    }
                }
                if (e.shiftKey && (e.key === 'b' || e.key === 'B')) {
                    e.preventDefault();
                    setActiveTab('session_controls');
                }
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, []);

    const SIDEBAR_CONFIG = GOD_MODE_SIDEBAR;
    const getTabMeta = (tabId) => _getTabMeta(SIDEBAR_CONFIG, tabId);


        const renderActiveComponent = () => {
        switch (activeTab) {
            case 'system_overview':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <GodModeStatus
                            facilitatorId={authData?.facilitator_id}
                            status={sysStatus.status}
                            loading={sysStatus.loading}
                            onRefresh={sysStatus.refresh}
                            lastSuccess={sysStatus.lastSuccess}
                        />
                        <SessionHealthDashboard />
                    </div>
                );
            // O2: renamed from 'activity_log' — see sidebarConfig.js for explanation
            case 'god_activity_log':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <GodModeAuditLog />
                        <ComplexityEventFeed sessionId={null} />
                    </div>
                );
            case 'platform_analytics':
                // O3: pass leaderboard and navigation handlers so god-mode has
                // the same prop contract as the facilitator dashboard.
                return <PlatformAnalytics leaderboard={leaderboard} onNavigate={setActiveTab} onSelectSession={setSelectedSession} />;
                
            case 'facilitator_registry':
                return <FacilitatorManager onNavigate={(tab) => setActiveTab(tab)} authContext={authData} />;
            case 'cohort_provisioning':
                return <SimulationManager fetchInternal={false} leaderboard={leaderboard} currentFacilitatorId={authData.facilitator_id} currentFacilitatorRole={authData.role} />;
            // G7: removed dead 'cohort_orchestration' case — no sidebar item has
            // that id, so it was unreachable code that invited config drift.
            case 'session_controls':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <UniversalBroadcast />
                        {/* Phase 6: pacing control added here — self-fetching in
                            god-mode, following the global target-cohort selection. */}
                        <RoundPacingControl selectedSession={selectedSession} />
                    </div>
                );
            case 'master_interventions':
                return <MasterInterventions />;
            case 'crisis_overrides':
                // Custom Black Swan Injector moved to the facilitator dashboard
                // (tab: custom_black_swan) — admins see it there with all
                // cohorts; facilitators only see cohorts unlocked per-cohort
                // via custom_black_swan_enabled.
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <CrisisTriggerConfig />
                    </div>
                );
                
            case 'macro_economics':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <EconomicEngineTunables />
                        <MasterVariableEditor />
                    </div>
                );
            case 'sim_switchboard':
                return (
                    <div style={{ padding: '1.5rem' }}>
                        <div style={{ marginBottom: '1rem' }}>
                            <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                                🛤️ Simulation Switchboard
                            </h2>
                            <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                Toggle the Advanced Climate Engine and set global climate parameters.
                                Enable Side Track Simulations platform-wide — lead facilitators may always assign any registered track to their cohorts.
                            </p>
                        </div>
                        <SimulationSwitchboard />
                    </div>
                );
            case 'materiality_config':
                return <MaterialityConfig sessionId={selectedSession} isFacilitator={false} />;
            case 'systemic_risk_controls':
                return <SystemicRiskControls />;
            case 'archetype_editor':
                return <ArchetypeEditor />;
            case 'scorecard_evaluator':
                return <div style={{padding:'1.5rem'}}><BalancedScorecardEvaluator /></div>;
            // esg_weights: moved to the Facilitator dashboard (Analytics &
            // Assessment) for all facilitators; no longer a God Mode tab.
            case 'regulatory_sandbox': {
                const sandboxSessions = leaderboard.filter(s => !s.player_id);
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div style={{ padding: '0.75rem 1.5rem', background: 'var(--bg-card)', borderRadius: '10px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <CohortSelector leaderboard={leaderboard} selectedSession={selectedSession} onSelect={setSelectedSession} label="⚖️ Target Cohort:" />
                            {sandboxSessions.length === 0 && (
                                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>No cohorts yet — provision one first.</span>
                            )}
                        </div>
                        <RegulatorySandboxControl sessionId={selectedSession} isGodMode={true} />
                    </div>
                );
            }
                
            case 'resources':
                return <ResourceManager />;
            // G-4 (v3): dead case 'glossary_editor' removed — no sidebar item has
            // that id (same class as v1 G7's 'cohort_orchestration'). Glossary
            // editing stays reachable: ResourceManager renders GlossaryManager
            // in its own "📖 Glossary" tab.
            case 'doc_reference':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <div style={{ padding: '1.5rem', background: 'var(--bg-card)', borderRadius: '12px' }}><TechnicalGlossary /></div>
                        <SimulationReference />
                    </div>
                );
                
            case 'system_export':
                return <SystemExport />;
            case 'session_reset':
                return <DangerZonePanel apiBase={API} />;
                
            case 'decision_timeline':
                return <DecisionTimeline sessionId={selectedSession} leaderboard={leaderboard} />;
            case 'dna_comparison':
                return <DNAComparison sessionId={selectedSession} leaderboard={leaderboard} />;
            case 'debrief_view': {
                const cohortSessions = leaderboard.filter(s => !s.player_id);
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div style={{ padding: '0.75rem 1.5rem', background: 'var(--bg-card)', borderRadius: '10px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <CohortSelector leaderboard={leaderboard} selectedSession={selectedSession} onSelect={setSelectedSession} label="📋 Select Cohort:" />
                            {cohortSessions.length === 0 && (
                                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>No cohorts yet — provision one first.</span>
                            )}
                        </div>
                        <DebriefReport sessionId={selectedSession} />
                    </div>
                );
            }

            case 'stakeholder_config':
                return <StakeholderConfig />;

            case 'pillar_config':
                return <PillarConfigurator />;

            default:
                return (
                    <div className={styles.placeholder}>
                        <h2>Select a tool from the sidebar</h2>
                    </div>
                );
        }
    };

    return (
        <div className={styles.dashboard}>
            {/* Phase 6 (F12): shortcut sheet ('?') */}
            {showShortcuts && (
                <ShortcutSheet
                    onClose={() => setShowShortcuts(false)}
                    shortcuts={GOD_SHORTCUTS}
                />
            )}

            {/* ── Master Password Modal (break-glass credential) ── */}
            {showMasterPw && (
                <MasterPasswordModal onClose={() => setShowMasterPw(false)} />
            )}

            {/* ── Change Password Modal ── */}
            {showChangePw && (
                <GodModeChangePasswordModal
                    facilitatorId={authData.facilitator_id}
                    onClose={() => setShowChangePw(false)}
                />
            )}

            {/* ── Onboarding Wizard (first-time only) ── */}
            {/* Deferred while the password modal is up — its full-screen
                backdrop is a z-index peer and would paint over the tour's
                spotlight cutout. See OnboardingWizard header. */}
            <OnboardingWizard
                mode="god_mode"
                userId={authData.facilitator_id}
                onStepChange={(tab) => setActiveTab(tab)}
                deferred={showChangePw}
            />

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
                    <h1>👑 God Mode</h1>
                    <div className={styles.godBadge}>Global Corporation</div>
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
                                        border: '1px solid rgba(245, 158, 11, 0.3)',
                                        color: '#f59e0b',
                                        fontSize: '0.65rem',
                                        fontWeight: 700,
                                        padding: '3px 8px',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                                    }}
                                    title="Change your own password"
                                >
                                    🔑 Password
                                </button>
                                {/* G-1 (v3): the 🗝️ master-key button no longer sits
                                    one icon away from the routine password button —
                                    the break-glass entry moved to the red "Break-Glass"
                                    item at the foot of the sidebar. */}
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
                    {SIDEBAR_CONFIG.map((group) => (
                        <div key={group.id} className={styles.navCategory} data-tour={`nav-${group.id}`}>
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
                                        data-tooltip-pos="right"
                                    >
                                        {item.icon && <span style={{ width: '18px', textAlign: 'center', flexShrink: 0, fontSize: '0.85rem' }}>{item.icon}</span>}
                                        <span>{item.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ))}

                    {/* Owner request (2026-07-12): the "Live Consoles" links
                        (Trading Floor / Shockwave / Region War-Map) were removed
                        from the God Mode sidebar. The consoles still exist at
                        their own routes and remain reachable from the Facilitator
                        screen; god_mode still passes their server-side gates. */}

                    {/* G-1 (v3): break-glass credential rotation lives here —
                        physically apart from the routine header password button,
                        with Danger-Zone-red framing. Opens the same modal. */}
                    <div style={{ margin: '14px 8px 4px', fontSize: '0.62rem', fontWeight: 800, letterSpacing: '0.12em', color: 'var(--text-muted, #64748b)', textTransform: 'uppercase' }}>
                        Break-Glass
                    </div>
                    <button
                        onClick={() => setShowMasterPw(true)}
                        className={styles.navItem}
                        data-tooltip="Rotate the MASTER password — the break-glass credential that signs in god_mode and bypass-logs into ANY facilitator account. Requires the current master password."
                        data-tooltip-pos="right"
                        style={{
                            display: 'flex', alignItems: 'center', gap: '8px', margin: '4px 8px 12px',
                            padding: '8px 10px', borderRadius: '8px', width: 'calc(100% - 16px)',
                            color: '#ef4444', fontWeight: 700, cursor: 'pointer', textAlign: 'left',
                            border: '1px dashed rgba(239,68,68,0.45)', background: 'rgba(239,68,68,0.05)',
                        }}
                    >
                        <span style={{ width: '18px', textAlign: 'center', flexShrink: 0, fontSize: '0.85rem' }}>🗝️</span>
                        <span>Master Key…</span>
                    </button>
                </nav>
            </aside>

            {/* ── Main Workspace ── */}
            <main className={styles.mainPanel}>
                <SystemContextBar
                    status={sysStatus.status}
                    lastSuccess={sysStatus.lastSuccess}
                    failedAttempts={sysStatus.failedAttempts}
                />
                <header className={styles.topBar}>
                    <div className={styles.meta} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', rowGap: '0.4rem', flexWrap: 'wrap', width: '100%' }}>
                        {(() => {
                            const meta = getTabMeta(activeTab);
                            return (
                                <nav style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.78rem' }}>
                                    <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>👑 God Mode</span>
                                    <span style={{ color: 'var(--text-muted)', opacity: 0.35 }}>›</span>
                                    <span style={{ color: 'var(--text-muted)' }}>{meta.categoryIcon} {meta.category}</span>
                                    <span style={{ color: 'var(--text-muted)', opacity: 0.35 }}>›</span>
                                    <span style={{ color: 'var(--text-primary)', fontWeight: 700 }}>{meta.label}</span>
                                </nav>
                            );
                        })()}
                        {/* G5: one visible, global target-cohort selection instead of
                            hidden coupling between per-tab pickers. */}
                        <CohortSelector
                            leaderboard={leaderboard}
                            selectedSession={selectedSession}
                            onSelect={setSelectedSession}
                        />
                    </div>
                </header>

                <div className={styles.mainContent}>
                    {renderActiveComponent()}
                </div>
            </main>

            {/* ── Mobile Sidebar Toggle (Phase 6: parity with the facilitator
                screen; makes the previously-dead sidebarOpen state real) ── */}
            <button
                onClick={() => setSidebarOpen(prev => !prev)}
                style={{
                    display: 'none', position: 'fixed', bottom: '1rem', right: '1rem', zIndex: 1300,
                    width: '48px', height: '48px', borderRadius: '50%',
                    background: 'var(--accent-gold, #f59e0b)', color: '#fff', border: 'none',
                    fontSize: '1.3rem', cursor: 'pointer',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.3)',
                }}
                className="mobile-sidebar-toggle"
                aria-label="Toggle sidebar"
            >
                {sidebarOpen ? '✕' : '☰'}
            </button>

            {/* Mobile responsive CSS */}
            <style>{`
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
                    }
                }
            `}</style>
        </div>
    );
}


/* ═════════════════════════════════════════════════════════════════
 *  DANGER ZONE PANEL
 * ═════════════════════════════════════════════════════════════════ */

function DangerZonePanel({ apiBase }) {
    const [sessions, setSessions] = useState([]);
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [loading, setLoading] = useState(true);
    // G6: a failed load must be distinguishable from "no cohorts exist" —
    // in a mass-deletion screen, mistaking an auth failure for an empty
    // database changes what an admin will do next.
    const [loadError, setLoadError] = useState(false);
    // Phase 5 (F4): tiered confirm + inline result feedback replace the
    // native confirm()/alert() pairs.
    const [confirmAction, confirmModal] = useConfirm();
    const [actionMsg, setActionMsg] = useState('');

    // Factory Reset guard state
    const [resetPhrase, setResetPhrase] = useState('');
    const [resetCountdown, setResetCountdown] = useState(0);
    const [resetResult, setResetResult] = useState('');
    const REQUIRED_PHRASE = 'DELETE ALL DATA';

    const loadSessions = useCallback(() => {
        setLoading(true);
        setLoadError(false);
        adminJson('/api/admin/sessions').then(({ ok, data }) => {
            if (ok) setSessions(data.sessions || []);
            else setLoadError(true);
            setLoading(false);
        });
    }, []);

    useEffect(() => { loadSessions(); }, [loadSessions]);

    // Factory Reset countdown effect
    useEffect(() => {
        if (resetCountdown <= 0) return;
        if (resetCountdown === 1) {
            (async () => {
                try {
                    const res = await fetch(`${apiBase}/api/admin/reset-all`, { method: 'DELETE', credentials: 'include' });
                    if (res.ok) {
                        const d = await res.json();
                        setResetResult(`✅ All ${d.sessions_removed} sessions wiped.`);
                        setSessions([]);
                    } else { setResetResult('❌ Reset failed'); }
                } catch { setResetResult('❌ Network error'); }
                setResetCountdown(0);
                setResetPhrase('');
            })();
            return;
        }
        const t = setTimeout(() => setResetCountdown(c => c - 1), 1000);
        return () => clearTimeout(t);
    }, [resetCountdown, apiBase]);

    const topLevelCohorts = sessions.filter(s => !s.player_id);

    const toggleSession = (id) => {
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const handleClearOrphans = async () => {
        const orphans = topLevelCohorts.filter(s => !s.facilitator_id);
        if (orphans.length === 0) {
            setActionMsg('ℹ️ No orphaned cohorts found.');
            return;
        }
        const ok = await confirmAction({
            title: `🗑️ Remove ${orphans.length} orphaned cohort(s)?`,
            message: 'Hard-deletes every cohort that has no facilitator assigned, including all player state under them.',
            impact: `Affected: ${orphans.map(s => s.cohort_name || s.session_id.slice(0, 8)).join(', ')}`,
            confirmLabel: 'Remove orphans',
        });
        if (!ok) return;
        try {
            await Promise.all(
                orphans.map(s => fetch(`${apiBase}/api/admin/sessions/${s.session_id}?hard=true`, { method: 'DELETE', credentials: 'include' }))
            );
            setActionMsg(`✅ Removed ${orphans.length} orphaned cohort(s).`);
            setSelectedIds(new Set());
            loadSessions(); // F4: refresh in place from the server, no stale local math
        } catch (e) {
            setActionMsg('❌ Failed to clear orphans: ' + e.message);
        }
    };

    const toggleAll = () => {
        if (selectedIds.size === topLevelCohorts.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(topLevelCohorts.map(s => s.session_id)));
        }
    };

    const handleDeleteSelected = async () => {
        if (selectedIds.size === 0) return;
        const names = topLevelCohorts
            .filter(s => selectedIds.has(s.session_id))
            .map(s => s.cohort_name || s.session_id.slice(0, 8));
        // F4: hard delete of live cohorts = irreversible + plural → typed phrase.
        const ok = await confirmAction({
            title: `🧨 Hard delete ${selectedIds.size} cohort(s)?`,
            message: 'Permanently deletes the selected cohorts and every player session under them. There is no grace period on this path.',
            impact: `Affected: ${names.join(', ')}`,
            requirePhrase: 'DELETE',
            confirmLabel: 'Delete permanently',
        });
        if (!ok) return;

        try {
            // Same endpoints as before — only the gate in front changed.
            await Promise.all(
                Array.from(selectedIds).map(id => fetch(`${apiBase}/api/admin/sessions/${id}?hard=true`, { method: 'DELETE', credentials: 'include' }))
            );
            setActionMsg(`✅ ${selectedIds.size} cohort(s) deleted.`);
            setSelectedIds(new Set());
            loadSessions(); // F4: refresh in place from the server
        } catch (e) {
            setActionMsg('❌ Failed to delete cohorts: ' + e.message);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', padding: '1.5rem', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
            {confirmModal}
            <div style={{ borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
                <h2 style={{ marginBottom: '0.5rem', color: '#ef4444' }}>☢️ Danger Zone</h2>
                <p style={{ color: 'var(--text-muted)' }}>Perform destructive operations on the simulation database. These actions cannot be undone.</p>
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.75rem',
                    padding: '0.5rem 0.75rem', borderRadius: '6px',
                    background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                    fontSize: '0.78rem', color: '#ef4444', fontWeight: 600,
                }}>
                    ⚠️ Active cohorts: {topLevelCohorts.length} · Total sessions (incl. players): {sessions.length}
                </div>
            </div>

            {/* Targeted Deletion Panel */}
            <div style={{ padding: '1.5rem', border: '1px solid var(--border-subtle)', borderRadius: '8px', background: 'var(--bg-body)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                    <div>
                        <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span>🗑️</span>
                            Targeted Deletion
                        </h3>
                        <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.9rem' }}>
                            Select specific cohorts to permanently delete. This will erase all connected player sessions within the cohort.
                        </p>
                    </div>
                    <button 
                        onClick={handleClearOrphans}
                        style={{
                            padding: '0.6rem 1.2rem', background: 'none', border: '1px solid #ef4444', 
                            color: '#ef4444', borderRadius: '6px', fontWeight: 600, cursor: 'pointer',
                            fontSize: '0.85rem'
                        }}
                    >
                        🗑️ Clear All Orphans Globally
                    </button>
                </div>

                {actionMsg && (
                    <div style={{
                        marginBottom: '1rem', padding: '8px 12px', borderRadius: '6px', fontSize: '0.82rem', fontWeight: 600,
                        color: actionMsg.startsWith('✅') ? '#10b981' : actionMsg.startsWith('ℹ️') ? 'var(--text-muted)' : '#ef4444',
                        background: actionMsg.startsWith('✅') ? 'rgba(16,185,129,0.1)' : actionMsg.startsWith('ℹ️') ? 'rgba(148,163,184,0.08)' : 'rgba(239,68,68,0.1)',
                    }}>{actionMsg}</div>
                )}
                {loading ? (
                    <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading cohorts...</div>
                ) : loadError ? (
                    <div style={{ padding: '1.25rem', textAlign: 'center', borderRadius: '6px', border: '1px solid rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.06)' }}>
                        <div style={{ color: '#ef4444', fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                            ⚠️ Couldn&apos;t load cohorts — this is a fetch/auth failure, not an empty database.
                        </div>
                        <button onClick={loadSessions} style={{ padding: '0.45rem 1.1rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.82rem', cursor: 'pointer', fontWeight: 600 }}>
                            🔄 Retry
                        </button>
                    </div>
                ) : (
                    <>
                        <div style={{ maxHeight: '350px', overflowY: 'auto', border: '1px solid var(--border-subtle)', borderRadius: '6px', marginBottom: '1rem', background: 'var(--bg-card)' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                <thead>
                                    <tr style={{ background: 'var(--bg-body)', textAlign: 'left', borderBottom: '1px solid var(--border-subtle)' }}>
                                        <th style={{ padding: '0.75rem', width: '40px' }}>
                                            <input 
                                                type="checkbox" 
                                                checked={topLevelCohorts.length > 0 && selectedIds.size === topLevelCohorts.length}
                                                onChange={toggleAll}
                                            />
                                        </th>
                                        <th style={{ padding: '0.75rem' }}>Cohort Name</th>
                                        <th style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>Facilitator</th>
                                        <th style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>Paradigm</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {topLevelCohorts.length === 0 ? (
                                        <tr>
                                            <td colSpan="4" style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>No cohorts active</td>
                                        </tr>
                                    ) : topLevelCohorts.map(s => {
                                        return (
                                            <tr key={s.session_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                                                <td style={{ padding: '0.75rem' }}>
                                                    <input 
                                                        type="checkbox" 
                                                        checked={selectedIds.has(s.session_id)}
                                                        onChange={() => toggleSession(s.session_id)}
                                                    />
                                                </td>
                                                <td style={{ padding: '0.75rem', fontWeight: 600 }}>{s.cohort_name || '(Unnamed Cohort)'}</td>
                                                <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{s.facilitator_id || '—'}</td>
                                                <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{s.decision_paradigm || 'legacy'}</td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                        
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <button 
                                onClick={handleDeleteSelected}
                                disabled={selectedIds.size === 0}
                                style={{
                                    background: selectedIds.size > 0 ? '#ef4444' : '#e2e8f0',
                                    color: selectedIds.size > 0 ? '#fff' : '#94a3b8',
                                    border: 'none',
                                    padding: '0.6rem 1.25rem',
                                    borderRadius: '6px',
                                    fontWeight: 'bold',
                                    cursor: selectedIds.size > 0 ? 'pointer' : 'not-allowed',
                                    transition: 'background 0.2s'
                                }}
                            >
                                DELETE {selectedIds.size} SELECTED COHORT(S)
                            </button>
                        </div>
                    </>
                )}
            </div>

            {/* Factory Reset — type-to-confirm guard */}
            <div style={{ padding: '1.5rem', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', background: 'rgba(239,68,68,0.04)' }}>
                <h3 style={{ color: '#ef4444', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span>☢️</span>
                    Factory Reset
                </h3>
                <p style={{ color: 'var(--text-muted)', margin: '0 0 0.5rem', fontSize: '0.9rem' }}>
                    Permanently destroy ALL sessions, player data, and simulation state. This cannot be undone.
                </p>
                <p style={{ color: 'var(--text-muted)', margin: '0 0 1rem', fontSize: '0.82rem', fontStyle: 'italic' }}>
                    Type <code style={{ background: 'rgba(239,68,68,0.12)', color: '#ef4444', padding: '2px 6px', borderRadius: '3px', fontWeight: 700, fontSize: '0.78rem' }}>{REQUIRED_PHRASE}</code> to unlock the reset button.
                </p>
                <input
                    type="text"
                    placeholder={`Type "${REQUIRED_PHRASE}" to confirm`}
                    value={resetPhrase}
                    onChange={e => setResetPhrase(e.target.value)}
                    disabled={resetCountdown > 0}
                    style={{
                        width: '100%', boxSizing: 'border-box', padding: '0.65rem 1rem',
                        border: '1.5px solid rgba(239,68,68,0.3)', borderRadius: '6px',
                        background: 'rgba(255,255,255,0.03)', color: 'var(--text-primary)',
                        fontSize: '0.88rem', fontFamily: 'var(--font-mono,monospace)',
                        outline: 'none', marginBottom: '0.75rem',
                    }}
                />
                {resetCountdown > 0 ? (
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: '10px',
                        padding: '10px 14px', borderRadius: '6px',
                        background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                        color: '#ef4444', fontSize: '0.85rem', fontWeight: 700,
                    }}>
                        ⏳ Executing in {resetCountdown}s…
                        <button
                            onClick={() => setResetCountdown(0)}
                            style={{
                                marginLeft: 'auto', background: 'none', border: '1px solid #ef4444',
                                color: '#ef4444', padding: '3px 10px', borderRadius: '4px',
                                cursor: 'pointer', fontWeight: 700, fontSize: '0.78rem',
                            }}
                        >
                            CANCEL
                        </button>
                    </div>
                ) : (
                    <button
                        disabled={resetPhrase !== REQUIRED_PHRASE}
                        onClick={() => { if (resetPhrase === REQUIRED_PHRASE) setResetCountdown(15); }}
                        style={{
                            width: '100%', padding: '0.7rem', borderRadius: '6px', border: 'none',
                            background: resetPhrase === REQUIRED_PHRASE ? '#ef4444' : 'rgba(239,68,68,0.15)',
                            color: resetPhrase === REQUIRED_PHRASE ? '#fff' : 'rgba(239,68,68,0.4)',
                            fontWeight: 700, fontSize: '0.88rem', cursor: resetPhrase === REQUIRED_PHRASE ? 'pointer' : 'not-allowed',
                            transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                            boxShadow: resetPhrase === REQUIRED_PHRASE ? '0 4px 12px rgba(239,68,68,0.3)' : 'none',
                        }}
                    >
                        ☢️ Erase All Sessions Permanently
                    </button>
                )}
                {resetResult && (
                    <div style={{ marginTop: '10px', padding: '8px 12px', borderRadius: '6px', fontSize: '0.82rem', fontWeight: 600, color: resetResult.startsWith('✅') ? '#10b981' : '#ef4444', background: resetResult.startsWith('✅') ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)' }}>
                        {resetResult}
                    </div>
                )}
            </div>


        </div>
    );
}
