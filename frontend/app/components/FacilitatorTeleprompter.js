'use client';
import { useState, useEffect } from 'react';
import { BRIEFINGS, HEALTHCARE_BRIEFINGS, SDG_BRIEFINGS } from './RoundBriefing';
const API = process.env.NEXT_PUBLIC_API_URL || '';

/* Hover-tooltip descriptions for every simulation engine flag */
const ENGINE_TOOLTIPS = {
    // ── Financial engines ──
    fog_of_war_active:          'Fog of War — Hides competitor data from players. Teams must make decisions without full market visibility, simulating real-world information asymmetry.',
    inflation_index_applied:    'Inflation Index — Applies year-over-year cost inflation to OPEX. Erodes margins if teams don\'t invest in efficiency or raise prices.',
    loan_triggered:             'Emergency Loan — Auto-fires when CAPEX exceeds 20% of treasury. Adds 12% interest penalty to next round, teaching capital discipline.',
    dividend_penalty:           'Dividend Clamp — Dividends clamped to treasury balance. Teams that over-promise distributions lose board confidence.',
    capex_overflow:             'CAPEX Overflow — Total CAPEX exceeded 2× treasury ceiling. Triggers forced loan with compounding penalties.',
    
    // ── ESG / Environmental engines ──
    ncd_compounding:            'NCD Compounding — Natural Capital Debt accrues interest (base 5% + 0.05% per unit). High-debt BUs face runaway ecological costs that become unrecoverable.',
    carbon_tax_applied:         'Carbon Tax — $250/tonne CO₂ deduction from terminal EBITDA. Can swing terminal value by $20M+ depending on cumulative emissions.',
    green_bond_active:          'Green Bond — NCD reduced by 15 units. Teams that activated early get compounding cost avoidance.',
    circular_redesign:          'Circular Redesign — NCD reduced by 12 units + synergy multiplier boost. Unlocks waste-to-energy gate in Round 8.',
    desalination_active:        'Desalination Plant — NCD reduced by 30 units (largest single reduction). Very expensive but eliminates Blue Stress risk.',
    greenwash_detected:         'Greenwashing Flag — Cosmetic ESG spending without substance detected. Reputation takes a hidden penalty that compounds in later rounds.',
    
    // ── Social / Workforce engines ──
    social_license_check:       'Social License — Measures community trust (0–100). Below 30 triggers strikes and regulatory intervention, cratering revenue.',
    brain_drain_risk:           'Brain Drain — Software BU staff flight risk. If triggered, top talent leaves and OPEX increases by 10.7% due to recruitment costs.',
    strike_probability:         'Strike Engine — Cumulative worker discontent. Probability increases with low wages, environmental damage, and rushed transitions.',
    talent_flight_triggered:    'Talent Flight — Brain drain confirmed. Software BU permanently loses efficiency. Cannot be reversed once triggered.',
    
    // ── Strategic engines ──
    vrio_imitation_decay:       'VRIO Decay — Competitive advantages erode over time if not reinforced. Rare capabilities become common without sustained R&D investment.',
    synergy_multiplier_boost:   'Synergy Boost — Cross-BU efficiency multiplier increased (max 1.35×). Makes future CAPEX 35% more productive.',
    contagion_engine:           'Contagion Engine — Crisis spreads between BUs. Electronics crisis can cascade into Pharma and Software, amplifying damage.',
    deep_audit_completed:       'Deep Audit — R1 audit choice affects R5 crisis severity. Deep audit halves contagion; surface scan doubles exposure.',
    electronics_blindspot:      'Electronics Blindspot — Surface audit in R1 left hidden supply chain vulnerabilities. R5 crisis hits this BU 2× harder.',
    
    // ── Round-specific engines ──
    truth_premium_check:        'Truth Premium — R7 AI Bias decision. Transparent overhaul costs more but yields +8 reputation and unlocks governance bonuses.',
    cyclone_damage:             'Stochastic Cyclone — R6 random weather event. Infrastructure hardening (R4-B) reduces damage by 60%.',
    water_stress_event:         'Blue Stress — R9 water shortage. Teams without desalination face -25 social license and emergency OPEX spikes.',
    just_transition_active:     'Just Transition — R10 workforce transformation. Mismanaged transition triggers full labor strike, halting operations.',
    spinoff_triggered:          'Spinoff — R10 strategic option. Zeros out weakest BU but eliminates its drag on group synergy.',
    divest_triggered:           'Divestiture — R10 strategic option. Wipes synergy multiplier entirely in exchange for immediate cash injection.',
    resist_integrate:           'Resist & Integrate — R10 premium option. Only available if synergy multiplier ≥ 1.20. Preserves all BUs with enhanced synergy.',
};

export default function FacilitatorTeleprompter({ currentRound = 1, sessionId = null }) {
    const [scripts, setScripts] = useState({});
    const [roundConfig, setRoundConfig] = useState(null);
    const [activeRound, setActiveRound] = useState(currentRound);
    const [checkedPoints, setCheckedPoints] = useState({});

    useEffect(() => {
        fetch(`${API}/api/admin/teleprompter`)
            .then(r => r.json())
            .then(d => setScripts(d.scripts || {}))
            .catch(() => {});
    }, []);

    useEffect(() => {
        if (!sessionId) {
            setRoundConfig(null);
            return;
        }
        fetch(`${API}/api/round-config/${activeRound}?session_id=${sessionId}`)
            .then(r => r.json())
            .then(d => setRoundConfig(d))
            .catch(() => setRoundConfig(null));
    }, [activeRound, sessionId]);

    const script = scripts[String(activeRound)] || {};
    const [notes, setNotes] = useState({ earlyAnalysis: '', commentary: '' });

    const updateNote = (key, value) => {
        setNotes(prev => ({ ...prev, [key]: value }));
    };

    const getGuidingQuestions = (paradigm, round) => {
        if (round <= 1) return 'First round — introduce the simulation';
        return `Analyse how teams handled R${round - 1} trade-offs`;
    };

    const toggleCheck = (round, idx) => {
        setCheckedPoints(prev => {
            const key = `${round}-${idx}`;
            return { ...prev, [key]: !prev[key] };
        });
    };

    // ── Styled section label ──
    const sectionLabel = (icon, text, accent = '#94a3b8') => (
        <div style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            marginBottom: '0.75rem', paddingBottom: '0.5rem',
            borderBottom: `1px solid ${accent}22`,
        }}>
            <span style={{ fontSize: '0.85rem' }}>{icon}</span>
            <span style={{
                fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.14em',
                textTransform: 'uppercase', color: accent,
            }}>{text}</span>
            <span style={{ flex: 1, height: '1px', background: `${accent}22` }} />
        </div>
    );

    const completedCount = Object.entries(checkedPoints)
        .filter(([k, v]) => k.startsWith(`${activeRound}-`) && v).length;
    const totalPoints = (script.talking_points || []).length;

    return (
        <div style={{
            padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem',
            fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif",
        }}>
            {/* ── Header ── */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <div style={{
                        width: '32px', height: '32px', borderRadius: '8px',
                        background: 'linear-gradient(135deg, #c9a84c, #a78a3a)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.9rem', boxShadow: '0 2px 8px rgba(201,168,76,0.25)',
                    }}>🎤</div>
                    <div>
                        <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
                            Facilitator Teleprompter
                        </h2>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono, monospace)', letterSpacing: '0.05em' }}>
                            ROUND {activeRound} OF 10 · {script.title ? 'ACTIVE' : 'NO SCRIPT'}
                        </div>
                    </div>
                </div>
                {totalPoints > 0 && (
                    <div style={{
                        display: 'flex', alignItems: 'center', gap: '0.4rem',
                        padding: '0.3rem 0.7rem', borderRadius: '6px',
                        background: completedCount === totalPoints ? 'rgba(34,197,94,0.12)' : 'rgba(201,168,76,0.08)',
                        border: `1px solid ${completedCount === totalPoints ? 'rgba(34,197,94,0.3)' : 'rgba(201,168,76,0.2)'}`,
                    }}>
                        <span style={{ fontSize: '0.7rem', fontWeight: 700, fontFamily: 'var(--font-mono, monospace)', color: completedCount === totalPoints ? '#22c55e' : '#c9a84c' }}>
                            {completedCount}/{totalPoints}
                        </span>
                    </div>
                )}
            </div>

            {/* ── Round Selector ── */}
            <div style={{
                display: 'flex', gap: '0.3rem', padding: '0.5rem',
                background: 'rgba(0,0,0,0.15)', borderRadius: '10px',
                border: '1px solid rgba(255,255,255,0.04)',
            }}>
                {Array.from({ length: 10 }, (_, i) => i + 1).map(r => {
                    const isActive = activeRound === r;
                    const isPast = r <= currentRound;
                    return (
                        <button key={r} onClick={() => setActiveRound(r)} style={{
                            flex: 1, height: '36px', borderRadius: '7px', border: 'none',
                            background: isActive
                                ? 'linear-gradient(135deg, #c9a84c, #b8963f)'
                                : isPast ? 'rgba(255,255,255,0.05)' : 'transparent',
                            color: isActive ? '#0f172a' : isPast ? 'var(--text-primary)' : 'var(--text-muted)',
                            fontWeight: isActive ? 800 : 600,
                            fontSize: '0.78rem', cursor: 'pointer',
                            fontFamily: 'var(--font-mono, monospace)',
                            transition: 'all 0.15s',
                            boxShadow: isActive ? '0 2px 10px rgba(201,168,76,0.35)' : 'none',
                            opacity: !isPast && !isActive ? 0.4 : 1,
                        }}>R{r}</button>
                    );
                })}
            </div>

            {script.title && (
                <>
                    {/* ── Round Title Banner ── */}
                    <div style={{
                        padding: '0.85rem 1.25rem', borderRadius: '10px',
                        background: 'linear-gradient(135deg, rgba(201,168,76,0.08), rgba(201,168,76,0.02))',
                        border: '1px solid rgba(201,168,76,0.18)',
                        borderLeft: '3px solid #c9a84c',
                    }}>
                        <div style={{ fontSize: '0.6rem', fontWeight: 700, color: '#c9a84c', letterSpacing: '0.15em', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                            ROUND {activeRound} DIRECTIVE
                        </div>
                        <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 }}>
                            {script.title}
                        </h3>
                    </div>

                    {/* ── Two-Column: Talking Points + Engines/Discussion ── */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>

                        {/* Left: Talking Points */}
                        <div style={{
                            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                            borderRadius: '10px', padding: '1rem', gridRow: 'span 2',
                        }}>
                            {sectionLabel('💬', 'Talking Points', '#60a5fa')}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                {(script.talking_points || []).map((point, i) => {
                                    const isChecked = checkedPoints[`${activeRound}-${i}`];
                                    return (
                                        <div key={i} onClick={() => toggleCheck(activeRound, i)} style={{
                                            padding: '0.55rem 0.7rem', borderRadius: '7px', cursor: 'pointer',
                                            background: isChecked ? 'rgba(34,197,94,0.06)' : 'rgba(255,255,255,0.02)',
                                            border: `1px solid ${isChecked ? 'rgba(34,197,94,0.2)' : 'rgba(255,255,255,0.04)'}`,
                                            display: 'flex', alignItems: 'flex-start', gap: '0.5rem',
                                            transition: 'all 0.2s ease', opacity: isChecked ? 0.55 : 1,
                                        }}>
                                            <span style={{
                                                width: '18px', height: '18px', borderRadius: '4px', flexShrink: 0,
                                                border: isChecked ? '2px solid #22c55e' : '2px solid rgba(255,255,255,0.15)',
                                                background: isChecked ? 'rgba(34,197,94,0.15)' : 'transparent',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontSize: '0.6rem', color: '#22c55e', marginTop: '1px', transition: 'all 0.2s',
                                            }}>{isChecked ? '✓' : ''}</span>
                                            <span style={{
                                                fontSize: '0.82rem', color: 'var(--text-primary)', lineHeight: 1.5,
                                                textDecorationLine: isChecked ? 'line-through' : 'none',
                                                textDecorationColor: 'rgba(34,197,94,0.4)',
                                            }}>{point}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Right Top: Engines Likely to Fire */}
                        {script.engines_likely?.length > 0 && (
                            <div style={{
                                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                                borderRadius: '10px', padding: '1rem',
                            }}>
                                {sectionLabel('⚙️', 'Engines Likely to Fire', '#f59e0b')}
                                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                                    {script.engines_likely.map((eng, i) => {
                                        const tip = ENGINE_TOOLTIPS[eng] || `Engine: ${eng}`;
                                        return (
                                            <span key={i} className="engine-tag-wrapper" style={{
                                                position: 'relative', display: 'inline-block',
                                            }}>
                                                <span style={{
                                                    padding: '0.25rem 0.55rem', borderRadius: '5px',
                                                    background: 'rgba(245,158,11,0.08)',
                                                    border: '1px solid rgba(245,158,11,0.2)',
                                                    color: '#fbbf24',
                                                    fontSize: '0.68rem', fontWeight: 600,
                                                    fontFamily: 'var(--font-mono, monospace)',
                                                    cursor: 'help', letterSpacing: '0.02em',
                                                    transition: 'all 0.15s', display: 'inline-block',
                                                }}
                                                onMouseOver={e => {
                                                    e.currentTarget.style.background = 'rgba(245,158,11,0.18)';
                                                    e.currentTarget.style.borderColor = 'rgba(245,158,11,0.45)';
                                                    e.currentTarget.parentElement.querySelector('.engine-tip').style.opacity = '1';
                                                    e.currentTarget.parentElement.querySelector('.engine-tip').style.pointerEvents = 'auto';
                                                    e.currentTarget.parentElement.querySelector('.engine-tip').style.transform = 'translateY(0)';
                                                }}
                                                onMouseOut={e => {
                                                    e.currentTarget.style.background = 'rgba(245,158,11,0.08)';
                                                    e.currentTarget.style.borderColor = 'rgba(245,158,11,0.2)';
                                                    e.currentTarget.parentElement.querySelector('.engine-tip').style.opacity = '0';
                                                    e.currentTarget.parentElement.querySelector('.engine-tip').style.pointerEvents = 'none';
                                                    e.currentTarget.parentElement.querySelector('.engine-tip').style.transform = 'translateY(4px)';
                                                }}
                                                >{eng}</span>
                                                <div className="engine-tip" style={{
                                                    position: 'absolute', bottom: 'calc(100% + 6px)', left: '50%',
                                                    transform: 'translateX(-50%) translateY(4px)',
                                                    maxWidth: 'min(400px, 80vw)', minWidth: '200px', width: 'max-content',
                                                    padding: '0.6rem 0.75rem', borderRadius: '8px',
                                                    background: 'rgba(15,23,42,0.97)', color: '#e2e8f0',
                                                    border: '1px solid rgba(245,158,11,0.25)',
                                                    boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                                                    fontSize: '0.72rem', lineHeight: 1.55,
                                                    opacity: 0, pointerEvents: 'none',
                                                    transition: 'opacity 0.15s, transform 0.15s',
                                                    zIndex: 50, whiteSpace: 'normal', wordBreak: 'break-word',
                                                }}>
                                                    <strong style={{ color: '#fbbf24', display: 'block', marginBottom: '3px', fontSize: '0.68rem', letterSpacing: '0.04em' }}>
                                                        {eng.replace(/_/g, ' ').toUpperCase()}
                                                    </strong>
                                                    {tip}
                                                </div>
                                            </span>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* Right Bottom: Discussion Prompts */}
                        <div style={{
                            background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                            borderRadius: '10px', padding: '1rem',
                        }}>
                            {sectionLabel('🗣️', 'Discussion Prompts', '#a78bfa')}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                {(script.discussion_prompts || []).map((prompt, i) => (
                                    <div key={i} style={{
                                        padding: '0.5rem 0.7rem', borderRadius: '7px',
                                        background: 'rgba(139,92,246,0.04)',
                                        borderLeft: '2px solid rgba(139,92,246,0.3)',
                                        fontSize: '0.82rem', color: 'var(--text-secondary, #94a3b8)',
                                        fontStyle: 'italic', lineHeight: 1.5,
                                    }}>
                                        &ldquo;{prompt}&rdquo;
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </>
            )}

            {/* ── Official Round Briefing ── */}
            {roundConfig && (
                <div style={{
                    background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                    borderRadius: '10px', padding: '1.25rem',
                    borderLeft: '3px solid #3b82f6',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                        {sectionLabel('📖', 'Official Round Briefing', '#3b82f6')}
                        {roundConfig.paradigm && (
                            <span style={{
                                fontSize: '0.6rem', padding: '2px 8px', marginBottom: '0.75rem',
                                background: 'rgba(59,130,246,0.08)', color: '#60a5fa',
                                borderRadius: '4px', border: '1px solid rgba(59,130,246,0.2)',
                                fontWeight: 700, letterSpacing: '0.1em',
                            }}>
                                {roundConfig.paradigm.replace('_', ' ').toUpperCase()}
                            </span>
                        )}
                    </div>
                    
                    {(() => {
                        const dictionary = roundConfig.paradigm === 'healthcare' ? HEALTHCARE_BRIEFINGS : roundConfig.paradigm?.includes('sdg') ? SDG_BRIEFINGS : BRIEFINGS;
                        const activeNarrative = dictionary[activeRound];
                        if (!activeNarrative) return <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No detailed briefing available for this round yet.</p>;

                        return (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                <div>
                                    <h5 style={{ margin: '0 0 0.3rem 0', fontSize: '1.05rem', color: 'var(--text-primary)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                        <span>{activeNarrative.icon}</span> {activeNarrative.title}
                                    </h5>
                                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>{activeNarrative.theme}</p>
                                </div>

                                <div style={{
                                    background: 'rgba(0,0,0,0.12)', padding: '1rem', borderRadius: '8px',
                                    border: '1px solid rgba(255,255,255,0.04)',
                                }}>
                                    <div style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', marginBottom: '0.6rem', letterSpacing: '0.1em' }}>
                                        Storyboard Outline
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.82rem', color: 'var(--text-secondary, #cbd5e1)', lineHeight: 1.6 }}>
                                        {activeNarrative.narrative.map((para, i) => (
                                            <p key={i} style={{ margin: 0 }} dangerouslySetInnerHTML={{ __html: para }} />
                                        ))}
                                    </div>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                                    <div style={{ background: 'rgba(59,130,246,0.04)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(59,130,246,0.1)' }}>
                                        <div style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', color: '#3b82f6', marginBottom: '0.5rem', letterSpacing: '0.1em', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                            <span>🎯</span> Strategic Objectives
                                        </div>
                                        <ul style={{ margin: 0, paddingLeft: '1.1rem', fontSize: '0.78rem', color: 'var(--text-secondary, #cbd5e1)', display: 'flex', flexDirection: 'column', gap: '0.25rem', lineHeight: 1.5 }}>
                                            {activeNarrative.objectives.map((obj, i) => (
                                                <li key={i}>{obj}</li>
                                            ))}
                                        </ul>
                                    </div>
                                    <div style={{ background: 'rgba(16,185,129,0.04)', padding: '0.85rem', borderRadius: '8px', border: '1px solid rgba(16,185,129,0.1)' }}>
                                        <div style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', color: '#10b981', marginBottom: '0.5rem', letterSpacing: '0.1em', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                                            <span>📊</span> Key Metrics
                                        </div>
                                        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                                            {activeNarrative.metrics.map((m, i) => (
                                                <div key={i} style={{ background: 'rgba(255,255,255,0.03)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.72rem', color: 'var(--text-secondary, #94a3b8)', display: 'flex', alignItems: 'center', gap: '0.25rem', border: '1px solid rgba(255,255,255,0.06)' }}>
                                                    <span>{m.icon}</span> <span>{m.label}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {roundConfig.crisis && (
                                    <div style={{ padding: '0.75rem 1rem', borderRadius: '8px', background: 'rgba(239,68,68,0.06)', borderLeft: '3px solid #ef4444', border: '1px solid rgba(239,68,68,0.12)' }}>
                                        {typeof roundConfig.crisis === 'object' ? (
                                            <>
                                                <span style={{ fontSize: '0.75rem', color: '#f87171', fontWeight: 700, display: 'block', marginBottom: '4px', letterSpacing: '0.05em' }}>
                                                    {roundConfig.crisis.icon} {roundConfig.crisis.title || '🚨 EXECUTIVE ALERT'}
                                                </span>
                                                <span style={{ fontSize: '0.82rem', color: '#fca5a5', lineHeight: 1.5 }}>{roundConfig.crisis.description}</span>
                                            </>
                                        ) : (
                                            <>
                                                <span style={{ fontSize: '0.75rem', color: '#f87171', fontWeight: 700, display: 'block', marginBottom: '4px', letterSpacing: '0.05em' }}>🚨 EXECUTIVE ALERT</span>
                                                <span style={{ fontSize: '0.82rem', color: '#fca5a5', lineHeight: 1.5 }}>{roundConfig.crisis}</span>
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })()}
                </div>
            )}

            {/* ── Facilitator Notes ── */}
            <div style={{
                background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
                borderRadius: '10px', padding: '1.25rem',
            }}>
                {sectionLabel('✍️', 'Facilitator Notes & Analysis', '#94a3b8')}
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                        <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                            Previous Round Analysis
                        </label>
                        <div style={{ fontSize: '0.65rem', color: 'rgba(148,163,184,0.6)', fontStyle: 'italic', marginBottom: '0.2rem' }}>
                            {getGuidingQuestions(roundConfig?.paradigm, activeRound)}
                        </div>
                        <textarea
                            value={notes.earlyAnalysis}
                            onChange={(e) => updateNote('earlyAnalysis', e.target.value)}
                            placeholder="Cohort decisions and engine triggers from previous round..."
                            style={{
                                width: '100%', minHeight: '80px', padding: '0.65rem', borderRadius: '7px',
                                background: 'rgba(0,0,0,0.15)', border: '1px solid rgba(255,255,255,0.06)',
                                color: 'var(--text-primary)', fontSize: '0.82rem', fontFamily: 'inherit',
                                resize: 'vertical', outline: 'none', lineHeight: 1.5,
                            }}
                        />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                        <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                            Current Round Commentary
                        </label>
                        <div style={{ fontSize: '0.65rem', color: 'transparent', marginBottom: '0.2rem' }}>&nbsp;</div>
                        <textarea
                            value={notes.commentary}
                            onChange={(e) => updateNote('commentary', e.target.value)}
                            placeholder="Custom narrative elements for this round's briefing..."
                            style={{
                                width: '100%', minHeight: '80px', padding: '0.65rem', borderRadius: '7px',
                                background: 'rgba(0,0,0,0.15)', border: '1px solid rgba(255,255,255,0.06)',
                                color: 'var(--text-primary)', fontSize: '0.82rem', fontFamily: 'inherit',
                                resize: 'vertical', outline: 'none', lineHeight: 1.5,
                            }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
