'use client';
import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import styles from './GameOverSummary.module.css';
import StudentReportExport from './StudentReportExport';

const CEOInterview = dynamic(() => import('./CEOInterview'), { ssr: false });

const PROFILES = {
    regenerative_titan: { icon: '🌱', gradient: 'linear-gradient(135deg, #10b981, #059669)', title: 'Regenerative Titan' },
    derisked_safe_haven: { icon: '🛡️', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', title: 'De-risked Safe Haven' },
    fragile_giant: { icon: '⚠️', gradient: 'linear-gradient(135deg, #f59e0b, #d97706)', title: 'Fragile Giant' },
    stranded_relic: { icon: '💀', gradient: 'linear-gradient(135deg, #ef4444, #b91c1c)', title: 'Stranded Relic' },
};

const FALLBACK_THEME = { icon: '🏅', gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)', title: 'Strategic Leader' };

/**
 * GameOverSummary — Final screen after Boardroom Showdown.
 * Simulation is definitively over. Player can download report or review scorecard.
 */
export default function GameOverSummary({ data, businessUnits, globalState, history, onReviewScorecard, decisionParadigm, sessionId, onLogout }) {
    const [showInterview, setShowInterview] = useState(false);
    const [interviewAvailable, setInterviewAvailable] = useState(false);
    const [interviewCompleted, setInterviewCompleted] = useState(false);
    const d = data || {};
    // Dynamic theme: prefer backend-provided icon/gradient (supports custom archetypes),
    // else fall back to PROFILES dict, else universal fallback.
    const baseTheme = PROFILES[d.profile] || FALLBACK_THEME;
    const theme = {
        icon: d.profile_icon || baseTheme.icon,
        gradient: d.profile_gradient || baseTheme.gradient,
        title: baseTheme.title,
    };

    const handleDownload = () => {
        // Open the scorecard which has the full report download capability
        if (onReviewScorecard) {
            onReviewScorecard();
        }
    };

    // Check if CEO Interview is available (polls every 10s so late-enable by facilitator is picked up)
    useEffect(() => {
        if (!sessionId) return;
        const API = process.env.NEXT_PUBLIC_API_URL || '';
        let cancelled = false;

        const checkAvailability = () => {
            fetch(`${API}/api/simulations/${sessionId}/ceo-interview/questions`)
                .then(r => {
                    if (!cancelled && r.ok) setInterviewAvailable(true);
                })
                .catch(() => {});
        };

        checkAvailability(); // immediate check
        const interval = setInterval(checkAvailability, 10_000); // re-check every 10s

        // Check if already completed (from globalState OR data/finalReport flags)
        const flags = globalState?.active_event_flags || {};
        const dataFlags = d || {};
        if (flags.ceo_interview_completed || dataFlags.ceo_interview_completed) {
            setInterviewCompleted(true);
        }

        return () => { cancelled = true; clearInterval(interval); };
    }, [sessionId, globalState]);

    // ── Peer Performance: fetch leaderboard on mount ──────────
    const [peerLeaderboard, setPeerLeaderboard] = useState([]);
    // Balance sheet: use prop or fetch if missing
    const [fetchedBS, setFetchedBS] = useState(null);
    useEffect(() => {
        if (!sessionId || sessionId === 'demo') return;
        let cancelled = false;
        const API = process.env.NEXT_PUBLIC_API_URL || '';
        fetch(`${API}/api/simulations/${sessionId}/peer-leaderboard`)
            .then(r => r.json())
            .then(data => {
                if (!cancelled && data.leaderboard?.length > 0) {
                    setPeerLeaderboard(data.leaderboard);
                }
            })
            .catch(() => {});
        // Fetch balance sheet if not in globalState
        if (!globalState?.balance_sheet?.total_assets) {
            fetch(`${API}/api/simulations/${sessionId}/balance-sheet`)
                .then(r => r.ok ? r.json() : null)
                .then(d => { if (!cancelled && d?.balance_sheet) setFetchedBS(d.balance_sheet); })
                .catch(() => {});
        }
        return () => { cancelled = true; };
    }, [sessionId]);

    return (
        <div className={styles.overlay}>
            <div className={styles.container}>
                {/* Completion Badge */}
                <div className={styles.badge}>SIMULATION COMPLETE</div>

                {/* Hero */}
                <div className={styles.hero} style={{ background: theme.gradient }}>
                    <span className={styles.heroEmoji}>{theme.icon}</span>
                    <h1 className={styles.heroTitle}>{d.profile_title || theme.title}</h1>
                    <p className={styles.heroDesc}>{d.profile_description || 'Your strategic journey has concluded.'}</p>
                </div>

                {/* Final Stats */}
                <div className={styles.statsGrid}>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Terminal Value</span>
                        <span className={styles.statValue}>${((d.terminal_value || 0) / 1_000_000).toFixed(2)}M</span>
                    </div>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Regenerative Multiple</span>
                        <span className={styles.statValue}>{(d.regenerative_multiple || 0).toFixed(2)}×</span>
                    </div>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Rounds Played</span>
                        <span className={styles.statValue}>10</span>
                    </div>
                </div>

                {/* Message */}
                <div className={styles.message}>
                    <h2>📋 Your Board Presentation Is Complete</h2>
                    <p>
                        You have presented your strategic recommendation to the Board of Directors.
                        The simulation is now concluded. You may download your Balanced Scorecard report
                        or review your performance across all 10 rounds.
                    </p>
                </div>

                {/* ── Final Peer Performance Leaderboard ── */}
                {peerLeaderboard.length > 0 && (
                    <div style={{
                        background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(168,85,247,0.05))',
                        border: '1px solid rgba(99,102,241,0.25)',
                        borderRadius: '12px',
                        padding: '1.2rem',
                        marginTop: '0.5rem',
                    }}>
                        <div style={{
                            fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.1em',
                            textTransform: 'uppercase', marginBottom: '0.8rem',
                            display: 'flex', alignItems: 'center', gap: '0.4rem',
                            color: '#818cf8',
                        }}>
                            <span>🏆</span> {peerLeaderboard.some(t => t.isAI) ? 'AI Benchmark Comparison' : 'Final Cohort Leaderboard'}
                            {peerLeaderboard.some(t => t.isAI) && <span style={{ fontSize: '0.68rem', background: 'rgba(245,158,11,0.15)', color: '#fbbf24', padding: '2px 6px', borderRadius: 3, fontWeight: 700, marginLeft: 6 }}>🤖 AI</span>}
                        </div>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                    <th style={{ textAlign: 'left', padding: '6px 8px', color: '#64748b', fontWeight: 700, fontSize: '0.68rem', textTransform: 'uppercase' }}>#</th>
                                    <th style={{ textAlign: 'left', padding: '6px 8px', color: '#64748b', fontWeight: 700, fontSize: '0.68rem', textTransform: 'uppercase' }}>Team</th>
                                    <th style={{ textAlign: 'right', padding: '6px 8px', color: '#64748b', fontWeight: 700, fontSize: '0.68rem', textTransform: 'uppercase' }}>Treasury</th>
                                    <th style={{ textAlign: 'right', padding: '6px 8px', color: '#64748b', fontWeight: 700, fontSize: '0.68rem', textTransform: 'uppercase' }}>Reputation</th>
                                    <th style={{ textAlign: 'right', padding: '6px 8px', color: '#64748b', fontWeight: 700, fontSize: '0.68rem', textTransform: 'uppercase' }}>CO₂</th>
                                    <th style={{ textAlign: 'right', padding: '6px 8px', color: '#64748b', fontWeight: 700, fontSize: '0.68rem', textTransform: 'uppercase' }}>Bonus</th>
                                    <th style={{ textAlign: 'center', padding: '6px 8px', color: '#64748b', fontWeight: 700, fontSize: '0.68rem', textTransform: 'uppercase' }}>Trend</th>
                                </tr>
                            </thead>
                            <tbody>
                                {peerLeaderboard.map(team => (
                                    <tr key={team.rank} style={{
                                        background: team.isYou ? 'rgba(99,102,241,0.12)' : 'transparent',
                                        borderBottom: '1px solid rgba(255,255,255,0.05)',
                                        transition: 'background 0.15s',
                                    }}>
                                        <td style={{ padding: '8px', fontSize: '0.9rem' }}>
                                            {team.rank <= 3 ? ['🥇', '🥈', '🥉'][team.rank - 1] : team.rank}
                                        </td>
                                        <td style={{
                                            padding: '8px', fontWeight: team.isYou ? 800 : 600,
                                            color: team.isYou ? '#a5b4fc' : '#e2e8f0',
                                        }}>
                                            {team.name}
                                            {team.isYou && <span style={{
                                                marginLeft: 8, fontSize: '0.68rem', fontWeight: 800,
                                                background: 'rgba(99,102,241,0.3)', color: '#c7d2fe',
                                                padding: '2px 8px', borderRadius: 4,
                                            }}>YOU</span>}
                                        </td>
                                        <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700, color: '#4ade80', fontFamily: "'JetBrains Mono', monospace" }}>
                                            ${((team.treasury || 0) / 1_000_000).toFixed(1)}M
                                        </td>
                                        <td style={{ padding: '8px', textAlign: 'right', color: '#cbd5e1' }}>
                                            {team.reputation?.toFixed(0) ?? '—'}
                                        </td>
                                        <td style={{ padding: '8px', textAlign: 'right', color: '#94a3b8', fontFamily: "'JetBrains Mono', monospace" }}>
                                            {(team.co2 || 0).toLocaleString()}t
                                        </td>
                                        <td style={{
                                            padding: '8px', textAlign: 'right',
                                            color: (team.bonus_score || 0) > 0 ? '#fbbf24' : '#475569',
                                            fontWeight: 700, fontFamily: "'JetBrains Mono', monospace",
                                        }}>
                                            {(team.bonus_score || 0) > 0 ? `🏅 ${(team.bonus_score || 0).toLocaleString()}` : '–'}
                                        </td>
                                        <td style={{
                                            padding: '8px', textAlign: 'center', fontSize: '0.9rem',
                                            color: team.trend === '↑' ? '#4ade80' : team.trend === '↓' ? '#f87171' : '#94a3b8',
                                        }}>{team.trend}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {/* Your rank highlight */}
                        {(() => {
                            const you = peerLeaderboard.find(t => t.isYou);
                            if (!you) return null;
                            return (
                                <div style={{
                                    marginTop: '0.8rem', padding: '0.6rem 0.8rem', borderRadius: '8px',
                                    background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
                                    fontSize: '0.8rem', fontWeight: 700, color: '#a5b4fc',
                                }}>
                                    <span style={{ fontSize: '1.1rem' }}>{you.rank <= 3 ? ['🥇', '🥈', '🥉'][you.rank - 1] : '🏅'}</span>
                                    You finished <strong style={{ color: '#e2e8f0' }}>#{you.rank}</strong> out of <strong style={{ color: '#e2e8f0' }}>{peerLeaderboard.length}</strong> teams
                                </div>
                            );
                        })()}
                    </div>
                )}

                {/* ── Final Balance Sheet — Statement of Financial Position ── */}
                {(() => {
                    const bs = globalState?.balance_sheet || fetchedBS;
                    if (!bs || !bs.total_assets) return null;

                    const fmtM = (v) => `$${((v || 0) / 1_000_000).toFixed(1)}M`;
                    const fmtK = (v) => Math.abs(v || 0) >= 1_000_000 ? fmtM(v) : `$${((v || 0) / 1_000).toFixed(0)}K`;
                    const ta = bs.tangible_assets || {};
                    const ia = bs.intangible_assets || {};
                    const ca = bs.current_assets || {};
                    const ncl = bs.non_current_liabilities || {};
                    const cl = bs.current_liabilities || {};
                    const totalTangible = Object.values(ta).reduce((s, v) => s + (v || 0), 0);
                    const totalIntangible = Object.values(ia).reduce((s, v) => s + (v || 0), 0);
                    const totalCurrent = Object.values(ca).reduce((s, v) => s + (v || 0), 0);
                    const totalNCL = Object.values(ncl).reduce((s, v) => s + (v || 0), 0);
                    const totalCL = Object.values(cl).reduce((s, v) => s + (v || 0), 0);
                    const totalEquity = (bs.share_capital || 0) + (bs.retained_earnings || 0) + (bs.other_reserves || 0);
                    const deRatio = bs.debt_to_equity || 0;
                    const ndEbitda = bs.net_debt_to_ebitda || 0;
                    const netAssets = bs.net_assets || 0;
                    const strandedExposure = bs.stranded_asset_exposure || 0;
                    const covenantStatus = bs.covenant_status || 'green';
                    const covenantColors = { green: '#10b981', amber: '#f59e0b', red: '#ef4444', breached: '#dc2626' };
                    const covenantLabels = { green: '🟢 Comfortable', amber: '🟡 Watch List', red: '🔴 Breach (Cure Period)', breached: '🚨 Acceleration' };

                    const lineRow = (label, value, opts = {}) => (
                        <div style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            padding: opts.bold ? '6px 0' : '3px 0',
                            borderTop: opts.topBorder ? '1px solid var(--border-subtle, rgba(148,163,184,0.2))' : 'none',
                            borderBottom: opts.bottomBorder ? '2px double var(--border-subtle, rgba(148,163,184,0.3))' : 'none',
                        }}>
                            <span style={{
                                fontSize: opts.bold ? '0.78rem' : '0.74rem',
                                fontWeight: opts.bold ? 800 : 500,
                                color: opts.color || (opts.bold ? 'var(--text-primary, #e2e8f0)' : 'var(--text-secondary, #334155)'),
                                paddingLeft: opts.indent ? 16 : 0,
                            }}>{label}</span>
                            <span style={{
                                fontSize: opts.bold ? '0.82rem' : '0.74rem',
                                fontWeight: opts.bold ? 800 : 600,
                                fontFamily: "'JetBrains Mono', monospace",
                                color: opts.color || (opts.bold ? 'var(--text-primary, #e2e8f0)' : 'var(--text-primary, #1e293b)'),
                            }}>{typeof value === 'number' ? fmtK(value) : value}</span>
                        </div>
                    );

                    const sectionHdr = (label, icon) => (
                        <div style={{
                            fontSize: '0.7rem', fontWeight: 800, textTransform: 'uppercase',
                            letterSpacing: '0.08em', color: 'var(--text-muted, #475569)', marginTop: 14, marginBottom: 6,
                            display: 'flex', alignItems: 'center', gap: 5,
                            borderBottom: '1px solid var(--border-subtle, rgba(148,163,184,0.15))', paddingBottom: 4,
                        }}>{icon} {label}</div>
                    );

                    return (
                        <div style={{
                            background: 'linear-gradient(135deg, rgba(56,189,248,0.06), rgba(99,102,241,0.04))',
                            border: '1px solid rgba(56,189,248,0.2)',
                            borderRadius: '12px',
                            padding: '1.2rem 1.4rem',
                            marginTop: '0.5rem',
                        }}>
                            {/* Header */}
                            <div style={{
                                textAlign: 'center', marginBottom: '0.8rem',
                                borderBottom: '2px solid rgba(56,189,248,0.2)', paddingBottom: '0.5rem',
                            }}>
                                <div style={{
                                    fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.12em',
                                    textTransform: 'uppercase', color: '#38bdf8',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem',
                                }}>
                                    📊 Statement of Financial Position
                                </div>
                                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted, #475569)', marginTop: 2, fontWeight: 500 }}>
                                    Muressons Global Corporation — As at End of Year 5 (Round 10)
                                </div>
                            </div>

                            {/* Summary hero cards */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 12 }}>
                                <div style={{ textAlign: 'center', padding: '8px', borderRadius: 8, background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.15)' }}>
                                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted, #475569)', fontWeight: 700, textTransform: 'uppercase' }}>Total Assets</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 900, color: '#38bdf8', marginTop: 2 }}>{fmtM(bs.total_assets)}</div>
                                </div>
                                <div style={{ textAlign: 'center', padding: '8px', borderRadius: 8, background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.12)' }}>
                                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted, #475569)', fontWeight: 700, textTransform: 'uppercase' }}>Total Liabilities</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 900, color: '#f87171', marginTop: 2 }}>{fmtM(bs.total_liabilities)}</div>
                                </div>
                                <div style={{ textAlign: 'center', padding: '8px', borderRadius: 8, background: netAssets >= 0 ? 'rgba(74,222,128,0.08)' : 'rgba(239,68,68,0.08)', border: `1px solid ${netAssets >= 0 ? 'rgba(74,222,128,0.15)' : 'rgba(239,68,68,0.15)'}` }}>
                                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted, #475569)', fontWeight: 700, textTransform: 'uppercase' }}>Net Assets</div>
                                    <div style={{ fontSize: '1rem', fontWeight: 900, color: netAssets >= 0 ? '#4ade80' : '#ef4444', marginTop: 2 }}>{fmtM(netAssets)}</div>
                                </div>
                            </div>

                            {/* ═══ DETAILED LINE ITEMS ═══ */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 24px' }}>
                                {/* LEFT COLUMN: ASSETS */}
                                <div>
                                    {sectionHdr('Non-Current Assets', '🏭')}
                                    {lineRow('Property, Plant & Equipment', ta.property_plant_equipment, { indent: true })}
                                    {lineRow('Right-of-Use Assets (IFRS 16)', ta.right_of_use_assets, { indent: true })}
                                    {lineRow('Inventory', ta.inventory, { indent: true })}
                                    {lineRow('Total Tangible', totalTangible, { bold: true, topBorder: true })}

                                    {sectionHdr('Intangible Assets', '💎')}
                                    {lineRow('Brand Value', ia.brand_value, { indent: true })}
                                    {lineRow('Intellectual Property', ia.intellectual_property, { indent: true })}
                                    {lineRow('Goodwill', ia.goodwill, { indent: true })}
                                    {lineRow('Social Licence (IAS 38)', ia.social_licence_asset, { indent: true })}
                                    {lineRow('Reputation Capital', ia.reputation_asset, { indent: true })}
                                    {lineRow('Total Intangible', totalIntangible, { bold: true, topBorder: true })}

                                    {sectionHdr('Current Assets', '💵')}
                                    {lineRow('Cash & Equivalents', ca.cash_and_equivalents, { indent: true, color: (ca.cash_and_equivalents || 0) < 0 ? '#f87171' : '#4ade80' })}
                                    {lineRow('Trade Receivables', ca.trade_receivables, { indent: true })}
                                    {lineRow('Prepayments', ca.prepayments, { indent: true })}
                                    {lineRow('Total Current', totalCurrent, { bold: true, topBorder: true })}

                                    <div style={{ marginTop: 8 }}>
                                        {lineRow('TOTAL ASSETS', bs.total_assets, { bold: true, topBorder: true, bottomBorder: true, color: '#38bdf8' })}
                                    </div>
                                </div>

                                {/* RIGHT COLUMN: LIABILITIES + EQUITY */}
                                <div>
                                    {sectionHdr('Non-Current Liabilities', '🏦')}
                                    {lineRow('Revolving Credit Facility', ncl.revolving_credit_facility, { indent: true })}
                                    {lineRow('Green Bonds', ncl.green_bonds_outstanding, { indent: true, color: (ncl.green_bonds_outstanding || 0) > 0 ? '#10b981' : undefined })}
                                    {lineRow('Environmental Provisions', ncl.environmental_provisions, { indent: true })}
                                    {lineRow('Decommissioning', ncl.decommissioning_obligations, { indent: true })}
                                    {lineRow('Lease Liabilities (IFRS 16)', ncl.lease_liabilities, { indent: true })}
                                    {lineRow('Total Non-Current', totalNCL, { bold: true, topBorder: true })}

                                    {sectionHdr('Current Liabilities', '📋')}
                                    {lineRow('Trade Payables', cl.trade_payables, { indent: true })}
                                    {lineRow('Tax Provisions', cl.tax_provisions, { indent: true })}
                                    {lineRow('Accrued Remediation', cl.accrued_remediation, { indent: true })}
                                    {lineRow('Short-Term Debt', cl.short_term_debt, { indent: true })}
                                    {lineRow('Total Current', totalCL, { bold: true, topBorder: true })}

                                    {sectionHdr("Shareholders' Equity", '🏛️')}
                                    {lineRow('Share Capital', bs.share_capital, { indent: true })}
                                    {lineRow('Retained Earnings', bs.retained_earnings, { indent: true, color: (bs.retained_earnings || 0) < 0 ? '#f87171' : undefined })}
                                    {lineRow('Other Reserves', bs.other_reserves, { indent: true })}
                                    {lineRow('TOTAL EQUITY', totalEquity, { bold: true, topBorder: true, bottomBorder: true, color: '#a78bfa' })}
                                </div>
                            </div>

                            {/* ═══ KEY RATIOS + COVENANT ═══ */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 8, marginTop: 14 }}>
                                {[
                                    { label: 'D/E Ratio', value: `${deRatio.toFixed(2)}×`, good: deRatio < 2.0, icon: '⚖️' },
                                    { label: 'ND/EBITDA', value: `${ndEbitda.toFixed(2)}×`, good: ndEbitda <= 2.5, icon: '📐' },
                                    { label: 'Stranded Exposure', value: fmtM(strandedExposure), good: strandedExposure < bs.total_assets * 0.15, icon: '⚠️' },
                                    { label: 'Brand Value', value: fmtM(ia.brand_value), good: (ia.brand_value || 0) > 15_000_000, icon: '💎' },
                                ].map((r, i) => (
                                    <div key={i} style={{
                                        textAlign: 'center', padding: '6px 8px', borderRadius: 8,
                                        background: r.good ? 'rgba(74,222,128,0.06)' : 'rgba(239,68,68,0.06)',
                                        border: `1px solid ${r.good ? 'rgba(74,222,128,0.12)' : 'rgba(239,68,68,0.12)'}`,
                                    }}>
                                        <div style={{ fontSize: '0.88rem' }}>{r.icon}</div>
                                        <div style={{ fontSize: '0.62rem', color: 'var(--text-muted, #475569)', fontWeight: 700, textTransform: 'uppercase', marginTop: 2 }}>{r.label}</div>
                                        <div style={{ fontSize: '0.82rem', fontWeight: 800, color: r.good ? '#4ade80' : '#f87171', fontFamily: "'JetBrains Mono', monospace", marginTop: 2 }}>{r.value}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Covenant Status */}
                            <div style={{
                                marginTop: 10, padding: '6px 10px', borderRadius: 6,
                                background: `${covenantColors[covenantStatus]}12`,
                                border: `1px solid ${covenantColors[covenantStatus]}30`,
                                fontSize: '0.72rem', fontWeight: 700,
                                color: covenantColors[covenantStatus],
                                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                            }}>
                                <span>Debt Covenant Status:</span>
                                <span>{covenantLabels[covenantStatus] || covenantStatus}</span>
                            </div>

                            {/* Net Assets Trend */}
                            {bs.balance_sheet_history?.length > 1 && (
                                <div style={{ marginTop: 12 }}>
                                    <div style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>Net Assets Trend (10 Rounds)</div>
                                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 40 }}>
                                        {bs.balance_sheet_history.map((h, i) => {
                                            const maxNA = Math.max(...bs.balance_sheet_history.map(x => Math.abs(x.net_assets || 1)));
                                            const pct = Math.max(5, Math.abs(h.net_assets || 0) / maxNA * 100);
                                            const isNeg = (h.net_assets || 0) < 0;
                                            return (
                                                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                                                    <div style={{
                                                        width: '100%', height: `${pct}%`, minHeight: 4, borderRadius: 3,
                                                        background: isNeg ? '#ef4444' : '#38bdf8',
                                                        opacity: 0.5 + (i / bs.balance_sheet_history.length) * 0.5,
                                                        transition: 'height 0.5s ease',
                                                    }} title={`R${h.round}: ${fmtM(h.net_assets)}`} />
                                                    <span style={{ fontSize: '0.5rem', color: '#475569' }}>R{h.round}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })()}

                {/* ── 3 Key Insights ── */}
                {history && history.length > 0 && (() => {
                    // Build per-round deltas from actual history array.
                    // History entries may store absolute treasury values; compute delta from consecutive rounds.
                    const ROUND_NAMES = {
                        1: 'ESG Audit', 2: 'Double Materiality', 3: 'Scope 3 Emissions',
                        4: 'Contagion Crisis', 5: 'Climate Event', 6: 'AI Bias Scandal',
                        7: 'Circular Economy', 8: 'Water Scarcity', 9: 'Just Transition',
                        10: 'Grand Finale',
                    };

                    const roundDeltas = history.map((h, i) => {
                        // Support explicit delta field OR derive from adjacent treasury values
                        let delta = h?.treasury_delta ?? null;
                        if (delta === null) {
                            const curr = h?.treasury ?? h?.corporate_treasury ?? 0;
                            const prev = i > 0 ? (history[i - 1]?.treasury ?? history[i - 1]?.corporate_treasury ?? curr) : curr;
                            delta = curr - prev;
                        }
                        // Choice label: prefer explicit title, then choice_selected, then raw choice key
                        const choiceLabel = h?.choice_title || h?.choice_label ||
                            (h?.choice_selected ? h.choice_selected.replace('option_', 'Option ').toUpperCase() : null) ||
                            h?.choice || null;
                        return {
                            round: i + 1,
                            treasury_delta: delta,
                            choice_title: choiceLabel,
                        };
                    }).filter(r => r.round <= 10 && r.choice_title); // only rounds with real decisions

                    // If no rounds have labelled choices yet, skip the section
                    if (roundDeltas.length === 0) return null;

                    const best = roundDeltas.reduce((a, b) => a.treasury_delta > b.treasury_delta ? a : b, roundDeltas[0]);
                    const worst = roundDeltas.reduce((a, b) => a.treasury_delta < b.treasury_delta ? a : b, roundDeltas[0]);

                    const insights = [
                        {
                            icon: '🏆',
                            title: 'Best Decision',
                            text: `Round ${best.round} (${ROUND_NAMES[best.round] || '—'}): "${best.choice_title}" generated ${best.treasury_delta >= 0 ? '+' : ''}$${(best.treasury_delta / 1_000_000).toFixed(1)}M in treasury impact.`,
                            color: '#10b981',
                        },
                        {
                            icon: '💸',
                            title: 'Most Costly Mistake',
                            text: `Round ${worst.round} (${ROUND_NAMES[worst.round] || '—'}): "${worst.choice_title}" cost $${(Math.abs(worst.treasury_delta) / 1_000_000).toFixed(1)}M in treasury impact.`,
                            color: '#ef4444',
                        },
                        {
                            icon: '🔮',
                            title: 'Road Not Taken',
                            text: `In Round ${worst.round}, an alternative approach could have changed your trajectory. The choices we don't make often define us as much as the ones we do.`,
                            color: '#a78bfa',
                        },
                    ];

                    return (
                        <div style={{
                            background: '#111827',
                            border: '1px solid #1e293b',
                            borderRadius: '12px',
                            padding: '1.2rem',
                            marginTop: '0.5rem',
                        }}>
                            <div style={{
                                fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.1em',
                                textTransform: 'uppercase', color: '#e2e8f0', marginBottom: '0.8rem',
                                display: 'flex', alignItems: 'center', gap: '0.4rem',
                            }}>
                                <span>💡</span> 3 Key Insights
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                                {insights.map((ins, i) => (
                                    <div key={i} style={{
                                        display: 'flex', alignItems: 'flex-start', gap: '0.6rem',
                                        padding: '0.7rem 0.9rem', borderRadius: '8px',
                                        background: '#0f172a',
                                        borderLeft: `3px solid ${ins.color}`,
                                    }}>
                                        <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{ins.icon}</span>
                                        <div>
                                            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: ins.color, marginBottom: '0.2rem' }}>
                                                {ins.title}
                                            </div>
                                            <div style={{ fontSize: '0.8rem', color: '#e2e8f0', lineHeight: 1.55, fontWeight: 500 }}>
                                                {ins.text}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })()}

                {/* ── Advanced Climate Engine Insights ── */}
                {decisionParadigm === 'advanced_climate' && (() => {
                    const gs = globalState || {};
                    const greenFund = gs.green_fund_balance ?? d.green_fund_balance ?? 0;
                    const avgCI = gs.avg_carbon_intensity ?? d.avg_carbon_intensity ?? null;
                    const tippingPoint = gs.tipping_point_active ?? d.tipping_point_active ?? false;
                    const carbonFeesPaid = gs.total_carbon_fees_paid ?? d.total_carbon_fees_paid ?? null;

                    // Climate verdict
                    let verdict, verdictColor, verdictIcon;
                    if (tippingPoint) {
                        verdict = 'Tipping Point — Irreversible Threshold Breached';
                        verdictColor = '#ef4444';
                        verdictIcon = '🌡️';
                    } else if (avgCI !== null && avgCI < 50) {
                        verdict = 'Climate Leader — Exemplary Decarbonisation';
                        verdictColor = '#10b981';
                        verdictIcon = '🌱';
                    } else if (avgCI !== null && avgCI < 70) {
                        verdict = 'Managed Retreat — Avoided Tipping Point';
                        verdictColor = '#f59e0b';
                        verdictIcon = '🌿';
                    } else {
                        verdict = 'High Carbon — Significant Transition Risk';
                        verdictColor = '#f97316';
                        verdictIcon = '💨';
                    }

                    return (
                        <div style={{
                            background: 'linear-gradient(135deg, rgba(16,185,129,0.06), rgba(6,182,212,0.06))',
                            border: '1px solid rgba(16,185,129,0.2)',
                            borderRadius: '12px',
                            padding: '1.2rem',
                            marginTop: '0.5rem',
                        }}>
                            {/* Header */}
                            <div style={{
                                fontSize: '0.68rem', fontWeight: 800, letterSpacing: '0.12em',
                                textTransform: 'uppercase', marginBottom: '0.8rem',
                                display: 'flex', alignItems: 'center', gap: '0.4rem',
                                color: '#10b981',
                            }}>
                                <span>🌍</span> Advanced Climate Engine — Final Report
                            </div>

                            {/* Prominent Green Transition Fund Banner */}
                            <div style={{
                                background: 'linear-gradient(135deg, rgba(16,185,129,0.1), rgba(52,211,153,0.15))',
                                border: '1px solid rgba(16,185,129,0.3)',
                                borderRadius: '8px',
                                padding: '1rem',
                                marginBottom: '1rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                                    <span style={{ fontSize: '2rem' }}>🌱</span>
                                    <div>
                                        <div style={{ fontSize: '0.75rem', fontWeight: 800, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                            Green Transition Fund
                                        </div>
                                        <div style={{ fontSize: '0.85rem', color: '#6ee7b7', marginTop: '0.2rem' }}>
                                            Capital accumulated for decarbonisation initiatives
                                        </div>
                                    </div>
                                </div>
                                <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#10b981' }}>
                                    ${(greenFund / 1_000_000).toFixed(2)}M
                                </div>
                            </div>

                            {/* Climate metrics grid */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '0.8rem' }}>
                                {[
                                    { label: '💨 Avg Carbon Intensity', value: avgCI !== null ? `${avgCI.toFixed(1)} t/BU` : '—', color: avgCI !== null && avgCI >= 70 ? '#ef4444' : '#6ee7b7' },
                                    { label: '🌡️ Tipping Point', value: tippingPoint ? 'BREACHED ⚠️' : 'Avoided ✓', color: tippingPoint ? '#ef4444' : '#10b981' },
                                    { label: '💰 Total Carbon Fees', value: carbonFeesPaid !== null ? `$${(carbonFeesPaid / 1_000_000).toFixed(2)}M` : '—', color: '#94a3b8' },
                                ].map((m, i) => (
                                    <div key={i} style={{
                                        background: 'rgba(255,255,255,0.03)',
                                        border: '1px solid rgba(148,163,184,0.08)',
                                        borderRadius: '8px',
                                        padding: '0.6rem 0.8rem',
                                    }}>
                                        <div style={{ fontSize: '0.68rem', color: '#64748b', marginBottom: '0.2rem' }}>{m.label}</div>
                                        <div style={{ fontSize: '0.88rem', fontWeight: 800, color: m.color }}>{m.value}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Verdict */}
                            <div style={{
                                display: 'flex', alignItems: 'center', gap: '0.6rem',
                                padding: '0.6rem 0.8rem', borderRadius: '8px',
                                background: `${verdictColor}15`,
                                border: `1px solid ${verdictColor}40`,
                            }}>
                                <span style={{ fontSize: '1.2rem' }}>{verdictIcon}</span>
                                <div>
                                    <div style={{ fontSize: '0.68rem', fontWeight: 800, color: verdictColor, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                                        Climate Verdict
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '0.1rem' }}>
                                        {verdict}
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })()}

                {/* ── Pathway Discovery Debrief (Hardening Phase) ── */}
                {d.pathway_discovery && (() => {
                    const pd = d.pathway_discovery;
                    const chain = pd.foreshadowing_chain || [];
                    return (
                        <div style={{
                            background: '#111827',
                            border: '1px solid #1e293b',
                            borderRadius: '12px',
                            padding: '1.2rem',
                            marginTop: '0.5rem',
                        }}>
                            <div style={{
                                fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.1em',
                                textTransform: 'uppercase', marginBottom: '0.8rem',
                                display: 'flex', alignItems: 'center', gap: '0.4rem',
                                color: '#c4b5fd',
                            }}>
                                <span>🗺️</span> Pathway Discovery — How Your Ending Was Shaped
                            </div>

                            {/* Pathway Name + Description */}
                            <div style={{
                                background: '#0f172a',
                                border: '1px solid #334155',
                                borderRadius: '8px',
                                padding: '1rem',
                                marginBottom: '0.8rem',
                            }}>
                                <div style={{ fontSize: '0.92rem', fontWeight: 800, color: '#c4b5fd', marginBottom: '0.3rem' }}>
                                    {pd.pathway_name || 'Unknown Pathway'}
                                </div>
                                <div style={{ fontSize: '0.82rem', color: '#e2e8f0', lineHeight: 1.55 }}>
                                    {pd.pathway_description || 'Your decisions shaped a unique ending pathway.'}
                                </div>
                            </div>

                            {/* Foreshadowing Chain */}
                            {chain.length > 0 && (
                                <>
                                    <div style={{
                                        fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
                                        color: '#94a3b8', letterSpacing: '0.08em', marginBottom: '0.5rem',
                                    }}>
                                        Decision Chain — Rounds {chain[0]?.round || '?'} to {chain[chain.length - 1]?.round || '?'}
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                        {chain.map((step, i) => (
                                            <div key={i} style={{
                                                display: 'flex', alignItems: 'flex-start', gap: '0.6rem',
                                                padding: '0.5rem 0.7rem', borderRadius: '6px',
                                                background: '#0f172a',
                                                borderLeft: `3px solid ${i === chain.length - 1 ? '#a78bfa' : '#475569'}`,
                                            }}>
                                                <span style={{
                                                    flexShrink: 0, width: 24, height: 24, borderRadius: '50%',
                                                    background: i === chain.length - 1 ? 'rgba(167,139,250,0.2)' : 'rgba(255,255,255,0.05)',
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    fontSize: '0.65rem', fontWeight: 800, color: i === chain.length - 1 ? '#a78bfa' : '#64748b',
                                                    border: i === chain.length - 1 ? '1px solid rgba(167,139,250,0.4)' : '1px solid rgba(255,255,255,0.1)',
                                                }}>R{step.round}</span>
                                                <div>
                                                    <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#e2e8f0' }}>
                                                        {step.event || step.headline || `Decision in Round ${step.round}`}
                                                    </div>
                                                    {step.detail && (
                                                        <div style={{ fontSize: '0.65rem', color: '#94a3b8', marginTop: '0.1rem' }}>
                                                            {step.detail}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            )}

                            {/* Pedagogical Note */}
                            {pd.pedagogical_note && (
                                <div style={{
                                    marginTop: '0.8rem', padding: '0.6rem 0.8rem', borderRadius: '6px',
                                    background: 'rgba(168,85,247,0.06)',
                                    border: '1px solid rgba(168,85,247,0.2)',
                                    fontSize: '0.72rem', color: '#c4b5fd', lineHeight: 1.5,
                                    fontStyle: 'italic',
                                }}>
                                    <strong>💡 Facilitator Note:</strong> {pd.pedagogical_note}
                                </div>
                            )}
                        </div>
                    );
                })()}

                {/* ── Side Track Results ── */}
                {(() => {
                    const flags = globalState?.active_event_flags || {};
                    const SIDE_TRACKS = [
                        { id: 'supply_chain', label: 'Supply Chain Deep Dive', icon: '🔗', scoreKey: 'supply_chain_final_score', gradeKey: 'supply_chain_grade', archetypeKey: 'supply_chain_archetype', completedKey: 'supply_chain_track_completed', mrBonusKey: 'sc_track_mr_bonus', mrPenaltyKey: 'sc_track_mr_penalty' },
                        { id: 'ethics', label: 'Ethics & Sustainability', icon: '⚖️', scoreKey: 'ethics_final_score', gradeKey: 'ethics_grade', archetypeKey: 'ethics_archetype', completedKey: 'ethics_track_completed', mrBonusKey: 'es_track_mr_bonus', mrPenaltyKey: 'es_track_mr_penalty' },
                        { id: 'stakeholder', label: 'Stakeholder Management', icon: '🤝', scoreKey: 'stakeholder_final_score', gradeKey: 'stakeholder_grade', archetypeKey: 'stakeholder_archetype', completedKey: 'stakeholder_track_completed', mrBonusKey: 'sm_track_mr_bonus', mrPenaltyKey: 'sm_track_mr_penalty' },
                        { id: 'reporting', label: 'Sustainability Reporting', icon: '📊', scoreKey: 'reporting_final_score', gradeKey: 'reporting_grade', archetypeKey: 'reporting_archetype', completedKey: 'reporting_track_completed', mrBonusKey: 'sr_track_mr_bonus', mrPenaltyKey: 'sr_track_mr_penalty' },
                    ];

                    const completedTracks = SIDE_TRACKS.filter(t => flags[t.completedKey]);
                    if (completedTracks.length === 0) return null;

                    const gradeColors = { 'A+': '#10b981', 'A': '#34d399', 'B': '#3b82f6', 'C': '#f59e0b', 'D': '#f97316', 'F': '#ef4444' };

                    return (
                        <div style={{
                            background: 'linear-gradient(135deg, rgba(99,102,241,0.06), rgba(0,229,195,0.06))',
                            border: '1px solid rgba(99,102,241,0.2)',
                            borderRadius: '12px',
                            padding: '1.2rem',
                            marginTop: '0.5rem',
                        }}>
                            <div style={{
                                fontSize: '0.68rem', fontWeight: 800, letterSpacing: '0.12em',
                                textTransform: 'uppercase', marginBottom: '0.8rem',
                                display: 'flex', alignItems: 'center', gap: '0.4rem',
                                color: '#818cf8',
                            }}>
                                <span>🛤️</span> Side Track Results
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Math.min(completedTracks.length, 2)}, 1fr)`, gap: '0.6rem' }}>
                                {completedTracks.map(t => {
                                    const score = flags[t.scoreKey] || 0;
                                    const grade = flags[t.gradeKey] || '—';
                                    const archetype = flags[t.archetypeKey] || 'Unknown';
                                    const mrBonus = flags[t.mrBonusKey];
                                    const mrPenalty = flags[t.mrPenaltyKey];
                                    const gc = gradeColors[grade] || '#94a3b8';
                                    return (
                                        <div key={t.id} style={{
                                            background: 'rgba(255,255,255,0.03)',
                                            border: '1px solid rgba(148,163,184,0.08)',
                                            borderRadius: '10px',
                                            padding: '0.8rem 1rem',
                                            display: 'flex', flexDirection: 'column', gap: '0.4rem',
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                                    <span style={{ fontSize: '1rem' }}>{t.icon}</span>
                                                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#e2e8f0' }}>{t.label}</span>
                                                </div>
                                                <span style={{
                                                    fontSize: '1rem', fontWeight: 900,
                                                    color: gc, fontFamily: "'JetBrains Mono', monospace",
                                                }}>{grade}</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                <span style={{ fontSize: '0.65rem', color: '#64748b' }}>{archetype}</span>
                                                <span style={{ fontSize: '0.78rem', fontWeight: 800, color: gc, fontFamily: "'JetBrains Mono', monospace" }}>{score.toFixed(1)}/100</span>
                                            </div>
                                            {/* Score bar */}
                                            <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
                                                <div style={{ height: '100%', width: `${Math.min(100, score)}%`, background: gc, borderRadius: 2, transition: 'width 0.5s' }} />
                                            </div>
                                            {/* M_R impact */}
                                            {(mrBonus || mrPenalty) && (
                                                <div style={{
                                                    fontSize: '0.68rem', fontWeight: 700,
                                                    color: mrBonus ? '#4ade80' : '#f87171',
                                                    display: 'flex', alignItems: 'center', gap: '0.3rem',
                                                }}>
                                                    <span>{mrBonus ? '📈' : '📉'}</span>
                                                    M_R Impact: {mrBonus ? `+${(mrBonus * 100).toFixed(0)}%` : `${(mrPenalty * 100).toFixed(0)}%`}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    );
                })()}

                {/* Actions */}
                <div className={styles.actions}>
                    {interviewAvailable && !interviewCompleted && (
                        <button
                            className={styles.primaryBtn}
                            onClick={() => setShowInterview(true)}
                            style={{
                                background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                                boxShadow: '0 4px 16px rgba(99,102,241,0.3)',
                            }}
                        >
                            🎤 CEO Interview & Assessment
                        </button>
                    )}
                    {interviewCompleted && (
                        <button
                            className={styles.primaryBtn}
                            onClick={() => setShowInterview(true)}
                            style={{
                                background: 'linear-gradient(135deg, #10b981, #059669)',
                            }}
                        >
                            ✅ View Interview Assessment
                        </button>
                    )}
                    <button className={styles.primaryBtn} onClick={onReviewScorecard}>
                        📊 Review Balanced Scorecard
                    </button>
                    <StudentReportExport
                        data={d}
                        globalState={globalState}
                        history={history}
                        businessUnits={businessUnits}
                        sessionId={sessionId}
                    />
                    <button className={styles.secondaryBtn} onClick={handleDownload}>
                        📥 Download Report (PDF)
                    </button>
                    {onLogout && (
                        <button className={styles.outlineBtn} onClick={() => { if (window.confirm('Log out? Your progress is saved and you can return anytime.')) onLogout(); }}>
                            🚪 Logout
                        </button>
                    )}
                </div>

                {/* CEO Interview Modal */}
                {showInterview && (
                    <CEOInterview
                        sessionId={sessionId}
                        onClose={() => setShowInterview(false)}
                        onComplete={() => setInterviewCompleted(true)}
                    />
                )}

                {/* Footer */}
                <div className={styles.footer}>
                    <p>Muressons Global Corporation — Sustainability Strategy Simulation</p>
                    <p>© Year 3 Board of Directors Meeting</p>
                </div>
            </div>
        </div>
    );
}
