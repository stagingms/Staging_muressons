'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
    LineChart, Line, AreaChart, Area,
    XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import styles from './DebriefReport.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const CHOICE_COLORS = {
    option_a: '#10b981',
    option_b: '#f59e0b',
    option_c: '#ef4444',
};

const CHOICE_LABELS = {
    option_a: 'A',
    option_b: 'B',
    option_c: 'C',
};

const BU_SHORT = {
    pharma: '💊 Pharma',
    electronics: '🔌 Electronics',
    consumer_goods: '🛒 Consumer Goods',
    software: '💻 Software',
    hospitals: '🏥 Hospitals',
    clinics: '🩺 Clinics',
    specialised_care: '🔬 Specialised Care',
    telehealth: '📱 Telehealth',
};

const METRIC_CONFIG = {
    corporate_treasury: {
        label: 'Treasury',
        tooltip: 'Corporate cash reserves available for CapEx, dividends, and loan repayments. Revenue minus costs each round.',
        format: (v) => `$${(v / 1e6).toFixed(1)}M`,
        deltaFormat: (v) => `${v >= 0 ? '+' : ''}$${(v / 1e6).toFixed(1)}M`,
    },
    group_reputation: {
        label: 'Reputation',
        tooltip: 'Group reputation score (0–100). Affected by crisis decisions, ESG performance, and stakeholder events.',
        format: (v) => `${v.toFixed(1)}`,
        deltaFormat: (v) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}`,
    },
    synergy_multiplier: {
        label: 'Synergy',
        tooltip: 'Cross-BU synergy multiplier. Values above 1.0× boost revenue; below 1.0× penalise it. Decays naturally each round.',
        format: (v) => `${v.toFixed(2)}×`,
        deltaFormat: (v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}`,
    },
    avg_natural_capital_debt: {
        label: 'NCD',
        tooltip: 'Average Natural Capital Debt across all BUs. Measures accumulated environmental liabilities from deferred sustainability investments.',
        format: (v) => `${v.toFixed(1)}`,
        deltaFormat: (v) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}`,
    },
    avg_social_license: {
        label: 'Social License',
        tooltip: 'Average Social License to Operate across all BUs. Represents community and stakeholder trust (0–100).',
        format: (v) => `${v.toFixed(1)}`,
        deltaFormat: (v) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}`,
    },
};

// ── Critical Analysis Diagnostics ────────────────────────
function generateCriticalAnalysis(latestSnapshot, trendHistory) {
    const insights = [];
    if (!latestSnapshot || !trendHistory || trendHistory.length < 2) return insights;

    const latest = latestSnapshot;
    const first = trendHistory[0];
    const prev = trendHistory[trendHistory.length - 2];

    // Treasury trend
    const treasuryDelta = latest.treasury - first.treasury;
    const treasuryTrend = treasuryDelta >= 0 ? 'growing' : 'declining';
    insights.push({
        icon: '💰',
        title: 'Treasury Performance',
        health: treasuryDelta > 0 ? 'good' : treasuryDelta > -5e6 ? 'warn' : 'bad',
        text: treasuryDelta >= 0
            ? `Treasury grew by $${(treasuryDelta / 1e6).toFixed(1)}M since Round 1 — steady capital accumulation despite CapEx obligations.`
            : `Treasury declined by $${(Math.abs(treasuryDelta) / 1e6).toFixed(1)}M since Round 1 — costs and CapEx are outpacing revenue generation.`,
    });

    // Reputation trajectory
    const repDelta = latest.reputation - first.reputation;
    const repRecent = latest.reputation - prev.reputation;
    insights.push({
        icon: '🤝',
        title: 'Reputation Trajectory',
        health: latest.reputation >= 65 ? 'good' : latest.reputation >= 45 ? 'warn' : 'bad',
        text: latest.reputation >= 65
            ? `Reputation at ${latest.reputation.toFixed(1)} — above-average. Stakeholders view leadership decisions favourably.`
            : latest.reputation >= 45
                ? `Reputation at ${latest.reputation.toFixed(1)} — below average. Media scrutiny and talent attrition risk increasing.`
                : `Reputation critically low at ${latest.reputation.toFixed(1)}. Consumer boycotts and regulatory intervention imminent.`,
    });

    // Synergy decay
    const syDelta = latest.synergy - first.synergy;
    insights.push({
        icon: '⚙️',
        title: 'Synergy Multiplier',
        health: latest.synergy > 1.0 ? 'good' : latest.synergy >= 0.9 ? 'warn' : 'bad',
        text: latest.synergy > 1.0
            ? `Synergy at ${latest.synergy.toFixed(2)}× — cross-BU efficiencies are generating additional revenue.`
            : `Synergy decayed to ${latest.synergy.toFixed(2)}× — BUs operating in silos. Consider allocating CapEx to circularity and cross-BU R&D.`,
    });

    // NCD warning
    if (latest.ncd > 0) {
        insights.push({
            icon: '🌍',
            title: 'Environmental Liabilities',
            health: latest.ncd < 3 ? 'warn' : 'bad',
            text: latest.ncd >= 5
                ? `Natural capital debt at ${latest.ncd.toFixed(1)} — environmental liabilities are significant and will increase cost of capital.`
                : `Natural capital debt at ${latest.ncd.toFixed(1)} — moderate but growing. Invest in sustainability to prevent accumulation.`,
        });
    }

    // Social License
    if (latest.social_license < 75) {
        insights.push({
            icon: '👥',
            title: 'Social License Warning',
            health: latest.social_license >= 50 ? 'warn' : 'bad',
            text: `Social License at ${latest.social_license.toFixed(1)} — below the 75 threshold. This would trigger the -0.4 Instability Discount on the Regenerative Multiple if at game end.`,
        });
    }

    return insights;
}

// ────────────────────────────────────────────────────────────
export default function DebriefReport({ sessionId }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [expandedRounds, setExpandedRounds] = useState(new Set());
    const [activeTab, setActiveTab] = useState('rounds'); // 'rounds' | 'trends' | 'analysis'

    const fetchDebrief = useCallback(async () => {
        if (!sessionId) return;
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/admin/${sessionId}/debrief`);
            if (res.ok) {
                const json = await res.json();
                setData(json);
                if (json.rounds?.length) {
                    const latest = json.rounds[json.rounds.length - 1];
                    setExpandedRounds(new Set([latest.round_number]));
                }
            }
        } catch (err) {
            console.error('Failed to fetch debrief:', err);
        } finally {
            setLoading(false);
        }
    }, [sessionId]);

    useEffect(() => {
        fetchDebrief();
        const interval = setInterval(fetchDebrief, 20000);
        return () => clearInterval(interval);
    }, [fetchDebrief]);

    const toggleRound = (rn) => {
        setExpandedRounds(prev => {
            const next = new Set(prev);
            next.has(rn) ? next.delete(rn) : next.add(rn);
            return next;
        });
    };

    const trendHistory = data?.trend_history || [];
    const latestTrend = trendHistory.length > 0 ? trendHistory[trendHistory.length - 1] : null;
    const analysis = useMemo(() => generateCriticalAnalysis(latestTrend, trendHistory), [latestTrend, trendHistory]);

    if (!sessionId) {
        return (
            <div className={styles.panel}>
                <div className={styles.header}>
                    <div className={styles.titleRow}><span>📋</span><h2>Round Debrief</h2></div>
                </div>
                <div className={styles.empty}>
                    <div className={styles.emptyIcon}>📊</div>
                    Select a session in the Leaderboard to view the debrief report.
                </div>
            </div>
        );
    }

    if (loading && !data) {
        return (
            <div className={styles.panel}>
                <div className={styles.header}>
                    <div className={styles.titleRow}><span>📋</span><h2>Round Debrief</h2></div>
                </div>
                <div className={styles.empty}>Loading debrief...</div>
            </div>
        );
    }

    const rounds = data?.rounds || [];

    return (
        <div className={styles.panel}>
            <div className={styles.header}>
                <div className={styles.titleRow}>
                    <span>📋</span>
                    <h2>Round Debrief</h2>
                </div>
                {data?.cohort_name && (
                    <span className={styles.cohortBadge}>{data.cohort_name}</span>
                )}
            </div>

            {/* Tab Navigation */}
            <nav className={styles.tabNav}>
                <button
                    className={`${styles.tab} ${activeTab === 'rounds' ? styles.tabActive : ''}`}
                    onClick={() => setActiveTab('rounds')}
                >
                    📋 Round Review
                </button>
                <button
                    className={`${styles.tab} ${activeTab === 'trends' ? styles.tabActive : ''}`}
                    onClick={() => setActiveTab('trends')}
                >
                    📈 Trends
                </button>
                <button
                    className={`${styles.tab} ${activeTab === 'analysis' ? styles.tabActive : ''}`}
                    onClick={() => setActiveTab('analysis')}
                >
                    🔍 Critical Analysis
                </button>
            </nav>

            <div className={styles.body}>
                {/* ──── Tab: Round Review ──── */}
                {activeTab === 'rounds' && (
                    rounds.length === 0 ? (
                        <div className={styles.empty}>
                            <div className={styles.emptyIcon}>⏳</div>
                            No rounds completed yet.
                        </div>
                    ) : (
                        rounds.map((round) => (
                            <RoundCard
                                key={round.round_number}
                                round={round}
                                expanded={expandedRounds.has(round.round_number)}
                                onToggle={() => toggleRound(round.round_number)}
                            />
                        ))
                    )
                )}

                {/* ──── Tab: Trends ──── */}
                {activeTab === 'trends' && (
                    <TrendsSection trendHistory={trendHistory} />
                )}

                {/* ──── Tab: Critical Analysis ──── */}
                {activeTab === 'analysis' && (
                    <AnalysisSection analysis={analysis} trendHistory={trendHistory} />
                )}
            </div>
        </div>
    );
}

// ═══════════════════════════════════════════════════════
//  ROUND CARD (unchanged logic)
// ═══════════════════════════════════════════════════════
function RoundCard({ round, expanded, onToggle }) {
    const choiceColor = CHOICE_COLORS[round.choice_selected] || '#6366f1';
    const choiceLabel = CHOICE_LABELS[round.choice_selected] || '?';

    return (
        <div className={styles.roundCard}>
            <button className={styles.roundCardHeader} onClick={onToggle}>
                <span className={styles.roundNumber}>{round.round_number}</span>
                <div className={styles.roundMeta}>
                    <div className={styles.roundTitle}>{round.title}</div>
                    <div className={styles.roundTheme}>{round.theme}</div>
                </div>
                {round.choice_selected && (
                    <span className={styles.choicePill} style={{ background: choiceColor }}>
                        {choiceLabel} — {round.choice_title}
                    </span>
                )}
                <span className={`${styles.expandIcon} ${expanded ? styles.expandIconOpen : ''}`}>▶</span>
            </button>

            {expanded && (
                <div className={styles.roundCardBody}>
                    <div className={styles.crisisSection}>
                        <span className={styles.crisisIcon}>{round.crisis_icon}</span>
                        <div className={styles.crisisText}>
                            <h4>{round.crisis_title}</h4>
                            <p>{round.crisis_description}</p>
                        </div>
                    </div>

                    {round.choice_selected && (
                        <div className={styles.decisionSection}>
                            <div className={styles.decisionLabel}>Decision Made</div>
                            <div className={styles.decisionChoice}>
                                <span className={styles.choicePill} style={{ background: choiceColor }}>{choiceLabel}</span>
                                <span className={styles.decisionTitle}>{round.choice_title}</span>
                            </div>
                            {round.choice_description && (
                                <div className={styles.decisionDesc}>{round.choice_description}</div>
                            )}
                        </div>
                    )}

                    {round.snapshot && (
                        <div className={styles.metricsGrid}>
                            {Object.entries(METRIC_CONFIG).map(([key, cfg]) => {
                                const val = round.snapshot[key];
                                const delta = round.deltas?.[key];
                                if (val === undefined) return null;
                                let deltaClass = styles.deltaZero;
                                if (delta > 0) deltaClass = key === 'avg_natural_capital_debt' ? styles.deltaNegative : styles.deltaPositive;
                                else if (delta < 0) deltaClass = key === 'avg_natural_capital_debt' ? styles.deltaPositive : styles.deltaNegative;
                                return (
                                    <div key={key} className={styles.metricCard} title={cfg.tooltip}>
                                        <div className={styles.metricLabel}>{cfg.label}</div>
                                        <div className={styles.metricValue}>
                                            {cfg.format(val)}
                                            {delta !== undefined && delta !== 0 && (
                                                <span className={`${styles.metricDelta} ${deltaClass}`}>{cfg.deltaFormat(delta)}</span>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {round.capex_by_bu && Object.keys(round.capex_by_bu).length > 0 && (
                        <div className={styles.capexSection}>
                            <h5>CapEx Allocation</h5>
                            <div className={styles.capexGrid}>
                                {Object.entries(round.capex_by_bu).map(([bu, capex]) => (
                                    <div key={bu} className={styles.capexItem}>
                                        <div className={styles.capexBu}>{BU_SHORT[bu] || bu}</div>
                                        <div className={styles.capexValue}>${(capex / 1e6).toFixed(1)}M</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {round.new_flags?.length > 0 && (
                        <div className={styles.flagsRow}>
                            <span className={styles.flagsLabel}>Flags Triggered:</span>
                            {round.new_flags.map((f) => (
                                <span key={f} className={styles.flag}>🏴 {f.replace(/_/g, ' ')}</span>
                            ))}
                        </div>
                    )}

                    {round.players?.length > 0 && (
                        <div className={styles.playersRow}>
                            <span>👤</span>
                            {round.players.map((p) => (
                                <span key={p} className={styles.playerBadge}>{p}</span>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}


// ═══════════════════════════════════════════════════════
//  TRENDS SECTION — Line/Area charts
// ═══════════════════════════════════════════════════════
function TrendsSection({ trendHistory }) {
    if (!trendHistory || trendHistory.length < 2) {
        return (
            <div className={styles.empty}>
                <div className={styles.emptyIcon}>📈</div>
                At least 2 rounds are needed to display trends.
            </div>
        );
    }

    const chartData = trendHistory.map(t => ({
        ...t,
        treasuryM: t.treasury / 1e6,
    }));

    const tooltipStyle = {
        fontSize: 12, borderRadius: 8,
        background: '#fff', border: '1px solid #e2e8f0',
        color: '#1e293b', boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    };

    return (
        <div className={styles.trendsSection}>
            <h3 className={styles.sectionHeading}>📈 Performance Trends Across Simulation</h3>
            <div className={styles.trendsGrid}>
                {/* Treasury */}
                <div className={styles.trendCard}>
                    <div className={styles.trendHeader}>
                        <span>💰</span><h4>Corporate Treasury</h4>
                    </div>
                    <div className={styles.trendChart}>
                        <ResponsiveContainer width="100%" height={180}>
                            <AreaChart data={chartData} margin={{ top: 5, right: 15, bottom: 5, left: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#64748b' }} />
                                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={(v) => `$${v.toFixed(0)}M`} />
                                <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`$${v.toFixed(1)}M`, 'Treasury']} />
                                <Area type="monotone" dataKey="treasuryM" stroke="#3b82f6" fill="rgba(59,130,246,0.1)" strokeWidth={2.5} dot={{ r: 4, fill: '#3b82f6' }} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Reputation */}
                <div className={styles.trendCard}>
                    <div className={styles.trendHeader}>
                        <span>🤝</span><h4>Group Reputation</h4>
                    </div>
                    <div className={styles.trendChart}>
                        <ResponsiveContainer width="100%" height={180}>
                            <LineChart data={chartData} margin={{ top: 5, right: 15, bottom: 5, left: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#64748b' }} />
                                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} />
                                <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v.toFixed(1)} / 100`, 'Reputation']} />
                                <Line type="monotone" dataKey="reputation" stroke="#8b5cf6" strokeWidth={2.5} dot={{ r: 4, fill: '#8b5cf6' }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Synergy */}
                <div className={styles.trendCard}>
                    <div className={styles.trendHeader}>
                        <span>⚙️</span><h4>Synergy Multiplier</h4>
                    </div>
                    <div className={styles.trendChart}>
                        <ResponsiveContainer width="100%" height={180}>
                            <LineChart data={chartData} margin={{ top: 5, right: 15, bottom: 5, left: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#64748b' }} />
                                <YAxis tick={{ fontSize: 10, fill: '#64748b' }} tickFormatter={(v) => `${v.toFixed(1)}×`} />
                                <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v.toFixed(2)}×`, 'Synergy']} />
                                <Line type="monotone" dataKey="synergy" stroke="#f59e0b" strokeWidth={2.5} dot={{ r: 4, fill: '#f59e0b' }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Social License */}
                <div className={styles.trendCard}>
                    <div className={styles.trendHeader}>
                        <span>👥</span><h4>Social License to Operate</h4>
                    </div>
                    <div className={styles.trendChart}>
                        <ResponsiveContainer width="100%" height={180}>
                            <LineChart data={chartData} margin={{ top: 5, right: 15, bottom: 5, left: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="year" tick={{ fontSize: 10, fill: '#64748b' }} />
                                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} />
                                <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v.toFixed(1)} / 100`, 'Social License']} />
                                <Line type="monotone" dataKey="social_license" stroke="#10b981" strokeWidth={2.5} dot={{ r: 4, fill: '#10b981' }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
}


// ═══════════════════════════════════════════════════════
//  CRITICAL ANALYSIS SECTION
// ═══════════════════════════════════════════════════════
function AnalysisSection({ analysis, trendHistory }) {
    if (!analysis || analysis.length === 0) {
        return (
            <div className={styles.empty}>
                <div className={styles.emptyIcon}>🔍</div>
                Complete at least 2 rounds to see critical analysis.
            </div>
        );
    }

    const latest = trendHistory[trendHistory.length - 1];

    // Overall verdict
    const goodCount = analysis.filter(a => a.health === 'good').length;
    const total = analysis.length;
    let verdict, verdictHealth;
    if (goodCount >= total * 0.75) {
        verdict = "Strong strategic performance. Key metrics are trending positively and the group is well-positioned for the next round.";
        verdictHealth = 'good';
    } else if (goodCount >= total * 0.5) {
        verdict = "Mixed performance. Some metrics show promise but critical weaknesses need addressing before they compound.";
        verdictHealth = 'warn';
    } else {
        verdict = "Multiple metrics are below viability thresholds. Immediate strategic intervention required to prevent cascading deterioration.";
        verdictHealth = 'bad';
    }

    const healthIcon = (h) => h === 'good' ? '✅' : h === 'warn' ? '⚠️' : '❌';
    const healthColor = (h) => h === 'good' ? '#059669' : h === 'warn' ? '#d97706' : '#dc2626';

    return (
        <div className={styles.analysisSection}>
            <h3 className={styles.sectionHeading}>🔍 Strategic Critical Analysis</h3>

            {/* Executive Summary */}
            <div className={styles.verdictCard} style={{ borderLeftColor: healthColor(verdictHealth) }}>
                <div className={styles.verdictHeader}>
                    <span>{healthIcon(verdictHealth)}</span>
                    <strong>Executive Summary</strong>
                </div>
                <p className={styles.verdictText}>{verdict}</p>
            </div>

            {/* Insight Cards */}
            {analysis.map((insight, i) => (
                <div key={i} className={styles.insightCard} style={{ borderLeftColor: healthColor(insight.health) }}>
                    <div className={styles.insightHeader}>
                        <span className={styles.insightIcon}>{insight.icon}</span>
                        <strong>{insight.title}</strong>
                        <span className={styles.insightBadge} style={{ color: healthColor(insight.health) }}>
                            {healthIcon(insight.health)}
                        </span>
                    </div>
                    <p className={styles.insightText}>{insight.text}</p>
                </div>
            ))}

            {/* Quick Metrics Summary Table */}
            {latest && (
                <div className={styles.summaryTable}>
                    <h4>Current State at Round {latest.round}</h4>
                    <table>
                        <tbody>
                            <tr><td>Treasury</td><td className={styles.summaryValue}>${(latest.treasury / 1e6).toFixed(1)}M</td></tr>
                            <tr><td>Reputation</td><td className={styles.summaryValue} style={{ color: healthColor(latest.reputation >= 65 ? 'good' : latest.reputation >= 45 ? 'warn' : 'bad') }}>{latest.reputation.toFixed(1)}</td></tr>
                            <tr><td>Synergy</td><td className={styles.summaryValue}>{latest.synergy.toFixed(2)}×</td></tr>
                            <tr><td>NCD</td><td className={styles.summaryValue}>{latest.ncd.toFixed(1)}</td></tr>
                            <tr><td>Social License</td><td className={styles.summaryValue} style={{ color: healthColor(latest.social_license >= 75 ? 'good' : latest.social_license >= 50 ? 'warn' : 'bad') }}>{latest.social_license.toFixed(1)}</td></tr>
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
