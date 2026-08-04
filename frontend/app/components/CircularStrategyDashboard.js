'use client';
import { useState, useMemo, useCallback } from 'react';
import { currencySymbol } from '../utils/format';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const SALE_UNITS = 10_000;   // units sold per year (max market)
const MFG_COST = 80_000;     // cost to manufacture 1 unit
const YEARS = 15;

function calcCircular({ transitionYrs, annualLease, recovery }) {
    // year-by-year annual cash flow
    const cashFlows = [];
    const fleetByYear = [];
    let fleet = 0;

    for (let yr = 1; yr <= YEARS; yr++) {
        // Units entering the lease fleet per year (ramp up over transition period)
        const newUnits = yr <= transitionYrs
            ? Math.round(SALE_UNITS / transitionYrs)
            : 0;

        fleet = Math.min(fleet + newUnits, SALE_UNITS);
        fleetByYear.push(fleet);

        const leaseRevenue = fleet * annualLease;
        // Manufacturing cost: reduced by recovery rate on recycled units
        const recycledUnits = yr > 3 ? Math.round(fleet * 0.1 * recovery) : 0; // returns start after 3 yrs
        const virginUnits = newUnits - Math.min(recycledUnits, newUnits);
        const mfgCost = virginUnits * MFG_COST * 0.001; // scaled down for readability ($M)
        const reverseLogistics = recycledUnits * 500 * 0.001; // $500/unit recovery cost
        const cf = (leaseRevenue - mfgCost * 1e3 - reverseLogistics * 1e3) / 1e6;
        cashFlows.push(cf);
    }
    return { cashFlows, fleetByYear };
}

function AreaChart({ cashFlows }) {
    const W = 520, H = 160, padL = 44, padT = 14, padB = 28, padR = 16;
    const cW = W - padL - padR, cH = H - padT - padB;
    const minV = Math.min(...cashFlows, 0);
    const maxV = Math.max(...cashFlows, 0);
    const range = maxV - minV || 1;
    const toX = i => padL + (i / (YEARS - 1)) * cW;
    const toY = v => padT + cH - ((v - minV) / range) * cH;
    const zeroY = toY(0);
    const pts = cashFlows.map((v, i) => [toX(i), toY(v)]);
    const polyline = pts.map(([x, y]) => `${x},${y}`).join(' ');
    const area = `M ${padL},${zeroY} ` + pts.map(([x, y]) => `L ${x},${y}`).join(' ') + ` L ${padL + cW},${zeroY} Z`;
    const gridVals = [minV, minV + range * 0.33, minV + range * 0.66, maxV];
    const lastV = cashFlows[YEARS - 1];

    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%' }}>
            {/* Grid */}
            {gridVals.map((v, i) => {
                const y = toY(v);
                return <g key={i}>
                    <line x1={padL} y1={y} x2={W - padR} y2={y} stroke="#f1f5f9" strokeWidth="1" />
                    <text x={padL - 5} y={y + 3} textAnchor="end" fontSize="9" fill="#94a3b8">{Math.round(v)}</text>
                </g>;
            })}
            {/* Zero */}
            <line x1={padL} y1={zeroY} x2={W - padR} y2={zeroY} stroke="#334155" strokeWidth="1.5" />
            {/* Area */}
            <path d={area} fill="rgba(59,130,246,0.15)" />
            {/* Line */}
            <polyline points={polyline} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinejoin="round"
                style={{ transition: 'background 0.35s, color 0.35s, border-color 0.35s, box-shadow 0.35s, opacity 0.35s, transform 0.35s' }} />
            {/* Year labels */}
            {[1, 3, 5, 7, 9, 11, 13, 15].map(yr => (
                <text key={yr} x={toX(yr - 1)} y={H - padB + 16} textAnchor="middle" fontSize="8" fill="#94a3b8">{yr}</text>
            ))}
            {/* Last value label */}
            <text x={W - padR - 4} y={toY(lastV) - 4} textAnchor="end" fontSize="9" fontWeight="700" fill="#2563eb">Yr 15: {currencySymbol()}{Math.round(lastV)}M</text>
            {/* Y axis */}
            <text x={10} y={H / 2} textAnchor="middle" fontSize="8" fill="#94a3b8" transform={`rotate(-90,10,${H/2})`}>↑ Annual Cash Flow ($M)</text>
            {/* X axis label */}
            <text x={W / 2} y={H} textAnchor="middle" fontSize="8" fill="#94a3b8">Year →</text>
        </svg>
    );
}

function FleetBars({ fleetByYear }) {
    const maxU = Math.max(...fleetByYear, 1);
    const W = 520, H = 110, padL = 36, padT = 16, padB = 28, padR = 16;
    const cW = W - padL - padR, cH = H - padT - padB;
    const barW = cW / YEARS * 0.7;
    const gap = cW / YEARS;
    const colFn = (v) => v >= maxU * 0.85 ? '#166534' : v >= maxU * 0.5 ? '#15803d' : '#86efac';
    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%' }}>
            {fleetByYear.map((v, i) => {
                const bH = (v / maxU) * cH;
                const x = padL + i * gap + gap * 0.15;
                const y = padT + cH - bH;
                return <g key={i}>
                    <rect x={x} y={y} width={barW} height={bH} fill={colFn(v)} rx="2" style={{ transition: 'background 0.35s, color 0.35s, border-color 0.35s, box-shadow 0.35s, opacity 0.35s, transform 0.35s' }} />
                    {i % 2 === 0 && <text x={x + barW / 2} y={y - 3} textAnchor="middle" fontSize="7" fill="#166534" fontWeight="700">{v.toLocaleString()}</text>}
                    <text x={x + barW / 2} y={H - padB + 14} textAnchor="middle" fontSize="8" fill="#94a3b8">{i + 1}</text>
                </g>;
            })}
            <text x={10} y={H / 2} textAnchor="middle" fontSize="8" fill="#94a3b8" transform={`rotate(-90,10,${H/2})`}>↑ Fleet</text>
            <text x={W / 2} y={H} textAnchor="middle" fontSize="8" fill="#94a3b8">Year</text>
        </svg>
    );
}

export default function CircularStrategyDashboard({ sessionId, onComplete }) {
    const [phase, setPhase] = useState('intro');
    const [transitionYrs, setTransitionYrs] = useState(3);
    const [annualLease, setAnnualLease] = useState(25_000);
    const [recovery, setRecovery] = useState(0.4);
    const [submitting, setSubmitting] = useState(false);

    const { cashFlows, fleetByYear } = useMemo(() => calcCircular({ transitionYrs, annualLease, recovery }), [transitionYrs, annualLease, recovery]);
    const valleyDuration = useMemo(() => cashFlows.filter(v => v < 0).length, [cashFlows]);
    const maxDeficit = Math.abs(Math.min(...cashFlows, 0)).toFixed(1);
    const yr15cf = cashFlows[YEARS - 1];
    const yr15margin = yr15cf > 0 ? ((yr15cf / ((fleetByYear[YEARS - 1] * annualLease) / 1e6)) * 100).toFixed(1) : '0';
    const phaseLabel = valleyDuration === 0 ? 'Stable' : valleyDuration <= 2 ? 'Transitioning' : 'High Risk Valley';

    const handleSubmit = useCallback(async () => {
        setSubmitting(true);
        try {
            await fetch(`${API}/api/admin/${sessionId}/mod10-circular`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transition_years: transitionYrs, annual_lease: annualLease, recovery_rate: recovery, valley_duration: valleyDuration }),
            });
        } catch { }
        setSubmitting(false);
        onComplete?.();
    }, [transitionYrs, annualLease, recovery, valleyDuration, sessionId, onComplete]);

    if (phase === 'intro') return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif" }}>
            <div style={{ background: '#fff', maxWidth: 600, width: '90%', borderRadius: 12, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.35)' }}>
                <div style={{ background: '#14532d', color: '#fff', padding: '1rem 1.5rem' }}>
                    <div style={{ fontSize: '0.6rem', letterSpacing: '0.15em', opacity: 0.6, textTransform: 'uppercase' }}>Module 10 — Chairman's Final Mandate</div>
                    <h2 style={{ margin: '0.3rem 0 0', fontSize: '1rem', fontWeight: 800 }}>The Circular Economy Transition</h2>
                </div>
                <div style={{ padding: '1.5rem 2rem' }}>
                    <blockquote style={{ borderLeft: '3px solid #16a34a', paddingLeft: '1rem', margin: '0 0 1.25rem', color: '#334155', fontSize: '0.87rem', lineHeight: 1.8, fontStyle: 'italic' }}>
                        "Congratulations. You survived the carbon taxes, the NGO scandals, and the debt refinancing.
                        But you are still digging raw materials out of the earth, turning them into products, and watching them go to landfills.
                        <strong>The Board demands a 2035 Master Plan.</strong> Transition your flagship division from
                        'Take-Make-Waste' to <strong>'Product-as-a-Service'</strong>. You are no longer selling products — you are leasing outcomes."
                    </blockquote>
                    <div style={{ background: '#fef9c3', border: '1px solid #fde047', borderRadius: 8, padding: '0.85rem 1rem', marginBottom: '1.25rem', fontSize: '0.82rem', color: '#713f12', lineHeight: 1.7 }}>
                        ⚠ <strong>Beware the Valley of Death:</strong> When you switch from upfront sales to recurring leases, short-term revenue plummets while manufacturing costs remain high. If you didn't secure cheap ESG debt in Module 9, you risk bankruptcy before reaching the circular utopia.
                    </div>
                    <button onClick={() => setPhase('dashboard')} style={{ width: '100%', padding: '0.85rem', background: 'linear-gradient(135deg,#14532d,#15803d)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}>
                        Open Circular Strategy Dashboard →
                    </button>
                </div>
            </div>
        </div>
    );

    return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif", padding: '1rem', overflowY: 'auto' }}>
            <div style={{ background: '#f8fafc', maxWidth: 600, width: '100%', borderRadius: 12, boxShadow: '0 30px 80px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
                {/* Header */}
                <div style={{ background: '#fff', padding: '0.9rem 1.5rem', borderBottom: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>Circular Strategy Dashboard</h2>
                        <div style={{ display: 'flex', gap: '1.2rem', fontSize: '0.72rem' }}>
                            {[['VALLEY DURATION', `${valleyDuration} Years`], ['MAX DEFICIT', `${currencySymbol()}${maxDeficit}M`], ['YR 15 MARGIN', `${yr15margin}%`]].map(([k, v]) => (
                                <div key={k} style={{ textAlign: 'center' }}>
                                    <div style={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.06em', fontSize: '0.68rem' }}>{k}</div>
                                    <div style={{ fontWeight: 800, color: k === 'VALLEY DURATION' && valleyDuration > 5 ? '#dc2626' : '#0f172a' }}>{v}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: valleyDuration > 5 ? '#dc2626' : '#16a34a', marginTop: '0.2rem', fontWeight: 600 }}>
                        Phase: {phaseLabel}. {maxDeficit !== '0' ? `Maximum liquidity gap of ${currencySymbol()}${maxDeficit}M in Year ${cashFlows.indexOf(Math.min(...cashFlows)) + 1}.` : 'Clean transition — no negative cash flow.'}
                    </div>
                </div>

                {/* Cash flow area chart */}
                <div style={{ background: '#fff', margin: '0.75rem 0.75rem 0', border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.5rem 0.25rem 0' }}>
                    <AreaChart cashFlows={cashFlows} />
                </div>

                {/* Fleet bar chart */}
                <div style={{ background: '#fff', margin: '0 0.75rem', border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.5rem 0.25rem 0' }}>
                    <FleetBars fleetByYear={fleetByYear} />
                </div>

                {/* Sliders */}
                <div style={{ padding: '0.75rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.6rem 1.25rem' }}>
                    {[
                        { label: 'Transition (Years)', val: transitionYrs, set: setTransitionYrs, min: 1, max: 10, step: 1, fmt: v => `${v}` },
                        { label: 'Annual Lease ($)', val: annualLease, set: setAnnualLease, min: 10_000, max: 60_000, step: 1000, fmt: v => v.toLocaleString() },
                        { label: 'Recovery Investment', val: recovery, set: setRecovery, min: 0.1, max: 0.9, step: 0.05, fmt: v => v.toFixed(2) },
                    ].map(sl => (
                        <div key={sl.label}>
                            <div style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 600, marginBottom: '3px', display: 'flex', justifyContent: 'space-between' }}>
                                <span>{sl.label}</span><span style={{ fontWeight: 700 }}>{sl.fmt(sl.val)}</span>
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <input type="range" min={sl.min} max={sl.max} step={sl.step} value={sl.val}
                                    onChange={e => sl.set(Number(e.target.value))} style={{ flex: 1, accentColor: '#15803d' }} />
                                <div style={{ minWidth: 44, textAlign: 'center', padding: '3px 5px', border: '1px solid #d1d5db', borderRadius: 5, fontSize: '0.75rem', fontWeight: 700 }}>{sl.fmt(sl.val)}</div>
                            </div>
                        </div>
                    ))}
                </div>

                <div style={{ padding: '0 1rem 1rem' }}>
                    <button onClick={handleSubmit} disabled={submitting}
                        style={{ width: '100%', padding: '0.85rem', background: valleyDuration > 5 ? 'linear-gradient(135deg,#b91c1c,#dc2626)' : 'linear-gradient(135deg,#14532d,#15803d)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.88rem', cursor: 'pointer' }}>
                        {submitting ? '⏳...' : valleyDuration > 5 ? '⚠ Submit (High Bankruptcy Risk)' : '✅ Submit Circular Transition Plan'}
                    </button>
                </div>
            </div>
        </div>
    );
}
