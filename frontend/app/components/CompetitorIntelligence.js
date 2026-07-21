import React from 'react';

const pulse = `@keyframes ci-pulse { 0%,100%{opacity:1} 50%{opacity:.6} }`;

function TrendArrow({ current, previous }) {
  if (previous == null || previous <= 0) return null;
  const delta = current - previous;
  const pct = previous ? delta / previous : 0;
  let arrow, color;
  if (pct > 0.05)       { arrow = '↑'; color = '#10b981'; }
  else if (pct > 0)     { arrow = '↗'; color = '#34d399'; }
  else if (pct < -0.05) { arrow = '↓'; color = '#ef4444'; }
  else if (pct < 0)     { arrow = '↘'; color = '#f87171'; }
  else                   { arrow = '→'; color = '#94a3b8'; }
  return <span style={{ color, fontSize: '0.85rem', fontWeight: 700, marginLeft: 4 }}>{arrow}</span>;
}

export default function CompetitorIntelligence({ globalState, ebitda, roundNumber }) {
  const competitorEbitda = globalState?.competitor_ebitda || ebitda;
  const previousEbitda = globalState?.previous_ebitda;
  const isTrailing = ebitda < competitorEbitda;
  const fmtM = (v) => `$${(v / 1_000_000).toFixed(1)}M`;
  const ratio = (ebitda / (competitorEbitda || 1)).toFixed(2);
  const isTied = ratio === '1.00';
  const hasData = ebitda > 0;
  const maxVal = Math.max(ebitda, competitorEbitda, 1);

  const badgeStyle = isTied
    ? { background: 'rgba(148,163,184,0.1)', color: '#64748b' }
    : isTrailing
      ? { background: 'rgba(244,63,94,0.15)', color: '#e11d48', boxShadow: '0 0 8px rgba(244,63,94,0.2)', animation: 'ci-pulse 2s ease-in-out infinite' }
      : { background: 'rgba(16,185,129,0.15)', color: '#10b981', boxShadow: '0 0 8px rgba(16,185,129,0.2)' };

  const barRow = (label, value, color) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ fontSize: '0.6rem', width: 52, color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: 10, borderRadius: 5, background: 'rgba(148,163,184,0.08)', overflow: 'hidden' }}>
        <div style={{
          width: `${Math.max((value / maxVal) * 100, 2)}%`,
          height: '100%', borderRadius: 5, background: color,
          transition: 'width 0.6s cubic-bezier(.22,1,.36,1)',
        }} />
      </div>
      <span style={{ fontSize: '0.62rem', color: '#cbd5e1', fontWeight: 600, minWidth: 40, textAlign: 'right', flexShrink: 0 }}>{fmtM(value)}</span>
    </div>
  );

  return (
    <div style={{
      padding: '10px 14px', borderBottom: '1px solid rgba(0,229,195,0.06)',
      display: 'flex', flexDirection: 'column', gap: 6,
      background: 'rgba(15,23,42,0.4)',
    }}>
      <style>{pulse}</style>
      <div style={{
        fontSize: '0.68rem', fontWeight: 800, textTransform: 'uppercase',
        letterSpacing: '0.08em', color: '#f1f5f9',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
          <span>👁️‍🗨️</span> Competitor Intel
        </div>
        {hasData && (
          <span style={{
            fontSize: '0.62rem', padding: '2px 7px', borderRadius: 4, fontWeight: 700,
            ...badgeStyle,
          }}>
            {isTied ? 'Tied' : isTrailing ? 'Trailing' : 'Leading'} ({ratio}x)
          </span>
        )}
      </div>

      {!hasData ? (
        <div style={{ padding: '8px 0', fontSize: '0.7rem', color: '#94a3b8', fontStyle: 'italic', textAlign: 'center' }}>
          📊 Competitor data available from Round 2
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginTop: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ flex: 1 }}>{barRow('You', ebitda, '#6366f1')}</div>
            <TrendArrow current={ebitda} previous={previousEbitda} />
          </div>
          {barRow('Rival', competitorEbitda, '#f43f5e')}
        </div>
      )}
    </div>
  );
}
