'use client';
import React, { useState, useEffect, useMemo } from 'react';
import { MR_OPPORTUNITIES, computeMrRegret } from '../utils/mrJourney';

/**
 * RewindRibbon (wow feature) — "Rewind your 5 years in 20 seconds."
 * A single horizontal ribbon of the journey's M_R-bearing decisions. On mount
 * each node lights up in round order (captured = glowing green, missed = dim
 * amber), so a team watches their five years replay and sees which choices
 * compounded into their final Regenerative Multiple — systems thinking, made
 * visible. Respects prefers-reduced-motion (shows the final state immediately).
 *
 * Props: flags (globalState.active_event_flags).
 */
export default function RewindRibbon({ flags = {} }) {
  const { items } = useMemo(() => computeMrRegret(flags), [flags]);
  const ordered = useMemo(
    () => [...items].sort((a, b) => a.round - b.round),
    [items]
  );

  const reduceMotion = typeof window !== 'undefined'
    && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  const [revealed, setRevealed] = useState(reduceMotion ? ordered.length : 0);

  useEffect(() => {
    if (reduceMotion) { setRevealed(ordered.length); return; }
    setRevealed(0);
    let i = 0;
    const t = setInterval(() => {
      i += 1;
      setRevealed(i);
      if (i >= ordered.length) clearInterval(t);
    }, 550); // staggered reveal, ~3s for the full journey
    return () => clearInterval(t);
  }, [ordered.length, reduceMotion]);

  const runningMr = ordered.slice(0, revealed).reduce((s, n) => s + (n.captured ? n.mr : 0), 0);

  return (
    <div style={wrap}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10 }}>
        <span style={{ fontSize: 'var(--type-caption)', fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--accent-purple, #8b5cf6)' }}>
          ⏪ Rewind — 5 years of consequences
        </span>
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--kpi-good, #10b981)', fontFamily: 'var(--font-mono, monospace)' }}>
          +{(Math.round(runningMr * 100) / 100).toFixed(2)} M_R
        </span>
      </div>

      <div style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 0 }}>
        {/* connecting line */}
        <div style={{ position: 'absolute', left: 8, right: 8, top: '50%', height: 2, background: 'rgba(148,163,184,0.2)' }} />
        {ordered.map((n, idx) => {
          const isLit = idx < revealed;
          const good = n.captured;
          const color = good ? 'var(--kpi-good, #10b981)' : 'var(--kpi-warn, #f59e0b)';
          return (
            <div key={n.flag} style={{ position: 'relative', flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 0 }}>
              <div
                title={`R${n.round}: ${n.label} — ${good ? 'captured' : 'missed'} ${good ? '+' : ''}${n.mr.toFixed(2)} M_R`}
                style={{
                  width: 22, height: 22, borderRadius: '50%', zIndex: 1,
                  background: isLit ? color : 'rgba(148,163,184,0.25)',
                  boxShadow: isLit && good ? `0 0 12px ${'var(--kpi-good, #10b981)'}` : 'none',
                  border: '2px solid var(--bg-card, #161e2e)',
                  opacity: isLit ? 1 : 0.4,
                  transform: isLit ? 'scale(1)' : 'scale(0.7)',
                  transition: 'all 0.4s ease',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 'var(--type-caption)',
                }}
              >
                {isLit ? (good ? '✓' : '✗') : ''}
              </div>
              <div style={{ fontSize: 'var(--type-caption)', color: 'var(--text-muted, #8899a6)', marginTop: 4, fontWeight: 700 }}>R{n.round}</div>
              <div style={{
                fontSize: 'var(--type-caption)', color: isLit ? 'var(--text-secondary, #b0bec5)' : 'transparent',
                textAlign: 'center', lineHeight: 1.2, maxWidth: 70, transition: 'color 0.4s ease',
              }}>
                {n.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const wrap = {
  marginTop: 16, padding: '16px 18px', borderRadius: 12,
  background: 'var(--bg-card, rgba(22,30,46,0.6))',
  border: '1px solid var(--border-subtle, rgba(148,163,184,0.15))',
};
