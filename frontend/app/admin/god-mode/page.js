'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import styles from '../page.module.css';

import MaterialityConfig from '../../components/MaterialityConfig';
import MasterInterventions from '../../components/MasterInterventions';
import RoundPacingControl from '../../components/RoundPacingControl';
import ResourceManager from '../../components/ResourceManager';

import FacilitatorManager from '../../components/FacilitatorManager';
import CrisisTriggerConfig from '../../components/CrisisTriggerConfig';
import CustomBlackSwanBuilder from '../../components/CustomBlackSwanBuilder';
import GodModeStatus from '../../components/GodModeStatus';
import GodModeAuditLog from '../../components/GodModeAuditLog';
import UniversalBroadcast from '../../components/UniversalBroadcast';
import SystemExport from '../../components/SystemExport';
import PlatformAnalytics from '../../components/PlatformAnalytics';
import AnalyticsControlPanel from '../../components/AnalyticsControlPanel';
import GlossaryManager from '../../components/GlossaryManager';
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
import { GOD_MODE_SIDEBAR, getTabMeta as _getTabMeta } from '../../config/sidebarConfig';
import OnboardingWizard from '../../components/OnboardingWizard';

const API = process.env.NEXT_PUBLIC_API_URL || '';


/* ═════════════════════════════════════════════════════════════════
 *  LOGIN GATE — Same facilitator-based auth as Workshop Facilitator
 * ═════════════════════════════════════════════════════════════════ */

function GodModeLoginGate({ onLogin }) {
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
                if (data.role !== 'super_admin' && !data.is_admin) {
                    setError('Unauthorized: God Mode requires Super Administrator privileges. Contact your system administrator to request God Mode access, or use the Facilitator dashboard instead.');
                    return;
                }
                localStorage.setItem('godmode_auth', JSON.stringify(data));
                onLogin(data);            } else {
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
                    <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>👑</div>
                    <h1 style={{
                        fontSize: '1.5rem',
                        fontWeight: 800,
                        color: 'var(--text-primary)',
                        margin: '0 0 0.5rem 0',
                    }}>
                        God Mode Access
                    </h1>
                    <p style={{
                        fontSize: '0.82rem',
                        color: 'var(--text-muted)',
                        margin: 0,
                    }}>
                        Enter your facilitator credentials to access the God Mode Control Room.
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
                            background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
                            color: '#fff',
                            fontSize: '0.9rem',
                            fontWeight: 700,
                            cursor: 'pointer',
                            opacity: loading ? 0.7 : 1,
                            transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                            boxShadow: '0 4px 16px rgba(245, 158, 11, 0.3)',
                        }}
                    >
                        {loading ? '⏳ Authenticating...' : '👑 Enter God Mode'}
                    </button>
                </form>
                <div style={{ textAlign: 'center', marginTop: '1.25rem' }}>
                    <Link href="/admin" style={{
                        fontSize: '0.8rem',
                        color: 'var(--text-muted)',
                        textDecoration: 'none',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        opacity: 0.7,
                        transition: 'opacity 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = 1}
                    onMouseLeave={e => e.currentTarget.style.opacity = 0.7}
                    >
                        ← Back to Admin Portal
                    </Link>
                </div>
                <div style={{
                    marginTop: '1rem', padding: '0.7rem 0.9rem', borderRadius: '8px',
                    background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)',
                    fontSize: '0.7rem', color: 'var(--text-muted)', lineHeight: 1.5,
                }}>
                    <strong style={{ color: '#818cf8' }}>ℹ️ Who has God Mode?</strong><br/>
                    Only Super Administrators can access God Mode. If you are a Facilitator or Lead Facilitator, use the{' '}
                    <Link href="/admin/facilitator" style={{ color: '#60a5fa', textDecoration: 'underline' }}>Facilitator Dashboard</Link> instead.
                    Your role is assigned by the system administrator.
                </div>
            </div>
        </div>
    );
}


/* ═════════════════════════════════════════════════════════════════
 *  CHANGE PASSWORD MODAL
 * ═════════════════════════════════════════════════════════════════ */

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
    const [authData, setAuthData] = useState(null);
    const [checked, setChecked] = useState(false);

    useEffect(() => {
        try {
            const stored = localStorage.getItem('godmode_auth');
            if (stored) setAuthData(JSON.parse(stored));
        } catch { /* ignore */ }
        setChecked(true);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('godmode_auth');
        setAuthData(null);
    };

    if (!checked) return null;

    if (!authData) {
        return <GodModeLoginGate onLogin={setAuthData} />;
    }

    return <GodModeDashboard authData={authData} onLogout={handleLogout} />;
}


/* ═════════════════════════════════════════════════════════════════
 *  GOD MODE DASHBOARD (protected behind login gate)
 * ═════════════════════════════════════════════════════════════════ */


/* ═════════════════════════════════════════════════════════════════
 *  SYSTEM CONTEXT BAR
 * ═════════════════════════════════════════════════════════════════ */
function SystemContextBar() {
    const [status, setStatus] = useState(null);

    useEffect(() => {
        const fetchStatus = () => {
            fetch(`${API}/api/admin/god/system-status`)
                .then(r => r.json())
                .then(d => setStatus(d))
                .catch(() => {});
        };
        fetchStatus();
        const t = setInterval(fetchStatus, 15000);
        return () => clearInterval(t);
    }, []);

    const activeCohorts = status ? status.total_cohorts : 0;
    const activePlayers = status ? status.total_players : 0;
    const isOptimal = status ? (status.system_memory_mb || 0) < 500 : true;

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
            <div style={{ display: 'flex', gap: '1.5rem' }}>
                <span style={{ color: '#38bdf8' }}>📡 COMMAND UPLINK</span>
                <span>Live Cohorts: <span style={{ color: 'var(--text-primary)' }}>{activeCohorts}</span></span>
                <span>Active Players: <span style={{ color: 'var(--text-primary)' }}>{activePlayers}</span></span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                System Health: 
                <span style={{
                    color: isOptimal ? '#10b981' : '#ef4444',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: isOptimal ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)'
                }}>
                    <span style={{ 
                        display: 'inline-block',
                        animation: 'heartbeatPulse 2.5s infinite'
                    }}>
                        {isOptimal ? '🟢' : '🔴'}
                    </span> 
                    {isOptimal ? 'Optimal' : 'Warning'}
                </span>
            </div>
        </div>
    );
}

function GodModeDashboard({ authData, onLogout }) {
    const [activeTab, setActiveTab] = useState('system_overview');
    const [showChangePw, setShowChangePw] = useState(false);
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

    useEffect(() => {
        const fetchLb = () => fetch(`${API}/api/admin/leaderboard`, {
            headers: { 'x-facilitator-id': authData?.facilitator_id }
        })
            .then(r => r.ok ? r.json() : null)
            .then(d => d?.leaderboard && setLeaderboard(d.leaderboard))
            .catch(() => {});
        fetchLb();
        const t = setInterval(fetchLb, 30000);
        return () => clearInterval(t);
    }, [authData]);

    const toggleCategory = (catId) => {
        setOpenCategories(prev => ({ ...prev, [catId]: !prev[catId] }));
    };

    // Keyboard shortcuts
    useEffect(() => {
        const handler = (e) => {
            if (e.ctrlKey || e.metaKey) {
                const categoryKeys = ['command_center', 'orchestration', 'engine_core', 'content', 'danger'];
                if (e.key >= '1' && e.key <= '5') {
                    e.preventDefault();
                    const idx = parseInt(e.key) - 1;
                    if (categoryKeys[idx]) {
                        setOpenCategories(prev => {
                            const newState = {};
                            categoryKeys.forEach(k => { newState[k] = false; });
                            newState[categoryKeys[idx]] = true;
                            return newState;
                        });
                    }
                }
                if (e.key === 'b' || e.key === 'B') {
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
                        <GodModeStatus facilitatorId={authData?.facilitator_id} />
                        <SessionHealthDashboard />
                    </div>
                );
            case 'activity_log':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <GodModeAuditLog />
                        <ComplexityEventFeed sessionId={null} />
                    </div>
                );
            case 'platform_analytics':
                return <PlatformAnalytics />;
                
            case 'facilitator_registry':
                return <FacilitatorManager onNavigate={(tab) => setActiveTab(tab)} />;
            case 'cohort_provisioning':
                return <SimulationManager fetchInternal={false} leaderboard={leaderboard} />;
            case 'cohort_orchestration':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <SimulationManager fetchInternal={false} leaderboard={leaderboard} />
                        <FacilitatorManager onNavigate={(tab) => setActiveTab(tab)} />
                    </div>
                );
            case 'session_controls':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <UniversalBroadcast />
                    </div>
                );
            case 'master_interventions':
                return <MasterInterventions />;
            case 'crisis_overrides':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <CrisisTriggerConfig />
                        <CustomBlackSwanBuilder />
                    </div>
                );
                
            case 'macro_economics':
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                        <EconomicEngineTunables />
                        <MasterVariableEditor />
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
            case 'regulatory_sandbox': {
                const sandboxSessions = leaderboard.filter(s => !s.player_id);
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {sandboxSessions.length > 0 && (
                            <div style={{ padding: '0.75rem 1.5rem', background: 'var(--bg-card)', borderRadius: '10px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)' }}>⚖️ Target Cohort:</span>
                                <select
                                    value={selectedSession || ''}
                                    onChange={e => setSelectedSession(e.target.value || null)}
                                    style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.85rem' }}
                                >
                                    <option value=''>— Select a cohort —</option>
                                    {sandboxSessions.map(s => <option key={s.session_id} value={s.session_id}>{s.cohort_name || s.session_id}</option>)}
                                </select>
                            </div>
                        )}
                        <RegulatorySandboxControl sessionId={selectedSession} isGodMode={true} />
                    </div>
                );
            }
                
            case 'resources':
                return <ResourceManager />;
            case 'glossary_editor':
                return <GlossaryManager />;
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
                        {cohortSessions.length > 0 && (
                            <div style={{ padding: '0.75rem 1.5rem', background: 'var(--bg-card)', borderRadius: '10px', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)' }}>📋 Select Cohort:</span>
                                <select
                                    value={selectedSession || ''}
                                    onChange={e => setSelectedSession(e.target.value || null)}
                                    style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid var(--border-subtle)', background: 'var(--bg-body)', color: 'var(--text-primary)', fontSize: '0.85rem' }}
                                >
                                    <option value=''>— Choose a cohort —</option>
                                    {cohortSessions.map(s => <option key={s.session_id} value={s.session_id}>{s.cohort_name || s.session_id}</option>)}
                                </select>
                            </div>
                        )}
                        <DebriefReport sessionId={selectedSession} />
                    </div>
                );
            }

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
            {/* ── Change Password Modal ── */}
            {showChangePw && (
                <GodModeChangePasswordModal
                    facilitatorId={authData.facilitator_id}
                    onClose={() => setShowChangePw(false)}
                />
            )}

            {/* ── Onboarding Wizard (first-time only) ── */}
            <OnboardingWizard mode="god_mode" userId={authData.facilitator_id} onStepChange={(tab) => setActiveTab(tab)} />

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
                    {SIDEBAR_CONFIG.map((group) => (
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
                                        data-tooltip-pos="right"
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
                <SystemContextBar />
                <header className={styles.topBar}>
                    <div className={styles.meta}>
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
 *  DANGER ZONE PANEL
 * ═════════════════════════════════════════════════════════════════ */

function DangerZonePanel({ apiBase }) {
    const [sessions, setSessions] = useState([]);
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [loading, setLoading] = useState(true);

    // Factory Reset guard state
    const [resetPhrase, setResetPhrase] = useState('');
    const [resetCountdown, setResetCountdown] = useState(0);
    const [resetResult, setResetResult] = useState('');
    const REQUIRED_PHRASE = 'DELETE ALL DATA';

    useEffect(() => {
        fetch(`${apiBase}/api/admin/sessions`)
            .then(res => res.json())
            .then(data => {
                setSessions(data.sessions || []);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, [apiBase]);

    // Factory Reset countdown effect
    useEffect(() => {
        if (resetCountdown <= 0) return;
        if (resetCountdown === 1) {
            (async () => {
                try {
                    const res = await fetch(`${apiBase}/api/admin/reset-all`, { method: 'DELETE' });
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
        if (!confirm('⚠️ REMOVE ORPHANED COHORTS?\nThis will clear all cohorts globally that do not have a facilitator assigned.')) return;
        try {
            const orphans = topLevelCohorts.filter(s => !s.facilitator_id);
            if (orphans.length === 0) {
               alert("No orphaned cohorts found.");
               return;
            }
            await Promise.all(
                orphans.map(s => fetch(`${apiBase}/api/admin/sessions/${s.session_id}?hard=true`, { method: 'DELETE' }))
            );
            alert(`✅ Successfully removed ${orphans.length} orphaned cohort(s).`);
            setSessions(prev => prev.filter(s => !!s.facilitator_id || !!s.player_id));
            setSelectedIds(new Set());
        } catch (e) {
            alert('❌ Failed to clear orphans: ' + e.message);
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
        if (!confirm(`⚠️ DELETE ${selectedIds.size} COHORT(S)?\nThis will permanently delete the selected cohorts and all their player state.`)) return;
        
        try {
            // Delete one by one manually, we don't need promise.all to spam it if we're worried about locks, but for speed Promise.all
            await Promise.all(
                Array.from(selectedIds).map(id => fetch(`${apiBase}/api/admin/sessions/${id}?hard=true`, { method: 'DELETE' }))
            );
            alert(`✅ ${selectedIds.size} cohort(s) deleted.`);
            setSessions(prev => prev.filter(s => !selectedIds.has(s.session_id)));
            setSelectedIds(new Set());
        } catch (e) {
            alert('❌ Failed to delete cohorts: ' + e.message);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', padding: '1.5rem', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
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

                {loading ? (
                    <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading cohorts...</div>
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
                        ☢️ Factory Nuke All Sessions
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
