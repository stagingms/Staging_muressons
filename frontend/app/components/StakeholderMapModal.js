'use client';

import React, { useState, useCallback, useEffect } from 'react';
import {
    DndContext,
    DragOverlay,
    useDraggable,
    useDroppable,
    PointerSensor,
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

    const style = transform
        ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
        : {};

    return (
        <div
            ref={setNodeRef}
            {...listeners}
            {...attributes}
            className={`${styles.chip} ${isDragging ? styles.chipDragging : ''}`}
            style={style}
        >
            <span className={styles.chipIcon}>{stakeholder.icon}</span>
            <span className={styles.chipName}>{stakeholder.name}</span>
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

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
    );

    // Load stakeholder list
    useEffect(() => {
        fetch(`${API}/api/simulations/stakeholder-map/stakeholders`)
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
    }, []);

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

    // Master quadrant mapping for client-side fallback scoring
    const MASTER_MAP = {
        activist_fund: 'manage_closely',
        eu_regulators: 'manage_closely',
        local_communities: 'keep_informed',
        tier3_miners: 'keep_informed',
        factory_employees: 'keep_informed',
        syndicate_banks: 'keep_satisfied',
        national_gov: 'keep_satisfied',
        cafeteria_vendors: 'monitor',
        gen_public: 'monitor',
        local_media: 'monitor',
    };

    const buildClientResult = useCallback((playerPlacements) => {
        let correctCount = 0;
        const details = Object.keys(MASTER_MAP).map(sid => {
            const playerQ = playerPlacements[sid] || '';
            const correctQ = MASTER_MAP[sid];
            const isCorrect = playerQ === correctQ;
            if (isCorrect) correctCount++;
            const s = stakeholders.find(st => st.id === sid);
            return {
                id: sid,
                name: s?.name || sid,
                player_quadrant: playerQ,
                correct_quadrant: correctQ,
                is_correct: isCorrect,
            };
        });
        const total = Object.keys(MASTER_MAP).length;
        const accuracy = total > 0 ? Math.round((correctCount / total) * 1000) / 10 : 0;
        const passed = accuracy >= 80;
        return {
            accuracy_percentage: accuracy,
            correct_count: correctCount,
            total_count: total,
            passed,
            points_awarded: passed ? 1000 : 0,
            details,
            master_mapping: MASTER_MAP,
        };
    }, [stakeholders]);

    const minRequired = Math.ceil(stakeholders.length * 0.5);

    const handleSubmit = useCallback(async () => {
        if (Object.keys(placements).length < minRequired) return;
        setSubmitting(true);
        try {
            const res = await fetch(`${API}/api/simulations/${sessionId}/stakeholder-map`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mapping: placements }),
            });
            const data = await res.json();
            // If the API returned valid data, use it; otherwise fall back to client scoring
            if (data.accuracy_percentage !== undefined && data.details) {
                setResult(data);
            } else {
                console.warn('API returned incomplete data, using client-side scoring');
                setResult(buildClientResult(placements));
            }
        } catch (err) {
            console.error('Stakeholder map submit failed, using client-side scoring:', err);
            setResult(buildClientResult(placements));
        } finally {
            setSubmitting(false);
        }
    }, [placements, sessionId, minRequired, buildClientResult]);

    const handleDismiss = () => {
        onComplete?.(result);
    };

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
                    <div className={styles.badge}>ROUND 1 • STAKEHOLDER ANALYSIS</div>
                    <h1 className={styles.title}>⚖️ Stakeholder Power / Interest Grid</h1>
                    <p className={styles.subtitle}>
                        Map each stakeholder to the correct quadrant based on their Power and Interest
                        in Muressons Global. This assessment determines your strategic alignment bonus.
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
                                margin: '0.5rem 0', padding: '0.5rem',
                                background: result.passed ? 'rgba(16,185,129,0.06)' : 'rgba(239,68,68,0.06)',
                                borderRadius: '10px',
                                border: `1px solid ${result.passed ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`,
                            }}>
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: result.passed ? '#10b981' : '#ef4444' }}>
                                        {result.accuracy_percentage}%
                                    </div>
                                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Accuracy</div>
                                </div>
                                <div style={{ width: '1px', background: 'var(--border-subtle, rgba(255,255,255,0.1))' }} />
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: result.passed ? '#f59e0b' : '#94a3b8' }}>
                                        {result.correct_count}/{result.total_count}
                                    </div>
                                    <div style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Correct</div>
                                </div>
                                <div style={{ width: '1px', background: 'var(--border-subtle, rgba(255,255,255,0.1))' }} />
                                <div style={{ textAlign: 'center', flex: 1 }}>
                                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: result.points_awarded > 0 ? '#6366f1' : '#94a3b8' }}>
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

                            {/* ── Comparison Table ── */}
                            {result.details && (
                                <div style={{ textAlign: 'left', marginTop: '0.4rem' }}>
                                    <table style={{
                                        width: '100%', borderCollapse: 'separate', borderSpacing: '0 2px',
                                        fontSize: '0.72rem',
                                    }}>
                                        <thead>
                                            <tr style={{
                                                fontSize: '0.65rem', textTransform: 'uppercase',
                                                letterSpacing: '0.08em', color: 'var(--text-muted)',
                                            }}>
                                                <th style={{ padding: '4px 6px', textAlign: 'left', width: '24px' }}></th>
                                                <th style={{ padding: '4px 6px', textAlign: 'left' }}>Stakeholder</th>
                                                <th style={{ padding: '4px 6px', textAlign: 'center' }}>Your Placement</th>
                                                <th style={{ padding: '4px 6px', textAlign: 'center' }}>Correct Placement</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {result.details.map((d, idx) => {
                                                const playerQ = QUADRANTS.find(q => q.id === d.player_quadrant);
                                                const correctQ = QUADRANTS.find(q => q.id === d.correct_quadrant);
                                                const s = getStakeholder(d.id);
                                                return (
                                                    <tr key={d.id} style={{
                                                        background: d.is_correct
                                                            ? (idx % 2 === 0 ? 'rgba(16,185,129,0.06)' : 'rgba(16,185,129,0.03)')
                                                            : (idx % 2 === 0 ? 'rgba(239,68,68,0.06)' : 'rgba(239,68,68,0.03)'),
                                                        borderRadius: '6px',
                                                    }}>
                                                        <td style={{ padding: '5px 6px', fontSize: '0.9rem', textAlign: 'center' }}>
                                                            {d.is_correct ? '✅' : '❌'}
                                                        </td>
                                                        <td style={{ padding: '5px 6px', fontWeight: 600 }}>
                                                            <span>{s?.icon || ''} {d.name}</span>
                                                        </td>
                                                        <td style={{ padding: '5px 6px', textAlign: 'center' }}>
                                                            <span style={{
                                                                display: 'inline-block',
                                                                padding: '2px 8px', borderRadius: '4px',
                                                                fontWeight: 600, fontSize: '0.7rem',
                                                                color: d.is_correct ? (playerQ?.color || '#10b981') : '#fff',
                                                                background: d.is_correct
                                                                    ? `${playerQ?.color || '#10b981'}18`
                                                                    : '#ef4444',
                                                            }}>
                                                                {playerQ?.label || '—'}
                                                            </span>
                                                        </td>
                                                        <td style={{ padding: '5px 6px', textAlign: 'center' }}>
                                                            <span style={{
                                                                display: 'inline-block',
                                                                padding: '2px 8px', borderRadius: '4px',
                                                                fontWeight: 600, fontSize: '0.7rem',
                                                                color: correctQ?.color || '#6366f1',
                                                                background: `${correctQ?.color || '#6366f1'}18`,
                                                            }}>
                                                                {correctQ?.label || '—'}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {/* ── Suggested Solution ── */}
                            {result.details && (
                                <div style={{
                                    marginTop: '0.5rem', padding: '0.5rem',
                                    background: 'rgba(99,102,241,0.04)',
                                    border: '1px solid rgba(99,102,241,0.12)',
                                    borderRadius: '8px',
                                }}>
                                    <h3 style={{ margin: '0 0 0.5rem', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                                        📖 Official Stakeholder Ratings
                                    </h3>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                        {QUADRANTS.map(q => {
                                            const qStakeholders = result.details.filter(d => d.correct_quadrant === q.id);
                                            if (qStakeholders.length === 0) return null;
                                            return (
                                                <div key={q.id} style={{
                                                    background: 'var(--bg-elevated, #16213e)',
                                                    borderRadius: '8px',
                                                    padding: '0.5rem 0.6rem',
                                                    borderLeft: `3px solid ${q.color}`,
                                                }}>
                                                    <div style={{
                                                        fontWeight: 700, fontSize: '0.72rem',
                                                        color: q.color, marginBottom: '0.35rem',
                                                    }}>
                                                        {q.label}
                                                        <span style={{
                                                            fontSize: '0.58rem', fontWeight: 500,
                                                            color: 'var(--text-muted)',
                                                            marginLeft: '6px',
                                                        }}>
                                                            {q.power} Power · {q.interest} Interest
                                                        </span>
                                                    </div>
                                                    {qStakeholders.map(d => {
                                                        const s = getStakeholder(d.id);
                                                        return (
                                                            <div key={d.id} style={{
                                                                display: 'flex', gap: '5px', alignItems: 'center',
                                                                padding: '3px 0',
                                                                fontSize: '0.72rem',
                                                                color: d.is_correct ? '#10b981' : '#ef4444',
                                                            }}>
                                                                <span style={{ fontSize: '0.85rem' }}>{s?.icon || '•'}</span>
                                                                <span style={{ fontWeight: 600 }}>{d.name}</span>
                                                                <span style={{ fontSize: '0.7rem' }}>{d.is_correct ? '✓' : '✗'}</span>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* ── Action Button — go to Decision Tab ── */}
                            <button className={styles.dismissBtn} onClick={handleDismiss}
                                style={{ width: '100%', marginTop: '0.6rem', fontSize: '0.9rem', padding: '0.65rem' }}>
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
                            {placedCount >= minRequired && placedCount < stakeholders.length && (
                                <span style={{ marginLeft: 8, fontSize: '0.7rem', color: '#22c55e', fontWeight: 600 }}>✓ Minimum met</span>
                            )}
                        </div>
                        <button
                            className={styles.submitBtn}
                            onClick={handleSubmit}
                            disabled={!allPlaced || submitting}
                        >
                            {submitting ? '⏳ Evaluating...' : allPlaced ? '📋 Submit Map to Board' : `Place at least ${minRequired} stakeholders`}
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
