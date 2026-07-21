'use client';
import React, { useMemo } from 'react';
import { computeMrRegret } from '../utils/mrJourney';

/**
 * RegretMeter (wow feature) — at terminal valuation, shows the team's actual
 * Regenerative Multiple next to the best they could have reached from the same
 * hand, and names exactly which decisions cost them. "You left 0.42 M_R on the
 * table" — a memorable, defensible teaching moment (every number traces to a
 * flag in the engine's dependency graph, so a facilitator can justify it).
 *
 * Props: mr (actual M_R number), flags (globalState.active_event_flags).
 */
export default function RegretMeter({ mr = 0, flags = {} }) {
  const { missed, captured, mrLeftOnTable } = useMemo(() => computeMrRegret(flags), [flags]);
  const actual = Number(mr) || 0;
  const best = Math.round((actual + mrLeftOnTable) * 100) / 100;
  const pct = best > 0 ? Math.min(100, (actual / best) * 100) : 100;

  if (mrLeftOnTable <= 0) {
    return (
      <div style={wrap}>
        <div style={{ ...headline, color: 'var(--kpi-good, #10b981)' }}>
          🏆 You captured every M_R opportunity available — nothing left on the table.
        </div>
      </div>
    );
  }

  return (
    <div style={wrap}>
      <div style={headline}>
        You left <strong style={{ color: 'var(--kpi-warn, #f59e0b)' }}>{mrLeftOnTable.toFixed(2)} M_R</strong> on the table.
      </div>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary, #b0bec5)', marginBottom: 10 }}>
        Actual <strong>{actual.toFixed(2)}×</strong> · Best achievable from your hand <strong>{best.toFixed(2)}×</strong>
      </div>

      {/* Bar: actual (solid) vs the missed remainder (ghosted) */}
      <div style={{ position: 'relative', height: 14, borderRadius: 7, background: 'rgba(148,163,184,0.15)', overflow: 'hidden', marginBottom: 12 }}>
        <div style={{ position: 'absolute', inset: 0, width: '100%', background: 'repeating-linear-gradient(45deg, rgba(245,158,11,0.18) 0 6px, transparent 6px 12px)' }} />
        <div style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: `${pct}%`, background: 'linear-gradient(90deg, var(--accent-blue, #3b82f6), var(--kpi-good, #10b981))', borderRadius: 7, transition: 'width 0.8s ease' }} />
      </div>

      {/* What was missed */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {missed.map((m) => (
          <div key={m.flag} style={row}>
            <span style={{ color: 'var(--kpi-warn, #f59e0b)' }}>✗ R{m.round} · {m.label}</span>
            <span style={{ fontWeight: 700, color: 'var(--kpi-warn, #f59e0b)' }}>+{m.mr.toFixed(2)} missed</span>
          </div>
        ))}
        {captured.map((m) => (
          <div key={m.flag} style={{ ...row, opacity: 0.75 }}>
            <span style={{ color: 'var(--kpi-good, #10b981)' }}>✓ R{m.round} · {m.label}</span>
            <span style={{ fontWeight: 700, color: 'var(--kpi-good, #10b981)' }}>+{m.mr.toFixed(2)} captured</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const wrap = {
  marginTop: 16, padding: '16px 18px', borderRadius: 12,
  background: 'var(--bg-card, rgba(22,30,46,0.6))',
  border: '1px solid var(--border-subtle, rgba(148,163,184,0.15))',
};
const headline = { fontSize: '1.05rem', fontWeight: 700, marginBottom: 4, color: 'var(--text-primary, #f1f5f9)' };
const row = { display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', lineHeight: 1.6 };
