'use client';
import { useState, useMemo, useCallback } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const PRINCIPAL = 1_000_000_000;
const BASE_RATE = 0.05;
const TERM = 10;

function getTier(score) {
    if (score >= 80) return { label: 'SUSTAINABILITY LEADER', rate: BASE_RATE - 0.0075, color: '#16a34a', tier: 'Greenium -75bp' };
    if (score >= 40) return { label: 'AVERAGE MARKET PERFORMER', rate: BASE_RATE, color: '#3b82f6', tier: 'Standard Market' };
    return { label: 'HIGH TRANSITION RISK', rate: BASE_RATE + 0.015, color: '#dc2626', tier: 'Brown Penalty +150bp' };
}

function ESGGauge({ score }) {
    const W = 260, H = 150, cx = W / 2, cy = H * 0.82, r = 88;
    const toRad = deg => (deg - 180) * Math.PI / 180;
    const pct = score / 100;
    const needleDeg = pct * 180;
    const nr = toRad(needleDeg);
    const nx = cx + (r - 14) * Math.cos(nr), ny = cy + (r - 14) * Math.sin(nr);
    const { color, label } = getTier(score);
    const endRad = toRad(needleDeg);
    const ex = cx + r * Math.cos(endRad), ey = cy + r * Math.sin(endRad);
    const large = needleDeg > 90 ? 1 : 0;
    return (
        <div style={{ textAlign: 'center' }}>
            <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxWidth: W }}>
                {/* Zone arcs */}
                {[['#fecaca', 0, 72], ['#bfdbfe', 72, 144], ['#bbf7d0', 144, 180]].map(([c2, s, e]) => {
                    const sr = toRad(s), er = toRad(e);
                    const sx = cx + r * Math.cos(sr), sy = cy + r * Math.sin(sr);
                    const ex2 = cx + r * Math.cos(er), ey2 = cy + r * Math.sin(er);
                    return <path key={s} d={`M ${sx} ${sy} A ${r} ${r} 0 ${e - s > 90 ? 1 : 0} 1 ${ex2} ${ey2}`} fill="none" stroke={c2} strokeWidth="26" strokeLinecap="round" />;
                })}
                {/* Progress */}
                {pct > 0 && <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`} fill="none" stroke={color} strokeWidth="7" strokeLinecap="round" style={{ transition: 'background 0.35s, color 0.35s, border-color 0.35s, box-shadow 0.35s, opacity 0.35s, transform 0.35s' }} />}
                {/* Needle */}
                <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#1e293b" strokeWidth="2.5" strokeLinecap="round" style={{ transition: 'background 0.35s, color 0.35s, border-color 0.35s, box-shadow 0.35s, opacity 0.35s, transform 0.35s' }} />
                <circle cx={cx} cy={cy} r="5.5" fill="#1e293b" />
                {/* Core */}
                <text x={cx} y={cy - 32} textAnchor="middle" fontSize="28" fontWeight="900" fill={color}
                    style={{ transition: 'fill 0.35s' }}>{score}</text>
                <text x={cx} y={cy - 12} textAnchor="middle" fontSize="9.5" fill="#64748b" letterSpacing="1.5">ESG SCORE</text>
            </svg>

            {/* Tier badge */}
            <div style={{ display: 'inline-block', border: `1.5px solid ${color}`, borderRadius: 20, padding: '3px 14px', fontSize: '0.72rem', fontWeight: 700, color, marginTop: '-8px' }}>
                {label}
            </div>
        </div>
    );
}

function CostBars({ scoreRate, baseRate }) {
    const calc = r => (PRINCIPAL * r * TERM + PRINCIPAL) / 1e6;
    const esgCost = calc(scoreRate), stdCost = calc(baseRate);
    const maxC = Math.max(esgCost, stdCost) * 1.1;
    const W = 400, H = 170, padL = 56, padT = 12, padB = 28, padR = 16;
    const cH = H - padT - padB, barW = 80;
    const gap = (W - padL - padR - barW * 2) / 3;
    const bars = [{ label: 'ESG Strategy', v: esgCost, col: '#2563eb' }, { label: 'Standard Market', v: stdCost, col: '#cbd5e1' }];
    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%' }}>
            {[0, 500, 1000, 1500, 2000].map((v, i) => {
                if (v > maxC * 1.05) return null;
                const y = padT + (1 - v / (maxC)) * cH;
                return <g key={i}>
                    <line x1={padL} y1={y} x2={W - padR} y2={y} stroke="#f1f5f9" strokeWidth="1" />
                    <text x={padL - 4} y={y + 3} textAnchor="end" fontSize="9" fill="#94a3b8">{v}</text>
                </g>;
            })}
            <text x={10} y={H / 2} textAnchor="middle" fontSize="9" fill="#94a3b8" transform={`rotate(-90,10,${H/2})`}>↑ Total Lifetime Cost ($M)</text>
            {bars.map((b, i) => {
                const bH = (b.v / maxC) * cH;
                const x = padL + gap * (i + 1) + barW * i;
                const y = padT + cH - bH;
                return <g key={b.label}>
                    <rect x={x} y={y} width={barW} height={bH} fill={b.col} rx="3" style={{ transition: 'background 0.35s, color 0.35s, border-color 0.35s, box-shadow 0.35s, opacity 0.35s, transform 0.35s' }} />
                    <text x={x + barW / 2} y={y - 5} textAnchor="middle" fontSize="10" fontWeight="700" fill={b.col}>${Math.round(b.v)}M</text>
                    <text x={x + barW / 2} y={H - padB + 15} textAnchor="middle" fontSize="10" fill="#64748b">{b.label}</text>
                </g>;
            })}
        </svg>
    );
}

export default function ESGRefinancingSimulator({ sessionId, onComplete, initialScore }) {
    const [phase, setPhase] = useState('intro');
    const [score, setScore] = useState(initialScore ?? 50);
    const [submitting, setSubmitting] = useState(false);

    const { rate, tier, color } = useMemo(() => getTier(score), [score]);
    const annualInterest = PRINCIPAL * rate;
    const totalCost = annualInterest * TERM + PRINCIPAL;
    const stdTotalCost = PRINCIPAL * BASE_RATE * TERM + PRINCIPAL;
    const impact10y = ((totalCost - stdTotalCost) / 1e6).toFixed(1);
    const saved = Number(impact10y) < 0;

    const handleSubmit = useCallback(async () => {
        setSubmitting(true);
        try {
            await fetch(`${API}/api/admin/${sessionId}/mod9-refinancing`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ esg_score: score, rate, total_cost: totalCost, tier }),
            });
        } catch { }
        setSubmitting(false);
        onComplete?.();
    }, [score, rate, totalCost, tier, sessionId, onComplete]);

    if (phase === 'intro') return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif" }}>
            <div style={{ background: '#fff', maxWidth: 580, width: '90%', borderRadius: 12, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.35)' }}>
                <div style={{ background: '#1e3a5f', color: '#fff', padding: '1rem 1.5rem' }}>
                    <div style={{ fontSize: '0.6rem', letterSpacing: '0.15em', opacity: 0.6, textTransform: 'uppercase' }}>Module 9 — CFO Directive</div>
                    <h2 style={{ margin: '0.3rem 0 0', fontSize: '1rem', fontWeight: 800 }}>The $1 Billion Refinancing</h2>
                </div>
                <div style={{ padding: '1.5rem 2rem' }}>
                    <blockquote style={{ borderLeft: '3px solid #3b82f6', paddingLeft: '1rem', margin: '0 0 1.25rem', color: '#334155', fontSize: '0.87rem', lineHeight: 1.75, fontStyle: 'italic' }}>
                        "Muressons has a <strong>$1,000,000,000 corporate bond maturing this period</strong>. Institutional demand — and your interest rate — will be
                        dictated by your aggregate ESG Rating, which reflects every decision you have made over the last 8 semesters."
                    </blockquote>
                    <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8, padding: '0.85rem 1rem', marginBottom: '1.25rem', fontSize: '0.82rem', lineHeight: 1.75 }}>
                        <strong>Greenium (score ≥80):</strong> −75bp below market · <strong>Standard (40–79):</strong> Base rate · <strong>Brown Penalty (&lt;40):</strong> +150bp premium
                    </div>
                    <button onClick={() => setPhase('simulator')} style={{ width: '100%', padding: '0.85rem', background: 'linear-gradient(135deg,#1e3a5f,#2563eb)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}>
                        Open Capital Markets Desk →
                    </button>
                </div>
            </div>
        </div>
    );

    return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif", padding: '1rem', overflowY: 'auto' }}>
            <div style={{ background: '#f8fafc', maxWidth: 580, width: '100%', borderRadius: 12, boxShadow: '0 30px 80px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
                {/* Header */}
                <div style={{ background: '#fff', padding: '0.9rem 1.5rem', borderBottom: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>ESG Refinancing Simulator</h2>
                        <div style={{ display: 'flex', gap: '1.2rem', fontSize: '0.72rem' }}>
                            {[['BOND PRINCIPAL', '$1.0B'], ['NEW RATE', `${(rate * 100).toFixed(2)}%`], ['10Y IMPACT', `${saved ? '-' : '+'}$${Math.abs(Number(impact10y)).toFixed(1)}M`]].map(([k, v]) => (
                                <div key={k} style={{ textAlign: 'center' }}>
                                    <div style={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.06em', fontSize: '0.68rem' }}>{k}</div>
                                    <div style={{ fontWeight: 800, color: k === '10Y IMPACT' ? (saved ? '#16a34a' : '#dc2626') : '#0f172a' }}>{v}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: saved ? '#16a34a' : '#dc2626', marginTop: '0.2rem', fontWeight: 600 }}>
                        10-Year Financial Impact: You {saved ? `Saved $${Math.abs(Number(impact10y)).toFixed(0)}M` : `Paid $${Math.abs(Number(impact10y)).toFixed(0)}M extra`} compared to market baseline.
                    </div>
                </div>

                {/* ESG Gauge */}
                <div style={{ padding: '0 1rem', background: '#fff' }}>
                    <ESGGauge score={score} />
                </div>

                <hr style={{ margin: '0 1rem', border: 'none', borderTop: '1px solid #f1f5f9' }} />

                {/* Bar chart */}
                <div style={{ background: '#fff', margin: '0.75rem', border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.5rem 0.25rem 0' }}>
                    <CostBars scoreRate={rate} baseRate={BASE_RATE} />
                </div>

                {/* Slider */}
                <div style={{ padding: '0.5rem 1.5rem 1rem' }}>
                    <div style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 600, marginBottom: '4px', display: 'flex', justifyContent: 'space-between' }}>
                        <span>Simulation ESG Score</span><span style={{ color, fontWeight: 800 }}>{score} — {tier}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '1rem' }}>
                        <input type="range" min={0} max={100} step={1} value={score}
                            onChange={e => setScore(Number(e.target.value))} style={{ flex: 1, accentColor: color }} />
                        <div style={{ minWidth: 42, textAlign: 'center', padding: '3px 6px', border: '1px solid #d1d5db', borderRadius: 5, fontSize: '0.85rem', fontWeight: 700, color }}>{score}</div>
                    </div>
                    <button onClick={handleSubmit} disabled={submitting}
                        style={{ width: '100%', padding: '0.85rem', background: score >= 80 ? 'linear-gradient(135deg,#15803d,#16a34a)' : score >= 40 ? 'linear-gradient(135deg,#1e3a5f,#2563eb)' : 'linear-gradient(135deg,#b91c1c,#dc2626)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.88rem', cursor: 'pointer' }}>
                        {submitting ? '⏳...' : `✅ Secure Financing at ${(rate * 100).toFixed(2)}% (${tier})`}
                    </button>
                </div>
            </div>
        </div>
    );
}
