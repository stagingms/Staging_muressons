'use client';

import { useId } from 'react';
import styles from './StakeholderAvatar.module.css';

/* ═════════════════════════════════════════════════════════════════
 *  STAKEHOLDER AVATAR — SA-A (Autonomous Stakeholders redesign)
 *
 *  Slot: Rail tab (asynchronous context). Replaces the 22px header
 *  emoji avatar in StakeholderAgentPanel's AgentCard with a fixed
 *  neutral profile silhouette wrapped in a STATE-COLOURED ring:
 *
 *    ring colour  = escalation stage (STAGE_META colour, passed in as
 *                   `color` — STAGE_META stays the single source).
 *    ring pulse   = on hostile / triggered (honours reduced-motion).
 *
 *  Pure presentation. No data, no logic, no new requests. The tolerance
 *  number + zones still render in the existing ToleranceBar below; SA-B
 *  will fold the tolerance *sweep* into this ring and retire that bar.
 *
 *  The silhouette is a vector stand-in for a real per-agent headshot —
 *  swap the <g class="sil"> shapes for an <image href="/avatars/…"/>
 *  clipped to the same circle and nothing else changes.
 * ═════════════════════════════════════════════════════════════════ */
export default function StakeholderAvatar({ color = '#64748b', stage = 'dormant', size = 38 }) {
  const uid = useId().replace(/:/g, '');
  const pulse = stage === 'hostile' || stage === 'triggered';

  return (
    <span
      className={`${styles.wrap} ${pulse ? styles.pulse : ''}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 44 44" width={size} height={size} className={styles.svg}>
        <defs>
          <clipPath id={`sav-${uid}`}>
            <circle cx="22" cy="22" r="18.5" />
          </clipPath>
        </defs>

        <circle cx="22" cy="22" r="18.5" className={styles.disc} />

        <g clipPath={`url(#sav-${uid})`} className={styles.sil}>
          <path d="M5.4 40 C6 31 14.4 28 22 28 C29.6 28 38 31 38.6 40 L38.6 43 L5.4 43 Z" />
          <rect x="18.7" y="23" width="6.6" height="5.2" />
          <ellipse cx="22" cy="19.4" rx="7.3" ry="8" />
          <path d="M14.4 21 C13.4 13.5 17.4 9.4 22 9.4 C26.6 9.4 30.6 13.5 29.6 21 C28.1 16.8 26.1 15.5 24.7 15.5 L25.8 12.4 L23.3 15 L22.1 11.7 L20.9 15 L18.7 12.8 L17.9 15.5 C16.5 15.5 15.5 17.3 14.4 21 Z" />
          <ellipse cx="14.6" cy="20.4" rx="1.3" ry="1.8" />
          <ellipse cx="29.4" cy="20.4" rx="1.3" ry="1.8" />
        </g>

        <circle cx="22" cy="22" r="20.4" fill="none" stroke="rgba(255,255,255,0.09)" strokeWidth="2.4" />
        <circle
          cx="22"
          cy="22"
          r="20.4"
          fill="none"
          stroke={color}
          strokeWidth="2.4"
          strokeLinecap="round"
          className={styles.ring}
        />
      </svg>
    </span>
  );
}
