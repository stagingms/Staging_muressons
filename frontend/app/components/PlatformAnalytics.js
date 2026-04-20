'use client';
import { useState, useEffect, useMemo } from 'react';
import styles from './PlatformAnalytics.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const TABS = [
    { id: 'heatmap', label: '📊 Decision Heatmap', key: 'decision_heatmap', title: 'Choice distribution matrix showing which strategic options (A, B, C, etc.) were selected in each round across all players. Includes a heatmap grid with counts/percentages and stacked bar charts for visual comparison. Answers: "What are the most popular choices per round?"' },
    { id: 'timing', label: '⏱ Time-to-Decision', key: 'time_to_decision', title: 'Decision speed analytics — how long players take to commit their choices each round. Displays average, median, min, and max times in seconds with horizontal bar visualizations. Answers: "Are players deliberating or rushing?"' },
    { id: 'cohorts', label: '📈 Cohort Comparison', key: 'cohort_comparison', title: 'Plots KPI trajectories side-by-side for multiple cohorts on an SVG line chart. Togglable between Treasury, Reputation, Synergy, and EBITDA metrics. Answers: "How do different cohorts perform against each other over time?"' },
    { id: 'convergence', label: '🔄 Convergence', key: 'convergence_analysis', title: 'Measures strategy similarity using a convergence gauge (0–100%). Tracks choice entropy (bits of unpredictability) and CapEx standard deviation per round. Low entropy = players thinking alike. Answers: "Are teams converging on the same strategy or diversifying?"' },
    { id: 'learning', label: '🎯 Learning Outcomes', key: 'learning_outcomes', title: 'Tracks gamification and engagement: total learning bonuses awarded, manual facilitator awards, badge distribution counts, and bonuses by category. Answers: "How engaged are students and what milestones have they hit?"' },
    { id: 'risk', label: '📉 Risk Exposure', key: 'risk_exposure', title: 'Multi-axis tracking of non-financial risks per cohort over time: Carbon Intensity, Natural Capital Debt, Social License, and Governance Risk. Rendered as vertical bar charts per cohort. Answers: "How are teams managing ESG/sustainability risks?"' },
];

const CHOICE_COLORS = {
    option_a: '#3b82f6', option_b: '#f59e0b', option_c: '#10b981',
    option_d: '#8b5cf6', option_e: '#ef4444',
};

export default function PlatformAnalytics({ visibility = null }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [tab, setTab] = useState('heatmap');

    const load = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/god/analytics`);
            if (res.ok) setData(await res.json());
        } catch {}
        setLoading(false);
    };
    useEffect(() => { load(); }, []);

    // Filter tabs based on visibility (facilitator mode)
    const visibleTabs = useMemo(() => {
        if (!visibility) return TABS; // God Mode sees all
        return TABS.filter(t => visibility[t.key] !== false);
    }, [visibility]);

    if (loading) return <div className={styles.loading}>Loading analytics…</div>;
    if (!data) return <div className={styles.error}>Failed to load analytics</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span className={styles.icon}>📊</span>
                <div>
                    <h2>Cohort Analytics</h2>
                    <p className={styles.subtitle}>
                        {data.total_cohorts} cohorts · {data.total_players} players · {data.total_decisions} decisions
                    </p>
                </div>
                <button className={styles.refreshBtn} onClick={() => load()}>🔄 Refresh</button>
            </div>

            <div className={styles.tabBar}>
                {visibleTabs.map(t => (
                    <button
                        key={t.id}
                        className={`${styles.tab} ${tab === t.id ? styles.tabActive : ''}`}
                        onClick={() => setTab(t.id)}
                        data-tooltip={t.title}
                        data-tooltip-pos="below"
                    >
                        {t.label}
                    </button>
                ))}
            </div>

            <div className={styles.panel}>
                {tab === 'heatmap' && <DecisionHeatmap data={data.decision_heatmap} />}
                {tab === 'timing' && <TimeToDecision data={data.time_to_decision} />}
                {tab === 'cohorts' && <CohortComparison data={data.cohort_trajectories} />}
                {tab === 'convergence' && <ConvergenceAnalysis data={data.convergence} />}
                {tab === 'learning' && <LearningOutcomes data={data.learning_outcomes} />}
                {tab === 'risk' && <RiskExposure data={data.risk_exposure} />}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   1. DECISION HEATMAP
   ═══════════════════════════════════════ */
function DecisionHeatmap({ data }) {
    if (!data || !Object.keys(data).length) return <EmptyState msg="No decision data yet" />;
    const rounds = Object.keys(data).sort();
    const allChoices = [...new Set(rounds.flatMap(r => Object.keys(data[r])))].sort();

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Choice Distribution by Round</h3>
            <p className={styles.sectionDesc}>Which options are most popular per round across all players</p>
            <div className={styles.heatmapGrid}>
                {/* Header */}
                <div className={styles.heatRow}>
                    <div className={styles.heatLabel} />
                    {allChoices.map(c => (
                        <div key={c} className={styles.heatColHead}>
                            <span className={styles.choiceDot} style={{ background: CHOICE_COLORS[c] || '#888' }} />
                            {c.replace('option_', 'Option ').toUpperCase()}
                        </div>
                    ))}
                    <div className={styles.heatColHead}>Total</div>
                </div>
                {/* Rows */}
                {rounds.map(r => {
                    const total = Object.values(data[r]).reduce((s, v) => s + v, 0);
                    return (
                        <div key={r} className={styles.heatRow}>
                            <div className={styles.heatLabel}>{r}</div>
                            {allChoices.map(c => {
                                const count = data[r][c] || 0;
                                const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                                const opacity = total > 0 ? 0.15 + (count / total) * 0.85 : 0.1;
                                return (
                                    <div key={c} className={styles.heatCell} style={{
                                        background: `${CHOICE_COLORS[c] || '#888'}${Math.round(opacity * 255).toString(16).padStart(2, '0')}`,
                                    }}>
                                        <strong>{count}</strong>
                                        <span className={styles.heatPct}>{pct}%</span>
                                    </div>
                                );
                            })}
                            <div className={styles.heatTotal}>{total}</div>
                        </div>
                    );
                })}
            </div>
            {/* Stacked bar visual */}
            <div className={styles.stackedBars}>
                {rounds.map(r => {
                    const total = Object.values(data[r]).reduce((s, v) => s + v, 0);
                    return (
                        <div key={r} className={styles.stackedRow}>
                            <span className={styles.barLabel}>{r}</span>
                            <div className={styles.barTrack}>
                                {allChoices.map(c => {
                                    const pct = total > 0 ? (data[r][c] || 0) / total * 100 : 0;
                                    return pct > 0 ? (
                                        <div key={c} className={styles.barSegment} style={{
                                            width: `${pct}%`,
                                            background: CHOICE_COLORS[c] || '#888',
                                        }} title={`${c}: ${data[r][c] || 0} (${Math.round(pct)}%)`} />
                                    ) : null;
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   2. TIME-TO-DECISION
   ═══════════════════════════════════════ */
function TimeToDecision({ data }) {
    if (!data || !Object.keys(data).length) return <EmptyState msg="No timing data yet" />;
    const rounds = Object.keys(data).sort();
    const maxAvg = Math.max(...rounds.map(r => data[r].avg_seconds || 0));

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Decision Speed Analytics</h3>
            <p className={styles.sectionDesc}>How long players take to commit decisions per round</p>
            <div className={styles.timingGrid}>
                {rounds.map(r => {
                    const d = data[r];
                    const barW = maxAvg > 0 ? (d.avg_seconds / maxAvg) * 100 : 50;
                    return (
                        <div key={r} className={styles.timingCard}>
                            <div className={styles.timingHeader}>
                                <span className={styles.timingRound}>{r}</span>
                                <span className={styles.timingCount}>{d.count} decisions</span>
                            </div>
                            <div className={styles.timingBar}>
                                <div className={styles.timingFill} style={{ width: `${barW}%` }}>
                                    <span>{d.avg_seconds}s avg</span>
                                </div>
                            </div>
                            <div className={styles.timingStats}>
                                <span>⏱ Median: <strong>{d.median_seconds}s</strong></span>
                                <span>📉 Min: <strong>{d.min}s</strong></span>
                                <span>📈 Max: <strong>{d.max}s</strong></span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   3. COHORT COMPARISON
   ═══════════════════════════════════════ */
function CohortComparison({ data }) {
    if (!data || !Object.keys(data).length) return <EmptyState msg="No cohort data yet" />;
    const cohorts = Object.keys(data);
    const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
    const [metric, setMetric] = useState('treasury');

    const maxRound = Math.max(...cohorts.flatMap(c => data[c].map(d => d.round)));
    const maxVal = Math.max(...cohorts.flatMap(c => data[c].map(d => d[metric] || 0)), 1);

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Cohort KPI Trajectories</h3>
            <div className={styles.metricToggle}>
                {[
                    { m: 'treasury', label: 'Treasury', icon: '💰', title: 'Total accumulated cash reserves.' },
                    { m: 'reputation', label: 'Reputation', icon: '⭐', title: 'Public perception and brand strength scale (0-100).' },
                    { m: 'synergy', label: 'Synergy', icon: '🔗', title: 'Corporate operational efficiency multiplier.' },
                    { m: 'ebitda', label: 'EBITDA', icon: '📊', title: 'Earnings before interest, taxes, depreciation, and amortization.' }
                ].map(({ m, label, icon, title }) => (
                    <button key={m} className={`${styles.metricBtn} ${metric === m ? styles.metricActive : ''}`}
                        onClick={() => setMetric(m)} title={title}>
                        {icon} {label}
                    </button>
                ))}
            </div>
            {/* Simple line chart using CSS */}
            <div className={styles.chartContainer}>
                <div className={styles.chartYAxis}>
                    <span>{metric === 'treasury' || metric === 'ebitda' ? `$${maxVal.toFixed(0)}M` : maxVal.toFixed(1)}</span>
                    <span>{metric === 'treasury' || metric === 'ebitda' ? `$${(maxVal / 2).toFixed(0)}M` : (maxVal / 2).toFixed(1)}</span>
                    <span>0</span>
                </div>
                <div className={styles.chartBody}>
                    {/* Grid lines */}
                    {[0.25, 0.5, 0.75].map(pct => (
                        <div key={pct} className={styles.gridLine} style={{ bottom: `${pct * 100}%` }} />
                    ))}
                    {/* Lines per cohort */}
                    {cohorts.map((cname, ci) => {
                        const points = data[cname];
                        return (
                            <svg key={cname} className={styles.chartSvg}>
                                <polyline
                                    fill="none"
                                    stroke={COLORS[ci % COLORS.length]}
                                    strokeWidth="2.5"
                                    strokeLinejoin="round"
                                    points={points.map(p => {
                                        const x = maxRound > 1 ? ((p.round - 1) / (maxRound - 1)) * 100 : 50;
                                        const y = 100 - ((p[metric] || 0) / maxVal) * 100;
                                        return `${x}%,${y}%`;
                                    }).join(' ')}
                                />
                                {points.map(p => {
                                    const x = maxRound > 1 ? ((p.round - 1) / (maxRound - 1)) * 100 : 50;
                                    const y = 100 - ((p[metric] || 0) / maxVal) * 100;
                                    return <circle key={p.round} cx={`${x}%`} cy={`${y}%`} r="4"
                                        fill={COLORS[ci % COLORS.length]} />;
                                })}
                            </svg>
                        );
                    })}
                    {/* X-axis labels */}
                    <div className={styles.chartXAxis}>
                        {Array.from({ length: maxRound }, (_, i) => (
                            <span key={i}>Y{i + 1}</span>
                        ))}
                    </div>
                </div>
            </div>
            <div className={styles.legend}>
                {cohorts.map((c, i) => (
                    <span key={c} className={styles.legendItem}>
                        <span className={styles.legendDot} style={{ background: COLORS[i % COLORS.length] }} />
                        {c}
                    </span>
                ))}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   4. CONVERGENCE ANALYSIS
   ═══════════════════════════════════════ */
function ConvergenceAnalysis({ data }) {
    if (!data) return <EmptyState msg="No convergence data yet" />;
    const entropy = data.choice_entropy_by_round || {};
    const capexStd = data.capex_std_by_round || {};
    const rounds = [...new Set([...Object.keys(entropy), ...Object.keys(capexStd)])].sort();
    const ci = data.convergence_index || 0.5;
    const ciPct = Math.round(ci * 100);

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Strategy Convergence Gauge</h3>
            <p className={styles.sectionDesc}>Are players making similar or diverse decisions?</p>

            {/* Big gauge */}
            <div className={styles.gaugeWrap}>
                <div className={styles.gauge}>
                    <div className={styles.gaugeFill} style={{
                        width: `${ciPct}%`,
                        background: ciPct > 70 ? '#10b981' : ciPct > 40 ? '#f59e0b' : '#ef4444'
                    }} />
                </div>
                <div className={styles.gaugeLabels}>
                    <span>🌈 Diverse</span>
                    <strong className={styles.gaugeVal}>{ciPct}% Convergence</strong>
                    <span>🎯 Uniform</span>
                </div>
            </div>

            {/* Per-round breakdown */}
            <div className={styles.convergenceGrid}>
                <div className={styles.convHeader}>
                    <span>Round</span>
                    <span title="A measure of unpredictability. Lower bits indicate players are making identical choices.">Choice Entropy</span>
                    <span title="Variance in capital expenditure. Lower deviation indicates identical spending behaviors.">CapEx StdDev</span>
                </div>
                {rounds.map(r => (
                    <div key={r} className={styles.convRow}>
                        <span className={styles.convRound}>{r}</span>
                        <span>
                            <div className={styles.miniBar}>
                                <div className={styles.miniFill} style={{
                                    width: `${Math.min((entropy[r] || 0) / 1.585 * 100, 100)}%`,
                                    background: '#8b5cf6'
                                }} />
                            </div>
                            {(entropy[r] || 0).toFixed(2)} bits
                        </span>
                        <span>
                            ${((capexStd[r] || 0) / 1_000_000).toFixed(1)}M
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════
   5. LEARNING OUTCOMES
   ═══════════════════════════════════════ */
function LearningOutcomes({ data }) {
    if (!data) return <EmptyState msg="No learning data yet" />;
    const badges = data.badges_awarded || {};
    const categories = data.bonuses_by_category || {};

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Learning & Engagement Tracker</h3>

            <div className={styles.summaryCards}>
                <div className={styles.sumCard} title="Total automated points awarded upon reaching learning milestones.">
                    <div className={styles.sumIcon}>🎓</div>
                    <div className={styles.sumVal}>{data.learning_bonuses_total || 0}</div>
                    <div className={styles.sumLabel}>Learning Bonuses</div>
                </div>
                <div className={styles.sumCard} title="Number of physical awards or manual facilitator grade-adjustments given.">
                    <div className={styles.sumIcon}>🏅</div>
                    <div className={styles.sumVal}>{data.student_bonus_count || 0}</div>
                    <div className={styles.sumLabel}>Awards Given</div>
                </div>
                <div className={styles.sumCard} title="Unique achievement badges earned globally.">
                    <div className={styles.sumIcon}>🏆</div>
                    <div className={styles.sumVal}>{Object.keys(badges).length}</div>
                    <div className={styles.sumLabel}>Badge Types</div>
                </div>
            </div>

            {Object.keys(badges).length > 0 && (
                <div className={styles.badgeGrid}>
                    <h4>Badge Distribution</h4>
                    {Object.entries(badges).sort((a, b) => b[1] - a[1]).map(([badge, count]) => (
                        <div key={badge} className={styles.badgeRow}>
                            <span className={styles.badgeName}>{badge.replace(/_/g, ' ')}</span>
                            <div className={styles.badgeBar}>
                                <div className={styles.badgeFill} style={{
                                    width: `${Math.min((count / Math.max(...Object.values(badges))) * 100, 100)}%`
                                }} />
                            </div>
                            <span className={styles.badgeCount}>×{count}</span>
                        </div>
                    ))}
                </div>
            )}

            {Object.keys(categories).length > 0 && (
                <div className={styles.catGrid}>
                    <h4>Bonuses by Category</h4>
                    {Object.entries(categories).map(([cat, count]) => (
                        <div key={cat} className={styles.catItem}>
                            <span>{cat.replace(/_/g, ' ')}</span>
                            <strong>{count}</strong>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════
   6. RISK EXPOSURE
   ═══════════════════════════════════════ */
function RiskExposure({ data }) {
    if (!data || !Object.keys(data).length) return <EmptyState msg="No risk data yet" />;
    const cohorts = Object.keys(data);
    const [metric, setMetric] = useState('avg_carbon_intensity');
    const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6'];
    const METRICS = [
        { key: 'avg_carbon_intensity', label: '🏭 Carbon Intensity', unit: '', title: 'Average metric tons of CO2e emitted per $1M revenue.' },
        { key: 'avg_natural_capital_debt', label: '🌍 Natural Capital Debt', unit: '', title: 'Unmitigated ecological damages demanding future environmental remediation.' },
        { key: 'avg_social_license', label: '🤝 Social License', unit: '', title: 'Level of ongoing community trust and stakeholder approval.' },
        { key: 'avg_governance_risk', label: '⚖️ Governance Risk', unit: '', title: 'Exposure to regulatory fines, internal corruption, or oversight failure.' },
    ];

    const maxVal = Math.max(...cohorts.flatMap(c => data[c].map(d => d[metric] || 0)), 1);

    return (
        <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Risk Exposure Trends</h3>
            <div className={styles.metricToggle}>
                {METRICS.map(m => (
                    <button key={m.key} className={`${styles.metricBtn} ${metric === m.key ? styles.metricActive : ''}`}
                        onClick={() => setMetric(m.key)} title={m.title}>
                        {m.label}
                    </button>
                ))}
            </div>
            {/* Risk chart */}
            <div className={styles.riskTable}>
                {cohorts.map((cname, ci) => (
                    <div key={cname} className={styles.riskCohort}>
                        <div className={styles.riskName}>
                            <span className={styles.legendDot} style={{ background: COLORS[ci % COLORS.length] }} />
                            {cname}
                        </div>
                        <div className={styles.riskBars}>
                            {data[cname].map(d => (
                                <div key={d.round} className={styles.riskBarWrap} title={`R${d.round}: ${(d[metric] || 0).toFixed(1)}`}>
                                    <div className={styles.riskBar} style={{
                                        height: `${maxVal > 0 ? ((d[metric] || 0) / maxVal) * 100 : 0}%`,
                                        background: COLORS[ci % COLORS.length],
                                    }} />
                                    <span className={styles.riskRound}>Y{d.round}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}


function EmptyState({ msg }) {
    return (
        <div className={styles.empty}>
            <span className={styles.emptyIcon}>📭</span>
            <p>{msg}</p>
            <p className={styles.emptyHint}>Play through some rounds to generate analytics data.</p>
        </div>
    );
}
