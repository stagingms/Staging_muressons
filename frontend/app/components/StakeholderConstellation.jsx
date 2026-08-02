'use client';

import { useMemo } from 'react';
import styles from './StakeholderConstellation.module.css';

/* ═════════════════════════════════════════════════════════════════
 *  STAKEHOLDER CONSTELLATION — SA-E (the "wow" layer)
 *
 *  Slot: Rail tab (asynchronous context) — a glanceable header ABOVE the
 *  existing roster, not a new panel. A relationship orbit around YOU:
 *
 *    distance from centre = tolerance  (allied sit close; estranged drift out)
 *    node tint            = agent identity colour
 *    ring colour          = escalation stage (STAGE_META, passed in)
 *    node size            = leverage (how hard they can hit you)
 *    pulse                = agitated / hostile / triggered
 *    link thickness       = relationship strength (tolerance)
 *
 *  Purely presentational: reads the same merged agent fields the rows use,
 *  derives everything client-side, adds no request and changes no logic.
 *  Renders nothing with fewer than two agents.
 *
 *  Props: nodes = [{ id, initials, tint, tolerance, maxTolerance, stage,
 *                    stageColor, leverage, name }]
 * ═════════════════════════════════════════════════════════════════ */

const AGITATED = new Set(['agitated', 'hostile', 'triggered']);

// Leverage label → node weight (0..1). Design-authored keywords; unknown → mid.
const HEAVY = /capital|regulat|legal|strike|narrative|divest|licen|permit|court|media/i;
function leverageWeight(lev) {
  if (!lev) return 0.55;
  if (HEAVY.test(lev)) return 1;
  if (/moderate|some|limited|low/i.test(lev)) return 0.45;
  return 0.65;
}

// Deterministic small jitter from the id so the ring isn't a rigid clock face.
function jitter(id) {
  let h = 0;
  for (let i = 0; i < (id || '').length; i++) h = (h * 31 + id.charCodeAt(i)) % 1000;
  return (h / 1000 - 0.5) * 0.5; // ±0.25 rad
}

export default function StakeholderConstellation({ nodes = [] }) {
  const placed = useMemo(() => {
    const n = nodes.length;
    if (n < 2) return [];
    return nodes.map((d, i) => {
      const max = d.maxTolerance || 100;
      const pct = Math.max(0, Math.min(1, (d.tolerance ?? 50) / max));
      // allied (high tolerance) sit near the centre; estranged drift outward.
      const rf = 0.4 + (1 - pct) * 0.5;
      const theta = -Math.PI / 2 + (i * 2 * Math.PI) / n + jitter(d.id);
      const x = Math.max(9, Math.min(91, 50 + Math.cos(theta) * rf * 42));
      const y = Math.max(12, Math.min(88, 50 + Math.sin(theta) * rf * 40));
      const size = 25 + leverageWeight(d.leverage) * 15; // 25..40px
      return { ...d, x, y, pct, size, agit: AGITATED.has(d.stage) };
    });
  }, [nodes]);

  if (placed.length < 2) return null;

  return (
    <div className={styles.field} role="img" aria-label="Stakeholder relationship field: closer nodes are more allied, colour shows mood">
      <span className={styles.legend}>ALLIED · CLOSE</span>
      <span className={`${styles.legend} ${styles.legendRight}`}>ESTRANGED · FAR</span>

      <div className={styles.orbit} style={{ width: '46%', height: '50%' }} />
      <div className={styles.orbit} style={{ width: '78%', height: '82%' }} />

      <svg className={styles.links} viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        {placed.map((p) => (
          <line
            key={`l-${p.id}`}
            x1="50" y1="50" x2={p.x} y2={p.y}
            stroke={p.stageColor}
            strokeOpacity={0.14 + p.pct * 0.28}
            strokeWidth={0.3 + p.pct * 0.5}
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>

      <div className={styles.core} aria-hidden="true">YOU</div>

      {placed.map((p, i) => {
        const drift = [styles.driftA, styles.driftB, styles.driftC][i % 3];
        return (
          <div
            key={p.id}
            className={`${styles.node} ${p.agit ? styles.agitated : drift}`}
            style={{ left: `${p.x}%`, top: `${p.y}%`, width: p.size, height: p.size }}
            title={`${p.name} — ${p.stage}, relationship ${Math.round(p.tolerance ?? 0)}/${p.maxTolerance || 100}`}
          >
            <div className={styles.nodeInner}>
              <div className={styles.ring} style={{ borderColor: p.stageColor }} />
              <div
                className={styles.disc}
                style={{ background: `${p.tint}26`, color: p.tint, fontSize: p.size / 3 }}
              >
                {p.initials}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
