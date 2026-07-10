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
import React, { useMemo, useCallback, useRef, useState } from 'react';
import styles from './ESGLeadershipProfile.module.css';

/** The 5 strategy pillars for the radar chart */
const PILLARS = [
  {
    id: 'climate_resilience',
    label: 'Climate Resilience',
    icon: '🌡️',
    flags: ['resilience_investment', 'circular_economy_leader'],
  },
  {
    id: 'governance_transparency',
    label: 'Governance',
    icon: '⚖️',
    flags: ['materiality_governance', 'truth_premium'],
  },
  {
    id: 'social_impact',
    label: 'Social Impact',
    icon: '👥',
    flags: ['social_license_rebuilt', 'community_champion', 'just_transition_fund'],
  },
  {
    id: 'environmental_stewardship',
    label: 'Environmental',
    icon: '🌍',
    flags: ['supply_chain_transparency', 'nature_based_solutions'],
  },
  {
    id: 'innovation',
    label: 'Innovation',
    icon: '💡',
    flags: ['circular_economy_leader', 'science_based_targets'],
  },
];

/** Compute pillar scores (0-100) from flags */
function computePillarScores(flags) {
  return PILLARS.map(p => {
    const earned = p.flags.filter(f => !!flags[f]).length;
    const score = p.flags.length > 0 ? Math.round((earned / p.flags.length) * 100) : 0;
    return { ...p, score, earned, total: p.flags.length };
  });
}

/** SVG radar chart coordinates */
function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = (angleDeg - 90) * (Math.PI / 180);
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function RadarChart({ scores, size = 200 }) {
  const cx = size / 2;
  const cy = size / 2;
  const maxR = size / 2 - 30;
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
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
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

  const pillarScores = useMemo(() => computePillarScores(flags), [flags]);
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
  <text x="300" y="180" font-family="monospace" font-size="16" font-weight="900" fill="#3b82f6">TV: $${tvM}M</text>
  <text x="520" y="180" font-family="monospace" font-size="16" font-weight="900" fill="#f59e0b">Share: $${sharePrice}</text>
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
