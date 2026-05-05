'use client';
import { useState, useMemo, useCallback } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const GREEN_FUND = 5_000_000;
const PROJECTS = [
    {
        id: 'led',
        name: 'Warehouse LED & HVAC Retrofit',
        icon: '💡',
        cost: 1_200_000,
        costLabel: '$1.2M',
        emissionsSaved: 8_000,
        mac: -150,
        macLabel: '−$150/t',
        verdict: 'REJECTED',
        verdictColor: '#dc2626',
        lesson: 'This project pays for itself — negative MAC means it\'s financially profitable without a subsidy. Business units must self-fund this via standard CapEx. The Green Fund is only for crossing the "green premium" hurdle.',
        tier: 'trap',
    },
    {
        id: 'waste',
        name: 'Manufacturing Waste-to-Heat Recovery',
        icon: '♻️',
        cost: 900_000,
        costLabel: '$900K',
        emissionsSaved: 30_000,
        mac: 30,
        macLabel: '$30/t',
        verdict: 'PRIME BID',
        verdictColor: '#16a34a',
        lesson: 'Best Carbon ROI in the portfolio. At $30/t, it\'s below the $40 shadow price — fund buys maximum emissions reduction for minimum cost, building a moat before the fee escalates in Round 4.',
        tier: 'sweet',
    },
    {
        id: 'resin',
        name: 'R&D — Bio-based Resins (Packaging)',
        icon: '🧬',
        cost: 3_200_000,
        costLabel: '$3.2M',
        emissionsSaved: 21_000,
        mac: 152,
        macLabel: '$152/t',
        verdict: 'LONG PLAY',
        verdictColor: '#d97706',
        lesson: 'High cost, low immediate return. Eats most of the Green Fund for minor near-term relief. But unlocks a new low-emission product line critical for Round 8–10 supply chain survival.',
        tier: 'longplay',
    },
];

// ── MAC Curve SVG ──────────────────────────────────────────────
function MACCurve({ funded, budgetLine }) {
    const sorted = [...PROJECTS].sort((a, b) => a.mac - b.mac);
    const W = 480, H = 220, padL = 56, padT = 14, padB = 36, padR = 20;
    const cW = W - padL - padR, cH = H - padT - padB;

    // x: cumulative tonnes, y: MAC $/t
    let cumX = 0;
    const bars = sorted.map(p => {
        const x = cumX;
        cumX += p.emissionsSaved;
        return { ...p, x, w: p.emissionsSaved };
    });
    const maxX = cumX;
    const minY = Math.min(...PROJECTS.map(p => p.mac)) * 1.3;
    const maxY = Math.max(...PROJECTS.map(p => p.mac)) * 1.2;
    const range = maxY - minY || 1;

    const toX = v => padL + (v / maxX) * cW;
    const toY = v => padT + cH - ((v - minY) / range) * cH;
    const zeroY = toY(0);

    // Budget line x: sum of costs for funded sorted projects
    const budgetX = funded.reduce((s, id) => {
        const p = PROJECTS.find(pr => pr.id === id);
        return s + (p ? p.emissionsSaved : 0);
    }, 0);

    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%' }}>
            {/* Grid horizontals */}
            {[-150, 0, 50, 100, 150].map(v => {
                const y = toY(v);
                return <g key={v}>
                    <line x1={padL} y1={y} x2={W - padR} y2={y} stroke={v === 0 ? '#334155' : '#f1f5f9'} strokeWidth={v === 0 ? 1.5 : 1} />
                    <text x={padL - 5} y={y + 3} textAnchor="end" fontSize="9" fill="#94a3b8">${v}</text>
                </g>;
            })}
            {/* Carbon fee reference line */}
            <line x1={padL} y1={toY(40)} x2={W - padR} y2={toY(40)}
                stroke="#6366f1" strokeWidth="1.5" strokeDasharray="6 3" />
            <text x={W - padR - 4} y={toY(40) - 4} textAnchor="end" fontSize="9" fill="#6366f1">Shadow Price $40/t</text>
            {/* Bars */}
            {bars.map(b => {
                const x1 = toX(b.x), x2 = toX(b.x + b.w);
                const barW = x2 - x1 - 2;
                const isFunded = funded.includes(b.id);
                const col = b.mac < 0 ? '#ef4444' : b.mac < 50 ? '#16a34a' : '#d97706';
                const bY = b.mac >= 0 ? toY(b.mac) : zeroY;
                const bH = Math.abs(toY(b.mac) - zeroY);
                return <g key={b.id}>
                    <rect x={x1 + 1} y={bY} width={barW} height={Math.max(bH, 1)}
                        fill={isFunded ? col : `${col}55`}
                        stroke={isFunded ? col : '#e2e8f0'} strokeWidth="1" rx="2"
                        style={{ transition: 'fill 0.25s' }} />
                    <text x={(x1 + x2) / 2} y={padT + cH + 14} textAnchor="middle" fontSize="9" fill={col}>{b.macLabel}</text>
                    <text x={(x1 + x2) / 2} y={bY - (b.mac >= 0 ? 4 : -12)} textAnchor="middle" fontSize="9" fontWeight="700" fill={col}>{b.emissionsSaved.toLocaleString()}t</text>
                </g>;
            })}
            {/* Budget line */}
            {budgetX > 0 && (
                <line x1={toX(budgetX)} y1={padT} x2={toX(budgetX)} y2={padT + cH}
                    stroke="#2563eb" strokeWidth="2" strokeDasharray="5 3" />
            )}
            {/* Axes labels */}
            <text x={10} y={H / 2} textAnchor="middle" fontSize="9" fill="#94a3b8" transform={`rotate(-90,10,${H/2})`}>↑ MAC ($/tonne)</text>
            <text x={W / 2} y={H - 2} textAnchor="middle" fontSize="9" fill="#94a3b8">Cumulative Abatement (tonnes) →</text>
        </svg>
    );
}

// ── Main component ─────────────────────────────────────────────
export default function GreenFundBidding({ sessionId, onComplete }) {
    const [phase, setPhase] = useState('memo');          // memo | bidding | curve
    const [funded, setFunded] = useState([]);            // project ids funded
    const [priority, setPriority] = useState([]);        // ordered bid list
    const [submitting, setSubmitting] = useState(false);
    const [selected, setSelected] = useState(null);

    const toggleProject = (id) => {
        const p = PROJECTS.find(pr => pr.id === id);
        if (funded.includes(id)) {
            setFunded(f => f.filter(x => x !== id));
            setPriority(pr => pr.filter(x => x !== id));
        } else {
            const allocatedCost = [...funded, id].reduce((s, fid) => {
                const fp = PROJECTS.find(pr => pr.id === fid);
                return s + (fp ? fp.cost : 0);
            }, 0);
            // Reject negative MAC projects
            if (p.mac < 0) { setSelected(id); return; }
            if (allocatedCost <= GREEN_FUND) {
                setFunded(f => [...f, id]);
                setPriority(pr => [...pr, id]);
            }
        }
    };

    const totalCost = funded.reduce((s, id) => { const p = PROJECTS.find(pr => pr.id === id); return s + (p ? p.cost : 0); }, 0);
    const remaining = GREEN_FUND - totalCost;
    const totalSaved = funded.reduce((s, id) => { const p = PROJECTS.find(pr => pr.id === id); return s + (p ? p.emissionsSaved : 0); }, 0);

    const handleSubmit = useCallback(async () => {
        setSubmitting(true);
        try {
            await fetch(`${API}/api/admin/${sessionId}/mod3-green-fund`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ funded_projects: funded, priority_order: priority, total_abatement: totalSaved }),
            });
        } catch { }
        setSubmitting(false);
        onComplete?.();
    }, [funded, priority, totalSaved, sessionId, onComplete]);

    // ── Phase 1: CEO Memo ──────────────────────────────────────
    if (phase === 'memo') return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif" }}>
            <div style={{ background: '#fff', maxWidth: 580, width: '90%', borderRadius: 12, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.4)' }}>
                {/* Letterhead */}
                <div style={{ background: 'linear-gradient(135deg,#0f172a,#1e293b)', color: '#fff', padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div style={{ fontSize: '0.6rem', letterSpacing: '0.15em', opacity: 0.5, textTransform: 'uppercase' }}>Muressons Global Corporation — BOARD OF DIRECTORS</div>
                        <h2 style={{ margin: '0.2rem 0 0', fontSize: '1rem', fontWeight: 800 }}>MEMORANDUM — CONFIDENTIAL</h2>
                    </div>
                    <div style={{ fontSize: '0.72rem', opacity: 0.5 }}>MODULE 3 · Q3</div>
                </div>
                <div style={{ padding: '1.75rem 2rem' }}>
                    <div style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.75rem', marginBottom: '1.25rem', fontSize: '0.78rem', color: '#94a3b8' }}>
                        <strong>TO:</strong> All Business Unit Heads &nbsp;·&nbsp; <strong>FROM:</strong> Office of the CEO &nbsp;·&nbsp; <strong>RE:</strong> Internal Carbon Levy & Green Fund Activation
                    </div>
                    <blockquote style={{ margin: '0 0 1.25rem', padding: '1rem 1.25rem', background: '#f8fafc', borderLeft: '4px solid #6366f1', fontSize: '0.9rem', lineHeight: 1.85, color: '#1e293b', borderRadius: '0 8px 8px 0' }}>
                        <p style={{ margin: '0 0 0.75rem' }}>
                            <strong>The grace period is over.</strong> As of this period, our <strong>$40/tonne shadow price is now a levied fee</strong>.
                            We have deducted this fee from the retained earnings of every business unit and pooled it into a central{' '}
                            <strong style={{ color: '#16a34a' }}>$5,000,000 Green Fund</strong>.
                        </p>
                        <p style={{ margin: 0 }}>
                            This capital is now available for decarbonization projects. <strong>You must bid for it.</strong>{' '}
                            Funding will be strictly prioritised by <strong>Carbon ROI</strong> — the lowest Marginal Abatement Cost wins.
                        </p>
                    </blockquote>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: 1.7, marginBottom: '1.5rem' }}>
                        Review each project's cost and emissions profile carefully. Not every project deserves the Green Fund.
                        If a project pays for itself financially, it should be funded from standard CapEx — not from this strategic reserve.
                    </div>
                    <button onClick={() => setPhase('bidding')} style={{ width: '100%', padding: '0.9rem', background: 'linear-gradient(135deg,#0f172a,#4f46e5)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}>
                        Enter the Green Fund Bidding Room →
                    </button>
                </div>
            </div>
        </div>
    );

    // ── Phase 2: Project Bidding ───────────────────────────────
    if (phase === 'bidding') return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.78)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif", padding: '1rem', overflowY: 'auto' }}>
            <div style={{ background: '#f8fafc', maxWidth: 620, width: '100%', borderRadius: 12, boxShadow: '0 30px 80px rgba(0,0,0,0.35)', overflow: 'hidden' }}>
                {/* Header bar */}
                <div style={{ background: '#0f172a', color: '#fff', padding: '0.9rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <div style={{ fontSize: '0.6rem', letterSpacing: '0.12em', opacity: 0.5, textTransform: 'uppercase' }}>Green Fund Bidding Room</div>
                        <h2 style={{ margin: '0.2rem 0 0', fontSize: '0.95rem', fontWeight: 800 }}>Select Projects to Fund — Budget: $5M</h2>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: '0.8rem' }}>
                        <div style={{ color: '#94a3b8', fontSize: '0.65rem' }}>REMAINING</div>
                        <div style={{ fontWeight: 800, color: remaining < 0 ? '#ef4444' : '#34d399' }}>${(remaining / 1e6).toFixed(2)}M</div>
                    </div>
                </div>

                {/* Project cards */}
                <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {PROJECTS.map(p => {
                        const isFunded = funded.includes(p.id);
                        const isRejected = selected === p.id;
                        const borderCol = p.mac < 0 ? '#fecaca' : isFunded ? '#bbf7d0' : '#e2e8f0';
                        return (
                            <div key={p.id} style={{ border: `2px solid ${isFunded ? '#16a34a' : borderCol}`, background: isFunded ? '#f0fdf4' : '#fff', borderRadius: 8, padding: '0.85rem 1rem', cursor: 'pointer', transition: 'all 0.2s' }}
                                onClick={() => toggleProject(p.id)}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.4rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ fontSize: '1.2rem' }}>{p.icon}</span>
                                        <div>
                                            <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#0f172a' }}>{p.name}</div>
                                            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{p.costLabel} upfront · {p.emissionsSaved.toLocaleString()}t saved · MAC: <strong style={{ color: p.mac < 0 ? '#dc2626' : p.mac < 50 ? '#16a34a' : '#d97706' }}>{p.macLabel}</strong></div>
                                        </div>
                                    </div>
                                    <div style={{ textAlign: 'right' }}>
                                        <div style={{ fontWeight: 800, fontSize: '0.72rem', color: p.verdictColor, letterSpacing: '0.05em' }}>{p.verdict}</div>
                                        <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: '2px' }}>{isFunded ? '✅ Selected' : p.mac < 0 ? '🚫 Fund rejects' : 'Click to bid'}</div>
                                    </div>
                                </div>
                                {(isRejected || p.mac < 0) && (
                                    <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, padding: '0.4rem 0.6rem', fontSize: '0.72rem', color: '#b91c1c', marginTop: '0.35rem' }}>
                                        ⛔ <strong>Green Fund Rejection:</strong> {p.lesson}
                                    </div>
                                )}
                                {isFunded && (
                                    <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: 6, padding: '0.4rem 0.6rem', fontSize: '0.72rem', color: '#166534', marginTop: '0.35rem' }}>
                                        ✅ <strong>Strategic rationale:</strong> {p.lesson}
                                    </div>
                                )}
                            </div>
                        );
                    })}

                    {/* Fund summary */}
                    <div style={{ background: '#1e293b', color: '#fff', borderRadius: 8, padding: '0.85rem 1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ fontSize: '0.8rem' }}>
                            Total abatement: <strong>{totalSaved.toLocaleString()}t</strong> · Spent: <strong>${(totalCost / 1e6).toFixed(2)}M</strong> of $5M
                        </div>
                        <button onClick={() => setPhase('curve')} disabled={funded.length === 0}
                            style={{ padding: '0.5rem 1rem', background: funded.length ? '#6366f1' : '#475569', color: '#fff', border: 'none', borderRadius: 6, fontWeight: 700, fontSize: '0.78rem', cursor: funded.length ? 'pointer' : 'not-allowed' }}>
                            View MAC Curve →
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );

    // ── Phase 3: MAC Curve Visual + Submit ────────────────────
    return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.78)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif", padding: '1rem', overflowY: 'auto' }}>
            <div style={{ background: '#f8fafc', maxWidth: 580, width: '100%', borderRadius: 12, boxShadow: '0 30px 80px rgba(0,0,0,0.35)', overflow: 'hidden' }}>
                <div style={{ background: '#0f172a', color: '#fff', padding: '0.9rem 1.5rem' }}>
                    <h2 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 800 }}>Marginal Abatement Cost Curve — Board Allocation View</h2>
                    <div style={{ fontSize: '0.7rem', opacity: 0.6, marginTop: '0.2rem' }}>Bars to the left of the budget line are funded by the Green Fund. Shaded bars = unfunded.</div>
                </div>
                <div style={{ background: '#fff', margin: '0.75rem', border: '1px solid #e2e8f0', borderRadius: 8, padding: '0.5rem 0.25rem 0' }}>
                    <MACCurve funded={funded} budgetLine={totalCost} />
                </div>
                <div style={{ padding: '0.75rem 1rem', background: '#fff', margin: '0 0.75rem', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: '0.8rem' }}>
                    <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '0.5rem' }}>
                        {funded.map(id => {
                            const p = PROJECTS.find(pr => pr.id === id);
                            return <span key={id} style={{ color: '#16a34a', fontWeight: 700 }}>✅ {p.name.split(' ')[0]}: {p.macLabel}</span>;
                        })}
                    </div>
                    <div style={{ color: '#64748b', fontSize: '0.74rem' }}>
                        Board ranking locks in: Projects with MAC below shadow price are prioritized. The budget line allocates remaining capital in order of cost-effectiveness.
                    </div>
                </div>
                <div style={{ padding: '0.75rem 1rem 1rem', display: 'flex', gap: '0.75rem' }}>
                    <button onClick={() => setPhase('bidding')} style={{ flex: 1, padding: '0.75rem', background: '#f1f5f9', border: '1px solid #d1d5db', borderRadius: 8, fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}>
                        ← Revise Bids
                    </button>
                    <button onClick={handleSubmit} disabled={submitting} style={{ flex: 2, padding: '0.75rem', background: 'linear-gradient(135deg,#16a34a,#15803d)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.88rem', cursor: 'pointer' }}>
                        {submitting ? '⏳ Filing...' : `✅ Submit Bids — ${totalSaved.toLocaleString()}t Abated`}
                    </button>
                </div>
            </div>
        </div>
    );
}
