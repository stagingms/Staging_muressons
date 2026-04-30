'use client';
import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import styles from './GameOverSummary.module.css';

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

                {/* ── 3 Key Insights ── */}
                {history && history.length > 0 && (() => {
                    // Find best and worst rounds by treasury delta
                    const roundDeltas = history.map((h, i) => ({
                        round: i + 1,
                        treasury_delta: h?.treasury_delta || 0,
                        choice: h?.choice || 'Unknown',
                        choice_title: h?.choice_title || h?.choice || 'Unknown',
                    })).filter(r => r.round <= 10);

                    const best = roundDeltas.reduce((a, b) => a.treasury_delta > b.treasury_delta ? a : b, roundDeltas[0]);
                    const worst = roundDeltas.reduce((a, b) => a.treasury_delta < b.treasury_delta ? a : b, roundDeltas[0]);

                    // Road not taken: for the worst round, suggest the alternative
                    const ROUND_NAMES = {
                        1: 'ESG Audit', 2: 'Double Materiality', 3: 'Scope 3 Emissions',
                        4: 'Contagion Crisis', 5: 'Climate Event', 6: 'AI Bias Scandal',
                        7: 'Circular Economy', 8: 'Water Scarcity', 9: 'Just Transition',
                        10: 'Grand Finale',
                    };

                    const insights = [
                        {
                            icon: '🏆',
                            title: 'Best Decision',
                            text: `Round ${best.round} (${ROUND_NAMES[best.round] || '—'}): Your choice of "${best.choice_title}" generated ${best.treasury_delta >= 0 ? '+' : ''}$${(best.treasury_delta / 1_000_000).toFixed(1)}M in treasury impact.`,
                            color: '#10b981',
                        },
                        {
                            icon: '💸',
                            title: 'Most Costly Mistake',
                            text: `Round ${worst.round} (${ROUND_NAMES[worst.round] || '—'}): Your choice of "${worst.choice_title}" cost $${(Math.abs(worst.treasury_delta) / 1_000_000).toFixed(1)}M in treasury impact.`,
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
                                        <div style={{ fontSize: '0.62rem', color: '#64748b', marginBottom: '0.2rem' }}>{m.label}</div>
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
                                                    fontSize: '0.58rem', fontWeight: 700,
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
                    <p>Muressons Global Command — Sustainability Strategy Simulation</p>
                    <p>© Year 3 Board of Directors Meeting</p>
                </div>
            </div>
        </div>
    );
}
