'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
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

/* Counter for custom factors */
let _customFactorCounter = 0;

/**
 * Draggable Issue Chip component — Fix 7 (cost badge), Fix 10 (IRO badge + data-tooltip)
 */
function IssueChip({ issue, isDragging, isBlindspot = false, isStakeholderBoosted = false }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: issue.id,
        data: issue,
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 9999,
        opacity: isDragging ? 0.4 : 1,
    } : undefined;

    const getCategoryIcon = (category) => {
        switch (category) {
            case 'ecological': return <span className={styles.catIcon} style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.5)' }}>E</span>;
            case 'social': return <span className={styles.catIcon} style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.5)' }}>S</span>;
            case 'governance': return <span className={styles.catIcon} style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.5)' }}>G</span>;
            case 'economic': return <span className={styles.catIcon} style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.5)' }}>G</span>;
            default: return null;
        }
    };

    const costDisplay = issue.mitigation_cost_usd > 0
        ? `$${(issue.mitigation_cost_usd / 1_000_000).toFixed(1)}M`
        : null;

    const iroType = issue.iro_type || null;

    // ESRS spectrum tags
    const severityColor = { high: '#ef4444', medium: '#f59e0b', low: '#10b981' };
    const horizonLabel = { short: 'ST', medium: 'MT', long: 'LT' };
    const sev = issue.severity;
    const horizon = issue.time_horizon;

    // ── NEW: ESRS topic badge color ──
    const esrsTopicColor = (t) => {
        if (!t) return { bg: 'rgba(148,163,184,0.15)', color: '#94a3b8' };
        if (t.startsWith('E')) return { bg: 'rgba(16,185,129,0.15)', color: '#10b981' };
        if (t.startsWith('S')) return { bg: 'rgba(59,130,246,0.15)', color: '#60a5fa' };
        return { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b' };
    };
    const vcLabel = { own_ops: '🏭', upstream: '⬆', downstream: '⬇' };
    const esrsTopic = issue.esrs_topic || null;
    const vcScope = issue.value_chain_scope || null;
    const isAmbiguous = !!issue.is_ambiguous;

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            className={`${styles.chip} ${isDragging ? styles.chipDragging : ''} ${isBlindspot ? styles.chipBlindspot : ''} ${isStakeholderBoosted ? styles.chipBoosted : ''}`}
            data-tooltip={isBlindspot ? '⚠️ R1 Audit Gap: Incomplete data — description degraded. Commission a Stakeholder Panel to restore clarity.' : (issue.hover_description || undefined)}
        >
            <div className={styles.chipLeft}>
                {getCategoryIcon(issue.category)}
            </div>
            <span className={styles.chipTitle}>{issue.title}</span>
            {isStakeholderBoosted && (
                <span className={styles.boostBadge} title="Stakeholder confirmed in R1 audit">★</span>
            )}
            {isBlindspot && (
                <span className={styles.blindspotBadge} title="R1 audit gap — data degraded">⚠</span>
            )}
            {isAmbiguous && (
                <span title="Ambiguous placement — genuinely sits on a quadrant boundary. Discuss in debrief."
                    style={{ fontSize: '0.68rem', cursor: 'help' }}>🔄</span>
            )}
            {esrsTopic && (() => {
                const tc = esrsTopicColor(esrsTopic);
                return (
                    <span title={`ESRS Topic: ${esrsTopic}`}
                        style={{ padding: '1px 5px', borderRadius: '3px', fontSize: '0.68rem', fontWeight: 800,
                            background: tc.bg, color: tc.color, border: `1px solid ${tc.color}44`,
                            letterSpacing: '0.02em', flexShrink: 0 }}>
                        {esrsTopic}
                    </span>
                );
            })()}
            {vcScope && vcLabel[vcScope] && (
                <span title={`Value chain: ${vcScope.replace('_', ' ')}`}
                    style={{ fontSize: '0.68rem', cursor: 'help', flexShrink: 0 }}>
                    {vcLabel[vcScope]}
                </span>
            )}
            {sev && (
                <span className={styles.severityBadge} style={{ background: `${severityColor[sev]}22`, color: severityColor[sev], border: `1px solid ${severityColor[sev]}55` }}>
                    {sev.toUpperCase()[0]}
                </span>
            )}
            {horizon && (
                <span className={styles.horizonBadge}>{horizonLabel[horizon] || horizon.toUpperCase()}</span>
            )}
            {iroType && (
                <span className={styles.iroBadge} data-iro={iroType}>
                    {iroType === 'impact' ? 'IMP' : iroType === 'risk' ? 'RSK' : 'OPP'}
                </span>
            )}
            {costDisplay && (
                <span className={styles.costBadge}>{costDisplay}</span>
            )}
        </div>
    );
}

/**
 * Overlay Chip for smooth drag animations
 */
function OverlayChip({ issue }) {
    if (!issue) return null;
    return (
        <div className={`${styles.chip} ${styles.chipDragging}`}>
            <span className={styles.chipTitle}>{issue.title}</span>
        </div>
    );
}

/**
 * Droppable Container component — Fix 5 (empty state), Fix 8 (ESRS subtitle)
 */
function DroppableContainer({ id, className, children, label, extraText, esrsLabel, hasItems }) {
    const { isOver, setNodeRef } = useDroppable({ id });

    return (
        <div
            ref={setNodeRef}
            className={`${className} ${isOver ? styles.isOver : ''}`}
        >
            {label && id !== 'bank' && <div className={styles.quadrantHeader}>{label}</div>}
            {label && id === 'bank' && <div style={{ fontWeight: 'bold', color: '#0f172a', marginBottom: '8px' }}>{label}</div>}
            {extraText && <div className={styles.bgText}>{extraText}</div>}
            {/* Fix 5: Empty state drop affordance */}
            {!hasItems && id !== 'bank' && (
                <div className={styles.emptyQuadrant}>
                    <span>📥</span>
                    <span>Drag issues here</span>
                </div>
            )}
            {children}
            {/* Fix 8: ESRS subtitle */}
            {esrsLabel && <div className={styles.esrsSubtitle}>{esrsLabel}</div>}
        </div>
    );
}

/**
 * Fix 2 + Fix 6: Dark-mode-aware SVG Cartesian plane with visible axis labels
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
            {/* Fix 2: Dark-mode colour scheme — muted, executive tones */}
            {/* Base: dark warm slate */}
            <rect width="140" height="140" fill="rgba(30, 41, 59, 0.3)" />

            {/* Low Priority (bottom-left) — muted teal */}
            <path d="M 0,140 L 60,140 L 60,95 Q 60,80 45,80 L 0,80 Z" fill="rgba(16, 185, 129, 0.10)" />

            {/* High Risk (top + right) — muted red-pink */}
            <path d="M 0,0 L 140,0 L 140,140 L 100,140 L 100,55 Q 100,40 85,40 L 0,40 Z" fill="rgba(239, 68, 68, 0.08)" />

            {/* Grid lines — subtle */}
            {ticks.map((pos) => (
                <g key={pos}>
                    <line x1="0" y1={pos} x2="140" y2={pos} stroke="rgba(148, 163, 184, 0.08)" strokeWidth="0.25" />
                    <line x1={pos} y1="0" x2={pos} y2="140" stroke="rgba(148, 163, 184, 0.08)" strokeWidth="0.25" />
                </g>
            ))}

            {/* Fix 4: Major axes — softer reference lines, not hard divisions */}
            <line x1="0" y1="70" x2="140" y2="70" stroke="rgba(148, 163, 184, 0.2)" strokeWidth="0.5" strokeDasharray="2,2" />
            <line x1="70" y1="0" x2="70" y2="140" stroke="rgba(148, 163, 184, 0.2)" strokeWidth="0.5" strokeDasharray="2,2" />

            {/* Fix 6: Axis labels — high contrast, readable */}
            <text x="135" y="73" fontSize="3.2" fontWeight="800" fill="rgba(148, 163, 184, 0.5)" textAnchor="end" letterSpacing="0.15">HIGH →</text>
            <text x="5" y="73" fontSize="3.2" fontWeight="800" fill="rgba(148, 163, 184, 0.5)" textAnchor="start" letterSpacing="0.15">← LOW</text>
            <text x="70" y="5" fontSize="3.2" fontWeight="800" fill="rgba(148, 163, 184, 0.5)" textAnchor="middle" letterSpacing="0.15">HIGH ↑</text>
            <text x="70" y="139" fontSize="3.2" fontWeight="800" fill="rgba(148, 163, 184, 0.5)" textAnchor="middle" letterSpacing="0.15">↓ LOW</text>
        </svg>
    );
};

/**
 * Fix 1: Onboarding Tutorial Overlay
 */
function OnboardingOverlay({ onDismiss }) {
    return (
        <div className={styles.onboardingOverlay}>
            <div className={styles.onboardingCard}>
                <h2>📊 CSRD Double Materiality Matrix</h2>
                <p>Assess your sustainability issues across two dimensions: how they affect \
your company financially (Financial Materiality) and how your company \
impacts people and the planet (Impact Materiality).</p>

                <div className={styles.onboardingSteps}>
                    <div className={styles.onboardingStep}>
                        <span className={styles.stepNum}>1</span>
                        <div className={styles.stepContent}>
                            <h4>Read each ESG issue in the Issue Bank</h4>
                            <p>Hover over any issue chip to see its description. Each is tagged as Ecological (E), Social (S), or Governance (G).</p>
                        </div>
                    </div>
                    <div className={styles.onboardingStep}>
                        <span className={styles.stepNum}>2</span>
                        <div className={styles.stepContent}>
                            <h4>Drag issues to the appropriate quadrant</h4>
                            <p>Place each issue where it belongs on the matrix based on its financial and societal impact. Issues in the top-right (Q1) are doubly material.</p>
                        </div>
                    </div>
                    <div className={styles.onboardingStep}>
                        <span className={styles.stepNum}>3</span>
                        <div className={styles.stepContent}>
                            <h4>Quadrant 1 drives capital allocation</h4>
                            <p>Issues placed in Q1 (CFO Approved — Prioritise) will have their mitigation costs deducted from your Corporate Strategic Fund budget.</p>
                        </div>
                    </div>
                    <div className={styles.onboardingStep}>
                        <span className={styles.stepNum}>4</span>
                        <div className={styles.stepContent}>
                            <h4>Submit when 6+ issues are placed</h4>
                            <p>Place at least 6 issues onto the matrix, then submit for CFO review. You can undo placements or reset the board at any time.</p>
                        </div>
                    </div>
                </div>

                <button className={styles.onboardingDismiss} onClick={onDismiss}>
                    Got It — Start Assessment
                </button>
            </div>
        </div>
    );
}

/**
 * Main Double Materiality Matrix Component
 */
export default function DoubleMaterialityMatrix({ onSubmit, onClose, csfPool = Infinity, initialQ1 = [], globalState = {}, buId = null, buLabel = null, sessionId = null, onOpenAdvisor = null }) {
    const [issues, setIssues] = useState([]);
    const [consultantFee, setConsultantFee] = useState(1500000);
    const [loading, setLoading] = useState(true);

    const [activeId, setActiveId] = useState(null);
    const [consultantUsed, setConsultantUsed] = useState(false);
    const [consultantAllowed, setConsultantAllowed] = useState(true);

    // Stakeholder Panel Survey state
    const [panelIssueCount, setPanelIssueCount] = useState(4);

    // R1 intelligence modulation
    const [blindspotActive, setBlindspotActive] = useState(false);
    const [stakeholderBoostedIds, setStakeholderBoostedIds] = useState([]);

    // Onboarding state
    const [showOnboarding, setShowOnboarding] = useState(true);

    // Undo history
    const [history, setHistory] = useState([]);

    // Custom factor form
    const [showAddFactor, setShowAddFactor] = useState(false);
    const [customTitle, setCustomTitle] = useState('');
    const [customCategory, setCustomCategory] = useState('ecological');

    // Modal states
    const [showConsultantConfirm, setShowConsultantConfirm] = useState(false);
    const [showCheatSheet, setShowCheatSheet] = useState(false);
    const [submitStatus, setSubmitStatus] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Time horizon filter (Gap 3)
    const [horizonFilter, setHorizonFilter] = useState('all'); // 'all' | 'short' | 'medium' | 'long'

    // 4-tab stakeholder group (Gap 2)
    const [activePanelGroup, setActivePanelGroup] = useState('investors');

    // Initial state: empty until fetched
    const [containers, setContainers] = useState({
        bank: [],
        q1: [], // Top Right: High Fin / High Impact
        q2: [], // Top Left: Low Fin / High Impact
        q3: [], // Bottom Right: High Fin / Low Impact
        q4: []  // Bottom Left: Low Fin / Low Impact
    });

    // Ref for initial containers (for reset)
    const initialContainersRef = useRef(null);

    useEffect(() => {
        const fetchConfig = async () => {
            try {
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
                        const initial = { bank: bankIds, q1: q1Ids, q2: [], q3: [], q4: [] };
                        initialContainersRef.current = JSON.parse(JSON.stringify(initial));
                        return initial;
                    });
                }
            } catch { /* Backend unreachable */ }
            setLoading(false);
        };
        fetchConfig();
    }, [buId]);

    // Detect R1 blindspot and stakeholder boost from globalState
    useEffect(() => {
        const flags = globalState?.active_event_flags || {};
        const allFlags = Object.keys(flags).filter(k => flags[k] === true || Array.isArray(flags[k]));
        setBlindspotActive(
            !!(flags.electronics_blindspot || flags.r1_blindspot_active_in_r2)
        );
        setStakeholderBoostedIds(globalState?.stakeholder_boosted_issues || []);
    }, [globalState]);

    // Fetch consultant allowed status from facilitator
    useEffect(() => {
        if (!sessionId) return;
        const checkConsultant = async () => {
            try {
                const res = await fetch(`${API}/api/admin/consultant-allowed/${sessionId}`);
                if (res.ok) {
                    const data = await res.json();
                    setConsultantAllowed(data.consultant_allowed);
                }
            } catch { /* default to true */ }
        };
        checkConsultant();
    }, [sessionId]);

    // Add custom factor handler
    const handleAddCustomFactor = useCallback(() => {
        if (!customTitle.trim()) return;
        _customFactorCounter++;
        const newId = `custom_factor_${_customFactorCounter}_${Date.now()}`;
        const newIssue = {
            id: newId,
            title: customTitle.trim(),
            category: customCategory,
            hover_description: `Custom factor added by player: ${customTitle.trim()}`,
            financial_impact: 'medium',
            societal_impact: 'medium',
            mitigation_cost_usd: 0,
            is_custom: true,
        };
        setIssues(prev => [...prev, newIssue]);
        setContainers(prev => ({ ...prev, bank: [...prev.bank, newId] }));
        setCustomTitle('');
        setShowAddFactor(false);
    }, [customTitle, customCategory]);

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
        useSensor(KeyboardSensor)
    );

    const handleDragStart = (event) => {
        setActiveId(event.active.id);
    };

    // Fix 3: Push to history on every drag
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
            // Save current state to history before changing
            setHistory(prev => [...prev, JSON.parse(JSON.stringify(containers))]);

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

    // Fix 3: Undo last action
    const handleUndo = useCallback(() => {
        if (history.length === 0) return;
        const previous = history[history.length - 1];
        setContainers(previous);
        setHistory(prev => prev.slice(0, -1));
    }, [history]);

    // Fix 3: Reset to initial state
    const handleReset = useCallback(() => {
        if (initialContainersRef.current) {
            setHistory(prev => [...prev, JSON.parse(JSON.stringify(containers))]);
            setContainers(JSON.parse(JSON.stringify(initialContainersRef.current)));
        }
    }, [containers]);

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

        // Save to history before auto-solving
        setHistory(prev => [...prev, JSON.parse(JSON.stringify(containers))]);

        // Auto-solve 5 issues
        setContainers(prev => {
            const newContainers = { ...prev };
            let currentBank = [...newContainers.bank];
            let solvedCount = 0;

            for (let i = currentBank.length - 1; i >= 0 && solvedCount < 5; i--) {
                const issueId = currentBank[i];
                const issue = getIssue(issueId);
                if (issue) {
                    const targetQuad = `q${getCorrectQuadrant(issue)}`;
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
            panel_issue_count: panelIssueCount,
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
            setSubmitStatus({ type: 'success', amount: result.allocated_budget, debrief: result.debrief });
            setIsSubmitting(false);
        }
    };

    const placedCount = containers.q1.length + containers.q2.length + containers.q3.length + containers.q4.length;
    const MIN_PLACED = 6;
    const hasEnoughPlaced = placedCount >= MIN_PLACED;

    const totalQ1Cost = containers.q1.reduce((sum, id) => {
        const issue = getIssue(id);
        const finalCost = issue ? issue.mitigation_cost_usd : 0;
        return sum + finalCost;
    }, 0);
    const isOverBudget = totalQ1Cost > csfPool;

    // Compute stakeholder panel fee for display
    const panelFee = panelIssueCount <= 4
        ? panelIssueCount * 250_000
        : (4 * 250_000) + ((panelIssueCount - 4) * 500_000);

    // Helper to render chip list for a container
    const renderChips = (containerKey) => {
        return containers[containerKey].map(id => {
            const issue = getIssue(id);
            if (!issue) return null;
            // Gap 3: time horizon filter (only apply to bank — placed issues always visible)
            if (containerKey === 'bank' && horizonFilter !== 'all') {
                if (issue.time_horizon && issue.time_horizon !== horizonFilter) return null;
            }
            const cost = globalState?.materiality_dictionary_override?.issues?.find(i => i.id === id)?.mitigation_cost_usd ?? issue.mitigation_cost_usd;
            const isBlindspot = blindspotActive && !!issue.electronics_sensitive;
            const isBoosted = stakeholderBoostedIds.includes(id);
            return <IssueChip key={id} issue={{ ...issue, mitigation_cost_usd: cost }} isDragging={activeId === id} isBlindspot={isBlindspot} isStakeholderBoosted={isBoosted} />;
        });
    };

    if (loading) return <div className={styles.overlay}><div className={styles.header}><h2 style={{ color: 'white' }}>Loading Materiality Dictionary...</h2></div></div>;

    return (
        <div className={styles.overlay}>
            {/* Fix 1: Onboarding */}
            {showOnboarding && <OnboardingOverlay onDismiss={() => setShowOnboarding(false)} />}

            <div className={styles.header}>
                <h2 className={styles.headerTitle}>
                    <span>📊</span> {buLabel ? `${buLabel} — ` : ''}CSRD Double Materiality Matrix
                </h2>
                <div className={styles.headerActions}>
                    {/* Fix 3: Undo + Reset */}
                    <button
                        className={styles.undoBtn}
                        onClick={handleUndo}
                        disabled={history.length === 0}
                        data-tooltip="Undo your last placement"
                    >
                        ↩ Undo
                    </button>
                    <button
                        className={styles.resetBtn}
                        onClick={handleReset}
                        data-tooltip="Reset all issues back to the Issue Bank"
                    >
                        🔄 Reset
                    </button>

                    {/* Stakeholder Panel Survey */}
                    {!consultantUsed && consultantAllowed && (
                        <button
                            className={styles.consultantBtn}
                            onClick={() => setShowConsultantConfirm(true)}
                            data-tooltip="Engage an independent stakeholder panel to pre-rate issues (ESRS 1 §1.47-1.50)"
                        >
                            👥 Commission Stakeholder Panel Survey
                        </button>
                    )}
                    {!consultantUsed && !consultantAllowed && (
                        <button
                            className={styles.advisorPromptBtn}
                            onClick={() => { if (onOpenAdvisor) { onOpenAdvisor(); } }}
                        >
                            🧠 Need Help? Ask the AI Advisor
                        </button>
                    )}
                    {consultantUsed && (
                        <span className={styles.consultantBadge}>👥 Panel Survey Active ({panelIssueCount} issues rated)</span>
                    )}
                    {blindspotActive && (
                        <span className={styles.blindspotWarning} title="R1 Surface Scan left gaps — some issue descriptions are degraded">
                            ⚠️ R1 Audit Gap Active
                        </span>
                    )}
                    <div style={{ padding: '0 0.75rem', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center', minWidth: '140px' }}>
                        <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700 }}>Placed</span>
                        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: hasEnoughPlaced ? '#4ade80' : '#f59e0b' }}>
                            {placedCount} / {issues.length} issues
                        </span>
                        {/* CL-4: Visual completion bar */}
                        <div style={{ width: '100%', height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, marginTop: 3, overflow: 'hidden' }}>
                            <div style={{
                                height: '100%', borderRadius: 2,
                                width: `${Math.min(100, (placedCount / Math.max(1, issues.length)) * 100)}%`,
                                background: hasEnoughPlaced ? '#4ade80' : '#f59e0b',
                                transition: 'width 0.3s ease, background 0.3s ease',
                            }} />
                        </div>
                        <div style={{ display: 'flex', gap: '0.4rem', marginTop: 2, fontSize: '0.58rem', color: '#64748b' }}>
                            <span>Q1:{containers.q1.length}</span>
                            <span>Q2:{containers.q2.length}</span>
                            <span>Q3:{containers.q3.length}</span>
                            <span>Q4:{containers.q4.length}</span>
                        </div>
                    </div>
                    {/* Fix 7: Budget counter with animated connection */}
                    <div style={{ padding: '0 0.75rem', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center' }}>
                        <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700 }}>Q1 Budget</span>
                        <span style={{
                            fontWeight: 700, fontSize: '0.9rem',
                            color: isOverBudget ? '#ef4444' : totalQ1Cost > 0 ? '#f59e0b' : '#4ade80',
                            transition: 'color 0.3s ease',
                        }}>
                            ${(totalQ1Cost / 1_000_000).toFixed(1)}M / ${(csfPool / 1_000_000).toFixed(1)}M
                        </span>
                    </div>
                    <button
                        className={styles.submitBtn}
                        disabled={isSubmitting || isOverBudget || !hasEnoughPlaced}
                        onClick={() => handleSubmit(false)}
                        data-tooltip={!hasEnoughPlaced ? `Place at least ${MIN_PLACED} issues into quadrants before submitting.` : isOverBudget ? "Your Quadrant 1 CapEx exceeds the total CSF pool balance." : "Submit your materiality assessment for CFO review."}
                    >
                        {isSubmitting ? 'Submitting...' : !hasEnoughPlaced ? `Place ${MIN_PLACED - placedCount} More Issues` : 'Submit Matrix to CFO'}
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

                        {/* Fix 5: Category Legend */}
                        <div className={styles.legend}>
                            <span className={styles.legendItem}>
                                <span className={styles.catIcon} style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.5)', width: 18, height: 18, fontSize: '0.6rem' }}>E</span>
                                Ecological
                            </span>
                            <span className={styles.legendItem}>
                                <span className={styles.catIcon} style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.5)', width: 18, height: 18, fontSize: '0.6rem' }}>S</span>
                                Social
                            </span>
                            <span className={styles.legendItem}>
                                <span className={styles.catIcon} style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', border: '1px solid rgba(245, 158, 11, 0.5)', width: 18, height: 18, fontSize: '0.6rem' }}>G</span>
                                Governance
                            </span>
                        </div>

                        <DroppableContainer id="bank" className={styles.bankScroll}>
                            {renderChips('bank')}
                        </DroppableContainer>

                        {/* Add Custom Factor */}
                        <div className={styles.addFactorSection}>
                            {!showAddFactor ? (
                                <button className={styles.addFactorBtn} onClick={() => setShowAddFactor(true)}>
                                    + Add Custom Factor
                                </button>
                            ) : (
                                <div className={styles.addFactorForm}>
                                    <input
                                        className={styles.addFactorInput}
                                        type="text"
                                        placeholder="e.g. Renewable Energy Transition"
                                        value={customTitle}
                                        onChange={(e) => setCustomTitle(e.target.value)}
                                        onKeyDown={(e) => { if (e.key === 'Enter') handleAddCustomFactor(); }}
                                        autoFocus
                                    />
                                    <div className={styles.addFactorRow}>
                                        <select
                                            className={styles.addFactorSelect}
                                            value={customCategory}
                                            onChange={(e) => setCustomCategory(e.target.value)}
                                        >
                                            <option value="ecological">🌱 Ecological</option>
                                            <option value="social">👥 Social</option>
                                            <option value="economic">💰 Economic</option>
                                        </select>
                                        <button className={styles.addFactorConfirm} onClick={handleAddCustomFactor} disabled={!customTitle.trim()}>Add</button>
                                        <button className={styles.addFactorCancel} onClick={() => { setShowAddFactor(false); setCustomTitle(''); }}>✕</button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right Pane: The Grid */}
                    <div className={styles.rightPane}>
                        {/* Gap 3: Time Horizon Filter */}
                        <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '0.5rem', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginRight: '0.25rem' }}>Horizon</span>
                            {[['all', 'All', '#6366f1'], ['short', 'ST ≤1yr', '#ef4444'], ['medium', 'MT 1-5yr', '#f59e0b'], ['long', 'LT >5yr', '#10b981']].map(([val, label, color]) => (
                                <button key={val} onClick={() => setHorizonFilter(val)}
                                    style={{
                                        padding: '2px 10px', borderRadius: '12px', border: `1px solid ${horizonFilter === val ? color : 'rgba(255,255,255,0.1)'}`,
                                        background: horizonFilter === val ? `${color}22` : 'transparent',
                                        color: horizonFilter === val ? color : '#64748b',
                                        fontSize: '0.68rem', fontWeight: 700, cursor: 'pointer',
                                        transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                    }}>{label}</button>
                            ))}
                            {horizonFilter !== 'all' && (
                                <span style={{ fontSize: '0.68rem', color: '#64748b', fontStyle: 'italic', marginLeft: '0.25rem' }}>Bank filtered — placed issues always visible</span>
                            )}
                        </div>
                        <div className={styles.axesContainer}>
                            <div className={styles.yAxisLabel}>Impact Materiality (People/Planet)</div>

                            <div className={styles.matrixGrid}>
                                <CartesianBackground />

                                {/* Top Left: Low Fin / High Impact — Monitor & Engage */}
                                {/* Fix 8: ESRS dual label */}
                                <DroppableContainer
                                    id="q2"
                                    className={styles.quadrant}
                                    extraText="Monitor & Engage"
                                    esrsLabel="Impact Material — Report Impact"
                                    hasItems={containers.q2.length > 0}
                                >
                                    {renderChips('q2')}
                                </DroppableContainer>

                                {/* Top Right: High Fin / High Impact (THE TARGET) — Prioritise */}
                                <DroppableContainer
                                    id="q1"
                                    className={`${styles.quadrant} ${styles.quadrant1}`}
                                    label="⚡ Prioritise & Allocate CapEx"
                                    extraText="CFO Approved — Prioritise"
                                    esrsLabel="Double Material — Report under ESRS"
                                    hasItems={containers.q1.length > 0}
                                >
                                    {renderChips('q1')}
                                </DroppableContainer>

                                {/* Bottom Left: Low Fin / Low Impact — Low Priority */}
                                <DroppableContainer
                                    id="q4"
                                    className={styles.quadrant}
                                    extraText="Low Priority"
                                    esrsLabel="Not Material — Monitor Only"
                                    hasItems={containers.q4.length > 0}
                                >
                                    {renderChips('q4')}
                                </DroppableContainer>

                                {/* Bottom Right: High Fin / Low Impact — Watch & Manage */}
                                <DroppableContainer
                                    id="q3"
                                    className={styles.quadrant}
                                    extraText="Watch & Manage"
                                    esrsLabel="Financially Material — Report Risk"
                                    hasItems={containers.q3.length > 0}
                                >
                                    {renderChips('q3')}
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

            {/* Stakeholder Panel Survey Confirmation — 4-group ESRS §1.47-1.50 */}
            {showConsultantConfirm && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modalContent}>
                        <h3>👥 Commission Stakeholder Panel Survey</h3>
                        <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
                            Engage independent stakeholder groups to pre-rate issues. Modelling ESRS 1 §1.47–1.50 stakeholder engagement requirements.
                        </p>

                        {/* 4-group tab selector — ESRS §1.47-1.50 */}
                        <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                            {[
                                { key: 'investors', label: '💰 Investors', desc: 'Prioritise Q3 financial risks and transition risks. May underweight community impacts.', color: '#6366f1' },
                                { key: 'workers', label: '👷 Own Workforce', desc: 'Surface S1 labour, safety, and fair wage issues. Strong on internal impacts.', color: '#3b82f6' },
                                { key: 'ngos', label: '🌍 NGOs / Communities', desc: 'Elevate Q2 environmental and community impacts (E4, S2, S3). May overweight long-term.', color: '#10b981' },
                                { key: 'experts', label: '🎓 Subject Matter Experts', desc: 'Provide technical accuracy on ESRS mapping and threshold calibration.', color: '#f59e0b' },
                            ].map(g => (
                                <button key={g.key} onClick={() => setActivePanelGroup(g.key)}
                                    style={{
                                        padding: '0.3rem 0.7rem', borderRadius: '6px', cursor: 'pointer',
                                        border: `1px solid ${activePanelGroup === g.key ? g.color : 'rgba(255,255,255,0.1)'}`,
                                        background: activePanelGroup === g.key ? `${g.color}22` : 'rgba(255,255,255,0.03)',
                                        color: activePanelGroup === g.key ? g.color : '#94a3b8',
                                        fontSize: '0.72rem', fontWeight: 700, transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                    }}>{g.label}</button>
                            ))}
                        </div>
                        {/* Group description */}
                        {(() => {
                            const groups = {
                                investors: { desc: 'Investors prioritise Q3 financial risks and transition risks (ESRS E1, G1). They may underweight community and social impacts relative to NGOs.', ref: 'ESRS §1.47(a)', color: '#6366f1' },
                                workers:   { desc: 'Own workforce focuses on S1 issues: fair wages, health & safety, working conditions. Strong signal for internal impacts.', ref: 'ESRS §1.47(b)', color: '#3b82f6' },
                                ngos:      { desc: 'NGOs and affected communities elevate Q2 environmental harms (E3, E4, S2, S3). ESRS §1.50: their views may conflict with investor priorities — this tension is pedagogically important.', ref: 'ESRS §1.47(c)', color: '#10b981' },
                                experts:   { desc: 'Subject matter experts (academics, assurance providers) calibrate ESRS topic mapping and materiality thresholds. They validate whether issues are correctly classified under E1–E5 and S1–S4.', ref: 'ESRS §1.47(d)', color: '#f59e0b' },
                            };
                            const g = groups[activePanelGroup];
                            return (
                                <div style={{ padding: '0.55rem 0.75rem', background: `${g.color}10`, borderRadius: '7px', borderLeft: `2px solid ${g.color}`, marginBottom: '0.75rem' }}>
                                    <div style={{ fontSize: '0.68rem', fontWeight: 700, color: g.color, marginBottom: '0.2rem' }}>{g.ref}</div>
                                    <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.5 }}>{g.desc}</div>
                                </div>
                            );
                        })()}

                        <div style={{ margin: '0.5rem 0', padding: '0.75rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                            <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '0.4rem' }}>
                                Issues to pre-rate: <strong style={{ color: '#f1f5f9' }}>{panelIssueCount}</strong>
                                {panelIssueCount > 4 && <span style={{ color: '#f59e0b', marginLeft: '0.5rem' }}>★ Extended panel (doubled rate)</span>}
                            </label>
                            <input type="range" min={1} max={8} value={panelIssueCount}
                                onChange={e => setPanelIssueCount(+e.target.value)}
                                style={{ width: '100%', accentColor: '#6366f1' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b' }}>
                                <span>1 issue — $250K</span><span>4 issues — $1M</span><span>8 issues — $3M</span>
                            </div>
                        </div>
                        <p style={{ fontWeight: 700, color: '#f1f5f9', textAlign: 'center', fontSize: '1rem' }}>
                            Cost: <span style={{ color: '#6366f1' }}>${(panelFee / 1_000_000).toFixed(2)}M</span>
                        </p>
                        <p className={styles.modalSubtext}>
                            The panel will auto-classify {Math.min(panelIssueCount, 5)} issues on the matrix.
                            Issues rated by stakeholders aligned with your R1 Mendelow mapping are marked ★.
                        </p>
                        <p style={{ fontSize: '0.72rem', color: '#64748b', fontStyle: 'italic', textAlign: 'center', marginTop: '0.25rem' }}>
                            ESRS §1.50: Commission all 4 groups to surface conflicting views and strengthen your materiality assessment.
                        </p>
                        <div className={styles.modalActions}>
                            <button onClick={handleHireConsultant} className={styles.submitBtn}>Commission Panel</button>
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
                                        data-tooltip="Warning: Overriding the CFO may negatively impact your reputation score. Have you considered the long-term ESG implications?"
                                    >
                                        Force Override
                                    </button>
                                </div>
                            </>
                        ) : (
                            <>
                                <h3>✅ Materiality Matrix Approved</h3>
                                <div 
                                    className={styles.budgetBox}
                                    title={submitStatus.debrief ? `Calculated as: Total Materiality Budget ($15,000,000) × ${submitStatus.debrief.full_accuracy_pct}% Accuracy\nMinus Consultant Fees ($${(consultantFee || 0).toLocaleString()})\n${submitStatus.debrief.clawback_applied > 0 ? `Minus Governance Penalty / Clawback ($${submitStatus.debrief.clawback_applied.toLocaleString()})\n` : ''}= $${submitStatus.amount?.toLocaleString()} Final Unlocked Budget` : `Allocated Budget: $${submitStatus.amount?.toLocaleString()}`}
                                >
                                    + ${submitStatus.amount?.toLocaleString()} Unlocked
                                </div>
                                {submitStatus.debrief && (
                                    <div style={{ textAlign: 'left', marginTop: '1rem', fontSize: '0.8rem' }}>
                                        {/* ESRS Reference */}
                                        <div style={{ padding: '0.6rem', background: 'rgba(99,102,241,0.1)', borderRadius: '6px', borderLeft: '3px solid #6366f1', marginBottom: '0.75rem' }}>
                                            <strong style={{ color: '#818cf8' }}>📋 {submitStatus.debrief.esrs_reference}</strong>
                                            <p style={{ color: '#cbd5e1', margin: '0.3rem 0 0' }}>{submitStatus.debrief.scoring_rationale}</p>
                                        </div>

                                        {/* ── Gap 4: Transparent Scoring Breakdown ── */}
                                        <details style={{ marginBottom: '0.75rem' }}>
                                            <summary style={{ cursor: 'pointer', padding: '0.5rem 0.6rem', background: 'rgba(255,255,255,0.04)', borderRadius: '6px', borderLeft: '3px solid #6366f1', color: '#a5b4fc', fontWeight: 700, fontSize: '0.78rem', listStyle: 'none', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                                <span>📊</span> How was this scored? ({submitStatus.debrief.full_accuracy_pct}% accuracy)
                                            </summary>
                                            <div style={{ padding: '0.6rem', background: 'rgba(0,0,0,0.15)', borderRadius: '0 0 6px 6px', borderLeft: '3px solid #6366f1' }}>
                                                <p style={{ color: '#94a3b8', fontSize: '0.72rem', margin: '0 0 0.5rem', fontStyle: 'italic' }}>ESRS 1 §1.38: Materiality threshold = ≥80% Q1 accuracy + board-level governance oversight</p>
                                                {submitStatus.debrief.q1_correct?.length > 0 && (
                                                    <div style={{ marginBottom: '0.5rem' }}>
                                                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#4ade80', marginBottom: '0.25rem' }}>✅ Correctly in Q1 ({submitStatus.debrief.q1_correct.length})</div>
                                                        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                                                            {submitStatus.debrief.q1_correct.map(id => (
                                                                <span key={id} style={{ padding: '2px 7px', borderRadius: '4px', background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.3)', color: '#4ade80', fontSize: '0.68rem' }}>{id.replace(/_/g, ' ')}</span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {submitStatus.debrief.q1_missed?.length > 0 && (
                                                    <div style={{ marginBottom: '0.5rem' }}>
                                                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#fbbf24', marginBottom: '0.25rem' }}>⚠ Should have been in Q1 ({submitStatus.debrief.q1_missed.length})</div>
                                                        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                                                            {submitStatus.debrief.q1_missed.map(id => (
                                                                <span key={id} style={{ padding: '2px 7px', borderRadius: '4px', background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.3)', color: '#fbbf24', fontSize: '0.68rem' }}>{id.replace(/_/g, ' ')}</span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {submitStatus.debrief.clawback_applied > 0 && (
                                                    <div style={{ padding: '0.4rem 0.6rem', background: 'rgba(239,68,68,0.08)', borderRadius: '5px', borderLeft: '2px solid #ef4444', color: '#fca5a5', fontSize: '0.72rem' }}>
                                                        ⚠ ESRS 1 §1.51: CEO-only sign-off (Option C) — ${submitStatus.debrief.clawback_applied?.toLocaleString()} clawback applied. Board committee oversight required.
                                                    </div>
                                                )}
                                            </div>
                                        </details>

                                        {submitStatus.debrief.q2_insight && (
                                            <div style={{ padding: '0.6rem', background: 'rgba(16,185,129,0.08)', borderRadius: '6px', borderLeft: '3px solid #10b981', marginBottom: '0.5rem' }}>
                                                <strong style={{ color: '#34d399' }}>Q2 Impact Disclosure</strong>
                                                <p style={{ color: '#cbd5e1', margin: '0.3rem 0 0' }}>{submitStatus.debrief.q2_insight}</p>
                                            </div>
                                        )}
                                        {submitStatus.debrief.spectrum_note && (
                                            <div style={{ padding: '0.6rem', background: 'rgba(245,158,11,0.08)', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}>
                                                <strong style={{ color: '#fbbf24' }}>⚠ Simulation Simplification</strong>
                                                <p style={{ color: '#cbd5e1', margin: '0.3rem 0 0' }}>{submitStatus.debrief.spectrum_note}</p>
                                            </div>
                                        )}
                                    </div>
                                )}
                                <button onClick={onClose} className={styles.submitBtn} style={{ marginTop: '1rem' }}>Return to Dashboard</button>
                            </>
                        )}
                    </div>
                </div>
            )}

        </div>
    );
}
