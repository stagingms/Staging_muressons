/**
 * ConsequenceTimeline.js — Flag Dependency Visualizer (PHASE-3)
 * Horizontal SVG timeline showing causal links between past decisions
 * and future consequences. Uses FLAG_DEPENDENCY_GRAPH from terminal_valuation.
 */
import React, { useMemo } from 'react';
import styles from './ConsequenceTimeline.module.css';

const CATEGORY_COLORS = {
  governance: { bg: 'rgba(139, 92, 246, 0.2)', stroke: '#8b5cf6', dot: '#8b5cf6' },
  climate: { bg: 'rgba(16, 185, 129, 0.2)', stroke: '#10b981', dot: '#10b981' },
  risk: { bg: 'rgba(239, 68, 68, 0.2)', stroke: '#ef4444', dot: '#ef4444' },
  social: { bg: 'rgba(59, 130, 246, 0.2)', stroke: '#3b82f6', dot: '#3b82f6' },
  supply_chain: { bg: 'rgba(245, 158, 11, 0.2)', stroke: '#f59e0b', dot: '#f59e0b' },
  strategic: { bg: 'rgba(99, 102, 241, 0.2)', stroke: '#6366f1', dot: '#6366f1' },
};

const FLAG_DEPENDENCY_GRAPH = [
  { source_round: 1, flag: 'deep_audit_completed', target_round: 4, effect: 'Halves crisis severity', category: 'governance', label: 'Deep Audit' },
  { source_round: 1, flag: 'electronics_blindspot', target_round: 4, effect: 'Doubles crisis severity', category: 'risk', label: 'Blind Spot' },
  { source_round: 2, flag: 'materiality_aligned', target_round: 10, effect: '+0.10 M_R bonus', category: 'governance', label: 'Materiality' },
  { source_round: 2, flag: 'materiality_partial', target_round: 10, effect: '+0.05 M_R bonus (partial)', category: 'governance', label: 'Materiality (partial)' },
  { source_round: 2, flag: 'blockchain_traceability', target_round: 8, effect: 'Prevents supply scandal', category: 'supply_chain', label: 'Blockchain' },
  { source_round: 3, flag: 'early_decarboniser', target_round: 7, effect: '+0.10 synergy bonus', category: 'climate', label: 'Decarboniser' },
  { source_round: 3, flag: 'greenwash_risk', target_round: 5, effect: 'Triggers greenwash penalty', category: 'risk', label: 'Greenwash' },
  { source_round: 5, flag: 'insurance_only', target_round: 10, effect: 'Blocks +0.20 M_R', category: 'climate', label: 'Insurance' },
  { source_round: 6, flag: 'ethical_ai_overhaul', target_round: 10, effect: '+0.15 Truth Premium', category: 'governance', label: 'AI Ethics' },
  { source_round: 6, flag: 'ai_monetised', target_round: 7, effect: 'EU AI Act costs', category: 'risk', label: 'AI Revenue' },
  { source_round: 7, flag: 'synergy_unlock', target_round: 10, effect: '+0.30 Synergy M_R', category: 'strategic', label: 'Synergy' },
  { source_round: 9, flag: 'community_fund', target_round: 10, effect: '+0.18 Community M_R', category: 'social', label: 'Community' },
  { source_round: 9, flag: 'managed_transition', target_round: 10, effect: '+0.12 Just Trans. M_R', category: 'social', label: 'Transition' },
];

export default function ConsequenceTimeline({ currentRound = 1, activeFlags = {}, foreshadowingSignals = [] }) {
  const allFlags = useMemo(() => {
    const s = new Set();
    if (activeFlags && typeof activeFlags === 'object') {
      Object.entries(activeFlags).forEach(([key, val]) => {
        // Flags stored as arrays under keys like r1_flags, r3_flags, etc.
        if (Array.isArray(val)) {
          val.forEach(f => { if (typeof f === 'string') s.add(f); });
        }
        // Boolean flags stored directly (e.g., deep_audit_completed: true)
        else if (val === true && typeof key === 'string') {
          s.add(key);
        }
        // String-valued flags (e.g., ending_pathway: "climate_black_swan")
        else if (typeof val === 'string' && typeof key === 'string') {
          s.add(key);
        }
      });
    }
    return s;
  }, [activeFlags]);

  const deps = useMemo(() =>
    FLAG_DEPENDENCY_GRAPH.map(d => ({
      ...d,
      status: allFlags.has(d.flag) ? 'active' : 'inactive',
      isPositive: !['risk'].includes(d.category) || d.flag === 'deep_audit_completed',
    })),
  [allFlags]);

  const SVG_W = 900;
  const SVG_H = 220;
  const TIMELINE_Y = 100;
  const PAD_X = 50;
  const ROUND_SPACING = (SVG_W - PAD_X * 2) / 9;

  const roundX = (r) => PAD_X + (r - 1) * ROUND_SPACING;

  return (
    <div className={styles.timelineContainer} id="consequence-timeline">
      <div className={styles.timelineHeader}>
        <h3 className={styles.timelineTitle}>🔗 Decision Consequence Map</h3>
        <div className={styles.legendRow}>
          {Object.entries(CATEGORY_COLORS).map(([cat, c]) => (
            <span key={cat} className={styles.legendItem}>
              <span className={styles.legendDot} style={{ background: c.dot }} />
              {cat.replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>

      <div className={styles.svgWrapper}>
        <svg viewBox={`0 0 ${SVG_W} ${SVG_H}`} className={styles.timelineSvg}>
          <defs>
            {Object.entries(CATEGORY_COLORS).map(([cat, c]) => (
              <linearGradient key={cat} id={`grad-${cat}`} x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={c.stroke} stopOpacity="0.8" />
                <stop offset="100%" stopColor={c.stroke} stopOpacity="0.3" />
              </linearGradient>
            ))}
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* Timeline axis */}
          <line x1={PAD_X} y1={TIMELINE_Y} x2={SVG_W - PAD_X} y2={TIMELINE_Y}
            stroke="rgba(148,163,184,0.3)" strokeWidth="2" />

          {/* Round markers */}
          {Array.from({ length: 10 }, (_, i) => i + 1).map(r => {
            const x = roundX(r);
            const isCurrent = r === currentRound;
            const isPast = r < currentRound;
            return (
              <g key={r}>
                <circle cx={x} cy={TIMELINE_Y} r={isCurrent ? 14 : 10}
                  fill={isCurrent ? 'rgba(99,102,241,0.3)' : isPast ? 'rgba(148,163,184,0.15)' : 'rgba(148,163,184,0.08)'}
                  stroke={isCurrent ? '#6366f1' : isPast ? 'rgba(148,163,184,0.4)' : 'rgba(148,163,184,0.2)'}
                  strokeWidth={isCurrent ? 2 : 1}
                  filter={isCurrent ? 'url(#glow)' : undefined}
                />
                <text x={x} y={TIMELINE_Y + 4} textAnchor="middle" fill={isCurrent ? '#e2e8f0' : '#94a3b8'}
                  fontSize={isCurrent ? '12' : '10'} fontWeight={isCurrent ? '700' : '400'}
                  fontFamily="Inter, sans-serif">
                  {r}
                </text>
                <text x={x} y={TIMELINE_Y + 28} textAnchor="middle" fill="rgba(148,163,184,0.5)"
                  fontSize="8" fontFamily="Inter, sans-serif">
                  R{r}
                </text>
              </g>
            );
          })}

          {/* Dependency arcs */}
          {deps.map((dep, i) => {
            const sx = roundX(dep.source_round);
            const tx = roundX(dep.target_round);
            const isActive = dep.status === 'active';
            const colors = CATEGORY_COLORS[dep.category] || CATEGORY_COLORS.governance;
            const arcHeight = 30 + (i % 4) * 18;
            const isAbove = i % 2 === 0;
            const cy = isAbove ? TIMELINE_Y - arcHeight : TIMELINE_Y + arcHeight + 20;
            const my = isAbove ? TIMELINE_Y - arcHeight - 10 : TIMELINE_Y + arcHeight + 30;

            return (
              <g key={`${dep.flag}-${i}`} opacity={1}>
                {/* Arc path */}
                <path
                  d={`M ${sx} ${TIMELINE_Y} Q ${(sx + tx) / 2} ${my} ${tx} ${TIMELINE_Y}`}
                  fill="none"
                  stroke={colors.stroke}
                  strokeWidth={isActive ? 2 : 1.5}
                  strokeDasharray={isActive ? 'none' : '4 4'}
                  className={isActive ? styles.activeArc : ''}
                  opacity={isActive ? 1 : 0.35}
                />
                {/* Source dot */}
                <circle cx={sx} cy={TIMELINE_Y} r={4}
                  fill={colors.dot} opacity={isActive ? 1 : 0.35} />
                {/* Target dot */}
                <circle cx={tx} cy={TIMELINE_Y} r={4}
                  fill={colors.dot} opacity={isActive ? 1 : 0.35} />
                {/* Label */}
                <text x={(sx + tx) / 2} y={my + (isAbove ? -4 : 12)}
                  textAnchor="middle" fontSize="10"
                  fill={colors.stroke}
                  fontFamily="Inter, sans-serif" fontWeight={isActive ? '800' : '500'}
                  opacity={isActive ? 1 : 0.85}>
                  {dep.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Foreshadowing signals */}
      {foreshadowingSignals && foreshadowingSignals.length > 0 && (
        <div className={styles.signalsContainer}>
          {foreshadowingSignals.map((sig, i) => (
            <div key={i} className={`${styles.signal} ${styles[`signal_${sig.category}`]}`}>
              {sig.message}
            </div>
          ))}
        </div>
      )}

      {/* Active dependency summary */}
      <div className={styles.summaryRow}>
        <span className={styles.summaryLabel}>Active Links:</span>
        <span className={styles.summaryValue}>
          {deps.filter(d => d.status === 'active').length} / {deps.length}
        </span>
        <span className={styles.summaryLabel}>Positive:</span>
        <span className={styles.summaryValueGreen}>
          {deps.filter(d => d.status === 'active' && d.isPositive).length}
        </span>
        <span className={styles.summaryLabel}>Risk:</span>
        <span className={styles.summaryValueRed}>
          {deps.filter(d => d.status === 'active' && !d.isPositive).length}
        </span>
      </div>
    </div>
  );
}
