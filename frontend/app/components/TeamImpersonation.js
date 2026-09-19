'use client';

import { useState, useMemo } from 'react';
import styles from './TeamImpersonation.module.css';
import { formatSessionId } from '../utils/sessionUtils';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Curate raw event flags into human-readable grouped summaries.
 */
function curateFlagSummary(flags, globalState) {
    if (!flags || typeof flags !== 'object') return { financial: [], esg: [], strategic: [] };

    const financial = [];
    const esg = [];
    const strategic = [];

    // --- Financial Health ---
    if (flags.insolvency_active) financial.push({ label: 'Insolvency Active', value: '🚨 Yes', severity: 'critical' });
    if (flags.dividend_suspended) financial.push({ label: 'Dividends Suspended', value: '⚠️ Yes', severity: 'warning' });
    if (flags.emergency_credit_used) financial.push({ label: 'Emergency Credit Used', value: `$${((flags.emergency_credit_amount || 0) / 1e6).toFixed(1)}M`, severity: 'warning' });
    if (flags.capex_capped) financial.push({ label: 'CapEx Capped', value: `Limit: $${((flags.capex_cap_limit || 0) / 1e6).toFixed(0)}M`, severity: 'warning' });
    if (flags.negative_treasury_interest_applied) financial.push({ label: 'Creditor Interest Charged', value: `$${((flags.negative_treasury_interest_applied || 0) / 1e6).toFixed(1)}M`, severity: 'warning' });
    if (flags.capex_cap_multiplier && flags.capex_cap_multiplier < 1) financial.push({ label: 'CapEx Multiplier', value: `${flags.capex_cap_multiplier.toFixed(1)}×`, severity: 'info' });
    if (flags.last_dividends_paid) financial.push({ label: 'Last Dividends Paid', value: `$${((flags.last_dividends_paid || 0) / 1e6).toFixed(1)}M`, severity: 'ok' });
    const inflApp = flags.inflation_index_applied;
    if (inflApp && inflApp > 0) financial.push({ label: 'Inflation Index', value: `${(inflApp * 100).toFixed(1)}%`, severity: inflApp > 0.04 ? 'warning' : 'info' });
    if (flags.coc_macro_rate_applied) financial.push({ label: 'Macro Rate Applied', value: `${(flags.coc_macro_rate_applied * 100).toFixed(1)}%`, severity: 'info' });

    // --- ESG & Risk ---
    if (flags.fx_risk && typeof flags.fx_risk === 'object') esg.push({ label: 'FX Risk', value: `${flags.fx_risk.fx_direction || '—'} (${((flags.fx_risk.fx_index || 0) * 100).toFixed(1)}%)`, severity: flags.fx_risk.fx_direction === 'weakened' ? 'warning' : 'ok' });
    if (flags.supply_chain_transparency != null) esg.push({ label: 'Supply Chain Transparency', value: `${flags.supply_chain_transparency}`, severity: flags.supply_chain_transparency > 0 ? 'ok' : 'warning' });
    if (flags.talent_penalty_applied && flags.talent_penalty_applied > 1) esg.push({ label: 'Talent Brain Drain', value: `${((flags.talent_penalty_applied - 1) * 100).toFixed(0)}% OPEX inflation`, severity: 'warning' });
    if (flags.employer_brand && typeof flags.employer_brand === 'object') esg.push({ label: 'Employer Brand Score', value: `${(flags.employer_brand.employer_brand_score || 0).toFixed(0)}/100`, severity: (flags.employer_brand.employer_brand_score || 0) > 50 ? 'ok' : 'warning' });
    if (flags.esg_adjusted_wacc && typeof flags.esg_adjusted_wacc === 'object') esg.push({ label: 'ESG-Adjusted WACC', value: `${((flags.esg_adjusted_wacc.base_wacc || 0) * 100).toFixed(1)}%`, severity: 'info' });
    if (flags.macro_rate_environment && typeof flags.macro_rate_environment === 'object') esg.push({ label: 'Macro Regime', value: `${flags.macro_rate_environment.label || flags.macro_rate_environment.regime || '—'}`, severity: flags.macro_rate_environment.regime === 'crisis' ? 'critical' : 'info' });

    // Supply chain contagion
    const scKeys = Object.keys(flags).filter(k => k.startsWith('supply_chain_contagion_'));
    if (scKeys.length > 0) {
        const total = scKeys.reduce((sum, k) => sum + (flags[k] || 0), 0);
        esg.push({ label: 'Supply Chain Contagion', value: `$${(total / 1e6).toFixed(1)}M across ${scKeys.length} BUs`, severity: total > 5e6 ? 'warning' : 'info' });
    }

    // Revenue cannibalization
    if (flags.revenue_cannibalized_consumer_goods_because) esg.push({ label: 'Revenue Cannibalized', value: flags.revenue_cannibalized_consumer_goods_because, severity: 'warning' });

    // Technical debt
    const tdKeys = Object.keys(flags).filter(k => k.startsWith('technical_debt_penalty_'));
    if (tdKeys.filter(k => flags[k]).length > 0) {
        const penalizedBUs = tdKeys.filter(k => flags[k]).map(k => k.replace('technical_debt_penalty_', '').replace(/_/g, ' '));
        esg.push({ label: 'Technical Debt Penalties', value: penalizedBUs.join(', '), severity: 'warning' });
    }

    // Burnout
    const burnoutKeys = Object.keys(flags).filter(k => k.startsWith('burnout_passive_decay_'));
    if (burnoutKeys.length > 0) {
        esg.push({ label: 'Staff Burnout Decay', value: `${burnoutKeys.length} BUs affected`, severity: 'info' });
    }

    // --- Strategic Flags ---
    if (flags.crisis_count_lifetime) strategic.push({ label: 'Crises Experienced', value: `${flags.crisis_count_lifetime}`, severity: 'info' });
    if (flags.revenue_generation_completed) strategic.push({ label: 'Revenue Projects Completed', value: `$${((flags.revenue_generation_completed || 0) / 1e6).toFixed(1)}M`, severity: 'ok' });
    if (flags.capex_project_completed && typeof flags.capex_project_completed === 'object') strategic.push({ label: 'Last CapEx Project', value: flags.capex_project_completed.description || '—', severity: 'ok' });
    if (flags.active_black_swans && Array.isArray(flags.active_black_swans) && flags.active_black_swans.length > 0) strategic.push({ label: 'Active Black Swans', value: `${flags.active_black_swans.length} event(s)`, severity: 'critical' });

    // DSO working capital
    if (flags.dso_working_capital && typeof flags.dso_working_capital === 'object') {
        const totalDeferred = flags.dso_working_capital.total_deferred || 0;
        if (totalDeferred > 0) strategic.push({ label: 'DSO Working Capital Deferred', value: `$${(totalDeferred / 1e6).toFixed(1)}M`, severity: 'warning' });
    }

    // Cash conversion drag
    const ccKeys = Object.keys(flags).filter(k => k.startsWith('cash_conversion_drag_'));
    if (ccKeys.length > 0) {
        const totalDrag = ccKeys.reduce((sum, k) => sum + (flags[k] || 0), 0);
        if (totalDrag > 0) strategic.push({ label: 'Cash Conversion Drag', value: `$${(totalDrag / 1e6).toFixed(1)}M total`, severity: 'info' });
    }

    return { financial, esg, strategic };
}

export default function TeamImpersonation({ leaderboard = [], selectedSession }) {
    const [viewSession, setViewSession] = useState(selectedSession || '');
    const [dashData, setDashData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [showRawFlags, setShowRawFlags] = useState(false);

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

    const flagSummary = useMemo(() => {
        if (!dashData?.global_state?.active_event_flags) return null;
        return curateFlagSummary(dashData.global_state.active_event_flags, dashData.global_state);
    }, [dashData]);

    const severityStyle = (severity) => {
        switch (severity) {
            case 'critical': return { background: 'rgba(239,68,68,0.12)', borderColor: 'rgba(239,68,68,0.3)', color: '#fca5a5' };
            case 'warning': return { background: 'rgba(245,158,11,0.10)', borderColor: 'rgba(245,158,11,0.3)', color: '#fcd34d' };
            case 'ok': return { background: 'rgba(16,185,129,0.10)', borderColor: 'rgba(16,185,129,0.3)', color: '#6ee7b7' };
            default: return { background: 'rgba(148,163,184,0.08)', borderColor: 'rgba(148,163,184,0.15)', color: '#94a3b8' };
        }
    };

    const renderFlagGroup = (title, icon, items) => {
        if (!items || items.length === 0) return null;
        return (
            <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 'var(--type-caption)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#64748b', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <span>{icon}</span> {title}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {items.map((item, i) => {
                        const sty = severityStyle(item.severity);
                        return (
                            <div key={i} style={{
                                display: 'flex', alignItems: 'center', gap: 8,
                                padding: '5px 10px', borderRadius: 6,
                                border: `1px solid ${sty.borderColor}`,
                                background: sty.background,
                                fontSize: 'var(--type-caption)',
                            }}>
                                <span style={{ fontWeight: 600, color: '#cbd5e1' }}>{item.label}</span>
                                <span style={{ fontWeight: 700, color: sty.color, fontFamily: "'JetBrains Mono', monospace" }}>{item.value}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>🔍</span>
                <div>
                    <h2 className={styles.title}>Session State Inspector</h2>
                    <p className={styles.subtitle}>Inspect financial state, business unit margins, and event flags for any enrolled session.</p>
                </div>
            </div>

            <div style={{ padding: '0.5rem 0.75rem', marginBottom: '1rem', background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.25)', borderRadius: '6px', fontSize: '0.8rem', color: '#93c5fd' }}>
                Participant cockpit view is accessed via view-only credentials (-VIEW). This panel inspects raw session financial state and risk flags.
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
                    {loading ? '⏳ Loading...' : '🔍 Inspect Session'}
                </button>
            </div>

            {error && <div className={styles.error}>❌ {error}</div>}

            {dashData && (
                <div className={styles.impersonationView}>
                    <div className={styles.viewHeader}>
                        <span className={styles.viewBadge}>👁️ SESSION STATE INSPECTOR</span>
                        <span className={styles.viewSession}>{leaderboard.find(s => s.session_id === dashData.session_id)?.short_code || dashData.session_id?.slice(0, 8)} — Round {dashData.current_round}</span>
                    </div>

                    {/* ── Global State ── */}
                    <div className={styles.stateGrid}>
                        <div className={styles.stateCard}>
                            <div className={styles.stateLabel}>💰 Corporate Treasury</div>
                            <div className={styles.stateValue} style={{ color: (dashData.global_state?.corporate_treasury || 0) < 0 ? '#f87171' : undefined }}>{formatCurrency(dashData.global_state?.corporate_treasury || 0)}</div>
                        </div>
                        <div className={styles.stateCard}>
                            <div className={styles.stateLabel}>⭐ Group Reputation</div>
                            <div className={styles.stateValue}>{(dashData.global_state?.group_reputation || 0).toFixed(1)}</div>
                        </div>
                        <div className={styles.stateCard}>
                            <div className={styles.stateLabel}>🔗 Synergy Multiplier</div>
                            <div className={styles.stateValue}>{(dashData.global_state?.synergy_multiplier || 1).toFixed(2)}×</div>
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
                                <th style={{ textAlign: 'center' }}>Margin</th>
                                <th>NCD</th>
                                <th>Social License</th>
                                <th>Reputation</th>
                            </tr>
                        </thead>
                        <tbody>
                            {(dashData.business_units || []).map(bu => {
                                const margin = bu.revenue_base > 0 ? ((bu.revenue_base - bu.opex_base) / bu.revenue_base * 100) : 0;
                                return (
                                    <tr key={bu.bu_id}>
                                        <td className={styles.buName}>{bu.bu_id?.replace(/_/g, ' ')}</td>
                                        <td>{formatCurrency(bu.revenue_base)}</td>
                                        <td>{formatCurrency(bu.opex_base)}</td>
                                        <td style={{ textAlign: 'center', fontWeight: 700, color: margin >= 25 ? '#10b981' : margin >= 15 ? '#f59e0b' : '#ef4444' }}>{margin.toFixed(0)}%</td>
                                        <td>{(bu.natural_capital_debt || 0).toFixed(0)}</td>
                                        <td>{(bu.social_license_score || 0).toFixed(1)}</td>
                                        <td>{(bu.reputation_score || 0).toFixed(1)}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>

                    {/* ── Curated Event Summary ── */}
                    {flagSummary && (flagSummary.financial.length > 0 || flagSummary.esg.length > 0 || flagSummary.strategic.length > 0) && (
                        <div className={styles.flagsSection}>
                            <h3 className={styles.flagsTitle}>Session Status Summary</h3>
                            {renderFlagGroup('Financial Health', '💰', flagSummary.financial)}
                            {renderFlagGroup('ESG & Risk', '🌍', flagSummary.esg)}
                            {renderFlagGroup('Strategic Progress', '🎯', flagSummary.strategic)}

                            {/* Raw data toggle for debugging */}
                            <button
                                onClick={() => setShowRawFlags(prev => !prev)}
                                style={{
                                    marginTop: 8, padding: '4px 10px', borderRadius: 4,
                                    background: 'transparent', border: '1px solid rgba(148,163,184,0.15)',
                                    color: '#475569', fontSize: 'var(--type-caption)', fontWeight: 600,
                                    cursor: 'pointer', letterSpacing: '0.04em', textTransform: 'uppercase',
                                }}
                            >
                                {showRawFlags ? '▲ Hide Raw Data' : '▼ Show Raw Data'}
                            </button>
                            {showRawFlags && (
                                <pre style={{
                                    marginTop: 8, padding: 12, borderRadius: 6,
                                    background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(148,163,184,0.1)',
                                    fontSize: 'var(--type-caption)', color: '#64748b', overflow: 'auto',
                                    maxHeight: 300, fontFamily: "'JetBrains Mono', monospace",
                                    lineHeight: 1.5, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                                }}>
                                    {JSON.stringify(dashData.global_state?.active_event_flags, null, 2)}
                                </pre>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
