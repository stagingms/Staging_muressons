/**
 * LivingPlanet — WOW-7
 *
 * An ambient CSS/SVG ESG health visualization showing composite ESG state
 * as a central orb with four orbital metric rings:
 *   - Reputation (green→red)
 *   - Carbon Intensity (blue→orange)
 *   - Nature Capital (teal→amber)
 *   - Social License (purple→red)
 *
 * Colour shifts from green → blue → amber → red based on real-time state.
 *
 * SAFETY: Pure presentation. Reads existing globalState metrics.
 * Falls back to flat metric cards when prefers-reduced-motion is set.
 * Renders nothing if data is unavailable.
 *
 * Props:
 *   globalState    — current global state object
 *   businessUnits  — BU state array (optional)
 *   compact        — boolean, renders smaller for sidebar
 */
'use client';
import React, { useMemo } from 'react';
import styles from './LivingPlanet.module.css';

/** Score 0-100 → colour hex */
function healthColor(score) {
  if (score >= 75) return '#10b981'; // green
  if (score >= 50) return '#3b82f6'; // blue
  if (score >= 30) return '#f59e0b'; // amber
  return '#ef4444';                  // red
}

/** Compute composite ESG score from global state */
function computeMetrics(gs) {
  if (!gs) return null;
  const rep = Number(gs.group_reputation) || 50;
  const flags = gs.active_event_flags || {};

  // Carbon: lower is better, normalize inversely
  const carbon = Number(gs.tco2e_emissions) || 0;
  const carbonScore = Math.max(0, Math.min(100, 100 - (carbon / 500) * 100));

  // Nature Capital Deficit: lower is better
  const ncd = Number(flags.ncd_index) || Number(gs.ncd) || 30;
  const ncdScore = Math.max(0, Math.min(100, 100 - ncd));

  // Social License: higher is better (SLO)
  const slo = Number(gs.social_license) || Number(flags.slo_index) || 60;
  const sloScore = Math.max(0, Math.min(100, slo));

  const composite = Math.round((rep + carbonScore + ncdScore + sloScore) / 4);

  return {
    composite,
    reputation: { score: rep, label: 'Reputation', icon: '⭐' },
    carbon: { score: Math.round(carbonScore), label: 'Carbon', icon: '🌡️' },
    nature: { score: Math.round(ncdScore), label: 'Nature', icon: '🌿' },
    social: { score: Math.round(sloScore), label: 'Social', icon: '👥' },
  };
}

function OrbRing({ metric, index, total, size }) {
  const radius = size / 2 - 8 - index * 12;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - metric.score / 100);
  const cx = size / 2;
  const cy = size / 2;
  const color = healthColor(metric.score);

  return (
    <circle
      cx={cx}
      cy={cy}
      r={radius}
      fill="none"
      stroke={color}
      strokeWidth={4}
      strokeDasharray={circumference}
      strokeDashoffset={dashOffset}
      strokeLinecap="round"
      transform={`rotate(-90 ${cx} ${cy})`}
      opacity={0.65}
      className={styles.ring}
      style={{ '--ring-delay': `${index * 0.2}s` }}
    />
  );
}

export default function LivingPlanet({ globalState, businessUnits, compact = false }) {
  const metrics = useMemo(() => computeMetrics(globalState), [globalState]);

  if (!metrics) return null;

  const size = compact ? 140 : 200;
  const orbColor = healthColor(metrics.composite);
  const ringMetrics = [metrics.reputation, metrics.carbon, metrics.nature, metrics.social];

  return (
    <div className={`${styles.container} ${compact ? styles.compact : ''}`}>
      <div className={styles.header}>
        <span className={styles.headerIcon}>🌍</span>
        <span className={styles.headerTitle}>Living Planet</span>
        <span className={styles.compositeScore} style={{ color: orbColor }}>
          {metrics.composite}/100
        </span>
      </div>

      {/* SVG Orb + Rings */}
      <div className={styles.orbWrapper}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className={styles.orbSvg}>
          {/* Background rings */}
          {ringMetrics.map((m, i) => (
            <circle
              key={`bg-${i}`}
              cx={size / 2}
              cy={size / 2}
              r={size / 2 - 8 - i * 12}
              fill="none"
              stroke="rgba(148,163,184,0.08)"
              strokeWidth={4}
            />
          ))}

          {/* Data rings */}
          {ringMetrics.map((m, i) => (
            <OrbRing key={i} metric={m} index={i} total={ringMetrics.length} size={size} />
          ))}

          {/* Central orb */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={size / 2 - 56}
            fill={orbColor}
            opacity={0.15}
            className={styles.centralOrb}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={size / 2 - 60}
            fill="none"
            stroke={orbColor}
            strokeWidth={2}
            opacity={0.4}
          />
          <text
            x={size / 2}
            y={size / 2 + 5}
            textAnchor="middle"
            fill={orbColor}
            fontSize={compact ? 18 : 24}
            fontWeight={900}
            fontFamily="var(--font-mono, monospace)"
          >
            {metrics.composite}
          </text>
        </svg>
      </div>

      {/* Metric cards (flat fallback for reduced motion) */}
      <div className={styles.metricGrid}>
        {ringMetrics.map((m, i) => (
          <div key={i} className={styles.metricCard}>
            <span className={styles.metricIcon}>{m.icon}</span>
            <span className={styles.metricLabel}>{m.label}</span>
            <span className={styles.metricValue} style={{ color: healthColor(m.score) }}>
              {m.score}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
