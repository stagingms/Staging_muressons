'use client';

/**
 * PlayerFeatureToggles — Configuration sub-tab on the Facilitator dashboard,
 * open to all run-managing facilitators (project_admin excluded server-side via
 * require_sim_manager). Switches the player-facing round surfaces — the results
 * Decision Consequence Map and the Board Room Moment reflection — on or off.
 * Reads the current values from /api/admin/global-settings and writes via
 * /api/admin/player-feature-toggles; the player cockpit reads the same settings.
 */
import { useState, useEffect, useCallback } from 'react';

const FEATURES = [
  {
    key: 'consequence_map_enabled',
    label: 'Decision Consequence Map',
    desc: 'The results-view timeline linking each round’s decisions to their downstream governance / climate / risk / social / supply-chain / strategic effects.',
  },
  {
    key: 'board_room_moments_enabled',
    label: 'Board Room Moment',
    desc: 'The guided post-round reflection (Noticing → Making Sense → Working with Meaning) shown after results are reviewed.',
  },
];

export default function PlayerFeatureToggles() {
  const API = process.env.NEXT_PUBLIC_API_URL || '';
  const [values, setValues] = useState({ consequence_map_enabled: true, board_room_moments_enabled: true });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState(null);

  const flash = (msg, ok = true) => { setStatus({ msg, ok }); setTimeout(() => setStatus(null), 4000); };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/admin/global-settings`, { credentials: 'include' });
      if (r.ok) {
        const s = await r.json();
        setValues({
          consequence_map_enabled: s.consequence_map_enabled !== false,
          board_room_moments_enabled: s.board_room_moments_enabled !== false,
        });
      }
    } catch { /* offline → keep defaults */ }
    setLoading(false);
  }, [API]);

  useEffect(() => { load(); }, [load]);

  const toggle = async (key) => {
    const next = !values[key];
    setValues((v) => ({ ...v, [key]: next }));  // optimistic
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/admin/player-feature-toggles`, {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [key]: next }),
      });
      if (r.ok) {
        const d = await r.json();
        setValues((v) => ({ ...v, [key]: d[key] !== false }));
        flash(`✅ ${next ? 'Enabled' : 'Disabled'}`);
      } else {
        setValues((v) => ({ ...v, [key]: !next }));  // revert
        flash(r.status === 403 ? '❌ Facilitator authentication required' : '❌ Save failed', false);
      }
    } catch {
      setValues((v) => ({ ...v, [key]: !next }));
      flash('❌ Connection error', false);
    }
    setSaving(false);
  };

  return (
    <div style={{ padding: '1.5rem', color: '#e2e8f0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800 }}>🎛️ Player Features</h2>
        {status && (
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: status.ok ? '#4ade80' : '#f87171' }}>{status.msg}</span>
        )}
      </div>
      <p style={{ color: '#94a3b8', fontSize: '0.8rem', margin: '0 0 16px' }}>
        Show or hide player-facing round surfaces. Changes apply to all cohorts and take effect on the players’ next dashboard refresh.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 720 }}>
        {FEATURES.map((f) => (
          <div key={f.key} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
            padding: '14px 16px', borderRadius: 12,
            background: 'rgba(99,102,241,0.05)', border: '1px solid rgba(99,102,241,0.18)',
          }}>
            <div>
              <div style={{ fontSize: '0.92rem', fontWeight: 700 }}>{f.label}</div>
              <div style={{ fontSize: '0.76rem', color: '#94a3b8', marginTop: 3, maxWidth: 560, lineHeight: 1.5 }}>{f.desc}</div>
            </div>
            <button
              onClick={() => toggle(f.key)}
              disabled={saving || loading}
              aria-pressed={values[f.key]}
              title={values[f.key] ? 'Shown to players — click to hide' : 'Hidden from players — click to show'}
              style={{
                position: 'relative', width: 52, height: 28, borderRadius: 14, flexShrink: 0, cursor: 'pointer',
                border: 'none', background: values[f.key] ? '#10b981' : 'rgba(148,163,184,0.3)',
                transition: 'background 0.2s', opacity: (saving || loading) ? 0.6 : 1,
              }}
            >
              <span style={{
                position: 'absolute', top: 3, left: 3, width: 22, height: 22, borderRadius: '50%',
                background: '#fff', transition: 'transform 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.4)',
                transform: values[f.key] ? 'translateX(24px)' : 'translateX(0)',
              }} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
