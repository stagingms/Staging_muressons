'use client';
import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { MAP_W, MAP_H, REGIONS, project, buildMapModel } from '../../components/warMapModel';

/**
 * Region War-Map (W-E / W7) — a full-screen projector view giving the
 * simulation its missing geography. BU/cohort nodes plotted by region,
 * pulsing on active crises, black-swan flashes, and a cyclone that tracks
 * across the Bay of Bengal while any team is in Round 5.
 *
 * Console pattern (same as /admin/trading-floor): its own route, a
 * facilitator ON/OFF switch persisted locally, and READ-ONLY data — it
 * polls the existing /api/admin/leaderboard and touches no game state.
 * Zero player-surface change.
 */

// Low-poly continent silhouettes (equirectangular, 1000×520). Stylised war-room
// cartography, not survey-grade coastlines.
const CONTINENTS = [
  // North America
  'M 75,105 L 150,62 L 232,58 L 262,86 L 250,120 L 282,138 L 262,170 L 222,196 L 198,232 L 172,222 L 158,186 L 118,168 L 92,140 Z',
  // South America
  'M 250,255 L 292,242 L 322,268 L 318,312 L 296,368 L 274,412 L 258,398 L 252,340 L 240,296 Z',
  // Greenland
  'M 320,42 L 372,32 L 392,58 L 352,74 L 322,64 Z',
  // Europe
  'M 468,110 L 502,84 L 540,78 L 574,92 L 566,120 L 540,138 L 508,148 L 482,136 Z',
  // Africa
  'M 462,162 L 516,150 L 566,162 L 596,196 L 604,248 L 578,304 L 550,352 L 528,344 L 506,296 L 478,244 L 460,200 Z',
  // Asia
  'M 578,88 L 640,58 L 730,52 L 812,68 L 872,96 L 888,132 L 848,158 L 800,150 L 772,184 L 742,220 L 712,196 L 676,172 L 628,150 L 592,128 Z',
  // India
  'M 700,190 L 736,196 L 742,232 L 718,268 L 700,238 Z',
  // SE Asia / Indonesia
  'M 776,238 L 806,246 L 830,266 L 806,278 L 780,262 Z M 792,292 L 836,286 L 868,296 L 838,308 L 800,304 Z',
  // Australia
  'M 812,332 L 862,324 L 896,348 L 884,388 L 840,398 L 810,372 Z',
  // Japan
  'M 884,120 L 902,108 L 910,132 L 894,146 Z',
];

const fmtM = (v) => `$${((Number(v) || 0) / 1_000_000).toFixed(1)}M`;

export default function WarMapPage() {
  const [enabled, setEnabled] = useState(false);
  const [model, setModel] = useState({ nodes: [], maxRound: 1, cycloneActive: false, events: [] });
  const [error, setError] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setEnabled(localStorage.getItem('muressons_warmap_enabled') === '1');
      const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
      setReducedMotion(mq.matches);
      const onChange = (e) => setReducedMotion(e.matches);
      mq.addEventListener?.('change', onChange);
      return () => mq.removeEventListener?.('change', onChange);
    }
  }, []);

  const toggle = () => {
    setEnabled((prev) => {
      const next = !prev;
      if (typeof window !== 'undefined') localStorage.setItem('muressons_warmap_enabled', next ? '1' : '0');
      return next;
    });
  };

  const load = useCallback(() => {
    fetch('/api/admin/leaderboard', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('unauth'))))
      .then((d) => { setModel(buildMapModel(d.leaderboard || [])); setError(false); })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    clearInterval(pollRef.current);
    if (!enabled) return;
    load();
    pollRef.current = setInterval(load, 5000);
    return () => clearInterval(pollRef.current);
  }, [enabled, load]);

  const regionAnchors = useMemo(
    () => Object.entries(REGIONS).map(([key, r]) => ({ key, label: r.label, ...project(r.lon, r.lat) })),
    []
  );

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div>
          <div style={S.brand}>MURESSONS GLOBAL SITUATION MAP</div>
          <div style={S.sub}>LIVE · ROUND {model.maxRound} · {model.nodes.length} OPERATING UNIT{model.nodes.length === 1 ? '' : 'S'} ON THE BOARD</div>
        </div>
        <label style={S.switchWrap} title="Facilitator on/off">
          <span style={{ fontSize: '0.8rem', color: '#8899a6', fontWeight: 700 }}>{enabled ? 'ON' : 'OFF'}</span>
          <span style={{ ...S.switch, background: enabled ? 'var(--kpi-good, #10b981)' : 'rgba(148,163,184,0.3)' }} onClick={toggle}>
            <span style={{ ...S.knob, transform: enabled ? 'translateX(24px)' : 'translateX(0)' }} />
          </span>
        </label>
      </div>

      {!enabled ? (
        <div style={S.center}>
          <div style={{ fontSize: '3rem', marginBottom: 10 }}>🗺️</div>
          <div style={{ fontSize: '1.1rem', color: '#8899a6' }}>War map is off. Flip the switch to project the situation board.</div>
        </div>
      ) : error ? (
        <div style={S.center}>
          <div style={{ fontSize: '2rem' }}>🔌</div>
          <div style={{ color: '#8899a6', marginTop: 8 }}>Waiting for the backend / facilitator sign-in…</div>
        </div>
      ) : (
        <>
          <svg viewBox={`0 0 ${MAP_W} ${MAP_H}`} style={S.map} aria-label="World situation map">
            {/* Graticule */}
            {Array.from({ length: 11 }, (_, i) => (
              <line key={`v${i}`} x1={i * 100} y1="0" x2={i * 100} y2={MAP_H} stroke="rgba(45,212,191,0.06)" strokeWidth="1" />
            ))}
            {Array.from({ length: 6 }, (_, i) => (
              <line key={`h${i}`} x1="0" y1={i * 100} x2={MAP_W} y2={i * 100} stroke="rgba(45,212,191,0.06)" strokeWidth="1" />
            ))}
            {/* Continents */}
            {CONTINENTS.map((d, i) => (
              <path key={i} d={d} fill="rgba(148,163,184,0.09)" stroke="rgba(148,163,184,0.22)" strokeWidth="1" />
            ))}
            {/* Region anchors */}
            {regionAnchors.map((r) => (
              <g key={r.key || 'hq'}>
                <circle cx={r.x} cy={r.y} r="3" fill="rgba(45,212,191,0.5)" />
                <text x={r.x} y={r.y - 10} textAnchor="middle" fontSize="10" fill="rgba(45,212,191,0.55)" fontFamily="var(--font-mono, monospace)" letterSpacing="2">{r.label}</text>
              </g>
            ))}
            {/* Cyclone track — R5 theatre across the Bay of Bengal */}
            {model.cycloneActive && (
              <g>
                <path id="cyclone-track" d="M 800,285 C 775,255 748,228 716,205" fill="none" stroke="rgba(96,165,250,0.25)" strokeWidth="2" strokeDasharray="5 5" />
                {!reducedMotion ? (
                  <text fontSize="20" aria-hidden="true">
                    🌀
                    <animateMotion dur="9s" repeatCount="indefinite" rotate="0">
                      <mpath href="#cyclone-track" />
                    </animateMotion>
                  </text>
                ) : (
                  <text x="740" y="230" fontSize="20" aria-hidden="true">🌀</text>
                )}
                <text x="810" y="300" fontSize="9" fill="rgba(96,165,250,0.7)" fontFamily="var(--font-mono, monospace)">CYCLONE WARNING · R5</text>
              </g>
            )}
            {/* Team nodes */}
            {model.nodes.map((n) => (
              <g key={n.id}>
                {n.crises.length > 0 && !reducedMotion && (
                  <circle cx={n.x} cy={n.y} r={n.radius} fill="none" stroke={n.blackSwan ? '#f8fafc' : '#ef4444'} strokeWidth="2" className="wm-pulse" />
                )}
                {n.crises.length > 0 && reducedMotion && (
                  <circle cx={n.x} cy={n.y} r={n.radius + 5} fill="none" stroke={n.blackSwan ? '#f8fafc' : '#ef4444'} strokeWidth="1.5" strokeDasharray="3 3" />
                )}
                <circle cx={n.x} cy={n.y} r={n.radius} fill={n.color} fillOpacity="0.28" stroke={n.color} strokeWidth="1.5" />
                <text x={n.x} y={n.y + 3} textAnchor="middle" fontSize="8" fontWeight="700" fill="#e2e8f0" fontFamily="var(--font-mono, monospace)">R{n.round}</text>
                <text x={n.x} y={n.y + n.radius + 11} textAnchor="middle" fontSize="9" fill="#cbd5e1">{n.name.length > 18 ? `${n.name.slice(0, 17)}…` : n.name}</text>
                <text x={n.x} y={n.y + n.radius + 21} textAnchor="middle" fontSize="7.5" fill="#64748b" fontFamily="var(--font-mono, monospace)">{fmtM(n.tv)}</text>
              </g>
            ))}
          </svg>

          {/* Legend + live crisis ticker */}
          <div style={S.footer}>
            <div style={S.legend}>
              <span style={{ ...S.dot, background: '#2dd4bf' }} /> healthy
              <span style={{ ...S.dot, background: '#f59e0b' }} /> strained
              <span style={{ ...S.dot, background: '#ef4444' }} /> critical
              <span style={{ ...S.dot, background: 'transparent', border: '1.5px solid #ef4444' }} /> crisis pulse
              <span style={{ marginLeft: 6 }}>node size = enterprise value</span>
            </div>
            <div style={S.eventStrip}>
              {model.events.length > 0
                ? model.events.slice(0, 6).map((e, i) => <span key={i} style={S.eventItem}>⚠ {e}</span>)
                : <span style={{ color: '#475569' }}>No active crises on the board.</span>}
            </div>
          </div>
        </>
      )}

      <style>{`
        @keyframes wm-pulse {
          0% { r: 10; opacity: 0.9; }
          100% { r: 34; opacity: 0; }
        }
        .wm-pulse { animation: wm-pulse 1.8s ease-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .wm-pulse { animation: none !important; }
        }
      `}</style>
    </div>
  );
}

const S = {
  page: { minHeight: '100vh', background: 'radial-gradient(ellipse at top, #0b1424 0%, #04060c 100%)', color: '#f1f5f9', padding: '24px 36px', fontFamily: 'var(--font-sans, system-ui, sans-serif)' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  brand: { fontSize: '1.7rem', fontWeight: 900, letterSpacing: '0.08em' },
  sub: { fontSize: '0.8rem', letterSpacing: '0.18em', color: '#2dd4bf', fontWeight: 700, marginTop: 4 },
  switchWrap: { display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', userSelect: 'none' },
  switch: { position: 'relative', width: 52, height: 28, borderRadius: 14, transition: 'background 0.2s', display: 'inline-block' },
  knob: { position: 'absolute', top: 3, left: 3, width: 22, height: 22, borderRadius: '50%', background: '#fff', transition: 'transform 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.4)' },
  center: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', textAlign: 'center' },
  map: { width: '100%', maxHeight: '72vh', display: 'block', border: '1px solid rgba(45,212,191,0.12)', borderRadius: 12, background: 'rgba(2,6,14,0.5)' },
  footer: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 20, marginTop: 12, flexWrap: 'wrap' },
  legend: { display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.72rem', color: '#8899a6' },
  dot: { display: 'inline-block', width: 10, height: 10, borderRadius: '50%', marginLeft: 10 },
  eventStrip: { display: 'flex', gap: 18, fontSize: '0.72rem', fontFamily: 'var(--font-mono, monospace)', color: '#fbbf24', overflow: 'hidden', whiteSpace: 'nowrap' },
  eventItem: { whiteSpace: 'nowrap' },
};
