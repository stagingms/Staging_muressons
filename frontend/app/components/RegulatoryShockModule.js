'use client';
import { useState, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || '';

// ── Business Unit profiles ─────────────────────────────────────
// Revenue: $10M each
// Division A (Decarbonized from Mod 3 Green Fund winner): 500t residual emissions
// Division B (Legacy - missed Green Fund): 30,000t residual emissions
const DIV_A = { name: 'Division A (Decarbonized)', revenue: 10_000_000, opex: 6_000_000, emissions: 500, color: '#16a34a' };
const DIV_B = { name: 'Division B (Legacy)', revenue: 10_000_000, opex: 7_800_000, emissions: 30_000, color: '#2563eb' };

// Default legacy BUS if not mapping dynamically
const DEFAULT_BUS = [
    { id: 'pharma', name: 'Muressons Pharma', emissions: 800 },
    { id: 'electronics', name: 'Electronics', emissions: 28_000 },
    { id: 'consumer_goods', name: 'Consumer Goods', emissions: 22_000 },
    { id: 'software', name: 'Software', emissions: 200 },
];

function calcProfit(div, fee) {
    return div.revenue - div.opex - div.emissions * fee;
}
function calcMargin(div, fee) {
    return (calcProfit(div, fee) / div.revenue) * 100;
}
function fmt(n) {
    const abs = Math.abs(n);
    const sign = n < 0 ? '-' : '';
    if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(2)}M`;
    return `${sign}$${(abs / 1_000).toFixed(0)}k`;
}

// ── SVG Bar Chart ──────────────────────────────────────────────
function BarChart({ fee }) {
    const pA = calcProfit(DIV_A, fee);
    const pB = calcProfit(DIV_B, fee);
    const maxAbs = Math.max(Math.abs(pA), Math.abs(pB), 5_000_000);
    const W = 480, H = 220, padL = 56, padR = 20, padTop = 12, padBot = 40;
    const chartH = H - padTop - padBot;
    const chartW = W - padL - padR;
    const zeroY = padTop + (maxAbs / (maxAbs * 2)) * chartH;
    const barW = 72;
    const gap = (chartW - barW * 2) / 3;
    const xA = padL + gap;
    const xB = padL + gap * 2 + barW;

    function barRect(profit, x) {
        const h = Math.abs(profit) / (maxAbs * 2) * chartH;
        const y = profit >= 0 ? zeroY - h : zeroY;
        const col = profit >= 0 ? (profit === pA ? '#16a34a' : '#2563eb') : '#ef4444';
        return { x, y, h, col };
    }
    const rA = barRect(pA, xA);
    const rB = barRect(pB, xB);
    const gridLines = 5;

    return (
        <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', maxHeight: 220 }}>
            {/* Grid lines */}
            {Array.from({ length: gridLines + 1 }, (_, i) => {
                const y = padTop + (i / gridLines) * chartH;
                const val = maxAbs - (i / gridLines) * maxAbs * 2;
                return (
                    <g key={i}>
                        <line x1={padL} y1={y} x2={W - padR} y2={y} stroke="#e2e8f0" strokeWidth="1" />
                        <text x={padL - 6} y={y + 4} textAnchor="end" fontSize="9" fill="#94a3b8">{fmt(val)}</text>
                    </g>
                );
            })}
            {/* Zero line */}
            <line x1={padL} y1={zeroY} x2={W - padR} y2={zeroY} stroke="#334155" strokeWidth="1.5" />

            {/* Bar A */}
            <rect x={rA.x} y={rA.y} width={barW} height={Math.max(rA.h, 1)} fill={rA.col} rx="2" style={{ transition: 'background 0.3s, color 0.3s, border-color 0.3s, box-shadow 0.3s, opacity 0.3s, transform 0.3s' }} />
            <text x={rA.x + barW / 2} y={rA.y - 5} textAnchor="middle" fontSize="10" fontWeight="700" fill={rA.col}>{fmt(pA)}</text>
            <text x={rA.x + barW / 2} y={H - padBot + 14} textAnchor="middle" fontSize="10" fill="#475569">Div A (Green)</text>

            {/* Bar B */}
            <rect x={rB.x} y={rB.y} width={barW} height={Math.max(rB.h, 1)} fill={rB.col} rx="2" style={{ transition: 'background 0.3s, color 0.3s, border-color 0.3s, box-shadow 0.3s, opacity 0.3s, transform 0.3s' }} />
            <text x={rB.x + barW / 2} y={rB.y - 5} textAnchor="middle" fontSize="10" fontWeight="700" fill={rB.col}>{fmt(pB)}</text>
            <text x={rB.x + barW / 2} y={H - padBot + 14} textAnchor="middle" fontSize="10" fill="#475569">Div B (Legacy)</text>

            {/* Y axis label */}
            <text x={10} y={H / 2} textAnchor="middle" fontSize="9" fill="#94a3b8"
                transform={`rotate(-90, 10, ${H / 2})`}>↑ Net Profit ($)</text>
        </svg>
    );
}

// ── Main Component ─────────────────────────────────────────────
export default function RegulatoryShockModule({ sessionId, businessUnits, onComplete }) {
    const [phase, setPhase] = useState('news');      // 'news' | 'stress' | 'dilemma' | 'done'
    const [fee, setFee] = useState(40);
    const [buChoices, setBuChoices] = useState({});  // bu_id → 'eat' | 'pass' | 'abate'
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState(null);      // server response summary

    const activeBUs = businessUnits?.length ? businessUnits : DEFAULT_BUS;

    const mA = calcMargin(DIV_A, fee).toFixed(1);
    const mB = calcMargin(DIV_B, fee).toFixed(1);
    const isShocked = fee >= 90;

    const statusText = fee < 60
        ? 'Market conditions stable.'
        : fee < 90
            ? '⚠ WARNING: Margin compression detected. Fee approaching compliance threshold.'
            : '🚨 CRITICAL: CBAM/ETS active. Legacy assets becoming stranded. Immediate action required.';

    const handleSubmit = useCallback(async () => {
        setSubmitting(true);
        try {
            // QA-2026-07-16 #2: the backend now binds this route to the session
            // owner (same SEC-3 contract as /api/simulations). Attach the
            // player's own id so registered players pass the ownership check;
            // solo sessions have no owner and pass without it.
            let playerIdHeader = {};
            try {
                const pid = window.localStorage.getItem('muressons_playerId');
                if (pid) playerIdHeader = { 'X-Player-Id': pid };
            } catch { /* storage unavailable */ }
            const res = await fetch(`${API}/api/admin/sessions/${sessionId}/mod4-crisis-choices`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...playerIdHeader },
                body: JSON.stringify({ choices: buChoices, effective_fee: fee }),
            });
            if (res.ok) {
                const data = await res.json();
                setResult(data);
                setPhase('done');
            }
        } catch { /* offline ok — still advance */ setPhase('done'); }
        setSubmitting(false);
    }, [buChoices, fee, sessionId]);

    const allChosen = activeBUs.every(bu => (bu.emissions || bu.carbon_intensity * 1000) < 1000 || buChoices[bu.bu_id || bu.id]);

    // ── Phase: Done (confirmation) ─────────────────────────────
    if (phase === 'done') return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.75)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'DM Sans', sans-serif",
        }}>
            <div style={{
                background: '#fff', maxWidth: 560, width: '90%', borderRadius: 12,
                overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.4)',
            }}>
                <div style={{ background: '#16a34a', color: '#fff', padding: '1rem 1.5rem' }}>
                    <div style={{ fontSize: '0.65rem', letterSpacing: '0.1em', opacity: 0.8, textTransform: 'uppercase' }}>Module 4 Complete</div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 800, marginTop: 2 }}>✅ CBAM Crisis Response Recorded</div>
                </div>
                <div style={{ padding: '1.5rem 2rem' }}>
                    {result && (
                        <>
                            <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Carbon Fee</div>
                                    <div style={{ fontWeight: 800, color: '#dc2626', fontSize: '1.1rem' }}>${result.effective_fee}/t</div>
                                </div>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Net Treasury Impact</div>
                                    <div style={{ fontWeight: 800, color: result.total_treasury_delta < 0 ? '#ef4444' : '#16a34a', fontSize: '1.1rem' }}>
                                        {result.total_treasury_delta >= 0 ? '+' : ''}{fmt(result.total_treasury_delta)}
                                    </div>
                                </div>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>BUs Impacted</div>
                                    <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '1.1rem' }}>{Object.keys(result.applied_impacts || {}).length}</div>
                                </div>
                            </div>
                            {Object.entries(result.applied_impacts || {}).map(([buId, imp]) => (
                                <div key={buId} style={{
                                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                    padding: '0.5rem 0.75rem', marginBottom: '0.4rem',
                                    background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0',
                                    fontSize: '0.8rem',
                                }}>
                                    <div style={{ fontWeight: 600, color: '#1e293b' }}>{buId}</div>
                                    <div style={{ color: '#475569' }}>{imp.label}</div>
                                    <div style={{ fontWeight: 700, color: '#ef4444' }}>{fmt(imp.treasury_delta)}</div>
                                </div>
                            ))}
                        </>
                    )}
                    <div style={{
                        marginTop: '1rem', background: '#fef3c7', border: '1px solid #fcd34d',
                        borderRadius: 8, padding: '0.75rem 1rem', fontSize: '0.78rem', color: '#92400e', lineHeight: 1.6,
                    }}>
                        <strong>📚 Debrief Note:</strong> Your crisis response choices are now stamped in the simulation state.
                        BUs that chose <em>Emergency Abatement</em> will show resilience improvements in future rounds,
                        while <em>Pass to Consumers</em> choices have reduced Social License scores. These consequences
                        carry forward into Round 5 (Climate Resilience) and Round 9 (Just Transition).
                    </div>
                    <button onClick={onComplete} style={{
                        marginTop: '1.25rem', width: '100%', padding: '0.9rem',
                        background: 'linear-gradient(135deg, #0f172a, #1e293b)',
                        color: '#fff', border: 'none', borderRadius: 8,
                        fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer',
                    }}>
                        Continue to Round 5 →
                    </button>
                </div>
            </div>
        </div>
    );

    // ── Phase 1: Breaking News ─────────────────────────────────
    if (phase === 'news') return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.85)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'DM Sans', sans-serif",
        }}>
            <div style={{
                background: '#fff', maxWidth: 620, width: '90%', borderRadius: 12,
                overflow: 'hidden', boxShadow: '0 30px 80px rgba(0,0,0,0.4)',
            }}>
                {/* Breaking news banner */}
                <div style={{
                    background: '#dc2626', color: '#fff', padding: '0.9rem 1.5rem',
                    display: 'flex', alignItems: 'center', gap: '1rem',
                }}>
                    <span style={{ fontSize: '1.4rem', animation: 'pulse 0.8s infinite' }}>🚨</span>
                    <div>
                        <div style={{ fontSize: '0.65rem', letterSpacing: '0.15em', fontWeight: 700, opacity: 0.85 }}>BREAKING — REGULATORY ALERT</div>
                        <div style={{ fontSize: '1rem', fontWeight: 800 }}>CBAM + ETS Double Strike</div>
                    </div>
                    <div style={{ marginLeft: 'auto', fontSize: '0.7rem', opacity: 0.7 }}>MODULE 4</div>
                </div>
                <div style={{ padding: '1.75rem 2rem' }}>
                    <p style={{ fontSize: '0.92rem', lineHeight: 1.75, color: '#1e293b', margin: '0 0 1.25rem' }}>
                        A major trading bloc representing <strong>40% of Muressons' revenue</strong> has implemented a strict{' '}
                        <strong>Carbon Border Adjustment Mechanism (CBAM)</strong> and simultaneously slashed free ETS allowances.
                    </p>
                    <div style={{
                        background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8,
                        padding: '1rem 1.25rem', marginBottom: '1.5rem',
                    }}>
                        <div style={{ fontWeight: 700, color: '#b91c1c', fontSize: '0.82rem', marginBottom: '0.5rem' }}>
                            ⚠ Immediate Financial Impact
                        </div>
                        <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#7f1d1d', fontSize: '0.82rem', lineHeight: 1.9 }}>
                            <li>Internal carbon fee <strong>forcibly escalates from $40 → $90/tonne</strong></li>
                            <li>Fee is no longer pooled in the Green Fund — it exits the ecosystem as a <strong>direct tax</strong></li>
                            <li>Business units that decarbonized in Round 3 maintain margins</li>
                            <li>Legacy units face <strong>stranded asset risk</strong> — operating profit wiped out</li>
                        </ul>
                    </div>
                    <button
                        onClick={() => { setFee(90); setPhase('stress'); }}
                        style={{
                            width: '100%', padding: '0.9rem',
                            background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
                            color: '#fff', border: 'none', borderRadius: 8,
                            fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer',
                            letterSpacing: '0.03em',
                        }}>
                        Open P&L Stress Tester →
                    </button>
                </div>
            </div>
        </div>
    );

    // ── Phase 2: P&L Stress Tester ────────────────────────────
    if (phase === 'stress') return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.75)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'DM Sans', sans-serif", padding: '1rem',
        }}>
            <div style={{
                background: '#f8fafc', maxWidth: 580, width: '100%', borderRadius: 12,
                boxShadow: '0 30px 80px rgba(0,0,0,0.3)', overflow: 'hidden',
            }}>
                {/* Header */}
                <div style={{ background: '#fff', padding: '1rem 1.5rem', borderBottom: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.2rem' }}>
                        <h2 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: '#0f172a' }}>Carbon Shock P&L Tester</h2>
                        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.72rem' }}>
                            {[
                                ['PRICE', `$${fee}/t`],
                                ['DIV A MARGIN', `${mA}%`],
                                ['DIV B MARGIN', `${mB}%`],
                            ].map(([k, v]) => (
                                <div key={k} style={{ textAlign: 'center' }}>
                                    <div style={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.06em' }}>{k}</div>
                                    <div style={{
                                        fontWeight: 800, color: k === 'DIV B MARGIN' && parseFloat(mB) < 0 ? '#ef4444' : '#0f172a',
                                    }}>{v}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: isShocked ? '#dc2626' : '#64748b', fontWeight: isShocked ? 700 : 400 }}>
                        {statusText}
                    </div>
                </div>

                {/* Chart */}
                <div style={{ background: '#fff', margin: '1rem 1rem 0', borderRadius: 8, border: '1px solid #e2e8f0', padding: '0.75rem' }}>
                    <BarChart fee={fee} />
                </div>

                {/* Slider */}
                <div style={{ padding: '1rem 1.5rem 0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <label style={{ fontSize: '0.78rem', color: '#475569', whiteSpace: 'nowrap', fontWeight: 600 }}>
                            Carbon Price ($/tonne)
                        </label>
                        <input type="range" min={20} max={150} step={1} value={fee}
                            onChange={e => setFee(Number(e.target.value))}
                            style={{ flex: 1, accentColor: '#dc2626' }} />
                        <div style={{
                            minWidth: 44, textAlign: 'center', padding: '4px 8px',
                            border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.85rem', fontWeight: 700,
                        }}>{fee}</div>
                        <button onClick={() => setFee(40)}
                            style={{
                                padding: '6px 16px', background: '#f1f5f9', border: '1px solid #d1d5db',
                                borderRadius: 6, fontSize: '0.78rem', cursor: 'pointer', whiteSpace: 'nowrap',
                            }}>Reset Scenario</button>
                    </div>

                    {/* Shock marker */}
                    {fee >= 90 && (
                        <div style={{
                            marginTop: '0.5rem', background: '#fef2f2', border: '1px solid #fecaca',
                            borderRadius: 6, padding: '0.4rem 0.75rem', fontSize: '0.75rem', color: '#b91c1c', fontWeight: 600,
                        }}>
                            🚨 CBAM/ETS threshold: Division B operating profit is NEGATIVE. Legacy asset stranded.
                        </div>
                    )}
                </div>

                <div style={{ padding: '1rem 1.5rem' }}>
                    <button onClick={() => setPhase('dilemma')}
                        style={{
                            width: '100%', padding: '0.8rem',
                            background: 'linear-gradient(135deg, #0f172a, #1e293b)',
                            color: '#fff', border: 'none', borderRadius: 8,
                            fontWeight: 700, fontSize: '0.88rem', cursor: 'pointer',
                        }}>
                        Proceed to Crisis Management →
                    </button>
                </div>
            </div>
        </div>
    );

    // ── Phase 3: Crisis Dilemma ────────────────────────────────
    const OPTIONS = [
        { id: 'eat', label: '💸 Eat the Cost', desc: 'Miss period targets. Board penalty applied to simulation score.', color: '#dc2626' },
        { id: 'pass', label: '📈 Pass to Consumers', desc: '+15% price → -20% market share (elasticity penalty).', color: '#d97706' },
        { id: 'abate', label: '⚙️ Emergency Abatement', desc: 'CapEx ×1.3 premium (expedited supply chain). Debt financing unlocked.', color: '#0891b2' },
    ];
    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 20000, background: 'rgba(0,0,0,0.75)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'DM Sans', sans-serif", padding: '1rem', overflowY: 'auto',
        }}>
            <div style={{
                background: '#fff', maxWidth: 660, width: '100%', borderRadius: 12,
                boxShadow: '0 30px 80px rgba(0,0,0,0.3)',
            }}>
                <div style={{ background: '#0f172a', color: '#fff', padding: '1rem 1.5rem', borderRadius: '12px 12px 0 0' }}>
                    <div style={{ fontSize: '0.65rem', letterSpacing: '0.12em', opacity: 0.6, textTransform: 'uppercase' }}>Module 4 — Crisis Management</div>
                    <h2 style={{ margin: '0.2rem 0 0', fontSize: '1rem', fontWeight: 800 }}>Choose Your Crisis Response — Per Business Unit</h2>
                </div>
                <div style={{ padding: '1.25rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {activeBUs.map(bu => {
                        const emissionsVal = bu.emissions || (bu.carbon_intensity * 1000) || 500;
                        const isGreen = emissionsVal < 1000;
                        const buIdentifier = bu.bu_id || bu.id;
                        const buName = bu.name || buIdentifier;
                        return (
                            <div key={buIdentifier} style={{
                                border: `1px solid ${isGreen ? '#bbf7d0' : '#fecaca'}`,
                                background: isGreen ? '#f0fdf4' : '#fef2f2',
                                borderRadius: 8, padding: '0.9rem 1rem',
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.6rem' }}>
                                    <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#0f172a' }}>{buName}</div>
                                    <div style={{ fontSize: '0.75rem', color: isGreen ? '#16a34a' : '#dc2626', fontWeight: 700 }}>
                                        {emissionsVal.toLocaleString()}t residual •{' '}
                                        Cost: ${((emissionsVal * 90) / 1_000_000).toFixed(2)}M/round
                                    </div>
                                </div>
                                {isGreen ? (
                                    <div style={{ fontSize: '0.78rem', color: '#15803d', fontWeight: 600 }}>
                                        ✅ Green Fund investment paid off — absorbs fee easily. No action required.
                                    </div>
                                ) : (
                                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                        {OPTIONS.map(opt => (
                                            <button key={opt.id} onClick={() => setBuChoices(c => ({ ...c, [buIdentifier]: opt.id }))}
                                                style={{
                                                    flex: 1, minWidth: 130, padding: '0.5rem 0.4rem',
                                                    border: `2px solid ${buChoices[buIdentifier] === opt.id ? opt.color : '#e2e8f0'}`,
                                                    background: buChoices[buIdentifier] === opt.id ? `${opt.color}15` : '#fff',
                                                    borderRadius: 6, cursor: 'pointer', textAlign: 'left',
                                                    transition: 'background 0.15s, color 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s, transform 0.15s',
                                                }}>
                                                <div style={{ fontWeight: 700, fontSize: '0.78rem', color: opt.color }}>{opt.label}</div>
                                                <div style={{ fontSize: '0.68rem', color: '#64748b', marginTop: 2 }}>{opt.desc}</div>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                    <button onClick={handleSubmit} disabled={!allChosen || submitting}
                        style={{
                            padding: '0.9rem', background: allChosen
                                ? 'linear-gradient(135deg, #16a34a, #15803d)'
                                : '#e2e8f0',
                            color: allChosen ? '#fff' : '#94a3b8',
                            border: 'none', borderRadius: 8,
                            fontWeight: 700, fontSize: '0.9rem',
                            cursor: allChosen ? 'pointer' : 'not-allowed',
                        }}>
                        {submitting ? '⏳ Submitting...' : allChosen ? '✅ Submit Crisis Responses' : 'Select a response for each distressed BU'}
                    </button>
                </div>
            </div>
        </div>
    );
}
