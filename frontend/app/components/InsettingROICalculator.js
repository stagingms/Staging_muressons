'use client';
import { useState, useMemo, useCallback } from 'react';
import { currencySymbol } from '../utils/format';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const YEARS = 5;
const VOLUME = 100_000; // units/yr
const SELL_PRICE = 25;

function calcCumulative(capex, coInvestOpex, greenOpex) {
    // Strategy 1: Green Premium — no upfront CapEx, pay greenOpex forever
    // Strategy 2: Co-Investment — pay capex upfront, then coInvestOpex
    const s1 = Array.from({ length: YEARS + 1 }, (_, yr) => {
        if (yr === 0) return 0;
        return -(greenOpex * VOLUME * yr); // cumulative COGS above baseline
    });
    const s2 = Array.from({ length: YEARS + 1 }, (_, yr) => {
        if (yr === 0) return -capex;
        return -capex - coInvestOpex * VOLUME * yr;
    });
    // Express as cumulative "savings vs baseline" — compare s1 vs s2 savings over time
    // Actually: cumulative profit (revenue fixed, we track cost advantage)
    const baseline = coInvestOpex * VOLUME; // per year if we had zero extra cost
    const s1_cum = Array.from({ length: YEARS + 1 }, (_, yr) => yr === 0 ? 0 : (SELL_PRICE - greenOpex) * VOLUME * yr / 1e6);
    const s2_cum = Array.from({ length: YEARS + 1 }, (_, yr) => yr === 0 ? -capex / 1e6 : -capex / 1e6 + (SELL_PRICE - coInvestOpex) * VOLUME * yr / 1e6);
    return { s1: s1_cum, s2: s2_cum };
}

function LineChart({ s1, s2, breakEvenYr }) {
    const W = 460, H = 220, padL = 52, padTop = 14, padBot = 32, padR = 16;
    const cW = W - padL - padR, cH = H - padTop - padBot;
    const allVals = [...s1, ...s2];
    const minV = Math.min(...allVals), maxV = Math.max(...allVals);
    const range = maxV - minV || 1;

    const toX = yr => padL + (yr / YEARS) * cW;
    const toY = v => padTop + cH - ((v - minV) / range) * cH;
    const zeroY = toY(0);

    const pathStr = (data, closed = false) => {
        return data.map((v, i) => `${i === 0 ? 'M' : 'L'} ${toX(i).toFixed(1)} ${toY(v).toFixed(1)}`).join(' ');
    };
    const fmtM = v => `${v >= 0 ? '' : '-'}${Math.abs(v).toFixed(0)}M`;
    const gridVals = [minV, minV + range * 0.25, minV + range * 0.5, minV + range * 0.75, maxV];

    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%' }}>
            {/* Grid */}
            {gridVals.map((v, i) => {
                const y = toY(v);
                return <g key={i}>
                    <line x1={padL} y1={y} x2={W - padR} y2={y} stroke="#f1f5f9" strokeWidth="1" />
                    <text x={padL - 5} y={y + 3} textAnchor="end" fontSize="9" fill="#94a3b8">{fmtM(v)}</text>
                </g>;
            })}
            {/* Year labels */}
            {Array.from({ length: YEARS + 1 }, (_, i) => (
                <text key={i} x={toX(i)} y={H - padBot + 16} textAnchor="middle" fontSize="9" fill="#94a3b8">{i.toFixed(1)}</text>
            ))}
            {/* Zero line */}
            <line x1={padL} y1={zeroY} x2={W - padR} y2={zeroY} stroke="#334155" strokeWidth="1.5" />
            {/* Strategy 1 (red) */}
            <path d={pathStr(s1)} fill="none" stroke="#dc2626" strokeWidth="2.5" strokeLinejoin="round" />
            {s1.map((v, i) => <circle key={i} cx={toX(i)} cy={toY(v)} r="4" fill="#dc2626" />)}
            {/* Strategy 2 (green) */}
            <path d={pathStr(s2)} fill="none" stroke="#16a34a" strokeWidth="2.5" strokeLinejoin="round" />
            {s2.map((v, i) => <circle key={i} cx={toX(i)} cy={toY(v)} r="4" fill="#16a34a" />)}
            {/* Breakeven marker */}
            {breakEvenYr > 0 && breakEvenYr <= YEARS && (
                <line x1={toX(breakEvenYr)} y1={padTop} x2={toX(breakEvenYr)} y2={H - padBot} stroke="#6366f1" strokeWidth="1.5" strokeDasharray="5 3" />
            )}
            {/* Y axis label */}
            <text x={10} y={H / 2} textAnchor="middle" fontSize="9" fill="#94a3b8" transform={`rotate(-90,10,${H / 2})`}>↑ Cumulative Profit ($M)</text>
        </svg>
    );
}

export default function InsettingROICalculator({ sessionId, onComplete }) {
    const [phase, setPhase] = useState('intro');
    const [capex, setCapex] = useState(2_000_000);
    const [coInvestOpex, setCoInvestOpex] = useState(12);
    const [greenOpex, setGreenOpex] = useState(22);
    const [submitting, setSubmitting] = useState(false);

    const { s1, s2 } = useMemo(() => calcCumulative(capex, coInvestOpex, greenOpex), [capex, coInvestOpex, greenOpex]);
    // Breakeven: first year where s2 > s1
    const breakEvenYr = useMemo(() => {
        for (let yr = 1; yr <= YEARS; yr++) if (s2[yr] >= s1[yr]) return yr;
        return null;
    }, [s1, s2]);
    const roiDelta = ((s2[YEARS] - s1[YEARS]) * 1e6).toFixed(0);
    const paybackStr = breakEvenYr != null ? `${breakEvenYr}.0 Years` : '>5 Years';
    const unitMarginS2 = (SELL_PRICE - coInvestOpex).toFixed(2);

    const handleSubmit = useCallback(async () => {
        setSubmitting(true);
        try {
            await fetch(`${API}/api/admin/${sessionId}/mod7-insetting`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ capex_grant: capex, co_invest_opex: coInvestOpex, green_opex: greenOpex, payback_years: breakEvenYr }),
            });
        } catch { }
        setSubmitting(false);
        onComplete?.();
    }, [capex, coInvestOpex, greenOpex, breakEvenYr, sessionId, onComplete]);

    if (phase === 'intro') return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif" }}>
            <div style={{ background: '#fff', maxWidth: 580, width: '90%', borderRadius: 12, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.35)' }}>
                <div style={{ background: '#14532d', color: '#fff', padding: '1rem 1.5rem' }}>
                    <div style={{ fontSize: '0.6rem', letterSpacing: '0.15em', opacity: 0.6, textTransform: 'uppercase' }}>Module 7 — CFO Directive</div>
                    <h2 style={{ margin: '0.3rem 0 0', fontSize: '1rem', fontWeight: 800 }}>The Insetting Deal Room</h2>
                </div>
                <div style={{ padding: '1.5rem 2rem' }}>
                    <blockquote style={{ borderLeft: '3px solid #16a34a', paddingLeft: '1rem', margin: '0 0 1.25rem', color: '#334155', fontSize: '0.88rem', lineHeight: 1.75, fontStyle: 'italic' }}>
                        "Paying a $12 premium/unit to the Green Pioneer is unsustainable. We are authorising use of the corporate balance sheet to finance capital upgrades for your legacy 'Cheap &amp; Dirty' suppliers.
                        Buy their equipment — secure their low base pricing forever."
                    </blockquote>
                    <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 8, padding: '0.85rem 1rem', marginBottom: '1.25rem', fontSize: '0.82rem', color: '#14532d', lineHeight: 1.75 }}>
                        <strong>The Deal:</strong> Invest $2M in Supplier A's factory. They drop from 4.0 → 1.5 kg CO₂e/unit and lock price at $12/unit for 5 years — vs. paying $22/unit to the Green Pioneer indefinitely.
                        Model the breakeven to decide if the CapEx is worth it.
                    </div>
                    <button onClick={() => setPhase('calculator')} style={{ width: '100%', padding: '0.85rem', background: 'linear-gradient(135deg,#14532d,#15803d)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}>
                        Open Insetting ROI Calculator →
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
                        <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>Scope 3 Insetting ROI Calculator</h2>
                        <div style={{ display: 'flex', gap: '1.2rem', fontSize: '0.72rem' }}>
                            {[['5-YEAR ROI DELTA', `${Number(roiDelta) >= 0 ? '+' : ''}${currencySymbol()}${(Number(roiDelta) / 1e6).toFixed(1)}M`], ['PAYBACK PERIOD', paybackStr], ['UNIT MARGIN (S2)', `${currencySymbol()}${unitMarginS2}`]].map(([k, v]) => (
                                <div key={k} style={{ textAlign: 'center' }}>
                                    <div style={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.06em', fontSize: '0.65rem' }}>{k}</div>
                                    <div style={{ fontWeight: 800, color: Number(roiDelta) >= 0 ? '#16a34a' : '#dc2626' }}>{v}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div style={{ fontSize: '0.73rem', color: '#64748b', marginTop: '0.2rem' }}>
                        {breakEvenYr ? `Strategic Alignment: Co-investment breaks even against premium sourcing in ${paybackStr}.` : 'Co-investment does not break even within 5 years with current parameters.'}
                    </div>
                </div>

                {/* Legend */}
                <div style={{ display: 'flex', gap: '1.5rem', padding: '0.6rem 1.25rem', background: '#fff', borderBottom: '1px solid #f1f5f9', fontSize: '0.78rem' }}>
                    {[['#dc2626', 'Green Premium (Strategy 1)'], ['#16a34a', 'Co-Investment (Strategy 2)']].map(([col, lbl]) => (
                        <div key={lbl} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div style={{ width: 28, height: 3, background: col, borderRadius: 2 }} />
                            <span style={{ color: '#475569' }}>{lbl}</span>
                        </div>
                    ))}
                </div>

                {/* Chart */}
                <div style={{ background: '#fff', margin: '0.75rem', borderRadius: 8, border: '1px solid #e2e8f0', padding: '0.5rem 0.25rem 0' }}>
                    <LineChart s1={s1} s2={s2} breakEvenYr={breakEvenYr} />
                </div>

                {/* Sliders */}
                <div style={{ padding: '0.75rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem 1.25rem' }}>
                    {[
                        { label: 'Upfront CapEx ($)', val: capex, set: setCapex, min: 500_000, max: 5_000_000, step: 100_000, fmt: v => `${currencySymbol()}${(v / 1e6).toFixed(1)}M` },
                        { label: 'Co-Investment OpEx ($/u)', val: coInvestOpex, set: setCoInvestOpex, min: 8, max: 20, step: 0.5, fmt: v => `${currencySymbol()}${v}` },
                        { label: 'Green Premium OpEx ($/u)', val: greenOpex, set: setGreenOpex, min: 15, max: 35, step: 0.5, fmt: v => `${currencySymbol()}${v}` },
                    ].map(sl => (
                        <div key={sl.label}>
                            <div style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 600, marginBottom: '3px', display: 'flex', justifyContent: 'space-between' }}>
                                <span>{sl.label}</span><span style={{ fontWeight: 700 }}>{sl.fmt(sl.val)}</span>
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <input type="range" min={sl.min} max={sl.max} step={sl.step} value={sl.val}
                                    onChange={e => sl.set(Number(e.target.value))} style={{ flex: 1, accentColor: '#16a34a' }} />
                                <div style={{ minWidth: 48, textAlign: 'center', padding: '3px 5px', border: '1px solid #d1d5db', borderRadius: 5, fontSize: '0.75rem', fontWeight: 700 }}>{sl.val.toLocaleString()}</div>
                            </div>
                        </div>
                    ))}
                </div>

                <div style={{ padding: '0 1rem 1rem' }}>
                    <button onClick={handleSubmit} disabled={submitting} style={{ width: '100%', padding: '0.85rem', background: 'linear-gradient(135deg,#14532d,#15803d)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.88rem', cursor: 'pointer' }}>
                        {submitting ? '⏳...' : '✅ Commit Co-Investment Strategy'}
                    </button>
                </div>
            </div>
        </div>
    );
}
