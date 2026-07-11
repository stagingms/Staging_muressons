/**
 * LivingPlanet — WOW-7
 *
 * An ambient CSS/SVG ESG state visualization that maps key metrics to
 * visual properties. A central orb changes colour based on composite
 * ESG health, with orbital rings representing Carbon Intensity, SLO,
 * NCD, and Reputation.
 *
 * SAFETY: Pure presentation component. Reads KPIs from globalState and
 * businessUnits props. No engine, flow, or backend changes. Renders
 * nothing if data is missing. Respects prefers-reduced-motion.
 *
 * Performance: CSS conic-gradient + SVG paths only. No Three.js or WebGL.
 * Confirmed viable on i5+ hardware.
 *
 * Props:
 *   globalState   — current game state
 *   businessUnits — array of BU state objects
 *   compact       — if true, renders smaller for inline use
 */
'use client';
import React, { useMemo, useEffect, useState } from 'react';
import styles from './LivingPlanet.module.css';

/** Compute composite ESG score from game state (0-100 scale) */
function computeESGHealth(gs, bus) {
  if (!gs) return { score: 50, label: 'Unknown', color: '#64748b' };

  const rep = gs.group_reputation ?? 50;
  const treasury = gs.corporate_treasury ?? 0;
  const treasuryHealth = Math.min(100, Math.max(0, (treasury / 100_000_000) * 100));

  // Carbon Intensity — lower is better, normalize to 0-100 score
  const ci = gs.tco2e_emissions ?? 50000;
  const ciScore = Math.min(100, Math.max(0, 100 - (ci / 100000) * 100));

  // NCD — lower is better
  const ncd = gs.natural_capital_debt ?? 50;
  const ncdScore = Math.max(0, 100 - ncd);

  // Avg SLO from BUs
  const avgSLO = bus?.length > 0
    ? bus.reduce((sum, bu) => sum + (bu.social_license_score ?? 50), 0) / bus.length
    : 50;

  // Weighted composite
  const score = Math.round(
    rep * 0.25 +
    ciScore * 0.20 +
    ncdScore * 0.20 +
    avgSLO * 0.20 +
    treasuryHealth * 0.15
  );

  let label, color;
  if (score >= 75) { label = 'Thriving'; color = '#10b981'; }
  else if (score >= 55) { label = 'Stable'; color = '#3b82f6'; }
  else if (score >= 35) { label = 'Stressed'; color = '#f59e0b'; }
  else { label = 'Critical'; color = '#ef4444'; }

  return { score, label, color };
}

/** Normalize a metric to 0-1 for ring rendering */
function normalize(value, min, max) {
  return Math.min(1, Math.max(0, (value - min) / (max - min)));
}

export default function LivingPlanet({ globalState, businessUnits, compact = false }) {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReduced(mq.matches);
    const h = (e) => setPrefersReduced(e.matches);
    mq.addEventListener?.('change', h);
    return () => mq.removeEventListener?.('change', h);
  }, []);

  const gs = globalState || {};
  const bus = businessUnits || [];

  const health = useMemo(() => computeESGHealth(gs, bus), [gs, bus]);

  // Metric rings
  const metrics = useMemo(() => {
    const rep = gs.group_reputation ?? 50;
    const ci = gs.tco2e_emissions ?? 50000;
    const ncd = gs.natural_capital_debt ?? 50;
    const avgSLO = bus.length > 0
      ? bus.reduce((s, bu) => s + (bu.social_license_score ?? 50), 0) / bus.length
      : 50;

    return [
      {
        id: 'reputation',
        label: 'Reputation',
        value: rep,
        displayValue: `${rep.toFixed(0)}/100`,
        fill: normalize(rep, 0, 100),
        color: rep >= 60 ? '#10b981' : rep >= 40 ? '#f59e0b' : '#ef4444',
      },
      {
        id: 'carbon',
        label: 'Carbon',
        value: ci,
        displayValue: `${(ci / 1000).toFixed(0)}k tCO₂`,
        fill: normalize(100000 - ci, 0, 100000), // inverted — lower emissions = more fill
        color: ci <= 30000 ? '#10b981' : ci <= 60000 ? '#f59e0b' : '#ef4444',
      },
      {
        id: 'ncd',
        label: 'Nature',
        value: ncd,
        displayValue: `NCD: ${ncd.toFixed(0)}`,
        fill: normalize(100 - ncd, 0, 100), // inverted — lower NCD = more fill
        color: ncd <= 30 ? '#10b981' : ncd <= 60 ? '#f59e0b' : '#ef4444',
      },
      {
        id: 'slo',
        label: 'Social',
        value: avgSLO,
        displayValue: `SLO: ${avgSLO.toFixed(0)}`,
        fill: normalize(avgSLO, 0, 100),
        color: avgSLO >= 60 ? '#10b981' : avgSLO >= 40 ? '#f59e0b' : '#ef4444',
      },
    ];
  }, [gs, bus]);

  // If reduced motion, just show flat metric cards
  if (prefersReduced) {
    return (
      <div className={`${styles.container} ${compact ? styles.compact : ''}`}>
        <div className={styles.flatHeader}>
          <span style={{ color: health.color }}>●</span> ESG Health: {health.label} ({health.score}/100)
        </div>
        <div className={styles.flatGrid}>
          {metrics.map(m => (
            <div key={m.id} className={styles.flatCard}>
              <span className={styles.flatLabel}>{m.label}</span>
              <span className={styles.flatValue} style={{ color: m.color }}>{m.displayValue}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const size = compact ? 140 : 180;
  const center = size / 2;
  const coreRadius = compact ? 32 : 42;

  return (
    <div className={`${styles.container} ${compact ? styles.compact : ''}`}>
      <div className={styles.vizWrapper}>
        {/* Central orb via SVG */}
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className={styles.svg}
        >
          {/* Ambient glow */}
          <defs>
            <radialGradient id="lp-glow">
              <stop offset="0%" stopColor={health.color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={health.color} stopOpacity="0" />
            </radialGradient>
          </defs>
          <circle cx={center} cy={center} r={coreRadius + 20} fill="url(#lp-glow)" />

          {/* Orbital metric rings */}
          {metrics.map((m, i) => {
            const ringRadius = coreRadius + 10 + i * (compact ? 10 : 12);
            const circumference = 2 * Math.PI * ringRadius;
            const dashLen = circumference * m.fill;
            const dashGap = circumference - dashLen;

            return (
              <circle
                key={m.id}
                cx={center}
                cy={center}
                r={ringRadius}
                fill="none"
                stroke={m.color}
                strokeWidth={compact ? 2.5 : 3}
                strokeDasharray={`${dashLen} ${dashGap}`}
                strokeDashoffset={circumference * 0.25} // Start from top
                strokeLinecap="round"
                opacity={0.6}
                className={styles.ring}
                style={{ '--ring-delay': `${i * 0.15}s` }}
              />
            );
          })}

          {/* Core orb */}
          <circle
            cx={center}
            cy={center}
            r={coreRadius}
            fill="none"
            stroke={health.color}
            strokeWidth={2}
            opacity={0.8}
            className={styles.coreRing}
          />
          <circle
            cx={center}
            cy={center}
            r={coreRadius - 4}
            fill={`${health.color}15`}
            className={styles.coreFill}
          />

          {/* Score text */}
          <text
            x={center}
            y={center - 6}
            textAnchor="middle"
            fill={health.color}
            fontSize={compact ? 18 : 22}
            fontWeight="900"
            fontFamily="var(--font-mono, monospace)"
          >
            {health.score}
          </text>
          <text
            x={center}
            y={center + 10}
            textAnchor="middle"
            fill="var(--text-muted, #94a3b8)"
            fontSize={compact ? 7 : 8}
            fontWeight="700"
            letterSpacing="0.12em"
            textTransform="uppercase"
          >
            {health.label.toUpperCase()}
          </text>
        </svg>

        {/* Metric labels around the orb */}
        <div className={styles.metricLabels}>
          {metrics.map((m, i) => {
            const angle = (i / metrics.length) * 2 * Math.PI - Math.PI / 2;
            const labelRadius = compact ? 78 : 100;
            const x = 50 + (labelRadius / (size / 2)) * Math.cos(angle) * 50;
            const y = 50 + (labelRadius / (size / 2)) * Math.sin(angle) * 50;

            return (
              <div
                key={m.id}
                className={styles.metricLabel}
                style={{
                  left: `${x}%`,
                  top: `${y}%`,
                  color: m.color,
                }}
                title={m.displayValue}
              >
                <span className={styles.metricLabelName}>{m.label}</span>
                <span className={styles.metricLabelValue}>{m.displayValue}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
