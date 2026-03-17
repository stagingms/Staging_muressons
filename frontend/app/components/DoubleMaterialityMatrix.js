'use client';

import React, { useState, useEffect } from 'react';
import {
    DndContext,
    useDraggable,
    useDroppable,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragOverlay
} from '@dnd-kit/core';
import styles from './DoubleMaterialityMatrix.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * Draggable Issue Chip component
 */
function IssueChip({ issue, isDragging }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: issue.id,
        data: issue,
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 9999, // Bring to front while dragging
        opacity: isDragging ? 0.4 : 1, // Optional visual cue on the original spot
    } : undefined;

    const getCategoryIcon = (category) => {
        switch (category) {
            case 'ecological': return <span className={styles.catIcon} style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.5)' }}>E</span>;
            case 'social': return <span className={styles.catIcon} style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.5)' }}>S</span>;
            case 'economic': return <span className={styles.catIcon} style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.5)' }}>G</span>;
            default: return null;
        }
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            className={`${styles.chip} ${isDragging ? styles.chipDragging : ''}`}
        >
            <div className={styles.chipLeft}>
                {getCategoryIcon(issue.category)}
            </div>
            <span className={styles.chipTitle}>{issue.title}</span>
            <div className={styles.tooltip}>
                <span className={styles.infoIcon}>ⓘ</span>
                <span className={styles.tooltipText}>{issue.hover_description}</span>
            </div>
        </div>
    );
}

/**
 * Overlay Chip for smooth drag animations without layout shifting
 */
function OverlayChip({ issue }) {
    if (!issue) return null;
    return (
        <div className={`${styles.chip} ${styles.chipDragging}`}>
            <span className={styles.chipTitle}>{issue.title}</span>
            <span className={styles.infoIcon}>ⓘ</span>
        </div>
    );
}

/**
 * Droppable Container component (for Bank or Quadrants)
 */
function DroppableContainer({ id, className, children, label, extraText }) {
    const { isOver, setNodeRef } = useDroppable({ id });

    return (
        <div
            ref={setNodeRef}
            className={`${className} ${isOver ? styles.isOver : ''}`}
        >
            {label && id !== 'bank' && <div className={styles.quadrantHeader}>{label}</div>}
            {label && id === 'bank' && <div style={{ fontWeight: 'bold', color: '#0f172a', marginBottom: '8px' }}>{label}</div>}
            {extraText && <div className={styles.bgText}>{extraText}</div>}
            {children}
        </div>
    );
}

/**
 * Custom SVG Cartesian plane for precise 3-zone visual layout
 */
const CartesianBackground = () => {
    const ticks = [];
    for (let i = 0; i <= 140; i += 10) {
        ticks.push(i);
    }

    return (
        <svg
            viewBox="0 0 140 140"
            preserveAspectRatio="none"
            style={{
                position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
                zIndex: 0, pointerEvents: 'none', borderRadius: '0.375rem'
            }}
        >
            {/* Base Layer - Medium Risk (Yellow) */}
            <rect width="140" height="140" fill="#fdf0d5" />

            {/* Low Risk Zone (Green) */}
            <path d="M 0,140 L 60,140 L 60,95 Q 60,80 45,80 L 0,80 Z" fill="#daebe4" />

            {/* High Risk Zone (Red) */}
            <path d="M 0,0 L 140,0 L 140,140 L 100,140 L 100,55 Q 100,40 85,40 L 0,40 Z" fill="#fcdada" />

            {/* Grid lines */}
            {ticks.map((pos) => {
                const val = pos - 70;
                return (
                    <g key={pos}>
                        <line x1="0" y1={pos} x2="140" y2={pos} stroke="rgba(255,255,255,0.7)" strokeWidth="0.3" />
                        <line x1={pos} y1="0" x2={pos} y2="140" stroke="rgba(255,255,255,0.7)" strokeWidth="0.3" />
                        {/* X-axis labels */}
                        {pos !== 70 && pos % 20 === 0 && (
                            <text x={pos} y="137" fontSize="2.8" fontWeight="600" fill="rgba(0,0,0,0.6)" textAnchor="middle">{val}</text>
                        )}
                        {/* Y-axis labels */}
                        {pos !== 70 && pos % 20 === 0 && (
                            <text x="3" y={pos + 1} fontSize="2.8" fontWeight="600" fill="rgba(0,0,0,0.6)" textAnchor="start">{-val}</text>
                        )}
                    </g>
                );
            })}

            {/* Major Axes */}
            <line x1="0" y1="70" x2="140" y2="70" stroke="rgba(0,0,0,0.4)" strokeWidth="0.6" />
            <line x1="70" y1="0" x2="70" y2="140" stroke="rgba(0,0,0,0.4)" strokeWidth="0.6" />
        </svg>
    );
};

/**
 * Main Double Materiality Matrix Component
 */
export default function DoubleMaterialityMatrix({ onSubmit, onClose, csfPool = Infinity, initialQ1 = [], globalState = {}, buId = null, buLabel = null }) {
    const [issues, setIssues] = useState([]);
    const [consultantFee, setConsultantFee] = useState(1500000);
    const [loading, setLoading] = useState(true);

    const [activeId, setActiveId] = useState(null);
    const [consultantUsed, setConsultantUsed] = useState(false);

    // Modal states
    const [showConsultantConfirm, setShowConsultantConfirm] = useState(false);
    const [showCheatSheet, setShowCheatSheet] = useState(false);
    const [submitStatus, setSubmitStatus] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Initial state: empty until fetched
    const [containers, setContainers] = useState({
        bank: [],
        q1: [], // Top Right: High Fin / High Impact
        q2: [], // Top Left: Low Fin / High Impact
        q3: [], // Bottom Right: High Fin / Low Impact
        q4: []  // Bottom Left: Low Fin / Low Impact
    });

    useEffect(() => {
        const fetchConfig = async () => {
            try {
                // If buId is provided, fetch BU-specific dictionary
                const endpoint = buId
                    ? `${API}/api/admin/materiality-config/bu/${buId}`
                    : `${API}/api/admin/materiality-config`;
                const res = await fetch(endpoint);
                if (res.ok) {
                    const data = await res.json();
                    setIssues(data.issues || []);
                    setConsultantFee(data.consultant_fee_usd || 1500000);
                    setContainers(prev => {
                        const allIds = (data.issues || []).map(i => i.id);
                        const q1Ids = initialQ1.filter(id => allIds.includes(id));
                        const bankIds = allIds.filter(id => !q1Ids.includes(id));
                        return {
                            bank: bankIds,
                            q1: q1Ids, q2: [], q3: [], q4: []
                        };
                    });
                }
            } catch (err) {
                console.error("Failed to load materiality config", err);
            }
            setLoading(false);
        };
        fetchConfig();
    }, [buId]);

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
        useSensor(KeyboardSensor)
    );

    const handleDragStart = (event) => {
        setActiveId(event.active.id);
    };

    const handleDragEnd = (event) => {
        const { active, over } = event;
        setActiveId(null);

        if (!over) return;

        const activeId = active.id;
        const overId = over.id;

        // Find which container the dragged item is currently in
        let sourceContainer = null;
        for (const [key, items] of Object.entries(containers)) {
            if (items.includes(activeId)) {
                sourceContainer = key;
                break;
            }
        }

        if (sourceContainer && sourceContainer !== overId) {
            setContainers(prev => {
                const newSource = prev[sourceContainer].filter(id => id !== activeId);
                const newTarget = [...prev[overId], activeId];
                return {
                    ...prev,
                    [sourceContainer]: newSource,
                    [overId]: newTarget
                };
            });
        }
    };

    // Helper to get issue object by ID
    const getIssue = (id) => issues.find(i => i.id === id);

    // Helper to compute correct quadrant from dynamic dimensions
    const getCorrectQuadrant = (issue) => {
        const hFin = issue.financial_impact === 'high';
        const hImp = issue.societal_impact === 'high';
        if (hFin && hImp) return 1;
        if (!hFin && hImp) return 2;
        if (hFin && !hImp) return 3;
        return 4;
    };

    const handleHireConsultant = () => {
        setConsultantUsed(true);
        setShowConsultantConfirm(false);
        setShowCheatSheet(true);

        // Auto-solve 5 issues
        setContainers(prev => {
            const newContainers = { ...prev };
            // Copy bank to mutate
            let currentBank = [...newContainers.bank];
            let solvedCount = 0;

            // We need to move exactly 5 issues to their correct quadrant
            // We iterate backward or filter the bank. Let's pick the first 5 standard issues.
            for (let i = currentBank.length - 1; i >= 0 && solvedCount < 5; i--) {
                const issueId = currentBank[i];
                const issue = getIssue(issueId);
                if (issue) {
                    const targetQuad = `q${getCorrectQuadrant(issue)}`; // q1, q2, q3, q4
                    newContainers[targetQuad] = [...newContainers[targetQuad], issueId];
                    currentBank.splice(i, 1);
                    solvedCount++;
                }
            }
            newContainers.bank = currentBank;
            return newContainers;
        });
    };

    const handleSubmit = async (forceOverride = false) => {
        if (!onSubmit) return;
        setIsSubmitting(true);
        const result = await onSubmit({
            consultant_used: consultantUsed,
            matrix_submission: {
                quadrant_1_top_right: containers.q1,
                quadrant_2_top_left: containers.q2,
                quadrant_3_bottom_right: containers.q3,
                quadrant_4_bottom_left: containers.q4,
            },
            force_override_cfo: forceOverride === true,
            bu_id: buId || undefined,
        });

        if (result && result.error) {
            setSubmitStatus({ type: 'error', message: result.error });
            setIsSubmitting(false);
        } else if (result && result.success) {
            setSubmitStatus({ type: 'success', amount: result.allocated_budget });
            setIsSubmitting(false);
        }
    };

    const allPlaced = containers.bank.length === 0;

    const totalQ1Cost = containers.q1.reduce((sum, id) => {
        const issue = getIssue(id);
        const finalCost = issue ? issue.mitigation_cost_usd : 0;
        return sum + finalCost;
    }, 0);
    const isOverBudget = totalQ1Cost > csfPool;

    if (loading) return <div className={styles.overlay}><div className={styles.header}><h2 style={{ color: 'white' }}>Loading Materiality Dictionary...</h2></div></div>;

    return (
        <div className={styles.overlay}>
            <div className={styles.header}>
                <h2 className={styles.headerTitle}>
                    <span>📊</span> {buLabel ? `${buLabel} — ` : ''}CSRD Double Materiality Matrix
                </h2>
                <div className={styles.headerActions}>
                    {!consultantUsed && (
                        <button
                            className={styles.consultantBtn}
                            onClick={() => setShowConsultantConfirm(true)}
                        >
                            💼 Hire External ESG Consultant (McBain & Partners)
                        </button>
                    )}
                    {consultantUsed && (
                        <span className={styles.consultantBadge}>🔍 Consultant Retained</span>
                    )}
                    <div style={{ padding: '0 1rem', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center' }}>
                        <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700 }}>Q1 Budget Limit</span>
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: isOverBudget ? '#ef4444' : '#4ade80' }}>
                            ${(totalQ1Cost / 1_000_000).toFixed(1)}M / ${(csfPool / 1_000_000).toFixed(1)}M
                        </span>
                    </div>
                    <button
                        className={styles.submitBtn}
                        disabled={isSubmitting || isOverBudget}
                        onClick={() => handleSubmit(false)}
                        title={isOverBudget ? "Your Quadrant 1 CapEx exceeds the total CSF pool balance." : ""}
                    >
                        {isSubmitting ? 'Submitting...' : 'Submit Matrix to CFO'}
                    </button>
                    {onClose && (
                        <button className={styles.submitBtn} onClick={onClose} style={{ background: 'rgba(255,255,255,0.12)', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.2)', boxShadow: 'none' }}>
                            Close
                        </button>
                    )}
                </div>
            </div>

            <main className={styles.mainContent}>
                <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragStart={handleDragStart}
                    onDragEnd={handleDragEnd}
                >
                    {/* Left Pane: Issue Bank */}
                    <div className={styles.leftPane}>
                        <div className={styles.bankHeader}>The Issue Bank ({containers.bank.length} remaining)</div>
                        <DroppableContainer id="bank" className={styles.bankScroll}>
                            {containers.bank.map(id => {
                                const issue = getIssue(id);
                                if (!issue) return null;
                                const cost = globalState?.materiality_dictionary_override?.issues?.find(i => i.id === id)?.mitigation_cost_usd ?? issue.mitigation_cost_usd;
                                return <IssueChip key={id} issue={{ ...issue, mitigation_cost_usd: cost }} isDragging={activeId === id} />;
                            })}
                        </DroppableContainer>
                    </div>

                    {/* Right Pane: The Grid */}
                    <div className={styles.rightPane}>
                        <div className={styles.axesContainer}>
                            <div className={styles.yAxisLabel}>Impact Materiality (People/Planet)</div>

                            <div className={styles.matrixGrid}>
                                <CartesianBackground />

                                {/* Top Left: Low Fin / High Impact */}
                                <DroppableContainer id="q2" className={styles.quadrant}>
                                    {containers.q2.map(id => {
                                        const issue = getIssue(id);
                                        if (!issue) return null;
                                        const cost = globalState?.materiality_dictionary_override?.issues?.find(i => i.id === id)?.mitigation_cost_usd ?? issue.mitigation_cost_usd;
                                        return <IssueChip key={id} issue={{ ...issue, mitigation_cost_usd: cost }} isDragging={activeId === id} />;
                                    })}
                                </DroppableContainer>

                                {/* Top Right: High Fin / High Impact (THE TARGET) */}
                                <DroppableContainer
                                    id="q1"
                                    className={`${styles.quadrant} ${styles.quadrant1}`}
                                    label="Quadrant 1"
                                    extraText="CFO Approved Capital Allocation Zone"
                                >
                                    {containers.q1.map(id => {
                                        const issue = getIssue(id);
                                        if (!issue) return null;
                                        const cost = globalState?.materiality_dictionary_override?.issues?.find(i => i.id === id)?.mitigation_cost_usd ?? issue.mitigation_cost_usd;
                                        return <IssueChip key={id} issue={{ ...issue, mitigation_cost_usd: cost }} isDragging={activeId === id} />;
                                    })}
                                </DroppableContainer>

                                {/* Bottom Left: Low Fin / Low Impact */}
                                <DroppableContainer id="q4" className={styles.quadrant}>
                                    {containers.q4.map(id => {
                                        const issue = getIssue(id);
                                        if (!issue) return null;
                                        const cost = globalState?.materiality_dictionary_override?.issues?.find(i => i.id === id)?.mitigation_cost_usd ?? issue.mitigation_cost_usd;
                                        return <IssueChip key={id} issue={{ ...issue, mitigation_cost_usd: cost }} isDragging={activeId === id} />;
                                    })}
                                </DroppableContainer>

                                {/* Bottom Right: High Fin / Low Impact */}
                                <DroppableContainer id="q3" className={styles.quadrant}>
                                    {containers.q3.map(id => {
                                        const issue = getIssue(id);
                                        if (!issue) return null;
                                        const cost = globalState?.materiality_dictionary_override?.issues?.find(i => i.id === id)?.mitigation_cost_usd ?? issue.mitigation_cost_usd;
                                        return <IssueChip key={id} issue={{ ...issue, mitigation_cost_usd: cost }} isDragging={activeId === id} />;
                                    })}
                                </DroppableContainer>

                            </div>

                            <div className={styles.xAxisLabel}>Financial Materiality (Enterprise Value)</div>
                        </div>
                    </div>

                    {/* Overlay for smooth dragging rendering outside regular flow */}
                    <DragOverlay>
                        {activeId ? (() => {
                            const issue = getIssue(activeId);
                            if (!issue) return null;
                            const cost = globalState?.materiality_dictionary_override?.issues?.find(i => i.id === activeId)?.mitigation_cost_usd ?? issue.mitigation_cost_usd;
                            return <OverlayChip issue={{ ...issue, mitigation_cost_usd: cost }} />;
                        })() : null}
                    </DragOverlay>

                </DndContext>
            </main>

            {/* ── Modals ── */}

            {/* Consultant Confirmation */}
            {showConsultantConfirm && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modalContent}>
                        <h3>Hire McBain & Partners</h3>
                        <p>Deduct ${consultantFee.toLocaleString()} from your Corporate Strategic Fund to hire McBain & Partners?</p>
                        <p className={styles.modalSubtext}>They will automatically classify 5 issues and provide an ESG Materiality Cheat Sheet.</p>
                        <div className={styles.modalActions}>
                            <button onClick={handleHireConsultant} className={styles.submitBtn}>Yes, Hire Them</button>
                            <button onClick={() => setShowConsultantConfirm(false)} className={styles.cancelBtn}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Cheat Sheet (Persistent) */}
            {showCheatSheet && (
                <div className={styles.cheatSheetPanel}>
                    <h4>📋 McBain & Partners Cheat Sheet</h4>
                    <p><strong>Outside-In (Financial Materiality):</strong> How sustainability issues affect the company\'s cash flows, development, performance, and position.</p>
                    <p><strong>Inside-Out (Impact Materiality):</strong> How the company\'s operations affect people or the environment.</p>
                    <p style={{ fontSize: '0.82rem', color: '#64748b', borderTop: '1px solid #e2e8f0', paddingTop: '0.65rem', marginBottom: '0.5rem' }}>
                        <strong style={{ color: '#475569' }}>Quadrant 1 (Top-Right):</strong> Issues that are <em>both</em> financially material <em>and</em> have high societal impact — these require CFO-approved capital allocation.
                    </p>
                    <button onClick={() => setShowCheatSheet(false)} className={styles.closeTabBtn}>✕ Dismiss</button>
                </div>
            )}

            {/* Error / Success Modal */}
            {submitStatus && (
                <div className={styles.modalOverlay}>
                    <div className={`${styles.modalContent} ${submitStatus.type === 'error' ? styles.errorModal : styles.successModal}`}>
                        {submitStatus.type === 'error' ? (
                            <>
                                <h3>📝 Memo from CFO</h3>
                                <p className={styles.errorText}>{submitStatus.message}</p>
                                <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'center' }}>
                                    <button onClick={() => setSubmitStatus(null)} className={styles.cancelBtn} style={{ flex: 1 }}>Fix Matrix</button>
                                    <button
                                        onClick={() => handleSubmit(true)}
                                        className={styles.submitBtn}
                                        style={{ flex: 1, background: '#ef4444', borderColor: '#ef4444', color: 'white' }}
                                        title="Have you considered carefully the long term impact of your choices on the ESG aspects of your company?"
                                    >
                                        Force Override
                                    </button>
                                </div>
                            </>
                        ) : (
                            <>
                                <h3>✅ Matrix Approved</h3>
                                <p>The CFO has approved your CSRD assessment.</p>
                                <div className={styles.budgetBox}>
                                    + ${submitStatus.amount?.toLocaleString()} Unlocked
                                </div>
                                <button onClick={onClose} className={styles.submitBtn}>Return to Dashboard</button>
                            </>
                        )}
                    </div>
                </div>
            )}

        </div>
    );
}
