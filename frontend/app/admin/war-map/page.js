'use client';
import { useState, useEffect, useRef, useCallback } from 'react';
import { MAP_W, MAP_H, buildWarMap } from '../../components/warMapModel';

/**
 * Operations & Stakeholder situation map — a full-screen facilitator projector.
 *
 * Redesigned: instead of scattering teams onto empty continents (region_id is
 * "" for standard cohorts, so every team piled onto one HQ anchor), it renders
 * the world the simulation models — Muressons' Business Units at their operating
 * hubs (sized by revenue, coloured by health), the five reactive stakeholders at
 * their home regions (coloured by escalation), and the current round's crisis at
 * the place it strikes. Read-only cohort AGGREGATE from /api/admin/war-map.
 */

const CONTINENTS = [
  'M 75,105 L 150,62 L 232,58 L 262,86 L 250,120 L 282,138 L 262,170 L 222,196 L 198,232 L 172,222 L 158,186 L 118,168 L 92,140 Z',
  'M 250,255 L 292,242 L 322,268 L 318,312 L 296,368 L 274,412 L 258,398 L 252,340 L 240,296 Z',
  'M 320,42 L 372,32 L 392,58 L 352,74 L 322,64 Z',
  'M 468,110 L 502,84 L 540,78 L 574,92 L 566,120 L 540,138 L 508,148 L 482,136 Z',
  'M 462,162 L 516,150 L 566,162 L 596,196 L 604,248 L 578,304 L 550,352 L 528,344 L 506,296 L 478,244 L 460,200 Z',
  'M 578,88 L 640,58 L 730,52 L 812,68 L 872,96 L 888,132 L 848,158 L 800,150 L 772,184 L 742,220 L 712,196 L 676,172 L 628,150 L 592,128 Z',
  'M 700,190 L 736,196 L 742,232 L 718,268 L 700,238 Z',
  'M 776,238 L 806,246 L 830,266 L 806,278 L 780,262 Z M 792,292 L 836,286 L 868,296 L 838,308 L 800,304 Z',
  'M 812,332 L 862,324 L 896,348 L 884,388 L 840,398 L 810,372 Z',
  'M 884,120 L 902,108 L 910,132 L 894,146 Z',
];

// A centred text label with a dark pill behind it, so labels stay readable even
// when a marker sits near another marker or a continent edge.
function Label({ x, y, text, size = 10, color = '#cbd5e1', weight = 600 }) {
  const w = String(text).length * size * 0.56 + 10;
  return (
    <g>
      <rect x={x - w / 2} y={y - size + 1} width={w} height={size + 4} rx="3" fill="rgba(3,7,15,0.78)" />
      <text x={x} y={y} textAnchor="middle" fontSize={size} fontWeight={weight} fill={color} fontFamily="var(--font-sans, system-ui, sans-serif)">{text}</text>
    </g>
  );
}

export default function WarMapPage() {
  const [enabled, setEnabled] = useState(false);
  const [model, setModel] = useState({ buNodes: [], shNodes: [], crisis: null, events: [], round: 0, teamCount: 0 });
  const [error, setError] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const pollRef = useRef(null);

  // Hover explainer — a floating card that tells the facilitator exactly what
  // the element under the cursor means in simulation terms.
  const [tip, setTip] = useState(null); // { x, y, title, lines: [] }
  const showTip = (e, title, lines) => setTip({ x: e.clientX, y: e.clientY, title, lines });
  const moveTip = (e) => setTip((t) => (t ? { ...t, x: e.clientX, y: e.clientY } : t));
  const hideTip = () => setTip(null);

  const healthWord = (h) => (h >= 60 ? 'healthy' : h >= 40 ? 'strained' : 'critical');
  const buTipLines = (n) => [
    `One of Muressons' Business Units, plotted at its operating hub. Circle SIZE = its share of group revenue; COLOUR = operational health.`,
    `Health ${n.health}/100 (${healthWord(n.health)}) — a composite of social licence, carbon intensity and staff strain, averaged across all ${model.teamCount || ''} team${model.teamCount === 1 ? '' : 's'} in the cohort.`,
    `SLO ${Math.round(n.slo)}/100 — Social Licence to Operate: the community's ongoing permission for this unit to do business. Low SLO invites activist and regulator pressure.`,
    `CI ${Math.round(n.ci)} — Carbon Intensity: emissions per unit of output. Sustained values above ~120 trigger stranded-asset penalties on the cost of capital.`,
  ];
  const shTipLines = (n) => [
    `One of the five autonomous stakeholders who react to every decision the teams make. The pin sits in their home region; its COLOUR is their current mood.`,
    `Stage: ${n.label.toUpperCase()} — stakeholders escalate calm → watching → agitated → hostile → on strike, and de-escalate when teams rebuild trust.`,
    n.hostile
      ? `${n.hostile} team${n.hostile > 1 ? 's are' : ' is'} currently facing this stakeholder as hostile — expect interventions (penalties, exposés, walkouts) against them.`
      : `No team currently has this stakeholder hostile.`,
    n.escalated ? `The pulsing ring marks an escalated stakeholder — worth naming in the debrief.` : null,
  ].filter(Boolean);
  const crisisTipLines = (c) => [
    `The scripted shock striking the cohort THIS round, shown where it hits in the simulation's world. The red pulse means it is live now.`,
    `Every team faces it simultaneously — how their earlier investments cushion (or amplify) it is the round's teaching point.`,
  ];

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
    fetch('/api/admin/war-map', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status === 401 || r.status === 403 ? 'auth' : 'http'))))
      .then((d) => { setModel(buildWarMap(d)); setError(false); })
      .catch((e) => setError(e && e.message === 'auth' ? 'auth' : 'net'));
  }, []);

  useEffect(() => {
    clearInterval(pollRef.current);
    if (!enabled) return;
    load();
    pollRef.current = setInterval(load, 5000);
    return () => clearInterval(pollRef.current);
  }, [enabled, load]);

  return (
    <div style={S.page}>
      <div style={S.header}>
        <div>
          <div style={S.brand}>MURESSONS GLOBAL OPERATIONS MAP</div>
          <div style={S.sub}>
            {model.round ? `ROUND ${model.round}` : 'LIVE'} · {model.teamCount} TEAM{model.teamCount === 1 ? '' : 'S'} · {model.cohortName ? `“${model.cohortName}”` : 'COHORT AGGREGATE'}
          </div>
          <div style={S.explain}>
            The cohort&apos;s world at a glance: each circle is a Business Unit (size = revenue, colour = health),
            each pin one of the five reactive stakeholders (colour = mood), and the red pulse is this round&apos;s crisis.
            Hover anything for what it means.
          </div>
        </div>
        <label style={S.switchWrap} title="Controls this screen's projection only — players and other screens are unaffected">
          <span style={{ fontSize: 'var(--type-caption)', color: '#64748b', fontWeight: 700, letterSpacing: '0.08em' }}>PROJECT ON THIS SCREEN</span>
          <span style={{ fontSize: '0.8rem', color: '#8899a6', fontWeight: 700 }}>{enabled ? 'ON' : 'OFF'}</span>
          <span style={{ ...S.switch, background: enabled ? 'var(--kpi-good)' : 'rgba(148,163,184,0.3)' }} onClick={toggle}>
            <span style={{ ...S.knob, transform: enabled ? 'translateX(24px)' : 'translateX(0)' }} />
          </span>
        </label>
      </div>

      {!enabled ? (
        <div style={S.center}>
          <div style={{ fontSize: '3rem', marginBottom: 10 }}>🗺️</div>
          <div style={{ fontSize: '1.1rem', color: '#8899a6' }}>Situation map is off. Flip the switch to project the operations board.</div>
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
      ) : (
        <>
          <svg viewBox={`0 0 ${MAP_W} ${MAP_H}`} style={S.map} aria-label="Muressons operations and stakeholder situation map">
            {Array.from({ length: 11 }, (_, i) => (
              <line key={`v${i}`} x1={i * 100} y1="0" x2={i * 100} y2={MAP_H} stroke="rgba(45,212,191,0.06)" strokeWidth="1" />
            ))}
            {Array.from({ length: 6 }, (_, i) => (
              <line key={`h${i}`} x1="0" y1={i * 100} x2={MAP_W} y2={i * 100} stroke="rgba(45,212,191,0.06)" strokeWidth="1" />
            ))}
            {CONTINENTS.map((d, i) => (
              <path key={i} d={d} fill="rgba(148,163,184,0.09)" stroke="rgba(148,163,184,0.22)" strokeWidth="1" />
            ))}

            {/* Live crisis — pulses at the place it strikes this round */}
            {model.crisis && (
              <g style={{ cursor: 'help' }}
                 onMouseEnter={(e) => showTip(e, `Round ${model.crisis.round} crisis — ${model.crisis.name}`, crisisTipLines(model.crisis))}
                 onMouseMove={moveTip} onMouseLeave={hideTip}>
                {!reducedMotion
                  ? <circle cx={model.crisis.x} cy={model.crisis.y} r="10" fill="none" stroke="#ef4444" strokeWidth="2" className="wm-pulse" />
                  : <circle cx={model.crisis.x} cy={model.crisis.y} r="26" fill="none" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="4 4" />}
                <circle cx={model.crisis.x} cy={model.crisis.y} r="4" fill="#ef4444" />
                <Label x={model.crisis.x} y={model.crisis.y + 30} text={`R${model.crisis.round} · ${model.crisis.name}`} size={10} weight={700} color="#fca5a5" />
              </g>
            )}

            {/* Business units — size = revenue, colour = health */}
            {model.buNodes.map((n) => (
              <g key={n.id} style={{ cursor: 'help' }}
                 onMouseEnter={(e) => showTip(e, `Muressons ${n.label} — operating hub`, buTipLines(n))}
                 onMouseMove={moveTip} onMouseLeave={hideTip}>
                <circle cx={n.x} cy={n.y} r={n.r} fill={n.color} fillOpacity="0.26" stroke={n.color} strokeWidth="1.5" />
                <text x={n.x} y={n.y + 3} textAnchor="middle" fontSize="9" fontWeight="800" fill="#e2e8f0" fontFamily="var(--font-mono, monospace)">{n.health}</text>
                <Label x={n.x} y={n.y + n.r + 13} text={n.label} size={10} weight={600} color="#e2e8f0" />
                <Label x={n.x} y={n.y + n.r + 25} text={`SLO ${Math.round(n.slo)} · CI ${Math.round(n.ci)}`} size={8} weight={400} color="#94a3b8" />
              </g>
            ))}

            {/* Stakeholders — pin colour = escalation state */}
            {model.shNodes.map((n) => (
              <g key={n.id} style={{ cursor: 'help' }}
                 onMouseEnter={(e) => showTip(e, `${n.name} — reactive stakeholder`, shTipLines(n))}
                 onMouseMove={moveTip} onMouseLeave={hideTip}>
                {n.escalated && !reducedMotion && (
                  <circle cx={n.x} cy={n.y} r="8" fill="none" stroke={n.color} strokeWidth="1.5" className="wm-pulse-s" />
                )}
                <path d={`M ${n.x} ${n.y + 12} l 6 -12 l -12 0 z`} fill={n.color} />
                <circle cx={n.x} cy={n.y} r="5" fill={n.color} stroke="#04060c" strokeWidth="1" />
                <Label x={n.x} y={n.y + 26} text={n.name} size={9.5} weight={500} color="#f1f5f9" />
                <Label x={n.x} y={n.y + 37} text={`${n.label}${n.hostile ? ` · ${n.hostile}` : ''}`} size={8} weight={500} color={n.color} />
              </g>
            ))}
          </svg>

          <div style={S.footer}>
            <div style={S.legend}>
              <span title="Health ≥ 60/100 — the unit's social licence, carbon intensity and staff strain are all under control."><span style={{ ...S.dot, background: '#2dd4bf' }} /> healthy</span>
              <span title="Health 40–59/100 — at least one pressure (social licence, carbon, burnout) is building. Watch this unit."><span style={{ ...S.dot, background: '#f59e0b' }} /> strained</span>
              <span title="Health < 40/100 — the unit is in trouble: expect stakeholder escalations and financial penalties if unaddressed."><span style={{ ...S.dot, background: '#ef4444' }} /> critical</span>
              <span style={{ marginLeft: 14 }} title="Each circle is one of Muressons' Business Units at its operating hub. Bigger circle = larger share of group revenue. The number inside is its health score /100.">● unit (size = revenue, colour = health)</span>
              <span style={{ marginLeft: 10 }} title="Each pin is one of the five autonomous stakeholders (regulator, investor, journalist, activist, employee). They escalate calm → watching → agitated → hostile → on strike in response to team decisions.">▲ stakeholder (colour = escalation)</span>
            </div>
            <div style={S.eventStrip} title="Live situation feed — the round's crisis, units under stress, and stakeholder escalations, most urgent first.">
              {model.events.length > 0
                ? model.events.slice(0, 6).map((e, i) => <span key={i} style={S.eventItem}>⚠ {e}</span>)
                : <span style={{ color: '#475569' }}>All units healthy · no stakeholder escalations.</span>}
            </div>
          </div>

          {/* Floating hover explainer */}
          {tip && (
            <div style={{
              position: 'fixed',
              left: Math.min(tip.x + 16, (typeof window !== 'undefined' ? window.innerWidth : 1200) - 356),
              top: Math.min(tip.y + 14, (typeof window !== 'undefined' ? window.innerHeight : 800) - 220),
              width: 340, zIndex: 1000, pointerEvents: 'none',
              background: 'rgba(4,8,16,0.96)', border: '1px solid rgba(45,212,191,0.35)',
              borderRadius: 10, padding: '12px 14px', boxShadow: '0 8px 30px rgba(0,0,0,0.55)',
            }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 800, color: '#2dd4bf', marginBottom: 6, letterSpacing: '0.03em' }}>{tip.title}</div>
              {tip.lines.map((l, i) => (
                <div key={i} style={{ fontSize: 'var(--type-caption)', color: '#cbd5e1', lineHeight: 1.5, marginBottom: i < tip.lines.length - 1 ? 6 : 0 }}>{l}</div>
              ))}
            </div>
          )}
        </>
      )}

      <style>{`
        @keyframes wm-pulse { 0% { r: 10; opacity: 0.9; } 100% { r: 40; opacity: 0; } }
        .wm-pulse { animation: wm-pulse 1.8s ease-out infinite; }
        @keyframes wm-pulse-s { 0% { r: 8; opacity: 0.8; } 100% { r: 20; opacity: 0; } }
        .wm-pulse-s { animation: wm-pulse-s 1.8s ease-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .wm-pulse, .wm-pulse-s { animation: none !important; }
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
  explain: { fontSize: '0.76rem', color: '#8899a6', marginTop: 6, maxWidth: 720, lineHeight: 1.5 },
  switchWrap: { display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', userSelect: 'none' },
  switch: { position: 'relative', width: 52, height: 28, borderRadius: 14, transition: 'background 0.2s', display: 'inline-block' },
  knob: { position: 'absolute', top: 3, left: 3, width: 22, height: 22, borderRadius: '50%', background: '#fff', transition: 'transform 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.4)' },
  center: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', textAlign: 'center' },
  map: { width: '100%', maxHeight: '72vh', display: 'block', border: '1px solid rgba(45,212,191,0.12)', borderRadius: 12, background: 'rgba(2,6,14,0.5)' },
  footer: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 20, marginTop: 12, flexWrap: 'wrap' },
  legend: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 'var(--type-caption)', color: '#8899a6', flexWrap: 'wrap' },
  dot: { display: 'inline-block', width: 10, height: 10, borderRadius: '50%', marginLeft: 10 },
  eventStrip: { display: 'flex', gap: 18, fontSize: 'var(--type-caption)', fontFamily: 'var(--font-mono, monospace)', color: '#fbbf24', overflow: 'hidden', whiteSpace: 'nowrap' },
  eventItem: { whiteSpace: 'nowrap' },
};
