'use client';

import { useId, useState, useEffect } from 'react';
import styles from './StakeholderAvatar.module.css';

/* ═════════════════════════════════════════════════════════════════
 *  STAKEHOLDER AVATAR — SA-A + SA-B + SA-D (Autonomous Stakeholders)
 *
 *  Slot: Rail tab (asynchronous context). One figure encodes identity
 *  AND state:
 *
 *    monogram     = identity (initials in the agent's brand colour, on a
 *                   tinted disc). Falls back to the vector silhouette when
 *                   no initials are supplied.
 *    ring colour  = escalation stage (STAGE_META colour, passed as `color`).
 *    ring sweep   = tolerance / maxTolerance — and it ANIMATES from empty on
 *                   mount (SA-D), so on every round re-commit the ring visibly
 *                   recharges: the "reaction" beat.
 *    ring ticks   = escalation thresholds.
 *    number       = numeric tolerance.
 *    figure motion= per-stage emote (breathe→sway→shiver→tremor→shake).
 *    pulse        = on hostile / triggered (honours reduced-motion).
 *
 *  Pure presentation. No data, no logic, no new requests.
 * ═════════════════════════════════════════════════════════════════ */
const R = 18.6;
const CIRC = 2 * Math.PI * R;

export default function StakeholderAvatar({
  color = '#64748b',
  stage = 'dormant',
  tolerance = null,
  maxTolerance = 100,
  thresholds = {},
  size = 42,
  label = '',
  initials = '',
  tint = null,
}) {
  const uid = useId().replace(/:/g, '');
  const pulse = stage === 'hostile' || stage === 'triggered';
  const hasGauge = tolerance != null && maxTolerance > 0;
  const pct = hasGauge ? Math.max(0, Math.min(1, tolerance / maxTolerance)) : 1;
  const dashoffset = CIRC * (1 - pct);

  // SA-D: mount ring-sweep. Start empty, then let the .ring stroke-dashoffset
  // transition draw it in — reused on every re-mount (round re-commit).
  const [swept, setSwept] = useState(false);
  useEffect(() => {
    const r = requestAnimationFrame(() => setSwept(true));
    return () => cancelAnimationFrame(r);
  }, []);
  const effOffset = swept ? dashoffset : CIRC;

  const idColor = tint || '#cbd5e1';

  const ticks = hasGauge
    ? Object.values(thresholds).map((v) => {
        const a = (v / maxTolerance) * 2 * Math.PI - Math.PI / 2;
        return {
          k: v,
          x1: 22 + (R - 2.4) * Math.cos(a),
          y1: 22 + (R - 2.4) * Math.sin(a),
          x2: 22 + (R + 2.4) * Math.cos(a),
          y2: 22 + (R + 2.4) * Math.sin(a),
        };
      })
    : [];

  return (
    <span
      className={`${styles.wrap} ${pulse ? styles.pulse : ''}`}
      data-stage={stage}
      {...(label ? { role: 'img', 'aria-label': label } : { 'aria-hidden': true })}
    >
      <svg viewBox="0 0 44 44" width={size} height={size} className={styles.svg}>
        <defs>
          <clipPath id={`sav-${uid}`}>
            <circle cx="22" cy="22" r="16.5" />
          </clipPath>
        </defs>

        {/* SA-C: the figure (disc + identity) carries the per-stage motion;
            the gauge ring + ticks stay put as stable instrumentation. */}
        <g className={styles.fig}>
          <circle cx="22" cy="22" r="16.5" className={styles.disc} />
          {tint && <circle cx="22" cy="22" r="16.5" fill={tint} opacity="0.16" />}
          {initials ? (
            <text
              x="22"
              y="22.5"
              className={styles.mono}
              fill={idColor}
              textAnchor="middle"
              dominantBaseline="central"
            >
              {initials}
            </text>
          ) : (
            <g clipPath={`url(#sav-${uid})`} className={styles.sil}>
              <path d="M5.4 40 C6 31 14.4 28 22 28 C29.6 28 38 31 38.6 40 L38.6 43 L5.4 43 Z" />
              <rect x="18.7" y="23" width="6.6" height="5.2" />
              <ellipse cx="22" cy="19.4" rx="7.3" ry="8" />
              <path d="M14.4 21 C13.4 13.5 17.4 9.4 22 9.4 C26.6 9.4 30.6 13.5 29.6 21 C28.1 16.8 26.1 15.5 24.7 15.5 L25.8 12.4 L23.3 15 L22.1 11.7 L20.9 15 L18.7 12.8 L17.9 15.5 C16.5 15.5 15.5 17.3 14.4 21 Z" />
              <ellipse cx="14.6" cy="20.4" rx="1.3" ry="1.8" />
              <ellipse cx="29.4" cy="20.4" rx="1.3" ry="1.8" />
            </g>
          )}
        </g>

        <circle cx="22" cy="22" r={R} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="2.6" />
        <circle
          cx="22"
          cy="22"
          r={R}
          fill="none"
          stroke={color}
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeDasharray={CIRC}
          strokeDashoffset={effOffset}
          transform="rotate(-90 22 22)"
          className={styles.ring}
        />
        {ticks.map((t) => (
          <line
            key={t.k}
            x1={t.x1}
            y1={t.y1}
            x2={t.x2}
            y2={t.y2}
            stroke="rgba(226,232,240,0.5)"
            strokeWidth="1.1"
            strokeLinecap="round"
          />
        ))}
      </svg>
      {hasGauge && <span className={styles.tol}>{Math.round(tolerance)}</span>}
    </span>
  );
}
