'use client';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { moneyM } from '../utils/format';

/**
 * ShockwaveOverlay (Feature 6) — full-screen takeover when the facilitator
 * detonates a synchronized black-swan. Klaxon + pulsing red vignette + a live
 * countdown + the event brief. "Respond Now" dismisses and drops the team back
 * into their decisions. Every team in the cohort sees this at the same instant.
 *
 * Props: event {title, narrative, financial_impact, reputation_impact},
 *        countdown (seconds), onDismiss().
 */
function klaxon() {
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    const ctx = new AC();
    const o = ctx.createOscillator(); const g = ctx.createGain();
    o.type = 'sawtooth'; o.connect(g); g.connect(ctx.destination);
    g.gain.value = 0.12;
    // two-tone alarm sweep
    let up = true;
    o.frequency.value = 440;
    const iv = setInterval(() => { o.frequency.value = up ? 660 : 440; up = !up; }, 500);
    o.start();
    return () => { clearInterval(iv); try { o.stop(); ctx.close(); } catch {} };
  } catch { return null; }
}

const fmtM = (v) => `${v < 0 ? '−' : '+'}${moneyM(Math.abs(v))}`;

export default function ShockwaveOverlay({ event, countdown = 60, onDismiss }) {
  const [left, setLeft] = useState(countdown);
  const stopRef = useRef(null);

  useEffect(() => {
    stopRef.current = klaxon();
    const t = setInterval(() => setLeft((s) => (s > 0 ? s - 1 : 0)), 1000);
    return () => { clearInterval(t); if (stopRef.current) stopRef.current(); };
  }, []);

  const dismiss = useCallback(() => {
    if (stopRef.current) stopRef.current();
    onDismiss?.();
  }, [onDismiss]);

  if (!event) return null;
  const mm = String(Math.floor(left / 60)).padStart(2, '0');
  const ss = String(left % 60).padStart(2, '0');

  return (
    <div style={S.overlay} role="alertdialog" aria-label="Global crisis alert">
      <div style={S.vignette} />
      <div style={S.inner}>
        <div style={S.klaxonIcon}>🌊</div>
        <div style={S.badge}>GLOBAL CRISIS · ALL TEAMS</div>
        <div style={S.title}>{event.title}</div>
        <div style={S.narrative}>{event.narrative}</div>
        <div style={S.impacts}>
          {event.financial_impact ? <span style={S.chip}>💰 {fmtM(event.financial_impact)} treasury</span> : null}
          {event.reputation_impact ? <span style={S.chip}>⭐ {event.reputation_impact > 0 ? '+' : ''}{event.reputation_impact} reputation</span> : null}
        </div>
        <div style={S.timer}>{mm}:{ss}</div>
        <div style={S.timerLabel}>time to respond</div>
        <button style={S.btn} onClick={dismiss}>Respond Now →</button>
      </div>
      <style>{`@keyframes mur-pulse{0%,100%{opacity:0.35}50%{opacity:0.7}}`}</style>
    </div>
  );
}

const S = {
  overlay: { position: 'fixed', inset: 0, zIndex: 99999, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(10,3,3,0.92)', backdropFilter: 'blur(2px)' },
  vignette: { position: 'absolute', inset: 0, boxShadow: 'inset 0 0 240px 60px rgba(239,68,68,0.55)', animation: 'mur-pulse 1.4s ease-in-out infinite', pointerEvents: 'none' },
  inner: { position: 'relative', textAlign: 'center', color: '#fff', maxWidth: 620, padding: '0 24px' },
  klaxonIcon: { fontSize: '4rem', marginBottom: 8 },
  badge: { display: 'inline-block', padding: '4px 14px', borderRadius: 999, background: '#ef4444', color: '#fff', fontWeight: 800, letterSpacing: '0.15em', fontSize: 'var(--type-caption)', marginBottom: 16 },
  title: { fontSize: '2.4rem', fontWeight: 900, lineHeight: 1.1, marginBottom: 12, textShadow: '0 2px 20px rgba(239,68,68,0.6)' },
  narrative: { fontSize: '1.1rem', color: '#e2e8f0', lineHeight: 1.5, marginBottom: 18 },
  impacts: { display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 22 },
  chip: { padding: '6px 14px', borderRadius: 999, background: 'rgba(239,68,68,0.18)', border: '1px solid rgba(239,68,68,0.5)', fontWeight: 700, fontSize: '0.9rem' },
  timer: { fontSize: '3.4rem', fontWeight: 900, fontFamily: 'monospace', color: '#fca5a5', letterSpacing: '0.05em' },
  timerLabel: { fontSize: '0.75rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: '#94a3b8', marginBottom: 24 },
  btn: { padding: '14px 36px', fontSize: '1.1rem', fontWeight: 800, borderRadius: 12, border: 'none', cursor: 'pointer', background: '#ef4444', color: '#fff', boxShadow: '0 6px 30px rgba(239,68,68,0.5)' },
};
