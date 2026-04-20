'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, YAxis } from 'recharts';
import styles from './InvestmentMatrix.module.css';
import { Abbr } from './Glossary';

const BU_META = {
    pharma: { label: 'Pharma', icon: '💊', accent: '#10b981' },
    electronics: { label: 'Electronics', icon: '🔌', accent: '#3b82f6' },
    consumer_goods: { label: 'Consumer Goods', icon: '🛒', accent: '#f59e0b' },
    software: { label: 'Software', icon: '💻', accent: '#8b5cf6' },
    // Healthcare Edition
    hospitals: { label: 'Hospitals', icon: '🏥', accent: '#ef4444' },
    clinics: { label: 'Primary Care Clinics', icon: '🩺', accent: '#10b981' },
    specialised_care: { label: 'Specialised Care', icon: '🔬', accent: '#8b5cf6' },
    telehealth: { label: 'Digital Health', icon: '📱', accent: '#0ea5e9' },
};

/**
 * InvestmentMatrix — Centre console with 4 mutually exclusive sliders.
 * Allocations deduct from the Corporate Strategic Fund (CSF) pool.
 *
 * Props:
 *  - csfPool:       total available funds (CSF from global treasury)
 *  - businessUnits: array of BU objects
 *  - allocations:   { [bu_id]: number } controlled externally
 *  - onAllocationsChange: (newAllocations) => void
 */
export default function InvestmentMatrix({
    csfPool = 0,
    globalState = {},
    businessUnits = [],
    allocations = {},
    onAllocationsChange,
    historyData = []
}) {
    const [csrdIssues, setCsrdIssues] = useState([]);

    // Fetch materiality issues so we can display funded ones
    useEffect(() => {
        const fetchIssues = async () => {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/materiality-config`);
                if (res.ok) {
                    const data = await res.json();
                    setCsrdIssues(data.issues || []);
                }
            } catch (err) {
                console.error("Failed to load generic materiality config for matrix", err);
            }
        };
        fetchIssues();
    }, []);

    const fundedIssueIds = globalState?.materiality_budget_allocated || [];
    const fundedIssues = csrdIssues.filter(i => fundedIssueIds.includes(i.id));

    const totalAllocated = useMemo(
        () => Object.values(allocations).reduce((s, v) => s + v, 0),
        [allocations]
    );

    const remaining = useMemo(
        () => Math.max(0, csfPool - totalAllocated),
        [csfPool, totalAllocated]
    );

    const handleSlider = useCallback(
        (buId, rawValue) => {
            const value = parseFloat(rawValue);
            const otherTotal = totalAllocated - (allocations[buId] || 0);

            // Allow them to theoretically borrow up to 30% of total treasury
            const absoluteMax = (globalState?.corporate_treasury || 50_000_000) * 0.3;
            const maxAvailable = Math.max(absoluteMax, csfPool) - otherTotal;

            const clamped = Math.min(value, Math.max(0, maxAvailable));

            onAllocationsChange?.({
                ...allocations,
                [buId]: Math.round(clamped * 100) / 100,
            });
        },
        [allocations, totalAllocated, csfPool, onAllocationsChange]
    );

    const pctUsed = csfPool > 0 ? ((totalAllocated / csfPool) * 100) : 0;

    return (
        <section className={styles.matrix}>
            {/* Pool summary */}
            <div className={styles.poolHeader}>
                <div className={styles.poolTitle}>
                    <span className={styles.poolIcon}>🏦</span>
                    <h2>Investment Matrix</h2>
                </div>
                <div className={styles.poolStats}>
                    <div className={styles.statBlock}>
                        <span className={styles.statLabel}><Abbr term="CSF">CSF Pool</Abbr></span>
                        <span className={styles.statValue}>
                            ${(csfPool / 1_000_000).toFixed(1)}M
                        </span>
                    </div>
                    <div className={styles.statBlock}>
                        <span className={styles.statLabel}>Allocated</span>
                        <span className={`${styles.statValue} ${styles.allocated}`}>
                            ${(totalAllocated / 1_000_000).toFixed(1)}M
                        </span>
                    </div>
                    <div className={styles.statBlock}>
                        <span className={styles.statLabel}>Remaining</span>
                        <span
                            className={`${styles.statValue} ${remaining < csfPool * 0.1 ? styles.low : ''
                                }`}
                        >
                            ${(remaining / 1_000_000).toFixed(1)}M
                        </span>
                    </div>
                </div>
                {/* Master progress */}
                <div className={styles.masterTrack}>
                    <div
                        className={styles.masterFill}
                        style={{ width: `${Math.min(100, pctUsed)}%` }}
                    />
                    {pctUsed > 100 && (
                        <div
                            className={`${styles.masterFill} ${styles.masterFillOver}`}
                            style={{ width: `${Math.min(100, pctUsed - 100)}%` }}
                        />
                    )}
                </div>

                {/* Warning for Over-allocation (Loan Required) */}
                {totalAllocated > csfPool && (
                    <div className={styles.loanWarning}>
                        <span className={styles.loanIcon}>⚠️</span>
                        <span>
                            Loan Required: <span className={styles.loanAmount}>${((totalAllocated - csfPool) / 1_000_000).toFixed(2)}M</span>
                            <span style={{ color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                                at {(globalState?.active_event_flags?.loan_interest_rate * 100 || 12).toFixed(1)}% interest per round
                            </span>
                        </span>
                    </div>
                )}
            </div>

            {/* BU Sliders */}
            <div className={styles.sliders}>
                {businessUnits.map((bu, i) => {
                    const meta = BU_META[bu.bu_id] || { label: bu.bu_id, icon: '📊', accent: '#6366f1' };
                    const alloc = allocations[bu.bu_id] || 0;
                    const sliderMax = Math.max((globalState?.corporate_treasury || 50_000_000) * 0.3, csfPool);
                    const pct = csfPool > 0 ? (alloc / csfPool) * 100 : 0;
                    // thumbPct must match the browser's thumb position: value / max * 100
                    const thumbPct = sliderMax > 0 ? (alloc / sliderMax) * 100 : 0;

                    // Find issues that target this BU
                    const buFundedIssues = fundedIssues.filter(issue =>
                        issue.affected_bu_1 === bu.bu_id || issue.affected_bu_2 === bu.bu_id
                    );

                    return (
                        <div
                            key={bu.bu_id}
                            className={styles.sliderCard}
                            style={{
                                '--bu-accent': meta.accent,
                                animationDelay: `${i * 100}ms`,
                            }}
                        >
                            <div className={styles.sliderHeader}>
                                <span className={styles.buIcon}>{meta.icon}</span>
                                <div className={styles.buInfo}>
                                    <span className={styles.buLabel}>{meta.label}</span>
                                    <span className={styles.buRevenue} title="Revenue — total income generated by this business unit">
                                        Rev: ${(bu.revenue_base / 1_000_000).toFixed(1)}M
                                    </span>
                                </div>
                                
                                <div style={{ flex: 1, height: 26, marginLeft: 10, marginRight: 10 }}>
                                    {historyData.length > 0 && (
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={historyData.map(h => {
                                                const hbu = h.business_units?.find(b => b.bu_id === bu.bu_id);
                                                return { val: hbu ? hbu.revenue_base : 0 };
                                            })}>
                                                <YAxis domain={['dataMin', 'dataMax']} hide />
                                                <Line type="monotone" dataKey="val" stroke={meta.accent} strokeWidth={1.5} dot={false} isAnimationActive={false} />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    )}
                                </div>

                                <span className={styles.allocAmount}>
                                    ${(alloc / 1_000_000).toFixed(2)}M
                                </span>
                            </div>

                            <div className={styles.sliderRow}>
                                <input
                                    type="range"
                                    id={`slider-${bu.bu_id}`}
                                    min={0}
                                    max={sliderMax}
                                    step={100_000}
                                    value={alloc}
                                    onChange={(e) => handleSlider(bu.bu_id, e.target.value)}
                                    className={styles.slider}
                                    style={{
                                        '--pct': `${thumbPct}%`,
                                        '--accent': meta.accent,
                                    }}
                                />
                            </div>

                            {/* P1: Context Scorecard */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', borderTop: '1px solid rgba(226, 232, 240, 0.1)', paddingTop: '0.4rem' }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Opex Base</span>
                                    <span style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>${(bu.opex_base / 1_000_000).toFixed(1)}M</span>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Margin</span>
                                    <span style={{ fontSize: '0.65rem', fontWeight: 600, color: bu.revenue_base > bu.opex_base ? '#10b981' : '#ef4444', fontFamily: 'JetBrains Mono, monospace' }}>
                                        {((bu.revenue_base - bu.opex_base) / bu.revenue_base * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Social Lic.</span>
                                    <span style={{ fontSize: '0.65rem', fontWeight: 600, color: bu.social_license_score < 40 ? '#ef4444' : 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
                                        {Math.round(bu.social_license_score || 0)}/100
                                    </span>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Gov Risk</span>
                                    <span style={{ fontSize: '0.65rem', fontWeight: 600, color: bu.governance_risk_score > 20 ? '#ef4444' : 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
                                        {Math.round(bu.governance_risk_score || 0)}%
                                    </span>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                                    <span style={{ fontSize: '0.6rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Nat. Debt</span>
                                    <span style={{ fontSize: '0.65rem', fontWeight: 600, color: bu.natural_capital_debt > 0 ? '#f59e0b' : 'var(--text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>
                                        ${(bu.natural_capital_debt / 1_000_000).toFixed(1)}M
                                    </span>
                                </div>
                            </div>


                            <div className={styles.sliderFooter}>
                                <span className={styles.footerLabel}>
                                    {pct.toFixed(1)}% of pool
                                </span>
                                <span className={styles.footerLabel}>
                                    Ratio: {csfPool > 0 ? (alloc / csfPool).toFixed(2) : '0.00'}
                                </span>
                            </div>

                            {/* Render Funded Mitigations for this BU */}
                            {buFundedIssues.length > 0 && (
                                <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'var(--bg-elevated)', borderTop: `2px solid ${meta.accent}`, borderRadius: '0.375rem' }}>
                                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                                        🎯 Funded ESG Mitigations
                                    </div>
                                    <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                        {buFundedIssues.map(issue => {
                                            const sandboxConfig = globalState?.materiality_dictionary_override;
                                            const sandboxIssue = sandboxConfig?.issues?.find(i => i.id === issue.id);
                                            const displayCost = sandboxIssue ? sandboxIssue.mitigation_cost_usd : issue.mitigation_cost_usd;
                                            return (
                                                <li key={issue.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                                                    <span style={{ color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '140px' }} title={issue.title}>
                                                        • {issue.title}
                                                    </span>
                                                    <span style={{ color: 'var(--accent-green, #10b981)', fontWeight: 'bold' }}>
                                                        ${(displayCost / 1_000_000).toFixed(1)}M
                                                    </span>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                </div>
                            )}

                        </div>
                    );
                })}
            </div>
        </section>
    );
}
