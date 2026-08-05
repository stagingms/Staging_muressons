'use client';

import { useState, useCallback } from 'react';
import { logoutAnchorStyle } from './logoutChrome';
import styles from './BoardroomShowdown.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * BoardroomShowdown — The Round 10 Grand Finale modal.
 *
 * Setting: A formal Board of Directors meeting. An activist rep from
 * "FutureFirst" tables a motion to break up Muressons.
 *
 * Props:
 *  - data: R10 finalReport data (extra_events from post_tick)
 *  - sessionId: current session ID
 *  - onComplete: () => void — called after submission to transition to SBSC
 */
export default function BoardroomShowdown({ data, sessionId, onComplete, onLogout }) {
    const [selectedOption, setSelectedOption] = useState(null);
    const [decadePlan, setDecadePlan] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [phase, setPhase] = useState('briefing'); // 'briefing' | 'decision' | 'plan'

    const d = data || {};
    const synergyScore = d.synergy_score || 0;
    const isResistDisabled = synergyScore <= 80;

    const OPTIONS = [
        {
            id: 'resist_integrate',
            title: 'Resist & Integrate',
            icon: '???',
            subtitle: 'Argue that Industrial Symbiosis makes the group more resilient together.',
            description:
                'Defend the conglomerate structure. Present evidence that cross-BU circular supply chains ' +
                'and shared natural capital strategies create more value combined than separated. The whole ' +
                'is greater than the sum of its parts.',
            impacts: [
                'Preserves synergy multiplier bonuses',
                'Highest Terminal Value potential if Synergy Score > 80',
                'Signals long-term commitment to stakeholders',
            ],
            disabled: isResistDisabled,
            disabledReason: `Blocked: Synergy Score (${synergyScore.toFixed(0)}) = 80 — insufficient integration to justify this argument.`,
            color: '#10b981',
            gradient: 'linear-gradient(135deg, #10b981, #059669)',
        },
        {
            id: 'strategic_spinoff',
            title: 'Strategic Spin-off',
            icon: '??',
            subtitle: 'Sell the high-carbon Electronics division to focus on Life Sciences & Software.',
            description:
                'Accept that the Electronics division\'s carbon intensity is dragging down the group\'s ESG rating. ' +
                'Divest it to a specialized buyer who can transition it independently. Focus capital on the ' +
                'two divisions with lower carbon footprints.',
            impacts: [
                'Removes weakest-margin BU from Terminal Value calculation',
                'Reduces Group Carbon Tonnage substantially',
                'Moderate market confidence boost',
            ],
            disabled: false,
            color: '#3b82f6',
            gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)',
        },
        {
            id: 'aggressive_divestment',
            title: 'Aggressive Divestment',
            icon: '??',
            subtitle: 'Agree with activists — break the company into four separate entities.',
            description:
                'The activist argument is compelling. The market would value four pure-play companies higher ' +
                'than one bloated conglomerate. Maximize short-term stock buyback value, even if it wipes out ' +
                'all synergy benefits and cross-BU resilience.',
            impacts: [
                'Synergy multiplier reset to 1.0×',
                'Short-term stock bump from breakup premium',
                'Destroys all cross-BU circularity gains',
            ],
            disabled: false,
            color: '#ef4444',
            gradient: 'linear-gradient(135deg, #ef4444, #dc2626)',
        },
    ];

    const handleSubmit = useCallback(async () => {
        if (!selectedOption || !decadePlan.trim() || !sessionId) return;
        setSubmitting(true);
        try {
            await fetch(`${API}/api/admin/${sessionId}/decade-plan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    boardroom_choice: selectedOption,
                    decade_forward_plan: decadePlan.trim(),
                }),
            });
            onComplete?.();
        } catch {
            // Backend unreachable — still proceed to SBSC
            onComplete?.();
        } finally {
            setSubmitting(false);
        }
    }, [selectedOption, decadePlan, sessionId, onComplete]);

    return (
        <div className={styles.overlay}>
            {onLogout && (
                <button
                    onClick={() => { if (window.confirm('Log out? Your progress is saved and you can return anytime.')) onLogout(); }}
                    style={{
                        ...logoutAnchorStyle(19000),
                        display: 'flex', alignItems: 'center', gap: 6, padding: '6px 14px',
                        background: 'rgba(15,23,42,0.75)', backdropFilter: 'blur(8px)',
                        border: '1px solid rgba(248,113,113,0.25)', borderRadius: 8,
                        color: '#fca5a5', fontSize: 'var(--type-caption)', fontWeight: 700,
                        fontFamily: "'DM Sans', system-ui, sans-serif",
                        cursor: 'pointer', transition: 'background 0.2s ease, color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease, transform 0.2s ease',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
                    }}
                    title="Logout & Exit Simulation"
                >
                    ?? Logout
                </button>
            )}
            <div className={styles.modal}>
                {/* -- Header -- */}
                <header className={styles.header}>
                    <div className={styles.headerBadge}>ROUND 10 • GRAND FINALE</div>
                    <h1 className={styles.title}>?? The Boardroom Showdown</h1>
                    <p className={styles.subtitle}>Muressons Global Corporation — Board of Directors Meeting, Year 5</p>
                </header>

                {/* -- Phase 1: Briefing -- */}
                {phase === 'briefing' && (
                    <section className={styles.briefing}>
                        <div className={styles.narrativeCard}>
                            <div className={styles.narrativeIcon}>??</div>
                            <div className={styles.narrativeContent}>
                                <h2>The FutureFirst Motion</h2>
                                <p>
                                    The boardroom falls silent as <strong>Dr. Amara Osei</strong>, activist board
                                    representative from the <strong>FutureFirst Alliance</strong>, rises to address the directors.
                                </p>
                                <blockquote className={styles.quote}>
                                    "Distinguished board members, I table a formal motion to <em>dissolve the Muressons
                                        conglomerate structure</em>. Our four business units — Pharmaceuticals, Electronics,
                                    Software, and Food & Beverage — are too fundamentally different to be managed
                                    sustainably under one roof.
                                    <br /><br />
                                    The evidence is clear: cross-subsidisation of high-carbon assets by green divisions
                                    is a form of corporate greenwashing. Each unit deserves its own sustainability
                                    mandate, its own carbon budget, and its own accountability structure.
                                    <br /><br />
                                    I call on the Chief Sustainability Officer to present their recommendation."
                                </blockquote>
                                <p className={styles.narrativeSubtext}>
                                    As CSO, you must now evaluate the activist's motion and recommend one of three
                                    alternatives to the Board. Your 10 rounds of performance data will be your evidence.
                                </p>
                            </div>
                        </div>

                        {/* Key stats for context */}
                        <div className={styles.statsBar}>
                            <div className={styles.stat}>
                                <span className={styles.statLabel}>Synergy Score</span>
                                <span className={styles.statValue} style={{ color: synergyScore > 80 ? '#10b981' : '#ef4444' }}>
                                    {synergyScore.toFixed(0)}
                                </span>
                            </div>
                            <div className={styles.stat}>
                                <span className={styles.statLabel}>Avg Social License</span>
                                <span className={styles.statValue}>
                                    {(d.avg_social_license || 0).toFixed(1)}
                                </span>
                            </div>
                            <div className={styles.stat}>
                                <span className={styles.statLabel}>Group Reputation</span>
                                <span className={styles.statValue}>
                                    {(d.group_reputation ?? 0).toFixed(1)}
                                </span>
                            </div>
                            <div className={styles.stat}>
                                <span className={styles.statLabel}>Carbon Tonnage</span>
                                <span className={styles.statValue}>
                                    {(d.carbon_tonnage_group || 0).toFixed(0)}
                                </span>
                            </div>
                        </div>

                        <button
                            className={styles.proceedBtn}
                            onClick={() => setPhase('decision')}
                        >
                            Present Your Recommendation ?
                        </button>
                    </section>
                )}

                {/* -- Phase 2: Decision -- */}
                {phase === 'decision' && (
                    <section className={styles.decisionPhase}>
                        <h2 className={styles.phaseTitle}>Choose Your Strategic Recommendation</h2>

                        <div className={styles.optionsGrid}>
                            {OPTIONS.map(opt => (
                                <button
                                    key={opt.id}
                                    className={`${styles.optionCard} ${selectedOption === opt.id ? styles.optionSelected : ''
                                        } ${opt.disabled ? styles.optionDisabled : ''}`}
                                    onClick={() => !opt.disabled && setSelectedOption(opt.id)}
                                    disabled={opt.disabled}
                                    style={{
                                        '--opt-color': opt.color,
                                        '--opt-gradient': opt.gradient,
                                    }}
                                >
                                    <div className={styles.optionHeader}>
                                        <span className={styles.optionIcon}>{opt.icon}</span>
                                        <h3>{opt.title}</h3>
                                    </div>
                                    <p className={styles.optionSubtitle}>{opt.subtitle}</p>
                                    <p className={styles.optionDesc}>{opt.description}</p>
                                    <ul className={styles.optionImpacts}>
                                        {opt.impacts.map((imp, i) => (
                                            <li key={i}>{imp}</li>
                                        ))}
                                    </ul>
                                    {opt.disabled && (
                                        <div className={styles.disabledNote}>{opt.disabledReason}</div>
                                    )}
                                    {selectedOption === opt.id && (
                                        <div className={styles.selectedBadge}>? Selected</div>
                                    )}
                                </button>
                            ))}
                        </div>

                        {selectedOption && (
                            <button
                                className={styles.proceedBtn}
                                onClick={() => setPhase('plan')}
                            >
                                Draft Your Decade Forward Plan ?
                            </button>
                        )}
                    </section>
                )}

                {/* -- Phase 3: Decade Forward Plan -- */}
                {phase === 'plan' && (
                    <section className={styles.planPhase}>
                        <div className={styles.planHeader}>
                            <h2 className={styles.phaseTitle}>?? Recommendation & Forward Plan (Next Decade)</h2>
                            <div className={styles.selectedChoice}>
                                Strategy: <strong>{OPTIONS.find(o => o.id === selectedOption)?.title}</strong>
                            </div>
                        </div>

                        <p className={styles.planInstruction}>
                            Draft a brief strategic plan justifying your choice to the Board. Use your 10-round
                            performance data as evidence. Consider how your chosen path will affect the company's
                            financial sustainability, stakeholder relationships, and environmental obligations
                            over the next decade.
                        </p>

                        <textarea
                            className={styles.planTextarea}
                            value={decadePlan}
                            onChange={(e) => setDecadePlan(e.target.value)}
                            placeholder={
                                "?? Click here and type your strategic plan...\n\n" +
                                "Dear Board Members,\n\n" +
                                "Based on our 10-round simulation performance, I recommend...\n\n" +
                                "Key evidence supporting this recommendation:\n" +
                                "1. \n2. \n3. \n\n" +
                                "Over the next decade, this strategy will...\n\n" +
                                "Respectfully submitted,\n" +
                                "Chief Sustainability Officer"
                            }
                            rows={14}
                        />

                        <div className={styles.planFooter}>
                            <button
                                className={styles.backBtn}
                                onClick={() => setPhase('decision')}
                            >
                                ? Change Selection
                            </button>
                            <button
                                className={styles.submitBtn}
                                onClick={handleSubmit}
                                disabled={!decadePlan.trim() || submitting}
                            >
                                {submitting ? '? Submitting...' : '?? Submit to the Board'}
                            </button>
                        </div>

                        {!decadePlan.trim() && (
                            <div className={styles.planWarning}>
                                ?? You must draft a strategic plan before submitting to the Board.
                            </div>
                        )}
                    </section>
                )}
            </div>
        </div>
    );
}
