'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import { RIVAL, rivalBenchmarkEV } from '../../components/rivalIntel';

/**
 * Trading-Floor Finale (Feature 1) — a full-screen projector view for the room.
 * Live ticker + ranked board of every team by Enterprise Value, plus a "Ring
 * the Bell" close that freezes the board, reveals the final ranking, and fires
 * a market_close broadcast so every player screen reacts. Presentation-only —
 * it reads the existing leaderboard and touches no game state.
 *
 * A facilitator ON/OFF switch (persisted) keeps it dormant until you want it.
 * Open this on the room's main screen:  /admin/trading-floor
 */

const fmtM = (v) => `$${((Number(v) || 0) / 1_000_000).toFixed(2)}M`;

function bell() {
  // Self-contained "closing bell" via Web Audio — no asset needed.
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ctx = new AC();
    [880, 1174.7, 1568].forEach((f, i) => {
      const o = ctx.createOscillator(); const g = ctx.createGain();
      o.type = 'sine'; o.frequency.value = f;
      o.connect(g); g.connect(ctx.destination);
      const t = ctx.currentTime + i * 0.12;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.3, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 1.1);
      o.start(t); o.stop(t + 1.15);
    });
  } catch { /* audio not available — silent */ }
}

export default function TradingFloorPage() {
  const [enabled, setEnabled] = useState(false);
  const [teams, setTeams] = useState([]);
  const [closed, setClosed] = useState(false);
  const [error, setError] = useState(false);
  // WOW-2E: Staggered reveal state
  const [revealedRows, setRevealedRows] = useState(new Set());
  const [revealComplete, setRevealComplete] = useState(false);
  const pollRef = useRef(null);

  // Restore the facilitator's on/off preference.
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setEnabled(localStorage.getItem('muressons_finale_enabled') === '1');
    }
  }, []);
  const toggle = () => {
    setEnabled((prev) => {
      const next = !prev;
      if (typeof window !== 'undefined') localStorage.setItem('muressons_finale_enabled', next ? '1' : '0');
      if (!next) setClosed(false);
      return next;
    });
  };

  // F-9 (v3): distinguish "signed out" (fix: sign in, reload) from "backend
  // down" (fix: check the server). error is false | 'auth' | 'net'.
  const load = useCallback(() => {
    fetch('/api/admin/leaderboard', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status === 401 || r.status === 403 ? 'auth' : 'http'))))
      .then((d) => {
        const rows = (d.leaderboard || []).filter((x) => x.player_name || x.parent_cohort_id);
        rows.sort((a, b) => (b.terminal_value || 0) - (a.terminal_value || 0));
        setTeams(rows);
        setError(false);
      })
      .catch((e) => setError(e && e.message === 'auth' ? 'auth' : 'net'));
  }, []);

  // Poll the live leaderboard while enabled and not yet closed.
  useEffect(() => {
    clearInterval(pollRef.current);
    if (!enabled || closed) return;
    load();
    pollRef.current = setInterval(load, 5000);
    return () => clearInterval(pollRef.current);
  }, [enabled, closed, load]);

  const ringBell = useCallback(() => {
    const cohortId = teams.find((t) => t.parent_cohort_id)?.parent_cohort_id || 'cohort';
    fetch(`/api/admin/${encodeURIComponent(cohortId)}/finale/ring-bell`, { method: 'POST', credentials: 'include' })
      .catch(() => { /* still close the local view even if broadcast fails */ });
    bell();
    setClosed(true);
    // WOW-2E: Staggered reveal — animate from last place to first
    const sorted = [...teams];
    sorted.sort((a, b) => (b.terminal_value || 0) - (a.terminal_value || 0));
    const reversed = [...sorted].reverse(); // last place first
    reversed.forEach((t, i) => {
      setTimeout(() => {
        setRevealedRows(prev => new Set([...prev, t.session_id || i]));
        if (i === reversed.length - 1) {
          setTimeout(() => setRevealComplete(true), 600);
        }
      }, 200 * (i + 1));
    });
  }, [teams]);

  const maxTv = Math.max(1, ...teams.map((t) => t.terminal_value || 0));
  // W-B (W2c): Nordhaven NPC benchmark — presentation-only estimate from the
  // engine's competitor growth model. Greyed, unranked, excluded from medals,
  // reveal sequence and the winner highlight.
  const maxRound = Math.max(1, ...teams.map((t) => t.round_number || 1));
  const rivalEV = rivalBenchmarkEV(maxRound);
  const rivalAfterIdx = teams.filter((t) => (t.terminal_value || 0) >= rivalEV).length;
  const rivalRow = (
    <div key="npc-nordhaven" style={{ ...S.row, opacity: 0.55, border: '1px dashed rgba(148,163,184,0.35)', background: 'rgba(148,163,184,0.05)' }}>
      <span style={{ ...S.rank, fontSize: '1rem', color: '#8899a6' }}>—</span>
      <span style={{ ...S.team, color: '#8899a6' }}>{RIVAL.avatar} {RIVAL.name.toUpperCase()} <span style={{ fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.08em' }}>· NPC BENCHMARK</span></span>
      <div style={S.barTrack}>
        <div style={{ ...S.barFill, width: `${Math.min(100, (rivalEV / maxTv) * 100)}%`, background: 'rgba(148,163,184,0.45)' }} />
      </div>
      <span style={{ ...S.value, color: '#8899a6' }}>{fmtM(rivalEV)} <span style={{ fontSize: '0.6rem' }}>EST</span></span>
    </div>
  );
  const medal = (i) => (i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`);
  const IPO_PRICE = 50; // Fixed IPO starting share price

  return (
    <div style={S.page}>
      {/* Header + switch */}
      <div style={S.header}>
        <div>
          <div style={S.brand}>MURESSONS GLOBAL EXCHANGE</div>
          <div style={S.sub}>{closed ? 'MARKET CLOSED · YEAR 5 FINAL RANKING' : 'LIVE · ENTERPRISE VALUE'}</div>
        </div>
        {/* F-9 (v3): scope truth — the switch governs this tab's projection only. */}
        <label style={S.switchWrap} title="Controls this screen's projection only — players and other screens are unaffected">
          <span style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 700, letterSpacing: '0.08em' }}>PROJECT ON THIS SCREEN</span>
          <span style={{ fontSize: '0.8rem', color: '#8899a6', fontWeight: 700 }}>{enabled ? 'ON' : 'OFF'}</span>
          <span style={{ ...S.switch, background: enabled ? 'var(--kpi-good, #10b981)' : 'rgba(148,163,184,0.3)' }} onClick={toggle}>
            <span style={{ ...S.knob, transform: enabled ? 'translateX(24px)' : 'translateX(0)' }} />
          </span>
        </label>
      </div>

      {!enabled ? (
        <div style={S.center}>
          <div style={{ fontSize: '3rem', marginBottom: 10 }}>🔕</div>
          <div style={{ fontSize: '1.1rem', color: '#8899a6' }}>Trading Floor is off. Flip the switch to project the room finale.</div>
        </div>
      ) : error ? (
        <div style={S.center}>
          <div style={{ fontSize: '2rem' }}>{error === 'auth' ? '🔒' : '🔌'}</div>
          <div style={{ color: '#8899a6', marginTop: 8 }}>
            {error === 'auth'
              ? 'Signed out — sign in on the Facilitator Dashboard in another tab, then reload this one.'
              : 'Backend unreachable — retrying every 5 seconds…'}
          </div>
        </div>
      ) : teams.length === 0 ? (
        <div style={S.center}><div style={{ color: '#8899a6' }}>No active teams yet.</div></div>
      ) : (
        <>
          {/* Scrolling ticker */}
          <div style={S.tickerWrap}>
            <div style={S.ticker}>
              {[...teams, ...teams].map((t, i) => (
                <span key={i} style={S.tickItem}>
                  <strong style={{ color: '#e2e8f0' }}>{t.player_name || t.cohort_name || 'Team'}</strong>
                  <span style={{ color: 'var(--kpi-good, #10b981)', marginLeft: 8 }}>{fmtM(t.terminal_value)} ▲</span>
                </span>
              ))}
            </div>
          </div>

          {/* Ranked board */}
          <div style={S.board}>
            {teams.map((t, i) => {
              const isWinner = closed && i === 0;
              const showRivalBefore = i === rivalAfterIdx; // W-B: NPC row slots in by EV
              const isRevealed = !closed || revealedRows.has(t.session_id || i);
              const sharePrice = Number(t.price_per_share) || 0;
              const ipoDelta = sharePrice - IPO_PRICE;
              const deltaColor = ipoDelta >= 0 ? 'var(--kpi-good, #10b981)' : '#ef4444';
              const deltaArrow = ipoDelta >= 0 ? '▲' : '▼';

              return (
                <div key={`wrap-${t.session_id || i}`} style={{ display: 'contents' }}>
                {showRivalBefore && rivalRow}
                <div
                  style={{
                    ...S.row,
                    ...(isWinner && revealComplete ? S.winner : {}),
                    opacity: closed && !isRevealed ? 0 : 1,
                    transform: closed && !isRevealed ? 'translateY(20px)' : 'translateY(0)',
                    transition: 'all 0.5s ease',
                  }}
                >
                  <span style={S.rank}>{closed ? medal(i) : `#${i + 1}`}</span>
                  <span style={S.team}>{t.player_name || t.cohort_name || 'Team'}</span>
                  <div style={S.barTrack}>
                    <div style={{ ...S.barFill, width: `${((t.terminal_value || 0) / maxTv) * 100}%` }} />
                  </div>
                  <span style={S.value}>{fmtM(t.terminal_value)}</span>
                  {/* WOW-2E: IPO delta */}
                  {closed && sharePrice > 0 && (
                    <span style={{ ...S.ipoDelta, color: deltaColor }}>
                      ${IPO_PRICE} → ${sharePrice.toFixed(2)} {deltaArrow}
                    </span>
                  )}
                </div>
                </div>
              );
            })}
            {rivalAfterIdx === teams.length && rivalRow}
          </div>

          {/* Bell */}
          <div style={{ textAlign: 'center', marginTop: 24 }}>
            {!closed ? (
              <button style={S.bellBtn} onClick={ringBell}>🔔 Ring the Closing Bell</button>
            ) : (
              <div style={S.closedBanner}>🔔 MARKET CLOSED — the numbers are final.</div>
            )}
          </div>
        </>
      )}

      <style>{`
        @keyframes mur-ticker { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
        @keyframes mur-confetti {
          0% { transform: translateY(0) rotate(0deg); opacity: 1; }
          100% { transform: translateY(120vh) rotate(720deg); opacity: 0; }
        }
        @keyframes mur-winner-pulse {
          0%, 100% { box-shadow: 0 0 24px rgba(16,185,129,0.35); }
          50% { box-shadow: 0 0 40px rgba(16,185,129,0.5); }
        }
      `}</style>
      {/* WOW-2E: CSS Confetti for winner */}
      {revealComplete && (
        <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 999, overflow: 'hidden' }}>
          {Array.from({ length: 40 }, (_, i) => (
            <div key={i} style={{
              position: 'absolute',
              top: -20,
              left: `${Math.random() * 100}%`,
              width: `${6 + Math.random() * 8}px`,
              height: `${6 + Math.random() * 8}px`,
              borderRadius: Math.random() > 0.5 ? '50%' : '2px',
              background: ['#10b981', '#f59e0b', '#6366f1', '#3b82f6', '#ec4899', '#f43f5e'][i % 6],
              animation: `mur-confetti ${2 + Math.random() * 3}s linear ${Math.random() * 1.5}s forwards`,
              opacity: 0.9,
            }} />
          ))}
        </div>
      )}
    </div>
  );
}

const S = {
  page: { minHeight: '100vh', background: 'radial-gradient(ellipse at top, #0f172a 0%, #05070d 100%)', color: '#f1f5f9', padding: '28px 40px', fontFamily: 'var(--font-sans, system-ui, sans-serif)' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  brand: { fontSize: '2rem', fontWeight: 900, letterSpacing: '0.06em' },
  sub: { fontSize: '0.85rem', letterSpacing: '0.18em', color: 'var(--accent-gold, #f59e0b)', fontWeight: 700, marginTop: 4 },
  switchWrap: { display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', userSelect: 'none' },
  switch: { position: 'relative', width: 52, height: 28, borderRadius: 14, transition: 'background 0.2s', display: 'inline-block' },
  knob: { position: 'absolute', top: 3, left: 3, width: 22, height: 22, borderRadius: '50%', background: '#fff', transition: 'transform 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.4)' },
  center: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', textAlign: 'center' },
  tickerWrap: { overflow: 'hidden', whiteSpace: 'nowrap', borderTop: '1px solid rgba(148,163,184,0.2)', borderBottom: '1px solid rgba(148,163,184,0.2)', padding: '8px 0', marginBottom: 24, background: 'rgba(0,0,0,0.3)' },
  ticker: { display: 'inline-block', animation: 'mur-ticker 30s linear infinite', fontFamily: 'var(--font-mono, monospace)', fontSize: '1rem' },
  tickItem: { marginRight: 48 },
  board: { maxWidth: 900, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 10 },
  row: { display: 'grid', gridTemplateColumns: '60px 1fr 3fr 130px', alignItems: 'center', gap: 14, padding: '12px 16px', borderRadius: 12, background: 'rgba(22,30,46,0.7)', border: '1px solid rgba(148,163,184,0.12)' },
  winner: { border: '1px solid var(--kpi-good, #10b981)', animation: 'mur-winner-pulse 2s ease infinite', background: 'rgba(16,185,129,0.08)' },
  rank: { fontSize: '1.4rem', fontWeight: 900, textAlign: 'center' },
  team: { fontSize: '1.1rem', fontWeight: 700, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  barTrack: { height: 12, borderRadius: 6, background: 'rgba(148,163,184,0.15)', overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 6, background: 'linear-gradient(90deg, var(--accent-blue, #3b82f6), var(--kpi-good, #10b981))', transition: 'width 0.8s ease' },
  value: { fontFamily: 'var(--font-mono, monospace)', fontWeight: 800, textAlign: 'right', color: 'var(--kpi-good, #10b981)' },
  bellBtn: { padding: '14px 32px', fontSize: '1.15rem', fontWeight: 800, borderRadius: 12, border: 'none', cursor: 'pointer', background: 'linear-gradient(135deg, var(--accent-gold, #f59e0b), #d97706)', color: '#1a1005', boxShadow: '0 6px 24px rgba(245,158,11,0.4)' },
  closedBanner: { display: 'inline-block', padding: '14px 32px', fontSize: '1.15rem', fontWeight: 800, borderRadius: 12, background: 'rgba(16,185,129,0.12)', color: 'var(--kpi-good, #10b981)', border: '1px solid var(--kpi-good, #10b981)' },
  ipoDelta: { fontFamily: 'var(--font-mono, monospace)', fontWeight: 700, fontSize: '0.85rem', whiteSpace: 'nowrap' },
};
