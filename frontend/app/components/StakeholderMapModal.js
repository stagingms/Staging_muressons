'use client';

import React, { useState, useCallback, useEffect } from 'react';
import {
    DndContext,
    DragOverlay,
    useDraggable,
    useDroppable,
    PointerSensor,
    KeyboardSensor,
    useSensor,
    useSensors,
    closestCenter,
} from '@dnd-kit/core';
import styles from './StakeholderMapModal.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * The 4 quadrants of the Power-Interest Grid (Mendelow's Matrix).
 */
const QUADRANTS = [
    { id: 'keep_satisfied', label: 'Keep Satisfied', row: 0, col: 0, power: 'HIGH', interest: 'LOW', color: '#f59e0b' },
    { id: 'manage_closely', label: 'Manage Closely', row: 0, col: 1, power: 'HIGH', interest: 'HIGH', color: '#ef4444' },
    { id: 'monitor', label: 'Monitor', row: 1, col: 0, power: 'LOW', interest: 'LOW', color: '#64748b' },
    { id: 'keep_informed', label: 'Keep Informed', row: 1, col: 1, power: 'LOW', interest: 'HIGH', color: '#3b82f6' },
];

/**
 * Static fallback stakeholders — used if the API is unreachable.
 */
const FALLBACK_STAKEHOLDERS = [
    { id: 'activist_fund', name: 'FutureFirst Activist Fund', icon: '🦅' },
    { id: 'eu_regulators', name: 'EU Regulators', icon: '🏛️' },
    { id: 'local_communities', name: 'Deccan Plateau Local Communities', icon: '🏘️' },
    { id: 'tier3_miners', name: 'Tier-3 Mine Workers', icon: '⛏️' },
    { id: 'factory_employees', name: 'Factory Floor Employees', icon: '👷' },
    { id: 'syndicate_banks', name: 'Institutional Syndicate Banks', icon: '🏦' },
    { id: 'national_gov', name: 'National Government Tax Authority', icon: '🏛️' },
    { id: 'cafeteria_vendors', name: 'Corporate Cafeteria Vendors', icon: '🍽️' },
    { id: 'gen_public', name: 'General Public', icon: '👥' },
    { id: 'local_media', name: 'Local Media', icon: '📰' },
];


// ═══════════════════════════════════════════════════════════════
//  Sub-Components
// ═══════════════════════════════════════════════════════════════

function DraggableChip({ stakeholder, isDragging }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: stakeholder.id,
        data: stakeholder,
    });
    const [showDossier, setShowDossier] = useState(false);

    const style = transform
        ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
        : {};

    const hasDossier = stakeholder.intel_dossier?.length > 0;

    return (
        <div
            ref={setNodeRef}
            {...listeners}
            {...attributes}
            className={`${styles.chip} ${isDragging ? styles.chipDragging : ''}`}
            style={{ ...style, position: 'relative' }}
            onMouseEnter={() => hasDossier && setShowDossier(true)}
            onMouseLeave={() => setShowDossier(false)}
        >
            <span className={styles.chipIcon}>{stakeholder.icon}</span>
            <span className={styles.chipName}>{stakeholder.name}</span>
            {hasDossier && <span style={{ fontSize: '0.68rem', color: '#60a5fa', marginLeft: 'auto', flexShrink: 0 }}>📋</span>}
            {/* C15: Intel Dossier Tooltip */}
            {showDossier && hasDossier && (
                <div style={{
                    position: 'absolute', bottom: 'calc(100% + 6px)', left: 0,
                    minWidth: '280px', maxWidth: '340px', padding: '8px 10px',
                    background: 'rgba(15,23,42,0.97)', borderRadius: '8px',
                    border: '1px solid rgba(59,130,246,0.25)',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
                    zIndex: 100, pointerEvents: 'none',
                }}>
                    <div style={{ fontSize: '0.6rem', fontWeight: 700, color: '#60a5fa', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '4px' }}>
                        Intelligence Dossier
                    </div>
                    <div style={{ fontSize: '0.65rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '4px' }}>
                        {stakeholder.description}
                    </div>
                    {stakeholder.intel_dossier.map((clip, i) => (
                        <div key={i} style={{ fontSize: '0.6rem', color: '#94a3b8', lineHeight: 1.4, padding: '2px 0', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                            {clip}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function DroppableQuadrant({ quadrant, children, chipCount }) {
    const { isOver, setNodeRef } = useDroppable({ id: quadrant.id });

    return (
        <div
            ref={setNodeRef}
            className={`${styles.quadrant} ${isOver ? styles.quadrantOver : ''}`}
            style={{ '--q-color': quadrant.color }}
        >
            <div className={styles.quadrantLabel}>{quadrant.label}</div>
            <div className={styles.quadrantPower}>{quadrant.power} Power</div>
            <div className={styles.quadrantInterest}>{quadrant.interest} Interest</div>
            <div className={styles.quadrantChips}>{children}</div>
            <span className={styles.chipCountBadge}>{chipCount}</span>
        </div>
    );
}


// ═══════════════════════════════════════════════════════════════
//  Main Component
// ═══════════════════════════════════════════════════════════════

/**
 * StakeholderMapModal — Round 1 interactive minigame.
 *
 * Props:
 *  - sessionId: current session ID
 *  - onComplete: (result) => void — called when the exercise is done
 */
export default function StakeholderMapModal({ sessionId, onComplete }) {
    const [stakeholders, setStakeholders] = useState([]);
    const [bank, setBank] = useState([]);                     // IDs still in the bank
    const [placements, setPlacements] = useState({});          // {stakeholder_id: quadrant_id}
    const [activeDragId, setActiveDragId] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null);                // API response after submit

    // C20: Timer (5 minutes default)
    const TIMER_SECONDS = 300;
    const [timeLeft, setTimeLeft] = useState(TIMER_SECONDS);
    const [timerActive, setTimerActive] = useState(false);

    useEffect(() => {
        if (!timerActive || result) return;
        if (timeLeft <= 0) return;
        const t = setTimeout(() => setTimeLeft(prev => prev - 1), 1000);
        return () => clearTimeout(t);
    }, [timeLeft, timerActive, result]);

    const timerMins = Math.floor(timeLeft / 60);
    const timerSecs = timeLeft % 60;

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
        useSensor(KeyboardSensor)
    );

    // Load stakeholder list (session-aware for vertical BU substitutions)
    useEffect(() => {
        const url = sessionId
            ? `${API}/api/simulations/stakeholder-map/stakeholders?session_id=${sessionId}`
            : `${API}/api/simulations/stakeholder-map/stakeholders`;
        fetch(url)
            .then(r => r.json())
            .then(data => {
                const list = data.stakeholders || FALLBACK_STAKEHOLDERS;
                setStakeholders(list);
                setBank(list.map(s => s.id));
            })
            .catch(() => {
                setStakeholders(FALLBACK_STAKEHOLDERS);
                setBank(FALLBACK_STAKEHOLDERS.map(s => s.id));
            });
    }, [sessionId]);

    const getStakeholder = (id) => stakeholders.find(s => s.id === id);

    const handleDragStart = useCallback((event) => {
        setActiveDragId(event.active.id);
    }, []);

    const handleDragEnd = useCallback((event) => {
        const { active, over } = event;
        setActiveDragId(null);

        if (!over) return;

        const stakeholderId = active.id;
        const targetQuadrant = over.id;

        // Check if dropping into a valid quadrant
        const isValidQuadrant = QUADRANTS.some(q => q.id === targetQuadrant);
        if (!isValidQuadrant) {
            // Dropping back to bank
            if (targetQuadrant === 'bank') {
                setPlacements(prev => {
                    const next = { ...prev };
                    delete next[stakeholderId];
                    return next;
                });
                setBank(prev => prev.includes(stakeholderId) ? prev : [...prev, stakeholderId]);
            }
            return;
        }

        // Place stakeholder into quadrant
        setPlacements(prev => ({ ...prev, [stakeholderId]: targetQuadrant }));
        setBank(prev => prev.filter(id => id !== stakeholderId));
    }, []);

    const removeFromQuadrant = (stakeholderId) => {
        setPlacements(prev => {
            const next = { ...prev };
            delete next[stakeholderId];
            return next;
        });
        setBank(prev => [...prev, stakeholderId]);
    };

    // Minimum 6 stakeholders must be placed before submission is allowed.
    // Players may still place more for a higher accuracy score, but 6 unlocks the submit button.
    const MIN_REQUIRED = 6;
    const minRequired = MIN_REQUIRED;

    const handleSubmit = useCallback(async () => {
        if (Object.keys(placements).length < minRequired) return;
        setSubmitting(true);
        setAttemptCount(prev => prev + 1);
        try {
            const res = await fetch(`${API}/api/simulations/${sessionId}/stakeholder-map`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mapping: placements }),
            });
            const data = await res.json();
            if (data.accuracy_percentage !== undefined && data.details) {
                setResult(data);
            } else {
                console.error('API returned incomplete data');
                setResult({ error: true, message: 'Server returned incomplete data. Please retry.' });
            }
        } catch (err) {
            console.error('Stakeholder map submit failed:', err);
            setResult({ error: true, message: 'Connection error. Please check your network and retry.' });
        } finally {
            setSubmitting(false);
        }
    }, [placements, sessionId, minRequired]);

    // C9: Re-attempt logic — 1 retry allowed
    const [attemptCount, setAttemptCount] = useState(0);
    const MAX_ATTEMPTS = 2;

    const handleRetry = () => {
        // Highlight incorrect placements by removing them back to bank
        if (result?.details) {
            const incorrectIds = result.details.filter(d => !d.is_correct).map(d => d.id);
            setPlacements(prev => {
                const next = { ...prev };
                incorrectIds.forEach(id => delete next[id]);
                return next;
            });
            setBank(prev => [...prev, ...incorrectIds]);
        }
        setResult(null);
    };

    const handleDismiss = () => {
        onComplete?.(result);
    };

    // C19: Executive rationale (stored for facilitator review)
    const [rationale, setRationale] = useState('');

    const placedCount = Object.keys(placements).length;
    const allPlaced = placedCount >= minRequired;
    const activeStakeholder = activeDragId ? getStakeholder(activeDragId) : null;

    // Get stakeholders placed in each quadrant
    const getQuadrantStakeholders = (quadrantId) =>
        Object.entries(placements)
            .filter(([, qId]) => qId === quadrantId)
            .map(([sId]) => getStakeholder(sId))
            .filter(Boolean);

    return (
        <div className={styles.overlay}>
            <div className={styles.modal}>
                {/* ── Header ── */}
                <header className={styles.header}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div className={styles.badge}>ROUND 1 • STAKEHOLDER ANALYSIS</div>
                        {/* C20: Timer */}
                        {!result && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                {timerActive ? (
                                    <span style={{
                                        fontFamily: 'JetBrains Mono, monospace', fontSize: '0.85rem',
                                        fontWeight: 800, padding: '3px 10px', borderRadius: '6px',
                                        color: timeLeft < 60 ? '#ef4444' : timeLeft < 120 ? '#f59e0b' : '#10b981',
                                        background: 'transparent',
                                        border: `1px solid ${timeLeft < 60 ? 'rgba(239,68,68,0.3)' : 'rgba(16,185,129,0.2)'}`,
                                    }}>
                                        ⏱ {timerMins}:{String(timerSecs).padStart(2, '0')}
                                    </span>
                                ) : (
                                    <button onClick={() => setTimerActive(true)} style={{
                                        fontSize: '0.65rem', padding: '3px 10px', borderRadius: '6px',
                                        background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)',
                                        color: '#818cf8', fontWeight: 700, cursor: 'pointer',
                                    }}>
                                        ⏱ Start 5-min Timer
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                    <h1 className={styles.title}>⚖️ Stakeholder Power / Interest Grid</h1>
                    <p className={styles.subtitle}>
                        Hover over each stakeholder to read their 📋 Intelligence Dossier before classifying.
                        Map each stakeholder based on their Power and Interest in Muressons Global.
                    </p>
                </header>

                {/* ── Result Modal Overlay ── */}
                {result && (
                    <div className={styles.resultOverlay}>
                        <div className={`${styles.resultCard} ${result.passed ? styles.resultPass : styles.resultFail}`}>
                            <div className={styles.resultIcon}>{result.passed ? '🎯' : '⚠️'}</div>
                            <h2>{result.passed ? 'Stakeholder Alignment Achieved!' : 'Misaligned Priorities'}</h2>

                            {/* Score Summary Cards */}
                            <div style={{
                                display: 'flex', justifyContent: 'center', gap: '1rem',
                                margin: '0.3rem 0', padding: '0.4rem',
                                background: 'transparent',
                                borderRadius: '10px',
                                border: `1px solid ${result.passed ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                            }}>
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: result.passed ? '#10b981' : '#ef4444' }}>
                                        {result.accuracy_percentage}%
                                    </div>
                                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Accuracy</div>
                                </div>
                                <div style={{ width: '1px', background: 'var(--border-subtle, rgba(255,255,255,0.1))' }} />
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: result.passed ? '#f59e0b' : '#94a3b8' }}>
                                        {result.correct_count}/{result.total_count}
                                    </div>
                                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Correct</div>
                                </div>
                                <div style={{ width: '1px', background: 'var(--border-subtle, rgba(255,255,255,0.1))' }} />
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: result.points_awarded > 0 ? '#6366f1' : '#94a3b8' }}>
                                        +{result.points_awarded}
                                    </div>
                                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Bonus Pts</div>
                                </div>
                            </div>

                            {result.passed ? (
                                <p className={styles.resultMessage}>
                                    Excellent strategic analysis! Your mapping matches the executive master set.
                                </p>
                            ) : (
                                <p className={styles.resultMessage}>
                                    Your stakeholder analysis needs refinement. Review the corrections below.
                                </p>
                            )}

                            {/* ── Two-Column Layout ── */}
                            <div className={styles.resultTwoCol}>
                              {/* LEFT COLUMN: Comparison + Ambiguous + Penalties */}
                              <div className={styles.resultColLeft}>
                                {result.details && (
                                  <div style={{ textAlign: 'left' }}>
                                    <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 1px', fontSize: '0.7rem' }}>
                                        <thead>
                                            <tr style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)' }}>
                                                <th style={{ padding: '3px 4px', textAlign: 'left', width: '20px' }}></th>
                                                <th style={{ padding: '3px 4px', textAlign: 'left' }}>Stakeholder</th>
                                                <th style={{ padding: '3px 4px', textAlign: 'center' }}>Your Placement</th>
                                                <th style={{ padding: '3px 4px', textAlign: 'center' }}>Correct Placement</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.details.map((d, idx) => {
                                                const playerQ = QUADRANTS.find(q => q.id === d.player_quadrant);
                                                const correctQ = QUADRANTS.find(q => q.id === d.correct_quadrant);
                                                const s = getStakeholder(d.id);
                                                return (
                                                    <tr key={d.id} style={{ background: idx % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent' }}>
                                                        <td style={{ padding: '3px 4px', fontSize: '0.8rem', textAlign: 'center' }}>{d.is_correct ? '✅' : '❌'}</td>
                                                        <td style={{ padding: '3px 4px', fontWeight: 600 }}><span>{s?.icon || ''} {d.name}</span></td>
                                                        <td style={{ padding: '3px 4px', textAlign: 'center' }}>
                                                            <span style={{ fontWeight: 600, fontSize: '0.65rem', color: d.is_correct ? (playerQ?.color || '#10b981') : '#ef4444' }}>{playerQ?.label || '—'}</span>
                                                        </td>
                                                        <td style={{ padding: '3px 4px', textAlign: 'center' }}>
                                                            <span style={{ fontWeight: 600, fontSize: '0.65rem', color: correctQ?.color || '#6366f1' }}>{correctQ?.label || '—'}</span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                  </div>
                                )}

                                {/* Ambiguous Stakeholder Callout */}
                                {result.details?.filter(d => d.alternate_quadrant).map(d => (
                                    <div key={`amb-${d.id}`} style={{ padding: '0.4rem 0.5rem', background: 'transparent', borderRadius: '8px', border: '1px solid rgba(245,158,11,0.2)', borderLeft: '3px solid #f59e0b' }}>
                                        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#fbbf24', marginBottom: '0.2rem' }}>⚖️ Ambiguous Classification — {d.name}</div>
                                        <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary, #94a3b8)', lineHeight: 1.4 }}>{d.alternate_rationale}</div>
                                    </div>
                                ))}

                                {/* Scoring Tier & Penalty Banner */}
                                {(result.scoring_tier || result.treasury_penalty || result.reputation_penalty) && (
                                    <div style={{ padding: '0.4rem 0.5rem', background: 'transparent', borderRadius: '8px', border: `1px solid ${result.passed ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}`, display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
                                        {result.scoring_tier && (<span style={{ fontSize: '0.65rem', fontWeight: 700, color: result.passed ? '#10b981' : '#f59e0b' }}>📊 {result.scoring_tier}</span>)}
                                        {result.reputation_penalty < 0 && (<span style={{ fontSize: '0.63rem', fontWeight: 600, color: '#ef4444' }}>🌍 Reputation {result.reputation_penalty}</span>)}
                                        {result.treasury_penalty < 0 && (<span style={{ fontSize: '0.63rem', fontWeight: 600, color: '#ef4444' }}>💰 Treasury ${Math.abs(result.treasury_penalty / 1000)}K penalty</span>)}
                                    </div>
                                )}
                              </div>

                              {/* RIGHT COLUMN: Salience + Ratings + Tactics */}
                              <div className={styles.resultColRight}>
                                {/* Urgency & Legitimacy Debrief */}
                                {result.urgency_debrief?.length > 0 && (
                                    <div style={{ padding: '0.4rem', background: 'transparent', border: '1px solid rgba(139,92,246,0.12)', borderRadius: '8px' }}>
                                        <h3 style={{ margin: '0 0 0.3rem', fontSize: '0.72rem', color: '#a78bfa' }}>
                                            🔬 Stakeholder Salience Debrief <span style={{ fontSize: '0.55rem', fontWeight: 400, color: 'var(--text-muted)' }}>(Mitchell, Agle & Wood 1997)</span>
                                        </h3>
                                        <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '0.25rem', lineHeight: 1.3 }}>
                                            Beyond Power × Interest, real-world stakeholder analysis considers <strong>Urgency</strong> (time-sensitivity of claims) and <strong>Legitimacy</strong> (moral/legal standing).
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px' }}>
                                            {result.urgency_debrief.map(u => (
                                                <div key={u.id} style={{ padding: '3px 6px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                                                    <span style={{ fontSize: '0.6rem', fontWeight: 600, color: 'var(--text-primary)', flex: 1 }}>{u.name}</span>
                                                    <span style={{ fontSize: '0.62rem', fontWeight: 700, color: u.urgency === 'high' ? '#f87171' : u.urgency === 'medium' ? '#fbbf24' : '#94a3b8' }}>⏱ {u.urgency}</span>
                                                    <span style={{ fontSize: '0.62rem', fontWeight: 700, color: u.legitimacy === 'high' ? '#4ade80' : u.legitimacy === 'medium' ? '#fbbf24' : '#94a3b8' }}>⚖ {u.legitimacy}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Official Stakeholder Ratings */}
                                {result.details && (
                                    <div style={{ padding: '0.4rem', background: 'transparent', border: '1px solid rgba(99,102,241,0.12)', borderRadius: '8px' }}>
                                        <h3 style={{ margin: '0 0 0.35rem', fontSize: '0.78rem', color: 'var(--text-primary)' }}>📖 Official Stakeholder Ratings</h3>
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                                            {QUADRANTS.map(q => {
                                                const qStakeholders = result.details.filter(d => d.correct_quadrant === q.id);
                                                if (qStakeholders.length === 0) return null;
                                                return (
                                                    <div key={q.id} style={{ background: 'var(--bg-elevated, #16213e)', borderRadius: '8px', padding: '0.35rem 0.5rem', borderLeft: `3px solid ${q.color}` }}>
                                                        <div style={{ fontWeight: 700, fontSize: '0.65rem', color: q.color, marginBottom: '0.2rem' }}>
                                                            {q.label} <span style={{ fontSize: '0.6rem', fontWeight: 500, color: 'var(--text-muted)', marginLeft: '4px' }}>{q.power} Power · {q.interest} Interest</span>
                                                        </div>
                                                        {qStakeholders.map(d => { const s = getStakeholder(d.id); return (
                                                            <div key={d.id} style={{ display: 'flex', gap: '4px', alignItems: 'center', padding: '2px 0', fontSize: '0.65rem', color: d.is_correct ? '#10b981' : '#ef4444' }}>
                                                                <span style={{ fontSize: '0.75rem' }}>{s?.icon || '•'}</span>
                                                                <span style={{ fontWeight: 600 }}>{d.name}</span>
                                                                <span style={{ fontSize: '0.62rem' }}>{d.is_correct ? '✓' : '✗'}</span>
                                                            </div>
                                                        ); })}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}

                                {/* Engagement Tactics */}
                                {result.engagement_tactics?.length > 0 && (
                                    <div style={{ padding: '0.4rem', background: 'transparent', border: '1px solid rgba(59,130,246,0.12)', borderRadius: '8px' }}>
                                        <h3 style={{ margin: '0 0 0.3rem', fontSize: '0.72rem', color: '#60a5fa' }}>🎯 Engagement Strategy — "Manage Closely"</h3>
                                        <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)', marginBottom: '0.3rem' }}>For high-power, high-interest stakeholders, what engagement tactic would you deploy?</div>
                                        {result.engagement_tactics.map(et => (
                                            <div key={et.stakeholder_id} style={{ marginBottom: '0.4rem' }}>
                                                <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.2rem' }}>{et.stakeholder_name}</div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                                    {et.tactics.map(t => (
                                                        <div key={t.id} style={{ padding: '3px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                                                            <div style={{ fontSize: '0.62rem', fontWeight: 600, color: t.correct ? '#10b981' : 'var(--text-secondary)' }}>{t.correct ? '✅' : '❌'} {t.label}</div>
                                                            <div style={{ fontSize: '0.55rem', color: 'var(--text-muted)', marginTop: '1px', fontStyle: 'italic' }}>{t.rationale}</div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                              </div>
                            </div>

                            {/* ── C19: Executive Rationale Prompt ── */}
                            <div style={{
                                marginTop: '0.3rem', padding: '0.4rem',
                                background: 'transparent',
                                border: '1px solid rgba(245,158,11,0.12)',
                                borderRadius: '8px',
                            }}>
                                <label style={{ fontSize: '0.65rem', fontWeight: 700, color: '#fbbf24', display: 'block', marginBottom: '0.2rem' }}>
                                    ✍️ Executive Rationale — Justify your most controversial placement:
                                </label>
                                <textarea
                                    value={rationale}
                                    onChange={e => setRationale(e.target.value)}
                                    placeholder="e.g., I placed the journalist in 'Keep Informed' because their track record of syndication means a negative story would rapidly amplify..."
                                    style={{
                                        width: '100%', minHeight: '40px', padding: '5px 7px', borderRadius: '6px',
                                        background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.06)',
                                        color: 'var(--text-primary, #e2e8f0)', fontSize: '0.68rem', fontFamily: 'inherit',
                                        resize: 'vertical', outline: 'none', lineHeight: 1.4,
                                    }}
                                />
                            </div>

                            {/* ── C9: Retry Button (1 re-attempt) ── */}
                            {!result.passed && attemptCount < MAX_ATTEMPTS && (
                                <button onClick={handleRetry} style={{
                                    width: '100%', marginTop: '0.3rem', padding: '0.45rem',
                                    fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer',
                                    background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.25)',
                                    borderRadius: '6px', color: '#818cf8',
                                }}>
                                    🔄 Re-attempt — Incorrect placements returned to bank ({MAX_ATTEMPTS - attemptCount} retry remaining)
                                </button>
                            )}

                            {/* ── Action Button — go to Decision Tab ── */}
                            <button className={styles.dismissBtn} onClick={handleDismiss}
                                style={{ width: '100%', marginTop: '0.3rem', fontSize: '0.85rem', padding: '0.55rem' }}>
                                📋 Open Decision Tab →
                            </button>
                        </div>
                    </div>
                )}

                {/* ── Drag & Drop Area ── */}
                {!result && (
                    <DndContext
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragStart={handleDragStart}
                        onDragEnd={handleDragEnd}
                    >
                        <div className={styles.content}>
                            {/* Left Pane: Stakeholder Bank */}
                            <StakeholderBank bank={bank} stakeholders={stakeholders} getStakeholder={getStakeholder} />

                            {/* Right Pane: Grid Matrix */}
                            <div className={styles.gridPane}>
                                {/* Axis Labels */}
                                <div className={styles.yAxisLabel}>
                                    <span>← LOW</span>
                                    <strong>POWER</strong>
                                    <span>HIGH →</span>
                                </div>
                                <div className={styles.matrixWrapper}>
                                    <div className={styles.matrix}>
                                        {QUADRANTS.map(q => (
                                            <DroppableQuadrant
                                                key={q.id}
                                                quadrant={q}
                                                chipCount={getQuadrantStakeholders(q.id).length}
                                            >
                                                {getQuadrantStakeholders(q.id).map(s => (
                                                    <DraggableChip key={s.id} stakeholder={s} />
                                                ))}
                                            </DroppableQuadrant>
                                        ))}
                                    </div>
                                    <div className={styles.xAxisLabel}>
                                        <span>← LOW</span>
                                        <strong>INTEREST</strong>
                                        <span>HIGH →</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <DragOverlay>
                            {activeStakeholder && (
                                <div className={styles.dragOverlay}>
                                    <span>{activeStakeholder.icon}</span>
                                    <span>{activeStakeholder.name}</span>
                                </div>
                            )}
                        </DragOverlay>
                    </DndContext>
                )}

                {/* ── Submit Button ── */}
                {!result && (
                    <div className={styles.footer}>
                        <div className={styles.progress}>
                            {placedCount} / {stakeholders.length} stakeholders placed
                            {placedCount < minRequired && (
                                <span style={{ marginLeft: 8, fontSize: '0.7rem', color: '#f59e0b', fontWeight: 600 }}>
                                    — {minRequired - placedCount} more required
                                </span>
                            )}
                            {placedCount >= minRequired && placedCount < stakeholders.length && (
                                <span style={{ marginLeft: 8, fontSize: '0.7rem', color: '#22c55e', fontWeight: 600 }}>✓ Minimum met — place more for higher accuracy</span>
                            )}
                            {placedCount >= stakeholders.length && (
                                <span style={{ marginLeft: 8, fontSize: '0.7rem', color: '#22c55e', fontWeight: 600 }}>✓ All stakeholders placed</span>
                            )}
                        </div>
                        <button
                            className={styles.submitBtn}
                            onClick={handleSubmit}
                            disabled={!allPlaced || submitting}
                        >
                            {submitting ? '⏳ Evaluating…' : allPlaced ? '📋 Submit Map to Board' : `Place at least ${minRequired} stakeholders to submit`}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

/**
 * Stakeholder Bank — Droppable area for unplaced stakeholders.
 */
function StakeholderBank({ bank, stakeholders, getStakeholder }) {
    const { setNodeRef, isOver } = useDroppable({ id: 'bank' });

    return (
        <div ref={setNodeRef} className={`${styles.bankPane} ${isOver ? styles.bankOver : ''}`}>
            <h3 className={styles.bankTitle}>📋 Stakeholder Bank</h3>
            <p className={styles.bankHint}>Drag each stakeholder to the correct quadrant</p>
            <div className={styles.bankList}>
                {bank.map(id => {
                    const s = getStakeholder(id);
                    if (!s) return null;
                    return <DraggableChip key={s.id} stakeholder={s} />;
                })}
                {bank.length === 0 && (
                    <div className={styles.bankEmpty}>All stakeholders placed! ✨</div>
                )}
            </div>
        </div>
    );
}
