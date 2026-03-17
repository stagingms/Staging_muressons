'use client';

import { useState, useCallback, useEffect } from 'react';
import styles from '../page.module.css';

import MaterialityConfig from '../../components/MaterialityConfig';
import MasterInterventions from '../../components/MasterInterventions';
import RoundPacingControl from '../../components/RoundPacingControl';
import ResourceManager from '../../components/ResourceManager';
import DecisionParadigmConfig from '../../components/DecisionParadigmConfig';
import FacilitatorManager from '../../components/FacilitatorManager';
import CrisisTriggerConfig from '../../components/CrisisTriggerConfig';

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
                sessionStorage.setItem('godmode_auth', JSON.stringify(data));
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
                            transition: 'all 0.2s',
                            boxShadow: '0 4px 16px rgba(245, 158, 11, 0.3)',
                        }}
                    >
                        {loading ? '⏳ Authenticating...' : '👑 Enter God Mode'}
                    </button>
                </form>
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
            const stored = sessionStorage.getItem('godmode_auth');
            if (stored) setAuthData(JSON.parse(stored));
        } catch { /* ignore */ }
        setChecked(true);
    }, []);

    const handleLogout = () => {
        sessionStorage.removeItem('godmode_auth');
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

function GodModeDashboard({ authData, onLogout }) {
    const [activeTab, setActiveTab] = useState('round_pacing');
    const [showChangePw, setShowChangePw] = useState(false);
    const [openCategories, setOpenCategories] = useState({
        config: true,
        master: true,
        danger: false,
    });

    const toggleCategory = (catId) => {
        setOpenCategories(prev => ({ ...prev, [catId]: !prev[catId] }));
    };

    const SIDEBAR_CONFIG = [
        {
            category: 'Simulation Config',
            icon: '⚙️',
            id: 'config',
            items: [
                { id: 'round_pacing', label: 'Round Pacing', component: 'RoundPacingControl' },
                { id: 'decision_paradigm', label: 'Decision Paradigm', component: 'DecisionParadigmConfig' },
                { id: 'facilitator_roles', label: 'Facilitator Roles', component: 'FacilitatorManager' },
            ]
        },
        {
            category: 'Master Data Hub',
            icon: '🌐',
            id: 'master',
            items: [
                { id: 'materiality', label: 'Materiality Matrix', component: 'MaterialityConfig' },
                { id: 'master_interventions', label: 'Team Interventions', component: 'MasterInterventions' },
                { id: 'crisis_triggers', label: 'Crisis Triggers', component: 'CrisisTriggerConfig' },
                { id: 'resources', label: 'Resource Library', component: 'ResourceManager' },
            ]
        },
        {
            category: 'Danger Zone',
            icon: '☢️',
            id: 'danger',
            items: [
                { id: 'global_reset', label: 'Global Reset', component: 'GlobalReset' },
            ]
        }
    ];

    const handleResetAll = useCallback(async () => {
        if (!confirm('☢️ RESET ALL SESSIONS?\nThis will DELETE every session and all data. Cannot be undone.')) return;
        if (!confirm('Are you absolutely sure? This action is irreversible.')) return;
        try {
            const res = await fetch(`${API}/api/admin/reset-all`, { method: 'DELETE' });
            if (res.ok) {
                const d = await res.json();
                alert(`✅ All ${d.sessions_removed} sessions have been wiped.`);
            } else {
                alert('❌ Reset failed: ' + res.status);
            }
        } catch { alert('❌ Reset failed: network error'); }
    }, []);

    const renderActiveComponent = () => {
        switch (activeTab) {
            case 'materiality':
                return <MaterialityConfig />;
            case 'master_interventions':
                return <MasterInterventions />;
            case 'round_pacing':
                return <RoundPacingControl />;
            case 'decision_paradigm':
                return <DecisionParadigmConfig sessions={[]} apiBase={API} />;
            case 'resources':
                return <ResourceManager />;
            case 'crisis_triggers':
                return <CrisisTriggerConfig />;
            case 'facilitator_roles':
                return <FacilitatorManager />;
            case 'global_reset':
                return (
                    <section style={{
                        background: 'var(--bg-card)',
                        border: '2px solid #ef4444',
                        borderRadius: 'var(--radius-lg)',
                        padding: '2rem',
                        maxWidth: '600px',
                    }}>
                        <h2 style={{ color: '#ef4444', marginBottom: '0.5rem' }}>☢️ Global Reset (Danger Zone)</h2>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                            Permanently wipe <strong>all</strong> simulation data across all cohorts and player sessions. This action cannot be undone.
                        </p>
                        <button
                            onClick={handleResetAll}
                            style={{
                                background: 'linear-gradient(135deg, #ef4444, #dc2626)',
                                color: '#fff',
                                border: 'none',
                                borderRadius: '8px',
                                padding: '0.8rem 2rem',
                                fontSize: '1rem',
                                fontWeight: 700,
                                cursor: 'pointer',
                                boxShadow: '0 4px 16px rgba(239, 68, 68, 0.4)',
                            }}
                        >
                            ☢️ Factory Nuke All Sessions
                        </button>
                    </section>
                );
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

            {/* ── Sidebar ── */}
            <aside className={styles.sidebar}>
                <div className={styles.sidebarHeader}>
                    <h1>👑 God Mode</h1>
                    <div className={styles.godBadge}>Muressons Global Command</div>
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
                            <button
                                className={styles.categoryHeader}
                                onClick={() => toggleCategory(group.id)}
                            >
                                <span>{group.icon} {group.category}</span>
                                <span>{openCategories[group.id] ? '▼' : '▶'}</span>
                            </button>

                            {openCategories[group.id] && (
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
                            )}
                        </div>
                    ))}
                </nav>
            </aside>

            {/* ── Main Workspace ── */}
            <main className={styles.mainPanel}>
                <header className={styles.topBar}>
                    <div className={styles.meta}>
                        <span className={styles.selectedTag}>Universal simulation parameters</span>
                    </div>
                </header>

                <div className={styles.mainContent}>
                    {renderActiveComponent()}
                </div>
            </main>
        </div>
    );
}
