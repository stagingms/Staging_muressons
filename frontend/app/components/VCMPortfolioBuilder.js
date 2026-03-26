'use client';
import { useState, useCallback, useMemo } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

const TOTAL_REQUIRED = 20_000; // tonnes to offset
const TIERS = [
    { id: 't1', label: 'Tier 1: Engineered', desc: 'Biochar / DAC / Rock Weathering', cost: 275, integrity: 100, color: '#16a34a' },
    { id: 't2', label: 'Tier 2: Nature-Based', desc: 'REDD+ / Reforestation', cost: 22, integrity: 55, color: '#d97706' },
    { id: 't3', label: 'Tier 3: Avoidance', desc: 'Grid renewables (developed nations)', cost: 4, integrity: 15, color: '#dc2626' },
];

// ── Donut Chart ────────────────────────────────────────────────
function DonutChart({ vols }) {
    const total = vols.reduce((s, v) => s + v, 0) || 1;
    const cx = 90, cy = 90, r = 68, strokeW = 26;
    const circ = 2 * Math.PI * r;
    let offset = 0;
    const segments = vols.map((v, i) => {
        const frac = v / total;
        const dash = frac * circ;
        const seg = { frac, dash, offset, color: TIERS[i].color };
        offset += dash;
        return seg;
    });
    return (
        <svg viewBox="0 0 180 180" style={{ width: 170, height: 170, display: 'block', margin: '0 auto' }}>
            {segments.map((seg, i) => (
                <circle key={i}
                    cx={cx} cy={cy} r={r}
                    fill="none" stroke={seg.color}
                    strokeWidth={strokeW}
                    strokeDasharray={`${seg.dash} ${circ - seg.dash}`}
                    strokeDashoffset={-seg.offset + circ / 4}
                    style={{ transition: 'stroke-dasharray 0.3s' }}
                />
            ))}
            <circle cx={cx} cy={cy} r={r - strokeW / 2 - 2} fill="#fff" />
            <text x={cx} y={cy - 8} textAnchor="middle" fontSize="10" fill="#94a3b8">Total Volume</text>
            <text x={cx} y={cy + 8} textAnchor="middle" fontSize="13" fontWeight="800" fill="#0f172a">
                {total.toLocaleString()} t
            </text>
        </svg>
    );
}

// ── Integrity Gauge (semicircle) ───────────────────────────────
function IntegrityGauge({ score }) {
    // score 0-100
    const cx = 110, cy = 110, r = 80;
    const sweepDeg = 180; // semicircle
    const toRad = d => (d - 180) * Math.PI / 180;
    const arcPath = (startDeg, endDeg, radius) => {
        const s = toRad(startDeg), e = toRad(endDeg);
        const x1 = cx + radius * Math.cos(s), y1 = cy + radius * Math.sin(s);
        const x2 = cx + radius * Math.cos(e), y2 = cy + radius * Math.sin(e);
        return `M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2}`;
    };
    const angle = score / 100 * sweepDeg; // 0..180 degrees mapped to semicircle
    const needleDeg = -180 + angle;
    const needleRad = toRad(needleDeg);
    const needleX = cx + (r - 10) * Math.cos(needleRad);
    const needleY = cy + (r - 10) * Math.sin(needleRad);

    const zoneColor = score >= 70 ? '#16a34a' : score >= 40 ? '#d97706' : '#dc2626';
    const icon = score >= 70 ? '✓' : score >= 40 ? '⚠' : '⚠';
    const riskText = score >= 70 ? 'Low Risk: Portfolio Integrity Acceptable'
        : score >= 40 ? 'MODERATE RISK: Increase Tier 1 allocation'
            : 'HIGH RISK: NGO Exposé Imminent. Brand damage likely.';

    return (
        <div style={{ textAlign: 'center' }}>
            <svg viewBox="0 0 220 130" style={{ width: '100%', maxWidth: 260 }}>
                {/* Background arc zones */}
                <path d={arcPath(0, 60, r)} stroke="#fecaca" strokeWidth="20" fill="none" strokeLinecap="round" />
                <path d={arcPath(60, 120, r)} stroke="#fef3c7" strokeWidth="20" fill="none" strokeLinecap="round" />
                <path d={arcPath(120, 180, r)} stroke="#bbf7d0" strokeWidth="20" fill="none" strokeLinecap="round" />
                {/* Zone labels */}
                <text x="18" y="115" fontSize="8.5" fill="#dc2626" opacity="0.7">0</text>
                <text x="195" y="115" fontSize="8.5" fill="#16a34a" opacity="0.7">100</text>
                {/* Needle */}
                <line x1={cx} y1={cy} x2={needleX} y2={needleY}
                    stroke="#0f172a" strokeWidth="2.5" strokeLinecap="round"
                    style={{ transition: 'all 0.35s ease-out' }} />
                <circle cx={cx} cy={cy} r="5" fill="#0f172a" />
                {/* Icon */}
                <text x={cx} y={cy - 24} textAnchor="middle" fontSize="14" fill={zoneColor}>{icon}</text>
                {/* Label */}
                <text x={cx} y={cy + 20} textAnchor="middle" fontSize="9.5" fontWeight="700" fill="#0f172a">PORTFOLIO INTEGRITY SCORE</text>
            </svg>
            <div style={{ fontSize: '0.72rem', color: score < 40 ? '#dc2626' : score < 70 ? '#d97706' : '#16a34a', fontWeight: score < 70 ? 700 : 600, marginTop: '0.25rem', maxWidth: 260, margin: '0 auto' }}>
                {riskText}
            </div>
        </div>
    );
}

// ── Main Component ─────────────────────────────────────────────
export default function VCMPortfolioBuilder({ sessionId, onComplete }) {
    const [phase, setPhase] = useState('intro');
    const [vols, setVols] = useState([2_000, 6_000, 12_000]); // t1, t2, t3
    const [submitting, setSubmitting] = useState(false);

    const totalVol = vols.reduce((s, v) => s + v, 0);
    const totalCost = vols.reduce((s, v, i) => s + v * TIERS[i].cost, 0);
    const avgCost = totalVol > 0 ? totalCost / totalVol : 0;
    const integrityScore = useMemo(() => {
        if (totalVol === 0) return 0;
        return Math.round(vols.reduce((s, v, i) => s + (v / totalVol) * TIERS[i].integrity, 0));
    }, [vols, totalVol]);

    const setVol = (idx, val) => {
        setVols(prev => {
            const next = [...prev];
            next[idx] = Number(val);
            return next;
        });
    };

    const handleSubmit = useCallback(async () => {
        setSubmitting(true);
        try {
            await fetch(`${API}/api/admin/${sessionId}/mod5-vcm-choice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    t1_volume: vols[0], t2_volume: vols[1], t3_volume: vols[2],
                    integrity_score: integrityScore, total_cost: totalCost,
                }),
            });
        } catch { /* offline */ }
        setSubmitting(false);
        onComplete?.();
    }, [vols, integrityScore, totalCost, sessionId, onComplete]);

    // ── Intro ──────────────────────────────────────────────────
    if (phase === 'intro') return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.8)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Inter', sans-serif",
        }}>
            <div style={{ background: '#fff', maxWidth: 600, width: '90%', borderRadius: 12, overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.35)' }}>
                <div style={{ background: '#0f172a', color: '#fff', padding: '1rem 1.5rem' }}>
                    <div style={{ fontSize: '0.6rem', letterSpacing: '0.15em', opacity: 0.6, textTransform: 'uppercase' }}>Module 5 — Board Directive</div>
                    <h2 style={{ margin: '0.3rem 0 0', fontSize: '1rem', fontWeight: 800 }}>The Carbon Exchange Opens</h2>
                </div>
                <div style={{ padding: '1.5rem 2rem' }}>
                    <blockquote style={{
                        borderLeft: '3px solid #6366f1', paddingLeft: '1rem', margin: '0 0 1.25rem',
                        color: '#334155', fontSize: '0.88rem', lineHeight: 1.75, fontStyle: 'italic',
                    }}>
                        "To alleviate the financial pressure of the $90/tonne internal carbon fee, business units are now
                        authorised to procure external carbon credits from the Voluntary Carbon Market to offset residual
                        non-compliance emissions. <strong>However</strong>: all claims will be audited against
                        the VCMI Claims Code of Practice. <em>You are responsible for the integrity of what you buy.</em>"
                    </blockquote>
                    <p style={{ fontSize: '0.82rem', color: '#64748b', lineHeight: 1.7, margin: '0 0 1.5rem' }}>
                        You must procure <strong>20,000 tonnes</strong> of offsets. Three tiers are available — each
                        with a different price, and a hidden reputational risk. Build your portfolio wisely.
                        If your Portfolio Integrity Score drops below 40, an NGO Exposé event triggers next round.
                    </p>
                    <button onClick={() => setPhase('builder')}
                        style={{
                            width: '100%', padding: '0.85rem',
                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                            color: '#fff', border: 'none', borderRadius: 8,
                            fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer',
                        }}>
                        Open Carbon Exchange Terminal →
                    </button>
                </div>
            </div>
        </div>
    );

    // ── Builder ────────────────────────────────────────────────
    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.75)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Inter', sans-serif", padding: '1rem',
        }}>
            <div style={{
                background: '#f8fafc', maxWidth: 580, width: '100%', borderRadius: 12,
                boxShadow: '0 30px 80px rgba(0,0,0,0.3)', overflow: 'hidden',
            }}>
                {/* Header stats */}
                <div style={{ background: '#fff', padding: '0.9rem 1.5rem', borderBottom: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>VCM Portfolio Builder</h2>
                        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.72rem' }}>
                            {[
                                ['TOTAL COST', `$${(totalCost / 1000).toFixed(0)}k`],
                                ['AVG COST/T', `$${avgCost.toFixed(2)}`],
                                ['INTEGRITY', `${integrityScore}/100`],
                            ].map(([k, v]) => (
                                <div key={k} style={{ textAlign: 'center' }}>
                                    <div style={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.06em' }}>{k}</div>
                                    <div style={{ fontWeight: 800, color: k === 'INTEGRITY' && integrityScore < 40 ? '#dc2626' : '#0f172a' }}>{v}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div style={{ fontSize: '0.72rem', color: totalVol !== TOTAL_REQUIRED ? '#d97706' : '#16a34a', marginTop: '0.25rem', fontWeight: 600 }}>
                        {totalVol !== TOTAL_REQUIRED
                            ? `⚠ Portfolio: ${totalVol.toLocaleString()}t / ${TOTAL_REQUIRED.toLocaleString()}t required`
                            : `✅ Portfolio complete: ${totalVol.toLocaleString()}t`}
                    </div>
                </div>

                {/* Donut + Gauge */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0', padding: '1rem 1rem 0' }}>
                    <DonutChart vols={vols} />
                    <IntegrityGauge score={integrityScore} />
                </div>

                {/* Tier key */}
                <div style={{ display: 'flex', gap: '0.75rem', padding: '0.75rem 1.5rem', justifyContent: 'center' }}>
                    {TIERS.map(t => (
                        <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.72rem', color: '#475569' }}>
                            <div style={{ width: 10, height: 10, borderRadius: 2, background: t.color, flexShrink: 0 }} />
                            {t.id.toUpperCase()}
                        </div>
                    ))}
                </div>

                {/* Sliders */}
                <div style={{ padding: '0.5rem 1.5rem 1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem 1.25rem' }}>
                    {TIERS.map((t, i) => (
                        <div key={t.id} style={{ gridColumn: i === 2 ? '1' : 'auto' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', marginBottom: '3px' }}>
                                <label style={{ color: '#475569', fontWeight: 600 }}>{t.label} (t)</label>
                                <span style={{ fontWeight: 700, color: t.color }}>${(vols[i] * t.cost / 1000).toFixed(0)}k</span>
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <input type="range" min={0} max={TOTAL_REQUIRED} step={500} value={vols[i]}
                                    onChange={e => setVol(i, e.target.value)}
                                    style={{ flex: 1, accentColor: t.color }} />
                                <div style={{
                                    minWidth: 54, textAlign: 'center', padding: '3px 6px',
                                    border: '1px solid #d1d5db', borderRadius: 5, fontSize: '0.78rem', fontWeight: 700,
                                }}>{vols[i].toLocaleString()}</div>
                            </div>
                            <div style={{ fontSize: '0.65rem', color: '#94a3b8', marginTop: '2px' }}>{t.desc} — ${t.cost}/t</div>
                        </div>
                    ))}
                    <div style={{ gridColumn: '2', display: 'flex', alignItems: 'flex-end' }}>
                        <button onClick={() => setVols([2_000, 6_000, 12_000])}
                            style={{
                                width: '100%', padding: '7px 0', background: '#f1f5f9', border: '1px solid #d1d5db',
                                borderRadius: 6, fontSize: '0.78rem', cursor: 'pointer', fontWeight: 600, color: '#475569',
                            }}>Reset Portfolio</button>
                    </div>
                </div>

                {/* Submit */}
                <div style={{ padding: '0 1.5rem 1.25rem' }}>
                    <button onClick={handleSubmit}
                        disabled={totalVol !== TOTAL_REQUIRED || submitting}
                        style={{
                            width: '100%', padding: '0.85rem',
                            background: totalVol === TOTAL_REQUIRED ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#e2e8f0',
                            color: totalVol === TOTAL_REQUIRED ? '#fff' : '#94a3b8',
                            border: 'none', borderRadius: 8, fontWeight: 700, fontSize: '0.9rem',
                            cursor: totalVol === TOTAL_REQUIRED ? 'pointer' : 'not-allowed',
                        }}>
                        {submitting ? '⏳ Filing...' : totalVol === TOTAL_REQUIRED
                            ? `✅ File VCM Portfolio (Integrity: ${integrityScore}/100)`
                            : `Allocate ${TOTAL_REQUIRED.toLocaleString()}t before filing`}
                    </button>
                </div>
            </div>
        </div>
    );
}
