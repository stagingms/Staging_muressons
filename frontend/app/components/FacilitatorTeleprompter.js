'use client';
import { useState, useEffect } from 'react';
import { BRIEFINGS, HEALTHCARE_BRIEFINGS, SDG_BRIEFINGS } from './RoundBriefing';
const API = process.env.NEXT_PUBLIC_API_URL || '';

/* ── Systemic Risk Intelligence Sub-Component ── */
function SystemicRiskIntel({ sessionId, sectionLabel }) {
    const [sysRisk, setSysRisk] = useState(null);
    useEffect(() => {
        if (!sessionId) return;
        const fetchSys = () => {
            fetch(`${API}/api/simulations/${sessionId}/dashboard`)
                .then(r => r.ok ? r.json() : null)
                .then(d => {
                    if (!d) return;
                    const flags = d.global_state?.active_event_flags || {};
                    setSysRisk({
                        tipping: flags.systemic_tipping_state || {},
                        cascades: flags.npc_cascade_events || [],
                        foreshadowing: flags.foreshadowing_signals || [],
                        blackSwans: flags.black_swan_result?.events_triggered || [],
                        blackSwanContinuing: flags.black_swan_result?.events_continuing || [],
                        difficulty: flags.difficulty_tier || 'standard',
                        wacc: flags.esg_wacc_diagnostics || null,
                    });
                })
                .catch(() => {});
        };
        fetchSys();
        const t = setInterval(fetchSys, 20000);
        return () => clearInterval(t);
    }, [sessionId]);

    if (!sysRisk) return null;
    const hasTipping = sysRisk.tipping.climate_tipped || sysRisk.tipping.social_tipped || sysRisk.tipping.financial_tipped;
    const hasCascades = sysRisk.cascades.length > 0;
    const hasBlackSwans = sysRisk.blackSwans.length > 0 || sysRisk.blackSwanContinuing.length > 0;
    const hasForeshadowing = sysRisk.foreshadowing.length > 0;
    const hasAny = hasTipping || hasCascades || hasBlackSwans || hasForeshadowing;

    if (!hasAny && !sysRisk.wacc) return null;

    const tpBadge = (label, tipped, color) => (
        <span key={label} style={{
            display: 'inline-flex', alignItems: 'center', gap: '4px',
            padding: '3px 10px', borderRadius: '6px', fontSize: '0.68rem', fontWeight: 700,
            background: tipped ? `${color}18` : 'rgba(0,0,0,0.1)',
            color: tipped ? color : 'var(--text-muted)',
            border: `1px solid ${tipped ? color + '40' : 'transparent'}`,
            fontFamily: 'var(--font-mono, monospace)',
        }}>
            <span style={{ fontSize: '0.6rem' }}>{tipped ? '🔴' : '🟢'}</span>
            {label}
        </span>
    );

    return (
        <div style={{
            background: 'linear-gradient(135deg, rgba(239,68,68,0.06), rgba(245,158,11,0.04))',
            border: '1px solid rgba(239,68,68,0.18)',
            borderRadius: '10px', padding: '1rem',
            borderLeft: '3px solid #ef4444',
        }}>
            {sectionLabel('🌡️', 'Systemic Risk Intelligence (Live)', '#ef4444')}
            <div style={{ fontSize: '0.68rem', color: 'rgba(239,68,68,0.7)', marginBottom: '0.75rem', fontStyle: 'italic' }}>
                Real-time systemic risk state for the connected session · Difficulty: <strong style={{ color: '#fbbf24' }}>{sysRisk.difficulty.toUpperCase()}</strong>
            </div>

            {/* Tipping Point Status */}
            <div style={{ marginBottom: '0.75rem' }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.4rem' }}>
                    Tipping Point Gates
                </div>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {tpBadge('CLIMATE', sysRisk.tipping.climate_tipped, '#ef4444')}
                    {tpBadge('SOCIAL', sysRisk.tipping.social_tipped, '#f59e0b')}
                    {tpBadge('FINANCIAL', sysRisk.tipping.financial_tipped, '#8b5cf6')}
                </div>
            </div>

            {/* ESG WACC */}
            {sysRisk.wacc && (
                <div style={{ marginBottom: '0.75rem', padding: '0.5rem 0.7rem', borderRadius: '7px', background: 'rgba(0,0,0,0.08)', border: '1px solid rgba(255,255,255,0.04)' }}>
                    <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#60a5fa', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>
                        ESG-Adjusted WACC
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                        <span>Base: {((sysRisk.wacc.base_wacc || 0.05) * 100).toFixed(1)}%</span>
                        <span style={{ color: '#ef4444' }}>Carbon: +{((sysRisk.wacc.carbon_premium || 0) * 100).toFixed(2)}%</span>
                        <span style={{ color: '#f59e0b' }}>Gov: +{((sysRisk.wacc.governance_premium || 0) * 100).toFixed(2)}%</span>
                        <span style={{ color: '#22c55e' }}>SLO: -{((sysRisk.wacc.slo_discount || 0) * 100).toFixed(2)}%</span>
                        <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Final: {((sysRisk.wacc.adjusted_wacc || 0.05) * 100).toFixed(2)}%</span>
                    </div>
                </div>
            )}

            {/* Active Black Swans */}
            {hasBlackSwans && (
                <div style={{ marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>
                        🦢 Active Black Swan Events
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                        {[...sysRisk.blackSwans, ...sysRisk.blackSwanContinuing].map((evt, i) => (
                            <div key={i} style={{
                                padding: '0.4rem 0.65rem', borderRadius: '6px',
                                background: 'rgba(167,139,250,0.06)',
                                borderLeft: '2px solid rgba(167,139,250,0.4)',
                                fontSize: '0.75rem', color: '#e9d5ff', lineHeight: 1.4,
                            }}>
                                {evt.icon || '🦢'} <strong>{evt.title}</strong>
                                {evt.rounds_remaining > 0 && <span style={{ fontSize: '0.65rem', color: '#a78bfa' }}> ({evt.rounds_remaining}r left)</span>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* NPC Cascades */}
            {hasCascades && (
                <div style={{ marginBottom: '0.75rem' }}>
                    <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#f97316', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>
                        ⚡ NPC Cascade Reactions
                    </div>
                    <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                        {sysRisk.cascades.map((c, i) => (
                            <span key={i} style={{
                                padding: '3px 8px', borderRadius: '5px', fontSize: '0.68rem',
                                background: 'rgba(249,115,22,0.08)', border: '1px solid rgba(249,115,22,0.2)',
                                color: '#fb923c', fontWeight: 600, fontFamily: 'var(--font-mono, monospace)',
                            }}>
                                {c.action?.replace(/_/g, ' ')}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Foreshadowing Signals */}
            {hasForeshadowing && (
                <div>
                    <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>
                        🔮 Foreshadowing Signals
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        {sysRisk.foreshadowing.map((sig, i) => (
                            <div key={i} style={{
                                padding: '0.35rem 0.6rem', borderRadius: '5px',
                                background: sig.category === 'warning' ? 'rgba(245,158,11,0.06)' : 'rgba(34,211,153,0.06)',
                                borderLeft: `2px solid ${sig.category === 'warning' ? 'rgba(245,158,11,0.4)' : 'rgba(34,211,153,0.4)'}`,
                                fontSize: '0.72rem', color: sig.category === 'warning' ? '#fde68a' : '#a7f3d0', lineHeight: 1.4,
                            }}>
                                {sig.category === 'warning' ? '⚠️' : '✅'} {sig.message || sig.signal_id?.replace(/_/g, ' ')}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

/* ── Live Autonomous Agent Intelligence Sub-Component ── */
function LiveAgentIntel({ sessionId, sectionLabel }) {
    const [agentData, setAgentData] = useState(null);
    useEffect(() => {
        if (!sessionId) return;
        const fetchAgents = () => {
            fetch(`${API}/api/admin/teleprompter/agents/${sessionId}`)
                .then(r => r.ok ? r.json() : null)
                .then(d => { if (d && d.agents) setAgentData(d); })
                .catch(() => {});
        };
        fetchAgents();
        const t = setInterval(fetchAgents, 15000);
        return () => clearInterval(t);
    }, [sessionId]);

    if (!agentData || !agentData.agents) return null;

    const STAGE_COLORS = {
        dormant:   { color: '#10b981', bg: 'rgba(16,185,129,0.10)' },
        watching:  { color: '#f59e0b', bg: 'rgba(245,158,11,0.10)' },
        agitated:  { color: '#f97316', bg: 'rgba(249,115,22,0.10)' },
        hostile:   { color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
        triggered: { color: '#dc2626', bg: 'rgba(220,38,38,0.15)' },
    };

    const STAGE_ICONS = { dormant: '😊', watching: '👀', agitated: '😠', hostile: '🔥', triggered: '💥' };

    return (
        <div style={{
            background: 'linear-gradient(135deg, rgba(6,182,212,0.06), rgba(139,92,246,0.06))',
            border: '1px solid rgba(6,182,212,0.2)',
            borderRadius: '10px', padding: '1rem',
            borderLeft: '3px solid #06b6d4',
        }}>
            {sectionLabel('📡', `Live Agent State — ${agentData.facilitator_alert || 'Active'}`, '#06b6d4')}

            {/* Agent Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.5rem', marginBottom: '0.75rem' }}>
                {agentData.agents.map(agent => {
                    const sc = STAGE_COLORS[agent.stage] || STAGE_COLORS.dormant;
                    const pct = agent.tolerance_pct || 0;
                    return (
                        <div key={agent.agent_id} style={{
                            padding: '0.6rem 0.7rem', borderRadius: '8px',
                            background: 'rgba(0,0,0,0.15)',
                            border: `1px solid ${sc.color}30`,
                            ...(agent.stage === 'triggered' ? { animation: 'pulse 2s infinite' } : {}),
                        }}>
                            {/* Agent header */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
                                <span style={{ fontSize: '0.85rem' }}>{agent.icon}</span>
                                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-primary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                    {agent.name}
                                </span>
                                <span style={{
                                    fontSize: '0.5rem', fontWeight: 800, padding: '1px 5px',
                                    borderRadius: '3px', background: sc.bg, color: sc.color,
                                    fontFamily: 'var(--font-mono, monospace)',
                                    letterSpacing: '0.06em',
                                }}>
                                    {STAGE_ICONS[agent.stage]} {agent.stage?.toUpperCase()}
                                </span>
                            </div>

                            {/* Tolerance bar */}
                            <div style={{
                                height: '4px', borderRadius: '2px',
                                background: 'rgba(255,255,255,0.06)', overflow: 'hidden',
                                marginBottom: '0.25rem',
                            }}>
                                <div style={{
                                    height: '100%', borderRadius: '2px',
                                    width: `${pct}%`, background: sc.color,
                                    transition: 'width 0.8s ease-out',
                                    boxShadow: `0 0 6px ${sc.color}`,
                                }} />
                            </div>

                            {/* Stats */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.58rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono, monospace)' }}>
                                <span>TOL: {agent.tolerance}/{agent.max_tolerance}</span>
                                <span style={{ color: agent.trend === 'deteriorating' ? '#ef4444' : agent.trend === 'improving' ? '#10b981' : '#64748b' }}>
                                    {agent.trend === 'deteriorating' ? '📉' : agent.trend === 'improving' ? '📈' : '➡️'} {agent.trend}
                                </span>
                            </div>

                            {/* Dialogue snippet */}
                            {agent.dialogue && (
                                <div style={{
                                    marginTop: '0.3rem', fontSize: '0.62rem', color: '#94a3b8',
                                    fontStyle: 'italic', lineHeight: 1.4,
                                    borderLeft: `2px solid ${sc.color}40`, paddingLeft: '0.4rem',
                                    maxHeight: '2.8em', overflow: 'hidden',
                                }}>
                                    &ldquo;{agent.dialogue}&rdquo;
                                </div>
                            )}

                            {/* Triggered round */}
                            {agent.triggered_round && (
                                <div style={{
                                    marginTop: '0.25rem', fontSize: '0.55rem', fontWeight: 700,
                                    color: '#fca5a5', fontFamily: 'var(--font-mono, monospace)',
                                }}>
                                    💥 TRIGGERED R{agent.triggered_round}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Interference alerts */}
            {agentData.agents && (() => {
                // Check for interference from the cascade log patterns
                const interferencePairs = [];
                const stages = {};
                agentData.agents.forEach(a => { stages[a.agent_id] = a.stage; });
                const escalated = new Set(['agitated', 'hostile', 'triggered']);
                // Journalist + Regulator
                if (escalated.has(stages.the_journalist) && escalated.has(stages.the_regulator)) {
                    interferencePairs.push({ a: 'Journalist', b: 'Regulator', icon: '📡', mult: '×1.4', label: 'Media-Regulator Feedback Loop' });
                }
                // Gen Z + Community
                if (escalated.has(stages.the_gen_z_employee) && escalated.has(stages.the_community_activist)) {
                    interferencePairs.push({ a: 'Gen Z', b: 'Community', icon: '✊', mult: '×1.25', label: 'Solidarity Amplification' });
                }
                // Investor + Regulator (hostile+)
                const hostile = new Set(['hostile', 'triggered']);
                if (hostile.has(stages.the_institutional_investor) && hostile.has(stages.the_regulator)) {
                    interferencePairs.push({ a: 'Investor', b: 'Regulator', icon: '📉', mult: '×1.3', label: 'Regulatory-Market Vortex' });
                }
                if (interferencePairs.length === 0) return null;
                return (
                    <div style={{
                        padding: '0.6rem 0.7rem', borderRadius: '8px',
                        background: 'linear-gradient(135deg, rgba(139,92,246,0.06), rgba(6,182,212,0.04))',
                        border: '1px solid rgba(139,92,246,0.18)',
                        marginBottom: '0.75rem',
                    }}>
                        <div style={{ fontSize: '0.62rem', fontWeight: 800, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.4rem' }}>
                            📡 Active Inter-Agent Interference
                        </div>
                        {interferencePairs.map((p, i) => (
                            <div key={i} style={{
                                display: 'flex', alignItems: 'center', gap: '0.4rem',
                                padding: '0.3rem 0.5rem', borderRadius: '5px',
                                background: 'rgba(139,92,246,0.05)',
                                border: '1px solid rgba(139,92,246,0.12)',
                                marginBottom: '0.25rem', fontSize: '0.72rem',
                            }}>
                                <span>{p.icon}</span>
                                <span style={{ color: '#c4b5fd', fontWeight: 700 }}>{p.a}</span>
                                <span style={{ color: '#64748b' }}>⇄</span>
                                <span style={{ color: '#c4b5fd', fontWeight: 700 }}>{p.b}</span>
                                <span style={{
                                    marginLeft: 'auto', fontSize: '0.58rem', fontWeight: 800,
                                    color: '#f472b6', background: 'rgba(244,114,182,0.10)',
                                    padding: '1px 5px', borderRadius: '4px',
                                    border: '1px solid rgba(244,114,182,0.2)',
                                    fontFamily: 'var(--font-mono, monospace)',
                                }}>{p.mult}</span>
                                <span style={{ fontSize: '0.6rem', color: '#94a3b8', fontStyle: 'italic' }}>{p.label}</span>
                            </div>
                        ))}
                    </div>
                );
            })()}

            {/* Contextual debrief questions */}
            {agentData.contextual_debrief_questions?.length > 0 && (
                <div style={{
                    padding: '0.6rem 0.7rem', borderRadius: '8px',
                    background: 'rgba(0,0,0,0.1)',
                    border: '1px solid rgba(255,255,255,0.04)',
                }}>
                    <div style={{ fontSize: '0.62rem', fontWeight: 800, color: '#06b6d4', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.4rem' }}>
                        🗣️ Contextual Debrief Questions (Stage: {agentData.worst_stage?.toUpperCase()})
                    </div>
                    {agentData.contextual_debrief_questions.map((q, i) => (
                        <div key={i} style={{
                            padding: '0.4rem 0.6rem', borderRadius: '6px',
                            background: q.startsWith('★') ? 'rgba(201,168,76,0.06)' : 'rgba(6,182,212,0.04)',
                            borderLeft: `2px solid ${q.startsWith('★') ? 'rgba(201,168,76,0.4)' : 'rgba(6,182,212,0.3)'}`,
                            fontSize: '0.75rem',
                            color: q.startsWith('★') ? '#fde68a' : 'var(--text-secondary, #94a3b8)',
                            fontStyle: 'italic', lineHeight: 1.5, marginBottom: '0.25rem',
                            fontWeight: q.startsWith('★') ? 600 : 400,
                        }}>
                            &ldquo;{q}&rdquo;
                        </div>
                    ))}
                </div>
            )}

            {/* Cascade log */}
            {agentData.cascade_log?.length > 0 && (
                <div style={{ marginTop: '0.5rem' }}>
                    <div style={{ fontSize: '0.58rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>
                        ⚡ Recent Cascade Events ({agentData.cascade_log.length})
                    </div>
                    {agentData.cascade_log.slice(-5).map((c, i) => (
                        <div key={i} style={{
                            display: 'flex', alignItems: 'center', gap: '0.4rem',
                            fontSize: '0.65rem', color: '#94a3b8',
                            fontFamily: 'var(--font-mono, monospace)', padding: '0.15rem 0',
                        }}>
                            <span style={{ color: '#fbbf24', fontWeight: 700 }}>{c.source?.replace(/the_/g, '').replace(/_/g, ' ')}</span>
                            <span style={{ color: '#475569' }}>→</span>
                            <span style={{ color: '#f59e0b' }}>{c.target?.replace(/the_/g, '').replace(/_/g, ' ')}</span>
                            <span style={{ color: '#ef4444', fontWeight: 700, marginLeft: 'auto' }}>−{c.tolerance_hit}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

/* ── Consequence DNA Insight Card (R5+ only) ── */
function LiveDNAInsight({ sessionId, activeRound, sectionLabel }) {
    const [dna, setDna] = useState(null);
    useEffect(() => {
        if (!sessionId) return;
        const fetchDNA = () => {
            fetch(`${API}/api/simulations/${sessionId}/consequence-dna-data`)
                .then(r => r.ok ? r.json() : null)
                .then(d => { if (d) setDna(d); })
                .catch(() => {});
        };
        fetchDNA();
        const t = setInterval(fetchDNA, 20000);
        return () => clearInterval(t);
    }, [sessionId]);

    if (!dna || !dna.ignited) return null;

    const mr = dna.mr_projection || {};
    const ls = dna.leverage_summary || {};
    const agents = dna.agents || [];
    const activeConflicts = agents.filter(a => ['agitated', 'hostile', 'triggered'].includes(a.stage));
    const triggeredAgents = agents.filter(a => a.stage === 'triggered');

    // Round-specific DNA debrief prompts
    const DNA_DEBRIEF = {
        5: [
            'The Shadow Board Audit just ignited the DNA Visualizer. Ask: "What causal chains can you already see forming from Rounds 1-4?"',
            'Point teams to the constriction nodes — which stakeholders are already narrowing their capital flow?',
        ],
        6: [
            'The Ethical AI decision in this round sets the Truth Premium flag. Ask: "How does this choice ripple through your DNA map?"',
            'Compare teams with deep vs shallow interventions — which have thicker Sankey paths?',
        ],
        7: [
            'Waste-to-Energy unlocks the largest synergy boost. Ask teams to trace the R7→Synergy→M_R path in their DNA.',
            'Look for interference pair activation — Journalist + Regulator feedback loops often ignite here.',
        ],
        8: [
            'Desalination vs alternative water solutions — trace the cost/benefit through the DNA to show long-term NCD impact.',
            'How many teams have triggered agents? The constriction factor directly reduces capital available for R9-R10.',
        ],
        9: [
            'Strike probability is visible in the DNA as a leak node. Ask: "Can you see where your workforce capital is being siphoned?"',
            'Teams approaching R10 should study their full causal chain — the System Freeze will capture everything.',
        ],
        10: [
            'SYSTEM FREEZE activated. The DNA Visualizer is now capturing the final snapshot for the debrief report.',
            'Direct teams to their DNA Map tab in the final scorecard — every decision from R1-R10 is now traced.',
            'Ask: "Looking at your complete DNA map, which single decision had the deepest systemic impact?"',
        ],
    };

    const prompts = DNA_DEBRIEF[activeRound] || [];

    return (
        <div style={{
            background: 'linear-gradient(135deg, rgba(16,185,129,0.06), rgba(6,182,212,0.04))',
            border: '1px solid rgba(16,185,129,0.2)',
            borderRadius: '10px', padding: '1rem',
            borderLeft: '3px solid #10b981',
        }}>
            {sectionLabel('🧬', `Consequence DNA Insight — R${activeRound}`, '#10b981')}

            {/* Quick stats row */}
            <div style={{
                display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem',
                marginBottom: '0.75rem',
            }}>
                {[
                    { label: 'M_R', value: (mr.mr || 1.0).toFixed(2),
                      color: mr.mr >= 1.8 ? '#10b981' : mr.mr >= 1.2 ? '#3b82f6' : mr.mr >= 0.8 ? '#f59e0b' : '#ef4444' },
                    { label: 'Deep', value: ls.deep_intervention_count || 0, color: '#10b981' },
                    { label: 'Shallow', value: ls.shallow_intervention_count || 0, color: '#f59e0b' },
                    { label: 'Conflicts', value: activeConflicts.length, color: activeConflicts.length > 2 ? '#ef4444' : '#f59e0b' },
                ].map((s, i) => (
                    <div key={i} style={{
                        padding: '0.5rem', borderRadius: '7px',
                        background: 'rgba(0,0,0,0.15)', textAlign: 'center',
                        border: `1px solid ${s.color}25`,
                    }}>
                        <div style={{ fontSize: '1rem', fontWeight: 800, color: s.color, fontFamily: 'var(--font-mono, monospace)' }}>
                            {s.value}
                        </div>
                        <div style={{ fontSize: '0.58rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                            {s.label}
                        </div>
                    </div>
                ))}
            </div>

            {/* Archetype projection */}
            {mr.archetype && (
                <div style={{
                    padding: '0.4rem 0.65rem', borderRadius: '6px',
                    background: mr.archetype.gradient || 'rgba(99,102,241,0.1)',
                    display: 'inline-flex', alignItems: 'center', gap: '0.4rem',
                    fontSize: '0.72rem', fontWeight: 700, color: '#fff',
                    marginBottom: '0.75rem',
                }}>
                    {mr.archetype.icon} {mr.archetype.title}
                </div>
            )}

            {/* Triggered agents alert */}
            {triggeredAgents.length > 0 && (
                <div style={{
                    padding: '0.5rem 0.7rem', borderRadius: '6px',
                    background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                    marginBottom: '0.75rem',
                }}>
                    <div style={{ fontSize: '0.62rem', fontWeight: 800, color: '#ef4444', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.3rem' }}>
                        💥 Triggered Agents — Capital Leaking
                    </div>
                    {triggeredAgents.map(a => (
                        <div key={a.agent_id} style={{
                            fontSize: '0.72rem', color: '#fca5a5', padding: '0.15rem 0',
                            display: 'flex', alignItems: 'center', gap: '0.4rem',
                        }}>
                            <span>{a.icon}</span>
                            <span style={{ fontWeight: 700 }}>{a.name}</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.62rem', color: '#ef4444', fontFamily: 'var(--font-mono, monospace)' }}>
                                CF: {((a.constriction_factor || 0) * 100).toFixed(0)}%
                            </span>
                        </div>
                    ))}
                </div>
            )}

            {/* Round-specific debrief prompts */}
            {prompts.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {prompts.map((prompt, i) => (
                        <div key={i} style={{
                            padding: '0.45rem 0.65rem', borderRadius: '6px',
                            background: 'rgba(16,185,129,0.04)',
                            borderLeft: '2px solid rgba(16,185,129,0.3)',
                            fontSize: '0.78rem', color: '#a7f3d0', fontStyle: 'italic', lineHeight: 1.5,
                        }}>
                            {prompt}
                        </div>
                    ))}
                </div>
            )}

            {/* Effectiveness score */}
            {ls.effectiveness_score != null && (
                <div style={{
                    marginTop: '0.5rem', fontSize: '0.68rem', color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono, monospace)',
                }}>
                    System Effectiveness: {(ls.effectiveness_score * 100).toFixed(0)}% · 
                    Leverage Depth: {ls.deep_intervention_count || 0} deep / {ls.shallow_intervention_count || 0} shallow
                </div>
            )}
        </div>
    );
}

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
    
    // ── Teleprompter Narrative Engines ──
    cash_conversion_drag:       'Cash Conversion Drag — High governance risk BUs suffer slower cash collections, temporarily reducing available treasury.',
    implementation_lag:         'Implementation Lag — Delayed realization of synergy or CAPEX benefits. Decisions made now only fully impact EBITDA in future rounds.',
    supply_chain_contagion:     'Supply Chain Contagion — A crisis or high risk in one business unit spills over, amplifying operational costs across the entire group.',
    competitor_warning:         'Competitor Growth — The NPC competitor expands reliably by 3% every round. Falling behind means sacrificing future market share.',
    revenue_cannibalized:       'Revenue Cannibalization — One highly dominant BU begins eating into the market share of your other BUs, limiting overall group growth.',
    technology_lockin_penalty:  'Technology Lock-in — Repeated investment in legacy systems over 3 consecutive rounds triggers switching costs and reduces future agility.',
    regulatory_ratchet_active:  'Regulatory Ratchet — Escalating compliance costs permanently elevate the cost of capital if ESG standards are repeatedly missed.',
    stakeholder_fatigue_applied:'Stakeholder Fatigue — Repeated crises degrade stakeholder trust. Recovering reputation becomes exponentially more expensive over time.',
    dividend_ratchet_triggered: 'Dividend Ratchet — Cutting dividends after a period of stable payouts severely damages board confidence and group reputation.',
    tipping_point_reached:      'Climate Tipping Point — Systemic environmental thresholds have been crossed, activating irreversible acceleration of natural capital debt costs.',
    talent_neglect_surcharge:   'Talent Neglect — Chronically underfunded BUs experience extreme turnover. Replacement hiring introduces a sharp OPEX surcharge.',
    technical_debt_penalty:     'Technical Debt — A compounding penalty for deferring necessary infrastructure upgrades, manifesting as sudden, unavoidable capital expenditures.',
    greenwashing_scandal:       'Greenwashing Scandal — Punishes cosmetic ESG spending without substance. Reputation takes a severe hit that takes rounds to recover.',

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

    // Auto-sync activeRound whenever the live cohort advances a round
    useEffect(() => {
        setActiveRound(currentRound);
    }, [currentRound]);

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
                overflowX: 'auto',
                WebkitOverflowScrolling: 'touch',
                scrollbarWidth: 'none',    /* Firefox */
                msOverflowStyle: 'none',   /* IE/Edge */
            }}>
                {Array.from({ length: 10 }, (_, i) => i + 1).map(r => {
                    const isActive = activeRound === r;
                    const isPast = r <= currentRound;
                    return (
                        <button key={r} onClick={() => setActiveRound(r)} style={{
                            flex: '0 0 auto', minWidth: '36px', height: '36px', borderRadius: '7px', border: 'none',
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

            {/* ── Journey Improvement Guidance (Phase 6 Mechanics) ── */}
            {(() => {
                const ji = script.journey_improvement;
                if (!ji) return null;
                const entries = Object.entries(ji);
                if (entries.length === 0) return null;
                return (
                    <div style={{
                        background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(168,85,247,0.04))',
                        border: '1px solid rgba(99,102,241,0.2)',
                        borderRadius: '10px', padding: '1rem',
                        borderLeft: '3px solid #818cf8',
                    }}>
                        {sectionLabel('🎮', 'Journey Mechanic Guidance (Phase 6)', '#818cf8')}
                        <div style={{ fontSize: '0.68rem', color: 'rgba(129,140,248,0.7)', marginBottom: '0.75rem', fontStyle: 'italic' }}>
                            New mechanic variants active this round — review these facilitator notes before gameplay.
                        </div>
                        {entries.map(([mechKey, mechData]) => (
                            <details key={mechKey} open style={{
                                background: 'rgba(0,0,0,0.12)', borderRadius: '8px',
                                border: '1px solid rgba(255,255,255,0.04)',
                                overflow: 'hidden', marginBottom: '0.5rem',
                            }}>
                                <summary style={{
                                    padding: '0.6rem 0.85rem', cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                                    fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)',
                                    listStyle: 'none',
                                }}>
                                    <span>🎮</span>
                                    {mechKey.replace(/_/g, ' ').replace(/\br\d/g, m => m.toUpperCase()).replace(/\b\w/g, m => m.toUpperCase())}
                                    {mechData.applies_to_tiers && (
                                        <span style={{
                                            marginLeft: 'auto', fontSize: '0.68rem', padding: '2px 6px',
                                            borderRadius: '4px', background: 'rgba(99,102,241,0.1)',
                                            color: '#a5b4fc', fontFamily: 'var(--font-mono, monospace)',
                                        }}>
                                            {mechData.applies_to_tiers.join(' / ')}
                                        </span>
                                    )}
                                </summary>
                                <div style={{ padding: '0 0.85rem 0.75rem' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                                        {(mechData.facilitator_guidance || []).map((point, i) => (
                                            <div key={i} style={{
                                                padding: '0.4rem 0.6rem', borderRadius: '6px',
                                                background: point.startsWith('DEBRIEF') || point.startsWith('Connect')
                                                    ? 'rgba(139,92,246,0.06)' : 'rgba(99,102,241,0.04)',
                                                borderLeft: `2px solid ${
                                                    point.startsWith('⚠️') || point.startsWith('CRITICAL')
                                                        ? 'rgba(239,68,68,0.4)'
                                                        : point.startsWith('DEBRIEF') || point.startsWith('Connect')
                                                            ? 'rgba(139,92,246,0.4)'
                                                            : 'rgba(99,102,241,0.25)'
                                                }`,
                                                fontSize: '0.78rem',
                                                color: point.startsWith('⚠️') || point.startsWith('CRITICAL')
                                                    ? '#fca5a5'
                                                    : point.startsWith('DEBRIEF') || point.startsWith('Connect')
                                                        ? '#e9d5ff'
                                                        : 'var(--text-secondary, #cbd5e1)',
                                                lineHeight: 1.5,
                                                fontStyle: point.startsWith('DEBRIEF') || point.startsWith('Connect')
                                                    ? 'italic' : 'normal',
                                            }}>{point}</div>
                                        ))}
                                    </div>
                                </div>
                            </details>
                        ))}
                    </div>
                );
            })()}

            {/* ── Strategic Intel Hints (Facilitator-Only) ── */}
            {(() => {
                const STRATEGIC_HINTS = {
                    1: '💡 Teams that choose Surface Scan (A) or Phased Rollout (C) will face amplified crisis severity in Round 4. This is a 2× or 1.5× multiplier respectively.',
                    2: '💡 Perfect materiality matrix scores (>90% accuracy) earn a $2M treasury bonus. Encourage teams to use the CSRD framework carefully. ⚡ STRATEGIC PILLARS: The "materiality_aligned" flag (which earns +0.10 M_R at terminal valuation) is set by the "Materiality Advisory Board" sub-option within the Operations area, NOT by the primary round choice. Ensure facilitators running Pillars cohorts highlight this — teams often miss it.',
                    3: '💡 Teams choosing Rapid Supplier Switch (A) get the "early_decarboniser" flag — this unlocks a +0.10 synergy bonus in Round 7.',
                    4: '💡 Teams that did deep audits in R1 will see base crisis severity (40). Surface scans face 80 (doubled!). Phased audits face 60 (1.5×).',
                    5: '💡 Insurance Only (C) provides ZERO physical protection. If the cyclone strikes, full $12M damage hits. Hard Engineering and Nature-Based both mitigate.',
                    6: '💡 Ethical AI Overhaul (B) sets the "ethical_ai_overhaul" flag that provides +0.15 to the Regenerative Multiple in R10. This is the "Truth Premium."',
                    7: '💡 Waste-to-Energy (C) unlocks +0.35 synergy multiplier — the largest single boost. Teams above 1.20 synergy unlock "Resist & Integrate" in R10.',
                    8: '💡 Desalination (C) now generates $3M/round payback for 3 rounds after completion. The $30M cost becomes $21M net — still expensive but recoverable.',
                    9: '💡 Strike probability is now 50% (reduced from 75%). Strike only fires if average Social License is below 50. Teams with good SLO are safe.',
                    10: '💡 The Regenerative Multiple (M_R) determines the profile: ≥1.8 = Regenerative Titan, ≥1.2 = De-Risked Safe Haven, ≥0.8 = Fragile Giant, <0.8 = Stranded Relic.',
                };
                const CLIMATE_HINTS = {
                    1: '🌍 CLIMATE MODE: Foundation decisions are identical to legacy. Remind teams that carbon intensity will matter — their choices here set the trajectory.',
                    2: '🌍 CLIMATE MODE: The materiality matrix is the same across paradigms. Carbon pricing activates from R3 onwards — this is their last "free" round.',
                    3: '🌍 The Internal Carbon Fee ($40/tonne default) is now active. Every tonne of CO₂e is taxed from treasury → Green Fund. Teams with high emissions pay more. The early_decarboniser flag from Option A gives +0.10 synergy in R7.',
                    4: '🌍 Watch teams\' carbon intensity. If avg CI > 70 by R5, the CLIMATE TIPPING POINT activates — doubling all NCD hostility. Surface Scan (R1) teams face 2× crisis severity AND higher carbon costs.',
                    5: '🌍 CRITICAL ROUND: Tipping point evaluation happens now. Avg CI > 70 = irreversible. Teams should know: BUs with CI > 120 become "stranded assets", adding +1.5% to cost of capital permanently.',
                    6: '🌍 The carbon fee continues to accumulate. Check each team\'s Green Fund balance — teams paying high carbon fees should be using the fund to subsidise green CapEx. Ethical AI (B) provides the Truth Premium for R10.',
                    7: '🌍 Green fund is consumed first for all treasury costs. Waste-to-Energy (C) unlocks +0.35 synergy AND reduces carbon intensity. Teams in tipping point territory should prioritise decarbonisation to trigger "managed retreat" (25% hostility reduction if avg CI < 50).',
                    8: '🌍 NCD Forgiveness is now active: green CapEx reduces NCD by 0.5 per $1M invested. Teams in NCD death spirals can invest their way out. Desalination (C) generates $3M/round payback.',
                    9: '🌍 If tipping point is active AND avg CI has dropped below 50, the managed retreat kicks in: hostility is 1.5× instead of 2×. This is the reward for aggressive mid-game decarbonisation.',
                    10: '🌍 FINAL ROUND: The Regenerative Multiple absorbs all climate decisions. Teams with low NCD, active green funds, and managed tipping points will score highest. Carbon tax paid to date is shown in the valuation.'
                };
                // Use climate hints if the session paradigm is advanced_climate
                const hints = roundConfig?.decision_paradigm === 'advanced_climate' ? CLIMATE_HINTS : STRATEGIC_HINTS;
                const hint = hints[activeRound];
                if (!hint) return null;
                return (
                    <div style={{
                        background: roundConfig?.decision_paradigm === 'advanced_climate' ? 'rgba(16,185,129,0.10)' : 'rgba(16,185,129,0.06)',
                        border: '1px solid rgba(16,185,129,0.18)',
                        borderRadius: '10px', padding: '1rem',
                        borderLeft: roundConfig?.decision_paradigm === 'advanced_climate' ? '3px solid #10b981' : '3px solid #10b981',
                    }}>
                        {sectionLabel('🔮', roundConfig?.decision_paradigm === 'advanced_climate' ? 'Climate Engine Intel (Facilitator Only)' : 'Strategic Intel (Facilitator Only)', '#10b981')}
                        <div style={{ fontSize: '0.82rem', color: '#a7f3d0', lineHeight: 1.6 }}>{hint}</div>
                    </div>
                );
            })()}

            {/* ── R2 ESRS Concepts Reference (Facilitator-Only) ── */}
            {activeRound === 2 && (() => {
                const concepts = [
                    { ref: 'ESRS 1 §1.51', icon: '🏛️', title: 'Governance Body Oversight', color: '#818cf8',
                      body: 'ESRS requires the management body (board committee, not CEO alone) to oversee the materiality assessment. Option C (CEO-only sign-off) violates this — why institutional investors apply a Green Bond risk premium.' },
                    { ref: 'ESRS E1–E5 / S1–S4 / G1', icon: '🏷️', title: 'ESRS Topic Mapping (chip badges)', color: '#34d399',
                      body: 'Each chip now shows its ESRS code. E1=Climate, E3=Water, E4=Biodiversity, E5=Circular Economy. S2=Value Chain Workers, S4=Consumers. G1=Business Conduct. "Economic" is not an ESRS pillar — those risks sit under G1 or ESRS 2 SBM-3.' },
                    { ref: 'ESRS 1 §1.38', icon: '📏', title: 'Materiality Threshold Disclosure', color: '#fbbf24',
                      body: 'ESRS requires disclosing the thresholds used to determine materiality. Simulation threshold: ≥80% Q1 accuracy + non-C governance. After submission, students see "How was this scored?" — point them to it.' },
                    { ref: 'ESRS 1 §1.50', icon: '⚖️', title: 'Stakeholder Tension (Investor vs NGO)', color: '#f87171',
                      body: 'ESRS §1.50 requires "due consideration of conflicting views." Investors highlight Q3 financial risks; NGOs elevate Q2 community impacts. Ask teams: did your Panel Survey reveal tensions between what investors vs NGOs rated material?' },
                    { ref: 'ESRS 1 §1.30', icon: '📊', title: 'Severity × Likelihood Scoring', color: '#60a5fa',
                      body: 'Real ESRS uses Severity (Scale, Scope, Irremediability) × Likelihood, not binary High/Low. Chips now show score badges. An issue scoring ≥12 (e.g. 4×3) is Q1-eligible. Ask why high-severity issues sometimes have low likelihood.' },
                ];
                return (
                    <div style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: '10px', padding: '1rem', borderLeft: '3px solid #818cf8' }}>
                        {sectionLabel('📐', 'R2 ESRS Concepts Reference (Facilitator Only)', '#818cf8')}
                        <div style={{ fontSize: '0.68rem', color: 'rgba(129,140,248,0.7)', marginBottom: '0.75rem', fontStyle: 'italic' }}>Key ESRS mechanics to explain during the Double Materiality exercise.</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {concepts.map((c, i) => (
                                <details key={i} style={{ background: 'rgba(0,0,0,0.12)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)', overflow: 'hidden' }}>
                                    <summary style={{ padding: '0.55rem 0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)', listStyle: 'none' }}>
                                        <span>{c.icon}</span>
                                        <span style={{ color: c.color }}>{c.title}</span>
                                        <span style={{ marginLeft: 'auto', fontSize: '0.68rem', padding: '2px 6px', borderRadius: '4px', background: `${c.color}18`, color: c.color, fontFamily: 'var(--font-mono, monospace)' }}>{c.ref}</span>
                                    </summary>
                                    <div style={{ padding: '0.5rem 0.85rem 0.75rem' }}>
                                        <div style={{ fontSize: '0.79rem', color: 'var(--text-secondary, #cbd5e1)', lineHeight: 1.65, borderLeft: `2px solid ${c.color}55`, paddingLeft: '0.65rem' }}>{c.body}</div>
                                    </div>
                                </details>
                            ))}
                        </div>
                    </div>
                );
            })()}

            {/* ── Consequence DNA Insight Card (R5+) ── */}
            {activeRound >= 5 && sessionId && (() => {
                return <LiveDNAInsight sessionId={sessionId} activeRound={activeRound} sectionLabel={sectionLabel} />;
            })()}

            {/* ── Reflection Pause Points ── */}
            {(() => {
                const PAUSE_PROMPTS = {
                    3: {
                        title: 'Mid-Act I Reflection Pause',
                        prompts: [
                            'What patterns are emerging in how teams are balancing cost vs. long-term risk?',
                            'Which teams are building governance credibility vs. cutting corners?',
                            'How did the materiality gate in R2 affect their R3 decision confidence?',
                        ],
                    },
                    6: {
                        title: 'Mid-Game Reflection Pause',
                        prompts: [
                            'Ask teams: "If you could redo one decision from R1-R5, which would it be?"',
                            'Compare treasury positions across teams — who is financially strongest and why?',
                            'Discuss the invisible cost of deferred decisions — NCD, SLO erosion, reputation damage.',
                        ],
                    },
                    9: {
                        title: 'Pre-Finale Reflection Pause',
                        prompts: [
                            'What is the accumulated human cost of each team\'s strategy?',
                            'Which teams have built genuine stakeholder trust vs. performative ESG?',
                            'Preview: R10 will calculate Terminal Value. Ask teams to predict their Regenerative Multiple.',
                        ],
                    },
                };
                const pause = PAUSE_PROMPTS[activeRound];
                if (!pause) return null;
                return (
                    <div style={{
                        background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.18)',
                        borderRadius: '10px', padding: '1rem', borderLeft: '3px solid #f59e0b',
                    }}>
                        {sectionLabel('⏸️', pause.title, '#f59e0b')}
                        <div style={{
                            fontSize: '0.68rem', fontWeight: 800, color: '#fbbf24',
                            letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '0.5rem',
                        }}>
                            RECOMMENDED: Pause the simulation for 5-10 minutes of facilitated discussion
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                            {pause.prompts.map((p, i) => (
                                <div key={i} style={{
                                    padding: '0.5rem 0.7rem', borderRadius: '7px',
                                    background: 'rgba(245,158,11,0.04)',
                                    borderLeft: '2px solid rgba(245,158,11,0.3)',
                                    fontSize: '0.82rem', color: '#fde68a',
                                    fontStyle: 'italic', lineHeight: 1.5,
                                }}>
                                    {p}
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })()}

            {/* ── Side Track Debrief Intel ── */}
            {(() => {
                const SIDE_TRACK_DEBRIEF = {
                    supply_chain: {
                        icon: '🔗', label: 'Supply Chain Deep Dive',
                        debrief_after_round: 5,
                        talking_points: [
                            'Compare how teams handled the cobalt sourcing ethics dilemma — did they prioritise cost or human rights?',
                            'Teams that invested in Tier-4 mapping (SC-R1) should have seen cost savings in SC-R2. Highlight this forward-looking ROI.',
                            'The SC-R7 stress test is the capstone: teams with "option_a" resilience investments absorbed 80% of damage vs. 10% for reactive teams.',
                            'Cross-track dependency: SC cobalt findings seed into the Ethics track — discuss how supply chain decisions cascade into governance.',
                        ],
                        discussion_prompts: [
                            'What was the most surprising trade-off between supply chain cost and resilience?',
                            'How did your SC choices affect your reputation with different stakeholder groups?',
                            'If you could redo one supply chain decision, which would it be and why?',
                        ],
                    },
                    ethics_sustainability: {
                        icon: '⚖️', label: 'Ethics & Sustainability Deep Dive',
                        debrief_after_round: 4,
                        talking_points: [
                            'The AI governance decision in ES-R1 has compounding effects — teams that denied the bias issue face credibility penalties in later rounds.',
                            'Modern slavery due diligence (ES-R2) mirrors real CSDDD requirements. Discuss how "sphere of influence" arguments play out in practice.',
                            'Greenwashing substantiation (ES-R3) connects directly to the main sim\'s reputation mechanics — teams that defended claims face ASA-style penalties.',
                            'The Just Transition fund (ES-R5) is the most expensive option but yields the highest M_R bonus. Discuss the tension between short-term cost and long-term trust.',
                        ],
                        discussion_prompts: [
                            'How did your R1 AI governance decision affect employee trust in later rounds?',
                            'What regulatory frameworks (EU AI Act, CSDDD, TNFD) were most surprising to encounter?',
                            'Is a "just transition" affordable, or is it a luxury only profitable companies can afford?',
                        ],
                    },
                    stakeholder_management: {
                        icon: '🤝', label: 'Stakeholder Management Deep Dive',
                        debrief_after_round: 3,
                        talking_points: [
                            'Teams that established engagement policies in SM-R1 had crisis playbooks for SM-R4 — discuss the value of proactive stakeholder strategy.',
                            'ESG rating downgrade threats (SM-R2) mirror real MSCI/Sustainalytics dynamics. Challenge teams: was challenging the methodology ever justifiable?',
                            'Community opposition (SM-R3) tests the "social license to operate" concept. Teams that overrode communities face compounding backlash in SM-R4.',
                            'The SM-R4 multi-front crisis is the capstone — did reactive teams spiral while engaged teams had pre-established channels?',
                        ],
                        discussion_prompts: [
                            'Which stakeholder group was hardest to manage, and why?',
                            'How does your SM strategy compare to real ESG rating agency methodologies?',
                            'When (if ever) is it justified to prioritise speed over community engagement?',
                        ],
                    },
                    sustainability_reporting: {
                        icon: '📊', label: 'Sustainability Reporting Deep Dive',
                        debrief_after_round: 4,
                        talking_points: [
                            'CSRD readiness (SR-R1) sets the trajectory — minimum compliance teams face compounding credibility issues by SR-R4.',
                            'Climate disclosure quality (SR-R2) directly mirrors IFRS S2 requirements. Discuss the real cost of Scope 3 data collection at 90%+ coverage.',
                            'Assurance credibility (SR-R4) is the inflection point — teams without external assurance have their entire reporting undermined.',
                            'The integrated reporting capstone (SR-R5) challenges teams to prove ESG-to-financial connectivity. Cross-track: Ethics track score enriches social metrics.',
                        ],
                        discussion_prompts: [
                            'What was the hardest data gap to close, and what does that tell you about real CSRD implementation?',
                            'Is reasonable assurance worth 2× the cost of limited assurance? When does credibility justify the investment?',
                            'How would you explain the ROI of sustainability reporting to a sceptical CFO?',
                        ],
                    },
                };

                // Show debrief sections for all tracks (facilitator can review at any time)
                const tracks = Object.entries(SIDE_TRACK_DEBRIEF);
                if (tracks.length === 0) return null;

                return (
                    <div style={{
                        background: 'linear-gradient(135deg, rgba(99,102,241,0.06), rgba(0,229,195,0.04))',
                        border: '1px solid rgba(99,102,241,0.15)',
                        borderRadius: '10px', padding: '1rem',
                        borderLeft: '3px solid #818cf8',
                    }}>
                        {sectionLabel('🛤️', 'Side Track Debrief Intel (Facilitator Only)', '#818cf8')}
                        <div style={{ fontSize: '0.68rem', color: 'rgba(129,140,248,0.7)', marginBottom: '0.75rem', fontStyle: 'italic' }}>
                            Use these prompts when debriefing side track results with your cohort.
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            {tracks.map(([tid, t]) => (
                                <details key={tid} style={{
                                    background: 'rgba(0,0,0,0.12)', borderRadius: '8px',
                                    border: '1px solid rgba(255,255,255,0.04)',
                                    overflow: 'hidden',
                                }}>
                                    <summary style={{
                                        padding: '0.6rem 0.85rem', cursor: 'pointer',
                                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                                        fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)',
                                        listStyle: 'none',
                                    }}>
                                        <span>{t.icon}</span> {t.label}
                                        <span style={{
                                            marginLeft: 'auto', fontSize: '0.68rem', padding: '2px 6px',
                                            borderRadius: '4px', background: 'rgba(99,102,241,0.1)',
                                            color: '#a5b4fc', fontFamily: 'var(--font-mono, monospace)',
                                        }}>Debrief after R{t.debrief_after_round}</span>
                                    </summary>
                                    <div style={{ padding: '0 0.85rem 0.75rem' }}>
                                        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.4rem' }}>
                                            Key Teaching Points
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', marginBottom: '0.6rem' }}>
                                            {t.talking_points.map((p, i) => (
                                                <div key={i} style={{
                                                    padding: '0.4rem 0.6rem', borderRadius: '6px',
                                                    background: 'rgba(99,102,241,0.04)',
                                                    borderLeft: '2px solid rgba(99,102,241,0.25)',
                                                    fontSize: '0.78rem', color: 'var(--text-secondary, #cbd5e1)', lineHeight: 1.5,
                                                }}>{p}</div>
                                            ))}
                                        </div>
                                        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#c4b5fd', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.4rem' }}>
                                            Discussion Prompts
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                                            {t.discussion_prompts.map((p, i) => (
                                                <div key={i} style={{
                                                    padding: '0.4rem 0.6rem', borderRadius: '6px',
                                                    background: 'rgba(139,92,246,0.04)',
                                                    borderLeft: '2px solid rgba(139,92,246,0.25)',
                                                    fontSize: '0.78rem', color: '#e9d5ff', fontStyle: 'italic', lineHeight: 1.5,
                                                }}>&ldquo;{p}&rdquo;</div>
                                            ))}
                                        </div>
                                    </div>
                                </details>
                            ))}
                        </div>
                    </div>
                );
            })()}
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

            {/* ── Systemic Risk Intelligence (Live Session Data) ── */}
            {sessionId && <SystemicRiskIntel sessionId={sessionId} sectionLabel={sectionLabel} />}

            {/* ── Autonomous Stakeholder Agent Intelligence ── */}
            {(() => {
                const aad = script.autonomous_agents_debrief;
                if (!aad) return null;
                // Collect all debrief question arrays
                const debriefKeys = Object.keys(aad).filter(k => k.startsWith('debrief_'));
                return (
                    <div style={{
                        background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(6,182,212,0.04))',
                        border: '1px solid rgba(139,92,246,0.2)',
                        borderRadius: '10px', padding: '1rem',
                        borderLeft: '3px solid #a78bfa',
                    }}>
                        {sectionLabel('🎭', 'Autonomous Stakeholder Agents — Debrief Intelligence', '#a78bfa')}

                        {/* Stage indicator */}
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: '0.5rem',
                            marginBottom: '0.75rem',
                        }}>
                            <span style={{
                                padding: '0.2rem 0.6rem', borderRadius: '5px', fontSize: '0.68rem',
                                fontWeight: 800, fontFamily: 'var(--font-mono, monospace)',
                                background: 'rgba(139,92,246,0.12)', color: '#c4b5fd',
                                border: '1px solid rgba(139,92,246,0.25)',
                                letterSpacing: '0.06em',
                            }}>
                                LIKELY STAGE: {aad.likely_stage}
                            </span>
                        </div>

                        {/* Facilitator note */}
                        {aad.facilitator_note && (
                            <div style={{
                                padding: '0.5rem 0.7rem', borderRadius: '7px',
                                background: 'rgba(245,158,11,0.06)',
                                border: '1px solid rgba(245,158,11,0.15)',
                                borderLeft: '2px solid rgba(245,158,11,0.4)',
                                fontSize: '0.78rem', color: '#fde68a',
                                lineHeight: 1.5, marginBottom: '0.75rem',
                            }}>
                                ⚠️ {aad.facilitator_note}
                            </div>
                        )}

                        {/* Debrief questions by category */}
                        {debriefKeys.map(key => {
                            const questions = aad[key] || [];
                            if (questions.length === 0) return null;
                            const label = key
                                .replace('debrief_', '')
                                .replace(/_/g, ' ')
                                .replace(/\b\w/g, m => m.toUpperCase());
                            return (
                                <details key={key} open style={{
                                    background: 'rgba(0,0,0,0.12)', borderRadius: '8px',
                                    border: '1px solid rgba(255,255,255,0.04)',
                                    overflow: 'hidden', marginBottom: '0.5rem',
                                }}>
                                    <summary style={{
                                        padding: '0.55rem 0.85rem', cursor: 'pointer',
                                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                                        fontSize: '0.75rem', fontWeight: 700, color: '#c4b5fd',
                                        listStyle: 'none', letterSpacing: '0.04em',
                                    }}>
                                        🗣️ {label} ({questions.length} questions)
                                    </summary>
                                    <div style={{ padding: '0 0.85rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                                        {questions.map((q, qi) => (
                                            <div key={qi} style={{
                                                padding: '0.45rem 0.65rem', borderRadius: '6px',
                                                background: q.startsWith('★') ? 'rgba(201,168,76,0.06)' : 'rgba(139,92,246,0.04)',
                                                borderLeft: `2px solid ${q.startsWith('★') ? 'rgba(201,168,76,0.4)' : 'rgba(139,92,246,0.3)'}`,
                                                fontSize: '0.78rem',
                                                color: q.startsWith('★') ? '#fde68a' : 'var(--text-secondary, #94a3b8)',
                                                fontStyle: 'italic', lineHeight: 1.5,
                                                fontWeight: q.startsWith('★') ? 600 : 400,
                                            }}>
                                                &ldquo;{q}&rdquo;
                                            </div>
                                        ))}
                                    </div>
                                </details>
                            );
                        })}
                    </div>
                );
            })()}

            {/* ── Live Agent State (Session-Aware) ── */}
            {sessionId && <LiveAgentIntel sessionId={sessionId} sectionLabel={sectionLabel} />}

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
