'use client';

import { useState } from 'react';
import styles from './TeamImpersonation.module.css';
import { formatSessionId } from '../utils/sessionUtils';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function TeamImpersonation({ leaderboard = [], selectedSession }) {
    const [viewSession, setViewSession] = useState(selectedSession || '');
    const [dashData, setDashData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleView = async () => {
        if (!viewSession) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API}/api/simulations/${viewSession}/dashboard`);
            if (res.ok) {
                const data = await res.json();
                setDashData(data);
            } else {
                setError('Failed to load session data');
            }
        } catch {
            setError('Network error');
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (val) => val >= 1e6 ? `$${(val / 1e6).toFixed(1)}M` : `$${val?.toFixed(0) || 0}`;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🔍</span>
                <div>
                    <h2 className={styles.title}>Team Impersonation</h2>
                    <p className={styles.subtitle}>View a team&#39;s dashboard as they see it. Select a session to inspect.</p>
                </div>
            </div>

            <div className={styles.selectorRow}>
                <select className={styles.select} value={viewSession} onChange={(e) => setViewSession(e.target.value)}>
                    <option value="">— Select a session —</option>
                    {leaderboard.map(s => (
                        <option key={s.session_id} value={s.session_id}>
                            {s.cohort_name || formatSessionId(s)} (R{s.round_number || 1})
                        </option>
                    ))}
                </select>
                <button className={styles.viewBtn} onClick={handleView} disabled={!viewSession || loading}>
                    {loading ? '⏳ Loading...' : '🔍 View Dashboard'}
                </button>
            </div>

            {error && <div className={styles.error}>❌ {error}</div>}

            {dashData && (
                <div className={styles.impersonationView}>
                    <div className={styles.viewHeader}>
                        <span className={styles.viewBadge}>👁️ IMPERSONATION VIEW</span>
                        <span className={styles.viewSession}>{leaderboard.find(s => s.session_id === dashData.session_id)?.short_code || dashData.session_id?.slice(0, 8)} — Round {dashData.current_round}</span>
                    </div>

                    {/* ── Global State ── */}
                    <div className={styles.stateGrid}>
                        <div className={styles.stateCard}>
                            <div className={styles.stateLabel}>💰 Corporate Treasury</div>
                            <div className={styles.stateValue}>{formatCurrency(dashData.global_state?.corporate_treasury || 0)}</div>
                        </div>
                        <div className={styles.stateCard}>
                            <div className={styles.stateLabel}>⭐ Group Reputation</div>
                            <div className={styles.stateValue}>{(dashData.global_state?.group_reputation || 0).toFixed(1)}</div>
                        </div>
                        <div className={styles.stateCard}>
                            <div className={styles.stateLabel}>🔗 Synergy Multiplier</div>
                            <div className={styles.stateValue}>{(dashData.global_state?.synergy_multiplier || 1).toFixed(3)}</div>
                        </div>
                        <div className={styles.stateCard}>
                            <div className={styles.stateLabel}>📈 Cost of Capital</div>
                            <div className={styles.stateValue}>{((dashData.global_state?.cost_of_capital || 0.05) * 100).toFixed(1)}%</div>
                        </div>
                    </div>

                    {/* ── Business Units ── */}
                    <h3 className={styles.buTitle}>Business Units</h3>
                    <table className={styles.buTable}>
                        <thead>
                            <tr>
                                <th>BU</th>
                                <th>Revenue</th>
                                <th>OPEX</th>
                                <th>NCD</th>
                                <th>Social License</th>
                                <th>Reputation</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(dashData.business_units || []).map(bu => (
                                <tr key={bu.bu_id}>
                                    <td className={styles.buName}>{bu.bu_id?.replace('_', ' ')}</td>
                                    <td>{formatCurrency(bu.revenue_base)}</td>
                                    <td>{formatCurrency(bu.opex_base)}</td>
                                    <td>{(bu.natural_capital_debt || 0).toFixed(0)}</td>
                                    <td>{(bu.social_license_score || 0).toFixed(1)}</td>
                                    <td>{(bu.reputation_score || 0).toFixed(1)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {/* ── Event Flags ── */}
                    {dashData.global_state?.active_event_flags && Object.keys(dashData.global_state.active_event_flags).length > 0 && (
                        <div className={styles.flagsSection}>
                            <h3 className={styles.flagsTitle}>Active Event Flags</h3>
                            <div className={styles.flagGrid}>
                                {Object.entries(dashData.global_state.active_event_flags).map(([key, val]) => (
                                    <div key={key} className={styles.flagChip}>
                                        <span className={styles.flagKey}>{key}</span>
                                        <span className={styles.flagVal}>{typeof val === 'boolean' ? (val ? '✅' : '❌') : typeof val === 'object' && val !== null ? JSON.stringify(val).slice(0, 100) : String(val).slice(0, 50)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
