'use client';

import { useState, useEffect } from 'react';
import styles from './SimulationReference.module.css';

const API = process.env.NEXT_PUBLIC_API_URL || '';

export default function SimulationReference() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeSection, setActiveSection] = useState('overview');
    const [expandedRound, setExpandedRound] = useState(null);
    const [formulaFilter, setFormulaFilter] = useState('all');

    useEffect(() => {
        const fetchRef = async () => {
            try {
                const res = await fetch(`${API}/api/admin/simulation-reference`);
                if (!res.ok) throw new Error('Failed to load reference data');
                const json = await res.json();
                setData(json);
            } catch (e) {
                setError(e.message);
            } finally {
                setLoading(false);
            }
        };
        fetchRef();
        // Refresh every 30s to pick up god-mode changes
        const interval = setInterval(fetchRef, 30000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return (
        <div className={styles.loadingState}>
            <div className={styles.spinner} />
            <span>Loading Simulation Reference...</span>
        </div>
    );
    if (error) return <div className={styles.errorState}>⚠️ {error}</div>;
    if (!data) return null;

    const { meta, starting_state, engine_formulas, ac_mechanics, terminal_valuation, flag_dependencies, rounds } = data;
    const cs = meta.currency_symbol;

    const sections = [
        { id: 'overview', label: 'Overview', icon: '📋' },
        { id: 'starting', label: 'Starting State', icon: '🏁' },
        { id: 'formulas', label: 'Engine Formulas', icon: '⚙️' },
        { id: 'rounds', label: 'Round-by-Round', icon: '🎯' },
        { id: 'flags', label: 'Flag Dependencies', icon: '🔗' },
        { id: 'ac', label: 'Climate Engine', icon: '🌡️' },
        { id: 'terminal', label: 'Terminal Value', icon: '🏆' },
    ];

    const categories = [...new Set(engine_formulas.map(f => f.category))];

    return (
        <div className={styles.container}>
            {/* Section Nav */}
            <nav className={styles.sectionNav}>
                {sections.map(s => (
                    <button
                        key={s.id}
                        className={`${styles.sectionBtn} ${activeSection === s.id ? styles.sectionActive : ''}`}
                        onClick={() => setActiveSection(s.id)}
                    >
                        <span className={styles.sectionIcon}>{s.icon}</span>
                        <span>{s.label}</span>
                    </button>
                ))}
            </nav>

            {/* Read-Only Badge */}
            <div className={styles.readOnlyBadge}>
                <span>🔒</span> READ-ONLY REFERENCE — Values auto-update from simulation state
            </div>

            {/* ═══ OVERVIEW ═══ */}
            {activeSection === 'overview' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <span className={styles.titleIcon}>📋</span>
                        Simulation Master Reference
                    </h2>
                    <p className={styles.subtitle}>{meta.description}</p>

                    <div className={styles.statGrid}>
                        <div className={styles.statCard}>
                            <div className={styles.statValue}>{meta.active_sessions}</div>
                            <div className={styles.statLabel}>Active Sessions</div>
                        </div>
                        <div className={styles.statCard}>
                            <div className={styles.statValue}>{Object.keys(meta.paradigm_distribution).length}</div>
                            <div className={styles.statLabel}>Active Paradigms</div>
                        </div>
                        <div className={styles.statCard}>
                            <div className={styles.statValue}>{engine_formulas.length}</div>
                            <div className={styles.statLabel}>Engine Formulas</div>
                        </div>
                        <div className={styles.statCard}>
                            <div className={styles.statValue}>10</div>
                            <div className={styles.statLabel}>Decision Rounds</div>
                        </div>
                    </div>

                    {Object.keys(meta.paradigm_distribution).length > 0 && (
                        <div className={styles.paradigmBar}>
                            <h4>Paradigm Distribution</h4>
                            <div className={styles.paradigmChips}>
                                {Object.entries(meta.paradigm_distribution).map(([k, v]) => (
                                    <span key={k} className={styles.paradigmChip}>
                                        {k.replace(/_/g, ' ')} <strong>{v}</strong>
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className={styles.infoBox}>
                        <strong>Core Loop:</strong> Crisis → Decision (A/B/C) → CapEx Allocation → Engine Tick ({engine_formulas.length} formulas) → Events → Next Round
                    </div>
                </div>
            )}

            {/* ═══ STARTING STATE ═══ */}
            {activeSection === 'starting' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <span className={styles.titleIcon}>🏁</span>
                        Starting State
                    </h2>

                    <div className={styles.globalParams}>
                        <h4>Global Parameters (Live)</h4>
                        <div className={styles.paramGrid}>
                            {[
                                ['Treasury', `${cs}${(starting_state.corporate_treasury/1e6).toFixed(1)}M`],
                                ['Reputation', starting_state.group_reputation],
                                ['Synergy', `${starting_state.synergy_multiplier}×`],
                                ['CoC', `${(starting_state.cost_of_capital * 100).toFixed(0)}%`],
                                ['Loan Rate', `${(starting_state.loan_interest_rate * 100).toFixed(0)}%`],
                                ['VRIO Decay', `${(starting_state.vrio_decay_rate * 100).toFixed(0)}%`],
                                ['Inflation', `${(starting_state.inflation_index * 100).toFixed(0)}%`],
                                ['Currency', cs],
                            ].map(([label, val]) => (
                                <div key={label} className={styles.paramItem}>
                                    <span className={styles.paramLabel}>{label}</span>
                                    <span className={styles.paramValue}>{val}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <h4 style={{ margin: '1.5rem 0 0.75rem', color: 'var(--text-primary)' }}>Business Units</h4>
                    <div className={styles.tableWrap}>
                        <table className={styles.dataTable}>
                            <thead>
                                <tr>
                                    <th>BU</th><th>Revenue</th><th>OPEX</th><th>Margin</th>
                                    <th>CI</th><th>NCD</th><th>SLO</th><th>Rep</th><th>Gov</th><th>Water</th>
                                </tr>
                            </thead>
                            <tbody>
                                {starting_state.standard_bus.map(bu => (
                                    <tr key={bu.bu_id}>
                                        <td className={styles.buName}>{bu.bu_id.replace(/_/g, ' ')}</td>
                                        <td>{cs}{(bu.revenue/1e6).toFixed(0)}M</td>
                                        <td>{cs}{(bu.opex/1e6).toFixed(1)}M</td>
                                        <td className={styles.positive}>{cs}{((bu.revenue - bu.opex)/1e6).toFixed(1)}M</td>
                                        <td className={bu.ci > 50 ? styles.negative : ''}>{bu.ci}</td>
                                        <td>{bu.ncd.toLocaleString()}</td>
                                        <td>{bu.slo}</td>
                                        <td>{bu.rep}</td>
                                        <td className={bu.gov_risk > 20 ? styles.negative : ''}>{bu.gov_risk}</td>
                                        <td>{bu.water_dep}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* ═══ ENGINE FORMULAS ═══ */}
            {activeSection === 'formulas' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <span className={styles.titleIcon}>⚙️</span>
                        Engine Formulas ({engine_formulas.length})
                    </h2>

                    <div className={styles.filterRow}>
                        <button
                            className={`${styles.filterBtn} ${formulaFilter === 'all' ? styles.filterActive : ''}`}
                            onClick={() => setFormulaFilter('all')}
                        >All</button>
                        {categories.map(c => (
                            <button
                                key={c}
                                className={`${styles.filterBtn} ${formulaFilter === c ? styles.filterActive : ''}`}
                                onClick={() => setFormulaFilter(c)}
                            >{c}</button>
                        ))}
                    </div>

                    <div className={styles.formulaGrid}>
                        {engine_formulas
                            .filter(f => formulaFilter === 'all' || f.category === formulaFilter)
                            .map(f => (
                                <div key={f.id} className={styles.formulaCard}>
                                    <div className={styles.formulaHeader}>
                                        <span className={styles.formulaNum}>#{f.id}</span>
                                        <span className={styles.formulaName}>{f.name}</span>
                                        <span className={styles.formulaCat}>{f.category}</span>
                                    </div>
                                    <code className={styles.formulaCode}>{f.formula}</code>
                                </div>
                            ))
                        }
                    </div>
                </div>
            )}

            {/* ═══ ROUNDS ═══ */}
            {activeSection === 'rounds' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <span className={styles.titleIcon}>🎯</span>
                        Round-by-Round Decisions
                    </h2>

                    <div className={styles.roundList}>
                        {rounds.map(r => (
                            <div key={r.round} className={styles.roundCard}>
                                <button
                                    className={`${styles.roundHeader} ${expandedRound === r.round ? styles.roundExpanded : ''}`}
                                    onClick={() => setExpandedRound(expandedRound === r.round ? null : r.round)}
                                >
                                    <div className={styles.roundMeta}>
                                        <span className={styles.roundIcon}>{r.crisis_icon}</span>
                                        <span className={styles.roundNum}>R{r.round}</span>
                                        <span className={styles.roundTitle}>{r.title}</span>
                                        <span className={styles.roundTheme}>{r.theme}</span>
                                    </div>
                                    <span className={styles.expandIcon}>{expandedRound === r.round ? '−' : '+'}</span>
                                </button>

                                {expandedRound === r.round && (
                                    <div className={styles.roundBody}>
                                        <p className={styles.crisisDesc}>{r.crisis_description}</p>

                                        {Object.keys(r.special_rules).length > 0 && (
                                            <div className={styles.specialRules}>
                                                ⚡ Special: {Object.entries(r.special_rules).map(([k, v]) =>
                                                    `${k.replace(/_/g, ' ')}: ${typeof v === 'boolean' ? (v ? '✅' : '✗') : v}`
                                                ).join(' | ')}
                                            </div>
                                        )}

                                        <div className={styles.tableWrap}>
                                            <table className={styles.dataTable}>
                                                <thead>
                                                    <tr>
                                                        <th>Opt</th><th>Title</th><th>Treasury</th>
                                                        <th>CI Δ</th><th>Rep Δ</th><th>Flags</th><th>Framing</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {Object.entries(r.options).map(([label, opt]) => (
                                                        <tr key={label}>
                                                            <td className={styles.optLabel}>{label}</td>
                                                            <td>{opt.title}</td>
                                                            <td className={opt.treasury > 0 ? styles.positive : opt.treasury < 0 ? styles.negative : ''}>
                                                                {opt.treasury !== 0 ? `${cs}${(opt.treasury/1e6).toFixed(0)}M` : '—'}
                                                            </td>
                                                            <td className={opt.ci_delta > 0 ? styles.negative : opt.ci_delta < 0 ? styles.positive : ''}>
                                                                {opt.ci_delta !== 0 ? (opt.ci_delta > 0 ? '+' : '') + opt.ci_delta : '—'}
                                                            </td>
                                                            <td className={opt.reputation_delta > 0 ? styles.positive : opt.reputation_delta < 0 ? styles.negative : ''}>
                                                                {opt.reputation_delta !== 0 ? (opt.reputation_delta > 0 ? '+' : '') + opt.reputation_delta : '—'}
                                                            </td>
                                                            <td className={styles.flagCell}>
                                                                {opt.flags.map(f => (
                                                                    <span key={f} className={styles.flagTag}>{f}</span>
                                                                ))}
                                                            </td>
                                                            <td className={styles.framingCell}>{opt.climate_framing || '—'}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* ═══ FLAG DEPENDENCIES ═══ */}
            {activeSection === 'flags' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <span className={styles.titleIcon}>🔗</span>
                        Flag Dependency Chain
                    </h2>
                    <div className={styles.flagChain}>
                        {flag_dependencies.map((dep, i) => (
                            <div key={i} className={styles.depCard}>
                                <div className={styles.depSource}>{dep.source}</div>
                                <div className={styles.depArrow}>
                                    <span className={styles.depFlag}>{dep.flag}</span>
                                    →
                                </div>
                                <div className={styles.depTarget}>{dep.target}</div>
                                <div className={styles.depEffect}>{dep.effect}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* ═══ ADVANCED CLIMATE ═══ */}
            {activeSection === 'ac' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <span className={styles.titleIcon}>🌡️</span>
                        Advanced Climate Engine
                        <span className={`${styles.statusBadge} ${ac_mechanics.enabled ? styles.statusOn : styles.statusOff}`}>
                            {ac_mechanics.enabled ? '🟢 ACTIVE' : '⚪ INACTIVE'}
                        </span>
                    </h2>

                    {/* Carbon Fee Schedule */}
                    <div className={styles.acBlock}>
                        <h4>Carbon Fee Schedule (Base: {cs}{ac_mechanics.carbon_fee_base}/ton, +15%/round)</h4>
                        <div className={styles.feeBar}>
                            {ac_mechanics.carbon_fee_schedule.map(s => (
                                <div key={s.round} className={styles.feeStep}>
                                    <div className={styles.feeValue}>{cs}{s.fee_per_ton.toFixed(0)}</div>
                                    <div className={styles.feeRound}>R{s.round}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Tipping Thresholds */}
                    <div className={styles.acBlock}>
                        <h4>Graduated Tipping Point (3-Tier)</h4>
                        <div className={styles.tableWrap}>
                            <table className={styles.dataTable}>
                                <thead><tr><th>Tier</th><th>CI Threshold</th><th>Hostility ×</th><th>Cyclone P</th><th>L&D Levy</th></tr></thead>
                                <tbody>
                                    {['none', 'warning', 'stressed', 'tipped'].map(tier => (
                                        <tr key={tier} className={tier === 'tipped' ? styles.criticalRow : ''}>
                                            <td style={{ textTransform: 'capitalize' }}>{tier === 'none' ? '✅ None' : tier === 'warning' ? '⚠️ Warning' : tier === 'stressed' ? '🔶 Stressed' : '🌡️ Tipped'}</td>
                                            <td>{tier === 'none' ? `≤${ac_mechanics.tipping_thresholds.warning}` : `>${ac_mechanics.tipping_thresholds[tier]}`}</td>
                                            <td>{ac_mechanics.hostility_multipliers[tier]}×</td>
                                            <td>{(ac_mechanics.cyclone_escalation[tier] * 100).toFixed(0)}%</td>
                                            <td>{ac_mechanics.loss_damage_levies[tier] ? `${cs}${(ac_mechanics.loss_damage_levies[tier]/1e6).toFixed(1)}M` : '—'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Scope Ratios */}
                    <div className={styles.acBlock}>
                        <h4>Dynamic Scope 1/2/3 Ratios (GHG Protocol)</h4>
                        <div className={styles.tableWrap}>
                            <table className={styles.dataTable}>
                                <thead><tr><th>BU</th><th>Scope 1 (Direct)</th><th>Scope 2 (Energy)</th><th>Scope 3 (Value Chain)</th></tr></thead>
                                <tbody>
                                    {Object.entries(ac_mechanics.scope_ratios).map(([bu, r]) => (
                                        <tr key={bu}>
                                            <td className={styles.buName}>{bu.replace(/_/g, ' ')}</td>
                                            <td>{r.scope_1}%</td>
                                            <td>{r.scope_2}%</td>
                                            <td className={r.scope_3 >= 60 ? styles.negative : ''}>{r.scope_3}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* SBTi Schedule */}
                    <div className={styles.acBlock}>
                        <h4>SBTi 1.5°C Pathway Target (4.2%/year decline)</h4>
                        <div className={styles.feeBar}>
                            {ac_mechanics.sbti_schedule.map(s => (
                                <div key={s.round} className={styles.feeStep}>
                                    <div className={styles.feeValue}>{s.target_ci.toFixed(1)}</div>
                                    <div className={styles.feeRound}>R{s.round}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Key Formulas */}
                    <div className={styles.acBlock}>
                        <h4>Key AC Formulas</h4>
                        <div className={styles.formulaGrid}>
                            {[
                                ['NCD Forgiveness', ac_mechanics.ncd_forgiveness_formula],
                                ['CBAM', ac_mechanics.cbam_formula],
                                ['Carbon Futures', `Spot ±${ac_mechanics.carbon_futures.spot_volatility_pct}% | Forward: +${ac_mechanics.carbon_futures.forward_premium_pct}% for ${ac_mechanics.carbon_futures.forward_duration_rounds}R`],
                                ['EU Taxonomy', `CI < ${ac_mechanics.taxonomy_thresholds.aligned_ci_max} = aligned | >${ac_mechanics.taxonomy_thresholds.green_discount_pct}% → CoC -0.5%`],
                            ].map(([name, formula]) => (
                                <div key={name} className={styles.formulaCard}>
                                    <div className={styles.formulaHeader}>
                                        <span className={styles.formulaName}>{name}</span>
                                    </div>
                                    <code className={styles.formulaCode}>{formula}</code>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* ═══ TERMINAL VALUATION ═══ */}
            {activeSection === 'terminal' && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>
                        <span className={styles.titleIcon}>🏆</span>
                        Terminal Valuation (R10)
                    </h2>

                    <div className={styles.formulaCard} style={{ marginBottom: '1.5rem' }}>
                        <div className={styles.formulaHeader}>
                            <span className={styles.formulaName}>Standard Formula</span>
                        </div>
                        <code className={styles.formulaCode}>{terminal_valuation.formula_standard}</code>
                    </div>
                    <div className={styles.formulaCard} style={{ marginBottom: '1.5rem' }}>
                        <div className={styles.formulaHeader}>
                            <span className={styles.formulaName}>AC Formula</span>
                        </div>
                        <code className={styles.formulaCode}>{terminal_valuation.formula_ac}</code>
                    </div>

                    <div className={styles.paramGrid} style={{ marginBottom: '1.5rem' }}>
                        <div className={styles.paramItem}>
                            <span className={styles.paramLabel}>Carbon Tax</span>
                            <span className={styles.paramValue}>{cs}{terminal_valuation.carbon_tax_per_ton}/ton</span>
                        </div>
                        <div className={styles.paramItem}>
                            <span className={styles.paramLabel}>Exit Multiple</span>
                            <span className={styles.paramValue}>{terminal_valuation.exit_multiple}×</span>
                        </div>
                        <div className={styles.paramItem}>
                            <span className={styles.paramLabel}>Synergy Gate</span>
                            <span className={styles.paramValue}>{terminal_valuation.synergy_gate_threshold}</span>
                        </div>
                    </div>

                    <h4 style={{ margin: '1.5rem 0 0.75rem', color: 'var(--text-primary)' }}>M_R Components</h4>
                    <div className={styles.tableWrap}>
                        <table className={styles.dataTable}>
                            <thead><tr><th>Component</th><th>Value</th><th>Source</th></tr></thead>
                            <tbody>
                                {terminal_valuation.mr_components.map(c => (
                                    <tr key={c.name}>
                                        <td>{c.name}</td>
                                        <td className={c.value > 0 ? styles.positive : c.value < 0 ? styles.negative : ''}>
                                            {c.value > 0 ? '+' : ''}{c.value.toFixed(2)}
                                        </td>
                                        <td className={styles.sourceCell}>{c.source}</td>
                                    </tr>
                                ))}
                                <tr className={styles.totalRow}>
                                    <td><strong>Max M_R</strong></td>
                                    <td className={styles.positive}><strong>
                                        {terminal_valuation.mr_components.reduce((s, c) => s + (c.value > 0 ? c.value : 0), 0).toFixed(2)}
                                    </strong></td>
                                    <td>All positive bonuses</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <h4 style={{ margin: '1.5rem 0 0.75rem', color: 'var(--text-primary)' }}>Profile Archetypes</h4>
                    <div className={styles.archetypeGrid}>
                        {terminal_valuation.profile_archetypes.map(a => (
                            <div key={a.name} className={styles.archetypeCard}>
                                {a.icon && <span className={styles.archetypeIcon}>{a.icon}</span>}
                                <span className={styles.archetypeName}>{a.name}</span>
                                <span className={styles.archetypeThreshold}>M_R ≥ {a.mr_min.toFixed(1)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
