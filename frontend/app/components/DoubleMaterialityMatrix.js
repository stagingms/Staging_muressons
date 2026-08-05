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
import { droppableKeyboardCoordinates } from '../lib/dndDroppableKeyboardCoordinates';
import styles from './DoubleMaterialityMatrix.module.css';
import { currencySymbol } from '../utils/format';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/* Counter for custom factors */
let _customFactorCounter = 0;

/**
 * Draggable Issue Chip component — Fix 7 (cost badge), Fix 10 (IRO badge + data-tooltip)
 * Updated: panel group recommendation badges below the cost badge
 */
function IssueChip({ issue, isDragging, isBlindspot = false, isStakeholderBoosted = false, commissionedGroups = [], panelRecommendations = {}, panelGroupConfig = {} }) {
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
            case 'ecological': return <span className={styles.catIcon} style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--kpi-good)', border: '1px solid rgba(16, 185, 129, 0.5)' }}>E</span>;
            case 'social': return <span className={styles.catIcon} style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.5)' }}>S</span>;
            case 'governance': return <span className={styles.catIcon} style={{ background: 'rgba(245, 158, 11, 0.2)', color: 'var(--caution)', border: '1px solid rgba(245, 158, 11, 0.5)' }}>G</span>;
            case 'economic': return <span className={styles.catIcon} style={{ background: 'rgba(245, 158, 11, 0.2)', color: 'var(--caution)', border: '1px solid rgba(245, 158, 11, 0.5)' }}>G</span>;
            default: return null;
        }
    };

    const costDisplay = issue.mitigation_cost_usd > 0
        ? `${currencySymbol()}${(issue.mitigation_cost_usd / 1_000_000).toFixed(1)}M`
        : null;

    const iroType = issue.iro_type || null;

    // ESRS spectrum tags
    const severityColor = { high: 'var(--danger)', medium: 'var(--caution)', low: 'var(--kpi-good)' };
    const horizonLabel = { short: 'ST', medium: 'MT', long: 'LT' };
    const sev = issue.severity;
    const horizon = issue.time_horizon;

    // ── NEW: ESRS topic badge color ──
    const esrsTopicColor = (t) => {
        if (!t) return { bg: 'rgba(148,163,184,0.15)', color: '#94a3b8' };
        if (t.startsWith('E')) return { bg: 'rgba(16,185,129,0.15)', color: 'var(--kpi-good)' };
        if (t.startsWith('S')) return { bg: 'rgba(59,130,246,0.15)', color: '#60a5fa' };
        return { bg: 'rgba(245,158,11,0.15)', color: 'var(--caution)' };
    };
    const vcLabel = { own_ops: '🏭', upstream: '⬆', downstream: '⬇' };
    const esrsTopic = issue.esrs_topic || null;
    const vcScope = issue.value_chain_scope || null;
    const isAmbiguous = !!issue.is_ambiguous;

    // ── Panel recommendation badges ──
    const issueRecs = panelRecommendations[issue.id] || {};
    const commissionedGroupsArray = Array.from(commissionedGroups);
    const hasPanelData = commissionedGroupsArray.length > 0 && Object.keys(issueRecs).length > 0;

    const quadrantLabel = { q1: 'Q1 ↗', q2: 'Q2 ↖', q3: 'Q3 ↘', q4: 'Q4 ↙' };

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
            {/* Panel group recommendation badges — shown after at least one group is commissioned */}
            {hasPanelData && (
                <div className={styles.panelBadgeRow}>
                    {commissionedGroupsArray.map(groupKey => {
                        const rec = issueRecs[groupKey];
                        const cfg = panelGroupConfig[groupKey];
                        if (!rec || !cfg) return null;
                        const emojiMap = { investors: '💰', workers: '👷', ngos: '🌍', experts: '🎓' };
                        return (
                            <span
                                key={groupKey}
                                className={styles.panelGroupBadge}
                                style={{
                                    background: `${cfg.color}18`,
                                    color: cfg.color,
                                    border: `1px solid ${cfg.color}44`,
                                }}
                                title={`${cfg.label} recommends: ${rec.toUpperCase()} — ${cfg.esrs_ref || ''}`}
                            >
                                {emojiMap[groupKey] || '👥'} {quadrantLabel[rec] || rec.toUpperCase()}
                            </span>
                        );
                    })}
                </div>
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
export default function DoubleMaterialityMatrix({ onSubmit, onClose, csfPool = Infinity, initialQ1 = [], globalState = {}, buId = null, buLabel = null, sessionId = null, onOpenAdvisor = null, alreadySubmitted = false }) {
    const [issues, setIssues] = useState([]);
    const [consultantFee, setConsultantFee] = useState(1500000);
    const [loading, setLoading] = useState(true);

    const [activeId, setActiveId] = useState(null);
    const [consultantAllowed, setConsultantAllowed] = useState(true);

    // ── Multi-group panel survey state ────────────────────────────────────────
    // commissionedGroups: Set of group keys that have been commissioned this session
    const [commissionedGroups, setCommissionedGroups] = useState(new Set());
    // Panel data fetched from server alongside issues
    const [panelGroupConfig, setPanelGroupConfig] = useState({});   // { investors: { label, fee_usd, color, ... }, ... }
    const [panelRecommendations, setPanelRecommendations] = useState({}); // { issue_id: { investors: 'q1', ... }, ... }

    // R1 intelligence modulation
    const [blindspotActive, setBlindspotActive] = useState(false);
    const [stakeholderBoostedIds, setStakeholderBoostedIds] = useState([]);

    // Onboarding state
    // LOOP FIX (2026-07-31): the intro used to be a plain useState(true), so
    // ANY remount of this component — paradigm churn, r2 selection churn, a
    // dashboard refresh racing the open panel — replayed the full onboarding
    // over a wiped board: the "matrix loops again" report. The CFO-override
    // flow keeps the player inside the panel longest (submit → memo → decide),
    // which is why the loop hit "especially" there. Dismissal is now latched
    // per session in localStorage, and a session that has ALREADY submitted
    // never sees the intro at all.
    const [showOnboarding, setShowOnboarding] = useState(() => {
        if (alreadySubmitted) return false;
        try { return localStorage.getItem(`mur_dmm_intro_${sessionId || 'solo'}`) !== '1'; }
        catch { return true; }
    });
    const dismissOnboarding = () => {
        setShowOnboarding(false);
        try { localStorage.setItem(`mur_dmm_intro_${sessionId || 'solo'}`, '1'); } catch { /* private mode */ }
    };

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

    // 4-tab stakeholder group tab selector (for commission modal preview)
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

    // FREEZE the BU for the lifetime of this mount. The config fetch below
    // REBUILDS every quadrant, so if buId changed mid-exercise the player's
    // placed issues would silently vanish and the assessment would restart —
    // the "matrix repeats a second time" report. The parent already holds the
    // mount until the paradigm and BU are settled; this makes the guarantee
    // local, so no future prop churn can reset an exercise in progress.
    // Swapping BU mid-assessment is not a real workflow: the modal is closed
    // and reopened for that, which remounts and re-reads the prop.
    const frozenBuIdRef = useRef(buId);
    const effectiveBuId = frozenBuIdRef.current;

    useEffect(() => {
        const fetchConfig = async () => {
            try {
                // session_id makes the BU view resolve through the SAME chain
                // the submit endpoint scores against (cohort override → pack →
                // region → BU) — the player must see the dictionary they will
                // be graded on, not the raw BU file.
                const _sq = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
                const endpoint = effectiveBuId
                    ? `${API}/api/admin/materiality-config/bu/${effectiveBuId}${_sq}`
                    : `${API}/api/admin/materiality-config`;
                const res = await fetch(endpoint);
                if (res.ok) {
                    const data = await res.json();
                    setIssues(data.issues || []);
                    setConsultantFee(data.consultant_fee_usd || 1500000);
                    // ── Load panel group config + recommendations from server ──
                    if (data.panel_group_config) setPanelGroupConfig(data.panel_group_config);
                    if (data.panel_recommendations) setPanelRecommendations(data.panel_recommendations);
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
    }, [effectiveBuId]);

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
        // A11Y-F20 (WCAG 2.1.1): snap between zones instead of dnd-kit's
        // default 25px-per-press nudge, which made this gate take ~200 key
        // presses to complete. See lib/dndDroppableKeyboardCoordinates.js.
        useSensor(KeyboardSensor, { coordinateGetter: droppableKeyboardCoordinates })
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

    // ── Commission a specific panel group (idempotent per group) ──
    const handleCommissionGroup = (groupKey) => {
        if (commissionedGroups.has(groupKey)) return; // already commissioned
        setCommissionedGroups(prev => {
            const next = new Set(prev);
            next.add(groupKey);
            return next;
        });
        // Show cheat sheet on first commission
        if (commissionedGroups.size === 0) setShowCheatSheet(true);
    };

    const handleSubmit = async (forceOverride = false) => {
        if (!onSubmit) return;
        // A committed submission is final for the round. The server replays the
        // committed result on a duplicate POST anyway (idempotency guard), but
        // the CLIENT must not walk the player through review→override again —
        // that walk WAS the loop.
        if (alreadySubmitted) {
            setSubmitStatus({
                type: 'error', overridable: false,
                message: 'Your materiality matrix for this round is already with the CFO — no resubmission is needed. Close this panel to continue.',
            });
            return;
        }
        setIsSubmitting(true);
        const result = await onSubmit({
            consultant_used: commissionedGroups.size > 0,
            panel_groups_commissioned: Array.from(commissionedGroups),
            total_panel_fee: totalPanelFee,
            matrix_submission: {
                quadrant_1_top_right: containers.q1,
                quadrant_2_top_left: containers.q2,
                quadrant_3_bottom_right: containers.q3,
                quadrant_4_bottom_left: containers.q4,
            },
            force_override_cfo: forceOverride === true,
            // MUST be the frozen id: the submission is scored against the
            // dictionary the player actually saw, and the server's idempotency
            // key includes bu_id — a mismatch would score the wrong issue set
            // AND defeat double-submit protection.
            bu_id: effectiveBuId || undefined,
        });

        if (result && result.error) {
            // Only the CFO materiality gate (a 400) is overridable. A generic
            // failure (500/network/etc.) must NOT show "Force Override", whose
            // re-submit of the identical payload is what looped the exercise.
            setSubmitStatus({ type: 'error', message: result.error, overridable: result.overridable === true });
            setIsSubmitting(false);
        } else if (result && result.success) {
            setSubmitStatus({ type: 'success', amount: result.allocated_budget, debrief: result.debrief });
            setIsSubmitting(false);
        }
    };

    // ── Panel fee calculations ──────────────────────────────────────────────
    // Sum flat fees for every commissioned group
    const totalPanelFee = Array.from(commissionedGroups).reduce((sum, gKey) => {
        const cfg = panelGroupConfig[gKey];
        return sum + (cfg ? cfg.fee_usd : 750_000);
    }, 0);

    // Net CSF after deducting panel fees (live preview during matrix session)
    const netCsf = Math.max(0, csfPool - totalPanelFee);

    const placedCount = containers.q1.length + containers.q2.length + containers.q3.length + containers.q4.length;
    const MIN_PLACED = 6;
    const hasEnoughPlaced = placedCount >= MIN_PLACED;

    const totalQ1Cost = containers.q1.reduce((sum, id) => {
        const issue = getIssue(id);
        const finalCost = issue ? issue.mitigation_cost_usd : 0;
        return sum + finalCost;
    }, 0);
    const isOverBudget = totalQ1Cost > netCsf;

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
            return <IssueChip
                key={id}
                issue={{ ...issue, mitigation_cost_usd: cost }}
                isDragging={activeId === id}
                isBlindspot={isBlindspot}
                isStakeholderBoosted={isBoosted}
                commissionedGroups={commissionedGroups}
                panelRecommendations={panelRecommendations}
                panelGroupConfig={panelGroupConfig}
            />;
        });
    };

    if (loading) return <div className={styles.overlay}><div className={styles.header}><h2 style={{ color: 'white' }}>Loading Materiality Dictionary...</h2></div></div>;

    return (
        <div className={styles.overlay}>
            {/* Fix 1: Onboarding */}
            {showOnboarding && <OnboardingOverlay onDismiss={dismissOnboarding} />}

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

                    {/* Panel fee live deduction display */}
                    {totalPanelFee > 0 && (
                        <div className={styles.panelFeeBar}>
                            <span className={styles.panelFeeLabel}>Panel Fees</span>
                            <span className={styles.panelFeeAmount}>−{currencySymbol()}{(totalPanelFee / 1_000_000).toFixed(2)}M</span>
                            <span className={styles.netCsfAmount}>Net CSF: {currencySymbol()}{(netCsf / 1_000_000).toFixed(1)}M</span>
                        </div>
                    )}

                    {/* Commission Stakeholder Panel Survey button */}
                    {commissionedGroups.size < 4 && consultantAllowed && (
                        <button
                            className={styles.consultantBtn}
                            onClick={() => setShowConsultantConfirm(true)}
                            data-tooltip="Engage independent stakeholder panels to get per-issue quadrant recommendations (ESRS 1 §1.47-1.50)"
                        >
                            👥 Commission Stakeholder Panel ({commissionedGroups.size}/4 groups)
                        </button>
                    )}
                    {commissionedGroups.size === 0 && !consultantAllowed && (
                        <button
                            className={styles.advisorPromptBtn}
                            onClick={() => { if (onOpenAdvisor) { onOpenAdvisor(); } }}
                        >
                            🧠 Need Help? Ask the AI Advisor
                        </button>
                    )}
                    {commissionedGroups.size === 4 && (
                        <span className={styles.consultantBadge}>👥 All 4 Panels Commissioned</span>
                    )}
                    {commissionedGroups.size > 0 && commissionedGroups.size < 4 && (
                        <span className={styles.consultantBadge} style={{ background: 'rgba(99,102,241,0.1)', borderColor: 'rgba(99,102,241,0.3)', color: '#818cf8' }}>
                            👥 {commissionedGroups.size} Panel{commissionedGroups.size > 1 ? 's' : ''} Active
                        </span>
                    )}
                    {blindspotActive && (
                        <span className={styles.blindspotWarning} title="R1 Surface Scan left gaps — some issue descriptions are degraded">
                            ⚠️ R1 Audit Gap Active
                        </span>
                    )}
                    <div style={{ padding: '0 0.75rem', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center', minWidth: '140px' }}>
                        <span style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#94a3b8', fontWeight: 700 }}>Placed</span>
                        <span style={{ fontWeight: 700, fontSize: '0.9rem', color: hasEnoughPlaced ? 'var(--positive-text)' : 'var(--caution)' }}>
                            {placedCount} / {issues.length} issues
                        </span>
                        {/* CL-4: Visual completion bar */}
                        <div style={{ width: '100%', height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, marginTop: 3, overflow: 'hidden' }}>
                            <div style={{
                                height: '100%', borderRadius: 2,
                                width: `${Math.min(100, (placedCount / Math.max(1, issues.length)) * 100)}%`,
                                background: hasEnoughPlaced ? 'var(--positive-text)' : 'var(--caution)',
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
                            color: isOverBudget ? 'var(--danger)' : totalQ1Cost > 0 ? 'var(--caution)' : 'var(--positive-text)',
                            transition: 'color 0.3s ease',
                        }}>
                            {currencySymbol()}{(totalQ1Cost / 1_000_000).toFixed(1)}M / {currencySymbol()}{(netCsf / 1_000_000).toFixed(1)}M
                        </span>
                    </div>
                    <button
                        className={styles.submitBtn}
                        disabled={alreadySubmitted || isSubmitting || isOverBudget || !hasEnoughPlaced}
                        onClick={() => handleSubmit(false)}
                        data-tooltip={alreadySubmitted ? "Your matrix for this round is already committed with the CFO." : !hasEnoughPlaced ? `Place at least ${MIN_PLACED} issues into quadrants before submitting.` : isOverBudget ? "Your Quadrant 1 CapEx exceeds the total CSF pool balance." : "Submit your materiality assessment for CFO review."}
                    >
                        {alreadySubmitted ? '✅ Submitted — CFO has your matrix' : isSubmitting ? 'Submitting...' : !hasEnoughPlaced ? `Place ${MIN_PLACED - placedCount} More Issues` : 'Submit Matrix to CFO'}
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

                {/* Committed Groups bar — shown below Issue Bank header when groups commissioned */}
                    {commissionedGroups.size > 0 && (
                        <div className={styles.commissionedGroupsBar}>
                            <span style={{ fontSize: '0.6rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginRight: '0.15rem', flexShrink: 0 }}>Panels:</span>
                            {Array.from(commissionedGroups).map(gKey => {
                                const cfg = panelGroupConfig[gKey];
                                if (!cfg) return null;
                                return (
                                    <span key={gKey} className={styles.commissionedGroupsBadge}
                                        style={{ background: `${cfg.color}18`, color: cfg.color, border: `1px solid ${cfg.color}33` }}
                                        title={`${cfg.label} — ${cfg.esrs_ref || ''} — Fee: ${currencySymbol()}${((cfg.fee_usd || 750000) / 1_000_000).toFixed(2)}M`}
                                    >
                                        {cfg.label} ✓
                                    </span>
                                );
                            })}
                        </div>
                    )}

                    {/* Category Legend */}
                    <div className={styles.legend}>
                            <span className={styles.legendItem}>
                                <span className={styles.catIcon} style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--kpi-good)', border: '1px solid rgba(16, 185, 129, 0.5)', width: 18, height: 18, fontSize: '0.6rem' }}>E</span>
                                Ecological
                            </span>
                            <span className={styles.legendItem}>
                                <span className={styles.catIcon} style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.5)', width: 18, height: 18, fontSize: '0.6rem' }}>S</span>
                                Social
                            </span>
                            <span className={styles.legendItem}>
                                <span className={styles.catIcon} style={{ background: 'rgba(245, 158, 11, 0.2)', color: 'var(--caution)', border: '1px solid rgba(245, 158, 11, 0.5)', width: 18, height: 18, fontSize: '0.6rem' }}>G</span>
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
                            {[['all', 'All', '#6366f1'], ['short', 'ST ≤1yr', 'var(--danger)'], ['medium', 'MT 1-5yr', 'var(--caution)'], ['long', 'LT >5yr', 'var(--kpi-good)']].map(([val, label, color]) => (
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

            {/* Stakeholder Panel Survey — Per-Group Commission Modal (ESRS §1.47-1.50) */}
            {showConsultantConfirm && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modalContent} style={{ maxWidth: 520, textAlign: 'left' }}>
                        <h3 style={{ textAlign: 'center' }}>👥 Commission Stakeholder Panel Survey</h3>
                        <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginBottom: '0.75rem', textAlign: 'center' }}>
                            Each ESRS §1.47 stakeholder group can be commissioned once. Their ratings appear as
                            badges on every issue chip. Fees are deducted from your CSF on final submission.
                        </p>

                        {/* Group selector tabs */}
                        <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                            {Object.entries(
                                Object.keys(panelGroupConfig).length > 0
                                    ? panelGroupConfig
                                    : {
                                        investors: { label: '💰 Investors', color: '#6366f1' },
                                        workers:   { label: '👷 Own Workforce', color: '#3b82f6' },
                                        ngos:      { label: '🌍 NGOs / Communities', color: 'var(--kpi-good)' },
                                        experts:   { label: '🎓 Subject Matter Experts', color: 'var(--caution)' },
                                    }
                            ).map(([gKey, gCfg]) => (
                                <button key={gKey} onClick={() => setActivePanelGroup(gKey)}
                                    style={{
                                        padding: '0.3rem 0.7rem', borderRadius: '6px', cursor: 'pointer',
                                        border: `1px solid ${activePanelGroup === gKey ? gCfg.color : 'rgba(255,255,255,0.1)'}`,
                                        background: activePanelGroup === gKey ? `${gCfg.color}22` : 'rgba(255,255,255,0.03)',
                                        color: activePanelGroup === gKey ? gCfg.color : commissionedGroups.has(gKey) ? 'var(--positive-text)' : '#94a3b8',
                                        fontSize: '0.72rem', fontWeight: 700,
                                        transition: 'background 0.15s, color 0.15s, border-color 0.15s',
                                        position: 'relative',
                                    }}>
                                    {gCfg.label} {commissionedGroups.has(gKey) ? '✓' : ''}
                                </button>
                            ))}
                        </div>

                        {/* Active group details */}
                        {(() => {
                            const cfg = panelGroupConfig[activePanelGroup] || {
                                label: activePanelGroup,
                                description: '',
                                esrs_ref: '',
                                fee_usd: 750_000,
                                color: '#6366f1',
                            };
                            const isCommissioned = commissionedGroups.has(activePanelGroup);
                            return (
                                <>
                                    <div style={{ padding: '0.6rem 0.8rem', background: `${cfg.color}10`, borderRadius: '8px', borderLeft: `3px solid ${cfg.color}`, marginBottom: '0.75rem' }}>
                                        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: cfg.color, marginBottom: '0.25rem' }}>{cfg.esrs_ref || 'ESRS §1.47'}</div>
                                        <div style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: 1.55 }}>{cfg.description || 'Engage this stakeholder group to receive per-issue quadrant recommendations.'}</div>
                                        <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                                            Fee: <strong style={{ color: cfg.color }}>{currencySymbol()}{((cfg.fee_usd || 750_000) / 1_000_000).toFixed(2)}M</strong> (flat rate — all issues rated)
                                        </div>
                                    </div>

                                    {/* Commission button for this group */}
                                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.75rem' }}>
                                        {isCommissioned ? (
                                            <span style={{ padding: '0.45rem 1.2rem', borderRadius: '6px', background: 'rgba(74,222,128,0.1)', color: 'var(--positive-text)', border: '1px solid rgba(74,222,128,0.3)', fontWeight: 700, fontSize: '0.82rem' }}>
                                                ✓ {cfg.label} Commissioned
                                            </span>
                                        ) : (
                                            <button
                                                className={styles.submitBtn}
                                                onClick={() => handleCommissionGroup(activePanelGroup)}
                                            >
                                                Commission {cfg.label} — {currencySymbol()}{((cfg.fee_usd || 750_000) / 1_000_000).toFixed(2)}M
                                            </button>
                                        )}
                                    </div>
                                </>
                            );
                        })()}

                        {/* Accumulated fee summary */}
                        {totalPanelFee > 0 && (
                            <div style={{ padding: '0.5rem 0.75rem', background: 'rgba(245,158,11,0.06)', borderRadius: '6px', border: '1px solid rgba(245,158,11,0.15)', marginBottom: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{commissionedGroups.size} group{commissionedGroups.size !== 1 ? 's' : ''} commissioned</span>
                                <span style={{ fontWeight: 700, color: 'var(--caution)', fontSize: '0.82rem' }}>Total: −{currencySymbol()}{(totalPanelFee / 1_000_000).toFixed(2)}M from CSF</span>
                            </div>
                        )}

                        <p style={{ fontSize: '0.7rem', color: '#475569', textAlign: 'center', margin: '0 0 0.5rem' }}>
                            ESRS §1.50: Commissioning multiple groups surfaces conflicting stakeholder perspectives — a key learning outcome.
                        </p>
                        <div className={styles.modalActions}>
                            <button onClick={() => setShowConsultantConfirm(false)} className={styles.cancelBtn}>Close</button>
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
                                {/* The CFO "Force Override" affordance appears ONLY for the
                                    materiality gate (a 400 rejecting non-material Q1 issues).
                                    For any other failure the override is hidden — re-submitting
                                    the identical payload is what looped the exercise. */}
                                <h3>{submitStatus.overridable ? '📝 Memo from CFO' : '⚠️ Submission Error'}</h3>
                                <p className={styles.errorText}>{submitStatus.message}</p>
                                <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', justifyContent: 'center' }}>
                                    <button onClick={() => setSubmitStatus(null)} className={styles.cancelBtn} style={{ flex: 1 }}>Fix Matrix</button>
                                    {submitStatus.overridable ? (
                                        <button
                                            onClick={() => handleSubmit(true)}
                                            className={styles.submitBtn}
                                            style={{ flex: 1, background: 'var(--danger)', borderColor: 'var(--danger)', color: 'white' }}
                                            data-tooltip="Warning: Overriding the CFO may negatively impact your reputation score. Have you considered the long-term ESG implications?"
                                        >
                                            Force Override
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => { setSubmitStatus(null); handleSubmit(false); }}
                                            className={styles.submitBtn}
                                            style={{ flex: 1 }}
                                            data-tooltip="Re-submit your current matrix."
                                        >
                                            Try Again
                                        </button>
                                    )}
                                </div>
                            </>
                        ) : (
                            <>
                                <h3>✅ Materiality Matrix Approved</h3>
                                <div 
                                    className={styles.budgetBox}
                                    title={submitStatus.debrief ? [
                                        `Calculated as:`,
                                        `Total Materiality Budget ($15,000,000) × ${submitStatus.debrief.full_accuracy_pct}% Accuracy`,
                                        submitStatus.debrief.panel_fee_paid > 0
                                            ? `Minus Panel Survey Fees (${currencySymbol()}${(submitStatus.debrief.panel_fee_paid || 0).toLocaleString()}) — ${(submitStatus.debrief.panel_groups_commissioned || []).join(', ')}`
                                            : null,
                                        submitStatus.debrief.clawback_applied > 0
                                            ? `Minus Governance Penalty / Clawback (${currencySymbol()}${submitStatus.debrief.clawback_applied.toLocaleString()})`
                                            : null,
                                        `= ${currencySymbol()}${submitStatus.amount?.toLocaleString()} Final Unlocked Budget`,
                                    ].filter(Boolean).join('\n') : `Allocated Budget: ${currencySymbol()}${submitStatus.amount?.toLocaleString()}`}
                                >
                                    + {currencySymbol()}{submitStatus.amount?.toLocaleString()} Unlocked
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
                                                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--positive-text)', marginBottom: '0.25rem' }}>✅ Correctly in Q1 ({submitStatus.debrief.q1_correct.length})</div>
                                                        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                                                            {submitStatus.debrief.q1_correct.map(id => (
                                                                <span key={id} style={{ padding: '2px 7px', borderRadius: '4px', background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.3)', color: 'var(--positive-text)', fontSize: '0.68rem' }}>{id.replace(/_/g, ' ')}</span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {submitStatus.debrief.q1_missed?.length > 0 && (
                                                    <div style={{ marginBottom: '0.5rem' }}>
                                                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--caution-text)', marginBottom: '0.25rem' }}>⚠ Should have been in Q1 ({submitStatus.debrief.q1_missed.length})</div>
                                                        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                                                            {submitStatus.debrief.q1_missed.map(id => (
                                                                <span key={id} style={{ padding: '2px 7px', borderRadius: '4px', background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.3)', color: 'var(--caution-text)', fontSize: '0.68rem' }}>{id.replace(/_/g, ' ')}</span>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {submitStatus.debrief.clawback_applied > 0 && (
                                                    <div style={{ padding: '0.4rem 0.6rem', background: 'rgba(239,68,68,0.08)', borderRadius: '5px', borderLeft: '2px solid var(--danger)', color: '#fca5a5', fontSize: '0.72rem' }}>
                                                        ⚠ ESRS 1 §1.51: CEO-only sign-off (Option C) — {currencySymbol()}{submitStatus.debrief.clawback_applied?.toLocaleString()} clawback applied. Board committee oversight required.
                                                    </div>
                                                )}
                                            </div>
                                        </details>

                                        {submitStatus.debrief.q2_insight && (
                                            <div style={{ padding: '0.6rem', background: 'rgba(16,185,129,0.08)', borderRadius: '6px', borderLeft: '3px solid var(--kpi-good)', marginBottom: '0.5rem' }}>
                                                <strong style={{ color: '#34d399' }}>Q2 Impact Disclosure</strong>
                                                <p style={{ color: '#cbd5e1', margin: '0.3rem 0 0' }}>{submitStatus.debrief.q2_insight}</p>
                                            </div>
                                        )}
                                        {submitStatus.debrief.spectrum_note && (
                                            <div style={{ padding: '0.6rem', background: 'rgba(245,158,11,0.08)', borderRadius: '6px', borderLeft: '3px solid var(--caution)' }}>
                                                <strong style={{ color: 'var(--caution-text)' }}>⚠ Simulation Simplification</strong>
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
