'use client';

import { useState } from 'react';
import PasswordInput from './PasswordInput';

const API = process.env.NEXT_PUBLIC_API_URL || '';

/**
 * AdminLogin — the ONE admin sign-in form (Phase L: role-aware login).
 *
 * Neutral by design: it never names a role or a portal (no "God Mode", no
 * "project admin"). It authenticates against the same endpoint both old gates
 * used, then hands the server-returned `data` to `onSuccess` — the CALLER
 * decides where to route and what to persist (see utils/roleRouting). This
 * removes the pre-auth "pick your portal" step that advertised privileged
 * consoles to every visitor.
 *
 * Props:
 *   - onSuccess(data): called with the full login response on 200.
 *   - subtitle?:       optional line under the title.
 */
export default function AdminLogin({ onSuccess, subtitle }) {
  const [facId, setFacId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [capsOn, setCapsOn] = useState(false);

  const trackCaps = (e) => {
    if (typeof e.getModifierState === 'function') setCapsOn(e.getModifierState('CapsLock'));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!facId.trim() || !password.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/api/admin/facilitators/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // credentials:'include' so the browser stores the HttpOnly JWT cookie.
        credentials: 'include',
        body: JSON.stringify({ facilitator_id: facId.trim(), password: password.trim() }),
      });
      if (res.ok) {
        onSuccess?.(await res.json());
      } else {
        const err = await res.json().catch(() => ({}));
        setError(err.detail || 'Login failed');
      }
    } catch {
      setError('Cannot connect to server');
    } finally {
      setLoading(false);
    }
  };

  const labelStyle = {
    display: 'block', fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
    letterSpacing: '0.1em', color: 'var(--text-muted)', marginBottom: '0.4rem',
  };
  const inputStyle = {
    width: '100%', padding: '0.7rem 1rem', borderRadius: 'var(--radius-md, 6px)',
    border: '1px solid var(--border-subtle)', background: 'var(--bg-body)',
    color: 'var(--text-primary)', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box',
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-body, #080c18)', padding: '2rem',
    }}>
      <div style={{
        background: 'var(--bg-card, #0f1729)', border: '1px solid var(--border-subtle, rgba(148,163,184,0.15))',
        borderRadius: 'var(--radius-lg, 12px)', padding: '3rem', maxWidth: '420px', width: '100%',
        boxShadow: '0 8px 32px rgba(0,0,0,0.35)',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '2rem', fontWeight: 900, letterSpacing: '0.06em', color: 'var(--text-primary, #f1f5f9)' }}>
            MURESSONS
          </div>
          <h1 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary, #f1f5f9)', margin: '0.75rem 0 0.4rem' }}>
            Sign in
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted, #8899a6)', margin: 0 }}>
            {subtitle || 'Enter your facilitator credentials to continue.'}
          </p>
        </div>

        <form onSubmit={handleSubmit} onKeyDown={trackCaps} onKeyUp={trackCaps}
          style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {error && (
            <div role="alert" style={{
              background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)',
              color: '#fca5a5', padding: '0.6rem', borderRadius: '6px', fontSize: '0.82rem',
            }}>{error}</div>
          )}
          {capsOn && (
            <div style={{
              background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.25)',
              color: '#f59e0b', padding: '0.45rem 0.6rem', borderRadius: '6px', fontSize: '0.78rem',
            }}>⇪ Caps Lock is on</div>
          )}
          <div>
            <label style={labelStyle}>Facilitator ID</label>
            <input
              type="text" value={facId} onChange={(e) => setFacId(e.target.value)}
              placeholder="e.g. FAC-001" disabled={loading} autoFocus
              /* Password managers tag the username field too (it is half of a
                 saved credential) — see the note in PasswordInput. */
              suppressHydrationWarning
              style={{ ...inputStyle, fontFamily: 'var(--font-mono, monospace)' }}
            />
          </div>
          <div>
            <label style={labelStyle}>Password</label>
            <PasswordInput
              value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password" disabled={loading} required style={inputStyle}
            />
          </div>
          <button type="submit" disabled={loading} style={{
            marginTop: '0.5rem', padding: '0.75rem', borderRadius: '8px', border: 'none',
            background: loading ? 'rgba(99,102,241,0.5)' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
            color: '#fff', fontSize: '0.9rem', fontWeight: 700,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
