'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * FacilitatorTeachableMoments (B5)
 * Facilitator-only prompt: when >= half a cohort's teams converge on a decision
 * flag the engine marks as adverse (doubles a crisis, BLOCKS a bonus, triggers
 * a penalty), show a non-blocking "pause and discuss" card. Read-only: polls the
 * analytics endpoint; players are unaffected. Renders nothing when there's
 * nothing to flag, so it never adds clutter.
 */
export default function FacilitatorTeachableMoments({ cohortId, pollMs = 20000 }) {
  const [notes, setNotes] = useState([]);

  useEffect(() => {
    if (!cohortId) return;
    let cancelled = false;
    const load = () => {
      fetch(`${API}/api/admin/analytics/${cohortId}/teachable-moments`, { credentials: 'include' })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (!cancelled && d) setNotes(d.teachable_moments || []); })
        .catch(() => { /* silent — facilitator aid, never blocks */ });
    };
    load();
    const id = setInterval(load, pollMs);
    return () => { cancelled = true; clearInterval(id); };
  }, [cohortId, pollMs]);

  if (!notes.length) return null;

  return (
    <div style={{
      marginTop: 12, borderRadius: 10, overflow: 'hidden',
      border: '1px solid rgba(217,119,6,0.35)', background: 'rgba(217,119,6,0.06)',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px',
        fontSize: 'var(--type-caption)', fontWeight: 800, letterSpacing: '0.06em',
        textTransform: 'uppercase', color: '#d97706',
      }}>
        <span>💡</span> Teachable Moments
      </div>
      <div style={{ padding: '0 14px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {notes.map((n) => (
          <div key={n.flag} style={{
            padding: '8px 10px', borderRadius: 8,
            background: 'var(--bg-elevated)',
            border: '1px solid rgba(148,163,184,0.18)',
          }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {n.count}/{n.total} teams · {n.flag}
            </div>
            <div style={{ fontSize: '0.78rem', lineHeight: 1.45, marginTop: 2, color: 'var(--text-secondary)' }}>
              {n.message}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
