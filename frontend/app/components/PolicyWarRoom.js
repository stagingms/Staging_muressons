'use client';
import { useState, useMemo, useCallback } from 'react';
const API = process.env.NEXT_PUBLIC_API_URL || '';

const WAR_CHEST = 5_000_000;
const BASE_MARKET = 50; // Muressons base market share %

const STANCES = [
    { id: 'defensive', label: 'Defensive Lobbying', desc: 'Delay/dilute the carbon tax. Trap: triggers "Climate Hypocrisy" if NGO discovers it.', probMod: -0.3, shareMod: -5, risk: 'high' },
    { id: 'neutral', label: 'Neutral (Do Nothing)', desc: 'Conserve War Chest. Outcome depends entirely on baseline legislative momentum.', probMod: 0, shareMod: 0, risk: 'medium' },
    { id: 'offensive', label: 'Offensive Lobbying', desc: 'Weaponize regulation — lobby for strictest carbon tax to crush dirty competitors.', probMod: 0.4, shareMod: 20, risk: 'low' },
    { id: 'coalition', label: 'Industry Coalition', desc: 'Co-build open-source standard. Safe but neutralizes your competitive advantage.', probMod: 0.2, shareMod: 8, risk: 'low' },
];

function SemiGaugePct({ value, label }) {
    const W = 240, H = 140, cx = W / 2, cy = H * 0.82, r = 80;
    const toRad = deg => (deg - 180) * Math.PI / 180;
    const pct = Math.min(Math.max(value, 0), 100) / 100;
    const needleDeg = pct * 180;
    const nr = toRad(needleDeg);
    const nx = cx + (r - 12) * Math.cos(nr), ny = cy + (r - 12) * Math.sin(nr);
    const col = value < 40 ? '#dc2626' : value < 70 ? '#d97706' : '#16a34a';
    const endRad = toRad(needleDeg);
    const ex = cx + r * Math.cos(endRad), ey = cy + r * Math.sin(endRad);
    const large = needleDeg > 90 ? 1 : 0;
    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxWidth: W }}>
            {/* Zones */}
            {[['#fecaca', 0, 72], ['#fef3c7', 72, 108], ['#bbf7d0', 108, 180]].map(([col2, s, e]) => {
                const sr = toRad(s), er2 = toRad(e);
                const sx = cx + r * Math.cos(sr), sy = cy + r * Math.sin(sr);
                const ex2 = cx + r * Math.cos(er2), ey2 = cy + r * Math.sin(er2);
                const lg = e - s > 90 ? 1 : 0;
                return <path key={s} d={`M ${sx} ${sy} A ${r} ${r} 0 ${lg} 1 ${ex2} ${ey2}`} fill="none" stroke={col2} strokeWidth="22" strokeLinecap="round" />;
            })}
            {/* Progress arc */}
            {pct > 0 && <path d={`M ${cx - r} ${cy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`} fill="none" stroke={col} strokeWidth="6" strokeLinecap="round" style={{ transition: 'background 0.3s, color 0.3s, border-color 0.3s, box-shadow 0.3s, opacity 0.3s, transform 0.3s' }} />}
            <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#1e293b" strokeWidth="2.5" strokeLinecap="round" style={{ transition: 'background 0.3s, color 0.3s, border-color 0.3s, box-shadow 0.3s, opacity 0.3s, transform 0.3s' }} />
            <circle cx={cx} cy={cy} r="5" fill="#1e293b" />
            <text x={cx} y={cy - 28} textAnchor="middle" fontSize="22" fontWeight="900" fill={col}>{value}%</text>
            <text x={cx} y={cy - 10} textAnchor="middle" fontSize="10" fill="#64748b">{label}</text>
        </svg>
    );
}

function MarketShareChart({ muressons, competitor }) {
    const W = 440, H = 100, padL = 100, padR = 70, padTop = 8;
    const cW = W - padL - padR;
    const bars = [{ label: 'Dirty Competitor', pct: competitor, col: '#dc2626' }, { label: 'Muressons (You)', pct: muressons, col: '#2563eb' }];
    const rowH = (H - padTop) / 2;
    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%' }}>
            {[0, 25, 50, 75, 100].map(v => {
                const x = padL + (v / 100) * cW;
                return <g key={v}><line x1={x} y1={padTop} x2={x} y2={H} stroke="#f1f5f9" strokeWidth="1" />
                    <text x={x} y={H} textAnchor="middle" fontSize="8" fill="#cbd5e1">{v}</text></g>;
            })}
            {bars.map((b, i) => {
                const y = padTop + i * rowH + rowH * 0.18;
                const bH = rowH * 0.55;
                const bW = (b.pct / 100) * cW;
                return <g key={b.label}>
                    <text x={padL - 6} y={y + bH / 2 + 4} textAnchor="end" fontSize="10" fill={b.col}>{b.label}</text>
                    <rect x={padL} y={y} width={Math.max(bW, 2)} height={bH} fill={b.col} rx="3" style={{ transition: 'width 0.35s' }} />
                    <text x={padL + bW + 6} y={y + bH / 2 + 4} fontSize="10" fontWeight="700" fill={b.col}>{b.pct}%</text>
                </g>;
            })}
            <text x={W - padR + 4} y={H} fontSize="8" fill="#94a3b8">Market Share (%) →</text>
        </svg>
    );
}

export default function PolicyWarRoom({ sessionId, onComplete }) {
    const [phase, setPhase] = useState('intro');
    const [stance, setStance] = useState('neutral');
    const [spend, setSpend] = useState(12_500);
    const [submitting, setSubmitting] = useState(false);

    const stanceObj = STANCES.find(s => s.id === stance);
    const spendRatio = spend / WAR_CHEST;
    const baseProb = 50; // 50% base legislative chance
    const prob = Math.round(Math.min(100, Math.max(0, baseProb + stanceObj.probMod * 100 * spendRatio)));
    const marketShare = Math.round(Math.min(95, Math.max(5, BASE_MARKET + (stance === 'offensive' ? stanceObj.shareMod * spendRatio : stanceObj.shareMod))));
    const netProfit = (marketShare / 100) * 50_000_000 * (1 + spendRatio * 0.1);
    const remaining = WAR_CHEST - spend;
    const outcome = prob >= 70 ? 'Tax Implemented' : prob >= 40 ? 'Uncertain' : 'Tax Defeated';

    const handleSubmit = useCallback(async () => {
        setSubmitting(true);
        try {
            await fetch(`${API}/api/admin/${sessionId}/mod8-policy`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stance, spend, legislative_probability: prob, market_share: marketShare }),
            });
        } catch { }
        setSubmitting(false);
        onComplete?.();
    }, [stance, spend, prob, marketShare, sessionId, onComplete]);

    if (phase === 'intro') return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif" }}>
            <div style={{ background: '#fff', maxWidth: 580, width: '90%', borderRadius: 12, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.35)' }}>
                <div style={{ background: '#1e3a5f', color: '#fff', padding: '1rem 1.5rem' }}>
                    <div style={{ fontSize: '0.6rem', letterSpacing: '0.15em', opacity: 0.6, textTransform: 'uppercase' }}>Module 8 — VP Government Affairs</div>
                    <h2 style={{ margin: '0.3rem 0 0', fontSize: '1rem', fontWeight: 800 }}>The Non-Market War Chest</h2>
                </div>
                <div style={{ padding: '1.5rem 2rem' }}>
                    <blockquote style={{ borderLeft: '3px solid #3b82f6', paddingLeft: '1rem', margin: '0 0 1.25rem', color: '#334155', fontSize: '0.87rem', lineHeight: 1.75, fontStyle: 'italic' }}>
                        "The 'Global Clean Competition Act' is moving through the legislature. The Board has authorised a <strong>$5M Non-Market War Chest</strong>.
                        Do we fight the regulation to save our remaining dirty assets — or do we <strong>weaponize the government to destroy our competitors?</strong>"
                    </blockquote>
                    <button onClick={() => setPhase('allocator')} style={{ width: '100%', padding: '0.85rem', background: 'linear-gradient(135deg,#1e3a5f,#2563eb)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}>
                        Enter the Policy War Room →
                    </button>
                </div>
            </div>
        </div>
    );

    return (
        <div style={{ position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'DM Sans',sans-serif", padding: '1rem', overflowY: 'auto' }}>
            <div style={{ background: '#f8fafc', maxWidth: 580, width: '100%', borderRadius: 12, boxShadow: '0 30px 80px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
                <div style={{ background: '#fff', padding: '0.9rem 1.5rem', borderBottom: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>Executive Policy Allocator</h2>
                        <div style={{ display: 'flex', gap: '1.2rem', fontSize: '0.72rem' }}>
                            {[['LEGISLATIVE PROBABILITY', `${prob}%`], ['PROJECTED OUTCOME', outcome], ['REMAINING BUDGET', `$${(remaining / 1e6).toFixed(2)}M`]].map(([k, v]) => (
                                <div key={k} style={{ textAlign: 'center' }}>
                                    <div style={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.06em', fontSize: '0.68rem' }}>{k}</div>
                                    <div style={{ fontWeight: 800, color: '#0f172a', fontSize: k === 'PROJECTED OUTCOME' ? '0.75rem' : 'inherit' }}>{v}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
                        By lobbying <em>{stanceObj.label.toLowerCase()}</em> with ${spend.toLocaleString()}, you have a {prob}% chance of shifting the regulatory landscape.
                    </div>
                </div>

                <div style={{ textAlign: 'center', padding: '0.5rem 1rem 0' }}>
                    <SemiGaugePct value={prob} label="Legislative Chance" />
                </div>

                <hr style={{ margin: '0 1rem', border: 'none', borderTop: '1px solid #f1f5f9' }} />

                <div style={{ padding: '0.6rem 1rem', background: '#fff', margin: '0.5rem' }}>
                    <MarketShareChart muressons={marketShare} competitor={100 - marketShare} />
                    <div style={{ textAlign: 'center', fontSize: '0.75rem', color: '#64748b', marginTop: '4px' }}>
                        Est. Net Profit: ${netProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </div>
                </div>

                <div style={{ padding: '0.5rem 1rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div>
                        <label style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Lobbying Stance</label>
                        <select value={stance} onChange={e => setStance(e.target.value)}
                            style={{ width: '100%', padding: '7px 10px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.78rem', fontFamily: 'inherit', background: '#fff' }}>
                            {STANCES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                        </select>
                        <div style={{ fontSize: '0.65rem', color: '#94a3b8', marginTop: '4px', lineHeight: 1.4 }}>{stanceObj.desc}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: '0.72rem', color: '#475569', fontWeight: 600, marginBottom: '4px', display: 'flex', justifyContent: 'space-between' }}>
                            <span>War Chest Spend ($)</span><span style={{ fontWeight: 700 }}>${spend.toLocaleString()}</span>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                            <input type="range" min={0} max={WAR_CHEST} step={12500} value={spend}
                                onChange={e => setSpend(Number(e.target.value))} style={{ flex: 1, accentColor: '#2563eb' }} />
                            <div style={{ minWidth: 52, textAlign: 'center', padding: '3px 5px', border: '1px solid #d1d5db', borderRadius: 5, fontSize: '0.75rem', fontWeight: 700 }}>{spend.toLocaleString()}</div>
                        </div>
                    </div>
                    <div style={{ gridColumn: '1/-1' }}>
                        <button onClick={() => { setStance('neutral'); setSpend(12500); }}
                            style={{ width: '100%', padding: '7px', background: '#f1f5f9', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.78rem', cursor: 'pointer', marginBottom: '0.5rem' }}>
                            Reset Strategy
                        </button>
                        <button onClick={handleSubmit} disabled={submitting}
                            style={{ width: '100%', padding: '0.8rem', background: 'linear-gradient(135deg,#1e3a5f,#2563eb)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.88rem', cursor: 'pointer' }}>
                            {submitting ? '⏳...' : '✅ Deploy Non-Market Strategy'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
