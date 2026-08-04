/**
 * ESGLeadershipProfile — WOW-12
 *
 * A branded one-page profile at game-over showing:
 * - Archetype badge and title
 * - SVG radar chart showing 5-pillar strategy emphasis
 * - "Strongest dimension" and "Biggest missed opportunity" callouts
 * - M_R breakdown
 * - Downloadable as PNG (SVG→canvas→PNG, same pattern as FrontPageReveal)
 *
 * SAFETY: Pure presentation. Reads existing data from the game-over payload
 * and existing mrJourney/RegretMeter data. No backend changes.
 *
 * Props:
 *   data         — game-over data object (terminal_value, regenerative_multiple, etc.)
 *   flags        — active_event_flags from globalState
 *   sessionId    — for settings fetch
 *   cohortName   — team/cohort display name
 *   businessUnits — BU state array
 */
'use client';
import React, { useMemo, useCallback, useRef, useState, useEffect } from 'react';
import styles from './ESGLeadershipProfile.module.css';
import { currencySymbol } from '../utils/format';

/** The 5 ESG dimensions for the radar chart */
const PILLARS = [
  { id: 'climate_resilience', label: 'Climate Resilience', icon: '🌡️' },
  { id: 'governance',         label: 'Governance',         icon: '⚖️' },
  { id: 'social_impact',      label: 'Social Impact',      icon: '👥' },
  { id: 'environmental',      label: 'Environmental',      icon: '🌍' },
  { id: 'innovation',         label: 'Innovation',         icon: '💡' },
];

/**
 * Default ESG signal weights — MUST stay in sync with backend
 * admin_shared.DEFAULT_ESG_WEIGHTS. Lead facilitators / super admins can
 * override these (ESG Profile Weights sub-tab); the profile deep-merges any
 * override over these defaults so partial configs are always safe.
 */
export const DEFAULT_ESG_WEIGHTS = {
  climate_resilience: {
    resilience_factor: 1.0, resilience_bonus: 100, climate_leader: 70,
    adaptation_premium: 70, carbon_transition: 60,
  },
  governance: {
    base: 48, materiality_governance: 300, truth_premium: 260,
    materiality_aligned: 10, instability_penalty: 100, reputation_blend: 0.3,
  },
  social_impact: {
    social_license_blend: 0.6, reputation_blend: 0.4, community_champion: 70,
    just_transition: 70, workforce: 60, wellbeing: 60, social_regeneration: 55,
    community_trust: 55, employee_champion: 55, just_transition_passed: 6,
    burnout_penalty: 0.4, social_collapse_penalty: 100,
  },
  environmental: {
    decarbonisation: 1.0, carbon_transition: 70, climate_leader: 40,
    stranded_asset_penalty: 100,
  },
  innovation: {
    base: 30, rd_multiplier: 2, rd_cap: 40, synergy: 200,
    brsr_pioneer: 30, brsr_steward: 30, brsr_laggard: 30,
  },
};

/** Deep-merge a (possibly partial) weights override over the defaults. */
export function mergeEsgWeights(override) {
  const out = {};
  for (const dim of Object.keys(DEFAULT_ESG_WEIGHTS)) {
    out[dim] = { ...DEFAULT_ESG_WEIGHTS[dim] };
    const o = override && override[dim];
    if (o && typeof o === 'object') {
      for (const k of Object.keys(DEFAULT_ESG_WEIGHTS[dim])) {
        if (Number.isFinite(Number(o[k]))) {
          let v = Number(o[k]);
          // Blends are shares of a dimension's baseline; outside [0,1] they
          // invert the complement term's sign. Mirror the backend clamp.
          if (k.endsWith('_blend')) v = Math.max(0, Math.min(1, v));
          out[dim][k] = v;
        }
      }
    }
  }
  return out;
}

const _num = (v, d = 0) => (Number.isFinite(Number(v)) ? Number(v) : d);
const _clamp = (v) => Math.max(0, Math.min(100, v));
const _avg = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null);

/**
 * Compute the 5 ESG dimension scores (0-100) from the player's ACTUAL end-state
 * performance, not flag trivia. Sources: per-BU social licence, carbon
 * intensity, staff burnout; group reputation; R&D intensity; the climate-
 * resilience factor; and the sim's own Regenerative-Multiple breakdown (the
 * components it actually rewards). The previous version keyed off ~10 boolean
 * flags — 6 of which the engine never sets and the rest under different names —
 * so every dimension but one was structurally stuck at 0%.
 */
function computePillarScores(data = {}, flags = {}, businessUnits = [], weights = null) {
  const W = mergeEsgWeights(weights);
  const bus = Array.isArray(businessUnits) ? businessUnits : [];
  const bd = data.mr_breakdown || {};
  const b = (k) => _num(bd[k], 0);           // signed M_R contribution (may be absent)

  const avgSLbu = _avg(bus.map((x) => _num(x.social_license_score, 50)));
  const avgSocial = data.avg_social_license != null ? _num(data.avg_social_license) : (avgSLbu != null ? avgSLbu : 50);
  const ciVals = bus.map((x) => _num(x.carbon_intensity, null)).filter((x) => x != null && Number.isFinite(x));
  const avgCI = ciVals.length ? _avg(ciVals) : (data.avg_carbon_intensity != null ? _num(data.avg_carbon_intensity) : null);
  const avgBurn = _avg(bus.map((x) => _num(x.staff_burnout_index, 0))) ?? 0;
  const reputation = _num(data.group_reputation, 50);
  const crf = data.climate_resilience_factor != null ? _num(data.climate_resilience_factor) * 100 : 50;
  const rd = _num(data.rd_allocation_pct, 0);

  // 1. Climate Resilience — resilience factor + earned climate/adaptation rewards
  const wc = W.climate_resilience;
  const climate = crf * wc.resilience_factor
    + b('resilience_bonus') * wc.resilience_bonus + b('climate_leader') * wc.climate_leader
    + b('adaptation_premium') * wc.adaptation_premium + b('carbon_transition') * wc.carbon_transition;

  // 2. Governance — materiality/transparency rewards, alignment, instability
  //    penalty, lightly anchored to reputation (stakeholder trust).
  const wg = W.governance;
  const governance = (1 - wg.reputation_blend) * (wg.base
      + b('materiality_governance') * wg.materiality_governance + b('truth_premium') * wg.truth_premium
      + (flags.materiality_aligned ? wg.materiality_aligned : 0)
      + b('instability_discount') * wg.instability_penalty)   // instability_discount is negative
    + wg.reputation_blend * reputation;

  // 3. Social Impact — social licence + reputation baseline, workforce/community
  //    rewards, burnout & social-collapse penalties.
  const ws = W.social_impact;
  const social = ws.social_license_blend * avgSocial + ws.reputation_blend * reputation
    + b('community_champion_bonus') * ws.community_champion + b('just_transition_bonus') * ws.just_transition
    + b('workforce_bonus') * ws.workforce + b('wellbeing_bonus') * ws.wellbeing
    + b('social_regeneration') * ws.social_regeneration + b('community_trust') * ws.community_trust
    + b('employee_champion') * ws.employee_champion
    + (data.just_transition_passed ? ws.just_transition_passed : 0)
    - Math.max(0, avgBurn - 40) * ws.burnout_penalty
    + b('social_collapse') * ws.social_collapse_penalty;      // social_collapse is negative

  // 4. Environmental — decarbonisation (lower carbon intensity is better) +
  //    earned transition rewards, stranded-asset penalty.
  const we = W.environmental;
  const carbonScore = avgCI != null ? _clamp(100 - avgCI) : 55;
  const environmental = carbonScore * we.decarbonisation
    + b('carbon_transition') * we.carbon_transition + b('climate_leader') * we.climate_leader
    + b('stranded_asset_penalty') * we.stranded_asset_penalty;  // stranded_asset_penalty is negative

  // 5. Innovation — R&D intensity + synergy / integration rewards. All three
  //    BRSR tiers count: pioneer (+0.65) and steward (+0.35) add credit; the
  //    laggard penalty (−0.30) is negative in the breakdown, so adding it
  //    subtracts.
  const wi = W.innovation;
  const innovation = wi.base
    + Math.min(wi.rd_cap, rd * wi.rd_multiplier)
    + b('synergy_bonus') * wi.synergy + b('brsr_pioneer_bonus') * wi.brsr_pioneer
    + b('brsr_steward_bonus') * wi.brsr_steward
    + b('brsr_laggard_penalty') * wi.brsr_laggard;

  const raw = {
    climate_resilience: climate,
    governance,
    social_impact: social,
    environmental,
    innovation,
  };
  return PILLARS.map((p) => ({ ...p, score: Math.round(_clamp(raw[p.id])) }));
}

/** SVG radar chart coordinates */
function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = (angleDeg - 90) * (Math.PI / 180);
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function RadarChart({ scores, size = 200 }) {
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size / 2 - 34;
  // Horizontal room so the left/right dimension labels (e.g. "⚖️ Governance")
  // aren't clipped at the SVG edge. The viewBox is widened symmetrically and the
  // rendered width matches, so the chart stays centred and undistorted.
  const padX = 48;
  const n = scores.length;
  const angleStep = 360 / n;

  // Background rings
  const rings = [0.25, 0.5, 0.75, 1.0];

  // Data polygon
  const dataPoints = scores.map((s, i) => {
    const r = (s.score / 100) * maxR;
    return polarToCartesian(cx, cy, r, i * angleStep);
  });
  const dataPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ') + ' Z';

  return (
    <svg width={size + padX * 2} height={size} viewBox={`${-padX} 0 ${size + padX * 2} ${size}`}>
      {/* Background rings */}
      {rings.map((pct, i) => (
        <polygon
          key={i}
          points={Array.from({ length: n }, (_, j) => {
            const p = polarToCartesian(cx, cy, maxR * pct, j * angleStep);
            return `${p.x},${p.y}`;
          }).join(' ')}
          fill="none"
          stroke="rgba(148,163,184,0.12)"
          strokeWidth={1}
        />
      ))}

      {/* Axis lines */}
      {scores.map((_, i) => {
        const p = polarToCartesian(cx, cy, maxR, i * angleStep);
        return <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="rgba(148,163,184,0.08)" strokeWidth={1} />;
      })}

      {/* Data polygon */}
      <polygon
        points={dataPoints.map(p => `${p.x},${p.y}`).join(' ')}
        fill="rgba(99, 102, 241, 0.15)"
        stroke="#6366f1"
        strokeWidth={2}
      />
      {dataPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={4} fill="#6366f1" stroke="#1e1b4b" strokeWidth={1.5} />
      ))}

      {/* Labels */}
      {scores.map((s, i) => {
        const labelR = maxR + 16;
        const p = polarToCartesian(cx, cy, labelR, i * angleStep);
        return (
          <text
            key={i}
            x={p.x}
            y={p.y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="var(--text-muted, #94a3b8)"
            fontSize={8}
            fontWeight={700}
          >
            {s.icon} {s.label}
          </text>
        );
      })}
    </svg>
  );
}

export default function ESGLeadershipProfile({ data = {}, flags = {}, sessionId, cohortName, businessUnits }) {
  const [downloading, setDownloading] = useState(false);
  const containerRef = useRef(null);

  const mr = Number(data.regenerative_multiple) || 0;
  const tvM = ((Number(data.terminal_value) || 0) / 1_000_000).toFixed(1);
  const sharePrice = data.price_per_share != null ? Number(data.price_per_share).toFixed(2) : '—';
  const archetype = data.profile_title || data.profile || 'Strategic Leader';

  // Load the facilitator-configured ESG signal weights (falls back to defaults).
  const [esgWeights, setEsgWeights] = useState(null);
  useEffect(() => {
    const API = process.env.NEXT_PUBLIC_API_URL || '';
    const q = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    fetch(`${API}/api/admin/global-settings${q}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((s) => { if (s && s.esg_profile_weights) setEsgWeights(s.esg_profile_weights); })
      .catch(() => {});
  }, [sessionId]);

  const pillarScores = useMemo(
    () => computePillarScores(data, flags, businessUnits, esgWeights),
    [data, flags, businessUnits, esgWeights]
  );
  const strongest = useMemo(() => {
    const sorted = [...pillarScores].sort((a, b) => b.score - a.score);
    return sorted[0];
  }, [pillarScores]);
  const weakest = useMemo(() => {
    const sorted = [...pillarScores].sort((a, b) => a.score - b.score);
    return sorted[0];
  }, [pillarScores]);

  const avgScore = useMemo(() => {
    const sum = pillarScores.reduce((s, p) => s + p.score, 0);
    return Math.round(sum / pillarScores.length);
  }, [pillarScores]);

  // PNG export (same SVG→canvas→PNG pattern as FrontPageReveal)
  const handleDownload = useCallback(() => {
    setDownloading(true);
    const W = 800, H = 1000;
    const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Build radar polygon for SVG export
    const cx = 400, cy = 480, maxR = 120;
    const n = pillarScores.length;
    const angleStep = 360 / n;
    const dataPoints = pillarScores.map((s, i) => {
      const r = (s.score / 100) * maxR;
      const rad = (i * angleStep - 90) * (Math.PI / 180);
      return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
    });
    const polyPoints = dataPoints.map(p => `${p.x},${p.y}`).join(' ');

    // Ring backgrounds
    const rings = [0.25, 0.5, 0.75, 1.0].map(pct => {
      const pts = Array.from({ length: n }, (_, j) => {
        const rad = (j * angleStep - 90) * (Math.PI / 180);
        return `${cx + maxR * pct * Math.cos(rad)},${cy + maxR * pct * Math.sin(rad)}`;
      }).join(' ');
      return `<polygon points="${pts}" fill="none" stroke="rgba(148,163,184,0.2)" stroke-width="1"/>`;
    }).join('');

    const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#0f172a"/>
  <rect x="0" y="0" width="${W}" height="6" fill="#6366f1"/>
  <text x="${W / 2}" y="50" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" font-weight="700" fill="#6366f1" letter-spacing="0.15em">ESG LEADERSHIP PROFILE</text>
  <text x="${W / 2}" y="90" text-anchor="middle" font-family="system-ui,sans-serif" font-size="28" font-weight="900" fill="#f1f5f9">${esc(archetype)}</text>
  <text x="${W / 2}" y="120" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" fill="#94a3b8">${esc(cohortName || 'Muressons Global Corporation')}</text>
  <line x1="60" y1="140" x2="${W - 60}" y2="140" stroke="rgba(148,163,184,0.2)" stroke-width="1"/>
  <text x="100" y="180" font-family="monospace" font-size="16" font-weight="900" fill="#10b981">M_R: ${mr.toFixed(2)}×</text>
  <text x="300" y="180" font-family="monospace" font-size="16" font-weight="900" fill="#3b82f6">TV: ${currencySymbol()}${tvM}M</text>
  <text x="520" y="180" font-family="monospace" font-size="16" font-weight="900" fill="#f59e0b">Share: ${currencySymbol()}${sharePrice}</text>
  <text x="100" y="220" font-family="system-ui,sans-serif" font-size="12" font-weight="700" fill="#94a3b8">Avg Pillar Score: ${avgScore}/100</text>
  <line x1="60" y1="240" x2="${W - 60}" y2="240" stroke="rgba(148,163,184,0.15)" stroke-width="1"/>
  <text x="${W / 2}" y="280" text-anchor="middle" font-family="system-ui,sans-serif" font-size="13" font-weight="800" fill="#818cf8" letter-spacing="0.1em">STRATEGY RADAR</text>
  ${rings}
  <polygon points="${polyPoints}" fill="rgba(99,102,241,0.2)" stroke="#6366f1" stroke-width="2"/>
  ${pillarScores.map((s, i) => {
    const labelR = maxR + 25;
    const rad = (i * angleStep - 90) * (Math.PI / 180);
    const lx = cx + labelR * Math.cos(rad);
    const ly = cy + labelR * Math.sin(rad);
    return `<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="middle" font-family="system-ui,sans-serif" font-size="10" font-weight="700" fill="#94a3b8">${esc(s.label)} (${s.score}%)</text>`;
  }).join('')}
  <line x1="60" y1="650" x2="${W - 60}" y2="650" stroke="rgba(148,163,184,0.15)" stroke-width="1"/>
  <text x="100" y="690" font-family="system-ui,sans-serif" font-size="12" font-weight="800" fill="#10b981">STRONGEST: ${esc(strongest?.label || '—')} (${strongest?.score || 0}%)</text>
  <text x="100" y="720" font-family="system-ui,sans-serif" font-size="12" font-weight="800" fill="#ef4444">OPPORTUNITY: ${esc(weakest?.label || '—')} (${weakest?.score || 0}%)</text>
  ${pillarScores.map((s, i) => {
    const y = 770 + i * 30;
    const barW = (s.score / 100) * 400;
    return `
      <text x="100" y="${y}" font-family="system-ui,sans-serif" font-size="11" fill="#94a3b8">${esc(s.label)}</text>
      <rect x="250" y="${y - 10}" width="400" height="14" rx="3" fill="rgba(148,163,184,0.1)"/>
      <rect x="250" y="${y - 10}" width="${barW}" height="14" rx="3" fill="#6366f1" opacity="0.7"/>
      <text x="660" y="${y}" font-family="monospace" font-size="11" font-weight="700" fill="#f1f5f9">${s.score}%</text>
    `;
  }).join('')}
  <text x="${W / 2}" y="${H - 20}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="10" fill="#475569">Muressons Global Command · ESG Leadership Profile</text>
</svg>`.trim();

    const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = W; c.height = H;
      c.getContext('2d').drawImage(img, 0, 0); URL.revokeObjectURL(url);
      c.toBlob((b) => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(b);
        a.download = `ESG_Leadership_Profile_${archetype.replace(/\s+/g, '_')}.png`;
        a.click();
        setDownloading(false);
      }, 'image/png');
    };
    img.onerror = () => { setDownloading(false); };
    img.src = url;
  }, [pillarScores, mr, tvM, sharePrice, archetype, cohortName, avgScore, strongest, weakest]);

  return (
    <div className={styles.container} ref={containerRef}>
      <div className={styles.header}>
        <span className={styles.headerIcon}>🎓</span>
        <span className={styles.headerTitle}>Your ESG Leadership Profile</span>
      </div>

      {/* Radar Chart */}
      <div className={styles.radarWrapper}>
        <RadarChart scores={pillarScores} size={220} />
      </div>

      {/* Pillar scores */}
      <div className={styles.pillarGrid}>
        {pillarScores.map(p => (
          <div key={p.id} className={styles.pillarCard}>
            <div className={styles.pillarIcon}>{p.icon}</div>
            <div className={styles.pillarLabel}>{p.label}</div>
            <div className={styles.pillarBar}>
              <div
                className={styles.pillarBarFill}
                style={{
                  width: `${p.score}%`,
                  background: p.score >= 75 ? '#10b981' : p.score >= 50 ? '#3b82f6' : p.score >= 25 ? '#f59e0b' : '#ef4444',
                }}
              />
            </div>
            <div className={styles.pillarScore}>{p.score}%</div>
          </div>
        ))}
      </div>

      {/* Callouts */}
      <div className={styles.callouts}>
        {strongest && (
          <div className={`${styles.callout} ${styles.calloutStrong}`}>
            <div className={styles.calloutLabel}>Strongest Dimension</div>
            <div className={styles.calloutValue}>{strongest.icon} {strongest.label} ({strongest.score}%)</div>
          </div>
        )}
        {weakest && (
          <div className={`${styles.callout} ${styles.calloutWeak}`}>
            <div className={styles.calloutLabel}>Biggest Opportunity</div>
            <div className={styles.calloutValue}>{weakest.icon} {weakest.label} ({weakest.score}%)</div>
          </div>
        )}
      </div>

      {/* Download */}
      <button className={styles.downloadBtn} onClick={handleDownload} disabled={downloading}>
        {downloading ? '⏳ Generating…' : '📥 Download as PNG'}
      </button>
    </div>
  );
}
