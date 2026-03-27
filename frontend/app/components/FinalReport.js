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
    synergy_bonus: { label: 'R7 Synergy', description: 'Achieved circularity synergy' },
    resilience_bonus: { label: 'R5/R8 Resilience', description: 'Survived without bailout' },
    truth_premium: { label: 'R6 Truth Premium', description: 'Chose ethical AI overhaul' },
    instability_discount: { label: 'Instability Discount', description: 'Social License < 75' },
};

/**
 * FinalReport — The Year 3 Annual Report.
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
                            <div className={styles.year}>MURESSONS GLOBAL — YEAR 3 ANNUAL REPORT</div>
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
                </section>

                {/* ── Terminal Value Formula ───────────────────────── */}
                <section className={styles.formulaSection}>
                    <h2 className={styles.sectionTitle}>
                        <span>🧮</span> Terminal Valuation Formula
                    </h2>
                    <div className={styles.formula}>
                        <div className={styles.formulaLine}>
                            V<sub>T</sub> = EBITDA<sub>Year 3</sub> × Exit Multiple × M<sub>R</sub>
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
