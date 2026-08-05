'use client';
import { currencySymbol, delta, money, price, ratio } from '../utils/format';
import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import styles from './GameOverSummary.module.css';
import { useAnalyticsVisibility } from '../hooks/useAnalyticsVisibility';
import StudentReportExport from './StudentReportExport';
import { useCurrency } from '../contexts/CurrencyContext';
import RewindRibbon from './RewindRibbon';
import RegretMeter from './RegretMeter';
import MRLadderReveal from './MRLadderReveal';
import MirrorDebrief from './MirrorDebrief';
import ESGLeadershipProfile from './ESGLeadershipProfile';
import ArchetypeCard from './ArchetypeCard';
import FrontPageReveal from './FrontPageReveal';
import CalibrationReport from './CalibrationReport';
import { deriveKeyInsights, fmtDeltaM } from '../lib/keyInsights';

const CEOInterview = dynamic(() => import('./CEOInterview'), { ssr: false });

const PROFILES = {
    regenerative_titan: { icon: '🌱', gradient: 'linear-gradient(135deg, var(--kpi-good), var(--positive-deep))', title: 'Regenerative Titan' },
    derisked_safe_haven: { icon: '🛡️', gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)', title: 'De-risked Safe Haven' },
    fragile_giant: { icon: '⚠️', gradient: 'linear-gradient(135deg, var(--caution), var(--caution-deep))', title: 'Fragile Giant' },
    stranded_relic: { icon: '💀', gradient: 'linear-gradient(135deg, var(--danger), #b91c1c)', title: 'Stranded Relic' },
};

const FALLBACK_THEME = { icon: '🏅', gradient: 'linear-gradient(135deg, #6366f1, #4f46e5)', title: 'Strategic Leader' };

/**
 * GameOverSummary — Final screen after Boardroom Showdown.
 * Simulation is definitively over. Player can download report or review scorecard.
 */
export default function GameOverSummary({ data, businessUnits, globalState, history, onReviewScorecard, decisionParadigm, sessionId, onLogout }) {
    // Cohort visibility for the terminal-screen panels (fail-open).
    const { isPlayerVisible } = useAnalyticsVisibility(sessionId);
    const [showInterview, setShowInterview] = useState(false);
    const [interviewAvailable, setInterviewAvailable] = useState(false);
    const [interviewCompleted, setInterviewCompleted] = useState(false);
    const d = data || {};
    const { currency } = useCurrency();
    /* `sym` was declared here and then bypassed by ten literal '$' templates.
       utils/format resolves the symbol once, from CurrencyProvider. */
    const isBRSR = decisionParadigm === 'brsr_ngrbc';
    // Dynamic theme: prefer backend-provided icon/gradient (supports custom archetypes),
    // else fall back to PROFILES dict, else universal fallback.
    const baseTheme = PROFILES[d.profile] || FALLBACK_THEME;
    const theme = {
        icon: d.profile_icon || baseTheme.icon,
        gradient: d.profile_gradient || baseTheme.gradient,
        title: baseTheme.title,
    };
    // First hex in the archetype gradient — used to brand the shareable card.
    const accentHex = (theme.gradient.match(/#[0-9a-fA-F]{6}/) || ['var(--kpi-good)'])[0];
    const activeFlags = globalState?.active_event_flags || {};

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
                        <span className={styles.statLabel}>Enterprise Value</span>
                        <span className={`${styles.statValue} num`}>{money(d.terminal_value)}</span>
                    </div>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Equity Value</span>
                        <span className={styles.statValue} style={{
                            color: d.equity_value != null ? (d.equity_value > 0 ? 'var(--kpi-good)' : 'var(--danger)') : undefined
                        }}>
                            {money(d.equity_value != null ? d.equity_value : d.terminal_value)}
                        </span>
                    </div>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>📈 Share Price</span>
                        <span className={styles.statValue} style={{
                            color: d.price_per_share != null
                                ? d.price_per_share >= 50 ? 'var(--kpi-good)' : d.price_per_share >= 30 ? 'var(--caution)' : 'var(--danger)'
                                : undefined,
                            fontSize: '1.4rem',
                        }}>
                            {price(d.price_per_share)}
                        </span>
                    </div>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Regenerative Multiple</span>
                        <span className={`${styles.statValue} num`}>{ratio(d.regenerative_multiple)}</span>
                    </div>
                    <div className={styles.statCard}>
                        <span className={styles.statLabel}>Rounds Played</span>
                        <span className={styles.statValue}>{isBRSR ? '5' : '10'}</span>
                    </div>
                    {/* Quiz score log — the player's knowledge-check performance across
                        the run. Only rendered when at least one quiz was taken. */}
                    {d.quiz_score_log && d.quiz_score_log.quizzes_taken > 0 && (
                        <div className={styles.statCard}
                            title={d.quiz_score_log.entries.map(e =>
                                `${e.round != null ? `R${e.round} · ` : ''}${e.title}: ${e.best_score_percent}%`
                                + `${e.passed ? ' ✓' : ''} (${e.attempts} attempt${e.attempts === 1 ? '' : 's'})`
                            ).join('\n')}>
                            <span className={styles.statLabel}>🧩 Quiz Score (avg)</span>
                            <span className={styles.statValue} style={{
                                color: d.quiz_score_log.average_best_score >= (d.quiz_score_log.pass_threshold || 70) ? 'var(--kpi-good)' : 'var(--caution)',
                            }}>
                                {d.quiz_score_log.average_best_score}%
                            </span>
                            <span style={{ fontSize: '0.6rem', color: '#94a3b8', marginTop: 2 }}>
                                {d.quiz_score_log.passed_count}/{d.quiz_score_log.quizzes_taken} passed
                            </span>
                        </div>
                    )}
                </div>

                {/* Quiz score log — per-round breakdown (the facilitator can read
                    each player's scores off their final results card). */}
                {d.quiz_score_log && d.quiz_score_log.quizzes_taken > 0 && (
                    <div style={{
                        margin: '0.5rem 0 1rem', padding: '10px 14px', borderRadius: 10,
                        background: 'rgba(79,70,229,0.08)', border: '1px solid rgba(79,70,229,0.25)',
                    }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 800, color: '#a5b4fc', letterSpacing: '0.04em', marginBottom: 6 }}>
                            🧩 KNOWLEDGE-CHECK LOG
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            {d.quiz_score_log.entries.map(e => (
                                <div key={e.notebook_id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.72rem' }}>
                                    <span style={{ color: '#94a3b8', minWidth: 34 }}>{e.round != null ? `R${e.round}` : '—'}</span>
                                    <span style={{ flex: 1, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.title}</span>
                                    <span style={{ color: '#94a3b8', fontSize: '0.66rem' }}>{e.attempts} att.</span>
                                    <span style={{ fontWeight: 700, fontFamily: "'JetBrains Mono', monospace", color: e.passed ? 'var(--positive-text)' : 'var(--caution-text)', minWidth: 42, textAlign: 'right' }}>
                                        {e.best_score_percent}%
                                    </span>
                                    <span style={{ minWidth: 16 }}>{e.passed ? '✓' : '·'}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Wow moments: replay the journey, name the regret, keep a card */}
                {isPlayerVisible('rewind_ribbon') && (
                    <RewindRibbon flags={activeFlags} />
                )}
                {/* WOW-10: M_R Ladder — animated stacking reveal of each M_R component */}
                {isPlayerVisible('mr_ladder_reveal') && (
                    <MRLadderReveal mr={d.regenerative_multiple} flags={activeFlags} />
                )}
                {isPlayerVisible('regret_meter') && (
                    <RegretMeter mr={d.regenerative_multiple} flags={activeFlags} />
                )}
                {/* WOW-3: Mirror Debrief — single highest-impact counterfactual */}
                {isPlayerVisible('mirror_debrief') && (
                    <MirrorDebrief
                        mr={Number(d.regenerative_multiple) || 0}
                        flags={activeFlags}
                        terminalValue={Number(d.terminal_value) || 0}
                    />
                )}
                {isPlayerVisible('archetype_card') && (
                    <div style={{ textAlign: 'center' }}>
                        <ArchetypeCard
                            title={d.profile_title || theme.title}
                            icon={theme.icon}
                            mr={d.regenerative_multiple || 0}
                            terminalValueM={(d.terminal_value || 0) / 1_000_000}
                            sharePrice={d.price_per_share}
                            equityWiped={d.equity_wiped_out ?? (d.equity_value != null ? d.equity_value < 0 : null)}
                            accent={accentHex}
                            cohortName={d.cohort_name || ''}
                        />
                    </div>
                )}
                {/* The cohort switch is an ADDITIONAL veto: FrontPageReveal still
                    self-checks the `front_page_enabled` global flag internally, so
                    both must allow it for the reveal to render. */}
                {isPlayerVisible('front_page_reveal') && (
                    <FrontPageReveal
                        sessionId={sessionId}
                        data={d}
                        cohortName={d.cohort_name || ''}
                        history={history}
                        peers={peerLeaderboard}
                    />
                )}
                {/* Calibration curve + Overconfidence Index (Phase 3) —
                    renders nothing if no scored predictions exist. */}
                {isPlayerVisible('calibration_report') && (
                    <CalibrationReport sessionId={sessionId} />
                )}
                {/* WOW-12: ESG Leadership Profile — radar chart + PNG export */}
                {isPlayerVisible('esg_leadership') && (
                    <ESGLeadershipProfile
                        data={d}
                        flags={activeFlags}
                        sessionId={sessionId}
                        cohortName={d.cohort_name || ''}
                        businessUnits={businessUnits}
                    />
                )}

                {/* Message */}
                <div className={styles.message}>
                    <h2>📋 Your Board Presentation Is Complete</h2>
                    <p>
                        You have presented your strategic recommendation to the Board of Directors.
                        The simulation is now concluded. You may download your Balanced Scorecard report
                        or review your performance across all {isBRSR ? '5' : '10'} rounds.
                    </p>
                </div>

                {/* ── Final Peer Performance Leaderboard ── */}
                {/* `peer_benchmarking` is the single switch for ALL peer data shown
                    to players. This table was a leak: it named every team and their
                    standing even for cohorts that had peer benchmarking turned off.
                    The non-empty guard stays — the switch is an extra veto on top. */}
                {isPlayerVisible('peer_benchmarking') && peerLeaderboard.length > 0 && (
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
                            {peerLeaderboard.some(t => t.isAI) && <span style={{ fontSize: '0.68rem', background: 'rgba(245,158,11,0.15)', color: 'var(--caution-text)', padding: '2px 6px', borderRadius: 3, fontWeight: 700, marginLeft: 6 }}>🤖 AI</span>}
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
                                        <td style={{ padding: '8px', textAlign: 'right', fontWeight: 700, color: 'var(--positive-text)', fontFamily: "'JetBrains Mono', monospace" }}>
                                            {money(team.treasury)}
                                        </td>
                                        <td style={{ padding: '8px', textAlign: 'right', color: '#cbd5e1' }}>
                                            {team.reputation?.toFixed(0) ?? '—'}
                                        </td>
                                        <td style={{ padding: '8px', textAlign: 'right', color: '#94a3b8', fontFamily: "'JetBrains Mono', monospace" }}>
                                            {(team.co2 || 0).toLocaleString()}t
                                        </td>
                                        <td style={{
                                            padding: '8px', textAlign: 'right',
                                            color: (team.bonus_score || 0) > 0 ? 'var(--caution-text)' : '#475569',
                                            fontWeight: 700, fontFamily: "'JetBrains Mono', monospace",
                                        }}>
                                            {(team.bonus_score || 0) > 0 ? `🏅 ${(team.bonus_score || 0).toLocaleString()}` : '–'}
                                        </td>
                                        <td style={{
                                            padding: '8px', textAlign: 'center', fontSize: '0.9rem',
                                            color: team.trend === '↑' ? 'var(--positive-text)' : team.trend === '↓' ? 'var(--danger-text)' : '#94a3b8',
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


                {/* ── 3 Key Insights ──
                    Derivation lives in ../lib/keyInsights so this block and the
                    newspaper's "Inside the numbers" column can never disagree.

                    It previously read `h.treasury ?? h.corporate_treasury` off a
                    history row. Neither key exists — a row is
                    { round_number, choice_selected, business_units, global_state }
                    with the balance at global_state.corporate_treasury — so every
                    delta computed as 0 − 0, and `best` and `worst` both collapsed
                    onto the last row. The class was shown "Best Decision …
                    +$0.0M" and "Most Costly Mistake … $0.0M" for the SAME round.
                    deriveKeyInsights now reads the real balance AND returns null
                    when the run genuinely cannot separate a best from a worst,
                    so a degenerate case prints nothing instead of a false claim. */}
                {isPlayerVisible('three_key_insights') && history && history.length > 0 && (() => {
                    const ki = deriveKeyInsights(history);
                    if (!ki) return null;
                    const { best, worst, swing } = ki;

                    const insights = [
                        {
                            icon: '🏆',
                            title: 'Best Decision',
                            text: `Round ${best.round}${best.name ? ` (${best.name})` : ''}: ${best.choice || 'your call'} moved the treasury ${fmtDeltaM(best.delta)} — the strongest single-round swing of the plan.`,
                            color: 'var(--kpi-good)',
                        },
                        {
                            icon: '💸',
                            title: 'Most Costly Decision',
                            text: `Round ${worst.round}${worst.name ? ` (${worst.name})` : ''}: ${worst.choice || 'your call'} moved the treasury ${fmtDeltaM(worst.delta)} — the deepest drawdown on the ledger.`,
                            color: 'var(--danger)',
                        },
                        // Third insight only when reputation actually moved. No
                        // filler: the old "Road Not Taken" line asserted a
                        // counterfactual nothing had computed.
                        ...(swing ? [{
                            icon: '📣',
                            title: 'Sharpest Reputation Swing',
                            text: `Round ${swing.round}${swing.name ? ` (${swing.name})` : ''}: group reputation moved from ${swing.from.toFixed(0)} to ${swing.reputation.toFixed(0)} out of 100 (${swing.change >= 0 ? '+' : '−'}${Math.abs(swing.change).toFixed(0)} points).`,
                            color: '#a78bfa',
                        }] : []),
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
                        verdictColor = 'var(--danger)';
                        verdictIcon = '🌡️';
                    } else if (avgCI !== null && avgCI < 50) {
                        verdict = 'Climate Leader — Exemplary Decarbonisation';
                        verdictColor = 'var(--kpi-good)';
                        verdictIcon = '🌱';
                    } else if (avgCI !== null && avgCI < 70) {
                        verdict = 'Managed Retreat — Avoided Tipping Point';
                        verdictColor = 'var(--caution)';
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
                                color: 'var(--kpi-good)',
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
                                        <div style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--kpi-good)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                            Green Transition Fund
                                        </div>
                                        <div style={{ fontSize: '0.85rem', color: '#6ee7b7', marginTop: '0.2rem' }}>
                                            Capital accumulated for decarbonisation initiatives
                                        </div>
                                    </div>
                                </div>
                                <div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--kpi-good)' }}>
                                    {currencySymbol()}{(greenFund / 1_000_000).toFixed(2)}M
                                </div>
                            </div>

                            {/* Climate metrics grid */}
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '0.8rem' }}>
                                {[
                                    { label: '💨 Avg Carbon Intensity', value: avgCI !== null ? `${avgCI.toFixed(1)} t/BU` : '—', color: avgCI !== null && avgCI >= 70 ? 'var(--danger)' : '#6ee7b7' },
                                    { label: '🌡️ Tipping Point', value: tippingPoint ? 'BREACHED ⚠️' : 'Avoided ✓', color: tippingPoint ? 'var(--danger)' : 'var(--kpi-good)' },
                                    { label: '💰 Total Carbon Fees', value: money(carbonFeesPaid), color: '#94a3b8' },
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


                {/* ── Side Track Results ── */}
                {isPlayerVisible('side_track_results') && (() => {
                    const flags = globalState?.active_event_flags || {};
                    const SIDE_TRACKS = [
                        { id: 'supply_chain', label: 'Supply Chain Deep Dive', icon: '🔗', scoreKey: 'supply_chain_final_score', gradeKey: 'supply_chain_grade', archetypeKey: 'supply_chain_archetype', completedKey: 'supply_chain_track_completed', mrBonusKey: 'sc_track_mr_bonus', mrPenaltyKey: 'sc_track_mr_penalty' },
                        { id: 'ethics', label: 'Ethics & Sustainability', icon: '⚖️', scoreKey: 'ethics_final_score', gradeKey: 'ethics_grade', archetypeKey: 'ethics_archetype', completedKey: 'ethics_track_completed', mrBonusKey: 'es_track_mr_bonus', mrPenaltyKey: 'es_track_mr_penalty' },
                        { id: 'stakeholder', label: 'Stakeholder Management', icon: '🤝', scoreKey: 'stakeholder_final_score', gradeKey: 'stakeholder_grade', archetypeKey: 'stakeholder_archetype', completedKey: 'stakeholder_track_completed', mrBonusKey: 'sm_track_mr_bonus', mrPenaltyKey: 'sm_track_mr_penalty' },
                        { id: 'reporting', label: 'Sustainability Reporting', icon: '📊', scoreKey: 'reporting_final_score', gradeKey: 'reporting_grade', archetypeKey: 'reporting_archetype', completedKey: 'reporting_track_completed', mrBonusKey: 'sr_track_mr_bonus', mrPenaltyKey: 'sr_track_mr_penalty' },
                        { id: 'corporate_sdg', label: 'Corporate SDG Alignment', icon: '🌐', scoreKey: 'sdg_impact_score', gradeKey: 'sdg_grade', archetypeKey: 'sdg_archetype', completedKey: 'sdg_track_completed', mrBonusKey: 'sdg_mr_bonus', mrPenaltyKey: 'sdg_mr_penalty' },
                        { id: 'brsr_ngrbc', label: 'BRSR: NGRBC Deep Dive', icon: '🇮🇳', scoreKey: 'brsr_performance_score', gradeKey: 'brsr_grade', archetypeKey: 'brsr_archetype', completedKey: 'brsr_track_completed', mrBonusKey: 'brsr_net_positive_dividend', mrPenaltyKey: 'brsr_mr_penalty' },
                    ];

                    const completedTracks = SIDE_TRACKS.filter(t => flags[t.completedKey]);
                    if (completedTracks.length === 0) return null;

                    const gradeColors = { 'A+': 'var(--kpi-good)', 'A': '#34d399', 'B': '#3b82f6', 'C': 'var(--caution)', 'D': '#f97316', 'F': 'var(--danger)' };

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
                                                    color: mrBonus ? 'var(--positive-text)' : 'var(--danger-text)',
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

                {/* ── BRSR NGRBC Certificate ── */}
                {isBRSR && (() => {
                  const flags = globalState?.active_event_flags || {};
                  if (!flags.brsr_track_completed) return null;
                  const brsrGrade = flags.brsr_grade || 'C';
                  const brsrArchetype = flags.brsr_archetype || 'Compliance Pragmatist';
                  const brsrScore = flags.brsr_performance_score || 0;
                  const gradeColors = { 'A+': 'var(--kpi-good)', 'A': 'var(--positive)', 'B': '#3b82f6', 'C': 'var(--caution)', 'D': 'var(--danger)', 'F': '#dc2626' };
                  const gradeColor = gradeColors[brsrGrade] || '#94a3b8';
                  const principleLabels = ['P1/P7: Governance', 'P3/P5: Workforce', 'P6/P2: Environment', 'P4/P8/P9: Value Chain', 'Integrated Disclosure'];
                  const roundHistory = flags.brsr_round_history || [];
                  return (
                    <div style={{
                      marginTop: 32, padding: 24, borderRadius: 16,
                      background: 'linear-gradient(135deg, rgba(16,185,129,0.08), rgba(59,130,246,0.08))',
                      border: `2px solid ${gradeColor}40`,
                      position: 'relative', overflow: 'hidden'
                    }}>
                      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: `linear-gradient(90deg, ${gradeColor}, ${gradeColor}80)` }} />
                      <div style={{ textAlign: 'center', marginBottom: 16 }}>
                        <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: '#94a3b8', marginBottom: 4 }}>SEBI Business Responsibility Index</div>
                        <div style={{ fontSize: '2.5rem', fontWeight: 900, color: gradeColor, textShadow: `0 0 20px ${gradeColor}40` }}>{brsrGrade}</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#e2e8f0' }}>{brsrArchetype}</div>
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 4 }}>Compliance Score: {brsrScore.toFixed(1)} / 100</div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                        {principleLabels.map((label, i) => {
                          const rh = roundHistory[i];
                          const passed = rh && rh.choice !== 'option_c';
                          return (
                            <div key={i} style={{ textAlign: 'center', padding: '8px 4px', borderRadius: 8, background: passed ? `${gradeColor}15` : 'rgba(239,68,68,0.1)', border: `1px solid ${passed ? gradeColor + '30' : 'var(--danger)30'}` }}>
                              <div style={{ fontSize: '1rem', marginBottom: 4 }}>{passed ? '✅' : '❌'}</div>
                              <div style={{ fontSize: '0.58rem', color: '#94a3b8', lineHeight: 1.3 }}>{label}</div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })()}

                {/* ── SDG Terminal Valuation Waterfall (Fix 7) ── */}
                {(() => {
                    const flags = globalState?.active_event_flags || {};
                    const sdgScore = flags.sdg_impact_score;
                    const sdgCompleted = flags.sdg_track_completed;
                    if (!sdgCompleted && sdgScore == null) return null;

                    const safeScore = sdgScore ?? 0;
                    const mSdg = 1.0 + (safeScore / 100.0) * 0.25;
                    const mR = d.regenerative_multiple || 1.0;
                    const exitMultiple = d.exit_multiple || 12.0;
                    const ebitda = d.terminal_ebitda || d.terminal_value / (exitMultiple * mR * mSdg) || 0;
                    const vT = d.terminal_value || 0;
                    const sdgMrBonus = flags.sdg_mr_bonus || 0;
                    const history = flags.sdg_score_history || [];

                    const lineColor = (val, threshold) => val >= threshold ? 'var(--kpi-good)' : val >= threshold * 0.7 ? 'var(--caution)' : 'var(--danger)';

                    return (
                        <div style={{
                            background: 'linear-gradient(135deg, rgba(99,102,241,0.07), rgba(0,229,195,0.05))',
                            border: '1px solid rgba(99,102,241,0.25)',
                            borderRadius: '12px',
                            padding: '1.2rem 1.4rem',
                            marginTop: '0.5rem',
                        }}>
                            {/* Header */}
                            <div style={{
                                fontSize: '0.72rem', fontWeight: 800, letterSpacing: '0.12em',
                                textTransform: 'uppercase', marginBottom: '1rem',
                                display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#818cf8',
                            }}>
                                <span>🌐</span> Terminal Valuation Waterfall — SDG Breakdown
                            </div>

                            {/* Formula line items */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0', marginBottom: '1rem' }}>
                                {[
                                    {
                                        label: 'Group EBITDA (Year 5)',
                                        value: money(ebitda > 0 ? ebitda : null),
                                        color: '#cbd5e1', op: null, desc: 'Base operating profit across all BUs',
                                    },
                                    {
                                        label: `Exit Multiple`,
                                        value: `${exitMultiple.toFixed(1)}×`,
                                        color: '#60a5fa', op: '×', desc: 'WACC-based Gordon Growth multiple (dynamic, linked to cost of capital)',
                                    },
                                    {
                                        label: `M_R — Regenerative Multiple`,
                                        value: ratio(mR),   /* was 4dp here and 2dp in the stat card above */
                                        color: lineColor(mR, 1.3), op: '×', desc: 'ESG performance score × Capital efficiency × Leverage quality',
                                    },
                                    {
                                        label: `M_SDG — Sustainability Multiplier`,
                                        value: sdgCompleted ? ratio(mSdg) : 'not used this run',
                                        color: sdgCompleted ? lineColor(mSdg, 1.1) : '#64748b', op: '×',
                                        desc: `SDG Impact Score: ${safeScore}/105 → M_SDG = 1.0 + (${safeScore}/100) × 0.25`,
                                        highlight: sdgCompleted,
                                    },
                                ].map((row, i, arr) => (
                                    <div key={i} style={{
                                        display: 'flex', alignItems: 'center',
                                        padding: '0.6rem 0.75rem',
                                        background: row.highlight ? 'rgba(99,102,241,0.08)' : 'rgba(0,0,0,0.1)',
                                        borderLeft: row.highlight ? '3px solid #818cf8' : '3px solid transparent',
                                        borderBottom: i < arr.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                                    }}>
                                        {row.op && (
                                            <span style={{ fontSize: '0.85rem', color: '#475569', width: '22px', flexShrink: 0, textAlign: 'center', fontWeight: 800 }}>
                                                {row.op}
                                            </span>
                                        )}
                                        {!row.op && <span style={{ width: '22px', flexShrink: 0 }} />}
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontSize: '0.72rem', fontWeight: 700, color: row.color }}>{row.label}</div>
                                            <div style={{ fontSize: '0.6rem', color: '#475569', marginTop: '1px' }}>{row.desc}</div>
                                        </div>
                                        <span style={{
                                            fontSize: '0.88rem', fontWeight: 900,
                                            fontFamily: "'JetBrains Mono', monospace",
                                            color: row.color,
                                        }}>{row.value}</span>
                                    </div>
                                ))}

                                {/* Result line — Enterprise Value */}
                                <div style={{
                                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                    padding: '0.75rem', marginTop: '4px',
                                    background: 'linear-gradient(135deg, rgba(16,185,129,0.1), rgba(99,102,241,0.08))',
                                    border: '1px solid rgba(16,185,129,0.3)', borderRadius: '8px',
                                }}>
                                    <div>
                                        <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#e2e8f0' }}>= V<sub>T</sub> — Terminal Enterprise Value</div>
                                        <div style={{ fontSize: '0.6rem', color: '#64748b', marginTop: '2px' }}>
                                            EBITDA × {ratio(exitMultiple)} × M_R({ratio(mR)}) × M_SDG({ratio(mSdg)})
                                        </div>
                                    </div>
                                    <span style={{
                                        fontSize: '1.2rem', fontWeight: 900,
                                        fontFamily: "'JetBrains Mono', monospace",
                                        color: 'var(--kpi-good)',
                                    }}>{currencySymbol()}{(vT / 1_000_000).toFixed(2)}M</span>
                                </div>

                                {/* STRAT-010: Equity Bridge */}
                                {(() => {
                                    const flags = globalState?.active_event_flags || {};
                                    const eqVal = flags.equity_value ?? d.equity_value;
                                    const pps   = flags.price_per_share ?? d.price_per_share;
                                    const nd    = flags.net_debt ?? d.net_debt;
                                    if (eqVal == null || pps == null) return null;
                                    const spColor = pps >= 50 ? 'var(--kpi-good)' : pps >= 30 ? 'var(--caution)' : 'var(--danger)';
                                    return (
                                        <div style={{ marginTop: '0.5rem', padding: '0.6rem 0.75rem', borderRadius: '8px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(148,163,184,0.12)' }}>
                                            <div style={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', marginBottom: '6px' }}>
                                                Equity Bridge (EV − Net Debt)
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', marginBottom: '4px', color: '#94a3b8' }}>
                                                <span>Net Debt</span>
                                                <span style={{ fontFamily: "'JetBrains Mono', monospace", color: 'var(--danger-text)' }}>
                                                    −{currencySymbol()}{((nd || 0) / 1_000_000).toFixed(1)}M
                                                </span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '6px' }}>
                                                <span>Equity Value</span>
                                                <span style={{ fontFamily: "'JetBrains Mono', monospace", color: eqVal > 0 ? 'var(--positive-text)' : 'var(--danger)', fontWeight: 800 }}>
                                                    {currencySymbol()}{(eqVal / 1_000_000).toFixed(2)}M
                                                </span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 8px', borderRadius: '6px', background: `${spColor}15`, border: `1px solid ${spColor}40` }}>
                                                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#e2e8f0' }}>📈 Share Price</span>
                                                <span style={{ fontSize: '1.1rem', fontWeight: 900, color: spColor, fontFamily: "'JetBrains Mono', monospace" }}>
                                                    {currencySymbol()}{pps.toFixed(2)}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })()}
                            </div>

                            {/* SDG contribution callout */}
                            {sdgCompleted && (
                                <div style={{
                                    display: 'grid', gridTemplateColumns: '1fr 1fr',
                                    gap: '0.6rem', marginBottom: '0.75rem',
                                }}>
                                    <div style={{ padding: '0.6rem 0.75rem', borderRadius: '8px', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.15)' }}>
                                        <div style={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', marginBottom: '3px' }}>SDG Track Score</div>
                                        <div style={{ fontSize: '0.9rem', fontWeight: 900, color: '#818cf8', fontFamily: "'JetBrains Mono', monospace" }}>{safeScore}/105</div>
                                        <div style={{ fontSize: '0.6rem', color: '#475569', marginTop: '2px' }}>
                                            {safeScore >= 85 ? '🌟 Champion' : safeScore >= 65 ? '🏆 Leader' : safeScore >= 45 ? '📈 Performer' : safeScore >= 20 ? '📋 Starter' : '⚠️ Laggard'}
                                        </div>
                                    </div>
                                    <div style={{ padding: '0.6rem 0.75rem', borderRadius: '8px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)' }}>
                                        <div style={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', marginBottom: '3px' }}>M_SDG Contribution</div>
                                        <div style={{ fontSize: '0.9rem', fontWeight: 900, color: 'var(--kpi-good)', fontFamily: "'JetBrains Mono', monospace" }}>
                                            {vT > 0 ? delta(vT - vT / mSdg, money) : ratio(mSdg)}
                                        </div>
                                        <div style={{ fontSize: '0.6rem', color: '#475569', marginTop: '2px' }}>
                                            {vT > 0 ? 'Value added vs. no SDG track' : 'Terminal multiplier'}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* SDG Round Sparkline (Fix 8 lite — show round-by-round score history in GameOver) */}
                            {history.length > 0 && (
                                <div>
                                    <div style={{ fontSize: '0.6rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.5rem' }}>
                                        SDG Score Progression (Round by Round)
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'flex-end', height: '44px' }}>
                                        {history.map((h, i) => {
                                            const maxScore = 105;
                                            const pct = Math.max(8, (h.score / maxScore) * 100);
                                            const col = h.points >= 15 ? 'var(--kpi-good)' : h.points >= 8 ? 'var(--caution)' : 'var(--danger)';
                                            return (
                                                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                                                    <div style={{ fontSize: '0.75rem', color: col, fontWeight: 700 }}>{h.points > 0 ? `+${h.points}` : h.points}</div>
                                                    <div style={{ width: '100%', height: `${pct}%`, minHeight: '5px', borderRadius: '3px 3px 0 0', background: col, opacity: 0.85 }}
                                                        title={`ST-R${h.sdg_track_round}: ${h.choice} (+${h.points}pts) → Total: ${h.score}`} />
                                                    <div style={{ fontSize: '0.75rem', color: '#475569' }}>ST-R{h.sdg_track_round}</div>
                                                </div>
                                            );
                                        })}
                                        {/* Remaining potential bars (if track not fully completed) */}
                                        {history.length < 5 && Array.from({ length: 5 - history.length }).map((_, i) => (
                                            <div key={`empty-${i}`} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                                                <div style={{ fontSize: '0.75rem', color: '#1e293b' }}>—</div>
                                                <div style={{ width: '100%', height: '8px', borderRadius: '3px 3px 0 0', background: 'rgba(255,255,255,0.04)', border: '1px dashed rgba(255,255,255,0.08)' }} />
                                                <div style={{ fontSize: '0.75rem', color: '#334155' }}>ST-R{history.length + i + 1}</div>
                                            </div>
                                        ))}
                                    </div>
                                    {/* M_SDG trend line labels */}
                                    <div style={{ display: 'flex', gap: '0.35rem', marginTop: '6px' }}>
                                        {history.map((h, i) => (
                                            <div key={i} style={{ flex: 1, textAlign: 'center', fontSize: '0.75rem', color: '#475569', fontFamily: "'JetBrains Mono', monospace" }}>
                                                {ratio(h.m_sdg)}
                                            </div>
                                        ))}
                                        {history.length < 5 && Array.from({ length: 5 - history.length }).map((_, i) => (
                                            <div key={`ml-${i}`} style={{ flex: 1 }} />
                                        ))}
                                    </div>
                                    <div style={{ fontSize: '0.75rem', color: '#334155', textAlign: 'right', marginTop: '2px' }}>M_SDG per round →</div>
                                </div>
                            )}

                            {/* M_R bonus from Integrated Reporting */}
                            {sdgMrBonus > 0 && (
                                <div style={{ marginTop: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: '7px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', fontSize: '0.72rem', color: '#a7f3d0' }}>
                                    <strong>📊 Integrated Reporting Bonus:</strong> +{(sdgMrBonus * 100).toFixed(0)}% M_R uplift from codifying the Universal Care Mandate. This stacks multiplicatively at terminal valuation.
                                </div>
                            )}

                            {/* What-if: if they had NOT done the SDG track.
                                This line is itself a side-track result (it quantifies
                                what the SDG track earned), so it follows
                                `side_track_results` on top of its own guards. */}
                            {isPlayerVisible('side_track_results') && sdgCompleted && vT > 0 && mSdg > 1.0 && (
                                <div style={{ marginTop: '0.6rem', fontSize: '0.68rem', color: '#334155', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '0.6rem' }}>
                                    Without SDG track: V<sub>T</sub> would be{' '}
                                    <span style={{ color: '#64748b', fontWeight: 700, fontFamily: "'JetBrains Mono', monospace" }}>
                                        {currencySymbol()}{((vT / mSdg) / 1_000_000).toFixed(2)}M
                                    </span>{' '}
                                    — the SDG track added{' '}
                                    <span style={{ color: 'var(--kpi-good)', fontWeight: 800, fontFamily: "'JetBrains Mono', monospace" }}>
                                        {currencySymbol()}{((vT - vT / mSdg) / 1_000_000).toFixed(2)}M
                                    </span>{' '}
                                    in terminal enterprise value.
                                </div>
                            )}
                        </div>
                    );
                })()}

                {/* Actions */}
                <div className={styles.actions}>
                    {/* `interviewAvailable` is the facilitator-authored-questions probe;
                        the cohort switch is ANDed on top so both must allow the entry point. */}
                    {isPlayerVisible('ceo_interview') && interviewAvailable && !interviewCompleted && (
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
                    {isPlayerVisible('ceo_interview') && interviewCompleted && (
                        <button
                            className={styles.primaryBtn}
                            onClick={() => setShowInterview(true)}
                            style={{
                                background: 'linear-gradient(135deg, var(--kpi-good), var(--positive-deep))',
                            }}
                        >
                            ✅ View Interview Assessment
                        </button>
                    )}
                    {/* Hidden when the cohort disables the Balanced Scorecard.
                        Offering it anyway produced the "does not go to the right
                        page" report: the click fell through to the phase router,
                        which skipped the hidden scorecard and dropped the player
                        into an ALREADY-COMPLETED boardroom. A control that leads
                        nowhere is worse than no control. */}
                    {onReviewScorecard && (
                        <button className={styles.primaryBtn} onClick={onReviewScorecard}>
                            📊 Review Balanced Scorecard
                        </button>
                    )}
                    {isPlayerVisible('student_report_export') && (
                        <StudentReportExport
                            data={d}
                            globalState={globalState}
                            history={history}
                            businessUnits={businessUnits}
                            sessionId={sessionId}
                        />
                    )}
                    {/* The PDF path is implemented BY the scorecard (handleDownload
                        opens it), so it is only offered when the scorecard is
                        available — otherwise the button silently does nothing.
                        StudentReportExport above remains available regardless. */}
                    {onReviewScorecard && (
                        <button className={styles.secondaryBtn} onClick={handleDownload}>
                            📥 Download Report (PDF)
                        </button>
                    )}
                    {onLogout && (
                        <button className={styles.outlineBtn} onClick={() => { if (window.confirm('Log out? Your progress is saved and you can return anytime.')) onLogout(); }}>
                            🚪 Logout
                        </button>
                    )}
                </div>

                {/* CEO Interview Modal */}
                {isPlayerVisible('ceo_interview') && showInterview && (
                    <CEOInterview
                        sessionId={sessionId}
                        onClose={() => setShowInterview(false)}
                        onComplete={() => setInterviewCompleted(true)}
                    />
                )}

                {/* Footer */}
                <div className={styles.footer}>
                    <p>Muressons Global Corporation — Sustainability Strategy Simulation</p>
                    <p>© Year 5 Board of Directors Meeting</p>
                </div>
            </div>
        </div>
    );
}
