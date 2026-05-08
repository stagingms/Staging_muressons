'use client';

import { useMemo } from 'react';
import styles from './FinalReport.module.css';
import { Abbr } from './Glossary';

/**
 * Profile theme map — colours, icons, and gradient per archetype.
 */
const PROFILES = {
    regenerative_titan: {
        icon: '🌱',
        gradient: 'linear-gradient(135deg, #10b981, #059669)',
        tagColor: '#10b981',
        rank: 'APEX',
    },
    derisked_safe_haven: {
        icon: '🛡️',
        gradient: 'linear-gradient(135deg, #3b82f6, #2563eb)',
        tagColor: '#3b82f6',
        rank: 'SOLID',
    },
    fragile_giant: {
        icon: '⚠️',
        gradient: 'linear-gradient(135deg, #f59e0b, #d97706)',
        tagColor: '#f59e0b',
        rank: 'AT RISK',
    },
    stranded_relic: {
        icon: '💀',
        gradient: 'linear-gradient(135deg, #ef4444, #b91c1c)',
        tagColor: '#ef4444',
        rank: 'TERMINAL',
    },
};

const MR_LABELS = {
    base: { label: 'Base', description: 'Starting multiple' },
    synergy_bonus: { label: 'R7 Synergy', description: 'Achieved circularity synergy (waste-to-energy)' },
    resilience_bonus: { label: 'R5/R8 Resilience', description: 'Survived without bailout or water prioritisation' },
    truth_premium: { label: 'R6 Truth Premium', description: 'Chose ethical AI overhaul' },
    community_champion_bonus: { label: 'R9 Community Champion', description: 'Invested $20M in community fund' },
    just_transition_bonus: { label: 'R9 Just Transition', description: 'Chose managed transition' },
    workforce_bonus: { label: 'HR Workforce Excellence', description: 'Workforce readiness ≥ 75 at terminal' },
    wellbeing_bonus: { label: 'HR Wellbeing Champion', description: 'Average burnout < 20 at terminal' },
    instability_discount: { label: 'Instability Discount', description: 'Average Social License < 75' },
    max_achievable_mr: { label: 'Max Achievable', description: 'Perfect play ceiling' },
};

/**
 * FinalReport — The Year 5 Annual Report.
 * Displays Terminal Value, Terminal_EBITDA, Regenerative Multiple breakdown,
 * profile archetype, and the Activist Ultimatum decision.
 *
 * Props:
 *  - data: the R10 extra_events from the backend post_tick
 *  - onClose: () => void
 */
export default function FinalReport({ data = null, onClose }) {
    // Seed data for standalone rendering when no live data
    const d = data || {
        terminal_ebitda: 14_250_000,
        carbon_tonnage_group: 183,
        carbon_cost: 45_750,
        carbon_tax_per_ton: 250,
        regenerative_multiple: 1.35,
        mr_breakdown: {
            base: 1.0,
            synergy_bonus: 0.3,
            resilience_bonus: 0.2,
            truth_premium: 0,
            community_champion_bonus: 0,
            just_transition_bonus: 0.12,
            workforce_bonus: 0.10,
            wellbeing_bonus: 0,
            instability_discount: -0.4,
        },
        terminal_value: 230_850_000,
        exit_multiple: 12.0,
        final_treasury: 38_500_000,
        profile: 'derisked_safe_haven',
        profile_title: 'The De-risked Safe-Haven',
        profile_description:
            'A resilient corporation that avoided the worst tail risks. ' +
            'Investors value the predictability, but innovation is stalling. ' +
            'Solid, but not transformational.',
        synergy_score: 120,
        avg_social_license: 58.5,
        r10_choice: 'option_b',
    };

    const theme = PROFILES[d.profile] || PROFILES.fragile_giant;
    const breakdown = d.mr_breakdown || {};

    const mrItems = useMemo(
        () =>
            Object.entries(breakdown)
                .filter(([, val]) => val !== 0)
                .map(([key, val]) => ({
                    key,
                    value: val,
                    ...MR_LABELS[key],
                })),
        [breakdown]
    );

    return (
        <div className={styles.overlay}>
            <div className={styles.report}>
                {/* ── Hero Banner ──────────────────────────────────── */}
                <header className={styles.hero} style={{ background: theme.gradient }}>
                    <div className={styles.heroContent}>
                        <span className={styles.heroIcon}>{theme.icon}</span>
                        <div>
                            <div className={styles.year}>MURESSONS GLOBAL — YEAR 5 ANNUAL REPORT</div>
                            <h1 className={styles.profileTitle}>{d.profile_title}</h1>
                            <span className={styles.rankBadge} style={{ background: 'rgba(0,0,0,0.3)' }}>
                                {theme.rank}
                            </span>
                        </div>
                    </div>
                </header>

                {/* ── Profile Description ──────────────────────────── */}
                <section className={styles.profileDesc}>
                    <p>{d.profile_description}</p>
                </section>

                {/* ── Key Metrics Row ─────────────────────────────── */}
                <section className={styles.metricsRow}>
                    <div className={styles.metricCard}>
                        <span className={styles.metricLabel}><Abbr term="TV">Terminal Value</Abbr></span>
                        <span className={styles.metricValue} style={{ color: theme.tagColor }}>
                            ${(d.terminal_value / 1_000_000).toFixed(1)}M
                        </span>
                        <span className={styles.metricSub}>
                            = <Abbr term="EBITDA">EBITDA</Abbr> × {d.exit_multiple}× × <abbr title="Regenerative Multiple — bonus/penalty multiplier based on ESG performance">M<sub>R</sub></abbr>
                        </span>
                    </div>
                    <div className={styles.metricCard}>
                        <span className={styles.metricLabel}><Abbr term="EBITDA">Terminal EBITDA</Abbr></span>
                        <span className={styles.metricValue}>
                            ${(d.terminal_ebitda / 1_000_000).toFixed(2)}M
                        </span>
                        <span className={styles.metricSub}>
                            After ${(d.carbon_cost / 1_000).toFixed(0)}K carbon tax
                        </span>
                    </div>
                    <div className={styles.metricCard}>
                        <span className={styles.metricLabel}>Regenerative Multiple</span>
                        <span className={styles.metricValue} style={{ color: theme.tagColor }}>
                            {d.regenerative_multiple.toFixed(2)}×
                        </span>
                        <span className={styles.metricSub}>
                            <abbr title="Regenerative Multiple">M<sub>R</sub></abbr> = Base + Bonuses − Penalties
                        </span>
                    </div>
                    <div className={styles.metricCard}>
                        <span className={styles.metricLabel}>Final Treasury</span>
                        <span className={styles.metricValue}>
                            ${(d.final_treasury / 1_000_000).toFixed(1)}M
                        </span>
                        <span className={styles.metricSub}>
                            Cash reserves at game end
                        </span>
                    </div>
                </section>

                {/* ── MR Breakdown ────────────────────────────────── */}
                <section className={styles.breakdownSection}>
                    <h2 className={styles.sectionTitle}>
                        <span>📊</span> Regenerative Multiple Breakdown
                    </h2>
                    <div className={styles.breakdownGrid}>
                        {mrItems.map((item) => (
                            <div
                                key={item.key}
                                className={`${styles.breakdownItem} ${item.value > 0 ? styles.positive : item.value < 0 ? styles.negative : ''
                                    }`}
                            >
                                <div className={styles.breakdownHeader}>
                                    <span className={styles.breakdownLabel}>{item.label}</span>
                                    <span className={styles.breakdownValue}>
                                        {item.value > 0 ? '+' : ''}
                                        {item.value.toFixed(2)}
                                    </span>
                                </div>
                                <div className={styles.breakdownDesc}>{item.description}</div>
                                <div className={styles.breakdownBar}>
                                    <div
                                        className={styles.breakdownFill}
                                        style={{
                                            width: `${Math.abs(item.value) * 100}%`,
                                            background: item.value >= 0 ? '#10b981' : '#ef4444',
                                        }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className={styles.mrTotal}>
                        <span>Final M<sub>R</sub></span>
                        <span className={styles.mrTotalValue} style={{ color: theme.tagColor }}>
                            {d.regenerative_multiple.toFixed(2)}×
                        </span>
                    </div>
                </section>

                {/* ── Carbon & Environment ────────────────────────── */}
                <section className={styles.carbonSection}>
                    <h2 className={styles.sectionTitle}>
                        <span>🌍</span> Carbon & Environmental Impact
                    </h2>
                    <div className={styles.carbonGrid}>
                        <div className={styles.carbonCard}>
                            <span className={styles.carbonLabel}>Group Carbon Tonnage</span>
                            <span className={styles.carbonValue}>
                                {d.carbon_tonnage_group?.toFixed(0) || '—'} units
                            </span>
                        </div>
                        <div className={styles.carbonCard}>
                            <span className={styles.carbonLabel}>Carbon Tax Rate</span>
                            <span className={styles.carbonValue}>
                                ${d.carbon_tax_per_ton}/ton
                            </span>
                        </div>
                        <div className={styles.carbonCard}>
                            <span className={styles.carbonLabel}>Total Carbon Cost</span>
                            <span className={styles.carbonValue}>
                                ${(d.carbon_cost / 1_000).toFixed(1)}K
                            </span>
                        </div>
                        <div className={styles.carbonCard}>
                            <span className={styles.carbonLabel}>Avg Social License</span>
                            <span className={styles.carbonValue}>
                                {d.avg_social_license?.toFixed(1) || '—'}/100
                            </span>
                        </div>
                    </div>

                    {/* SBTi Pathway History */}
                    {d.sbti_pathway_history && d.sbti_pathway_history.length > 0 && (
                        <div style={{ marginTop: '1.5rem', background: 'rgba(0,0,0,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(0,0,0,0.05)' }}>
                            <h3 style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span>📉</span> SBTi Decarbonisation Pathway
                            </h3>
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                {d.sbti_pathway_history.map((pt, i) => (
                                    <div key={i} style={{ background: '#fff', padding: '6px 10px', borderRadius: '4px', border: '1px solid #e2e8f0', fontSize: '0.75rem' }}>
                                        <span style={{ color: '#64748b', marginRight: '6px' }}>R{pt.round}</span>
                                        <span style={{ fontWeight: 'bold', color: pt.on_track ? '#10b981' : '#ef4444' }}>
                                            {pt.emissions.toFixed(0)}t {pt.on_track ? '✅' : '⚠️'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Carbon Forwards */}
                    {d.carbon_forwards && d.carbon_forwards.length > 0 && (
                        <div style={{ marginTop: '1rem', background: 'rgba(0,0,0,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(0,0,0,0.05)' }}>
                            <h3 style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span>📜</span> Active Carbon Forwards
                            </h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px' }}>
                                {d.carbon_forwards.map((fw, i) => (
                                    <div key={i} style={{ background: '#fff', padding: '8px', borderRadius: '4px', border: '1px solid #e2e8f0', fontSize: '0.75rem', display: 'flex', flexDirection: 'column' }}>
                                        <span style={{ color: '#64748b', fontSize: '0.65rem', textTransform: 'uppercase' }}>Volume</span>
                                        <span style={{ fontWeight: 'bold' }}>{fw.amount} tons</span>
                                        <span style={{ color: '#64748b', fontSize: '0.65rem', textTransform: 'uppercase', marginTop: '4px' }}>Strike Price</span>
                                        <span style={{ fontWeight: 'bold', color: '#3b82f6' }}>${fw.strike_price}/t</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </section>

                {/* ── Terminal Value Formula ───────────────────────── */}
                <section className={styles.formulaSection}>
                    <h2 className={styles.sectionTitle}>
                        <span>🧮</span> Terminal Valuation Formula
                    </h2>
                    <div className={styles.formula}>
                        <div className={styles.formulaLine}>
                            V<sub>T</sub> = EBITDA<sub>Year 5</sub> × Exit Multiple × M<sub>R</sub>
                        </div>
                        <div className={styles.formulaLine}>
                            V<sub>T</sub> = ${(d.terminal_ebitda / 1_000_000).toFixed(2)}M × {d.exit_multiple}×
                            {' '} × {d.regenerative_multiple.toFixed(2)}
                        </div>
                        <div className={styles.formulaResult} style={{ color: theme.tagColor }}>
                            V<sub>T</sub> = ${(d.terminal_value / 1_000_000).toFixed(2)}M
                        </div>
                    </div>
                </section>

                {/* ── HR ROI Report ─────────────────────────────────── */}
                {d.hr_roi_report && (
                    <section className={styles.carbonSection}>
                        <h2 className={styles.sectionTitle}>
                            <span>🧑‍💼</span> HR Investment ROI Report
                        </h2>
                        <div className={styles.carbonGrid}>
                            <div className={styles.carbonCard}>
                                <span className={styles.carbonLabel}>Workforce Readiness</span>
                                <span className={styles.carbonValue} style={{
                                    color: d.hr_roi_report.workforce_readiness_r10 >= 75 ? '#10b981' : '#f59e0b'
                                }}>
                                    {d.hr_roi_report.workforce_readiness_r10}/100
                                    {d.hr_roi_report.workforce_bonus_earned && ' ✅'}
                                </span>
                            </div>
                            <div className={styles.carbonCard}>
                                <span className={styles.carbonLabel}>Avg Burnout Index</span>
                                <span className={styles.carbonValue} style={{
                                    color: d.hr_roi_report.avg_burnout_r10 < 20 ? '#10b981' :
                                           d.hr_roi_report.avg_burnout_r10 < 50 ? '#f59e0b' : '#ef4444'
                                }}>
                                    {d.hr_roi_report.avg_burnout_r10}/100
                                    {d.hr_roi_report.wellbeing_bonus_earned && ' ✅'}
                                </span>
                            </div>
                            <div className={styles.carbonCard}>
                                <span className={styles.carbonLabel}>Burnout OPEX Penalty</span>
                                <span className={styles.carbonValue} style={{
                                    color: d.hr_roi_report.burnout_opex_penalty_rate > 0 ? '#ef4444' : '#10b981'
                                }}>
                                    {d.hr_roi_report.burnout_opex_penalty_rate > 0
                                        ? `−${d.hr_roi_report.burnout_opex_penalty_rate.toFixed(1)}%`
                                        : 'None ✅'}
                                </span>
                            </div>
                            <div className={styles.carbonCard}>
                                <span className={styles.carbonLabel}>HR Terminal Value Uplift</span>
                                <span className={styles.carbonValue} style={{ color: theme.tagColor }}>
                                    {d.hr_roi_report.terminal_value_uplift_from_hr > 0
                                        ? `+$${(d.hr_roi_report.terminal_value_uplift_from_hr / 1_000_000).toFixed(1)}M`
                                        : '$0'}
                                </span>
                            </div>
                        </div>
                        {d.hr_roi_report.mr_bonus_from_hr > 0 && (
                            <div className={styles.mrTotal}>
                                <span>HR M<sub>R</sub> Contribution</span>
                                <span className={styles.mrTotalValue} style={{ color: '#10b981' }}>
                                    +{d.hr_roi_report.mr_bonus_from_hr.toFixed(2)}
                                </span>
                            </div>
                        )}
                    </section>
                )}

                {/* ── Close Button ────────────────────────────────── */}
                <div className={styles.closeRow}>
                    <button className={styles.closeBtn} onClick={onClose} style={{ background: theme.gradient }}>
                        Close Annual Report
                    </button>
                </div>
            </div>
        </div>
    );
}
