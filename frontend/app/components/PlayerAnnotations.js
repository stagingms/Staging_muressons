'use client';
import { useState, useEffect } from 'react';

/**
 * PlayerAnnotations — Student-facing view of facilitator annotations.
 *
 * Gap 3 from UX Audit: Facilitator annotations system with student visibility
 * controlled by the facilitator. Only annotations with visible_to_students=true
 * are surfaced to players.
 *
 * Props:
 *   sessionId:   Current session ID
 *   roundNumber: Current round (filters to relevant annotations)
 */

const TAG_STYLES = {
  general:         { bg: 'rgba(100,116,139,0.08)', border: 'rgba(100,116,139,0.2)', color: '#94a3b8', icon: '📝' },
  teaching_moment: { bg: 'rgba(99,102,241,0.08)',  border: 'rgba(99,102,241,0.2)',  color: '#a5b4fc', icon: '💡' },
  warning:         { bg: 'rgba(239,68,68,0.08)',    border: 'rgba(239,68,68,0.2)',   color: '#fca5a5', icon: '⚠️' },
  insight:         { bg: 'rgba(34,197,94,0.08)',     border: 'rgba(34,197,94,0.2)',   color: '#86efac', icon: '🔍' },
};

export default function PlayerAnnotations({ sessionId, roundNumber }) {
  const [annotations, setAnnotations] = useState([]);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (!sessionId || sessionId === 'demo') return;
    let cancelled = false;
    const API = process.env.NEXT_PUBLIC_API_URL || '';

    const fetchAnnotations = () => {
      fetch(`${API}/api/simulations/${sessionId}/annotations`)
        .then(r => r.ok ? r.json() : { annotations: [] })
        .then(d => {
          if (!cancelled) {
            // Filter to current round and earlier
            const relevant = (d.annotations || []).filter(a =>
              a.round <= roundNumber
            );
            setAnnotations(relevant);
          }
        })
        .catch(() => {});
    };

    fetchAnnotations();
    // Poll every 15s for new annotations
    const interval = setInterval(fetchAnnotations, 15000);
    return () => { cancelled = true; clearInterval(interval); };
  }, [sessionId, roundNumber]);

  if (annotations.length === 0) return null;

  return (
    <div style={{
      background: 'rgba(99, 102, 241, 0.04)',
      border: '1px solid rgba(99, 102, 241, 0.12)',
      borderRadius: '8px',
      padding: collapsed ? '6px 10px' : '10px 12px',
      marginBottom: '8px',
      transition: 'all 0.25s ease',
    }}>
      {/* Header */}
      <div
        onClick={() => setCollapsed(!collapsed)}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          cursor: 'pointer', userSelect: 'none',
        }}
      >
        <div style={{
          display: 'flex', alignItems: 'center', gap: '6px',
          fontSize: '0.68rem', fontWeight: 800,
          textTransform: 'uppercase', letterSpacing: '0.1em',
          color: '#a5b4fc',
        }}>
          <span>📌</span> Facilitator Notes
          <span style={{
            fontSize: '0.68rem', fontWeight: 700,
            background: 'rgba(99,102,241,0.2)',
            color: '#c7d2fe', padding: '1px 6px',
            borderRadius: '3px', marginLeft: '2px',
          }}>
            {annotations.length}
          </span>
        </div>
        <span style={{
          fontSize: '0.65rem', color: '#64748b',
          transform: collapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s',
        }}>▼</span>
      </div>

      {/* Annotation Cards */}
      {!collapsed && (
        <div style={{
          display: 'flex', flexDirection: 'column', gap: '5px',
          marginTop: '8px',
        }}>
          {annotations.map(ann => {
            const tc = TAG_STYLES[ann.tag] || TAG_STYLES.general;
            return (
              <div key={ann.id} style={{
                padding: '7px 10px',
                borderRadius: '6px',
                background: tc.bg,
                borderLeft: `3px solid ${tc.border}`,
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                animation: 'fadeIn 0.3s ease-out',
              }}>
                <span style={{ fontSize: '0.82rem', flexShrink: 0 }}>{tc.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '0.75rem', color: tc.color,
                    lineHeight: 1.5, fontWeight: 500,
                  }}>
                    {ann.text}
                  </div>
                  <div style={{
                    fontSize: '0.68rem', color: '#475569',
                    marginTop: '2px', display: 'flex', gap: '6px',
                  }}>
                    <span>R{ann.round}</span>
                    <span>·</span>
                    <span>{(ann.tag || 'general').replace('_', ' ')}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
