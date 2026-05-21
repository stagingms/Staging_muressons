'use client';
import { useState, useMemo, useCallback } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

// Supplier profiles
const SUPPLIERS = [
    { id: 'a', label: 'Supplier A (Low Cost)', co2: 4.2, cost: 10.0, color: '#6b7280' },
    { id: 'b', label: 'Supplier B (Transition)', co2: 2.1, cost: 15.5, color: '#3b82f6' },
    { id: 'c', label: 'Supplier C (Eco-Lead)', co2: 0.3, cost: 22.0, color: '#16a34a' },
];
const TOTAL_UNITS = 100_000;
const THRESHOLD_CO2 = 2.0; // kg/unit mega-client limit
const REVENUE_PER_UNIT = 25; // $

function SemiGauge({ value, max, redAbove, label, unit, w = 200 }) {
    const h = w * 0.6;
    const cx = w / 2, cy = h * 0.85, r = w * 0.36;
    const toRad = deg => (deg - 180) * Math.PI / 180;
    const pct = Math.min(value / max, 1);
    const needleDeg = pct * 180;
    const nr = toRad(needleDeg);
    const nx = cx + (r - 12) * Math.cos(nr);
    const ny = cy + (r - 12) * Math.sin(nr);
    const overThreshold = redAbove ? value > redAbove : false;
    const col = overThreshold ? '#dc2626' : '#16a34a';
    const arcX1 = cx - r, arcX2 = cx + r;

    return (
        <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%' }}>
            {/* Background track */}
            <path d={`M ${arcX1} ${cy} A ${r} ${r} 0 0 1 ${arcX2} ${cy}`}
                fill="none" stroke="#e2e8f0" strokeWidth="22" strokeLinecap="round" />
            {/* Filled arc */}
            {(() => {
                const endRad = toRad(needleDeg);
                const ex = cx + r * Math.cos(endRad), ey = cy + r * Math.sin(endRad);
                const large = needleDeg > 90 ? 1 : 0;
                return <path d={`M ${arcX1} ${cy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`}
                    fill="none" stroke={col} strokeWidth="22" strokeLinecap="round" />;
            })()}
            {/* Threshold marker */}
            {redAbove && (() => {
                const tp = redAbove / max, td = tp * 180;
                const tr = toRad(td), tx = cx + (r + 14) * Math.cos(tr), ty = cy + (r + 14) * Math.sin(tr);
                const ti = cx + (r - 14) * Math.cos(tr), tiy = cy + (r - 14) * Math.sin(tr);
                return <line x1={tx} y1={ty} x2={ti} y2={tiy} stroke="#dc2626" strokeWidth="2.5" />;
            })()}
            {/* Needle */}
            <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#1e293b" strokeWidth="2" strokeLinecap="round"
                style={{ transition: 'background 0.3s ease-out, color 0.3s ease-out, border-color 0.3s ease-out, box-shadow 0.3s ease-out, opacity 0.3s ease-out, transform 0.3s ease-out' }} />
            <circle cx={cx} cy={cy} r="5" fill="#1e293b" />
            {/* Center value */}
            <text x={cx} y={cy - r * 0.35} textAnchor="middle" fontSize={w * 0.13} fontWeight="800" fill={col}
                style={{ transition: 'fill 0.3s' }}>
                {typeof value === 'number' ? value.toFixed(2) : value}
            </text>
            <text x={cx} y={cy - r * 0.15} textAnchor="middle" fontSize={w * 0.07} fill="#94a3b8" letterSpacing="1.5"
                style={{ textTransform: 'uppercase' }}>{label}</text>
        </svg>
    );
}

function BarChart3({ cogs, profit, revenue }) {
    const vals = [{ label: 'COGS', v: cogs, col: '#94a3b8' }, { label: 'Profit', v: profit, col: '#16a34a' }, { label: 'Revenue', v: revenue, col: '#3b82f6' }];
    const maxV = Math.max(...vals.map(v => Math.abs(v.v))) * 1.15 || 1;
    const W = 380, H = 160, padL = 44, padTop = 10, padBot = 24;
    const cH = H - padTop - padBot, barW = 56, gap = (W - padL - barW * 3) / 4;
    const fmtK = v => `$${(v / 1000).toFixed(0)}k`;
    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxHeight: H }}>
            {[0, 0.25, 0.5, 0.75, 1].map((f, i) => {
                const y = padTop + (1 - f) * cH;
                return <g key={i}>
                    <line x1={padL} y1={y} x2={W} y2={y} stroke="#f1f5f9" strokeWidth="1" />
                    <text x={padL - 3} y={y + 3} textAnchor="end" fontSize="8" fill="#cbd5e1">{`$${((f * maxV) / 1000).toFixed(0)}k`}</text>
                </g>;
            })}
            <text x={8} y={H / 2} textAnchor="middle" fontSize="8" fill="#94a3b8" transform={`rotate(-90,8,${H / 2})`}>↑ USD ($)</text>
            {vals.map((v, i) => {
                const bH = Math.max(Math.abs(v.v) / maxV * cH, 1);
                const x = padL + gap * (i + 1) + barW * i;
                const y = padTop + (maxV - Math.abs(v.v)) / maxV * cH;
                return <g key={v.label}>
                    <rect x={x} y={y} width={barW} height={bH} fill={v.v < 0 ? '#ef4444' : v.col} rx="3"
                        style={{ transition: 'background 0.3s, color 0.3s, border-color 0.3s, box-shadow 0.3s, opacity 0.3s, transform 0.3s' }} />
                    <text x={x + barW / 2} y={y - 4} textAnchor="middle" fontSize="9" fontWeight="700" fill={v.v < 0 ? '#ef4444' : v.col}>{fmtK(v.v)}</text>
                    <text x={x + barW / 2} y={H - padBot + 14} textAnchor="middle" fontSize="9" fill="#64748b">{v.label}</text>
                </g>;
            })}
        </svg>
    );
}

export default function Scope3ProcurementOptimizer({ sessionId, onComplete }) {
    const [phase, setPhase] = useState('intro');
    const [units, setUnits] = useState([60_000, 30_000, 10_000]); // a, b, c

    const totalU = units.reduce((s, v) => s + v, 0) || 1;
    const avgCO2 = units.reduce((s, v, i) => s + (v / totalU) * SUPPLIERS[i].co2, 0);
    const avgCost = units.reduce((s, v, i) => s + (v / totalU) * SUPPLIERS[i].cost, 0);
    const cogs = avgCost * TOTAL_UNITS;
    const revenue = REVENUE_PER_UNIT * TOTAL_UNITS;
    const profit = revenue - cogs;
    const contractSafe = avgCO2 <= THRESHOLD_CO2;
    const status = contractSafe ? 'CONTRACT SECURED ✅' : 'CONTRACT LOST ❌';

    const setU = (i, val) => setUnits(prev => { const n = [...prev]; n[i] = Number(val); return n; });

    const handleSubmit = useCallback(async () => {
        try {
            await fetch(`${API}/api/admin/${sessionId}/mod6-procurement`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ supplier_a: units[0], supplier_b: units[1], supplier_c: units[2], avg_co2: avgCO2, contract_secured: contractSafe }),
            });
        } catch { }
        onComplete?.();
    }, [units, avgCO2, contractSafe, sessionId, onComplete]);

    if (phase === 'intro') return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif" }}>
            <div style={{ background: '#fff', maxWidth: 580, width: '90%', borderRadius: 12, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.35)' }}>
                <div style={{ background: '#1e293b', color: '#fff', padding: '1rem 1.5rem' }}>
                    <div style={{ fontSize: '0.6rem', letterSpacing: '0.15em', opacity: 0.6, textTransform: 'uppercase' }}>Module 6 — Two-Phase Alert</div>
                    <h2 style={{ margin: '0.3rem 0 0', fontSize: '1rem', fontWeight: 800 }}>The Scope 3 Ultimatum</h2>
                </div>
                <div style={{ padding: '1.5rem 2rem' }}>
                    <blockquote style={{ borderLeft: '3px solid #dc2626', paddingLeft: '1rem', margin: '0 0 1.25rem', color: '#334155', fontSize: '0.88rem', lineHeight: 1.75, fontStyle: 'italic' }}>
                        "Muressons' largest B2B customer — representing <strong>25% of total revenue</strong> — issues an ultimatum.
                        Reduce the carbon intensity of delivered products by 20% within two rounds, or <strong>lose the contract entirely</strong>. Target: ≤{THRESHOLD_CO2} kg CO₂e/unit."
                    </blockquote>
                    <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.7, margin: '0 0 1.5rem' }}>
                        Allocate your <strong>{TOTAL_UNITS.toLocaleString()} unit</strong> order across three supplier tiers.
                        Balance carbon intensity against COGS to keep the contract <em>and</em> stay profitable.
                    </p>
                    <button onClick={() => setPhase('optimizer')} style={{ width: '100%', padding: '0.85rem', background: 'linear-gradient(135deg, #1e293b, #334155)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}>
                        Open Procurement Optimizer →
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
                        <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>Scope 3 Procurement Optimizer</h2>
                        <div style={{ display: 'flex', gap: '1.2rem', fontSize: '0.72rem' }}>
                            {[['CO2 INTENSITY', `${avgCO2.toFixed(2)} kg/u`], ['UNIT COST', `$${avgCost.toFixed(2)}`], ['GROSS PROFIT', `$${(profit / 1000).toFixed(0)}k`], ['STATUS', contractSafe ? 'SECURED' : 'LOST']].map(([k, v]) => (
                                <div key={k} style={{ textAlign: 'center' }}>
                                    <div style={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.06em' }}>{k}</div>
                                    <div style={{ fontWeight: 800, color: k === 'STATUS' ? (contractSafe ? '#16a34a' : '#dc2626') : '#0f172a', fontSize: k === 'STATUS' ? '0.65rem' : 'inherit' }}>{v}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div style={{ fontSize: '0.72rem', marginTop: '0.2rem', color: contractSafe ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                        {contractSafe ? `✅ Carbon threshold met (${avgCO2.toFixed(2)} kg/u ≤ ${THRESHOLD_CO2} kg/u threshold)` : `⚠ WARNING: Carbon threshold exceeded (${avgCO2.toFixed(2)} kg/u > ${THRESHOLD_CO2} kg/u). Contract at risk!`}
                    </div>
                </div>

                {/* Status banner + Gauges */}
                <div style={{ background: contractSafe ? '#f0fdf4' : '#fef2f2', padding: '0.75rem 1rem', margin: '0.75rem', borderRadius: 8, border: `1px solid ${contractSafe ? '#bbf7d0' : '#fecaca'}` }}>
                    <div style={{ textAlign: 'center', fontWeight: 700, fontSize: '0.78rem', color: contractSafe ? '#16a34a' : '#dc2626', marginBottom: '0.5rem', border: `1px solid ${contractSafe ? '#16a34a' : '#dc2626'}`, display: 'inline-block', padding: '2px 12px', borderRadius: 12, marginLeft: '50%', transform: 'translateX(-50%)' }}>
                        {contractSafe ? 'CONTRACT SECURED' : 'CONTRACT LOST'}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                        <SemiGauge value={avgCO2} max={5.0} redAbove={THRESHOLD_CO2} label="Carbon Intensity" unit="kg/u" />
                        <SemiGauge value={avgCost} max={25} redAbove={null} label="Unit Cost (COGS)" unit="$" />
                    </div>
                </div>

                {/* Bar chart */}
                <div style={{ background: '#fff', margin: '0 0.75rem', borderRadius: 8, border: '1px solid #e2e8f0', padding: '0.5rem 0.75rem' }}>
                    <BarChart3 cogs={cogs} profit={profit} revenue={revenue} />
                </div>

                {/* Sliders */}
                <div style={{ padding: '0.75rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem 1rem' }}>
                    {SUPPLIERS.map((s, i) => (
                        <div key={s.id} style={{ gridColumn: i === 2 ? '1' : 'auto' }}>
                            <div style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 600, marginBottom: '3px', display: 'flex', justifyContent: 'space-between' }}>
                                <span>{s.label}</span>
                                <span style={{ color: s.color }}>CO₂: {s.co2}kg · ${s.cost}/u</span>
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <input type="range" min={0} max={TOTAL_UNITS} step={1000} value={units[i]}
                                    onChange={e => setU(i, e.target.value)} style={{ flex: 1, accentColor: s.color }} />
                                <div style={{ minWidth: 54, textAlign: 'center', padding: '3px 6px', border: '1px solid #d1d5db', borderRadius: 5, fontSize: '0.78rem', fontWeight: 700 }}>{units[i].toLocaleString()}</div>
                            </div>
                        </div>
                    ))}
                    <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                        <button onClick={() => setUnits([60_000, 30_000, 10_000])} style={{ width: '100%', padding: '7px', background: '#f1f5f9', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.78rem', cursor: 'pointer' }}>Reset</button>
                    </div>
                </div>

                <div style={{ padding: '0 1rem 1rem' }}>
                    <button onClick={handleSubmit} style={{ width: '100%', padding: '0.85rem', background: contractSafe ? 'linear-gradient(135deg,#16a34a,#15803d)' : 'linear-gradient(135deg,#dc2626,#b91c1c)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.88rem', cursor: 'pointer' }}>
                        {contractSafe ? '✅ Lock In Procurement Strategy' : '⚠ Submit (Contract at Risk)'}
                    </button>
                </div>
            </div>
        </div>
    );
}
