'use client';
/**
 * PedagogicalScaffolding.js
 * 
 * Unified component suite for pedagogical enhancement features.
 * Contains: PredictionGate, BoardRoomMoment, MentalModelTracker,
 * ConfidenceCalibration, RoundRecap, RealWorldCard, StrategyMemo,
 * MidGameCheckpoint, DebriefProtocol.
 * 
 * All components respect facilitator toggles and are player-facing.
 */

import React, { useState, useEffect, useCallback } from 'react';
import styles from './PedagogicalScaffolding.module.css';
import { currencySymbol, atRate } from '../utils/format';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/* ═══════════════════════════════════════════════════════════════
   1. PREDICTION GATE (Pre-Mortem)
   Klein (2007): Prospective hindsight before each decision.
   ═══════════════════════════════════════════════════════════════ */

export function PredictionGate({ roundNumber, choiceSelected, onSubmit, previousPredictions = [] }) {
    const [prediction, setPrediction] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = () => {
        if (!prediction.trim()) return;
        onSubmit?.({
            round: roundNumber,
            prediction: prediction.trim(),
            choice_selected: choiceSelected,
        });
        setSubmitted(true);
    };

    if (submitted) {
        return (
            <div className={styles.predictionGate}>
                <div className={styles.pgHeader}>
                    <span className={styles.pgIcon}>🔮</span>
                    <h4>Prediction Logged</h4>
                </div>
                <div className={styles.pgSubmitted}>
                    <p className={styles.pgQuote}>"{prediction}"</p>
                    <span className={styles.pgBadge}>✅ Saved — you'll see the outcome after this round resolves</span>
                </div>
                {previousPredictions.length > 0 && (
                    <div className={styles.pgHistory}>
                        <h5>Your Prediction Track Record</h5>
                        {previousPredictions.map((p, i) => (
                            <div key={i} className={`${styles.pgHistoryItem} ${styles[`pg_${p.calibration || 'pending'}`]}`}>
                                <span className={styles.pgHistoryRound}>R{p.round}</span>
                                <span className={styles.pgHistoryText}>{p.prediction}</span>
                                <span className={styles.pgHistoryBadge}>{p.calibration_icon || '⏳'}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className={styles.predictionGate}>
            <div className={styles.pgHeader}>
                <span className={styles.pgIcon}>🔮</span>
                <h4>Pre-Decision Prediction</h4>
            </div>
            <p className={styles.pgPrompt}>
                Before you commit: <strong>What do you think will happen</strong> as a result of this decision?
                What's the best outcome? What could go wrong?
            </p>
            <textarea
                className={styles.pgTextarea}
                value={prediction}
                onChange={e => setPrediction(e.target.value)}
                placeholder="I predict that choosing this option will..."
                rows={3}
                maxLength={500}
            />
            <div className={styles.pgActions}>
                <span className={styles.pgCharCount}>{prediction.length}/500</span>
                <button className={styles.pgSubmitBtn} onClick={handleSubmit} disabled={!prediction.trim()}>
                    Lock Prediction & Proceed
                </button>
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   2. BOARD ROOM MOMENT (Moon 2004 Three-Stage Reflection)
   ═══════════════════════════════════════════════════════════════ */

export function BoardRoomMoment({ roundNumber, onSubmit, triggerReason = '' }) {
    const [stage, setStage] = useState(0); // 0=noticing, 1=making_sense, 2=working_with_meaning
    const [responses, setResponses] = useState({ noticing: '', making_sense: '', working_with_meaning: '' });
    const [submitted, setSubmitted] = useState(false);

    const STAGES = [
        { key: 'noticing', label: 'Noticing', icon: '👁️', duration: 30,
          prompt: 'What surprised you about the outcome of this round?', level: 'Descriptive' },
        { key: 'making_sense', label: 'Making Sense', icon: '🧠', duration: 60,
          prompt: 'Why do you think this happened? What causal chain produced this result?', level: 'Analytical' },
        { key: 'working_with_meaning', label: 'Working with Meaning', icon: '🎯', duration: 60,
          prompt: 'What does this tell you about your assumptions? What will you change?', level: 'Evaluative' },
    ];

    const current = STAGES[stage];

    const handleNext = () => {
        if (stage < 2) {
            setStage(stage + 1);
        } else {
            onSubmit?.({ round: roundNumber, ...responses });
            setSubmitted(true);
        }
    };

    if (submitted) {
        return (
            <div className={styles.boardRoom}>
                <div className={styles.brHeader}>
                    <span className={styles.brIcon}>🏢</span>
                    <h4>Board Room Reflection Complete</h4>
                </div>
                <div className={styles.brSummary}>
                    {STAGES.map((s, i) => (
                        <div key={s.key} className={styles.brSummaryItem}>
                            <span className={styles.brSummaryIcon}>{s.icon}</span>
                            <div>
                                <strong>{s.label}</strong>
                                <p>{responses[s.key]}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className={styles.boardRoom}>
            <div className={styles.brHeader}>
                <span className={styles.brIcon}>🏢</span>
                <h4>Board Room Moment</h4>
            </div>
            {triggerReason && (
                <div className={styles.brTrigger}>
                    ⚡ Triggered by: {triggerReason}
                </div>
            )}
            <div className={styles.brProgress}>
                {STAGES.map((s, i) => (
                    <div key={s.key} className={`${styles.brProgressStep} ${i <= stage ? styles.brProgressActive : ''} ${i < stage ? styles.brProgressDone : ''}`}>
                        <span>{s.icon}</span>
                        <span>{s.label}</span>
                    </div>
                ))}
            </div>
            <div className={styles.brStage}>
                <div className={styles.brStageHeader}>
                    <span className={styles.brStageBadge}>{current.level}</span>
                    <span className={styles.brStageDuration}>⏱ {current.duration}s recommended</span>
                </div>
                <p className={styles.brStagePrompt}>{current.prompt}</p>
                <textarea
                    className={styles.brTextarea}
                    value={responses[current.key]}
                    onChange={e => setResponses(prev => ({ ...prev, [current.key]: e.target.value }))}
                    placeholder="Type your reflection here..."
                    rows={3}
                />
            </div>
            <div className={styles.brActions}>
                {stage > 0 && (
                    <button className={styles.brBackBtn} onClick={() => setStage(stage - 1)}>← Back</button>
                )}
                <button className={styles.brNextBtn} onClick={handleNext} disabled={!responses[current.key]?.trim()}>
                    {stage < 2 ? `Next: ${STAGES[stage + 1].label} →` : '✓ Submit Reflection'}
                </button>
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   3. CONFIDENCE CALIBRATION ("Would You Bet?")
   ═══════════════════════════════════════════════════════════════ */

export function ConfidenceCalibration({ roundNumber, choiceLabel, onSubmit, calibrationHistory = [] }) {
    const [confidence, setConfidence] = useState(3);
    const [submitted, setSubmitted] = useState(false);

    const LABELS = ['Very Unsure', 'Unsure', 'Neutral', 'Confident', 'Very Confident'];
    const EMOJIS = ['😰', '😟', '🤔', '😊', '🤩'];

    const handleSubmit = () => {
        onSubmit?.({ round: roundNumber, confidence, choice: choiceLabel });
        setSubmitted(true);
    };

    if (submitted) {
        return (
            <div className={styles.confidence}>
                <div className={styles.confHeader}>
                    <span>🎰</span>
                    <h4>Confidence: {EMOJIS[confidence - 1]} {LABELS[confidence - 1]}</h4>
                </div>
                <span className={styles.confBadge}>Logged — we'll show your calibration curve after R10</span>
            </div>
        );
    }

    return (
        <div className={styles.confidence}>
            <div className={styles.confHeader}>
                <span>🎰</span>
                <h4>Would You Bet On This Decision?</h4>
            </div>
            <p className={styles.confPrompt}>
                How confident are you that <strong>{choiceLabel || 'your choice'}</strong> is the right decision?
            </p>
            <div className={styles.confSlider}>
                <input
                    type="range" min="1" max="5" value={confidence}
                    onChange={e => setConfidence(Number(e.target.value))}
                    className={styles.confRange}
                />
                <div className={styles.confLabels}>
                    {LABELS.map((l, i) => (
                        <span key={i} className={i + 1 === confidence ? styles.confLabelActive : ''}>
                            {EMOJIS[i]}
                        </span>
                    ))}
                </div>
                <div className={styles.confValue}>
                    {EMOJIS[confidence - 1]} {LABELS[confidence - 1]}
                </div>
            </div>
            <button className={styles.confSubmitBtn} onClick={handleSubmit}>Lock Confidence Rating</button>
            {calibrationHistory.length > 0 && (
                <div className={styles.confHistory}>
                    <h5>Your Calibration History</h5>
                    <div className={styles.confHistoryGrid}>
                        {calibrationHistory.map((h, i) => (
                            <div key={i} className={styles.confHistoryItem}>
                                <span>R{h.round}</span>
                                <span>{EMOJIS[h.confidence - 1]}</span>
                                <span className={h.overconfident ? styles.confOver : h.underconfident ? styles.confUnder : styles.confCalibrated}>
                                    {h.overconfident ? '↑ Over' : h.underconfident ? '↓ Under' : '✓ Calibrated'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   4. ROUND RECAP ("What Just Happened?")
   ═══════════════════════════════════════════════════════════════ */

export function RoundRecap({ recapData }) {
    if (!recapData) return null;

    const { three_word_anchor, causal_chains = [], summary_sentence, round, choice_selected } = recapData;

    // B3: Group chains by source type for attributable recap
    const decisionChains = causal_chains.filter(c => c.source_type === 'decision');
    const backgroundChains = causal_chains.filter(c => c.source_type !== 'decision');
    const hasGrouping = causal_chains.some(c => c.source_label);
    const [bgExpanded, setBgExpanded] = useState(false);

    const renderChain = (chain, i) => (
        <div key={`${chain.engine_id || 'chain'}-${i}`} className={`${styles.rrChain} ${styles[`rr_${chain.source_type}`]}`}>
            <span className={styles.rrChainIcon}>{chain.source_icon}</span>
            <div className={styles.rrChainContent}>
                <span className={styles.rrChainEngine}>{chain.engine_id}</span>
                <p className={styles.rrChainNarrative}>{chain.narrative}</p>
            </div>
        </div>
    );

    return (
        <div className={styles.roundRecap}>
            <div className={styles.rrHeader}>
                <span className={styles.rrIcon}>📋</span>
                <h4>What Just Happened?</h4>
                <span className={styles.rrRound}>Round {round}</span>
            </div>
            {three_word_anchor && (
                <div className={styles.rrAnchor}>
                    <span className={styles.rrAnchorLabel}>Three-Word Summary</span>
                    <span className={styles.rrAnchorText}>{three_word_anchor}</span>
                </div>
            )}

            {/* B3: Attributable grouping — decision vs background */}
            {hasGrouping && decisionChains.length > 0 ? (
                <>
                    <div style={{ fontSize: 'var(--type-caption)', fontWeight: 700, color: 'var(--kpi-good)', margin: '8px 0 4px', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                        🎯 Because of your decision
                    </div>
                    <div className={styles.rrChains}>
                        {decisionChains.map(renderChain)}
                    </div>
                    {backgroundChains.length > 0 && (
                        <>
                            <button
                                onClick={() => setBgExpanded(!bgExpanded)}
                                style={{
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    fontSize: 'var(--type-caption)', fontWeight: 600, color: 'var(--text-muted)',
                                    margin: '6px 0 2px', padding: 0, letterSpacing: '0.04em',
                                    textTransform: 'uppercase', fontFamily: 'inherit',
                                }}
                            >
                                {bgExpanded ? '▼' : '▶'} Background movements ({backgroundChains.length})
                            </button>
                            {bgExpanded && (
                                <div className={styles.rrChains}>
                                    {backgroundChains.map(renderChain)}
                                </div>
                            )}
                        </>
                    )}
                </>
            ) : (
                /* Fallback: flat display (backward compatible) */
                <div className={styles.rrChains}>
                    {causal_chains.map(renderChain)}
                </div>
            )}

            {summary_sentence && (
                <div className={styles.rrSummary}>
                    <p>{summary_sentence}</p>
                </div>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   5. REAL WORLD PARALLEL CARD
   Baldwin & Ford (1988): Transfer design
   ═══════════════════════════════════════════════════════════════ */

export function RealWorldCard({ roundNumber }) {
    const [card, setCard] = useState(null);
    const [expanded, setExpanded] = useState(false);

    useEffect(() => {
        fetch(`${API}/api/admin/pedagogical/real-world-parallels/${roundNumber}`)
            .then(r => r.json())
            .then(d => setCard(d.parallel))
            .catch(() => {});
    }, [roundNumber]);

    if (!card) return null;

    return (
        <div className={`${styles.realWorld} ${expanded ? styles.rwExpanded : ''}`}>
            <button type="button" className={styles.rwHeader} onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>
                <span className={styles.rwIcon}>{card.icon}</span>
                <div className={styles.rwHeaderText}>
                    <h4>{card.title}</h4>
                    <span className={styles.rwCompany}>{card.company}</span>
                </div>
                <span className={styles.rwToggle}>{expanded ? '▲' : '▼'}</span>
            </button>
            {expanded && (
                <div className={styles.rwBody}>
                    <div className={styles.rwSection}>
                        <h5>📰 The Case</h5>
                        <p>{card.brief}</p>
                    </div>
                    <div className={styles.rwSection}>
                        <h5>🎮 Simulation Parallel</h5>
                        <p>{card.simulation_parallel}</p>
                    </div>
                    <div className={styles.rwSection}>
                        <h5>📊 Outcome</h5>
                        <p>{card.outcome}</p>
                    </div>
                    <div className={styles.rwLesson}>
                        <span className={styles.rwLessonIcon}>💡</span>
                        <strong>{card.key_lesson}</strong>
                    </div>
                    <div className={styles.rwTheory}>
                        <span>📖</span>
                        <em>{card.theory_link}</em>
                    </div>
                </div>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   6. MENTAL MODEL TRACKER (R1, R5, R10)
   ═══════════════════════════════════════════════════════════════ */

export function MentalModelTracker({ roundNumber, onSubmit, previousRankings = [] }) {
    const [factors, setFactors] = useState([]);
    const [ranking, setRanking] = useState([]);
    const [submitted, setSubmitted] = useState(false);
    const [dragItem, setDragItem] = useState(null);

    useEffect(() => {
        fetch(`${API}/api/admin/pedagogical/mental-model-factors`)
            .then(r => r.json())
            .then(d => {
                setFactors(d.factors || []);
                setRanking((d.factors || []).map(f => f.id));
            })
            .catch(() => {});
    }, []);

    const handleDragStart = (idx) => setDragItem(idx);
    const handleDragOver = (e, idx) => {
        e.preventDefault();
        if (dragItem === null || dragItem === idx) return;
        const newRanking = [...ranking];
        const item = newRanking.splice(dragItem, 1)[0];
        newRanking.splice(idx, 0, item);
        setRanking(newRanking);
        setDragItem(idx);
    };

    const handleSubmit = () => {
        onSubmit?.({ round: roundNumber, ranking });
        setSubmitted(true);
    };

    const factorMap = Object.fromEntries(factors.map(f => [f.id, f]));

    // Check if this is a collection round
    const COLLECTION_ROUNDS = [1, 5, 10];
    if (!COLLECTION_ROUNDS.includes(roundNumber)) return null;

    if (submitted) {
        return (
            <div className={styles.mentalModel}>
                <div className={styles.mmHeader}>
                    <span>🧬</span>
                    <h4>Mental Model Snapshot — Round {roundNumber}</h4>
                </div>
                <div className={styles.mmSubmitted}>
                    {ranking.map((id, i) => (
                        <div key={id} className={styles.mmRankItem}>
                            <span className={styles.mmRankPos}>#{i + 1}</span>
                            <span style={{ color: factorMap[id]?.color }}>{factorMap[id]?.label || id}</span>
                        </div>
                    ))}
                </div>
                <span className={styles.mmBadge}>✅ Saved — you'll see your mental model evolution at R10</span>
            </div>
        );
    }

    return (
        <div className={styles.mentalModel}>
            <div className={styles.mmHeader}>
                <span>🧬</span>
                <h4>What Matters Most to You?</h4>
                <span className={styles.mmRound}>Snapshot {COLLECTION_ROUNDS.indexOf(roundNumber) + 1}/3</span>
            </div>
            <p className={styles.mmPrompt}>
                Drag to rank these factors from <strong>most important</strong> (top) to <strong>least important</strong> (bottom)
                for a successful company:
            </p>
            <div className={styles.mmList}>
                {ranking.map((id, idx) => {
                    const f = factorMap[id];
                    if (!f) return null;
                    return (
                        <div
                            key={id}
                            className={styles.mmDragItem}
                            draggable
                            onDragStart={() => handleDragStart(idx)}
                            onDragOver={(e) => handleDragOver(e, idx)}
                            onDragEnd={() => setDragItem(null)}
                            style={{ borderLeftColor: f.color }}
                        >
                            <span className={styles.mmDragHandle}>⠿</span>
                            <span className={styles.mmDragPos}>#{idx + 1}</span>
                            <span className={styles.mmDragLabel} style={{ color: f.color }}>{f.label}</span>
                        </div>
                    );
                })}
            </div>
            <button className={styles.mmSubmitBtn} onClick={handleSubmit}>Lock Ranking</button>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   7. MID-GAME CHECKPOINT (R5 Formative Assessment)
   ═══════════════════════════════════════════════════════════════ */

export function MidGameCheckpoint({ checkpointData }) {
    const [expanded, setExpanded] = useState(true);
    if (!checkpointData) return null;

    const { projected_mr, projected_tv_range, bonuses_earned = [],
            bonuses_locked_out = [], top_risk, all_recommendations = [],
            current_archetype_projection } = checkpointData;

    const mrColor = projected_mr >= 1.8 ? '#10b981' : projected_mr >= 1.2 ? '#6366f1' : projected_mr >= 0.8 ? '#f59e0b' : '#ef4444';

    return (
        <div className={styles.checkpoint}>
            <button type="button" className={styles.cpHeader} onClick={() => setExpanded(!expanded)} aria-expanded={expanded}>
                <span className={styles.cpIcon}>📍</span>
                <h4>Mid-Game Checkpoint — Round 5</h4>
                <span className={styles.cpArchetype} style={{ color: mrColor }}>
                    Projected: {current_archetype_projection}
                </span>
                <span className={styles.cpToggle}>{expanded ? '▲' : '▼'}</span>
            </button>
            {expanded && (
                <div className={styles.cpBody}>
                    <div className={styles.cpMetrics}>
                        <div className={styles.cpMetric}>
                            <span className={styles.cpMetricLabel}>Projected M_R</span>
                            <span className={styles.cpMetricValue} style={{ color: mrColor }}>
                                {projected_mr}×
                            </span>
                        </div>
                        {projected_tv_range && (
                            <div className={styles.cpMetric}>
                                <span className={styles.cpMetricLabel}>Terminal Value Range</span>
                                <span className={styles.cpMetricValue}>
                                   {currencySymbol()}{atRate(projected_tv_range.low / 1e6).toFixed(0)}M – {currencySymbol()}{atRate(projected_tv_range.high / 1e6).toFixed(0)}M
                                </span>
                            </div>
                        )}
                    </div>
                    {bonuses_earned.length > 0 && (
                        <div className={styles.cpSection}>
                            <h5>✅ Bonuses Earned</h5>
                            {bonuses_earned.map((b, i) => (
                                <div key={i} className={styles.cpBonusEarned}>🏆 {b}</div>
                            ))}
                        </div>
                    )}
                    {bonuses_locked_out.length > 0 && (
                        <div className={styles.cpSection}>
                            <h5>🔒 Locked Out</h5>
                            {bonuses_locked_out.map((b, i) => (
                                <div key={i} className={styles.cpBonusLocked}>❌ {b}</div>
                            ))}
                        </div>
                    )}
                    {top_risk && (
                        <div className={styles.cpRisk}>
                            <span>⚠️</span>
                            <strong>Top Risk:</strong> {top_risk}
                        </div>
                    )}
                    {all_recommendations.length > 0 && (
                        <div className={styles.cpSection}>
                            <h5>💡 Recommendations</h5>
                            {all_recommendations.map((r, i) => (
                                <div key={i} className={styles.cpRecommendation}>→ {r}</div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   8. DEBRIEF PROTOCOL (Thiagarajan 1993)
   ═══════════════════════════════════════════════════════════════ */

export function DebriefProtocol() {
    const [protocol, setProtocol] = useState(null);
    const [activePhase, setActivePhase] = useState(null);

    useEffect(() => {
        fetch(`${API}/api/admin/pedagogical/debrief-protocol`, { credentials: 'include' })
            .then(r => r.json())
            .then(d => setProtocol(d.protocol))
            .catch(() => {});
    }, []);

    if (!protocol) return null;

    const phases = Object.entries(protocol);

    return (
        <div className={styles.debrief}>
            <div className={styles.dbHeader}>
                <span>🎭</span>
                <h4>Structured Debrief Protocol</h4>
            </div>
            <div className={styles.dbPhases}>
                {phases.map(([key, phase], i) => (
                    <button
                        type="button"
                        key={key}
                        className={`${styles.dbPhase} ${activePhase === key ? styles.dbPhaseActive : ''}`}
                        onClick={() => setActivePhase(activePhase === key ? null : key)}
                        aria-expanded={activePhase === key}
                    >
                        <div className={styles.dbPhaseHeader}>
                            <span className={styles.dbPhaseIcon}>{phase.icon}</span>
                            <div>
                                <h5>{phase.title}</h5>
                                <span className={styles.dbPhaseDuration}>⏱ {phase.duration_min} min</span>
                            </div>
                        </div>
                        {activePhase === key && (
                            <div className={styles.dbPhaseBody}>
                                <p className={styles.dbInstruction}>{phase.instruction}</p>
                                <div className={styles.dbFacilitatorPrompt}>
                                    <span>🎤 Say:</span>
                                    <em>"{phase.facilitator_prompt}"</em>
                                </div>
                            </div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
}


/* IMP-04 (audit 2026-09-04, WP-22): the R6/R7/R8 journey panels promised
   effects (consequences that would "unfold", impacts that would "apply at
   round resolution") that no engine ever applied, and posted the player's
   answers to a super-admin settings route. They are reflection exercises: the note
   below says so on every panel, and the answers go to the player
   journey-response endpoint for the facilitator's debrief. */
const REFLECTION_NOTE = "Reflection exercise — your answer is recorded for the facilitator's debrief. It does not change the simulation's numbers.";

/* ═══════════════════════════════════════════════════════════════
   9. R6 REVELATION PANEL (Kolb 1984 Reflective Observation)
   Post-decision twist — whistleblower leak with micro-decisions.
   ═══════════════════════════════════════════════════════════════ */

export function R6RevelationPanel({ onMicroDecision, onVisible }) {
    const [revelation, setRevelation] = useState(null);
    const [selected, setSelected] = useState(null);
    const [submitted, setSubmitted] = useState(false);

    useEffect(() => {
        fetch(`${API}/api/admin/journey/r6-revelation`)
            .then(r => r.json())
            .then(d => { setRevelation(d.revelation); if (d.revelation?.enabled) onVisible?.(); })
            .catch(() => {});
    }, []);

    if (!revelation || !revelation.enabled) return null;

    const handleSubmit = () => {
        if (!selected) return;
        onMicroDecision?.({
            decision_key: selected,
            ...revelation.micro_decisions[selected],
        });
        setSubmitted(true);
    };

    if (submitted) {
        const choice = revelation.micro_decisions[selected];
        return (
            <div className={styles.predictionGate} style={{ borderColor: 'rgba(239, 68, 68, 0.35)' }}>
                <div className={styles.pgHeader}>
                    <span className={styles.pgIcon}>🚨</span>
                    <h4>Response Logged</h4>
                </div>
                <div className={styles.pgSubmitted}>
                    <p className={styles.pgQuote}>{choice.icon} {choice.label}</p>
                    <span className={styles.pgBadge}>✅ Response recorded for the debrief (reflection exercise — no engine impact)</span>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.predictionGate} style={{ borderColor: 'rgba(239, 68, 68, 0.35)' }}>
            <div className={styles.pgHeader}>
                <span className={styles.pgIcon}>🚨</span>
                <h4>{revelation.title}</h4>
            </div>
            <p className={styles.pgPrompt}>{revelation.narrative}</p>
            <p className={styles.pgTheory} data-testid="journey-reflection-note">{revelation.note || REFLECTION_NOTE}</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {Object.entries(revelation.micro_decisions).map(([key, dec]) => (
                    <button
                        key={key}
                        onClick={() => setSelected(key)}
                        style={{
                            padding: '10px 14px', borderRadius: 8, textAlign: 'left',
                            border: selected === key ? '2px solid #ef4444' : '1px solid var(--border-subtle)',
                            background: selected === key ? 'rgba(239, 68, 68, 0.06)' : 'var(--bg-secondary)',
                            color: 'var(--text-primary)', cursor: 'pointer',
                            transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                        }}
                    >
                        <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: 4 }}>
                            {dec.icon} {dec.label}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                            {dec.description}
                        </div>
                        {dec.stochastic && (
                            <div style={{ fontSize: 'var(--type-caption)', color: '#f59e0b', marginTop: 4 }}>
                                ⚠️ {(dec.stochastic.backfire_probability * 100).toFixed(0)}% backfire probability
                            </div>
                        )}
                    </button>
                ))}
            </div>
            <div className={styles.pgActions} style={{ marginTop: 10 }}>
                <span className={styles.pgTheory}>{revelation.pedagogical_purpose}</span>
                <button className={styles.pgSubmitBtn} onClick={handleSubmit} disabled={!selected}
                    style={{ background: selected ? 'linear-gradient(135deg, #dc2626, #ef4444)' : undefined }}>
                    Confirm Response
                </button>
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   10. BUDGET ALLOCATION PANEL (R7 Mechanic Variant)
   Thiagarajan (2006): Slider-based trade-off instead of A/B/C.
   ═══════════════════════════════════════════════════════════════ */

export function BudgetAllocationPanel({ onAllocate, onVisible }) {
    const [variant, setVariant] = useState(null);
    const [allocs, setAllocs] = useState({});
    const [submitted, setSubmitted] = useState(false);

    useEffect(() => {
        fetch(`${API}/api/admin/journey/mechanic-variant/7`)
            .then(r => r.json())
            .then(d => {
                if (d.variant?.enabled) {
                    setVariant(d.variant);
                    const init = {};
                    Object.keys(d.variant.initiatives).forEach(k => { init[k] = 5_000_000; });
                    setAllocs(init);
                    onVisible?.();
                }
            })
            .catch(() => {});
    }, []);

    if (!variant) return null;

    const totalBudget = variant.total_budget;
    const totalAllocated = Object.values(allocs).reduce((s, v) => s + v, 0);
    const remaining = totalBudget - totalAllocated;

    const handleChange = (key, value) => {
        const v = Math.max(0, Math.min(totalBudget, value));
        setAllocs(prev => ({ ...prev, [key]: v }));
    };

    const handleSubmit = () => {
        if (remaining < 0) return;
        onAllocate?.(allocs);
        setSubmitted(true);
    };

    if (submitted) {
        return (
            <div className={styles.mentalModel} style={{ borderColor: 'rgba(16, 185, 129, 0.3)' }}>
                <div className={styles.mmHeader}>
                    <span>♻️</span>
                    <h4>Circular Economy Budget Locked</h4>
                </div>
                <div className={styles.mmSubmitted}>
                    {Object.entries(variant.initiatives).map(([key, init]) => (
                        <div key={key} className={styles.mmRankItem}>
                            <span className={styles.mmRankPos}>{init.icon}</span>
                            <span style={{ flex: 1 }}>{init.label}</span>
                            <span style={{ fontWeight: 800, color: '#10b981' }}>
                               {currencySymbol()}{atRate(allocs[key] / 1_000_000).toFixed(1)}M
                            </span>
                        </div>
                    ))}
                </div>
                <span className={styles.mmBadge}>✅ Allocation recorded for the debrief (reflection exercise — no engine impact)</span>
            </div>
        );
    }

    return (
        <div className={styles.mentalModel} style={{ borderColor: 'rgba(16, 185, 129, 0.3)' }}>
            <div className={styles.mmHeader}>
                <span>♻️</span>
                <h4>{variant.title}</h4>
                <span className={styles.mmRound}>
                   {currencySymbol()}{atRate(remaining / 1_000_000).toFixed(1)}M remaining
                </span>
            </div>
            <p className={styles.mmPrompt}>{variant.instruction}</p>
            <p className={styles.pgTheory} data-testid="journey-reflection-note">{variant.note || REFLECTION_NOTE}</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {Object.entries(variant.initiatives).map(([key, init]) => (
                    <div key={key} style={{
                        padding: '14px 16px', borderRadius: 10,
                        background: '#f8fafc',
                        border: '1.5px solid #e2e8f0',
                        transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                            <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#0f172a' }}>{init.icon} {init.label}</span>
                            <span style={{ fontWeight: 800, color: '#059669', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.9rem' }}>
                               {currencySymbol()}{atRate(allocs[key] / 1_000_000).toFixed(1)}M
                            </span>
                        </div>
                        <div style={{ fontSize: '0.78rem', color: '#64748b', marginBottom: 10, lineHeight: 1.5 }}>
                            {init.description}
                        </div>
                        <input
                            type="range" min={0} max={totalBudget} step={500_000}
                            value={allocs[key]}
                            onChange={e => handleChange(key, Number(e.target.value))}
                            style={{ width: '100%', accentColor: '#10b981', height: 6 }}
                        />
                        {allocs[key] >= init.synergy_threshold && (
                            <div style={{ fontSize: 'var(--type-caption)', color: '#d97706', marginTop: 6, fontWeight: 600 }}>
                                🎯 Above the synergy threshold — worth defending in the debrief
                            </div>
                        )}
                    </div>
                ))}
            </div>
            {remaining < 0 && (
                <div style={{ color: '#ef4444', fontSize: '0.78rem', marginTop: 8 }}>
                    ⚠️ Over budget by{currencySymbol()}{atRate(Math.abs(remaining) / 1_000_000).toFixed(1)}M — reduce allocations
                </div>
            )}
            <button className={styles.mmSubmitBtn} onClick={handleSubmit} disabled={remaining < 0}
                style={{ marginTop: 10, background: remaining < 0 ? '#475569' : undefined }}>
                ✓ Lock Allocation
            </button>
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   11. STAKEHOLDER TRIBUNAL (R8 Mechanic Variant)
   Freeman (1984): Sequential stakeholder challenges under pressure.
   ═══════════════════════════════════════════════════════════════ */

export function StakeholderTribunal({ onResponses, onVisible }) {
    const [variant, setVariant] = useState(null);
    const [currentIdx, setCurrentIdx] = useState(0);
    const [responses, setResponses] = useState({});
    const [submitted, setSubmitted] = useState(false);

    useEffect(() => {
        fetch(`${API}/api/admin/journey/mechanic-variant/8`)
            .then(r => r.json())
            .then(d => { if (d.variant?.enabled) { setVariant(d.variant); onVisible?.(); } })
            .catch(() => {});
    }, []);

    if (!variant) return null;

    const challenges = variant.challenges;
    const current = challenges[currentIdx];
    const allAnswered = Object.keys(responses).length === challenges.length;

    const handleResponse = (key) => {
        setResponses(prev => ({ ...prev, [currentIdx]: key }));
        if (currentIdx < challenges.length - 1) {
            setTimeout(() => setCurrentIdx(currentIdx + 1), 300);
        }
    };

    const handleSubmit = () => {
        if (!allAnswered) return;
        onResponses?.(responses);
        setSubmitted(true);
    };

    if (submitted) {
        return (
            <div className={styles.boardRoom} style={{ borderColor: 'rgba(245, 158, 11, 0.3)' }}>
                <div className={styles.brHeader}>
                    <span className={styles.brIcon}>⚖️</span>
                    <h4>Tribunal Responses Logged</h4>
                </div>
                <div className={styles.brSummary}>
                    {challenges.map((ch, i) => {
                        const resp = ch.responses[responses[i]];
                        return (
                            <div key={i} className={styles.brSummaryItem}>
                                <span className={styles.brSummaryIcon}>{ch.icon}</span>
                                <div>
                                    <strong>{ch.stakeholder}</strong>
                                    <p>{resp?.label}</p>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    }

    return (
        <div className={styles.boardRoom} style={{ borderColor: 'rgba(245, 158, 11, 0.3)' }}>
            <div className={styles.brHeader}>
                <span className={styles.brIcon}>⚖️</span>
                <h4>{variant.title}</h4>
                <span className={styles.brTheory}>Freeman (1984) Stakeholder Theory</span>
            </div>
            <p className={styles.pgPrompt} style={{ marginBottom: 12 }}>{variant.instruction}</p>
            <p className={styles.pgTheory} data-testid="journey-reflection-note">{variant.note || REFLECTION_NOTE}</p>

            {/* Progress */}
            <div className={styles.brProgress}>
                {challenges.map((ch, i) => (
                    <div key={i} className={`${styles.brProgressStep} ${i === currentIdx ? styles.brProgressActive : ''} ${i < currentIdx ? styles.brProgressDone : ''}`}>
                        <span>{ch.icon}</span>
                        <span style={{ fontSize: 'var(--type-caption)' }}>{ch.stakeholder.split(' ')[0]}</span>
                    </div>
                ))}
            </div>

            {/* Current Challenge */}
            <div className={styles.brStage}>
                <div className={styles.brStageHeader}>
                    <span className={styles.brStageBadge}>{current.icon} {current.stakeholder}</span>
                    <span className={styles.brStageDuration}>⏱ {variant.response_time_seconds}s</span>
                </div>
                <p className={styles.brStagePrompt} style={{ fontStyle: 'italic' }}>
                    "{current.challenge}"
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {Object.entries(current.responses).map(([key, resp]) => (
                        <button
                            key={key}
                            onClick={() => handleResponse(key)}
                            style={{
                                padding: '10px 14px', borderRadius: 8, textAlign: 'left',
                                border: responses[currentIdx] === key ? '2px solid #f59e0b' : '1px solid var(--border-subtle)',
                                background: responses[currentIdx] === key ? 'rgba(245, 158, 11, 0.06)' : 'var(--bg-secondary)',
                                color: 'var(--text-primary)', cursor: 'pointer',
                                transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                            }}
                        >
                            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{resp.label}</div>
                        </button>
                    ))}
                </div>
            </div>

            {allAnswered && (
                <button className={styles.brNextBtn} onClick={handleSubmit} style={{ width: '100%', marginTop: 10 }}>
                    ✓ Submit All Responses
                </button>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   12. FLAG DEPENDENCY WARNINGS
   Transparency layer: shows players WHY past choices affect now.
   ═══════════════════════════════════════════════════════════════ */

export function FlagDependencyWarnings({ roundNumber, activeFlags = {} }) {
    const [warnings, setWarnings] = useState([]);

    useEffect(() => {
        fetch(`${API}/api/admin/journey/flag-warnings/${roundNumber}`)
            .then(r => r.json())
            .then(d => {
                const active = [];
                for (const [flag, warning] of Object.entries(d.warnings || {})) {
                    if (flag in activeFlags) {
                        active.push(warning);
                    }
                }
                setWarnings(active);
            })
            .catch(() => {});
    }, [roundNumber]);

    if (warnings.length === 0) return null;

    const severityColors = {
        critical: { bg: 'rgba(239, 68, 68, 0.06)', border: 'rgba(239, 68, 68, 0.25)', text: '#fca5a5' },
        warning: { bg: 'rgba(245, 158, 11, 0.06)', border: 'rgba(245, 158, 11, 0.25)', text: '#fde68a' },
        positive: { bg: 'rgba(16, 185, 129, 0.06)', border: 'rgba(16, 185, 129, 0.25)', text: '#6ee7b7' },
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 8 }}>
            {warnings.map((w, i) => {
                const c = severityColors[w.severity] || severityColors.warning;
                return (
                    <div key={i} style={{
                        padding: '10px 14px', borderRadius: 8,
                        background: c.bg, border: `1px solid ${c.border}`,
                        fontSize: '0.82rem', color: c.text, lineHeight: 1.5,
                    }}>
                        <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', marginBottom: 2 }}>
                            From Round {w.from_round} ({w.from_option.replace('option_', 'Option ').toUpperCase()})
                        </div>
                        {w.warning}
                    </div>
                );
            })}
        </div>
    );
}


/* ═══════════════════════════════════════════════════════════════
   13. ORIENTATION PANEL (R1a — Foundation/Advanced Tiers)
   Sweller (1988): Reduce cognitive load by separating context
   building from decision-making.
   ═══════════════════════════════════════════════════════════════ */

export function OrientationPanel({ onComplete, onOpenStakeholderMap, hasCompletedStakeholderMap }) {
    const [config, setConfig] = useState(null);
    const [completedTasks, setCompletedTasks] = useState({});

    useEffect(() => {
        fetch(`${API}/api/admin/journey/r1-split/r1a`)
            .then(r => r.json())
            .then(d => { if (d.split_active) setConfig(d.config); })
            .catch(() => {});
    }, []);

    if (!config) return null;

    const tasks = config.orientation_tasks || [];
    const allDone = tasks.every(t =>
        t.id === 'stakeholder_map' ? hasCompletedStakeholderMap : completedTasks[t.id]
    );

    const toggleTask = (id) => {
        if (id === 'stakeholder_map') {
            onOpenStakeholderMap?.();
            return;
        }
        setCompletedTasks(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const completedCount = tasks.filter(t =>
        t.id === 'stakeholder_map' ? hasCompletedStakeholderMap : completedTasks[t.id]
    ).length;

    return (
        <div className={styles.boardRoom} style={{ borderColor: 'rgba(99, 102, 241, 0.3)' }}>
            <div className={styles.brHeader}>
                <span className={styles.brIcon}>🏢</span>
                <h4>{config.title}</h4>
                <span className={styles.brTheory}>Sweller (1988) Cognitive Load</span>
            </div>
            <p className={styles.pgPrompt}>
                {config.crisis.description}
            </p>

            {/* Progress Bar */}
            <div style={{
                height: 4, borderRadius: 2, background: 'rgba(99, 102, 241, 0.12)',
                marginBottom: 12, overflow: 'hidden',
            }}>
                <div style={{
                    height: '100%', borderRadius: 2,
                    width: `${(completedCount / tasks.length) * 100}%`,
                    background: 'linear-gradient(90deg, #6366f1, #818cf8)',
                    transition: 'width 0.3s ease',
                }} />
            </div>

            {/* Task Checklist */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {tasks.map((task) => {
                    const isDone = task.id === 'stakeholder_map'
                        ? hasCompletedStakeholderMap
                        : completedTasks[task.id];
                    return (
                        <button
                            key={task.id}
                            onClick={() => toggleTask(task.id)}
                            style={{
                                display: 'flex', alignItems: 'flex-start', gap: 12,
                                padding: '12px 14px', borderRadius: 8, textAlign: 'left',
                                border: isDone ? '1px solid rgba(16, 185, 129, 0.35)' : '1px solid var(--border-subtle)',
                                background: isDone ? 'rgba(16, 185, 129, 0.04)' : 'var(--bg-secondary)',
                                color: 'var(--text-primary)', cursor: 'pointer',
                                transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s', width: '100%',
                            }}
                        >
                            <span style={{
                                fontSize: '1.2rem', flexShrink: 0,
                                filter: isDone ? 'none' : 'grayscale(0.7)',
                            }}>
                                {isDone ? '✅' : task.icon}
                            </span>
                            <div>
                                <div style={{
                                    fontWeight: 700, fontSize: '0.88rem',
                                    textDecoration: isDone ? 'line-through' : 'none',
                                    color: isDone ? '#6ee7b7' : 'inherit',
                                }}>
                                    {task.label}
                                </div>
                                <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: 2, lineHeight: 1.4 }}>
                                    {task.instruction}
                                </div>
                            </div>
                        </button>
                    );
                })}
            </div>

            {/* Ready Button */}
            <button
                onClick={() => allDone && onComplete?.()}
                disabled={!allDone}
                style={{
                    width: '100%', marginTop: 12, padding: '12px 16px',
                    borderRadius: 8, border: 'none',
                    background: allDone
                        ? 'linear-gradient(135deg, #6366f1, #818cf8)'
                        : 'rgba(148, 163, 184, 0.1)',
                    color: allDone ? '#fff' : '#64748b',
                    fontWeight: 800, fontSize: '0.82rem', cursor: allDone ? 'pointer' : 'not-allowed',
                    letterSpacing: '0.05em', textTransform: 'uppercase',
                    transition: 'background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s, opacity 0.2s, transform 0.2s',
                }}
            >
                {allDone ? '✓ Ready to Make Your First Decision →' : `Complete ${tasks.length - completedCount} remaining task${tasks.length - completedCount !== 1 ? 's' : ''}`}
            </button>

            <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted)', marginTop: 8, fontStyle: 'italic', textAlign: 'center' }}>
                {config.pedagogical_purpose}
            </div>
        </div>
    );
}
