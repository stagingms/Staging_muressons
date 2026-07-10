'use client';
import { useState, useMemo } from 'react';

const PILLARS = [
    { id: 'financial', label: 'Financial', shortLabel: 'Financial', weight: 0.30, color: '#2563eb' },
    { id: 'decarbon', label: 'Decarbonization', shortLabel: 'Decarbon', weight: 0.25, color: '#16a34a' },
    { id: 'risk', label: 'Risk & Integrity', shortLabel: 'Risk', weight: 0.20, color: '#d97706' },
    { id: 'nonmarket', label: 'Non-Market & Circular', shortLabel: 'Circular', weight: 0.25, color: '#8b5cf6' },
];

const TIERS = [
    { min: 85, label: 'TIER 1: MARKET SHAPER', desc: 'Used sustainability as an offensive weapon. Industry dominance achieved.', action: '🏆 Board Action: Industry Dominance Achieved', color: '#16a34a', bg: '#f0fdf4' },
    { min: 66, label: 'TIER 2: TRANSITION LEADER', desc: 'Successfully navigated risks, protected margins. Highly efficient modern business.', action: '🎖 Board Action: Bonuses Awarded', color: '#3b82f6', bg: '#eff6ff' },
    { min: 40, label: 'TIER 3: COMPLIANCE LAGGARD', desc: 'Survived by reacting. Paid green premiums, heavily eroded margins. Losing market share.', action: '⚠ Board Action: CEO Replaced', color: '#d97706', bg: '#fffbeb' },
    { min: 0, label: 'TIER 4: STRANDED ASSET', desc: 'Treated sustainability as PR. Crushed by regulatory taxes and capital markets.', action: '💀 Board Action: Executive Team Terminated', color: '#dc2626', bg: '#fef2f2' },
];

// ── Radar Chart (SVG polygon on 4 axes) ──────────────────────
function RadarChart({ scores, size = 220 }) {
    const padding = 40;
    const fullSize = size + padding * 2;
    const cx = fullSize / 2, cy = fullSize / 2, r = size * 0.36;
    // 4 axes: top=Financial(0°), right=Decarbon(90°), bottom=Risk(180°), left=Circular(270°)
    const angles = [-90, 0, 90, 180]; // degrees from top, clockwise
    const toRad = d => d * Math.PI / 180;

    const axisPoints = angles.map((a, i) => ({
        x: cx + r * Math.cos(toRad(a)),
        y: cy + r * Math.sin(toRad(a)),
        label: PILLARS[i].shortLabel,
        lx: cx + (r + 18) * Math.cos(toRad(a)),  // label positions
        ly: cy + (r + 18) * Math.sin(toRad(a)),
    }));

    const scorePoints = scores.map((s, i) => {
        const frac = s / 100;
        const a = toRad(angles[i]);
        return { x: cx + r * frac * Math.cos(a), y: cy + r * frac * Math.sin(a) };
    });

    const polyPts = scorePoints.map(p => `${p.x},${p.y}`).join(' ');

    // concentric rings at 25%, 50%, 75%, 100%
    const rings = [0.25, 0.5, 0.75, 1.0];

    return (
        <svg viewBox={`0 0 ${fullSize} ${fullSize}`} style={{ width: '100%', maxWidth: fullSize, overflow: 'visible' }}>
            {/* Rings */}
            {rings.map(f => {
                const pts = angles.map(a => {
                    const rad = toRad(a);
                    return `${(cx + r * f * Math.cos(rad)).toFixed(1)},${(cy + r * f * Math.sin(rad)).toFixed(1)}`;
                }).join(' ');
                return <polygon key={f} points={pts} fill="none" stroke="#e2e8f0" strokeWidth="1" />;
            })}
            {/* Axes */}
            {axisPoints.map((p, i) => (
                <line key={i} x1={cx} y1={cy} x2={p.x} y2={p.y} stroke="#e2e8f0" strokeWidth="1" />
            ))}
            {/* Score polygon filled */}
            <polygon points={polyPts} fill="rgba(220,38,38,0.12)" stroke="#dc2626" strokeWidth="2" strokeLinejoin="round" style={{ transition: 'background 0.35s, color 0.35s, border-color 0.35s, box-shadow 0.35s, opacity 0.35s, transform 0.35s' }} />
            {/* Score dots */}
            {scorePoints.map((p, i) => (
                <circle key={i} cx={p.x} cy={p.y} r="4.5" fill={PILLARS[i].color} style={{ transition: 'background 0.35s, color 0.35s, border-color 0.35s, box-shadow 0.35s, opacity 0.35s, transform 0.35s' }} />
            ))}
            {/* Axis labels */}
            {axisPoints.map((p, i) => (
                <text key={i} x={p.lx} y={p.ly + 4} textAnchor="middle" fontSize="10" fill="#475569" fontWeight="600">
                    {p.label}
                </text>
            ))}
        </svg>
    );
}

export default function BalancedScorecardEvaluator({ scores: propScores, readOnly = false }) {
    const [scores, setScores] = useState(propScores ?? [50, 50, 50, 50]);
    const setSc = (i, v) => setScores(prev => { const n = [...prev]; n[i] = Number(v); return n; });

    const weighted = useMemo(() =>
        Math.round(scores.reduce((s, v, i) => s + v * PILLARS[i].weight, 0))
    , [scores]);

    const tier = TIERS.find(t => weighted >= t.min) || TIERS[TIERS.length - 1];

    return (
        <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden', fontFamily: "'DM Sans',sans-serif", maxWidth: 560 }}>
            {/* Header */}
            <div style={{ padding: '0.9rem 1.25rem', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>Board Assessment Scorecard</h2>
                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.72rem' }}>
                    {[['WEIGHTED SCORE', `${weighted}%`], ['STATUS', `${tier.label.split(':')[0]}: ${tier.label.split(': ')[1].split('(')[0]}`]].map(([k, v]) => (
                        <div key={k} style={{ textAlign: 'center' }}>
                            <div style={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.06em' }}>{k}</div>
                            <div style={{ fontWeight: 800, color: k === 'STATUS' ? tier.color : '#0f172a', fontSize: k === 'STATUS' ? '0.78rem' : 'inherit' }}>{v}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Radar + Score */}
            <div style={{ padding: '1rem', background: tier.bg, borderBottom: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <RadarChart scores={scores} size={190} />
                    <div style={{ flex: 1, textAlign: 'center' }}>
                        <div style={{ fontSize: '4rem', fontWeight: 900, color: tier.color, lineHeight: 1 }}>{weighted}%</div>
                        <div style={{ fontSize: '0.85rem', fontWeight: 800, color: tier.color, marginTop: '0.25rem', letterSpacing: '0.03em' }}>
                            {tier.label}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.5rem', lineHeight: 1.6, maxWidth: 180 }}>
                            {tier.desc}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: tier.color, fontWeight: 700, marginTop: '0.5rem' }}>
                            {tier.action}
                        </div>
                    </div>
                </div>
            </div>

            {/* Pillar breakdowns */}
            <div style={{ padding: '0.75rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem 1.25rem' }}>
                {PILLARS.map((p, i) => (
                    <div key={p.id}>
                        <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#475569', marginBottom: '3px', display: 'flex', justifyContent: 'space-between' }}>
                            <span>{p.label} ({Math.round(p.weight * 100)}%)</span>
                            <span style={{ color: p.color, fontWeight: 800 }}>{scores[i]}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <input type="range" min={0} max={100} step={1} value={scores[i]}
                                onChange={e => setSc(i, e.target.value)}
                                disabled={readOnly}
                                style={{ flex: 1, accentColor: p.color }} />
                            <div style={{ minWidth: 38, textAlign: 'center', padding: '3px 5px', border: '1px solid #d1d5db', borderRadius: 5, fontSize: '0.78rem', fontWeight: 700 }}>{scores[i]}</div>
                        </div>
                        {/* Pillar contribution bar */}
                        <div style={{ height: 4, background: '#f1f5f9', borderRadius: 2, marginTop: '3px', overflow: 'hidden' }}>
                            <div style={{ width: `${scores[i]}%`, height: '100%', background: p.color, borderRadius: 2, transition: 'width 0.3s' }} />
                        </div>
                    </div>
                ))}
                {!readOnly && (
                    <div style={{ gridColumn: '1/-1' }}>
                        <button onClick={() => setScores([50, 50, 50, 50])}
                            style={{ width: '100%', padding: '7px', background: '#f1f5f9', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.78rem', cursor: 'pointer', marginTop: '0.25rem' }}>
                            Reset Scores
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
