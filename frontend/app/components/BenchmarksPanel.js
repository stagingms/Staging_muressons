'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * BenchmarksPanel — FTSE 100 ESG Benchmarks comparison.
 * Fetches from /{sessionId}/benchmarks and renders percentile gauges.
 */
export default function BenchmarksPanel({ sessionId, roundNumber }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!sessionId || !expanded) return;
    setLoading(true);
    fetch(`${API}/api/simulations/${sessionId}/benchmarks`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [sessionId, expanded, roundNumber]);

  // Don't show until at least R2
  if (roundNumber < 2) return null;

  const badgeColors = { '🏆': '#10b981', '✅': '#22c55e', '⚠️': '#f59e0b', '🔴': '#ef4444' };

  return (
    <div style={{
      marginTop: 10, borderRadius: 8,
      background: 'rgba(14,165,233,0.04)',
      border: '1px solid rgba(14,165,233,0.15)',
      overflow: 'hidden',
    }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%', padding: '8px 14px',
          background: 'transparent', border: 'none',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          cursor: 'pointer', fontFamily: 'Inter, sans-serif',
        }}
      >
        <span style={{
          fontSize: '0.62rem', fontWeight: 800, color: '#38bdf8',
          letterSpacing: '0.08em', textTransform: 'uppercase',
          display: 'flex', alignItems: 'center', gap: 5,
        }}>
          <span>📈</span> FTSE 100 ESG Benchmarks
        </span>
        <span style={{
          fontSize: '0.65rem', color: '#64748b',
          transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s',
        }}>
          ▼
        </span>
      </button>

      {expanded && (
        <div style={{ padding: '0 14px 12px' }}>
          {loading && (
            <div style={{ fontSize: '0.68rem', color: '#64748b', padding: '8px 0' }}>
              Loading benchmark data…
            </div>
          )}
          {data && data.benchmarks && (
            <>
              <div style={{
                display: 'grid', gridTemplateColumns: '1fr 1fr',
                gap: 6, marginBottom: 8,
              }}>
                {Object.entries(data.benchmarks).map(([key, bm]) => {
                  const pctl = bm.percentile;
                  const barWidth = Math.min(pctl, 100);
                  const barColor = pctl >= 75 ? '#10b981' : pctl >= 50 ? '#22c55e' : pctl >= 25 ? '#f59e0b' : '#ef4444';
                  return (
                    <div key={key} style={{
                      padding: '6px 8px', borderRadius: 6,
                      background: 'rgba(255,255,255,0.02)',
                      border: '1px solid rgba(255,255,255,0.05)',
                    }}>
                      <div style={{
                        display: 'flex', justifyContent: 'space-between',
                        alignItems: 'center', marginBottom: 3,
                      }}>
                        <span style={{ fontSize: '0.58rem', fontWeight: 700, color: '#94a3b8' }}>
                          {bm.label}
                        </span>
                        <span style={{ fontSize: '0.55rem', fontWeight: 800, color: badgeColors[bm.badge] || '#94a3b8' }}>
                          {bm.badge} {bm.percentile_label}
                        </span>
                      </div>
                      {/* Percentile bar */}
                      <div style={{
                        height: 4, borderRadius: 2,
                        background: 'rgba(255,255,255,0.06)',
                        overflow: 'hidden', marginBottom: 3,
                      }}>
                        <div style={{
                          height: '100%', width: `${barWidth}%`,
                          background: barColor,
                          borderRadius: 2,
                          transition: 'width 0.6s ease',
                        }} />
                      </div>
                      <div style={{
                        display: 'flex', justifyContent: 'space-between',
                        fontSize: '0.55rem', color: '#64748b',
                      }}>
                        <span>Your value: <strong style={{ color: '#e2e8f0' }}>{bm.your_value} {bm.unit}</strong></span>
                        <span>{bm.insight?.split('—')[0]}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ fontSize: '0.5rem', color: '#475569', fontStyle: 'italic' }}>
                {data.data_source} · {data.note}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
